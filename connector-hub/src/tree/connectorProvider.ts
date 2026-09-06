import * as vscode from 'vscode';
import { Connector, HealthResult } from '../doctor';

export class ConnectorItem extends vscode.TreeItem {
  constructor(public readonly connector: Connector, public readonly health?: HealthResult) {
    super(connector.name, vscode.TreeItemCollapsibleState.None);
    const ok = health?.ok;
    this.description = health
      ? `${ok ? '✅' : '❌'} ${health.detail}`
      : connector.enabled ? '未检查' : '已禁用';
    this.tooltip = new vscode.MarkdownString(
      `**${connector.name}**\n\n- 类型: ${connector.type}\n- 路径: \`${connector.path}\`\n- 工具数: ${connector.tools.length}\n- 启用: ${connector.enabled}`
    );
    this.contextValue = 'connector';
    this.iconPath = new vscode.ThemeIcon(
      ok === undefined ? 'circle-outline' : ok ? 'pass' : 'error'
    );
  }
}

export class ConnectorProvider implements vscode.TreeDataProvider<ConnectorItem> {
  private _onDidChange = new vscode.EventEmitter<ConnectorItem | undefined | void>();
  readonly onDidChangeTreeData = this._onDidChange.event;

  constructor(
    private getConnectors: () => Connector[],
    private getHealth: (name: string) => HealthResult | undefined
  ) {}

  refresh(): void { this._onDidChange.fire(); }

  getTreeItem(el: ConnectorItem): vscode.TreeItem { return el; }

  getChildren(): ConnectorItem[] {
    return this.getConnectors().map(c => new ConnectorItem(c, this.getHealth(c.name)));
  }
}
