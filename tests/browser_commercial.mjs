// End-to-end checks against the disposable browser_commercial_server fixture only.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const base=process.env.BROWSER_BASE_URL || 'http://127.0.0.1:5001',out=process.env.BROWSER_OUTPUT_DIR || 'docs/commercial/admin-browser';
await fs.mkdir(out,{recursive:true});
const materialName='TEST Material navegador '+Date.now();
const credentials=JSON.parse(await fs.readFile('instance/commercial-check/credentials.json','utf8'));
const targets=await (await fetch('http://127.0.0.1:9222/json/list')).json();
const ws=new WebSocket(targets.find(t=>t.type==='page').webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
let seq=0;const pending=new Map(),results=[],errors=[];
ws.onmessage=event=>{const m=JSON.parse(event.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);};
function call(method,params={}){return new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});}
async function evaluate(expression){const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function until(expression){for(let i=0;i<100;i++){if(await evaluate(expression))return;await new Promise(r=>setTimeout(r,100));}throw Error('Timeout: '+expression);}
async function navigate(path){await call('Page.navigate',{url:base+path});await until(`document.readyState==='complete' && location.pathname===${JSON.stringify(path.split('?')[0])}`);}
async function check(name,expression){assert.ok(await evaluate(expression),name);results.push(name);}
async function fill(values){await evaluate(`(()=>{const values=${JSON.stringify(values)};for(const [name,value] of Object.entries(values)){const el=document.querySelector('[name="'+name+'"]');if(!el)throw Error('Missing '+name);el.value=value;el.dispatchEvent(new Event('change',{bubbles:true}));}})()`);}
async function submit(selector,path){await evaluate(`document.querySelector(${JSON.stringify(selector)}).requestSubmit()`);await until(`document.readyState==='complete' && ${path}`);}
async function screenshot(name){const r=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await fs.writeFile(out+'/'+name+'.png',Buffer.from(r.data,'base64'));}
async function login(role){await navigate('/login');await fill({username:'browser_'+role,password:credentials[role]});await submit('form',`location.pathname==='/admin/' || location.pathname==='/admin'`);}
async function postAction(action,values={}){await evaluate(`(()=>{const form=[...document.forms].find(f=>f.action.endsWith(${JSON.stringify(action)}));if(!form)throw Error('Missing form');for(const [name,value] of Object.entries(${JSON.stringify(values)})){form.elements.namedItem(name).value=value;}form.requestSubmit();})()`);await new Promise(r=>setTimeout(r,400));await until(`document.readyState==='complete'`);}
try{
 await call('Page.enable');await call('Runtime.enable');await call('Network.enable');await call('Network.setCacheDisabled',{cacheDisabled:true});await call('Network.clearBrowserCookies');
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
 await call('Page.navigate',{url:base+'/admin'});await until(`location.pathname==='/login' && document.readyState==='complete'`);results.push('Administrative routes redirect anonymous users to login');
 await screenshot('login');await login('admin');
 await check('Admin dashboard and configuration menu',`document.querySelector('h1').textContent==='Resumen' && !!document.querySelector('a[href="/admin/configuracion"]')`);
 await screenshot('dashboard-1440');
 await navigate('/admin/clientes/nuevo');await fill({name:'TEST Cliente navegador '+Date.now(),phone:'0990000000',city:'Ciudad de prueba'});await submit('form.panel',String.raw`/^\/admin\/clientes\/\d+$/.test(location.pathname)`);
 await check('Customer created with optional fields empty',`document.querySelector('h1').textContent.includes('TEST Cliente navegador')`);
 const customerId=await evaluate(`location.pathname.split('/').pop()`);
 await navigate('/admin/costos/materiales');
 await fill({name:materialName,unit:'hoja',unit_cost:'0.10'});
 await submit('form.panel',`document.body.textContent.includes(${JSON.stringify(materialName)})`);
 await navigate('/admin/costos');
 await evaluate(`(()=>{const picker=document.getElementById('material-picker');picker.value=[...picker.options].find(o=>o.dataset.name===${JSON.stringify(materialName)}).value;picker.dispatchEvent(new Event('change'));document.querySelector('[data-add-row="indirect-template"]').click();})()`);
 await check('Saved material is linked and its cost is read only',`!!document.querySelector('[name=material_id]').value && document.querySelector('[name=material_cost]').readOnly`);
 await fill({product_id:'1',requested_size:'20 cm',personalization:'TEST Nombre de prueba',material_name:materialName,material_quantity:'2.5',material_unit:'hoja',material_cost:'0.10',indirect_name:'TEST Embalaje prueba',indirect_amount:'0.15',labor_time:'30',labor_unit:'minutes',hourly_cost:'4',profit_method:'margin',profit_percentage:'20',quantity:'2'});
 await check('Margin explanation distinct from markup',`document.getElementById('profit-formula').textContent.includes('÷')`);
 await submit('form.cost-form',`!!document.getElementById('cost-result')`);
 await check('Server calculates materials labor margin and configured tax',`document.getElementById('cost-result').textContent.includes('6.60') && document.getElementById('cost-result').textContent.includes('Margen sobre precio')`);
 await screenshot('cost-result-1440');
 const estimateId=await evaluate(`document.querySelector('[name=estimate_id]').value`);
 await fill({name:'TEST Receta navegador',notes:'Receta sintética de prueba'});
 await submit('form.recipe-save',`location.search.includes('receta=') && !document.getElementById('cost-result')`);
 await check('Cost recipe saved and reopenable',`document.querySelector('[name=material_name]').value===${JSON.stringify(materialName)}`);
 const recipeId=await evaluate(`new URLSearchParams(location.search).get('receta')`);
 await navigate('/admin/cotizaciones/nueva?calculo='+estimateId);
 await fill({customer_id:customerId});
 await submit('main form',String.raw`/^\/admin\/cotizaciones\/\d+$/.test(location.pathname)`);
 const quoteId=await evaluate(`location.pathname.split('/').pop()`);
 await check('Quote saved as draft with exact server total',`document.querySelector('.document').textContent.includes('6.60') && document.querySelector('.document').textContent.includes('Borrador')`);
 await navigate('/admin/cotizaciones/'+quoteId+'/whatsapp');
 await check('WhatsApp text includes code and does not imply acceptance',`document.querySelector('textarea').value.includes('FY.AN.001') && document.body.textContent.includes('no registra envío ni aceptación')`);
 await navigate('/admin/cotizaciones/'+quoteId);
 await check('Opening WhatsApp leaves quote draft',`document.querySelector('.document').textContent.includes('Borrador')`);
 await postAction('/estado',{status:'sent'});await check('Quote sent explicitly',`document.querySelector('.document').textContent.includes('Enviada')`);
 await postAction('/estado',{status:'accepted'});await check('Acceptance recorded explicitly',`document.querySelector('.document').textContent.includes('Aceptada')`);
 await postAction('/facturar');await until(String.raw`/^\/admin\/facturas\/\d+$/.test(location.pathname)`);
 const invoiceId=await evaluate(`location.pathname.split('/').pop()`);
 await check('Accepted quote converts to internal draft invoice',`document.querySelector('.document').textContent.includes('FAC-') && document.querySelector('.document').textContent.includes('Borrador')`);
 await postAction('/estado',{status:'issued'});await check('Invoice issued',`document.querySelector('.document').textContent.includes('Emitida')`);
 await postAction('/estado',{status:'paid',payment_method:'transferencia'});await check('Manual payment recorded',`document.querySelector('.document').textContent.includes('Pagada') && document.querySelector('.document').textContent.includes('transferencia')`);
 await screenshot('paid-invoice-1440');
 await navigate('/admin/facturas/'+invoiceId+'/imprimir');
 await check('Print invoice has internal disclaimer and print button',`!!document.querySelector('[data-print]') && document.body.textContent.includes('no constituye comprobante electrónico autorizado')`);
 await call('Emulation.setEmulatedMedia',{media:'print'});await screenshot('invoice-print');await call('Emulation.setEmulatedMedia',{media:''});
 for(const width of [1440,768,390,320]){
  await call('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<768});
  for(const [path,label] of [['/admin','dashboard'],['/admin/clientes/'+customerId,'customer-history'],['/admin/costos?receta='+recipeId,'costs'],['/admin/cotizaciones/nueva','quote-form'],['/admin/costos/materiales','materials'],['/admin/costos/recetas','recipes'],['/admin/clientes','customers'],['/admin/usuarios','users'],['/admin/configuracion','configuration'],['/admin/cotizaciones','quotes'],['/admin/facturas','invoices'],['/admin/facturas/'+invoiceId,'invoice']]){
   await navigate(path);
   await check(`${label} fits viewport ${width}`,`document.documentElement.scrollWidth<=innerWidth`);
   await screenshot(label+'-'+width);
  }
 }
 await postAction('/logout');await until(`location.pathname==='/login'`);results.push('Logout removes administrative session');
 await login('vendedor');
 await check('Seller menu excludes users and configuration',`!document.querySelector('a[href="/admin/usuarios"]') && !document.querySelector('a[href="/admin/configuracion"]')`);
 assert.equal(await evaluate(`fetch('/admin/costos').then(r=>r.status)`),403);results.push('Seller cannot access internal calculator');
 const denied=await evaluate(`fetch('/admin/usuarios').then(r=>r.status)`);assert.equal(denied,403);results.push('Seller cannot access users even by direct URL');
 await postAction('/logout');await until(`location.pathname==='/login'`);
 assert.deepEqual(errors,[]);results.push('No uncaught JavaScript errors');
}finally{await fs.writeFile(out+'/results.json',JSON.stringify({checks:results.length,results,errors},null,2)+'\n');ws.close();}
console.log(results.length+' commercial Chrome checks passed.');
