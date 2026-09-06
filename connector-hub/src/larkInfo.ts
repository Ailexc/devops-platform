import { execFile } from 'child_process';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';
import * as vscode from 'vscode';
import { runJson } from './larkAuth';
import { Risk } from './tools/base';

const LARK_BIN = `${os.homedir()}/.npm-global/bin/lark-cli`;
const ENV_PATH = `${os.homedir()}/.npm-global/bin`;

export interface SkillInfo {
  name: string;
  description: string;
  version: string;
  cliHelp?: string;
}

export interface DomainInfo {
  name: string;
  description: string;
}

export interface UpdateInfo {
  current?: string;
  latest?: string;
  hasUpdate: boolean;
  method?: string;
  error?: string;
}

export interface InstallInfo {
  binPath: string;
  realPath?: string;
  pkgDir?: string;
}

/** 安装位置：符号链接 + 真实路径 + 包目录 */
export async function getInstallInfo(): Promise<InstallInfo> {
  const binPath = LARK_BIN;
  const info: InstallInfo = { binPath };
  try {
    const real = await fs.promises.realpath(binPath);
    info.realPath = real;
    // ~/.npm-global/lib/node_modules/@larksuite/cli/scripts/run.js → 包目录
    const m = real.match(/^(.+\/node_modules\/@larksuite\/cli)\//);
    if (m) info.pkgDir = m[1];
  } catch { /* binary missing */ }
  return info;
}

/** CLI 命令域列表：解析 `lark-cli --help` 的 "Lark domains" 段 */
export async function getDomains(): Promise<DomainInfo[]> {
  try {
    const out = await runJson(['--help'], 15_000);
    const raw = typeof out.raw === 'string' ? out.raw : '';
    const domains: DomainInfo[] = [];
    const lines = raw.split('\n');
    let inSection = false;
    for (const line of lines) {
      if (/^Lark domains:/.test(line)) { inSection = true; continue; }
      if (inSection) {
        if (/^\s*$/.test(line) || /^[A-Z]/.test(line.trim())) { inSection = false; continue; }
        const m = line.trim().match(/^(\S+)\s+(.+)$/);
        if (m) domains.push({ name: m[1], description: m[2] });
      }
    }
    return domains;
  } catch {
    return [];
  }
}

/** 内置 Skills：`skills list --json` */
export async function getSkills(): Promise<SkillInfo[]> {
  try {
    const out = await runJson(['skills', 'list'], 20_000);
    const skills = Array.isArray(out?.skills) ? out.skills as Record<string, unknown>[] : [];
    return skills.map(s => ({
      name: String(s.name ?? ''),
      description: String(s.description ?? '').slice(0, 120),
      version: String(s.version ?? ''),
      cliHelp: (s.metadata as Record<string, unknown> | undefined)?.cliHelp as string | undefined
    })).filter(s => s.name);
  } catch {
    return [];
  }
}

/** 更新检查：`update --json`（只检查不升级）。实测字段：action/current_version/latest_version/ok */
export async function checkUpdate(): Promise<UpdateInfo> {
  try {
    const out = await runJson(['update', '--json'], 30_000);
    const current = typeof out.current_version === 'string' ? out.current_version : undefined;
    const latest = typeof out.latest_version === 'string' ? out.latest_version : undefined;
    const action = typeof out.action === 'string' ? out.action : '';
    const hasUpdate = action === 'update_available' || (!!current && !!latest && current !== latest);
    return {
      current, latest, hasUpdate,
      method: typeof out.action === 'string' ? out.action : undefined
    };
  } catch (e) {
    return { hasUpdate: false, error: e instanceof Error ? e.message.slice(0, 100) : String(e) };
  }
}

/** 读取某个 skill 的 SKILL.md（点击查看详情用） */
export async function readSkill(name: string): Promise<string | undefined> {
  return new Promise(resolve => {
    execFile(LARK_BIN, ['skills', 'read', name], { timeout: 15_000, env: { ...process.env, PATH: `${ENV_PATH}:${process.env.PATH ?? ''}` }, maxBuffer: 4 * 1024 * 1024 }, (err, stdout) => {
      resolve(err ? undefined : stdout.slice(0, 8000));
    });
  });
}

/** Copilot 工具卡片信息（运行时从 vscode.lm.tools 读取） */
export interface ToolCardInfo {
  name: string;
  description: string;
  params: string[];        // 从 inputSchema.properties 提取的参数名
  required: string[];
  registered: boolean;     // 是否已在 vscode.lm.tools 中
}

/** CLI 域卡片信息（--help 解析 + 关联 skill） */
export interface DomainCardInfo {
  name: string;
  description: string;
  shortcuts: string[];     // +create 等 + 命令
  skillName?: string;      // 关联的内置 skill
  skillVersion?: string;
}

/** 从 vscode.lm.tools 提取本插件注册的工具卡片信息 */
export function getToolCards(expected: string[]): ToolCardInfo[] {
  const lmTools = vscode.lm.tools;
  return expected.map(name => {
    const t = lmTools.find(x => x.name === name);
    if (!t) return { name, description: '未注册', params: [], required: [], registered: false };
    const props = (t.inputSchema as { properties?: Record<string, unknown> } | undefined)?.properties ?? {};
    const required = ((t.inputSchema as { required?: string[] } | undefined)?.required) ?? [];
    return {
      name,
      description: t.description,
      params: Object.keys(props),
      required,
      registered: true
    };
  });
}

/** 解析单个域的 + 快捷命令列表（跑 <domain> --help） */
function parseDomainShortcuts(helpText: string): string[] {
  const out: string[] = [];
  for (const line of helpText.split('\n')) {
    const m = line.trim().match(/^\+(\S+)\s+/);
    if (m) out.push('+' + m[1]);
  }
  return out;
}

function runHelp(domain: string): Promise<string> {
  return new Promise(resolve => {
    execFile(LARK_BIN, [domain, '--help'], { timeout: 15_000, env: { ...process.env, PATH: `${ENV_PATH}:${process.env.PATH ?? ''}` }, maxBuffer: 2 * 1024 * 1024 }, (err, stdout) => resolve(err ? '' : stdout));
  });
}

/** 域卡片：并行解析各域 --help，并按 skills list 的 cliHelp 字段关联 skill */
export async function getDomainCards(domains: DomainInfo[], skills: SkillInfo[]): Promise<DomainCardInfo[]> {
  // cliHelp 形如 "lark-cli docs --help; lark-cli mindnotes --help" → 域名 → skill 映射
  const domainToSkill = new Map<string, { name: string; version: string }>();
  for (const s of skills) {
    if (!s.cliHelp) continue;
    for (const seg of s.cliHelp.split(';')) {
      const m = seg.trim().match(/^lark-cli\s+(\S+)\s+/);
      if (m) domainToSkill.set(m[1], { name: s.name, version: s.version });
    }
  }
  const cards = await Promise.all(domains.map(async d => {
    const help = await runHelp(d.name);
    return {
      name: d.name,
      description: d.description,
      shortcuts: parseDomainShortcuts(help),
      skillName: domainToSkill.get(d.name)?.name,
      skillVersion: domainToSkill.get(d.name)?.version
    };
  }));
  return cards;
}
