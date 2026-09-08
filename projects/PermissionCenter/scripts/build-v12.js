#!/usr/bin/env node
// Build v12 demo from v10 base
// Usage: node scripts/build-v12.js
const fs = require('fs');
const path = require('path');

const src = path.join(__dirname, '../docs/capability-apply-demo-v10.html');
const dst = path.join(__dirname, '../docs/capability-apply-demo-v12.html');

let h = fs.readFileSync(src, 'utf8');

// ===== HTML changes =====
h = h.replace(
  '<title>能力包 Demo v10（定版）- 查看/编辑/授权管理统一/表达式构建器+手册/预览增强</title>',
  '<title>能力包 Demo v12 - 范围字段类型系统（表单模板 v2）</title>'
);
h = h.replace('<h1>🧭 能力包 Demo v10（定版）</h1>', '<h1>🧭 能力包 Demo v12</h1>');
h = h.replace(
  '查看=编辑器只读 · 授权管理统一上架/下架 · 表达式构建器+OpenFGA手册 · 预览增强',
  '范围字段类型系统 · owner 配置表单模板 · applicant 友好交互 · 自动表达式生成'
);
h = h.replace('风格：方案 A · 云原生企业蓝', '核心改动：数据范围从"手写表达式"升级为"表单字段类型系统"');

// ===== Add new CSS =====
const newCSS = `
.choice-chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;}
.choice-chip{display:inline-flex;align-items:center;gap:4px;padding:5px 12px;background:var(--bg-card);border:2px solid var(--border);border-radius:8px;font-size:12px;cursor:pointer;transition:all .15s;}
.choice-chip:hover{border-color:var(--brand);}
.choice-chip.selected{border-color:var(--brand);background:var(--brand-soft);color:var(--brand-strong);font-weight:600;}
.choice-chip .cc-value{font-family:var(--font-mono);color:var(--text-tertiary);font-size:11px;}
.choice-chip .cc-x{margin-left:4px;cursor:pointer;opacity:.5;}
.choice-chip .cc-x:hover{opacity:1;}
.var-display{display:flex;align-items:center;gap:8px;padding:10px 14px;background:var(--brand-softer);border:1px solid #d6e4ff;border-radius:8px;margin-top:6px;}
.var-display .var-icon{font-size:18px;}
.var-display .var-text{font-size:12px;color:var(--brand-strong);}
.var-display .var-resolved{font-family:var(--font-mono);font-weight:600;}
.expr-preview{margin-top:8px;padding:8px 12px;background:#fff;border:1px solid var(--border);border-radius:6px;font-family:var(--font-mono);font-size:12px;color:var(--brand-strong);}`;
h = h.replace('</style>', newCSS + '\n</style>');

// ===== Script changes =====
const scriptStart = h.indexOf('<script>') + '<script>'.length;
const scriptEnd = h.indexOf('</script>');
const before = h.substring(0, scriptStart);
const after = h.substring(scriptEnd);
let js = h.substring(scriptStart, scriptEnd);

// 1. SCOPE_OPT_LABEL
js = js.replace(
  'const SCOPE_OPT_LABEL = { all:"所有数据", instance:"具体实例", expression:"条件表达式" };',
  'const SCOPE_OPT_LABEL = { all:"所有数据", instance:"具体实例", select:"单选", multi_select:"多选", variable:"自动匹配", input:"自由输入" };'
);

// 2. scopeIcon
js = js.replace(
  'function scopeIcon(t){ return {all:"🌍",instance:"📌",expression:"🏷️"}[t]||"📋"; }',
  'function scopeIcon(t){ return {all:"🌍",instance:"📌",select:"📋",multi_select:"☑️",variable:"🔄",input:"⌨️"}[t]||"📋"; }'
);

// Helper to do replacement with logging
function rep(js, label, search, replacement) {
  if (js.includes(search)) {
    js = js.replace(search, replacement);
    console.log(`  ✅ ${label}: replaced`);
  } else {
    console.log(`  ❌ ${label}: NOT FOUND (search string doesn't match)`);
  }
  return js;
}

// 3. CAPS readonly preset — replace expression with select/multi_select/variable/input
js = rep(js, 'readonly',
  `{type:"all",label:"所有数据",desc:"无需填写"}, {type:"instance",label:"具体实例",desc:"勾选要访问的主机实例",api:"/api/v1/hosts"}, {type:"expression",label:"条件表达式",desc:"按字段条件过滤",field:"env",op:"==",value:"prod",expr:'env == "prod"'}`,
  `{type:"all",label:"所有数据",desc:"无需填写"}, {type:"instance",label:"具体实例",desc:"勾选要访问的主机实例",api:"/api/v1/hosts"}, {type:"select",label:"选择环境",desc:"选择目标环境（单选）",field:"env",op:"==",choices:[{label:"生产环境",value:"prod"},{label:"预发布",value:"staging"},{label:"开发环境",value:"dev"}]}, {type:"multi_select",label:"选择云账号",desc:"选择要访问的云账号（可多选）",field:"account_id",op:"in",choices:[{label:"运维账号",value:"acc-ops-001"},{label:"研发账号",value:"acc-rd-002"},{label:"测试账号",value:"acc-test-003"}]}, {type:"variable",label:"仅自己的资源",desc:"自动匹配你的身份，只能看到自己创建的资源",field:"owner_id",op:"==",variable:"@currentUser",varLabel:"当前用户"}, {type:"input",label:"按标签过滤",desc:"输入标签名进行模糊匹配",field:"tags",op:"contains",placeholder:"如 web、prod"}`
);

// 4. CAPS dbview preset — add select + variable
js = rep(js, 'dbview',
  `{type:"all",label:"所有数据",desc:"无需填写"}, {type:"instance",label:"具体实例",desc:"勾选要访问的数据库实例",api:"/api/v1/databases"} ] } } },`,
  `{type:"all",label:"所有数据",desc:"无需填写"}, {type:"instance",label:"具体实例",desc:"勾选要访问的数据库实例",api:"/api/v1/databases"}, {type:"select",label:"选择数据库",desc:"从预设数据库中选择（单选）",field:"db_name",op:"==",choices:[{label:"CMDB 库",value:"db-cmdb"},{label:"订单库",value:"db-order"}]}, {type:"variable",label:"仅本部门数据",desc:"自动匹配你的所属部门",field:"owner_dept",op:"==",variable:"@currentOrg",varLabel:"当前组织"} ] } } },`
);

// 5. CAPS dba preset — replace expression with select
js = rep(js, 'dba',
  `{type:"all",label:"所有数据",desc:"无需填写"}, {type:"expression",label:"按库名条件",desc:"使用表达式过滤数据库",field:"db_name",op:"==",value:"db-cmdb",expr:'db_name == "db-cmdb"',examples:['db_name == "db-cmdb"','db_name in ["db-cmdb", "db-order"]']}, {type:"instance",label:"具体实例",desc:"勾选要访问的数据库实例",api:"/api/v1/databases"}`,
  `{type:"all",label:"所有数据",desc:"无需填写"}, {type:"select",label:"选择数据库",desc:"从预设数据库中选择（单选）",field:"db_name",op:"==",choices:[{label:"CMDB 库",value:"db-cmdb"},{label:"订单库",value:"db-order"},{label:"全部生产库",value:"db-prod-*"}]}, {type:"instance",label:"具体实例",desc:"勾选要访问的数据库实例",api:"/api/v1/databases"}`
);

// 6. CAPS cloudportal viewer — replace expression with multi_select + select + variable
js = rep(js, 'cloudportal',
  `{type:"all",label:"所有数据",desc:"无需填写"}, {type:"expression",label:"按账号条件",desc:"使用表达式过滤资源",field:"account_id",op:"==",value:"acc-ops-001",expr:'account_id == "acc-ops-001"',examples:['account_id == "acc-ops-001"']}`,
  `{type:"all",label:"所有数据",desc:"无需填写"}, {type:"multi_select",label:"选择云账号",desc:"选择要查看的云账号（可多选）",field:"account_id",op:"in",choices:[{label:"运维账号",value:"acc-ops-001"},{label:"研发账号",value:"acc-rd-002"}]}, {type:"select",label:"选择地域",desc:"选择目标地域",field:"region",op:"==",choices:[{label:"广州",value:"ap-guangzhou"},{label:"上海",value:"ap-shanghai"}]}, {type:"variable",label:"仅自己账号的资源",desc:"自动匹配你负责的云账号",field:"account_id",op:"==",variable:"@currentAccount",varLabel:"当前账号"}`
);

// 7. Add new helper functions + fix apScopeSel before initialization
js = js.replace(
  'renderAC(); goTab(0);',
  `// === New helper functions for scope types ===
function apScopeSelectVal(mc,v){const cur=apply.scope[mc];cur.selectedValue=v;mkApplyHTML();}
function apScopeMultiToggle(mc,v,on){const cur=apply.scope[mc]||(apply.scope[mc]={type:"multi_select",selectedValues:[],expr:"",instances:[]});const i=cur.selectedValues.indexOf(v);if(on&&i<0)cur.selectedValues.push(v);else if(!on&&i>=0)cur.selectedValues.splice(i,1);mkApplyHTML();}
function apScopeInput(mc,v){const cur=apply.scope[mc];cur.selectedValue=v;}

renderAC(); goTab(0);`
);

// 8. Fix apScopeSel to reset selectedValue/selectedValues
js = js.replace(
  'function apScopeSel(mc,type){ const cur=apply.scope[mc]||(apply.scope[mc]={type:"all",expr:"",instances:[]}); cur.type=type; cur.expr=""; mkApplyHTML(); }',
  'function apScopeSel(mc,type){ const cur=apply.scope[mc]||(apply.scope[mc]={type:"all",selectedValue:null,selectedValues:[],expr:"",instances:[]}); cur.type=type; cur.selectedValue=null; cur.selectedValues=[]; cur.expr=""; mkApplyHTML(); }'
);

// 9. Remove composeExpr function
const ceMatch = js.match(/function composeExpr\(field,op,value\)\{[\s\S]*?return \`\$\{field\} \$\{op==="!in"\?"!in":op\} \$\{v\}`;\}\n/);
if (ceMatch) {
  js = js.replace(ceMatch[0], '');
  console.log('  ✅ composeExpr removed');
} else {
  console.log('  ❌ composeExpr NOT FOUND');
}

// ===== Reassemble =====
const full = before + js + after;

// ===== Verify =====
const m = full.match(/<script>([\s\S]*?)<\/script>/);
if (m) {
  try {
    require('vm').compileFunction(m[1]);
    console.log('✅ JS syntax OK');
  } catch (e) {
    const stack = e.stack || '';
    const lineMatch = stack.match(/:(\d+):\d+/);
    if (lineMatch) {
      const lineNum = parseInt(lineMatch[1]);
      const lines = m[1].split('\n');
      console.log('❌ JS Error at line ' + lineNum + ':', e.message);
      console.log('  ' + (lines[lineNum - 1] || '').substring(0, 200));
    } else {
      console.log('❌ JS Error:', e.message);
    }
  }
}

fs.writeFileSync(dst, full);
console.log('Written to', dst);
