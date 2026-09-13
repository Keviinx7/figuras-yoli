'use strict';
document.addEventListener('click', event => {
  const add = event.target.closest('[data-add-cart]');
  if (add) Yoli.addCart(add.dataset.addCart);
  const gallery = event.target.closest('[data-gallery-src]');
  if (gallery) {
    const main = document.getElementById('main-product-image');
    main.src = gallery.dataset.gallerySrc; main.alt = gallery.dataset.galleryAlt;
    main.dataset.placeholder = '/static/img/placeholder.svg';
  }
});
document.getElementById('product-form')?.addEventListener('submit', event => {
  event.preventDefault();
  const form = event.currentTarget;
  const data = new FormData(form);
  Yoli.addCart(form.dataset.code, Number(data.get('quantity')), data.get('requested_size') || '', data.get('personalization') || '');
});
