import * as fs from 'fs';
import * as vscode from 'vscode';
import { REGISTRY_PATH, DOCTOR_PATH, appendConnector, appendDoctorEntry } from './registry';
import { LARK_ENTRY, LARK_DOCTOR_LINE } from './registryEntry';

export interface CheckItem {
  id: string;
  label: string;
  ok: boolean;
  detail: string;
}

export interface InjectionReport {
  allOk: boolean;
  items: CheckItem[];
}

/** 三项注入一致性检查 */
export async function checkInjection(): Promise<InjectionReport> {
  const items: CheckItem[] = [];

  // 1. 注册表条目
  let registryOk = false;
  let registryDetail = '';
  try {
    const content = await fs.promises.readFile(REGISTRY_PATH, 'utf8');
    registryOk = content.includes('## lark-cli\n');
    registryDetail = registryOk ? '已注册' : '缺少 lark-cli 条目';
  } catch {
    registryDetail = '注册表文件不存在';
  }
  items.push({ id: 'registry', label: '注册表 (~/.agent/connectors.md)', ok: registryOk, detail: registryDetail });

  // 2. doctor 脚本条目
  let doctorOk = false;
  let doctorDetail = '';
  try {
    const content = await fs.promises.readFile(DOCTOR_PATH, 'utf8');
    doctorOk = content.includes('lark-cli');
    doctorDetail = doctorOk ? '已注入' : '缺少 lark-cli 自检条目';
  } catch {
    doctorDetail = 'doctor 脚本不存在';
  }
  items.push({ id: 'doctor', label: '自检脚本 (~/tools/connector-doctor.sh)', ok: doctorOk, detail: doctorDetail });

  // 3. 工具注册状态
  const toolNames = vscode.lm.tools.map(t => t.name);
  const expected = ['lark_doc_create', 'lark_doc_update', 'lark_doc_fetch', 'lark_doc_search', 'lark_md_create', 'lark_md_overwrite', 'lark_md_fetch'];
  const missing = expected.filter(n => !toolNames.includes(n));
  items.push({
    id: 'tools',
    label: 'Copilot 工具注册',
    ok: missing.length === 0,
    detail: missing.length === 0 ? `7/7 已注册` : `缺失: ${missing.join(', ')}`
  });

  return { allOk: items.every(i => i.ok), items };
}

/** 一键修复：补齐缺失项 */
export async function fixInjection(): Promise<string[]> {
  const actions: string[] = [];
  const report = await checkInjection();

  if (!report.items.find(i => i.id === 'registry')?.ok) {
    const r = await appendConnector(LARK_ENTRY);
    actions.push(r === 'added' ? '已写入注册表条目' : '注册表条目已存在');
  }
  if (!report.items.find(i => i.id === 'doctor')?.ok) {
    await appendDoctorEntry('lark-cli', LARK_DOCTOR_LINE);
    actions.push('已注入 doctor 自检条目');
  }
  if (!report.items.find(i => i.id === 'tools')?.ok) {
    actions.push('工具注册缺失——请重载窗口（Developer: Reload Window）后复查');
  }
  if (!actions.length) actions.push('全部就绪，无需修复');
  return actions;
}

/** 导出给 webview 用的注册表原始内容（只读展示） */
export async function readRegistryRaw(): Promise<string> {
  try { return await fs.promises.readFile(REGISTRY_PATH, 'utf8'); } catch { return ''; }
}
