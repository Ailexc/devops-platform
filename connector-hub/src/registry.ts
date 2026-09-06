import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';

/** 连接器工具声明（注册表 ### tools 节） */
export interface ToolDecl {
  name: string;
  title: string;
  cmd: string;
  risk: 'read' | 'write' | 'high-risk-write';
}

/** 连接器条目（注册表 ## 节） */
export interface Connector {
  name: string;
  type: 'cli' | 'mcp';
  path: string;
  envPath?: string;
  versionCmd?: string;
  doctorCmd?: string;
  enabled: boolean;
  tools: ToolDecl[];
}

export const REGISTRY_DIR = path.join(os.homedir(), '.agent');
export const REGISTRY_PATH = path.join(REGISTRY_DIR, 'connectors.md');
export const DOCTOR_PATH = path.join(os.homedir(), 'tools', 'connector-doctor.sh');

/**
 * doctor 脚本模板。
 * 注意：check 用 version_cmd 而非 doctor_cmd——lark-cli doctor 在未配置应用时会
 * 因 config_file 检查失败而整体退出码非 0，导致"已安装但未认证"被误报为不可用。
 * version_cmd 只验证二进制可用性，认证状态由面板单独展示。
 */
export const DOCTOR_TEMPLATE = `#!/usr/bin/env bash
# 连接器健康检查（由 connector-hub 插件维护，可手工编辑）
set -u
PASS=0; FAIL=0
check() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "✅ $name"; PASS=$((PASS+1))
  else
    echo "❌ $name"; FAIL=$((FAIL+1))
  fi
}
# >>> connectors
# <<< connectors
echo "---"
echo "通过: $PASS  失败: $FAIL"
exit $FAIL
`;


/**
 * 解析 ~/.agent/connectors.md
 * 格式：## <name> 开启连接器块，- key: value 键值对；### tools 子节声明工具
 */
export function parseRegistry(content: string): Connector[] {
  const connectors: Connector[] = [];
  let current: Connector | null = null;
  let inTools = false;
  let lastTool: ToolDecl | null = null;

  for (const rawLine of content.split('\n')) {
    const line = rawLine.trim();

    if (line.startsWith('## ') && !line.startsWith('### ')) {
      if (current) connectors.push(current);
      current = {
        name: line.slice(3).trim(),
        type: 'cli',
        path: '',
        enabled: true,
        tools: []
      };
      inTools = false;
      lastTool = null;
      continue;
    }

    if (!current) continue;

    if (line.startsWith('### ')) {
      inTools = line.slice(4).trim().toLowerCase() === 'tools';
      lastTool = null;
      continue;
    }

    if (line.startsWith('- ')) {
      const body = line.slice(2);
      const m = body.match(/^([a-z_]+):\s*(.*)$/);
      if (!m) continue;
      const [, key, rawValue] = m;
      const value = rawValue.trim().replace(/^["']|["']$/g, '');

      if (inTools) {
        if (key === 'name') {
          lastTool = { name: value, title: value, cmd: '', risk: 'write' };
          current.tools.push(lastTool);
        } else if (lastTool) {
          if (key === 'title') lastTool.title = value;
          else if (key === 'cmd') lastTool.cmd = value;
          else if (key === 'risk') lastTool.risk = value as ToolDecl['risk'];
        }
      } else {
        switch (key) {
          case 'type': current.type = value as Connector['type']; break;
          case 'path': current.path = value.replace(/^~/, os.homedir()); break;
          case 'env_path': current.envPath = value.replace(/^~/, os.homedir()); break;
          case 'version_cmd': current.versionCmd = value; break;
          case 'doctor_cmd': current.doctorCmd = value; break;
          case 'enabled': current.enabled = value !== 'false'; break;
        }
      }
    }
  }
  if (current) connectors.push(current);
  return connectors;
}

export async function loadRegistry(): Promise<Connector[]> {
  try {
    const content = await fs.promises.readFile(REGISTRY_PATH, 'utf8');
    return parseRegistry(content);
  } catch {
    return [];
  }
}

/** 原子写入（临时文件 + rename） */
export async function atomicWrite(filePath: string, content: string): Promise<void> {
  await fs.promises.mkdir(path.dirname(filePath), { recursive: true });
  const tmp = filePath + '.tmp-' + Date.now();
  await fs.promises.writeFile(tmp, content, 'utf8');
  await fs.promises.rename(tmp, filePath);
}

/** 追加条目到注册表（幂等：已存在同名连接器则跳过） */
export async function appendConnector(entry: string): Promise<'added' | 'exists'> {
  let content = '';
  try {
    content = await fs.promises.readFile(REGISTRY_PATH, 'utf8');
  } catch {
    content = '---\nversion: 1\n---\n\n';
  }
  const name = (entry.match(/^## (.+)$/m) || ['', ''])[1].trim();
  if (name && content.includes(`## ${name}\n`)) return 'exists';
  if (!content.endsWith('\n')) content += '\n';
  content += '\n' + entry + '\n';
  await atomicWrite(REGISTRY_PATH, content);
  return 'added';
}

/** 追加自检条目到 doctor 脚本（幂等） */
export async function appendDoctorEntry(marker: string, line: string): Promise<void> {
  let content = '';
  try {
    content = await fs.promises.readFile(DOCTOR_PATH, 'utf8');
  } catch {
    content = DOCTOR_TEMPLATE;
  }
  if (content.includes(marker)) return;
  content = content.replace('# >>> connectors', `# >>> connectors\n${line}`);
  await atomicWrite(DOCTOR_PATH, content);
  await fs.promises.chmod(DOCTOR_PATH, 0o755);
}
