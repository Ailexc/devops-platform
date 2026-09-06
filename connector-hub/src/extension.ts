import * as vscode from 'vscode';
import { loadRegistry, REGISTRY_PATH, appendConnector, appendDoctorEntry, Connector } from './registry';
import { buildLarkTools } from './tools/lark';
import { ToolRegistrar } from './toolRegistrar';
import { runDoctor, HealthResult } from './doctor';
import { DashboardView } from './webview/dashboardView';
import { LARK_ENTRY, LARK_DOCTOR_LINE } from './registryEntry';

let healthCache = new Map<string, HealthResult>();
let statusBarItem: vscode.StatusBarItem;

export async function activate(context: vscode.ExtensionContext) {
  // 1. 注册表（唯一事实来源）
  let connectors = await loadRegistry();

  // 2. 工具注册（实现与 package.json languageModelTools 声明配对）
  const registrar = new ToolRegistrar();
  registrar.registerAll(buildLarkTools());
  context.subscriptions.push(registrar);

  // 3. Webview 仪表盘（替代 TreeView）
  const dashboard = new DashboardView(context);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(DashboardView.VIEW_ID, dashboard, {
      webviewOptions: { retainContextWhenHidden: true }
    })
  );

  // 4. 状态栏徽标
  statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 50);
  statusBarItem.command = 'connectorHub.focus';
  context.subscriptions.push(statusBarItem);

  // 5. 命令
  context.subscriptions.push(
    vscode.commands.registerCommand('connectorHub.refresh', async () => {
      connectors = await loadRegistry();
      healthCache.clear();
      await dashboard.refresh(connectors, Object.fromEntries(healthCache));
      await updateStatusBar(connectors);
    }),

    vscode.commands.registerCommand('connectorHub.doctor', async (item?: { connector: Connector }) => {
      const targets = item?.connector ? [item.connector] : connectors;
      const results = await runDoctor(targets);
      for (const r of results) healthCache.set(r.name, r);
      await dashboard.refresh(connectors, Object.fromEntries(healthCache));
      await updateStatusBar(connectors);
      const summary = results.map(r => `${r.ok ? '✅' : '❌'} ${r.name}: ${r.detail}`).join('\n');
      void vscode.window.showInformationMessage(`连接器健康检查\n${summary}`, { modal: false });
    }),

    vscode.commands.registerCommand('connectorHub.showDetails', async (item?: { connector: Connector }) => {
      const c = item?.connector;
      if (!c) return;
      const tools = c.tools.length
        ? c.tools.map(t => `- \`${t.name}\` (${t.risk}) ${t.title}`).join('\n')
        : '_无工具声明_';
      await vscode.window.showInformationMessage(
        `**${c.name}**\n\n类型: ${c.type}\n路径: \`${c.path}\`\n启用: ${c.enabled}\n\n工具:\n${tools}`,
        { modal: true }
      );
    }),

    vscode.commands.registerCommand('connectorHub.openRegistry', async () => {
      try {
        await vscode.window.showTextDocument(vscode.Uri.file(REGISTRY_PATH));
      } catch {
        void vscode.window.showWarningMessage(`注册表不存在: ${REGISTRY_PATH}，请在面板中执行"一键修复"`);
      }
    }),

    vscode.commands.registerCommand('connectorHub.initRegistry', async () => {
      const pick = await vscode.window.showQuickPick(['lark-cli（飞书官方 CLI）'], { placeHolder: '选择要注册的连接器' });
      if (pick !== 'lark-cli（飞书官方 CLI）') return;
      const added = await appendConnector(LARK_ENTRY);
      await appendDoctorEntry('lark-cli', LARK_DOCTOR_LINE);
      await vscode.commands.executeCommand('connectorHub.refresh');
      void vscode.window.showInformationMessage(added === 'added' ? '已注册 lark-cli（注册表 + doctor）' : 'lark-cli 已在注册表中，跳过');
    }),

    vscode.commands.registerCommand('connectorHub.focus', async () => {
      await vscode.commands.executeCommand('connectorHub.list.focus');
    })
  );

  // 6. 启动时：轻量健康检查 + 首次刷新（不阻塞）
  void (async () => {
    const results = await runDoctor(connectors);
    for (const r of results) healthCache.set(r.name, r);
    await dashboard.refresh(connectors, Object.fromEntries(healthCache));
    await updateStatusBar(connectors);
  })();

  // 7. 注册表文件变化 → 自动刷新
  const path = await import('path');
  const watcher = vscode.workspace.createFileSystemWatcher(
    new vscode.RelativePattern(vscode.Uri.file(path.dirname(REGISTRY_PATH)), 'connectors.md')
  );
  context.subscriptions.push(
    watcher,
    watcher.onDidChange(() => vscode.commands.executeCommand('connectorHub.refresh')),
    watcher.onDidCreate(() => vscode.commands.executeCommand('connectorHub.refresh')),
    watcher.onDidDelete(() => vscode.commands.executeCommand('connectorHub.refresh'))
  );
}

export function deactivate() { /* registrar 随 subscriptions 自动 dispose */ }

async function updateStatusBar(connectors: Connector[]): Promise<void> {
  if (!statusBarItem) return;
  if (!connectors.length) {
    statusBarItem.text = '$(link) Connectors';
    statusBarItem.tooltip = 'Connector Hub：注册表为空';
    statusBarItem.show();
    return;
  }
  const okCount = connectors.filter(c => healthCache.get(c.name)?.ok).length;
  statusBarItem.text = `$(link) ${okCount}/${connectors.length}`;
  statusBarItem.tooltip = `Connector Hub：${okCount}/${connectors.length} 个连接器健康`;
  statusBarItem.show();
}
