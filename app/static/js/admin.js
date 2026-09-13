'use strict';
(() => {
  // UI only. Amounts and totals are validated and calculated by Flask/Decimal.
  function addRow(templateId, targetId) {
    const template = document.getElementById(templateId), target = document.getElementById(targetId);
    if (!template || !target || target.children.length >= 50) return null;
    const row = template.content.firstElementChild.cloneNode(true);
    target.append(row);
    return row;
  }
  document.addEventListener('click', event => {
    const add = event.target.closest('[data-add-row]');
    if (add) addRow(add.dataset.addRow, add.dataset.target)?.querySelector('input,select')?.focus();
    event.target.closest('[data-remove-row]')?.closest('.repeat-row')?.remove();
    if (event.target.closest('[data-print]')) window.print();
    if (event.target.closest('[data-back]')) history.back();
    const toggle = event.target.closest('.nav-toggle');
    if (toggle) {
      const expanded = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(expanded));
      document.getElementById('admin-nav')?.classList.toggle('open', expanded);
    }
  });
  document.querySelector('[data-copy]')?.addEventListener('click', async event => {
    const area = document.getElementById(event.currentTarget.dataset.copy);
    const status = document.getElementById('copy-status');
    try { await navigator.clipboard.writeText(area.value); status.textContent = 'Texto copiado.'; }
    catch (_) { area.focus(); area.select(); status.textContent = 'Texto seleccionado. Use la opción Copiar del navegador.'; }
  });
  document.getElementById('material-picker')?.addEventListener('change', event => {
    const option = event.target.selectedOptions[0];
    if (!option.value) return;
    const row = addRow('material-template', 'material-rows');
    if (row) {
      row.querySelector('[name=material_name]').value = option.dataset.name;
      row.querySelector('[name=material_unit]').value = option.dataset.unit;
      row.querySelector('[name=material_cost]').value = option.dataset.cost;
      row.querySelector('[name=material_quantity]').focus();
    }
    event.target.value = '';
  });
  const method = document.getElementById('profit-method');
  function explain() {
    document.getElementById('profit-formula').textContent = method.value === 'margin'
      ? 'Margen sobre venta: precio = costo ÷ (1 − porcentaje / 100). El porcentaje debe ser menor al 100%.'
      : 'Recargo sobre costo: precio = costo × (1 + porcentaje / 100).';
  }
  if (method) { method.addEventListener('change', explain); explain(); }
})();
