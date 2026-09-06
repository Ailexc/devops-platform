/** lark-cli 注册表条目模板（extension.ts 与 injection.ts 共用） */
export const LARK_ENTRY = `## lark-cli
- type: cli
- path: ~/.npm-global/bin/lark-cli
- env_path: ~/.npm-global/bin
- version_cmd: lark-cli --version
- doctor_cmd: lark-cli doctor
- enabled: true

### tools
- name: lark_doc_create
  title: 创建飞书文档
  cmd: docs +create --title {title}
  risk: write
- name: lark_doc_update
  title: 更新飞书文档(追加/覆写/替换)
  cmd: docs +update --doc {doc} --command {mode}
  risk: high-risk-write
- name: lark_doc_fetch
  title: 读取飞书文档
  cmd: docs +fetch --doc {doc}
  risk: read
- name: lark_doc_search
  title: 搜索飞书文档
  cmd: docs +search --query {query}
  risk: read
- name: lark_md_create
  title: 创建云盘 Markdown 文件
  cmd: markdown +create --name {name}
  risk: write
- name: lark_md_overwrite
  title: 覆写云盘 Markdown 文件
  cmd: markdown +overwrite --file-token {file_token}
  risk: high-risk-write
- name: lark_md_fetch
  title: 读取云盘 Markdown 文件
  cmd: markdown +fetch --file-token {file_token}
  risk: read
`;

export const LARK_DOCTOR_LINE = `check "lark-cli" "$HOME/.npm-global/bin/lark-cli" --version`;
