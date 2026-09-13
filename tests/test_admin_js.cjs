'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let count=0;
function fixture(){
 const handlers={},elements={},rows=[];
 const document={addEventListener:(name,fn)=>handlers[name]=fn,getElementById:id=>elements[id]||null,querySelector:()=>null};
 const window={print:()=>window.printed=true};
 vm.runInNewContext(fs.readFileSync('app/static/js/admin.js','utf8'),{document,window,history:{back(){}},navigator:{}});
 return {handlers,elements,rows,window};
}
function check(name,fn){fn();console.log('OK '+name);count++;}
check('Print button invokes native print',()=>{const f=fixture();f.handlers.click({target:{closest:s=>s==='[data-print]'?{}:null}});assert.equal(f.window.printed,true);});
check('Remove button only removes its row',()=>{let removed=false;const f=fixture();f.handlers.click({target:{closest:s=>s==='[data-remove-row]'?{closest:()=>({remove:()=>removed=true})}:null}});assert.equal(removed,true);});
check('Row additions are capped',()=>{const f=fixture();let added=false;f.elements.t={content:{firstElementChild:{cloneNode:()=>({})}}};f.elements.r={children:Array(50),append:()=>added=true};f.handlers.click({target:{closest:s=>s==='[data-add-row]'?{dataset:{addRow:'t',target:'r'}}:null}});assert.equal(added,false);});
check('Menu maintains expanded state',()=>{const f=fixture();let state,open;f.elements['admin-nav']={classList:{toggle:(key,value)=>open=value}};f.handlers.click({target:{closest:s=>s==='.nav-toggle'?{getAttribute:()=> 'false',setAttribute:(key,value)=>state=value}:null}});assert.equal(state,'true');assert.equal(open,true);});
check('Changing product excludes incompatible recipes and estimates',()=>{
 const f=fixture();
 const recipe={value:'7',options:[{value:'',dataset:{}},{value:'7',dataset:{product:'1'}}]};
 recipe.selectedOptions=[recipe.options[1]];
 const estimate={value:'',options:[{value:'',dataset:{}}]};estimate.selectedOptions=[estimate.options[0]];
 const row={querySelector:s=>s==='[name=item_product_id]'?{value:'2'}:s==='[name=item_recipe_id]'?recipe:estimate};
 f.handlers.change({target:{name:'item_product_id',closest:()=>row}});
 assert.equal(recipe.value,'');assert.equal(recipe.options[1].disabled,true);assert.equal(recipe.options[1].hidden,true);
});
check('Selecting recipe copies variant and clears competing estimate',()=>{
 const f=fixture(),estimate={value:'8'},size={value:''};
 const row={querySelector:s=>s==='[name=item_estimate_id]'?estimate:size};
 f.handlers.change({target:{name:'item_recipe_id',value:'7',selectedOptions:[{dataset:{size:'TEST variante'}}],closest:()=>row}});
 assert.equal(estimate.value,'');assert.equal(size.value,'TEST variante');
});
console.log(`${count} admin JavaScript tests passed.`);
