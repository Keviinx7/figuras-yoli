// Storage behavior tests using Node's built-in modules; no npm dependencies.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const listeners = {};
const values = new Map();
const toast = {};
const cartCount = {};
const favoriteCount = {};
let blocked = false;
const document = {
  getElementById: id => id === 'toast' ? toast : null,
  querySelector: () => ({addEventListener() {}}),
  querySelectorAll: selector => selector === '[data-cart-count]' ? [cartCount] : selector === '[data-favorites-count]' ? [favoriteCount] : [],
  addEventListener(name, handler) { (listeners[name] ||= []).push(handler); },
  dispatchEvent(event) { (listeners[event.type] || []).forEach(handler => handler(event)); }
};
const context = {document, window: {addEventListener() {}},
  localStorage: {getItem: key => values.get(key), setItem(key, value) { if (blocked) throw Error('blocked'); values.set(key, value); }},
  setTimeout: () => 0, clearTimeout() {}, console,
  CustomEvent: class { constructor(type, options) { this.type = type; Object.assign(this, options); } }
};
vm.createContext(context);
vm.runInContext(fs.readFileSync('app/static/js/app.js', 'utf8'), context);
const yoli = context.window.Yoli;
let tests = 0;
function test(name, callback) { values.clear(); blocked = false; callback(); tests++; console.log('OK', name); }
test('Stores product.code including Ñ and leading zeros', () => {
  yoli.addCart('FY.ÑA.001');
  const line = JSON.parse(values.get('yoli.cart.v1'))[0];
  assert.equal(line.product_code, 'FY.ÑA.001');
  assert.deepEqual(Object.keys(line).sort(), ['personalization', 'product_code', 'quantity', 'requested_size']);
});
test('Different personalizations remain separate', () => {
  yoli.addCart('FY.ÑA.001', 1, '30 cm', 'Uno'); yoli.addCart('FY.ÑA.001', 2, '30 cm', 'Dos');
  assert.equal(yoli.read('cart').length, 2); assert.equal(cartCount.textContent, 3);
});
test('Different requested sizes remain separate without assigning prices', () => {
  yoli.addCart('FY.ÑA.001', 1, 'Tamaño de prueba A', '');
  yoli.addCart('FY.ÑA.001', 1, 'Tamaño de prueba B', '');
  assert.equal(yoli.read('cart').length, 2);
  assert.deepEqual(Array.from(yoli.read('cart'), line => line.requested_size), ['Tamaño de prueba A', 'Tamaño de prueba B']);
});
test('Stored administrative or client prices cannot become request prices', () => {
  yoli.write('cart', [{product_code:'FY.ÑA.001', quantity:1, requested_size:'', personalization:'',
    price:'7654.32', total:'7654.32', recipe_id:123}]);
  assert.deepEqual(Object.keys(yoli.read('cart')[0]).sort(), ['personalization', 'product_code', 'quantity', 'requested_size']);
});
test('Matching selections merge quantities', () => {
  yoli.addCart('FY.ÑA.001', 1, '30 cm', 'Uno'); yoli.addCart('FY.ÑA.001', 2, '30 cm', 'Uno');
  assert.equal(yoli.read('cart').length, 1); assert.equal(yoli.read('cart')[0].quantity, 3);
});
test('Rejects placeholders and invalid quantities', () => {
  yoli.addCart('FY.AN.000'); yoli.addCart('FY.AN.001', 0); yoli.addCart('FY.AN.001', 1.5);
  assert.equal(yoli.read('cart').length, 0);
});
test('Rejects aggregate quantities over limit', () => {
  yoli.addCart('FY.AN.001', 99); yoli.addCart('FY.AN.001', 1);
  assert.equal(yoli.read('cart')[0].quantity, 99);
});
test('Recovers from malformed localStorage', () => {
  values.set('yoli.cart.v1', '{invalid'); assert.equal(yoli.read('cart').length, 0);
});
test('Favorites preserve distinct Ñ and N codes and remove duplicates', () => {
  yoli.write('favorites', ['FY.ÑA.001', 'FY.NA.001', 'FY.ÑA.001']);
  assert.equal(yoli.read('favorites').length, 2);
});
test('Reports blocked storage without claiming success', () => {
  blocked = true; assert.equal(yoli.write('cart', []), false);
  assert.match(toast.textContent, /no permite guardar/);
});
test('Rejects oversized or non-text customization before saving', () => {
  for (const [size, personalization] of [['x'.repeat(121), ''], ['', 'x'.repeat(501)], [null, ''], ['', 7]]) {
    assert.doesNotThrow(() => yoli.addCart('FY.ÑA.001', 1, size, personalization));
    assert.equal(yoli.read('cart').length, 0);
    assert.equal(values.has('yoli.cart.v1'), false);
  }
});

test('Confirmed submission clears cart, updates counters and preserves favorites', () => {
  yoli.addCart('FY.AN.001', 2, '20 cm', 'Ana');
  yoli.write('favorites', ['FY.AN.001']);
  const sent = yoli.read('cart');
  assert.equal(yoli.removeSubmitted(sent), true);
  assert.equal(yoli.read('cart').length, 0);
  assert.equal(cartCount.textContent, 0);
  assert.equal(favoriteCount.textContent, 1);
  assert.equal(yoli.read('favorites')[0], 'FY.AN.001');
});
test('Only submitted quantities and variants are removed', () => {
  yoli.addCart('FY.AN.001', 2, '20 cm', 'Ana');
  const sent = yoli.read('cart');
  yoli.addCart('FY.AN.001', 3, '20 cm', 'Ana');
  yoli.addCart('FY.AN.001', 1, '30 cm', 'Luis');
  yoli.removeSubmitted(sent);
  assert.equal(cartCount.textContent, 4);
  assert.equal(yoli.read('cart')[0].quantity, 3);
  assert.equal(yoli.read('cart')[1].personalization, 'Luis');
});
console.log(`${tests} JavaScript storage tests passed.`);
