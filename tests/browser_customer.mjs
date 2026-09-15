// End-to-end checks against the disposable browser fixture: customer portal.
// Register, persist a cart request, follow the status, staff side manages it.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const base=process.env.BROWSER_BASE_URL || 'http://127.0.0.1:5001',out=process.env.BROWSER_OUTPUT_DIR || 'docs/customer/browser';
const emailE2E = process.env.BROWSER_EMAIL_E2E === '1' || process.argv.includes('--email-e2e');
await fs.mkdir(out,{recursive:true});
const credentials=JSON.parse(await fs.readFile('instance/commercial-check/credentials.json','utf8'));
const targets=await (await fetch('http://127.0.0.1:9222/json/list')).json();
const ws=new WebSocket(targets.find(t=>t.type==='page').webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ws.onopen=resolve;ws.onerror=reject;});
let seq=0;const pending=new Map(),results=[],errors=[];
ws.onmessage=event=>{const m=JSON.parse(event.data);if(m.id){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result);}if(m.method==='Runtime.exceptionThrown')errors.push(m.params.exceptionDetails.text);};
function call(method,params={}){return new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});}
async function evaluate(expression){const r=await call('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function until(expression){for(let i=0;i<150;i++){if(await evaluate(expression))return;await new Promise(r=>setTimeout(r,100));}throw Error(expression.includes('/cuenta/verificar/') || expression.includes('/cuenta/restablecer/') ? 'Timeout on account link' : 'Timeout: '+expression);}
async function navigate(path){await call('Page.navigate',{url:base+path});await until(`document.readyState==='complete' && location.pathname===${JSON.stringify(path.split('?')[0])}`);}
async function check(name,expression){assert.ok(await evaluate(expression),name);results.push(name);}
async function fill(values){await evaluate(`(()=>{const values=${JSON.stringify(values)};for(const [name,value] of Object.entries(values)){const el=document.querySelector('[name="'+name+'"]');if(!el)throw Error('Missing '+name);el.value=value;el.dispatchEvent(new Event('change',{bubbles:true}));}})()`);}
async function submit(selector,path){await evaluate(`document.querySelector(${JSON.stringify(selector)}).requestSubmit()`);await until(`document.readyState==='complete' && ${path}`);}
async function screenshot(name){const r=await call('Page.captureScreenshot',{format:'png',captureBeyondViewport:true});await fs.writeFile(out+'/'+name+'.png',Buffer.from(r.data,'base64'));}
async function postAction(action,values={}){await evaluate(`(()=>{const form=[...document.forms].find(f=>f.action.endsWith(${JSON.stringify(action)}));if(!form)throw Error('Missing form');for(const [name,value] of Object.entries(${JSON.stringify(values)})){form.elements.namedItem(name).value=value;}form.requestSubmit();})()`);await new Promise(r=>setTimeout(r,400));await until(`document.readyState==='complete'`);}
async function loginAdmin(){await navigate('/login');await fill({username:'browser_admin',password:credentials.admin});await submit('form',`location.pathname==='/admin/' || location.pathname==='/admin'`);}
async function capture(email){
 const response=await fetch(base+'/__test/mail',{headers:{'X-Test-Key':credentials.mail_capture}});
 assert.equal(response.status,200,'Local fake capture accessible');
 return (await response.json()).filter(m=>m.to===email);
}
async function emailPath(email){
 const messages=await capture(email);
 const link=messages.at(-1).body.match(/http:\/\/127\.0\.0\.1:\d+(\/\S+)/);
 assert.ok(link,'Fake email contains local link');
 return link[1];
}
try{
 await call('Page.enable');await call('Runtime.enable');await call('Network.enable');await call('Network.setCacheDisabled',{cacheDisabled:true});await call('Network.clearBrowserCookies');
 await call('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
 await navigate('/');
 await evaluate(`localStorage.clear();sessionStorage.clear();Yoli.counters()`);
 await check('Anonymous navbar links to Cuenta',`!!document.querySelector('a[href="/cuenta/login"]')`);
 const email='e2e.'+Date.now()+'@example.com';
 await navigate('/registro');
 await fill({name:'Cliente E2E',email,phone:'0991234567',password:'clave-e2e-segura-de-prueba',confirm:'clave-e2e-segura-de-prueba'});
 await submit('form[action="/registro"]',emailE2E ? `location.pathname==='/cuenta/verificacion-pendiente'` : `location.pathname==='/cuenta'`);
 if(emailE2E){
  const link=await emailPath(email);
  // No screenshots, token logging or persistent capture of bearer URLs.
  await navigate(link);
  await submit('main form',`location.pathname==='/cuenta'`);
  await check('Email verified with fake delivery',`document.body.textContent.includes('Correo: verificado')`);
  await postAction('/cuenta/logout');
  await navigate('/cuenta/login');await fill({email,password:'clave-e2e-segura-de-prueba'});
  await submit('form[action="/cuenta/login"]',`location.pathname==='/cuenta'`);
 }
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
 await evaluate(`Yoli.write('favorites', ['FY.EZE.777']); window.originalCart = localStorage.getItem('yoli.cart.v1'); window.realFetch = window.fetch; window.fetch = async (...args) => { if(args[1]?.method === 'POST') throw new Error('Simulated network failure'); return window.realFetch(...args); }; document.querySelector('#quote-form').requestSubmit();`);
 await until(`!document.querySelector('#quote-submit').disabled`);
 await check('Failed submission preserves quantities sizes customization and favorites', `localStorage.getItem('yoli.cart.v1')===window.originalCart && Yoli.read('favorites')[0]==='FY.EZE.777' && document.querySelector('[data-cart-count]').textContent==='2'`);
 await evaluate(`window.fetch = async (...args) => {
   if (args[1]?.method !== 'POST') return window.realFetch(...args);
   args[1].body.set('delivery', 'invalid');
   return window.realFetch(...args);
 }; document.querySelector('#quote-form').requestSubmit();`);
 await until(`!document.querySelector('#quote-submit').disabled`);
 await check('Server validation error preserves the full cart', `localStorage.getItem('yoli.cart.v1')===window.originalCart`);
 await evaluate(`window.fetch = async (...args) => {
   const response = await window.realFetch(...args);
   if (args[1]?.method === 'POST') {
     const result = await response.json();
     window.savedRequest = result.request_id;
     throw Error('Simulated lost confirmation');
   }
   return response;
 }; document.querySelector('#quote-form').requestSubmit();`);
 await until(`!document.querySelector('#quote-submit').disabled`);
 await check('Lost confirmation preserves cart for safe retry', `Number.isInteger(window.savedRequest) && localStorage.getItem('yoli.cart.v1')===window.originalCart`);
 await evaluate(`document.addEventListener('yoli:change', () => {
   if(Yoli.read('cart').length===0) sessionStorage.setItem('e2e-header', document.querySelector('[data-cart-count]').textContent);
 });`);
 await evaluate(`window.fetch = async (...args) => {
   if (args[1]?.method !== 'POST') return window.realFetch(...args);
   window.postCount = (window.postCount || 0) + 1;
   const [a,b] = await Promise.all([window.realFetch(...args), window.realFetch(...args)]);
   const first = await a.clone().json(), second = await b.json();
   if(first.request_id !== second.request_id || first.request_id !== window.savedRequest) throw Error('Duplicate request');
   sessionStorage.setItem('e2e-deduplicated', String(first.request_id));
   return a;
 }; const form=document.querySelector('#quote-form');form.requestSubmit();form.requestSubmit();`);
 await check('Double click disables submission and sends once', `document.querySelector('#quote-submit').disabled && window.postCount===1`);
 await until(String.raw`/^\/cuenta\/pedido\/\d+$/.test(location.pathname) && document.readyState==='complete'`);
 await check('Success clears cart and header and preserves favorites', `Yoli.read('cart').length===0 && document.querySelector('[data-cart-count]').textContent==='0' && Yoli.read('favorites')[0]==='FY.EZE.777'`);
 await check('Header updates before navigation', `sessionStorage.getItem('e2e-header')==='0'`);
 await check('Concurrent server resubmission returns the same request', `sessionStorage.getItem('e2e-deduplicated')===location.pathname.split('/').pop()`);
 if(emailE2E){assert.equal((await capture(email)).length,2);results.push('Request confirmation delivered through fake backend');}
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
 if(emailE2E){
  assert.equal((await capture(email)).length,3);
  await postAction('/estado',{status:'processing'});
  assert.equal((await capture(email)).length,3);
  results.push('Real status change sends one fake update; same status sends none');
 }
 await check('Admin moves request into processing',`document.body.textContent.includes('En elaboración')`);
 assert.ok((await evaluate(`fetch('/cuenta/pedidos').then(r=>r.url)`)).includes('/cuenta/login'));results.push('Staff session cannot open the portal');
 await postAction('/logout');await until(`location.pathname==='/login'`);
 await navigate('/cuenta/login');
 await fill({email,password:'clave-e2e-segura-de-prueba'});
 await submit('form[action="/cuenta/login"]',`location.pathname==='/cuenta'`);
 await navigate(requestUrl);
 await check('Customer sees the updated status',`document.body.textContent.includes('En elaboración')`);
 await screenshot('request-processing-1440');
 if(emailE2E){
  await postAction('/cuenta/logout');await navigate('/cuenta/olvide-contrasena');
  await fill({email});
  await submit('main form',`document.body.textContent.includes('Si existe una cuenta activa')`);
  const link=await emailPath(email);await navigate(link);
  await fill({password:'nueva-clave-e2e-segura',confirm:'nueva-clave-e2e-segura'});
  await submit('main form',`location.pathname==='/cuenta/login'`);
  await fill({email,password:'clave-e2e-segura-de-prueba'});
  await submit('form[action="/cuenta/login"]',`document.body.textContent.includes('Correo o contraseña incorrectos')`);
  await fill({email,password:'nueva-clave-e2e-segura'});
  await submit('form[action="/cuenta/login"]',`location.pathname==='/cuenta'`);
  results.push('Fake recovery resets password; old password fails and new password works');
 }
 assert.deepEqual(errors,[]);results.push('No uncaught JavaScript errors');
}finally{await fs.writeFile(out+'/results.json',JSON.stringify({checks:results.length,results,errors},null,2)+'\n');ws.close();}
console.log(results.length+' customer portal Chrome checks passed.');