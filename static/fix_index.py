# -*- coding: utf-8 -*-
content = """<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Wyckoff · SLJ Scanner</title>
<style>
  :root {
    --bg: #ffffff;
    --bg2: #f7f7f7;
    --bg3: #eeeeee;
    --border: #e0e0e0;
    --border2: #cccccc;
    --text: #111111;
    --text2: #444444;
    --text3: #888888;
    --green: #16a34a;
    --green-bg: #dcfce7;
    --green-border: #86efac;
    --red: #dc2626;
    --red-bg: #fee2e2;
    --amber: #f59e0b;
    --teal: #2dd4bf;
    --font: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: var(--font); font-size: 13px; min-height: 100vh; }

  /* ── LAYOUT ── */
  .app { max-width: 1200px; margin: 0 auto; padding: 1.5rem 1rem; }

  /* ── HEADER ── */
  .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 10px; }
  .header-left h1 { font-size: 18px; font-weight: 700; letter-spacing: .08em; color: var(--text); }
  .header-left p  { font-size: 10px; color: var(--text3); letter-spacing: .1em; text-transform: uppercase; margin-top: 3px; }
  .live-badge { font-size: 10px; padding: 4px 10px; border-radius: 4px; background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); display: flex; align-items: center; gap: 6px; }
  .live-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--green); animation: pulse 1.4s infinite; }
  @keyframes pulse { 0%,100%{opacity:1}50%{opacity:.2} }

  /* ── CONFIG PANEL ── */
  .config-panel { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 16px; margin-bottom: 1.5rem; }
  .config-title { font-size: 9px; color: var(--text3); text-transform: uppercase; letter-spacing: .1em; margin-bottom: 12px; }
  .sectors-grid { display: flex; flex-direction: column; gap: 8px; margin-bottom: 14px; }
  .sector-line { display: flex; align-items: flex-start; gap: 10px; padding-bottom: 8px; border-bottom: 1px solid var(--border); }
  .sector-line:last-child { border-bottom: none; padding-bottom: 0; }
  .sec-meta { min-width: 100px; }
  .sec-etf  { font-size: 12px; font-weight: 700; color: var(--text); }
  .sec-nome { font-size: 9px; color: var(--text3); margin-top: 2px; }
  .sec-toggle { font-size: 9px; color: var(--text3); cursor: pointer; background: transparent; border: 1px solid var(--border); border-radius: 10px; padding: 2px 7px; font-family: var(--font); margin-top: 5px; display: inline-block; }
  .sec-toggle:hover { color: var(--text2); border-color: var(--border2); }
  .pills { display: flex; flex-wrap: wrap; gap: 5px; flex: 1; }
  .pill { font-size: 10px; padding: 3px 9px; border-radius: 20px; border: 1px solid var(--border2); color: var(--text3); cursor: pointer; transition: all .12s; user-select: none; }
  .pill.on { background: var(--green-bg); color: var(--green); border-color: var(--green-border); }
  .pill:hover { border-color: #555; color: var(--text2); }

  .params-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 12px; }
  .param-group label { font-size: 9px; color: var(--text3); text-transform: uppercase; letter-spacing: .07em; display: block; margin-bottom: 4px; }
  .param-group input { width: 100%; background: var(--bg3); border: 1px solid var(--border2); border-radius: 6px; color: var(--text); font-family: var(--font); font-size: 12px; padding: 6px 10px; }
  .param-group input:focus { outline: none; border-color: #444; }

  .sel-info { font-size: 10px; color: var(--text3); margin-bottom: 10px; }
  .sel-info span { color: var(--text); }

  .run-btn { width: 100%; padding: 10px; background: var(--bg3); border: 1px solid var(--border2); border-radius: 8px; color: var(--text); font-family: var(--font); font-size: 12px; cursor: pointer; letter-spacing: .05em; transition: all .15s; display: flex; align-items: center; justify-content: center; gap: 8px; }
  .run-btn:hover { background: #222; border-color: #444; }
  .run-btn:disabled { opacity: .4; cursor: not-allowed; }

  /* ── METRICS ── */
  .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-bottom: 1.5rem; }
  .metric { background: var(--bg2); border: 1px solid var(--border); border-radius: 8px; padding: 12px 14px; }
  .metric-lbl { font-size: 9px; color: var(--text3); text-transform: uppercase; letter-spacing: .07em; margin-bottom: 6px; }
  .metric-val { font-size: 22px; font-weight: 700; color: var(--text); }
  .metric-sub { font-size: 9px; color: var(--text3); margin-top: 3px; }
  .metric-val.green { color: var(--green); }
  .metric-val.red   { color: var(--red); }

  /* ── SECTOR RANK ── */
  .rank-section { margin-bottom: 1.5rem; display: none; }
  .section-label { font-size: 9px; color: var(--text3); text-transform: uppercase; letter-spacing: .1em; margin-bottom: 8px; }
  .rank-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; }
  .rank-card { background: var(--bg2); border: 1px solid var(--border); border-radius: 8px; padding: 10px 12px; }
  .rank-card.top { border-color: var(--green-border); }
  .rank-etf  { font-size: 10px; color: var(--text3); margin-bottom: 4px; }
  .rank-perf { font-size: 13px; font-weight: 700; }
  .rank-nome { font-size: 9px; color: var(--text3); margin-top: 2px; }

  /* ── FILTERS ── */
  .filter-bar { display: flex; gap: 6px; margin-bottom: 10px; flex-wrap: wrap; }
  .f-btn { font-size: 10px; padding: 4px 12px; border-radius: 20px; border: 1px solid var(--border2); background: transparent; color: var(--text3); cursor: pointer; font-family: var(--font); transition: all .12s; }
  .f-btn:hover, .f-btn.active { background: var(--bg3); color: var(--text); border-color: #555; }

  /* ── TABLE ── */
  .table-wrap { overflow-x: auto; }
  .tbl-head { display: grid; grid-template-columns: 56px 90px 62px 44px 44px 100px 72px 46px 140px 75px; gap: 0; padding: 7px 12px; background: var(--bg3); border-radius: 6px; margin-bottom: 4px; min-width: 700px; }
  .th { font-size: 9px; color: var(--text3); text-transform: uppercase; letter-spacing: .07em; }
  .sig-row { display: grid; grid-template-columns: 56px 90px 62px 44px 44px 100px 72px 46px 140px 75px; gap: 0; padding: 9px 12px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg2); margin-bottom: 3px; align-items: center; cursor: pointer; transition: all .12s; min-width: 700px; }
  .sig-row:hover { background: var(--bg3); }
  .sig-row.long  { border-left: 2px solid var(--green); border-radius: 0 6px 6px 0; }
  .sig-row.watch { border-left: 2px solid var(--amber); border-radius: 0 6px 6px 0; }
  .sig-row.short { border-left: 2px solid var(--red);   border-radius: 0 6px 6px 0; }
  .td { font-size: 11px; color: var(--text); }
  .td-ticker { font-size: 14px; font-weight: 700; }
  .td-sec    { font-size: 10px; color: var(--text3); }
  .td-sa     { font-size: 10px; line-height: 1.6; }
  .green { color: var(--green); } .red { color: var(--red); } .amber { color: var(--amber); } .muted { color: var(--text3); }

  .pbadge { font-size: 9px; padding: 2px 6px; border-radius: 3px; font-weight: 700; white-space: nowrap; }
  .p-acc { background: #dcfce7; color: #15803d; }
  .p-spr { background: #d9f99d; color: #3f6212; }
  .p-mup { background: #ccfbf1; color: #0f766e; }
  .p-dis { background: #fee2e2; color: #b91c1c; }
  .p-tst { background: #fef9c3; color: #854d0e; }
  .sbadge { font-size: 9px; padding: 2px 7px; border-radius: 3px; font-weight: 700; }
  .s-long  { background: #dcfce7; color: #15803d; }
  .s-short { background: #fee2e2; color: #b91c1c; }
  .s-wait  { background: #f3f4f6; color: #6b7280; }

  /* ── DETAIL PANEL ── */
  .detail { display: none; padding: 12px 14px; margin-bottom: 4px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg3); }
  .detail.open { display: block; }
  .detail-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 10px; }
  .d-lbl { font-size: 9px; color: var(--text3); text-transform: uppercase; margin-bottom: 3px; }
  .d-val { font-size: 13px; font-weight: 700; color: var(--text); }
  .bar-wrap { height: 3px; background: var(--border); border-radius: 2px; margin: 6px 0 12px; }
  .bar-fill { height: 100%; border-radius: 2px; transition: width .4s; }
  .ai-box { font-size: 11px; color: var(--text2); line-height: 1.7; padding: 10px 12px; border-left: 2px solid #333; margin-bottom: 10px; white-space: pre-wrap; background: var(--bg2); border-radius: 0 6px 6px 0; }
  .detail-btns { display: flex; gap: 8px; flex-wrap: wrap; }
  .d-btn { font-size: 10px; padding: 5px 12px; border-radius: 6px; border: 1px solid var(--border2); background: transparent; color: var(--text3); cursor: pointer; font-family: var(--font); transition: all .12s; }
  .d-btn:hover { background: var(--bg2); color: var(--text); }

  /* ── STATES ── */
  .loading-state, .empty-state { text-align: center; padding: 3rem; color: var(--text3); }
  .spinner { width: 20px; height: 20px; border: 2px solid var(--border2); border-top-color: var(--text3); border-radius: 50%; animation: spin .7s linear infinite; display: inline-block; margin-bottom: 10px; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .progress-bar { height: 2px; background: var(--border); border-radius: 1px; margin: 10px auto; max-width: 200px; overflow: hidden; }
  .progress-fill { height: 100%; background: var(--green); border-radius: 1px; transition: width .3s; }

  /* ── FOOTER ── */
  .footer { display: flex; justify-content: space-between; align-items: center; margin-top: 1.5rem; padding-top: 12px; border-top: 1px solid var(--border); flex-wrap: wrap; gap: 8px; }
  .footer-note { font-size: 9px; color: var(--text3); }
  .rescan-btn { font-size: 10px; padding: 5px 14px; border-radius: 6px; border: 1px solid var(--border2); background: transparent; color: var(--text3); cursor: pointer; font-family: var(--font); display: flex; align-items: center; gap: 6px; transition: all .12s; }
  .rescan-btn:hover { background: var(--bg3); color: var(--text); }

  @media (max-width: 600px) {
    .metrics { grid-template-columns: repeat(2,1fr); }
    .rank-grid { grid-template-columns: repeat(2,1fr); }
    .params-row { grid-template-columns: repeat(2,1fr); }
  }
</style>
</head>
<body>
<div class="app">

  <!-- HEADER -->
  <div class="header">
    <div class="header-left">
      <h1>WYCKOFF · SLJ SCANNER</h1>
      <p>Alpaca Markets · Dados Reais · Sector Rotation</p>
    </div>
    <div class="live-badge"><span class="live-dot"></span>ALPACA LIVE</div>
  </div>

  <!-- CONFIG -->
  <div class="config-panel">
    <div class="config-title">Sectores e tickers</div>
    <div class="sectors-grid" id="sectors-grid"></div>
    <div class="params-row" style="margin-top:14px">
      <div class="param-group"><label>Preço mín $</label><input type="number" id="p-min" value="5" min="1"></div>
      <div class="param-group"><label>Preço máx $</label><input type="number" id="p-max" value="50" min="1"></div>
      <div class="param-group"><label>ADX mín</label><input type="number" id="adx-min" value="20" min="1"></div>
      <div class="param-group"><label>RSI máx</label><input type="number" id="rsi-max" value="55" min="1"></div>
    </div>
    <div class="sel-info" id="sel-info"></div>
    <button class="run-btn" id="run-btn" onclick="runScan()">
      ▶ Executar scan com dados Alpaca
    </button>
  </div>

  <!-- METRICS -->
  <div class="metrics">
    <div class="metric"><div class="metric-lbl">Analisados</div><div class="metric-val" id="m-total">—</div><div class="metric-sub">tickers</div></div>
    <div class="metric"><div class="metric-lbl">Sinais LONG</div><div class="metric-val green" id="m-long">—</div><div class="metric-sub">compra</div></div>
    <div class="metric"><div class="metric-lbl">Melhor R/R</div><div class="metric-val" id="m-rr">—</div><div class="metric-sub">risco/recomp.</div></div>
    <div class="metric"><div class="metric-lbl">VTI / Mercado</div><div class="metric-val" id="m-market">—</div><div class="metric-sub" id="m-market-sub">—</div></div>
  </div>

  <!-- RANK -->
  <div class="rank-section" id="rank-section">
    <div class="section-label">Ranking sectorial — momentum 10 dias</div>
    <div class="rank-grid" id="rank-grid"></div>
  </div>

  <!-- RESULTS -->
  <div id="results">
    <div class="empty-state">Configura os parâmetros e clica em "Executar scan"</div>
  </div>

  <!-- FOOTER -->
  <div class="footer">
    <span class="footer-note">SMA200 · EMA21 pullback · ADX>min · RSI 30–max · Wyckoff · SLJ · Alpaca IEX feed</span>
    <button class="rescan-btn" onclick="runScan()">↻ Novo scan</button>
  </div>

</div>

<script>
const SECTORES = [];
let selected = {};
let lastSignals = [];
let openDetail = null;

const PHASE_CLASS = {
  Acumulação:'p-acc', Spring:'p-spr', Markup:'p-mup', Distribuição:'p-dis', Test:'p-tst'
};

// ── Carregar sectores do backend ──
async function loadSectores() {
  try {
    const r = await fetch('/api/sectores');
    const data = await r.json();
    data.sectores.forEach(s => {
      SECTORES.push(s);
      selected[s.etf] = new Set(s.tickers);
    });
    buildSectorsUI();
    updateSelInfo();
    loadMercado();
  } catch(e) {
    console.error('Erro ao carregar sectores:', e);
  }
}

function buildSectorsUI() {
  const grid = document.getElementById('sectors-grid');
  grid.innerHTML = SECTORES.map(s => `
    <div class="sector-line">
      <div class="sec-meta">
        <div class="sec-etf">${s.etf}</div>
        <div class="sec-nome">${s.nome}</div>
        <button class="sec-toggle" onclick="toggleSector('${s.etf}')" id="stb-${s.etf}">tudo</button>
      </div>
      <div class="pills" id="pills-${s.etf}">
        ${s.tickers.map(t => `<span class="pill on" id="pill-${t}" onclick="toggleTicker('${s.etf}','${t}')">${t}</span>`).join('')}
      </div>
    </div>`).join('');
}

function toggleTicker(etf, t) {
  if (selected[etf].has(t)) selected[etf].delete(t);
  else selected[etf].add(t);
  const el = document.getElementById('pill-' + t);
  if (el) el.classList.toggle('on', selected[etf].has(t));
  updateSelInfo();
}

function toggleSector(etf) {
  const sec = SECTORES.find(s => s.etf === etf);
  const allOn = sec.tickers.every(t => selected[etf].has(t));
  if (allOn) selected[etf].clear();
  else sec.tickers.forEach(t => selected[etf].add(t));
  sec.tickers.forEach(t => {
    const el = document.getElementById('pill-' + t);
    if (el) el.classList.toggle('on', selected[etf].has(t));
  });
  const btn = document.getElementById('stb-' + etf);
  if (btn) btn.textContent = allOn ? 'tudo' : 'nenhum';
  updateSelInfo();
}

function updateSelInfo() {
  let total = 0;
  SECTORES.forEach(s => { total += selected[s.etf] ? selected[s.etf].size : 0; });
  const secs = SECTORES.filter(s => selected[s.etf] && selected[s.etf].size > 0).length;
  document.getElementById('sel-info').innerHTML =
    `<span>${total}</span> tickers seleccionados em <span>${secs}</span> sectores`;
}

async function loadMercado() {
  try {
    const r = await fetch('/api/mercado');
    const d = await r.json();
    const el = document.getElementById('m-market');
    const sub = document.getElementById('m-market-sub');
    el.textContent = d.estado || '—';
    el.className = 'metric-val ' + (d.ok ? 'green' : 'red');
    sub.textContent = d.preco ? `VTI $${d.preco} / SMA21 $${d.sma21}` : '—';
  } catch(e) {}
}

async function loadRanking() {
  try {
    const r = await fetch('/api/ranking');
    const d = await r.json();
    const section = document.getElementById('rank-section');
    section.style.display = 'block';
    document.getElementById('rank-grid').innerHTML = d.ranking.slice(0,5).map((s,i) => `
      <div class="rank-card top">
        <div class="rank-etf">#${i+1} ${s.etf}</div>
        <div class="rank-perf ${s.perf >= 0 ? 'green' : 'red'}">${s.perf >= 0 ? '+' : ''}${s.perf}%</div>
        <div class="rank-nome">${s.nome}</div>
      </div>`).join('');
  } catch(e) {}
}

async function runScan() {
  const btn = document.getElementById('run-btn');
  btn.disabled = true;
  btn.textContent = '⟳ A scanear dados Alpaca...';

  const pMin   = parseFloat(document.getElementById('p-min').value)   || 5;
  const pMax   = parseFloat(document.getElementById('p-max').value)   || 50;
  const adxMin = parseFloat(document.getElementById('adx-min').value) || 20;
  const rsiMax = parseFloat(document.getElementById('rsi-max').value) || 55;

  const tickers = [];
  SECTORES.forEach(s => {
    selected[s.etf].forEach(t => tickers.push({ ticker: t, etf: s.etf, sector: s.nome }));
  });

  document.getElementById('results').innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <div>A obter dados do Alpaca... (${tickers.length} tickers)</div>
      <div class="progress-bar"><div class="progress-fill" id="prog" style="width:5%"></div></div>
      <div style="font-size:10px;color:#444;margin-top:8px">Pode demorar 1-2 minutos</div>
    </div>`;

  // Simular progresso visual
  let prog = 5;
  const progInterval = setInterval(() => {
    prog = Math.min(prog + 2, 90);
    const el = document.getElementById('prog');
    if (el) el.style.width = prog + '%';
  }, 800);

  try {
    // Ranking em paralelo
    loadRanking();

    const r = await fetch('/api/scan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tickers, p_min: pMin, p_max: pMax, adx_min: adxMin, rsi_max: rsiMax })
    });
    const data = await r.json();
    const signals = data.sinais || [];
    lastSignals = signals;

    clearInterval(progInterval);

    document.getElementById('m-total').textContent = data.total;
    document.getElementById('m-long').textContent  = signals.filter(s => s.slj === 'LONG').length;
    document.getElementById('m-rr').textContent    = signals.length ? signals[0].rr + 'x' : '—';

    renderResults(signals);
  } catch(e) {
    clearInterval(progInterval);
    document.getElementById('results').innerHTML =
      `<div class="empty-state">Erro: ${e.message}<br><small style="color:#555">Verifica se o Flask está a correr e as API keys estão configuradas.</small></div>`;
  }

  btn.disabled = false;
  btn.textContent = '▶ Executar scan com dados Alpaca';
}

function renderResults(signals) {
  if (!signals.length) {
    document.getElementById('results').innerHTML =
      '<div class="empty-state">Nenhum sinal com os critérios actuais. Tenta ajustar os parâmetros.</div>';
    return;
  }

  const etfsPresentes = [...new Set(signals.map(s => s.etf))];
  const filterBtns = `
    <div class="filter-bar">
      <button class="f-btn active" onclick="applyFilter('all',this)">Todos (${signals.length})</button>
      <button class="f-btn" onclick="applyFilter('long',this)">LONG (${signals.filter(s=>s.slj==='LONG').length})</button>
      <button class="f-btn" onclick="applyFilter('watch',this)">Vigiar (${signals.filter(s=>s.slj==='AGUARDAR').length})</button>
      ${etfsPresentes.map(e => `<button class="f-btn" onclick="applyFilter('${e}',this)">${e}</button>`).join('')}
    </div>`;

  document.getElementById('results').innerHTML = filterBtns + `
    <div class="table-wrap">
      <div class="tbl-head">
        <span class="th">Ticker</span><span class="th">Sector</span>
        <span class="th">Preço</span><span class="th">RSI</span><span class="th">ADX</span>
        <span class="th">Fase Wyckoff</span><span class="th">Sinal SLJ</span>
        <span class="th">R/R</span><span class="th">Stop / Alvo</span><span class="th">Score SLJ</span>
      </div>
      <div id="rows"></div>
    </div>`;

  renderRows(signals);
  openDetail = null;
}

function renderRows(sigs) {
  document.getElementById('rows').innerHTML = sigs.map(s => {
    const i = lastSignals.indexOf(s);
    const cls = s.slj === 'LONG' ? 'long' : s.slj === 'SHORT' ? 'short' : 'watch';
    const pc  = PHASE_CLASS[s.fase] || 'p-tst';
    const sc  = s.slj === 'LONG' ? 's-long' : s.slj === 'SHORT' ? 's-short' : 's-wait';
    return `
    <div class="sig-row ${cls}" onclick="toggleDetail(${i})">
      <span class="td td-ticker">${s.ticker}</span>
      <span class="td td-sec">${s.sector}</span>
      <span class="td">$${s.price.toFixed(2)}</span>
      <span class="td ${s.rsi < 42 ? 'green' : s.rsi > 55 ? 'red' : 'muted'}">${s.rsi}</span>
      <span class="td">${s.adx}</span>
      <span class="td"><span class="pbadge ${pc}">${s.fase}</span></span>
      <span class="td"><span class="sbadge ${sc}">${s.slj}</span></span>
      <span class="td ${s.rr >= 2 ? 'green' : 'muted'}">${s.rr}:1</span>
      <span class="td td-sa"><span class="red">▼ $${s.stop.toFixed(2)}</span><br><span class="green">▲ $${s.alvo.toFixed(2)}</span></span>
      <span class="td"><span style="font-size:9px;padding:2px 6px;border-radius:3px;font-weight:700;background:${(s.score_total||0)>=12?'#fee2e2':(s.score_total||0)>=7?'#fef9c3':'#f3f4f6'};color:${(s.score_total||0)>=12?'#b91c1c':(s.score_total||0)>=7?'#854d0e':'#6b7280'};">${s.score_total!=null?s.score_total+'/15':'—'}</span></span>
    </div>
    <div class="detail" id="det-${i}">
      <div class="detail-grid">
        <div><div class="d-lbl">SMA 200</div><div class="d-val">$${s.sma200}</div></div>
        <div><div class="d-lbl">EMA 21</div><div class="d-val">$${s.ema21}</div></div>
        <div><div class="d-lbl">ATR</div><div class="d-val">$${s.atr}</div></div>
        <div><div class="d-lbl">Risco $</div><div class="d-val red">$${(s.price - s.stop).toFixed(2)}</div></div>
      </div>
      <div style="margin:6px 0 8px;"><div style="font-size:9px;color:#888;text-transform:uppercase;margin-bottom:4px;">Score SLJ — ${s.score_total!=null?s.score_total+'/15':'—'}</div><div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:4px;"><span style="font-size:9px;padding:2px 7px;border-radius:3px;background:#e0f2fe;color:#0369a1;font-weight:600;">S ${s.score_simons!=null?s.score_simons+'/3':'—'}</span><span style="font-size:9px;padding:2px 7px;border-radius:3px;background:#dcfce7;color:#15803d;font-weight:600;">L ${s.score_livermore!=null?s.score_livermore+'/3':'—'}</span><span style="font-size:9px;padding:2px 7px;border-radius:3px;background:#f3e8ff;color:#7e22ce;font-weight:600;">P ${s.score_ptj!=null?s.score_ptj+'/3':'—'}</span><span style="font-size:9px;padding:2px 7px;border-radius:3px;background:#fef9c3;color:#854d0e;font-weight:600;">W ${s.score_wyckoff!=null?s.score_wyckoff+'/3':'—'}</span><span style="font-size:9px;padding:2px 7px;border-radius:3px;background:#fee2e2;color:#b91c1c;font-weight:600;">M ${s.score_markov!=null?s.score_markov+'/3':'—'}</span></div>${((s.notes_simons||[]).concat(s.notes_livermore||[]).concat(s.notes_ptj||[]).concat(s.notes_wyckoff||[]).concat(s.notes_markov||[])).slice(0,5).map(n=>`<div style="font-size:10px;color:#666;margin-top:2px;">• ${n}</div>`).join('')}</div>
      <div class="detail-grid" style="display:none">
        <div><div class="d-lbl">Vol Ratio</div><div class="d-val ${s.vol_ratio > 1.5 ? 'green' : ''}">${s.vol_ratio}x</div></div>
      </div>
      <div class="bar-wrap">
        <div class="bar-fill" style="width:${Math.min(100, s.adx * 2.3).toFixed(0)}%;background:${s.slj==='LONG'?'#22c55e':s.slj==='SHORT'?'#ef4444':'#f59e0b'}"></div>
      </div>
      <div class="ai-box" id="ai-${i}" style="font-style:italic;color:#444">Clica em "Analisar com IA" para análise Wyckoff/SLJ detalhada.</div>
      <div class="detail-btns">
        <button class="d-btn" onclick="event.stopPropagation();analyzeAI(${i})">⬡ Analisar com IA</button>
        <button class="d-btn" onclick="event.stopPropagation();openTradingView('${s.ticker}')">↗ TradingView</button>
      </div>
    </div>`;
  }).join('');
}

function applyFilter(type, btn) {
  document.querySelectorAll('.f-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  let filtered = lastSignals;
  if (type === 'long')  filtered = lastSignals.filter(s => s.slj === 'LONG');
  else if (type === 'watch') filtered = lastSignals.filter(s => s.slj === 'AGUARDAR');
  else if (type !== 'all')   filtered = lastSignals.filter(s => s.etf === type);
  renderRows(filtered);
  openDetail = null;
}

function toggleDetail(i) {
  if (openDetail !== null && openDetail !== i) {
    const prev = document.getElementById('det-' + openDetail);
    if (prev) prev.classList.remove('open');
  }
  const det = document.getElementById('det-' + i);
  if (det) {
    det.classList.toggle('open');
    openDetail = det.classList.contains('open') ? i : null;
  }
}

async function analyzeAI(i) {
  const s = lastSignals[i];
  const box = document.getElementById('ai-' + i);
  box.style.fontStyle = 'italic'; box.style.color = '#555';
  box.textContent = 'A consultar IA...';
  try {
    const prompt = `És um analista técnico especializado em Wyckoff e SLJ. Analisa este ativo de forma concisa (3-4 linhas em português europeu):\nTicker: ${s.ticker} | Sector: ${s.sector}\nPreço real: $${s.price} | SMA200: $${s.sma200} | EMA21: $${s.ema21}\nRSI: ${s.rsi} | ADX: ${s.adx} | ATR: $${s.atr} | Vol Ratio: ${s.vol_ratio}x\nFase Wyckoff: ${s.fase} | Sinal SLJ: ${s.slj}\nStop: $${s.stop} | Alvo: $${s.alvo} | R/R: ${s.rr}:1\nFoca na validade do sinal SLJ, contexto da fase Wyckoff e o que vigiar.`;
    const r = await fetch('/api/ai-analysis', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    });
    const d = await r.json();
    box.style.fontStyle = 'normal'; box.style.color = '#888';
    box.textContent = d.analysis || 'Sem resposta.';
  } catch(e) {
    box.textContent = 'Erro: ' + e.message;
  }
}

function openTradingView(ticker) {
  window.open(`https://www.tradingview.com/chart/?symbol=${ticker}`, '_blank');
}

loadSectores();
</script>
</body>
</html>
"""
dst = r'C:\Users\Nuno Gueifão\Desktop\Python\scanner\static\index.html'
with open(dst, 'w', encoding='utf-8') as f:
    f.write(content)
print('OK! Tamanho:', len(content))
