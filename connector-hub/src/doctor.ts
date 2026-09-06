import * as vscode from 'vscode';
import { execFile } from 'child_process';
import { Connector, DOCTOR_PATH } from './registry';
export type { Connector } from './registry';

export interface HealthResult {
  name: string;
  ok: boolean;
  detail: string;
}

function run(cmd: string, args: string[], envPath?: string, timeout = 15_000): Promise<string> {
  return new Promise((resolve, reject) => {
    execFile(cmd, args, {
      timeout,
      env: { ...process.env, PATH: `${envPath ?? ''}:${process.env.PATH ?? ''}` }
    }, (err, stdout) => (err ? reject(err) : resolve(stdout)));
  });
}

/** 单连接器健康检查：优先 doctor_cmd，退化到 version_cmd，再退化到文件存在性 */
export async function checkConnector(c: Connector): Promise<HealthResult> {
  try {
    if (c.doctorCmd) {
      const parts = c.doctorCmd.split(/\s+/);
      const out = await run(parts[0], parts.slice(1), c.envPath);
      return { name: c.name, ok: true, detail: out.trim().split('\n')[0] || 'ok' };
    }
    if (c.versionCmd) {
      const parts = c.versionCmd.split(/\s+/);
      const out = await run(parts[0], parts.slice(1), c.envPath);
      return { name: c.name, ok: true, detail: out.trim().split('\n')[0] || 'ok' };
    }
    await vscode.workspace.fs.stat(vscode.Uri.file(c.path));
    return { name: c.name, ok: true, detail: 'binary exists' };
  } catch (e) {
    return { name: c.name, ok: false, detail: e instanceof Error ? e.message.split('\n')[0] : String(e) };
  }
}

/** 全量 doctor：跑服务器上的 connector-doctor.sh（若存在），否则逐个检查 */
export async function runDoctor(connectors: Connector[]): Promise<HealthResult[]> {
  try {
    await vscode.workspace.fs.stat(vscode.Uri.file(DOCTOR_PATH));
    const out = await run(DOCTOR_PATH, []);
    const results: HealthResult[] = [];
    for (const line of out.split('\n')) {
      const m = line.match(/^([✅❌])\s+(.+)$/);
      if (m) results.push({ name: m[2].trim(), ok: m[1] === '✅', detail: m[1] === '✅' ? 'ok' : 'failed' });
    }
    if (results.length) return results;
  } catch { /* fallthrough */ }
  return Promise.all(connectors.map(checkConnector));
}
