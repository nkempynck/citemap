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
  const stored = localStorage.getItem('citemap_data');
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
