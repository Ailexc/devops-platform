import { execFile, spawn } from 'child_process';
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';

const LARK_BIN = `${os.homedir()}/.npm-global/bin/lark-cli`;
const ENV_PATH = `${os.homedir()}/.npm-global/bin`;

function env(): NodeJS.ProcessEnv {
  return { ...process.env, PATH: `${ENV_PATH}:${process.env.PATH ?? ''}` };
}

/** 运行 lark-cli 并解析 JSON 输出（失败时返回 {raw} 兜底） */
export function runJson(args: string[], timeout = 20_000): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    execFile(LARK_BIN, args, { timeout, env: env(), maxBuffer: 8 * 1024 * 1024 }, (err, stdout) => {
      if (err) { reject(err); return; }
      try { resolve(JSON.parse(stdout)); } catch { resolve({ raw: stdout }); }
    });
  });
}

/** 在对象中递归查找第一个命中的字符串字段 */
function pickString(obj: unknown, keys: string[], depth = 0): string | undefined {
  if (depth > 4 || obj === null || typeof obj !== 'object') return undefined;
  const rec = obj as Record<string, unknown>;
  for (const k of keys) {
    const v = rec[k];
    if (typeof v === 'string' && v) return v;
    if (typeof v === 'number') return String(v);
  }
  for (const v of Object.values(rec)) {
    const hit = pickString(v, keys, depth + 1);
    if (hit) return hit;
  }
  return undefined;
}

export interface IdentityInfo {
  configured: boolean;
  authorized: boolean;
  user?: string;
  app?: string;
  tenant?: string;
  expiresAt?: string;
  scopes?: string[];
}

/**
 * 聚合身份信息。
 * 实测返回结构（v1.0.93）：
 *  - whoami 成功时无 ok 字段：{ profile, appId, brand, identity, available, tokenStatus, onBehalfOf: { userName, openId } }
 *  - auth status 成功时无 ok 字段：{ appId, identities: { bot: {...}, user: { status, userName, tokenStatus, scope, expiresAt } } }
 *  - 未配置时：{ ok: false, error: { type: 'config', subtype: 'not_configured' } }
 */
export async function getIdentity(): Promise<IdentityInfo> {
  const info: IdentityInfo = { configured: false, authorized: false };

  // 1. whoami：available/tokenStatus 判定授权
  try {
    const w = await runJson(['whoami']);
    const available = w?.available === true;
    const tokenStatus = w?.tokenStatus === 'ready';
    if (available || tokenStatus) {
      info.configured = true;
      info.authorized = true;
      const onBehalf = (w?.onBehalfOf ?? {}) as Record<string, unknown>;
      info.user = (typeof onBehalf.userName === 'string' && onBehalf.userName) || undefined;
      info.app = typeof w?.appId === 'string' ? w.appId : undefined;
      info.tenant = typeof w?.brand === 'string' ? w.brand : undefined;
      return info;
    }
    // whoami 有响应但未就绪 → 已配置未授权
    if (w?.profile || w?.appId) {
      info.configured = true;
    }
  } catch { /* not configured or failed */ }

  // 2. auth status 兜底：identities.user.status === 'ready'
  try {
    const st = await runJson(['auth', 'status', '--json']);
    const user = (st?.identities as Record<string, unknown> | undefined)?.user as Record<string, unknown> | undefined;
    if (user?.status === 'ready' && user?.available === true) {
      info.configured = true;
      info.authorized = true;
      info.user = typeof user.userName === 'string' ? user.userName : undefined;
      info.app = typeof st?.appId === 'string' ? st.appId : undefined;
      info.expiresAt = typeof user.expiresAt === 'string' ? user.expiresAt : undefined;
      info.scopes = typeof user.scope === 'string' ? user.scope.split(/\s+/) : undefined;
      return info;
    }
    if (st?.appId) info.configured = true;
  } catch { /* ignore */ }

  // 3. config show 判定"已配置"（应用已建但未授权）
  try {
    const cfg = await runJson(['config', 'show']);
    if (cfg?.appId || cfg?.profile) info.configured = true;
  } catch { /* not configured */ }

  return info;
}

/** 获取 CLI 版本号 */
export async function getVersion(): Promise<string | undefined> {
  try {
    const out = await runJson(['--version']);
    const raw = typeof out.raw === 'string' ? out.raw : JSON.stringify(out);
    const m = raw.match(/(\d+\.\d+\.\d+)/);
    return m?.[1];
  } catch { return undefined; }
}

// ---------- 应用创建（config init --new，阻塞式，后台跑 + 日志提取 URL） ----------

export interface SetupSession {
  pid: number;
  logFile: string;
}

export function startAppSetup(): SetupSession {
  const logFile = path.join(os.tmpdir(), `connector-hub-init-${Date.now()}.log`);
  const out = fs.openSync(logFile, 'a');
  const child = spawn(LARK_BIN, ['config', 'init', '--new', '--lang', 'zh'], {
    env: env(),
    detached: true,
    stdio: ['ignore', out, out]
  });
  child.unref();
  fs.closeSync(out);
  return { pid: child.pid ?? 0, logFile };
}

export async function extractSetupUrl(logFile: string): Promise<string | undefined> {
  try {
    const content = await fs.promises.readFile(logFile, 'utf8');
    const m = content.match(/https:\/\/open\.feishu\.cn\/page\/cli\?\S+/);
    return m?.[0];
  } catch { return undefined; }
}

export function killProcessGroup(pid: number): void {
  try { process.kill(-pid, 'SIGTERM'); } catch { /* already gone */ }
}

// ---------- 用户授权（Device Flow：--no-wait 拿 URL，--device-code 后台完成） ----------

export interface LoginStart {
  url?: string;
  deviceCode?: string;
  error?: string;
}

export async function startLogin(domains: string[]): Promise<LoginStart> {
  try {
    const out = await runJson(['auth', 'login', '--no-wait', '--json', '--domain', domains.join(',')]);
    const s = JSON.stringify(out);
    const url = s.match(/https:\/\/[^"\\\s]+/)?.[0];
    const deviceCode = pickString(out, ['device_code', 'deviceCode', 'user_code', 'userCode']);
    if (!url) return { error: '未从输出中解析到验证 URL', raw: JSON.stringify(out).slice(0, 500) } as LoginStart;
    return { url, deviceCode };
  } catch (e) {
    return { error: e instanceof Error ? e.message : String(e) };
  }
}

/** 后台运行 --device-code 完成令牌换取（CLI 自己轮询，成功后 token 落盘） */
export function completeLoginInBackground(deviceCode: string): { pid: number; logFile: string } {
  const logFile = path.join(os.tmpdir(), `connector-hub-login-${Date.now()}.log`);
  const out = fs.openSync(logFile, 'a');
  const child = spawn(LARK_BIN, ['auth', 'login', '--device-code', deviceCode], {
    env: env(),
    detached: true,
    stdio: ['ignore', out, out]
  });
  child.unref();
  fs.closeSync(out);
  return { pid: child.pid ?? 0, logFile };
}

// ---------- 二维码 ----------

export async function qrcodeDataUrl(url: string): Promise<string | undefined> {
  const file = path.join(os.tmpdir(), `connector-hub-qr-${Date.now()}.png`);
  try {
    await new Promise<void>((resolve, reject) => {
      execFile(LARK_BIN, ['auth', 'qrcode', url, '-o', file, '--size', '256'], { timeout: 15_000, env: env() }, err => (err ? reject(err) : resolve()));
    });
    const buf = await fs.promises.readFile(file);
    return `data:image/png;base64,${buf.toString('base64')}`;
  } catch {
    return undefined;
  }
}

// ---------- 轮询工具 ----------

export function pollUntil<T>(
  fn: () => Promise<T | undefined>,
  intervalMs: number,
  timeoutMs: number
): { promise: Promise<T | undefined>; cancel: () => void } {
  let timer: NodeJS.Timeout | undefined;
  let cancelled = false;
  const promise = new Promise<T | undefined>(resolve => {
    const tick = async () => {
      if (cancelled) { resolve(undefined); return; }
      try {
        const r = await fn();
        if (r !== undefined) { resolve(r); return; }
      } catch { /* keep polling */ }
      timer = setTimeout(tick, intervalMs);
    };
    void tick();
    setTimeout(() => { if (!cancelled) { cancelled = true; resolve(undefined); } }, timeoutMs);
  });
  return { promise, cancel: () => { cancelled = true; if (timer) clearTimeout(timer); } };
}
