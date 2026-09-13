// End-to-end checks against the disposable browser fixture: customer portal.
// Register, persist a cart request, follow the status, staff side manages it.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const base=process.env.BROWSER_BASE_URL || 'http://127.0.0.1:5001',out=process.env.BROWSER_OUTPUT_DIR || 'docs/customer/browser';
await fs.mkdir(out,{recursive:true});
const credentials=JSON.parse(await fs.readFile('instance/commercial-check/credentials.json','utf8'));
const targets=await (await fetch('http://127.0.0.1:9222/json/list')).json();
const ws=new WebSocket(targets.find(t=>t.type==='page').webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
let seq=0;const pending=new Map(),results=[],errors=[];
ws.onmessage=event=>{const m=JSON.parse(event.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);};
function call(method,params={}){return new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});}
async function evaluate(expression){const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function until(expression){for(let i=0;i<150;i++){if(await evaluate(expression))return;await new Promise(r=>setTimeout(r,100));}throw Error('Timeout: '+expression);}
async function navigate(path){await call('Page.navigate',{url:base+path});await until(`document.readyState==='complete' && location.pathname===${JSON.stringify(path.split('?')[0])}`);}
async function check(name,expression){assert.ok(await evaluate(expression),name);results.push(name);}
async function fill(values){await evaluate(`(()=>{const values=${JSON.stringify(values)};for(const [name,value] of Object.entries(values)){const el=document.querySelector('[name="'+name+'"]');if(!el)throw Error('Missing '+name);el.value=value;el.dispatchEvent(new Event('change',{bubbles:true}));}})()`);}
async function submit(selector,path){await evaluate(`document.querySelector(${JSON.stringify(selector)}).requestSubmit()`);await until(`document.readyState==='complete' && ${path}`);}
async function screenshot(name){const r=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await fs.writeFile(out+'/'+name+'.png',Buffer.from(r.data,'base64'));}
async function postAction(action,values={}){await evaluate(`(()=>{const form=[...document.forms].find(f=>f.action.endsWith(${JSON.stringify(action)}));if(!form)throw Error('Missing form');for(const [name,value] of Object.entries(${JSON.stringify(values)})){form.elements.namedItem(name).value=value;}form.requestSubmit();})()`);await new Promise(r=>setTimeout(r,400));await until(`document.readyState==='complete'`);}
async function loginAdmin(){await navigate('/login');await fill({username:'browser_admin',password:credentials.admin});await submit('form',`location.pathname==='/admin/' || location.pathname==='/admin'`);}
try{
 await call('Page.enable');await call('Runtime.enable');await call('Network.enable');await call('Network.setCacheDisabled',{cacheDisabled:true});await call('Network.clearBrowserCookies');
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
 await navigate('/');
 await check('Anonymous navbar links to Cuenta',`!!document.querySelector('a[href="/cuenta/login"]')`);
 const email='e2e.'+Date.now()+'@example.com';
 await navigate('/registro');
 await fill({name:'Cliente E2E',email,phone:'0991234567',password:'clave-e2e-segura-de-prueba',confirm:'clave-e2e-segura-de-prueba'});
 await submit('form[action="/registro"]',`location.pathname==='/cuenta'`);
 await check('Registration lands on panel with greeting',`document.querySelector('h1').textContent==='Hola, Cliente E2E'`);
 await check('Authenticated navbar links to Mi cuenta',`!!document.querySelector('a[href="/cuenta"]') && !!document.querySelector('form.nav-logout')`);
 await screenshot('panel-1440');
 await navigate('/producto/figura-e2e-del-portal');
 await fill({requested_size:'20 cm',personalization:'Nombre E2E',quantity:'2'});
 await evaluate(`document.querySelector('#product-form').requestSubmit()`);
 await navigate('/carrito');
 await until(`document.querySelectorAll('.cart-item').length===1`);
 await check('Cart uses the account form',`!!document.querySelector('form[action="/cuenta/pedidos"]') && document.querySelector('#quote-submit').textContent.includes('Guardar mi solicitud')`);
 await fill({delivery:'shipping',notes:'Solicitud E2E para coordinar'});
 await submit('#quote-form',String.raw`/^\/cuenta\/pedido\/\d+$/.test(location.pathname)`);
 const requestId=await evaluate(`location.pathname.split('/').pop()`);
 const requestUrl='/cuenta/pedido/'+requestId;
 await check('Persisted request shown with pending status',`document.body.textContent.includes('Lo que pediste') && document.body.textContent.includes('Por atender')`);
 await check('No cost or margin language on the customer detail',`!/costo de producción|margen|ganancia|unit_price/i.test(document.body.textContent)`);
 await screenshot('request-detail-1440');
 for(const width of [1440,768,390,320]){
  await call('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<768});
  for(const [path,label] of [['/cuenta','panel'],['/cuenta/pedidos','requests'],['/cuenta/perfil','profile'],[requestUrl,'request']]){
   await navigate(path);
   await check(label+' fits viewport '+width,`document.documentElement.scrollWidth<=innerWidth`);
   await screenshot(label+'-'+width);
  }
 }
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
 await navigate('/cuenta/perfil');
 await fill({address:'Av. de prueba 123',city:'Quito'});
 await submit('form[action="/cuenta/perfil"]',`location.pathname==='/cuenta/perfil'`);
 await check('Profile edits persist',`document.querySelector('[name=city]').value==='Quito' && document.querySelector('[name=address]').value==='Av. de prueba 123'`);
 await postAction('/cuenta/logout');await until(`location.pathname==='/cuenta/login'`);
 await check('Logout returns to login with anonymous navbar',`!!document.querySelector('a[href="/cuenta/login"]')`);
 assert.ok((await evaluate(`fetch('/cuenta/pedidos').then(r=>r.url)`)).includes('/cuenta/login'));results.push('Portal session closed after logout');
 await navigate('/cuenta/login');
 await fill({email,password:'clave-e2e-segura-de-prueba'});
 await submit('form[action="/cuenta/login"]',`location.pathname==='/cuenta'`);
 await check('Customer logs back in',`document.querySelector('h1').textContent==='Hola, Cliente E2E'`);
 assert.ok((await evaluate(`fetch('/admin').then(r=>r.url)`)).includes('/login'));results.push('Customer session never reaches /admin');
 await loginAdmin();
 await navigate('/admin/pedidos/'+requestId);
 await check('Admin opens customer request as pending',`document.body.textContent.includes('Por atender')`);
 await postAction('/estado',{status:'processing'});
 await check('Admin moves request into processing',`document.body.textContent.includes('En elaboración')`);
 assert.ok((await evaluate(`fetch('/cuenta/pedidos').then(r=>r.url)`)).includes('/cuenta/login'));results.push('Staff session cannot open the portal');
 await postAction('/logout');await until(`location.pathname==='/login'`);
 await navigate('/cuenta/login');
 await fill({email,password:'clave-e2e-segura-de-prueba'});
 await submit('form[action="/cuenta/login"]',`location.pathname==='/cuenta'`);
 await navigate(requestUrl);
 await check('Customer sees the updated status',`document.body.textContent.includes('En elaboración')`);
 await screenshot('request-processing-1440');
 assert.deepEqual(errors,[]);results.push('No uncaught JavaScript errors');
}finally{await fs.writeFile(out+'/results.json',JSON.stringify({checks:results.length,results,errors},null,2)+'\n');ws.close();}
console.log(results.length+' customer portal Chrome checks passed.');