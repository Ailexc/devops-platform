import * as vscode from 'vscode';
import { execFile } from 'child_process';

export type Risk = 'read' | 'write' | 'high-risk-write';

export interface ToolMeta {
  name: string;
  description: string;
  inputSchema: object;
  tags: string[];
}

/** 通用 CLI 工具基类：exec + 确认分级 + 结果裁剪 */
export abstract class CliToolBase implements vscode.LanguageModelTool<Record<string, unknown>> {
  constructor(
    protected readonly binPath: string,
    protected readonly envPath?: string
  ) {}

  /** 工具元信息（与 package.json languageModelTools 声明保持一致） */
  abstract meta(): ToolMeta;
  /** 由参数构造 argv */
  abstract buildArgs(input: Record<string, unknown>): string[];
  /** 风险等级 → 确认策略 */
  abstract get risk(): Risk;
  /** 确认框/进度文案 */
  abstract describe(input: Record<string, unknown>): string;

  prepareInvocation(
    options: vscode.LanguageModelToolInvocationPrepareOptions<Record<string, unknown>>,
    _token?: vscode.CancellationToken
  ): vscode.ProviderResult<vscode.PreparedToolInvocation> {
    const desc = this.describe(options.input);
    let confirmationMessages: vscode.LanguageModelToolConfirmationMessages | undefined;
    if (this.risk === 'write') {
      confirmationMessages = {
        title: '确认操作',
        message: new vscode.MarkdownString(`将执行：**${desc}**，确认？`)
      };
    } else if (this.risk === 'high-risk-write') {
      confirmationMessages = {
        title: '⚠️ 高危操作',
        message: new vscode.MarkdownString(`**覆盖/删除操作**：${desc}\n\n该操作不可逆，确认继续？`)
      };
    }
    return { invocationMessage: desc, confirmationMessages };
  }

  async invoke(
    options: vscode.LanguageModelToolInvocationOptions<Record<string, unknown>>,
    token: vscode.CancellationToken
  ): Promise<vscode.LanguageModelToolResult> {
    const stdout = await this.run(this.buildArgs(options.input), token);
    return new vscode.LanguageModelToolResult([new vscode.LanguageModelTextPart(this.summarize(stdout))]);
  }

  protected run(args: string[], token: vscode.CancellationToken): Promise<string> {
    return new Promise((resolve, reject) => {
      const p = execFile(
        this.binPath,
        args,
        {
          timeout: 120_000,
          maxBuffer: 16 * 1024 * 1024,
          env: { ...process.env, PATH: `${this.envPath ?? ''}:${process.env.PATH ?? ''}` }
        },
        (err, stdout) => (err ? reject(err) : resolve(stdout))
      );
      token.onCancellationRequested(() => p.kill());
    });
  }

  /** 给模型的摘要：结构化 JSON 截断，避免撑爆上下文 */
  protected summarize(stdout: string): string {
    const trimmed = stdout.trim();
    try {
      const j = JSON.parse(trimmed);
      const s = JSON.stringify(j, null, 2);
      return s.length > 4000 ? s.slice(0, 4000) + '\n…(truncated)' : s;
    } catch {
      return trimmed.length > 4000 ? trimmed.slice(0, 4000) + '\n…(truncated)' : trimmed;
    }
  }
}
