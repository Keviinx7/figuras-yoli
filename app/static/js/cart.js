'use strict';
(() => {
  const container = document.getElementById('cart-list');
  if (!container) return;
  const submit = document.getElementById('quote-submit');
  let generation = 0;
  let sending = false;
  let attempt;
  let ownChange = false;
  function save(cart) { ownChange = true; const result = Yoli.write('cart', cart); ownChange = false; return result; }
  function inputField(labelText, name, value, index, product) {
    const field = Yoli.node('div', 'field' + (name === 'quantity' ? ' quantity-field' : ''));
    const label = Yoli.node('label', '', labelText); label.htmlFor = `line-${index}-${name}`;
    const input = Yoli.node(name === 'personalization' ? 'textarea' : 'input');
    input.id = label.htmlFor; input.value = value;
    if (name === 'quantity') { input.type = 'number'; input.min = '1'; input.max = '99'; input.required = true; }
    else input.maxLength = name === 'personalization' ? 500 : 120;
    if (name === 'personalization' && !product?.allows_customization) input.disabled = true;
    input.addEventListener('change', () => {
      const cart = Yoli.read('cart');
      if (!cart[index]) return render();
      if (!input.checkValidity()) { input.reportValidity(); input.value = cart[index][name]; return; }
      const nextValue = name === 'quantity' ? Number(input.value) : input.value;
      cart[index][name] = nextValue;
      if (!save(cart)) render();
    });
    field.append(label, input); return field;
  }
  async function render() {
    const current = ++generation;
    const cart = Yoli.read('cart');
    submit.disabled = true;
    container.replaceChildren();
    document.getElementById('cart-empty').hidden = cart.length > 0;
    document.getElementById('cart-content').hidden = cart.length === 0;
    if (!cart.length) return;
    try {
      const products = await Yoli.lookup(cart.map(line => line.product_code));
      if (current !== generation) return;
      let invalid = false;
      cart.forEach((line, index) => {
        const product = products.find(item => item.code === line.product_code);
        if (!product) invalid = true;
        const item = Yoli.node('article', 'cart-item');
        if (product) item.append(Yoli.productImage(product));
        else item.append(Yoli.node('span', 'unavailable', 'Pendiente'));
        const body = Yoli.node('div');
        const title = Yoli.node('h3');
        if (product) { const link = Yoli.node('a', '', product.name); link.href = product.url; title.append(link); }
        else title.textContent = line.product_code;
        body.append(title, Yoli.node('p', 'product-code', 'Código: ' + line.product_code));
        if (!product) body.append(Yoli.node('p', 'unavailable', 'Este producto no está publicado. Elimínalo para continuar.'));
        if (product && !product.allows_customization && line.personalization) {
          invalid = true;
          body.append(Yoli.node('p', 'unavailable', 'Las opciones de personalización cambiaron. Elimina esta línea y vuelve a agregar el producto.'));
        }
        body.append(inputField('Cantidad', 'quantity', line.quantity, index, product), inputField('Tamaño solicitado (opcional)', 'requested_size', line.requested_size, index, product));
        if (product?.allows_customization || line.personalization) body.append(inputField('Personalización (opcional)', 'personalization', line.personalization, index, product));
        const remove = Yoli.node('button', 'remove-button', 'Eliminar producto'); remove.type = 'button';
        remove.addEventListener('click', () => { const latest = Yoli.read('cart'); latest.splice(index, 1); save(latest); render(); });
        body.append(remove); item.append(body); container.append(item);
      });
      submit.disabled = invalid || sending;
    } catch (error) { if (current === generation) container.append(Yoli.node('p', 'notice', error.message)); }
  }
  document.addEventListener('yoli:change', event => { if (!ownChange && event.detail !== 'favorites') render(); });
  document.getElementById('quote-form').addEventListener('submit', async event => {
    const inputs = [...container.querySelectorAll('input,textarea')];
    const invalid = inputs.find(input => !input.checkValidity());
    if (invalid || submit.disabled) { event.preventDefault(); invalid?.reportValidity(); return; }
    const sent = Yoli.read('cart');
    document.getElementById('cart-payload').value = JSON.stringify(sent);
    const form = event.currentTarget;
    if (!form.dataset.customerRequest) return;
    event.preventDefault();
    if (sending) return;
    sending = true; submit.disabled = true;
    const label = submit.textContent;
    submit.textContent = 'Guardando solicitud…';
    try {
      const data = new FormData(form);
      const payload = JSON.stringify([sent, data.get('delivery'), data.get('notes')]);
      try { attempt ||= JSON.parse(sessionStorage.getItem('yoli.request.v1')); } catch (_) { /* Optional retry storage. */ }
      if (!attempt || attempt.payload !== payload) attempt = {payload, key: crypto.randomUUID()};
      try { sessionStorage.setItem('yoli.request.v1', JSON.stringify(attempt)); } catch (_) { /* In-memory retry remains available. */ }
      data.set('submission_key', attempt.key);
      const response = await fetch(form.action, {method: 'POST', body: data, headers: {Accept: 'application/json'}});
      const result = await response.json();
      if (!response.ok || result.created !== true || !Number.isInteger(result.request_id)
          || result.url !== '/cuenta/pedido/' + result.request_id) {
        throw new Error(result.error || 'No pudimos confirmar tu solicitud. Intenta de nuevo.');
      }
      if (!Yoli.removeSubmitted(sent)) {
        Yoli.notify('Tu solicitud está guardada, pero no pudimos actualizar el carrito. Habilita el almacenamiento y reintenta para sincronizarlo.');
        return;
      }
      try { sessionStorage.removeItem('yoli.request.v1'); } catch (_) { /* Storage may be unavailable. */ }
      attempt = null;
      window.location.assign(result.url);
    } catch (error) {
      Yoli.notify('No pudimos confirmar tu solicitud. Tu carrito se conserva; puedes reintentar.');
    } finally {
      sending = false; submit.textContent = label;
      render();
    }
  });
  render();
})();
