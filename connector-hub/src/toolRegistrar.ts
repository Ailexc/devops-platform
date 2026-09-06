import * as vscode from 'vscode';
import { ToolMeta } from './tools/base';
import { CliToolBase } from './tools/base';

/**
 * 动态注册器：把工具实现注册进 vscode.lm。
 * 注意：工具要被模型看见，还必须在 package.json 的 languageModelTools 贡献点声明
 * （本插件 MVP 采用"声明式 + 实现配对"模式，见指导文档 §2.5）。
 */
export class ToolRegistrar implements vscode.Disposable {
  private disposables: vscode.Disposable[] = [];

  registerAll(tools: CliToolBase[]): void {
    this.disposeAll();
    for (const impl of tools) {
      const meta: ToolMeta = impl.meta();
      const wrapper: vscode.LanguageModelTool<Record<string, unknown>> = {
        invoke: (o, tk) => impl.invoke(o, tk),
        prepareInvocation: (o, tk) => impl.prepareInvocation!(o, tk)
      };
      this.disposables.push(vscode.lm.registerTool(meta.name, wrapper));
    }
  }

  disposeAll(): void {
    this.disposables.forEach(d => d.dispose());
    this.disposables = [];
  }

  dispose(): void { this.disposeAll(); }
}
