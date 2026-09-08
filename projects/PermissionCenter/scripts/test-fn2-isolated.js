// Test the function in isolation
const fn2 = `function apScopeMultiToggle(mc,v,on){const cur=apply.scope[mc]||(apply.scope[mc]={type:"multi_select",selectedValues:[],expr:"",instances:[]});const i=cur.selectedValues.indexOf(v);on&&i<0?cur.selectedValues.push(v):(!on&&i>=0?cur.selectedValues.splice(i,1));mkApplyHTML();}`;

try {
  new Function(fn2);
  console.log('fn2 syntax OK');
} catch(e) {
  console.log('fn2 syntax error:', e.message);
  // Try to find the issue
  const lines = fn2.split('\n');
  console.log('Lines:', lines.length);
  console.log('Full:', fn2);
}

// Try simpler version
const fn2simple = `function apScopeMultiToggle(mc,v,on){const cur=apply.scope[mc]||(apply.scope[mc]={type:"multi_select",selectedValues:[],expr:"",instances:[]});const i=cur.selectedValues.indexOf(v);if(on&&i<0)cur.selectedValues.push(v);else if(!on&&i>=0)cur.selectedValues.splice(i,1);mkApplyHTML();}`;
try {
  new Function(fn2simple);
  console.log('fn2simple syntax OK');
} catch(e) {
  console.log('fn2simple syntax error:', e.message);
}
