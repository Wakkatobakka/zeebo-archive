(() => {
  'use strict';
  const normalize = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const input = document.querySelector('#search');
  if (input) {
    const cards = [...document.querySelectorAll('.entry-card')].map(el => ({
      el, text: normalize(el.dataset.search), kind: el.dataset.type,
      subsets: el.dataset.subsets.split(' '), guide: el.dataset.hasGuide === 'yes'
    }));
    const chips = [...document.querySelectorAll('.chip[data-type]')];
    const collection = document.querySelector('#collection');
    const guide = document.querySelector('#guide-only');
    const count = document.querySelector('#results-count');
    const empty = document.querySelector('#no-results');
    let kind = 'All';
    function restore() {
      const params = new URLSearchParams(location.search);
      input.value = params.get('q') || '';
      kind = chips.some(c => c.dataset.type === params.get('type')) ? params.get('type') : 'All';
      collection.value = [...collection.options].some(o => o.value === params.get('set')) ? params.get('set') : 'All';
      guide.checked = params.get('guide') === '1';
    }
    function run(updateUrl = true) {
      const terms = normalize(input.value.trim()).split(/\s+/).filter(Boolean);
      let shown = 0;
      for (const card of cards) {
        const match = (kind === 'All' || card.kind === kind)
          && (collection.value === 'All' || card.subsets.includes(collection.value))
          && (!guide.checked || card.guide)
          && terms.every(term => card.text.includes(term));
        card.el.hidden = !match;
        if (match) shown++;
      }
      count.textContent = `Showing ${shown} of ${cards.length} records`;
      empty.hidden = shown !== 0;
      for (const chip of chips) {
        const active = chip.dataset.type === kind;
        chip.classList.toggle('active', active);
        chip.setAttribute('aria-pressed', String(active));
      }
      if (updateUrl) {
        const params = new URLSearchParams();
        if (input.value.trim()) params.set('q', input.value.trim());
        if (kind !== 'All') params.set('type', kind);
        if (collection.value !== 'All') params.set('set', collection.value);
        if (guide.checked) params.set('guide', '1');
        try { history.replaceState(null, '', location.pathname + (params.size ? '?' + params : '') + location.hash); }
        catch (_) { /* Local file previews keep working without history support. */ }
      }
    }
    input.addEventListener('input', () => run());
    collection.addEventListener('change', () => run());
    guide.addEventListener('change', () => run());
    chips.forEach(chip => chip.addEventListener('click', () => { kind = chip.dataset.type; run(); }));
    document.querySelector('#clear-search').addEventListener('click', () => {
      input.value = ''; kind = 'All'; collection.value = 'All'; guide.checked = false;
      run(); input.focus();
    });
    document.addEventListener('keydown', event => {
      const active = document.activeElement;
      if (event.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON'].includes(active.tagName) && !active.isContentEditable) {
        event.preventDefault(); input.focus();
      }
    });
    window.addEventListener('popstate', () => { restore(); run(false); });
    restore(); run(false);
  }
  for (const button of document.querySelectorAll('button[data-copy]')) {
    button.addEventListener('click', async () => {
      const value = button.dataset.copy || '';
      try {
        if (navigator.clipboard && window.isSecureContext) await navigator.clipboard.writeText(value);
        else {
          const field = document.createElement('textarea');
          field.value = value; field.style.position = 'fixed'; field.style.opacity = '0';
          document.body.appendChild(field); field.select();
          const copied = document.execCommand('copy'); field.remove(); button.focus();
          if (!copied) throw new Error('Clipboard unavailable');
        }
        const label = button.textContent;
        button.textContent = 'Copied!';
        setTimeout(() => { button.textContent = label; }, 1500);
      } catch (_) { button.textContent = 'Select and copy the text above'; }
    });
  }
})();
