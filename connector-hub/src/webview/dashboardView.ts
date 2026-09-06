import * as vscode from 'vscode';
import { renderDashboard, DashboardState } from './dashboard';
import { getIdentity, getVersion, startAppSetup, extractSetupUrl, killProcessGroup, startLogin, completeLoginInBackground, qrcodeDataUrl, pollUntil, SetupSession } from '../larkAuth';
import { checkInjection, fixInjection } from '../injection';
import { REGISTRY_PATH } from '../registry';
import { Connector } from '../registry';
import { HealthResult } from '../doctor';
import { getInstallInfo, getDomains, getSkills, checkUpdate, readSkill, getToolCards, getDomainCards } from '../larkInfo';

const EXPECTED_TOOLS = ['lark_doc_create', 'lark_doc_update', 'lark_doc_fetch', 'lark_doc_search', 'lark_md_create', 'lark_md_overwrite', 'lark_md_fetch'];

type AuthPhase = 'idle' | 'setting-up' | 'authorizing';

export class DashboardView implements vscode.WebviewViewProvider {
  public static readonly VIEW_ID = 'connectorHub.list';
  private view?: vscode.WebviewView;
  private state: DashboardState = { health: {}, connectors: [] };
  private setupSession?: SetupSession;
  private loginDeviceCode?: string;
  private pollers: Array<{ cancel: () => void }> = [];

  constructor(private readonly context: vscode.ExtensionContext) {}

  resolveWebviewView(view: vscode.WebviewView): void {
    this.view = view;
    view.webview.options = { enableScripts: true, localResourceRoots: [] };
    view.webview.html = this.html();
    view.webview.onDidReceiveMessage(msg => void this.onMessage(msg));
    view.onDidDispose(() => this.cancelPollers());
  }

  /** 外部刷新入口（extension.ts 调用）。保留 banner 与授权流程状态，只更新数据 */
  async refresh(connectors: Connector[], health: Record<string, HealthResult>): Promise<void> {
    this.state.connectors = connectors;
    this.state.health = health;
    this.state.version = await getVersion();
    this.state.identity = await getIdentity();
    this.state.injection = await checkInjection();
    // 深度信息（安装位置/命令域/skills/更新）——并行拉取，失败不阻塞
    if (!this.state.install) this.state.install = await getInstallInfo();
    if (!this.state.domains) this.state.domains = await getDomains();
    if (!this.state.skills) this.state.skills = await getSkills();
    if (!this.state.update) this.state.update = await checkUpdate();
    // 卡片数据（工具运行时状态 + 域快捷命令解析）
    this.state.toolCards = getToolCards(EXPECTED_TOOLS);
    if (this.state.domains.length && !this.state.domainCards) {
      this.state.domainCards = await getDomainCards(this.state.domains, this.state.skills);
    }
    this.paint();
  }

  /** 清除 banner（前端 8 秒后自动调用） */
  private async dismissBanner(): Promise<void> {
    if (this.state.banner) {
      this.state.banner = undefined;
      this.paint();
    }
  }

  private async onMessage(msg: { cmd?: string; name?: string }): Promise<void> {
    switch (msg?.cmd) {
      case 'setupApp': await this.setupApp(); break;
      case 'startLogin': await this.startLoginFlow(); break;
      case 'copyUrl': if (this.state.authFlow?.url) await vscode.env.clipboard.writeText(this.state.authFlow.url); break;
      case 'copyBinPath': if (this.state.install?.binPath) await vscode.env.clipboard.writeText(this.state.install.binPath); break;
      case 'copyToolRef': if (msg.name) await vscode.env.clipboard.writeText('#' + msg.name.replace(/_/g, '')); break;
      case 'openRegistry': {
        try {
          await vscode.window.showTextDocument(vscode.Uri.file(REGISTRY_PATH), { preview: true });
        } catch {
          void vscode.window.showWarningMessage(`注册表不存在: ${REGISTRY_PATH}，请先执行"一键修复"`);
        }
        break;
      }
      case 'openDoctor': {
        try {
          await vscode.window.showTextDocument(vscode.Uri.file(require('os').homedir() + '/tools/connector-doctor.sh'), { preview: true });
        } catch {
          void vscode.window.showWarningMessage('doctor 脚本不存在，请先执行"一键修复"');
        }
        break;
      }
      case 'showToolDeps': {
        const pkgUri = vscode.Uri.joinPath(this.context.extensionUri, 'package.json');
        const doc = await vscode.workspace.openTextDocument(pkgUri);
        await vscode.window.showTextDocument(doc, { preview: true, selection: new vscode.Range(0, 0, 0, 0) });
        void vscode.window.showInformationMessage('工具声明在 package.json 的 languageModelTools 节；实现在源码 src/tools/lark.ts');
        break;
      }
      case 'dismissBanner': await this.dismissBanner(); break;
      case 'doctor': await vscode.commands.executeCommand('connectorHub.doctor'); break;
      case 'checkUpdate': {
        void vscode.window.withProgress(
          { location: vscode.ProgressLocation.Notification, title: '检查 lark-cli 更新…' },
          () => checkUpdate().then(async u => {
            this.state.update = u;
            this.paint();
            void vscode.window.showInformationMessage(u.hasUpdate ? `有新版：${u.latest}（当前 ${u.current}）` : `已是最新版本 ${u.current ?? ''}`);
          })
        );
        break;
      }
      case 'readSkill': {
        if (!msg.name) break;
        const content = await readSkill(msg.name);
        if (content) {
          const doc = await vscode.workspace.openTextDocument({ content, language: 'markdown' });
          await vscode.window.showTextDocument(doc, { preview: true });
        } else {
          void vscode.window.showWarningMessage(`无法读取 skill: ${msg.name}`);
        }
        break;
      }
      case 'fixInjection': {
        const actions = await fixInjection();
        void vscode.window.showInformationMessage(actions.join('；'));
        await this.refreshAll();
        break;
      }
    }
  }

  /** 一键创建应用：后台跑 config init --new，提取 URL → 二维码 → 轮询 whoami */
  private async setupApp(): Promise<void> {
    this.cancelPollers();
    this.setupSession = startAppSetup();
    this.state.authFlow = { phase: 'setting-up', message: '正在生成配置二维码…' };
    this.paint();

    // 提取 URL（最多等 15s）
    const urlPoll = pollUntil<string | undefined>(
      async () => {
        const url = await extractSetupUrl(this.setupSession!.logFile);
        return url ?? undefined;
      },
      1000, 15_000
    );
    this.pollers.push(urlPoll);
    const url = await urlPoll.promise;
    if (!url) {
      this.state.authFlow = { phase: 'idle' };
      this.paint();
      void vscode.window.showErrorMessage('未能获取配置链接，请查看终端手动执行 lark-cli config init --new');
      return;
    }

    const qr = await qrcodeDataUrl(url);
    this.state.authFlow = { phase: 'setting-up', url, qrDataUrl: qr, message: '用飞书 App 扫码完成应用创建' };
    this.paint();

    // 轮询 whoami（扫码成功后 configured 变 true），最长 5 分钟
    const donePoll = pollUntil(
      async () => {
        const id = await getIdentity();
        return id.configured ? id : undefined;
      },
      3000, 5 * 60_000
    );
    this.pollers.push(donePoll);
    const identity = await donePoll.promise;
    killProcessGroup(this.setupSession.pid);
    if (identity) {
      this.state.authFlow = { phase: 'idle' };
      this.state.banner = { kind: 'success', text: '应用创建成功！还差一步：点击下方「扫码授权」开通文档权限' };
      await this.refreshAll();
      void vscode.window.showInformationMessage('应用创建成功！接下来请扫码授权文档权限');
    } else {
      this.state.authFlow = { phase: 'setting-up', url, qrDataUrl: qr, message: '等待扫码中…（超时后可重试）' };
      this.paint();
    }
  }

  /** 扫码授权：--no-wait 拿 URL → 二维码 → 后台 --device-code 完成换取 → 轮询 auth status */
  private async startLoginFlow(): Promise<void> {
    this.cancelPollers();
    this.state.authFlow = { phase: 'authorizing', message: '正在发起授权…' };
    this.paint();

    const start = await startLogin(['docs', 'drive', 'markdown']);
    if (!start.url) {
      this.state.authFlow = { phase: 'idle' };
      this.paint();
      void vscode.window.showErrorMessage(`发起授权失败: ${start.error ?? '未知错误'}`);
      return;
    }
    this.loginDeviceCode = start.deviceCode;
    const qr = await qrcodeDataUrl(start.url);
    this.state.authFlow = { phase: 'authorizing', url: start.url, qrDataUrl: qr, message: '用飞书 App 扫码完成授权' };
    this.paint();

    // 后台完成令牌换取
    if (this.loginDeviceCode) completeLoginInBackground(this.loginDeviceCode);

    // 轮询授权状态
    const donePoll = pollUntil(
      async () => {
        const id = await getIdentity();
        return id.authorized ? id : undefined;
      },
      3000, 5 * 60_000
    );
    this.pollers.push(donePoll);
    const identity = await donePoll.promise;
    if (identity) {
      this.state.authFlow = { phase: 'idle' };
      this.state.banner = { kind: 'success', text: `授权成功！${identity.user ? '欢迎，' + identity.user : ''} 现在可以在 Copilot 中直接操作飞书文档了` };
      await this.refreshAll();
      void vscode.window.showInformationMessage(`授权成功！${identity.user ? '用户: ' + identity.user : ''}`);
    } else {
      this.state.authFlow = { phase: 'authorizing', url: start.url, qrDataUrl: qr, message: '等待扫码中…（超时后可重试）' };
      this.paint();
    }
  }

  private async refreshAll(): Promise<void> {
    await vscode.commands.executeCommand('connectorHub.refresh');
  }

  private cancelPollers(): void { this.pollers.forEach(p => p.cancel()); this.pollers = []; }

  private paint(): void {
    if (!this.view) return;
    this.view.webview.html = this.html();
  }

  private html(): string {
    const nonce = Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2);
    return renderDashboard(this.state, this.view!.webview.cspSource, nonce);
  }
}
