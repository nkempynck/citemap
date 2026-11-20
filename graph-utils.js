// Shared utilities for the citation network pages.
// Loaded as a classic <script> — exposes globals on window.

function debounce(fn, ms) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

function rafThrottle(fn) {
  let scheduled = false;
  return () => {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => { scheduled = false; fn(); });
  };
}

// Escape text for use inside innerHTML or a quoted attribute.
function escapeHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// OpenAlex titles carry inline markup such as <i>Bhlhe41</i> or CO<sub>2</sub>.
// titleHtml escapes everything, restores only those tags written without attributes,
// and lets the parser close any left open so they can't style what follows.
const TITLE_TAGS = /&lt;(\/?)(i|b|em|strong|sub|sup)&gt;/gi;
const titleHtmlCache = new Map();
function titleHtml(t) {
  t = String(t ?? '');
  if (!titleHtmlCache.has(t)) {
    const d = document.createElement('div');
    d.innerHTML = escapeHtml(t).replace(TITLE_TAGS, '<$1$2>');
    titleHtmlCache.set(t, d.innerHTML);
  }
  return titleHtmlCache.get(t);
}

// Title for plain-text places (tooltips, info panel, CSV export): markup removed.
function plainTitle(t) {
  return String(t ?? '').replace(/<\/?(i|b|em|strong|sub|sup)>/gi, '');
}

// Only http(s) links; anything else (e.g. javascript: from a hand-edited JSON) becomes '#'.
function safeHref(u) {
  return /^https?:\/\//i.test(u || '') ? u : '#';
}

// ── Version merging ──────────────────────────────────────────────────────────
// Collapses preprint/published versions of one paper: same DOI, or same first-author
// surname within ±2 years and ≥85% title-word containment. Titles with fewer than three
// words longer than two letters ("Editorial", "Correction") never title-match.
// Used by index.html when fetching and by the viewers when loading, so every view
// shows the same merge, including for JSON saved before this merge existed.
const TYPE_P = { author: 5, mutual: 4, citing: 3, reference: 2 };

class UF {
  find(x) { return this[x] = (this[x] === undefined || this[x] === x) ? x : this.find(this[x]); }
  union(a, b) { this[this.find(a)] = this.find(b); }
}

function normDoi(d) {
  if (!d) return null;
  const s = d.replace(/https?:\/\/doi\.org\//i, '').toLowerCase();
  return s.startsWith('10.48550') ? null : s; // arXiv DOIs are per-version
}

function firstLast(n) {
  const l = n.authors_list?.length ? n.authors_list : [(n.authors || '').replace(' et al.', '')];
  const parts = (l[0] || '').trim().split(/\s+/);
  return parts[parts.length - 1]?.toLowerCase() || null;
}

function sim(a, b) {
  const w = s => new Set(plainTitle(s).toLowerCase().replace(/[^\w\s]/g, '').split(/\s+/).filter(x => x.length > 2));
  const wa = w(a), wb = w(b);
  if (wa.size < 3 || wb.size < 3) return 0;
  const inter = [...wa].filter(x => wb.has(x)).length;
  // Use containment (overlap / shorter set) so subtitle additions don't tank the score
  return inter / Math.min(wa.size, wb.size);
}

// nodeMap: { id: node }. Returns { nodes: { id: node }, edges, collapsed, remap }
// where remap maps every merged-away id to its surviving id.
function mergeVersions(nodeMap, edges) {
  const uf = new UF();
  const arr = Object.values(nodeMap);

  // DOI matching
  const doiIdx = {};
  arr.forEach(n => { const d = normDoi(n.doi); if (!d) return; doiIdx[d] ? uf.union(n.id, doiIdx[d]) : (doiIdx[d] = n.id); });

  // Title + author + year bucket matching
  const bkts = {};
  arr.forEach(n => {
    const ln = firstLast(n); if (!ln || !n.year) return;
    for (let dy = -2; dy <= 2; dy++) {
      const k = `${ln}|${(n.year || 0) + dy}`;
      (bkts[k] = bkts[k] || []).push(n);
    }
  });
  const compared = new Set();
  arr.forEach(n => {
    const ln = firstLast(n); if (!ln || !n.year) return;
    (bkts[`${ln}|${n.year}`] || []).forEach(m => {
      if (m.id === n.id) return;
      const pk = [n.id, m.id].sort().join('~');
      if (compared.has(pk)) return; compared.add(pk);
      if (sim(n.title, m.title) >= 0.85) uf.union(n.id, m.id);
    });
  });

  // Build groups and canonical nodes
  const groups = {};
  arr.forEach(n => { const r = uf.find(n.id); (groups[r] = groups[r] || []).push(n); });
  const remap = {}, merged = {};
  // Track non-canonical nodes that had outgoing reference edges (author/mutual type)
  // so we can drop those edges and keep only the canonical version's references
  const nonCanonRefSources = new Set();
  let collapsed = 0;
  Object.values(groups).forEach(g => {
    if (g.length === 1) { merged[g[0].id] = g[0]; return; }
    collapsed += g.length - 1;
    // Canonical = latest year, tiebreak: most citations
    g.sort((a, b) => (b.year || 0) - (a.year || 0) || (b.cited_by_count || 0) - (a.cited_by_count || 0));
    const c = { ...g[0] };
    c.cited_by_count = g.reduce((s, n) => s + (n.cited_by_count || 0), 0);
    c.type = g.reduce((best, n) => (TYPE_P[n.type] || 0) > (TYPE_P[best] || 0) ? n.type : best, c.type);
    g.forEach(n => { if (n.id !== c.id) remap[n.id] = c.id; });
    // Non-canonical nodes: all except the first (canonical) in sorted order
    g.slice(1).forEach(n => {
      if (n.type === 'author' || n.type === 'mutual') nonCanonRefSources.add(n.id);
    });
    merged[c.id] = c;
  });

  // Remap edges, keeping only the canonical version's outgoing reference edges
  const edgeSeen = new Set(), remapped = [];
  edges.forEach(e => {
    // Drop outgoing edges from non-canonical author/mutual versions (their references)
    if (nonCanonRefSources.has(e.from)) return;
    const f = remap[e.from] || e.from, t = remap[e.to] || e.to;
    if (f === t || !merged[f] || !merged[t]) return;
    const k = `${f}|${t}`; if (!edgeSeen.has(k)) { edgeSeen.add(k); remapped.push({ from: f, to: t }); }
  });

  return { nodes: merged, edges: remapped, collapsed, remap };
}

// Viewer entry point: data.nodes is an array. Returns a new data object plus remap.
function dedupeData(data) {
  const map = {};
  data.nodes.forEach(n => { map[n.id] = n; });
  const { nodes, edges, remap } = mergeVersions(map, data.edges);
  return { data: { ...data, nodes: Object.values(nodes), edges }, remap };
}

// Sky-blue → red heatmap. `scale` controls the asinh curve steepness; smaller = steeper.
function heatmapColor(value, max, scale = 4) {
  const t = max > 0 ? Math.min(1, Math.asinh((value || 0) / scale) / Math.asinh(max / scale)) : 0;
  const r = Math.round(135 + (214 - 135) * t);
  const g = Math.round(206 + (48  - 206) * t);
  const b = Math.round(235 + (30  - 235) * t);
  return {
    bg:     `rgb(${r},${g},${b})`,
    border: `rgb(${Math.round(r * 0.68)},${Math.round(g * 0.68)},${Math.round(b * 0.68)})`,
    font:   `rgb(${Math.round(r * 0.45)},${Math.round(g * 0.45)},${Math.round(b * 0.45)})`,
  };
}

// Loads citation_data.json from localStorage if present, else fetches from disk.
function loadCitationData(onSuccess, onError) {
  let stored = null;
  try { stored = localStorage.getItem('citemap_data'); } catch (_) { /* storage blocked */ }
  if (stored) {
    try { onSuccess(JSON.parse(stored)); return; }
    catch (e) { onError('Failed to load stored data: ' + e); return; }
  }
  fetch('citation_data.json')
    .then(r => { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(onSuccess)
    .catch(e => {
      const msg = e instanceof SyntaxError
        ? 'No data found. Open index.html to fetch a citation network, or deploy citation_data.json alongside this file.'
        : 'Error loading data: ' + (e && e.message ? e.message : e);
      onError(msg);
    });
}

// Reads the six barnesHut physics params from the standard slider IDs.
// Caller is responsible for ensuring those inputs exist in the DOM.
function readPhysicsFromControls() {
  return {
    gravitationalConstant: parseFloat(document.getElementById('gravConst').value),
    centralGravity:        parseFloat(document.getElementById('centralGravity').value),
    springLength:          parseInt(document.getElementById('springLength').value),
    springConstant:        parseFloat(document.getElementById('springConst').value),
    damping:               parseFloat(document.getElementById('damping').value),
    avoidOverlap:          parseFloat(document.getElementById('avoidOverlap').value),
  };
}
