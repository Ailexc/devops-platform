#!/usr/bin/env bash
# doc-sync.sh — 飞书技术梳理文档本地镜像工作流（pull / check / push）
# 用法：
#   scripts/doc-sync.sh pull <key> <wiki-url>   # 拉取文档到 docs-local/<key>/（首次需 url，之后可省略）
#   scripts/doc-sync.sh check <key>             # 只查线上状态：revision / 网页卡片 / 与本地基线差异
#   scripts/doc-sync.sh push <key> [--force]    # 本地内容 overwrite 回写（含防呆拦截 + 自动回读验证）
# 约定：所有 lark-cli 调用在仓库根执行（reference-map 相对路径按 CWD 解析）
set -euo pipefail
export PATH="$HOME/.npm-global/bin:$PATH"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"

ACTION="${1:-}"; KEY="${2:-}"
DIR="docs-local/$KEY"
META="$DIR/meta.json"; CONTENT="$DIR/content.md"; REFMAP="$DIR/reference-map.json"
[ -n "$ACTION" ] && [ -n "$KEY" ] || { echo "用法: $0 pull|check|push <doc-key> [wiki-url|--force]"; exit 1; }

doc_url() { python3 -c "import json;print(json.load(open('$META'))['url'])"; }

fetch_remote_to() { # $1=输出文件
  lark-cli docs +fetch --doc "$(doc_url)" --detail full --doc-format markdown --as user > "$1"
}

remote_state() { # stdout: {"revision","sha","cards":[...]}（fetch 落 /tmp 后解析）
  local tmp="/tmp/docsync-remote-$KEY.json"
  fetch_remote_to "$tmp"
  python3 -c "
import json,sys,hashlib,re
d=json.load(open('$tmp'))
def fc(o):
    if isinstance(o,dict):
        for k,v in o.items():
            if k=='content' and isinstance(v,str) and len(v)>200: return v
            r=fc(v)
            if r: return r
    elif isinstance(o,list):
        for it in o:
            r=fc(it)
            if r: return r
c=fc(d) or ''
doc=d.get('data',{}).get('document',{})
print(json.dumps({'revision':doc.get('revision_id'),'sha':hashlib.sha256(c.encode()).hexdigest(),'cards':re.findall(r'<readonly-block[^>]*href=\"([^\"]+)\"',c)},ensure_ascii=False))
"
}

rebuild_index() {
  python3 -c "
import json,glob
idx=[]
for m in sorted(glob.glob('docs-local/*/meta.json')):
    d=json.load(open(m))
    idx.append({'key':d['key'],'url':d['url'],'revision_id':d.get('revision_id'),'cards':len(d.get('cards',[])),'html5':len(d.get('html5_refs',[]))})
json.dump(idx,open('docs-local/index.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('docs-local/index.json 已更新:', [i['key'] for i in idx])
"
}

case "$ACTION" in
pull)
  mkdir -p "$DIR"
  URL="${3:-}"
  if [ -f "$META" ]; then URL=$(doc_url); fi
  [ -n "$URL" ] || { echo "❌ 首次 pull 需要文档 URL：$0 pull $KEY <wiki-or-docx-url>"; exit 1; }
  OLD_SHA=""
  [ -f "$META" ] && OLD_SHA=$(python3 -c "import json;print(json.load(open('$META')).get('content_sha',''))")
  # 本地未推修改保护：本地 content 与基线不一致 = 有未推送的本地修改，直接 pull 会被线上内容覆盖
  HAS_FORCE=""
  for _a in "$@"; do [ "$_a" = "--force" ] && HAS_FORCE=1; done
  if [ -f "$CONTENT" ] && [ -n "$OLD_SHA" ]; then
    LOCAL_SHA=$(sha256sum "$CONTENT" | cut -d' ' -f1)
    if [ "$LOCAL_SHA" != "$OLD_SHA" ] && [ -z "$HAS_FORCE" ]; then
      echo "🛑 pull 拦截：本地 content.md 存在未推送的修改（本地 ${LOCAL_SHA:0:12} vs 基线 ${OLD_SHA:0:12}）"
      echo "   直接 pull 会用线上内容覆盖这些修改。"
      echo "   选项: ① 保留本地修改 → 先 scripts/doc-sync.sh push $KEY 再 pull"
      echo "         ② 两边都要 → 先手动合并（VS Code 对比本地与线上）"
      echo "         ③ 确认放弃本地修改 → scripts/doc-sync.sh pull $KEY $URL --force"
      exit 2
    fi
    [ -n "$HAS_FORCE" ] && echo "⚠️  --force：将放弃本地未推送修改，用线上内容覆盖"
  fi
  lark-cli docs +fetch --doc "$URL" --detail full --doc-format markdown --as user > "/tmp/docsync-pull-$KEY.json"
  python3 -c "
import json,hashlib,re,os
key='$KEY'; url='$URL'; old_sha='$OLD_SHA'
d=json.load(open(f'/tmp/docsync-pull-{key}.json'))
doc=d['data']['document']
c=doc['content']; rm=doc.get('reference_map') or ''
rm=rm or {}
os.makedirs(f'docs-local/{key}',exist_ok=True)
open(f'docs-local/{key}/content.md','w',encoding='utf-8').write(c)
json.dump(rm,open(f'docs-local/{key}/reference-map.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
meta={'key':key,'url':url,'document_id':doc.get('document_id'),'revision_id':doc.get('revision_id'),'content_sha':hashlib.sha256(c.encode()).hexdigest(),'cards':re.findall(r'<readonly-block[^>]*href=\"([^\"]+)\"',c),'html5_refs':list((rm.get('html5-block') or {}).keys())}
json.dump(meta,open(f'docs-local/{key}/meta.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(f'✅ pull {key}: rev={meta[\"revision_id\"]} sha={meta[\"content_sha\"][:12]} 网页卡片={len(meta[\"cards\"])} html5块={len(meta[\"html5_refs\"])}')
if old_sha and old_sha!=meta['content_sha']:
    print(f'⚠️ 注意：线上内容与上次基线不同（旧 {old_sha[:12]}）——若本地有未推送修改，请先人工合并再继续')
"
  rebuild_index
  ;;
check)
  [ -f "$META" ] || { echo "❌ 先 pull：$0 pull $KEY <url>"; exit 1; }
  RS=$(remote_state)
  RS="$RS" python3 -c "
import json,os
rs=json.loads(os.environ['RS']); meta=json.load(open('$META'))
print(f'线上: rev={rs[\"revision\"]} sha={rs[\"sha\"][:12]} 网页卡片={len(rs[\"cards\"])} {rs[\"cards\"]}')
print(f'基线: rev={meta.get(\"revision_id\")} sha={meta.get(\"content_sha\",\"\")[:12]}')
if rs['sha']==meta.get('content_sha'): print('✅ 线上与本地基线一致，可安全 push')
else: print('⚠️ 线上与基线不一致（线上被改过 / 本地未同步）——push 会被拦截，先 pull')
"
  ;;
push)
  [ -f "$CONTENT" ] || { echo "❌ 无本地内容，先 pull"; exit 1; }
  RS=$(remote_state)
  BLOCK=$(RS="$RS" python3 -c "
import json,os
rs=json.loads(os.environ['RS']); meta=json.load(open('$META'))
reasons=[]
if rs['sha']!=meta.get('content_sha'): reasons.append(f'线上 revision {rs[\"revision\"]} 与本地基线不一致（线上有新变更）→ 先 pull 合并')
if rs['cards']: reasons.append(f'线上含 {len(rs[\"cards\"])} 个网页卡片，overwrite 会丢弃：{chr(10).join(rs[\"cards\"])}')
print(chr(10).join('· '+r for r in reasons))
")
  if [ -n "$BLOCK" ] && [ "${3:-}" != "--force" ]; then
    echo "🛑 push 被防呆拦截："; echo "$BLOCK"
    echo "选项: ① 线上有新变更 → 先 pull 合并 ② 网页卡片会丢 → 确认后 $0 push $KEY --force（推送后需在飞书 UI 重插卡片）③ 单点小改 → 走逐块手术不动 overwrite"
    exit 2
  fi
  echo "== overwrite 回写 =="
  lark-cli docs +update --doc "$(doc_url)" --command overwrite --content "@$CONTENT" --reference-map "@$REFMAP" --doc-format markdown --as user | python3 -c "
import json,sys
raw=sys.stdin.read(); d=json.loads(raw[raw.find('{'):])
print('update ok:', d.get('ok'), '| result:', d.get('data',{}).get('result',''))
"
  echo "== 回读验证（五项）=="
  fetch_remote_to "/tmp/docsync-post-$KEY.json"
  python3 -c "
import json,sys,re,hashlib
key='$KEY'
d=json.load(open(f'/tmp/docsync-post-{key}.json'))
doc=d['data']['document']; c=doc['content']; rm=doc.get('reference_map') or {}
meta=json.load(open(f'docs-local/{key}/meta.json'))
local=open(f'docs-local/{key}/content.md',encoding='utf-8').read()
h5r=len(re.findall(r'<html5-block',c)); h5l=len(meta.get('html5_refs',[]))
h1_local=set(re.findall(r'^# .*',local,re.M)); h1_remote=set(re.findall(r'^# .*',c,re.M))
cards=len(re.findall(r'<readonly-block',c))
sha_now=hashlib.sha256(c.encode()).hexdigest()
sha_local=hashlib.sha256(local.encode()).hexdigest()
def p(ok,msg): print(('✅' if ok else '❌'), msg)
p(sha_now==sha_local, f'回读内容与本地一致（sha {sha_now[:12]} vs {sha_local[:12]}）')
p(h5r>=h5l, f'html5 块存活 {h5r}/{h5l}')
p(h1_local<=h1_remote, f'h1 章节齐全（本地 {len(h1_local)} 个全部在线上）')
print(('ℹ️' if cards==len(meta.get('cards',[])) else '⚠️'), f'网页卡片: 线上 {cards} 个（push 前基线 {len(meta.get(\"cards\",[]))} 个）')
meta['revision_id']=doc.get('revision_id'); meta['content_sha']=sha_now; meta['cards']=re.findall(r'<readonly-block[^>]*href=\"([^\"]+)\"',c)
json.dump(meta,open(f'docs-local/{key}/meta.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
print(f'基线已更新: rev={meta[\"revision_id\"]} sha={sha_now[:12]}')
"
  rebuild_index
  ;;
*)
  echo "用法: $0 pull|check|push <doc-key> [wiki-url|--force]"; exit 1;;
esac
