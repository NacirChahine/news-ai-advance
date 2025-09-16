(function() {
  function parseDetections() {
    const el = document.getElementById('fallacyDetections');
    if (!el) return [];
    try { return JSON.parse(el.textContent || '[]'); } catch(e) { return []; }
  }
  function buildIndex(container) {
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null);
    const nodes = []; let text = '', node;
    while ((node = walker.nextNode())) {
      const val = node.nodeValue || '';
      nodes.push({ node, start: text.length, len: val.length });
      text += val;
    }
    return { text, nodes };
  }
  function locFromGlobal(index, idx) {
    for (let i = 0; i < idx.nodes.length; i++) {
      const entry = idx.nodes[i];
      if (index < entry.start + entry.len) {
        return { node: entry.node, offset: Math.max(0, index - entry.start) };
      }
    }
    return null;
  }
  function enableSpanInteractions(span, meta) {
    const title = (meta.name || 'Logical fallacy') + (meta.desc ? (' — ' + meta.desc) : '') + ' • Click to learn more';
    span.setAttribute('title', title);
    span.setAttribute('data-bs-toggle', 'tooltip');
    span.setAttribute('role', 'link');
    span.setAttribute('tabindex', '0');
    span.setAttribute('aria-label', (meta.name || 'Logical fallacy') + '. Click to learn more.');
    span.addEventListener('click', function(e){
      const sel = window.getSelection && window.getSelection();
      if (sel && String(sel).length > 0) return; // don't hijack text selection
      if (meta.detail_url) window.location.href = meta.detail_url;
    });
    span.addEventListener('keydown', function(e){
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        if (meta.detail_url) window.location.href = meta.detail_url;
      }
    });
  }
  function wrapByGlobal(container, start, end, meta, idx) {
    if (typeof start !== 'number' || typeof end !== 'number' || end <= start) return false;
    const startLoc = locFromGlobal(start, idx);
    const endLoc = locFromGlobal(end, idx);
    if (!startLoc || !endLoc) return false;
    try {
      const range = document.createRange();
      range.setStart(startLoc.node, startLoc.offset);
      range.setEnd(endLoc.node, endLoc.offset);
      const span = document.createElement('span');
      span.className = 'fallacy-highlight';
      span.id = 'fallacy-detection-' + meta.id;
      enableSpanInteractions(span, meta);
      range.surroundContents(span);
      return true;
    } catch (e) {
      console.warn('Wrap failed, will try fallback search:', e);
      return false;
    }
  }
  function scrollToHighlight(id) {
    const el = document.getElementById('fallacy-detection-' + id);
    if (!el) return;
    el.classList.add('active');
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(() => el.classList.remove('active'), 3500);
  }
  function initHoverAndClick() {
    document.querySelectorAll('.fallacy-excerpt[data-detection-id]').forEach(function(excerpt){
      const id = excerpt.getAttribute('data-detection-id');
      excerpt.addEventListener('mouseenter', function(){
        const hl = document.getElementById('fallacy-detection-' + id);
        if (hl) hl.classList.add('hover');
      });
      excerpt.addEventListener('mouseleave', function(){
        const hl = document.getElementById('fallacy-detection-' + id);
        if (hl) hl.classList.remove('hover');
      });
      excerpt.addEventListener('click', function(e){
        e.preventDefault();
        scrollToHighlight(id);
        if (history && history.replaceState) {
          history.replaceState(null, '', '#fallacy-detection-' + id);
        } else {
          location.hash = 'fallacy-detection-' + id;
        }
      });
    });
    document.querySelectorAll('a[href^="#fallacy-detection-"]').forEach(function(a){
      a.addEventListener('click', function(e){
        const match = this.getAttribute('href').match(/#fallacy-detection-(\d+)/);
        if (!match) return;
        const id = match[1];
        e.preventDefault();
        scrollToHighlight(id);
        if (history && history.replaceState) {
          history.replaceState(null, '', '#fallacy-detection-' + id);
        } else {
          location.hash = 'fallacy-detection-' + id;
        }
      });
    });
  }
  function tryFallbackSearch(meta, idx, container) {
    const excerpt = meta.excerpt || '';
    if (!excerpt) return false;
    // 1) Case-insensitive exact
    let s = idx.text.toLowerCase().indexOf(excerpt.toLowerCase());
    if (s !== -1) return wrapByGlobal(container, s, s + excerpt.length, meta, idx);
    // 2) Fuzzy by tokens allowing punctuation/whitespace
    const tokens = excerpt.match(/[A-Za-z0-9]+/g) || [];
    if (!tokens.length) return false;
    const pat = new RegExp(tokens.map(t => t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('[\\W_]+'),'i');
    const m = pat.exec(idx.text);
    if (m) return wrapByGlobal(container, m.index, m.index + m[0].length, meta, idx);
    return false;
  }
  function applyInitialHash() {
    if (location.hash && location.hash.startsWith('#fallacy-detection-')) {
      const id = location.hash.replace('#fallacy-detection-','');
      setTimeout(function(){ scrollToHighlight(id); }, 50);
    }
  }
  document.addEventListener('DOMContentLoaded', function(){
    const container = document.getElementById('article-content');
    if (!container) return;
    const detections = parseDetections();
    const idx = buildIndex(container);
    detections.sort((a,b)=>{
      const as = (typeof a.start==='number')?a.start:Infinity;
      const bs = (typeof b.start==='number')?b.start:Infinity;
      return as - bs;
    });
    detections.forEach(function(d){
      let ok = false;
      if (typeof d.start === 'number' && typeof d.end === 'number' && d.end > d.start) {
        let useProvided = true;
        const ex = (d.excerpt || '').trim();
        if (ex) {
          const slice = idx.text.slice(d.start, d.end);
          const a = slice.toLowerCase();
          const b = ex.toLowerCase();
          if (!(a.includes(b) || b.includes(a))) {
            useProvided = false;
          }
        }
        if (useProvided) {
          ok = wrapByGlobal(container, d.start, d.end, d, idx);
        }
      }
      if (!ok) {
        ok = tryFallbackSearch(d, idx, container);
      }
      if (!ok) {
        console.warn('Failed to highlight fallacy detection; will show excerpt only:', d);
      }
    });

    // Activate Bootstrap tooltips (including those on highlights)
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (el) { return new bootstrap.Tooltip(el); });

    initHoverAndClick();
    applyInitialHash();
  });
})();

// Key Insights toggle arrow update
document.addEventListener('DOMContentLoaded', function(){
  const btn = document.querySelector('[data-bs-target="#keyInsightsCollapse"]');
  const collapseEl = document.getElementById('keyInsightsCollapse');
  if (!btn || !collapseEl) return;
  const update = () => { btn.textContent = collapseEl.classList.contains('show') ? '▲' : '▼'; };
  update();
  collapseEl.addEventListener('shown.bs.collapse', update);
  collapseEl.addEventListener('hidden.bs.collapse', update);
});

// Make entire Key Insights header clickable (not just the arrow)
document.addEventListener('DOMContentLoaded', function(){
  const toggleBtn = document.querySelector('.card-header [data-bs-target="#keyInsightsCollapse"]');
  if (!toggleBtn) return;
  const header = toggleBtn.closest('.card-header');
  const collapseEl = document.getElementById('keyInsightsCollapse');
  if (!header || !collapseEl) return;
  const bsCollapse = bootstrap.Collapse.getOrCreateInstance(collapseEl, { toggle: false });
  header.addEventListener('click', function(e){
    // Prevent double toggle when clicking the button itself; let button's default work
    if (e.target === toggleBtn || toggleBtn.contains(e.target)) return;
    if (collapseEl.classList.contains('show')) { bsCollapse.hide(); } else { bsCollapse.show(); }
  });
});
