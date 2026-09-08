// New scopeOptRowHTML function - read by build script
// DO NOT put backticks at start/end - they are added by the build script
module.exports = `function scopeOptRowHTML(pi,mc,o,oi,app){
  const base=\`<span style="font-size:16px;">\${scopeIcon(o.type)}</span><span class="tag" style="background:var(--brand-soft);color:var(--brand-strong);border-color:#c9dbff;">\${SCOPE_OPT_LABEL[o.type]||o.type}</span><input class="form-control" style="flex:0 0 120px;height:30px;" value="\${o.label}" oninput="pEdit(\${pi},'soptLabel','\${mc}',\${oi},this.value)">\`;
  const delBtn=\`<button class="btn btn-ghost btn-sm" onclick="pEdit(\${pi},'soptDel','\${mc}',\${oi})">✕</button>\`;
  if(o.type==="select"||o.type==="multi_select"){
    const choices=o.choices||[];
    const model=app.models.find(mm=>mm.code===mc); const fields=model?model.fields:[];
    return \`<div class="scope-opt-row" style="flex-direction:column;">\${base}\${delBtn}
      <div style="width:100%;margin-top:4px;">
        <div style="display:flex;gap:8px;align-items:center;margin-bottom:6px;">
          <select class="form-control form-select" style="flex:0 0 120px;height:30px;" onchange="pEdit(\${pi},'soptField','\${mc}',\${oi},this.value)"><option value="">字段…</option>\${fields.map(f=>\`<option value="\${f.name}" \${o.field===f.name?'selected':''}>\${f.name}</option>\`).join('')}</select>
          <select class="form-control form-select" style="flex:0 0 80px;height:30px;" onchange="pEdit(\${pi},'soptOp','\${mc}',\${oi},this.value)">\${["==","!=","in","!in"].map(op=>\`<option value="\${op}" \${o.op===op?'selected':''}>\${op}</option>\`).join('')}</select>
          <span style="font-size:11px;color:var(--text-tertiary);">→ 选项列表：</span>
        </div>
        <div class="choice-chips">\${choices.map((ch,ci)=>\`<span class="choice-chip"><span class="cc-label">\${ch.label}</span><span class="cc-value">\${ch.value}</span><span class="cc-x" onclick="pEdit(\${pi},'soptChoiceDel','\${mc}',\${oi},\${ci})">×</span></span>\`).join('')}</div>
        <div style="display:flex;gap:6px;margin-top:6px;">
          <input class="form-control" style="flex:1;height:28px;font-size:11px;" placeholder="显示名" id="chL_\${pi}_\${mc}_\${oi}">
          <input class="form-control" style="flex:1;height:28px;font-size:11px;" placeholder="值(value)" id="chV_\${pi}_\${mc}_\${oi}">
          <button class="btn btn-ghost btn-sm" style="height:28px;" onclick="pEdit(\${pi},'soptChoiceAdd','\${mc}',\${oi})">＋ 添加</button>
        </div>
      </div>
    </div>\`;}
  if(o.type==="variable"){
    return \`<div class="scope-opt-row" style="flex-direction:column;">\${base}\${delBtn}
      <div style="width:100%;margin-top:4px;"><div style="display:flex;gap:8px;align-items:center;">
        <select class="form-control form-select" style="flex:0 0 120px;height:30px;" onchange="pEdit(\${pi},'soptField','\${mc}',\${oi},this.value)"><option value="">字段…</option>\${(app.models.find(mm=>mm.code===mc)?.fields||[]).map(f=>\`<option value="\${f.name}" \${o.field===f.name?'selected':''}>\${f.name}</option>\`).join('')}</select>
        <select class="form-control form-select" style="flex:0 0 80px;height:30px;" onchange="pEdit(\${pi},'soptOp','\${mc}',\${oi},this.value)">\${["==","!="].map(op=>\`<option value="\${op}" \${o.op===op?'selected':''}>\${op}</option>\`).join('')}</select>
        <select class="form-control form-select" style="flex:1;height:30px;" onchange="pEdit(\${pi},'soptVariable','\${mc}',\${oi},this.value)">
          <option value="@currentUser" \${o.variable==='@currentUser'?'selected':''}>@currentUser（当前用户）</option>
          <option value="@currentOrg" \${o.variable==='@currentOrg'?'selected':''}>@currentOrg（当前组织）</option>
          <option value="@currentGroup" \${o.variable==='@currentGroup'?'selected':''}>@currentGroup（当前自建组）</option>
          <option value="@currentAccount" \${o.variable==='@currentAccount'?'selected':''}>@currentAccount（当前账号）</option>
        </select>
      </div></div>
      <div class="var-display"><span class="var-icon">🔄</span><span class="var-text">applicant 看到：<b>\${o.varLabel||o.variable}</b>，运行时自动解析，无需手动填写</span></div>
    </div>\`;}
  if(o.type==="input"){
    return \`<div class="scope-opt-row" style="flex-direction:column;">\${base}\${delBtn}
      <div style="width:100%;margin-top:4px;"><div style="display:flex;gap:8px;align-items:center;">
        <select class="form-control form-select" style="flex:0 0 120px;height:30px;" onchange="pEdit(\${pi},'soptField','\${mc}',\${oi},this.value)"><option value="">字段…</option>\${(app.models.find(mm=>mm.code===mc)?.fields||[]).map(f=>\`<option value="\${f.name}" \${o.field===f.name?'selected':''}>\${f.name}</option>\`).join('')}</select>
        <select class="form-control form-select" style="flex:0 0 100px;height:30px;" onchange="pEdit(\${pi},'soptOp','\${mc}',\${oi},this.value)">\${["==","!=","contains","startsWith","in"].map(op=>\`<option value="\${op}" \${o.op===op?'selected':''}>\${op}</option>\`).join('')}</select>
        <input class="form-control" style="flex:1;height:30px;" value="\${o.placeholder||''}" placeholder="placeholder 提示" oninput="pEdit(\${pi},'soptPlaceholder','\${mc}',\${oi},this.value)">
      </div></div>
      <div class="info-box cyan" style="margin-top:6px;margin-bottom:0;">⌨️ applicant 看到文本输入框，自由填写值</div>
    </div>\`;}
  return \`<div class="scope-opt-row">\${base}\${delBtn}<span class="mono" style="color:var(--text-tertiary);font-size:11px;">\${o.desc||''}</span></div>\`;
}`;
