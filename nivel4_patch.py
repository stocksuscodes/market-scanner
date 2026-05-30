# -*- coding: utf-8 -*-
"""Nivel 4: Heatmap sectorial, Watchlist alerts, Export PDF, Print CSS"""
import os

scanner_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Python", "scanner")
app_path  = os.path.join(scanner_dir, "app.py")
html_path = os.path.join(scanner_dir, "static", "index.html")

with open(app_path,  'r', encoding='utf-8') as f: app  = f.read()
with open(html_path, 'r', encoding='utf-8') as f: html = f.read()

applied = 0

# ── APP.PY ──
old_snap = '"ranking_snapshot": [{"nome": s["nome"], "etf": s["etf"], "perf": s["perf"], "rank": s["rank"], "top5": s["top5"]} for s in _cache["ranking"]],'
new_snap = '"ranking_snapshot": [{"nome": s["nome"], "etf": s["etf"], "sector": s.get("sector", s["nome"]), "perf": s["perf"], "rank": s["rank"], "top5": s["top5"], "mom10": s.get("mom10", s["perf"])} for s in _cache["ranking"]],'
if old_snap in app:
    app = app.replace(old_snap, new_snap)
    print("PATCH A1 OK -- ranking_snapshot com mom10")
    applied += 1
else:
    print("PATCH A1 SKIP")

with open(app_path, 'w', encoding='utf-8') as f: f.write(app)

# ── HTML ──

# Heatmap HTML
old_h1 = '    <div class="params-row" style="margin-top:14px">'
heatmap_html = '''    <!-- HEATMAP SECTORIAL -->
    <div id="heatmap-section" style="margin-bottom:12px;display:none;">
      <div style="font-size:10px;font-weight:700;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">◈ Heatmap Sectorial — Momentum 10d <button onclick="document.getElementById('heatmap-section').style.display='none'" style="background:none;border:none;color:#555;cursor:pointer;font-size:10px;">✕</button></div>
      <div id="heatmap-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:5px;"></div>
    </div>
    '''
if 'heatmap-section' not in html and old_h1 in html:
    html = html.replace(old_h1, heatmap_html + old_h1)
    print("PATCH H1 OK -- heatmap HTML")
    applied += 1
else:
    print("PATCH H1 SKIP")

# PDF button
old_csv = '<button onclick="exportCSV()" style="padding:8px 14px;font-size:11px;background:#1a1a1a;color:#888;border:1px solid #333;border-radius:6px;cursor:pointer;">⬇ CSV</button>'
new_csv = '<button onclick="exportCSV()" style="padding:8px 14px;font-size:11px;background:#1a1a1a;color:#888;border:1px solid #333;border-radius:6px;cursor:pointer;">⬇ CSV</button>\n      <button onclick="exportPDF()" style="padding:8px 14px;font-size:11px;background:#1a1a1a;color:#888;border:1px solid #333;border-radius:6px;cursor:pointer;">⬇ PDF</button>'
if old_csv in html and 'exportPDF()' not in html:
    html = html.replace(old_csv, new_csv)
    print("PATCH H2 OK -- PDF button")
    applied += 1
else:
    print("PATCH H2 SKIP")

# Print CSS
print_css = '\n@media print {\n  .run-btn, .btn-primary, .btn-secondary, .detail-btns, .rescan-btn, .footer button { display: none !important; }\n  body { background: white !important; color: black !important; }\n  .sig-row { break-inside: avoid; }\n}\n'
if '@media print' not in html:
    script_idx = html.find('<script>')
    style_idx  = html.rfind('</style>', 0, script_idx)
    if style_idx != -1:
        html = html[:style_idx] + print_css + html[style_idx:]
        print("PATCH H3 OK -- print CSS")
        applied += 1
else:
    print("PATCH H3 SKIP")

# Heatmap + alerts JS
heatmap_js = '''
function renderHeatmap(ranking) {
  const section = document.getElementById('heatmap-section');
  const grid    = document.getElementById('heatmap-grid');
  if (!ranking || !ranking.length || !section) return;
  section.style.display = 'block';
  const max = Math.max(...ranking.map(r => Math.abs(r.mom10||r.perf||0))) || 1;
  grid.innerHTML = ranking.map((r, i) => {
    const pct  = r.mom10 || r.perf || 0;
    const norm = pct / max;
    const green = Math.max(0, Math.round(norm * 160));
    const red   = Math.max(0, Math.round(-norm * 160));
    const bg    = `rgb(${15+red},${15+green},15)`;
    const border = i < 5 ? '1px solid #4ade80' : '1px solid #222';
    const label = r.sector || r.nome || r.etf || '';
    return `<div style="background:${bg};border:${border};border-radius:5px;padding:6px 5px;text-align:center;cursor:pointer;" onclick="filterBySector('${label}')">
      <div style="font-size:9px;font-weight:700;color:#ddd;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${label}">${label}</div>
      <div style="font-size:11px;font-weight:800;color:${pct>=0?'#4ade80':'#f87171'};margin-top:2px">${pct>=0?'+':''}${(pct||0).toFixed(1)}%</div>
      <div style="font-size:8px;color:#666">#${i+1}</div>
    </div>`;
  }).join('');
}
function filterBySector(sector) {
  if (!sector || !lastSignals) return;
  const sigs = lastSignals.filter(s => (s.sector||'').includes(sector) || sector.includes(s.sector||''));
  renderRows(sigs.length ? sigs : lastSignals);
}
function checkWatchlistAlerts(signals) {
  if (!watchlist || !watchlist.length) return;
  const prev = JSON.parse(localStorage.getItem('scanner_prev_signals') || '{}');
  let alerts = [];
  signals.forEach(s => {
    if (watchlist.includes(s.ticker) && prev[s.ticker] && prev[s.ticker] !== s.slj)
      alerts.push(`${s.ticker}: ${prev[s.ticker]} → ${s.slj}`);
    prev[s.ticker] = s.slj;
  });
  localStorage.setItem('scanner_prev_signals', JSON.stringify(prev));
  if (alerts.length) {
    const d = document.createElement('div');
    d.style.cssText = 'position:fixed;top:16px;right:16px;background:#1e3a1e;border:1px solid #4ade80;color:#4ade80;padding:10px 14px;border-radius:8px;font-size:11px;z-index:9999;max-width:260px;white-space:pre';
    d.textContent = '⚡ Mudança de sinal:\n' + alerts.join('\n');
    document.body.appendChild(d);
    setTimeout(() => d.remove(), 6000);
  }
}
function exportPDF() { window.print(); }
'''

if 'renderHeatmap' not in html:
    html = html.replace('</script>', heatmap_js + '\n</script>', 1)
    print("PATCH H4 OK -- heatmap+alerts+PDF JS")
    applied += 1
else:
    print("PATCH H4 SKIP")

# Call renderHeatmap after scan
old_render = "  renderRows(signals);\n  openDetail = null;"
new_render = "  renderRows(signals);\n  openDetail = null;\n  if (data.ranking_snapshot) renderHeatmap(data.ranking_snapshot);\n  checkWatchlistAlerts(signals);"
if old_render in html and 'renderHeatmap(data' not in html:
    html = html.replace(old_render, new_render, 1)
    print("PATCH H5 OK -- call heatmap after scan")
    applied += 1
else:
    print("PATCH H5 SKIP")

with open(html_path, 'w', encoding='utf-8') as f: f.write(html)

print(f"\nConcluido -- {applied} patches aplicados")
