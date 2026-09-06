import * as os from 'os';
import { CliToolBase, ToolMeta, Risk } from './base';

const LARK_BIN = `${os.homedir()}/.npm-global/bin/lark-cli`;
const LARK_ENV = `${os.homedir()}/.npm-global/bin`;

/** 多行长文本参数走临时文件（@file 语法），避免 shell 转义问题 */
function tmpFileFor(content: string): string {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const fs = require('fs') as typeof import('fs');
  const p = `${os.tmpdir()}/connector-hub-${Date.now()}-${Math.random().toString(36).slice(2)}.md`;
  fs.writeFileSync(p, content, 'utf8');
  return p;
}

/** lark-cli docs +create：创建飞书文档（Markdown 内容） */
export class LarkDocCreateTool extends CliToolBase {
  constructor() { super(LARK_BIN, LARK_ENV); }

  meta(): ToolMeta {
    return {
      name: 'lark_doc_create',
      description: 'Create a new Lark (Feishu) document with Markdown content. Use ONLY for Lark online documents; do NOT use for local files. Returns document_id and url.',
      inputSchema: {
        type: 'object',
        properties: {
          title: { type: 'string', description: '文档标题' },
          content: { type: 'string', description: '可选：Markdown 全文，创建后立即写入' }
        },
        required: ['title']
      },
      tags: ['lark', 'docs']
    };
  }

  get risk(): Risk { return 'write'; }
  describe(input: Record<string, unknown>) { return `创建飞书文档「${input.title}」`; }

  buildArgs(input: Record<string, unknown>): string[] {
    const args = ['docs', '+create', '--title', String(input.title), '--doc-format', 'markdown'];
    if (typeof input.content === 'string' && input.content.trim()) {
      args.push('--content', `@${tmpFileFor(input.content)}`);
    }
    return args;
  }
}

/** lark-cli docs +update：追加/覆写/str_replace */
export class LarkDocUpdateTool extends CliToolBase {
  constructor() { super(LARK_BIN, LARK_ENV); }

  meta(): ToolMeta {
    return {
      name: 'lark_doc_update',
      description: 'Update an existing Lark document. Modes: append (add Markdown at end), overwrite (replace ENTIRE document, destructive), str_replace (find/replace inline text). Use overwrite only when full replacement is intended.',
      inputSchema: {
        type: 'object',
        properties: {
          doc: { type: 'string', description: '文档 URL 或 document token' },
          mode: { type: 'string', enum: ['append', 'overwrite', 'str_replace'], description: '更新方式' },
          content: { type: 'string', description: 'append/overwrite 时的 Markdown 内容' },
          pattern: { type: 'string', description: 'str_replace 时要查找的文本' },
          replacement: { type: 'string', description: 'str_replace 时的替换文本；空串表示删除匹配' }
        },
        required: ['doc', 'mode']
      },
      tags: ['lark', 'docs']
    };
  }

  get risk(): Risk { return 'high-risk-write'; }
  describe(input: Record<string, unknown>) {
    const mode = String(input.mode);
    if (mode === 'str_replace') return `在飞书文档 ${input.doc} 中替换文本`;
    if (mode === 'overwrite') return `整体覆写飞书文档 ${input.doc}`;
    return `向飞书文档 ${input.doc} 追加内容`;
  }

  buildArgs(input: Record<string, unknown>): string[] {
    const mode = String(input.mode);
    const args = ['docs', '+update', '--doc', String(input.doc), '--doc-format', 'markdown'];
    if (mode === 'str_replace') {
      args.push('--command', 'str_replace', '--pattern', String(input.pattern));
      if (typeof input.replacement === 'string') args.push('--content', input.replacement);
    } else {
      args.push('--command', mode, '--content', `@${tmpFileFor(String(input.content ?? ''))}`);
    }
    return args;
  }
}

/** lark-cli docs +fetch：读取文档（Markdown） */
export class LarkDocFetchTool extends CliToolBase {
  constructor() { super(LARK_BIN, LARK_ENV); }

  meta(): ToolMeta {
    return {
      name: 'lark_doc_fetch',
      description: 'Fetch content of a Lark document by URL or token. Returns content as Markdown (default) or XML. Read-only.',
      inputSchema: {
        type: 'object',
        properties: {
          doc: { type: 'string', description: '文档 URL 或 document token' },
          format: { type: 'string', enum: ['markdown', 'xml'], description: '输出格式，默认 markdown' }
        },
        required: ['doc']
      },
      tags: ['lark', 'docs']
    };
  }

  get risk(): Risk { return 'read'; }
  describe(input: Record<string, unknown>) { return `读取飞书文档 ${input.doc}`; }

  buildArgs(input: Record<string, unknown>): string[] {
    const args = ['docs', '+fetch', '--doc', String(input.doc), '--doc-format', String(input.format ?? 'markdown')];
    return args;
  }
}

/** lark-cli docs +search：搜索文档 */
export class LarkDocSearchTool extends CliToolBase {
  constructor() { super(LARK_BIN, LARK_ENV); }

  meta(): ToolMeta {
    return {
      name: 'lark_doc_search',
      description: 'Search Lark docs, Wiki and spreadsheet files by keyword. Returns matching files with tokens and URLs. Read-only.',
      inputSchema: {
        type: 'object',
        properties: {
          query: { type: 'string', description: '搜索关键词' },
          page_size: { type: 'number', description: '每页数量，默认 15，最大 20' }
        },
        required: ['query']
      },
      tags: ['lark', 'docs']
    };
  }

  get risk(): Risk { return 'read'; }
  describe(input: Record<string, unknown>) { return `搜索飞书文档「${input.query}」`; }

  buildArgs(input: Record<string, unknown>): string[] {
    const args = ['docs', '+search', '--query', String(input.query)];
    if (typeof input.page_size === 'number') args.push('--page-size', String(input.page_size));
    return args;
  }
}

/** lark-cli markdown +create：云盘原生 Markdown 文件 */
export class LarkMdCreateTool extends CliToolBase {
  constructor() { super(LARK_BIN, LARK_ENV); }

  meta(): ToolMeta {
    return {
      name: 'lark_md_create',
      description: 'Create a native Markdown file in Lark Drive (Drive-native .md, NOT a docx document). Best for plain Markdown knowledge notes. Returns file_token and url.',
      inputSchema: {
        type: 'object',
        properties: {
          name: { type: 'string', description: '文件名（含 .md 后缀）' },
          content: { type: 'string', description: 'Markdown 全文' },
          folder_token: { type: 'string', description: '可选：目标文件夹 token，默认根目录' }
        },
        required: ['name', 'content']
      },
      tags: ['lark', 'markdown']
    };
  }

  get risk(): Risk { return 'write'; }
  describe(input: Record<string, unknown>) { return `在飞书云盘创建 Markdown 文件「${input.name}」`; }

  buildArgs(input: Record<string, unknown>): string[] {
    const args = ['markdown', '+create', '--name', String(input.name), '--content', `@${tmpFileFor(String(input.content))}`];
    if (typeof input.folder_token === 'string' && input.folder_token) args.push('--folder-token', input.folder_token);
    return args;
  }
}

/** lark-cli markdown +overwrite：覆写云盘 Markdown */
export class LarkMdOverwriteTool extends CliToolBase {
  constructor() { super(LARK_BIN, LARK_ENV); }

  meta(): ToolMeta {
    return {
      name: 'lark_md_overwrite',
      description: 'Overwrite content of an existing Drive-native Markdown file by file_token. Destructive: replaces entire content.',
      inputSchema: {
        type: 'object',
        properties: {
          file_token: { type: 'string', description: 'Markdown 文件 token' },
          content: { type: 'string', description: '新的 Markdown 全文' }
        },
        required: ['file_token', 'content']
      },
      tags: ['lark', 'markdown']
    };
  }

  get risk(): Risk { return 'high-risk-write'; }
  describe(input: Record<string, unknown>) { return `覆写飞书 Markdown 文件 ${input.file_token}`; }

  buildArgs(input: Record<string, unknown>): string[] {
    return ['markdown', '+overwrite', '--file-token', String(input.file_token), '--content', `@${tmpFileFor(String(input.content))}`];
  }
}

/** lark-cli markdown +fetch：读取云盘 Markdown */
export class LarkMdFetchTool extends CliToolBase {
  constructor() { super(LARK_BIN, LARK_ENV); }

  meta(): ToolMeta {
    return {
      name: 'lark_md_fetch',
      description: 'Fetch content of a Drive-native Markdown file by file_token. Read-only.',
      inputSchema: {
        type: 'object',
        properties: {
          file_token: { type: 'string', description: 'Markdown 文件 token' }
        },
        required: ['file_token']
      },
      tags: ['lark', 'markdown']
    };
  }

  get risk(): Risk { return 'read'; }
  describe(input: Record<string, unknown>) { return `读取飞书 Markdown 文件 ${input.file_token}`; }

  buildArgs(input: Record<string, unknown>): string[] {
    return ['markdown', '+fetch', '--file-token', String(input.file_token)];
  }
}

/** MVP 工具集（与 package.json languageModelTools 声明一一对应） */
export function buildLarkTools(): CliToolBase[] {
  return [
    new LarkDocCreateTool(),
    new LarkDocUpdateTool(),
    new LarkDocFetchTool(),
    new LarkDocSearchTool(),
    new LarkMdCreateTool(),
    new LarkMdOverwriteTool(),
    new LarkMdFetchTool()
  ];
}
