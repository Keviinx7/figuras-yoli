'use strict';
(() => {
  const container = document.getElementById('favorites-list');
  let generation = 0;
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-favorite]');
    if (!button) return;
    const code = button.dataset.favorite;
    const favorites = Yoli.read('favorites');
    if (!favorites.includes(code) && favorites.length >= 100) return Yoli.notify('Puedes guardar hasta 100 favoritos.');
    Yoli.write('favorites', favorites.includes(code) ? favorites.filter(item => item !== code) : [...favorites, code]);
  });
  async function render() {
    if (!container) return;
    const current = ++generation;
    const codes = Yoli.read('favorites');
    container.replaceChildren();
    document.getElementById('favorites-empty').hidden = codes.length !== 0;
    if (!codes.length) return;
    try {
      const products = await Yoli.lookup(codes);
      if (current !== generation) return;
      codes.forEach(code => {
        const product = products.find(item => item.code === code);
        const card = Yoli.node('article', 'product-card');
        if (product) {
          const visual = Yoli.node('a', 'product-visual'); visual.href = product.url; visual.append(Yoli.productImage(product)); card.append(visual);
        }
        const info = Yoli.node('div', 'product-info');
        const title = Yoli.node('h3');
        if (product) { const link = Yoli.node('a', '', product.name); link.href = product.url; title.append(link); }
        else title.textContent = code;
        info.append(title, Yoli.node('p', 'product-code', 'Código: ' + code), Yoli.node('p', 'price-note', product ? 'Precio por confirmar' : 'Producto no publicado actualmente.'));
        if (product) {
          const add = Yoli.node('button', 'button button-outline full-width', 'Agregar al carrito +');
          add.type = 'button'; add.dataset.addCart = code; info.append(add);
        }
        const remove = Yoli.node('button', 'remove-button', 'Eliminar de favoritos');
        remove.type = 'button'; remove.dataset.favorite = code; remove.setAttribute('aria-pressed', 'true');
        info.append(remove); card.append(info); container.append(card);
      });
      Yoli.counters();
    } catch (error) { if (current === generation) container.append(Yoli.node('p', 'notice', error.message)); }
  }
  document.addEventListener('yoli:change', event => { if (event.detail !== 'cart') render(); });
  render();
})();
