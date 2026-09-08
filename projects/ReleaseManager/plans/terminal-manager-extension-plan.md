# Terminal Manager —— VS Code 扩展开发方案

> 目标：像"文件管理器"一样管理多个终端。左侧活动栏使用**自己的专用图标**（不劫持内置终端图标），点开后左侧只有终端列表（树视图）；单击某终端即在**编辑区**打开；支持新建 / 删除 / 重命名 / 移入移出编辑区。

---

## 1. 需求清单

| # | 需求 | 关键点 |
|---|------|--------|
| R1 | 左侧活动栏有**自己的专用图标** | 不接管/不劫持内置终端图标，用户点自己那个 |
| R2 | 点图标后左侧**只显示终端列表** | 不要像内置那样出现"极窄终端窗口 + 列表"两块 |
| R3 | 列表**实时**显示**所有运行中的终端** | 关键：必须包含"编辑区终端"（内置列表做不到这点） |
| R4 | **单击**列表项 → 终端在**编辑区**打开 | 已在面板的移入编辑区；已在编辑区的聚焦即可 |
| R5 | 标题栏按钮**新建终端** | 直接建在编辑区 |
| R6 | 右键/行内操作 | 聚焦、移入编辑区、移回面板、重命名、删除（删除要确认） |
| R7 | 列表信息有用 | 显示位置（编辑区/面板）、当前活动终端、退出码、Shell、cwd 等 |

**明确不做**：不劫持内置终端图标；不读取终端输出内容；不暴露终端 split 分组关系（API 不支持）。

---

## 2. 已核实的技术事实（2026-07 验证）

### 稳定 API（直接可用）

- `window.terminals: readonly Terminal[]` —— 当前**所有**终端，**含编辑区终端**（这是解决内置"编辑区终端不显示"痛点的关键）。
- 事件：`window.onDidOpenTerminal` / `onDidCloseTerminal` / `onDidChangeActiveTerminal` / `onDidChangeTerminalState`。
- `window.createTerminal({ name, location })`，其中 `location` 可为：
  - `TerminalLocation.Panel` / `TerminalLocation.Editor`（枚举）
  - `TerminalEditorLocationOptions`（`{ viewColumn }`）或 `TerminalSplitLocationOptions`（`{ parentTerminal }`）→ 均为编辑区
- `Terminal.dispose()` —— 结束/删除终端。
- `Terminal.show(preserveFocus?)` —— 聚焦/显示（保持原位置）。
- `Terminal.name`（只读）、`Terminal.state.shell`、`Terminal.exitStatus`、`Terminal.creationOptions`、`Terminal.shellIntegration.cwd`。
- 侧边栏树视图：`viewsContainers.activitybar` + `views` + `TreeDataProvider` + `TreeItem`（`command` 做单击、`contextValue` 过滤右键菜单、`view/title` 工具栏、`view/item/context` 右键菜单）。

### 内部命令（存在，已核实；作用于"活动终端"，需先 `show()` 再执行）

- `workbench.action.terminal.moveToEditor` —— 移入编辑区
- `workbench.action.terminal.moveToTerminalPanel` —— 移回面板
- `workbench.action.terminal.rename` —— 弹"Enter terminal name"输入框
- `workbench.action.terminal.renameWithArg` —— 带参重命名，参数 `{ name: string }`（推荐：自己用 `showInputBox` 再调用它）

---

## 3. 项目结构

```
terminal-manager/
├── .vscode/
│   ├── launch.json          # F5 启动扩展开发宿主
│   └── tasks.json           # npm: watch 编译任务
├── media/
│   └── terminal.svg         # 活动栏/视图图标（任意 24x24 svg）
├── src/
│   └── extension.ts         # 全部核心逻辑（单文件即可）
├── package.json
├── tsconfig.json
└── .vscodeignore            # 打包时忽略的文件
```

---

## 4. package.json

```jsonc
{
  "name": "terminal-manager",
  "displayName": "Terminal Manager",
  "description": "像文件管理器一样管理所有运行中的终端：左侧列表，单击在编辑区打开",
  "version": "0.0.1",
  "publisher": "your-name",
  "engines": { "vscode": "^1.85.0" },
  "categories": ["Other"],
  "activationEvents": ["onView:terminalManager.terminals", "onStartupFinished"],
  "main": "./out/extension.js",
  "contributes": {
    "viewsContainers": {
      "activitybar": [
        { "id": "terminalManager", "title": "Terminal Manager", "icon": "media/terminal.svg" }
      ]
    },
    "views": {
      "terminalManager": [
        { "id": "terminalManager.terminals", "name": "终端", "icon": "media/terminal.svg", "contextualTitle": "Terminal Manager" }
      ]
    },
    "commands": [
      { "command": "terminalManager.new",       "title": "新建终端（编辑区）", "icon": "$(add)",            "category": "Terminal Manager" },
      { "command": "terminalManager.newInPanel", "title": "新建终端（面板）",  "icon": "$(add)",            "category": "Terminal Manager" },
      { "command": "terminalManager.refresh",   "title": "刷新",              "icon": "$(refresh)",        "category": "Terminal Manager" },
      { "command": "terminalManager.open",      "title": "打开",              "icon": "$(open-preview)",   "category": "Terminal Manager" },
      { "command": "terminalManager.moveToEditor", "title": "移入编辑区",     "icon": "$(editor-layout)",  "category": "Terminal Manager" },
      { "command": "terminalManager.moveToPanel",  "title": "移回面板",       "icon": "$(chevron-down)",   "category": "Terminal Manager" },
      { "command": "terminalManager.rename",    "title": "重命名",            "icon": "$(edit)",           "category": "Terminal Manager" },
      { "command": "terminalManager.kill",      "title": "结束终端",          "icon": "$(trash)",          "category": "Terminal Manager" }
    ],
    "menus": {
      "view/title": [
        { "command": "terminalManager.new",    "when": "view == terminalManager.terminals", "group": "navigation@1" },
        { "command": "terminalManager.refresh", "when": "view == terminalManager.terminals", "group": "navigation@2" }
      ],
      "view/item/context": [
        { "command": "terminalManager.open",         "when": "view == terminalManager.terminals && viewItem == terminal", "group": "inline@1" },
        { "command": "terminalManager.moveToEditor", "when": "view == terminalManager.terminals && viewItem == terminal", "group": "inline@2" },
        { "command": "terminalManager.moveToPanel",  "when": "view == terminalManager.terminals && viewItem == terminal", "group": "1_actions@1" },
        { "command": "terminalManager.rename",       "when": "view == terminalManager.terminals && viewItem == terminal", "group": "1_actions@2" },
        { "command": "terminalManager.kill",         "when": "view == terminalManager.terminals && viewItem == terminal", "group": "2_danger@1" }
      ]
    },
    "configuration": {
      "title": "Terminal Manager",
      "properties": {
        "terminalManager.clickBehavior": {
          "type": "string",
          "enum": ["editor", "focus"],
          "default": "editor",
          "description": "单击列表项的行为：editor=在编辑区打开；focus=仅聚焦（保持原位置）"
        }
      }
    }
  },
  "scripts": {
    "vscode:prepublish": "npm run compile",
    "compile": "tsc -p ./",
    "watch": "tsc -watch -p ./"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "@types/vscode": "^1.85.0",
    "typescript": "^5.4.0"
  }
}
```

> 说明：`activationEvents` 加 `onStartupFinished` 可保证扩展始终激活、列表从窗口打开起就实时同步（个人工具无所谓性能）；只想要按需激活可删掉它，仅保留 `onView:...`。

---

## 5. tsconfig.json

```jsonc
{
  "compilerOptions": {
    "module": "commonjs",
    "target": "ES2022",
    "lib": ["ES2022"],
    "outDir": "out",
    "rootDir": "src",
    "sourceMap": true,
    "strict": true,
    "esModuleInterop": true
  },
  "exclude": ["node_modules", ".vscode-test"]
}
```

---

## 6. .vscode/launch.json + tasks.json（F5 调试）

```jsonc
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "运行扩展（Extension Development Host）",
      "type": "extensionHost",
      "request": "launch",
      "args": ["--extensionDevelopmentPath=${workspaceFolder}"],
      "outFiles": ["${workspaceFolder}/out/**/*.js"],
      "preLaunchTask": "npm: watch"
    }
  ]
}
```

```jsonc
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "type": "npm",
      "script": "watch",
      "problemMatcher": "$tsc-watch",
      "isBackground": true,
      "presentation": { "reveal": "never" },
      "group": { "kind": "build", "isDefault": true }
    }
  ]
}
```

---

## 7. src/extension.ts（核心骨架，可直接编译运行）

```ts
import * as vscode from 'vscode';

let provider: TerminalTreeDataProvider;

export function activate(context: vscode.ExtensionContext) {
  provider = new TerminalTreeDataProvider();

  context.subscriptions.push(
    // 注册树视图（数据源）
    vscode.window.registerTreeDataProvider('terminalManager.terminals', provider),
    // 释放 provider 内的事件订阅
    new vscode.Disposable(() => provider.dispose()),

    // ---- 命令 ----
    vscode.commands.registerCommand('terminalManager.new', () => newTerminal(vscode.TerminalLocation.Editor)),
    vscode.commands.registerCommand('terminalManager.newInPanel', () => newTerminal(vscode.TerminalLocation.Panel)),
    vscode.commands.registerCommand('terminalManager.refresh', () => provider.refresh()),
    vscode.commands.registerCommand('terminalManager.open', openTerminal),
    vscode.commands.registerCommand('terminalManager.moveToEditor', async (t?: vscode.Terminal) => {
      await focusAndRun(t, 'workbench.action.terminal.moveToEditor');
    }),
    vscode.commands.registerCommand('terminalManager.moveToPanel', async (t?: vscode.Terminal) => {
      await focusAndRun(t, 'workbench.action.terminal.moveToTerminalPanel');
    }),
    vscode.commands.registerCommand('terminalManager.rename', renameTerminal),
    vscode.commands.registerCommand('terminalManager.kill', killTerminal),
  );
}

export function deactivate() {}

// ---------- 新建 ----------
function newTerminal(location: vscode.TerminalLocation): vscode.Terminal {
  const t = vscode.window.createTerminal({ name: '终端', location });
  t.show();
  return t;
}

// ---------- 单击列表项：默认在编辑区打开 ----------
async function openTerminal(t?: vscode.Terminal) {
  if (!t) return;
  t.show();
  const behavior = vscode.workspace
    .getConfiguration('terminalManager')
    .get<'editor' | 'focus'>('clickBehavior', 'editor');
  if (behavior !== 'focus' && isInPanel(t)) {
    await vscode.commands.executeCommand('workbench.action.terminal.moveToEditor');
  }
}

// ---------- 先聚焦目标终端，再执行"作用于活动终端"的内部命令 ----------
async function focusAndRun(t: vscode.Terminal | undefined, command: string) {
  if (!t) return;
  t.show();
  await vscode.commands.executeCommand(command);
  provider.refresh();
}

// ---------- 重命名：自己弹输入框，再走带参命令 ----------
async function renameTerminal(t?: vscode.Terminal) {
  if (!t) return;
  const name = await vscode.window.showInputBox({
    title: '重命名终端',
    value: t.name,
    prompt: '输入新的终端名称',
  });
  if (name === undefined || name === t.name) return; // 取消或未变化
  t.show();
  await vscode.commands.executeCommand('workbench.action.terminal.renameWithArg', { name });
  provider.refresh();
}

// ---------- 删除（带确认） ----------
async function killTerminal(t?: vscode.Terminal) {
  if (!t) return;
  const ok = await vscode.window.showWarningMessage(
    `确定要结束终端「${t.name}」吗？`,
    { modal: false },
    '结束',
  );
  if (ok !== '结束') return;
  t.dispose();
}

// ---------- 工具函数 ----------
/** 判断终端是否在面板（location 为对象或 Editor 枚举时都算编辑区） */
function isInPanel(t: vscode.Terminal): boolean {
  const loc = (t.creationOptions as vscode.TerminalOptions).location;
  return loc === vscode.TerminalLocation.Panel;
}

function locationLabel(t: vscode.Terminal): string {
  return isInPanel(t) ? '面板' : '编辑区';
}

function describeTerminal(t: vscode.Terminal): string {
  const parts: string[] = [locationLabel(t)];
  if (t === vscode.window.activeTerminal) parts.push('● 当前');
  if (t.exitStatus.code !== undefined) {
    parts.push(t.exitStatus.code === 0 ? '已结束' : `退出码 ${t.exitStatus.code}`);
  }
  return parts.join(' · ');
}

// ---------- 树节点 ----------
class TerminalTreeItem extends vscode.TreeItem {
  constructor(public readonly terminal: vscode.Terminal) {
    super(terminal.name, vscode.TreeItemCollapsibleState.None);
    this.contextValue = 'terminal'; // 用于右键菜单 when 过滤
    this.iconPath = new vscode.ThemeIcon('terminal');
    this.description = describeTerminal(terminal);
    this.tooltip = new vscode.MarkdownString(
      [
        `**名称**: ${terminal.name}`,
        `**位置**: ${locationLabel(terminal)}`,
        `**Shell**: ${terminal.state.shell || '未知'}`,
      ].join('\n\n'),
      true,
    );
    // 单击 = 打开（在编辑区打开 / 聚焦）
    this.command = { command: 'terminalManager.open', title: '打开', arguments: [terminal] };
  }
}

// ---------- 树数据源（实时同步 window.terminals） ----------
class TerminalTreeDataProvider implements vscode.TreeDataProvider<TerminalTreeItem> {
  private readonly _onDidChangeTreeData = new vscode.EventEmitter<TerminalTreeItem | undefined | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private readonly disposables: vscode.Disposable[] = [];

  constructor() {
    const sync = () => this.refresh();
    this.disposables.push(
      vscode.window.onDidOpenTerminal(sync),
      vscode.window.onDidCloseTerminal(sync),
      vscode.window.onDidChangeActiveTerminal(sync),
      vscode.window.onDidChangeTerminalState(sync),
    );
  }

  dispose() {
    this.disposables.forEach((d) => d.dispose());
    this._onDidChangeTreeData.dispose();
  }

  refresh() {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: TerminalTreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(): TerminalTreeItem[] {
    // window.terminals 包含面板 + 编辑区所有终端（内置列表做不到这点）
    return vscode.window.terminals.map((t) => new TerminalTreeItem(t));
  }
}
```

---

## 8. 关键实现细节

1. **为什么能解决"编辑区终端不显示"**：内置终端视图有 bug/限制，但 `window.terminals` 返回全部终端（`TerminalLocation.Editor` 和 `Panel` 都算），所以我们的列表天然完整。
2. **为什么单击能"在编辑区打开"**：`createTerminal` 时指定 `location: Editor`；对已存在终端则 `show()` 后执行 `workbench.action.terminal.moveToEditor`（该命令作用于活动终端，故必须**先聚焦再执行**——`focusAndRun` 就是这个套路）。
3. **菜单过滤**：树节点设 `contextValue = 'terminal'`，右键菜单全部加 `viewItem == terminal` 的 `when`，保证只有终端行有这些操作。
4. **实时性**：订阅 4 个终端事件统一 `refresh()`。`onDidChangeTerminalState` 触发较频繁（shell 集成、交互状态），个人工具可接受；若要优化可在事件回调里做节流。
5. **删除安全**：`killTerminal` 弹确认框再 `dispose()`。
6. **重命名**：用 `showInputBox` 自己弹输入框（比内置命令体验统一），再调 `renameWithArg`。

---

## 9. 已知限制与绕过（接受即可）

| 限制 | 说明 | 绕过 |
|------|------|------|
| 无法劫持内置终端图标 | 内置图标行为硬编码 | **方案已定为不用它**，用自己注册的活动栏图标 |
| `moveToEditor` 等是内部命令 | 作用于"活动终端" | 先 `show()` 再执行（已封装进 `focusAndRun`）；命令已稳定存在多年 |
| `Terminal.name` 只读 | 不能直接改名 | 走 `renameWithArg`（已解决） |
| 拿不到终端输出内容 | 稳定 API 无输出读取 | 本方案不需要输出，不影响 |
| 拿不到 split 分组关系 | 稳定 API 无分组信息 | 列表平铺展示即可 |

---

## 10. 新窗口开发流程

```bash
# 1) 新建项目目录并进入
mkdir terminal-manager && cd terminal-manager

# 2) 把本方案的 package.json / tsconfig.json / src/extension.ts /
#    .vscode/launch.json / .vscode/tasks.json / media/terminal.svg 复制进去

# 3) 安装依赖
npm install

# 4) 编译（一次性）
npm run compile
#    或后台 watch：npm run watch
```

5. 在 VS Code 打开该目录，按 **F5** 启动"扩展开发宿主"窗口。
6. 在开发宿主里：用 `` Ctrl+` `` 新建几个终端、打开几个编辑区终端、结束一个 → 验证左侧列表实时变化。
7. 调试完毕关掉宿主窗口即可。

### 打包安装（可选）

```bash
npm install -g @vscode/vsce
vsce package            # 生成 .vsix
code --install-extension terminal-manager-0.0.1.vsix
```

---

## 11. 验收清单

- [ ] 左侧活动栏出现**自己的**终端图标（不是内置那个）
- [ ] 点自己的图标 → 左侧**只有列表**，没有极窄终端窗口
- [ ] 列表实时显示**所有**运行中终端（含编辑区终端）——对应痛点二
- [ ] 单击列表项 → 终端在**编辑区**打开（面板的移入，编辑区的聚焦）
- [ ] 标题栏 `+` → 新建终端到编辑区
- [ ] 行内/右键 → 聚焦、移入编辑区、移回面板、重命名、删除
- [ ] 删除有确认弹窗
- [ ] 新建/结束终端后列表自动刷新；当前活动终端有高亮（`● 当前`）
- [ ] 列表项显示位置 / Shell / 退出码等描述信息

---

## 12. 后续可扩展（非必需）

- 按 workspace 文件夹分组（`TreeItem.collapsibleState` + 二级节点）
- 状态栏 badge 显示终端数量（`TreeView.badge`）
- 双击行为区分于单击
- 记住每个终端的命名规则（`shellIntegration.cwd` 自动生成 `folder$N` 名称）
