'use strict';
(() => {
  const keys = {cart: 'yoli.cart.v1', favorites: 'yoli.favorites.v1'};
  const validCode = code => typeof code === 'string' && /^FY\.[A-ZÑ]+\.[0-9]{3}$/.test(code) && !code.endsWith('000');
  let toastTimer;
  function notify(message) {
    const box = document.getElementById('toast');
    box.textContent = message;
    box.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => { box.hidden = true; }, 5000);
  }
  function read(kind) {
    try {
      const value = JSON.parse(localStorage.getItem(keys[kind]) || '[]');
      if (!Array.isArray(value)) return [];
      if (kind === 'favorites') return [...new Set(value.filter(validCode))].slice(0, 100);
      return value.filter(line => line && validCode(line.product_code) && Number.isInteger(line.quantity)
        && line.quantity >= 1 && line.quantity <= 99 && typeof line.requested_size === 'string'
        && line.requested_size.length <= 120 && typeof line.personalization === 'string'
        && line.personalization.length <= 500).slice(0, 50).map(line => ({product_code: line.product_code,
          quantity: line.quantity, requested_size: line.requested_size, personalization: line.personalization}));
    } catch (_) { notify('No se pudo leer la selección guardada en este navegador.'); return []; }
  }
  function write(kind, value) {
    try {
      localStorage.setItem(keys[kind], JSON.stringify(value));
      document.dispatchEvent(new CustomEvent('yoli:change', {detail: kind}));
      return true;
    } catch (_) { notify('El navegador no permite guardar la selección. Revisa sus opciones de almacenamiento.'); return false; }
  }
  function counters() {
    document.querySelectorAll('[data-cart-count]').forEach(el => { el.textContent = read('cart').reduce((total, line) => total + line.quantity, 0); });
    const favorites = read('favorites');
    document.querySelectorAll('[data-favorites-count]').forEach(el => { el.textContent = favorites.length; });
    document.querySelectorAll('[data-favorite]').forEach(el => { el.setAttribute('aria-pressed', String(favorites.includes(el.dataset.favorite))); });
  }
  function addCart(code, quantity = 1, size = '', personalization = '') {
    if (!validCode(code) || !Number.isInteger(quantity) || quantity < 1 || quantity > 99) return notify('Revisa el código y la cantidad.');
    if (typeof size !== 'string' || typeof personalization !== 'string'
      || size.length > 120 || personalization.length > 500) return notify('Revisa el tamaño y la personalización: máximo 120 y 500 caracteres, respectivamente.');
    const cart = read('cart');
    size = size.trim(); personalization = personalization.trim();
    const match = cart.find(line => line.product_code === code && line.requested_size === size && line.personalization === personalization);
    if (match) {
      if (match.quantity + quantity > 99) return notify('El máximo por línea es 99.');
      match.quantity += quantity;
    } else {
      if (cart.length >= 50) return notify('Puedes cotizar hasta 50 líneas por solicitud.');
      cart.push({product_code: code, quantity, requested_size: size, personalization});
    }
    if (write('cart', cart)) notify('Figura agregada al carrito.');
  }
  function node(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }
  async function lookup(codes) {
    const params = new URLSearchParams();
    [...new Set(codes)].forEach(code => params.append('code', code));
    const response = await fetch('/api/productos?' + params.toString(), {headers: {'Accept': 'application/json'}});
    if (!response.ok) throw new Error('No pudimos consultar los productos. Recarga la página para intentar de nuevo.');
    return (await response.json()).products;
  }
  function productImage(product) {
    const img = node('img'); img.src = product.image; img.alt = product.name;
    img.width = 640; img.height = 480; img.loading = 'lazy'; img.dataset.placeholder = '/static/img/placeholder.svg';
    return img;
  }
  window.Yoli = {read, write, counters, addCart, notify, node, lookup, productImage};
  document.addEventListener('yoli:change', counters);
  window.addEventListener('storage', event => {
    const kind = Object.keys(keys).find(key => keys[key] === event.key);
    if (kind || event.key === null) document.dispatchEvent(new CustomEvent('yoli:change', {detail: kind || 'all'}));
  });
  document.querySelector('.menu-toggle').addEventListener('click', event => {
    const expanded = event.currentTarget.getAttribute('aria-expanded') === 'true';
    event.currentTarget.setAttribute('aria-expanded', String(!expanded));
    document.getElementById('navigation').classList.toggle('is-open', !expanded);
  });
  function imageFallback(img) {
    if (img.tagName === 'IMG' && img.dataset.placeholder) {
      const fallback = img.dataset.placeholder; delete img.dataset.placeholder; img.src = fallback;
    }
  }
  document.addEventListener('error', event => imageFallback(event.target), true);
  document.querySelectorAll('img[data-placeholder]').forEach(img => {
    if (img.complete && img.naturalWidth === 0) imageFallback(img);
  });
  document.getElementById('copy-message')?.addEventListener('click', async () => {
    const area = document.getElementById('quote-message');
    try { await navigator.clipboard.writeText(area.value); notify('Mensaje copiado. Pégalo en WhatsApp.'); }
    catch (_) { area.focus(); area.select(); notify('Seleccionamos el mensaje. Usa la opción Copiar de tu navegador.'); }
  });
  counters();
})();
