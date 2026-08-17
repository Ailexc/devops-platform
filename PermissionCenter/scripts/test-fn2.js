#!/usr/bin/env node
const fs = require('fs');
const v10 = fs.readFileSync('docs/capability-apply-demo-v10.html', 'utf8');
const scriptStart = v10.indexOf('<script>') + '<script>'.length;
const scriptEnd = v10.indexOf('</script>');
const before = v10.substring(0, scriptStart);
const after = v10.substring(scriptEnd);
let js = v10.substring(scriptStart, scriptEnd);

const fn2 = `function apScopeMultiToggle(mc,v,on){const cur=apply.scope[mc]||(apply.scope[mc]={type:"multi_select",selectedValues:[],expr:"",instances:[]});const i=cur.selectedValues.indexOf(v);on&&i<0?cur.selectedValues.push(v):(!on&&i>=0?cur.selectedValues.splice(i,1));mkApplyHTML();}`;

js = js.replace('renderAC(); goTab(0);', fn2 + ' renderAC(); goTab(0);');
const full = before + js + after;
const m = full.match(/<script>([\s\S]*?)<\/script>/);
try { require('vm').compileFunction(m[1]); console.log('fn2 via file: OK'); } catch(e) { console.log('fn2 via file: Error -', e.message); }
