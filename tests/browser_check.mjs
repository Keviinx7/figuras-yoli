// Real Chrome / DevTools integration. Uses only localhost and a disposable browser profile.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const baseline = process.argv.includes('--names-baseline');
const outputDir = 'docs/name-review';
const targets = await (await fetch('http://127.0.0.1:9222/json/list')).json();
const ws = new WebSocket(targets.find(t => t.type === 'page').webSocketDebuggerUrl);
await new Promise((resolve, reject) => { ws.onopen = resolve; ws.onerror = reject; });
let sequence = 0;
const pending = new Map(), errors = [], results = [];
ws.onmessage = event => {
  const message = JSON.parse(event.data);
  if (message.id) {
    const request = pending.get(message.id); pending.delete(message.id);
    if (message.error) request.reject(Error(JSON.stringify(message.error))); else request.resolve(message.result);
  }
  if (message.method === 'Runtime.exceptionThrown') errors.push(message.params.exceptionDetails.text);
};
function call(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++sequence; pending.set(id, {resolve, reject}); ws.send(JSON.stringify({id, method, params}));
  });
}
async function evaluate(expression) {
  const result = await call('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
  if (result.exceptionDetails) throw Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function until(expression) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (await evaluate(expression)) return;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw Error('Timed out: ' + expression);
}
async function navigate(path) {
  await call('Page.navigate', {url: 'http://127.0.0.1:5000' + path});
  await until(`location.pathname === ${JSON.stringify(path.split('?')[0])} && document.readyState === 'complete' && !!window.Yoli`);
}
async function check(name, expression) { assert.ok(await evaluate(expression), name); results.push(name); }
async function screenshot(name) {
  await evaluate(`Promise.all([...document.images].map(i => { i.loading = 'eager'; return i.decode().catch(() => {}); }))`);
  const {data} = await call('Page.captureScreenshot', {format: 'png', captureBeyondViewport: true});
  await fs.writeFile(`${outputDir}/${name}.png`, Buffer.from(data, 'base64'));
}
try {
  await call('Page.enable'); await call('Runtime.enable');
  await call('Network.enable'); await call('Network.setCacheDisabled', {cacheDisabled: true});
  await call('Emulation.setDeviceMetricsOverride', {width: 1440, height: 1000, deviceScaleFactor: 1, mobile: false});
  if (baseline) {
    await navigate('/catalogo?page=4');
    await screenshot('before-cards-desktop');
    results.push(await evaluate(`JSON.stringify([...document.querySelectorAll('.product-card')].map(c => ({name:c.querySelector('h3').textContent.trim(),top:c.offsetTop,buttonBottom:c.querySelector('[data-add-cart]').getBoundingClientRect().bottom})))`));
    await call('Emulation.setDeviceMetricsOverride', {width: 390, height: 844, deviceScaleFactor: 1, mobile: true});
    await screenshot('before-cards-mobile');
  } else {
  await navigate('/catalogo');
  await evaluate('localStorage.clear(); Yoli.counters()');
  await check('Catalog displays 173 real products and 12 first-page cards', `document.querySelector('.results-count').textContent.includes('173 productos') && document.querySelectorAll('.product-card').length === 12`);
  await evaluate(`Promise.all([...document.querySelectorAll('.product-card img')].map(i => { i.loading = 'eager'; return i.decode(); }))`);
  await check('Product photos load', `[...document.querySelectorAll('.product-card img')].every(i => i.complete && i.naturalWidth > 0 && !i.src.includes('placeholder'))`);
  await screenshot('catalog-desktop');
  await navigate('/catalogo?q=FY.%C3%91A.012');
  await check('Exact Ñ search', `document.querySelectorAll('.product-card').length === 1 && document.querySelector('.product-code').textContent === 'Código: FY.ÑA.012'`);
  await evaluate(`document.querySelector('[data-favorite]').click(); document.querySelector('[data-add-cart]').click()`);
  await check('Catalog buttons persist favorite and cart', `Yoli.read('favorites')[0] === 'FY.ÑA.012' && Yoli.read('cart')[0].product_code === 'FY.ÑA.012'`);
  await navigate('/favoritos');
  await until(`document.querySelectorAll('#favorites-list .product-card').length === 1`);
  await check('Favorite resolves actual product', `document.querySelector('#favorites-list .product-code').textContent === 'Código: FY.ÑA.012'`);
  await evaluate(`document.querySelector('[data-add-cart]').click()`);
  await navigate('/carrito');
  await until(`document.querySelectorAll('.cart-item').length === 1 && !document.getElementById('quote-submit').disabled`);
  await check('Cart persists and merges quantity', `document.getElementById('line-0-quantity').value === '2'`);
  await evaluate(`const q = document.getElementById('line-0-quantity'); q.value = '3'; q.dispatchEvent(new Event('change')); const p = document.getElementById('line-0-personalization'); p.value = 'Nombre de prueba Ñ'; p.dispatchEvent(new Event('change'));`);
  await check('Cart edit persists', `Yoli.read('cart')[0].quantity === 3 && Yoli.read('cart')[0].personalization === 'Nombre de prueba Ñ'`);
  await screenshot('cart-desktop');
  await evaluate(`document.getElementById('name').value = 'Prueba'; document.getElementById('city').value = 'Tulcán'; document.getElementById('delivery').value = 'shipping'; document.getElementById('quote-submit').click()`);
  await until(`!!document.getElementById('quote-message')`);
  await check('Quote includes real code, quantity and personalization', `document.getElementById('quote-message').value.includes('FY.ÑA.012') && document.getElementById('quote-message').value.includes('Nombre de prueba Ñ') && document.getElementById('quote-message').value.includes('3')`);
  await check('Both WhatsApp quote URLs retain Ñ and message', `[...document.querySelectorAll('.button-row a')].length === 2 && [...document.querySelectorAll('.button-row a')].every(a => new URL(a.href).searchParams.get('text').includes('FY.ÑA.012'))`);
  await screenshot('quote-desktop');
  await navigate('/catalogo?categoria=ni%C3%B1as');
  await check('Category filter displays 17 girls', `document.querySelector('.results-count').textContent.includes('17 productos')`);
  await call('Emulation.setDeviceMetricsOverride', {width: 390, height: 844, deviceScaleFactor: 1, mobile: true});
  await screenshot('catalog-mobile');
  await check('Mobile catalog has no horizontal overflow', `document.documentElement.scrollWidth <= innerWidth`);
  await evaluate(`document.querySelector('.menu-toggle').click()`);
  await check('Mobile navigation opens', `document.querySelector('.menu-toggle').getAttribute('aria-expanded') === 'true'`);
  await navigate('/producto/fy-%C3%B1a-012');
  await check('Mobile detail has no horizontal overflow', `document.documentElement.scrollWidth <= innerWidth`);
  await screenshot('detail-mobile');
  await evaluate(`document.getElementById('personalization').value = 'Otra variante'; document.querySelector('#product-form button[type=submit]').click()`);
  await check('Distinct personalization remains a separate cart line', `Yoli.read('cart').length === 2`);
  await navigate('/carrito');
  await until(`document.querySelectorAll('.cart-item').length === 2`);
  await check('Mobile cart has no horizontal overflow', `document.documentElement.scrollWidth <= innerWidth`);
  await screenshot('cart-mobile');
  await evaluate(`document.querySelector('.remove-button').click()`);
  await until(`document.querySelectorAll('.cart-item').length === 1`);
  await evaluate(`document.querySelector('.remove-button').click()`);
  await until(`!document.getElementById('cart-empty').hidden`);
  await check('Removing all lines disables quote', `Yoli.read('cart').length === 0 && document.getElementById('quote-submit').disabled`);
  await navigate('/favoritos');
  await until(`!!document.querySelector('#favorites-list .remove-button')`);
  await evaluate(`document.querySelector('#favorites-list .remove-button').click()`);
  await check('Removing favorite updates empty state', `Yoli.read('favorites').length === 0 && !document.getElementById('favorites-empty').hidden`);
  const expectedNames = JSON.parse(await fs.readFile('data/catalog_names.json', 'utf8'));
  for (const term of ['Gato', 'FY.AN.001']) {
    await navigate('/catalogo?q=' + encodeURIComponent(term));
    await check('Search finds Gato by ' + term, `!![...document.querySelectorAll('.product-card')].find(c => c.querySelector('h3').textContent.trim() === 'Gato' && c.querySelector('.product-code').textContent === 'Código: FY.AN.001')`);
  }
  for (const width of [1440, 390, 320]) {
    await call('Emulation.setDeviceMetricsOverride', {width, height: width === 1440 ? 1000 : 844, deviceScaleFactor: 1, mobile: width < 800});
    const found = new Set();
    for (let page = 1; page <= 15; page++) {
      await navigate('/catalogo?page=' + page);
      await evaluate(`Promise.all([...document.querySelectorAll('.product-card img')].map(i => { i.loading='eager'; return i.decode(); }))`);
      const cards = await evaluate(`[...document.querySelectorAll('.product-card')].map(c => ({code:c.querySelector('[data-add-cart]').dataset.addCart, name:c.querySelector('h3').textContent.trim(), label:c.querySelector('.product-code').textContent, top:c.offsetTop, height:c.getBoundingClientRect().height, bottom:c.querySelector('[data-add-cart]').getBoundingClientRect().bottom, overflow:c.scrollWidth > c.clientWidth, imageFit:getComputedStyle(c.querySelector('img')).objectFit}))`);
      for (const card of cards) {
        assert.equal(card.name, expectedNames[card.code] || card.code);
        assert.equal(card.label, 'Código: ' + card.code);
        assert.equal(card.overflow, false, `Card overflow ${card.code} at ${width}`);
        assert.equal(card.imageFit, 'contain');
        found.add(card.code);
        for (const other of cards.filter(c => c.top === card.top)) {
          assert.ok(Math.abs(card.height-other.height) <= 1, `Unequal card heights at ${width}`);
          assert.ok(Math.abs(card.bottom-other.bottom) <= 1, `Misaligned buttons ${card.code} at ${width}`);
        }
      }
      await check(`Catalog page ${page} at ${width}px: names, codes, alignment, photos and overflow`, `document.documentElement.scrollWidth <= innerWidth`);
      if (page === 4) await screenshot('named-cards-' + width);
    }
    assert.deepEqual([...found].sort(), Object.keys(expectedNames).sort());
    results.push(`All 173 products remain accessible at ${width}px`);
    for (const [route, label] of [['/', 'home'], ['/categorias', 'categories'], ['/producto/fy-re-007', 'long-name-detail']]) {
      await navigate(route);
      await check(`${label} at ${width}px has no overflow`, `document.documentElement.scrollWidth <= innerWidth && [...document.querySelectorAll('h1,h3')].every(e => e.scrollWidth <= e.clientWidth)`);
      if (label === 'home') await check(`Home content visible and populated at ${width}px`, `document.querySelectorAll('.product-card').length === 8 && !document.body.textContent.includes('Estamos preparando nuestro catálogo') && [...document.querySelectorAll('.hero-copy h1,.hero-copy p,.hero-copy .button-row,.hero-caption')].every(e => e.getBoundingClientRect().right <= innerWidth + 1 && e.getBoundingClientRect().left >= 0 && e.scrollWidth <= e.clientWidth)`);
      if (label === 'categories') await check(`All 17 categories at ${width}px`, `document.querySelectorAll('.category-card').length === 17`);
      await screenshot(label + '-' + width);
    }
    await evaluate(`Yoli.write('favorites', ['FY.AN.001','FY.CAR.004','FY.RE.007']); Yoli.write('cart', [{product_code:'FY.CAR.004',quantity:1,requested_size:'',personalization:''},{product_code:'FY.RE.007',quantity:1,requested_size:'',personalization:''}])`);
    await navigate('/favoritos');
    await until(`document.querySelectorAll('#favorites-list .product-card').length === 3`);
    await check(`Named favorites at ${width}px`, `document.querySelector('#favorites-list').textContent.includes('Gato') && document.querySelector('#favorites-list').textContent.includes('Código: FY.AN.001') && document.documentElement.scrollWidth <= innerWidth`);
    await screenshot('named-favorites-' + width);
    await navigate('/carrito');
    await until(`document.querySelectorAll('.cart-item').length === 2`);
    await check(`Long names in cart at ${width}px`, `document.querySelector('#cart-list').textContent.includes('Bienvenida con nombre de profesora') && document.documentElement.scrollWidth <= innerWidth && [...document.querySelectorAll('.cart-item h3')].every(e => e.scrollWidth <= e.clientWidth)`);
    await screenshot('named-cart-' + width);
  }
  await evaluate('localStorage.clear(); Yoli.counters()');
  assert.deepEqual(errors, [], 'No uncaught browser exceptions');
  results.push('No uncaught JavaScript exceptions');
  }
} finally {
  await fs.writeFile(`${outputDir}/${baseline ? 'baseline' : 'browser-results'}.json`, JSON.stringify({checks: results.length, results, errors}, null, 2) + '\n');
  ws.close();
}
console.log(`${results.length} browser checks passed.`);
