content = open('static/index.html', 'r', encoding='utf-8').read()

# 1. Adicionar botao Squeeze junto aos filtros
old_btns = "${etfsPresentes.map(e => `<button class=\"f-btn\" onclick=\"applyFilter('${e}',this)\">${e}</button>`).join('')}"
new_btns = "${etfsPresentes.map(e => `<button class=\"f-btn\" onclick=\"applyFilter('${e}',this)\">${e}</button>`).join('')}<button class=\"f-btn\" style=\"background:#1a0a2e;color:#c084fc;border-color:#7c3aed\" onclick=\"showSqueezeTab()\">⚡ Squeeze</button>"
content = content.replace(old_btns, new_btns)
print('Botao:', 'OK' if 'showSqueezeTab' in content else 'FALHOU')

# 2. Adicionar div do squeeze antes do fecho do body
squeeze_div = """
<!-- SQUEEZE TAB -->
<div id="squeeze-panel" style="display:none;margin-top:16px">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
    <div style="font-size:12px;font-weight:700;letter-spacing:2px;color:#c084fc">⚡ SQUEEZE CANDIDATES</div>
    <div id="squeeze-timestamp" style="font-size:10px;color:#666"></div>
  </div>
  <div id="squeeze-rows"></div>
</div>
"""

squeeze_js = """
<script>
async function showSqueezeTab() {
  // Toggle panel
  const panel = document.getElementById('squeeze-panel');
  const rows  = document.getElementById('rows');
  if (panel.style.display === 'block') {
    panel.style.display = 'none';
    rows.style.display  = 'block';
    return;
  }
  panel.style.display = 'block';
  rows.style.display  = 'none';

  // Carregar dados
  try {
    const r = await fetch('/api/squeeze/candidates');
    const data = await r.json();

    document.getElementById('squeeze-timestamp').textContent = 'Atualizado: ' + (data.timestamp || '--');

    const candidates = data.candidates || [];
    if (!candidates.length) {
      document.getElementById('squeeze-rows').innerHTML = '<div style="color:#666;padding:20px;text-align:center">Sem candidatos. Corre o squeeze_scanner.py primeiro.</div>';
      return;
    }

    const colorMap = {
      '🔴': '#fca5a5', '🟠': '#fb923c', '🟡': '#fbbf24', '⚪': '#94a3b8'
    };

    let html = `<div class="table-wrap"><div class="sig-table">
      <div class="sig-header">
        <span class="th">TICKER</span>
        <span class="th">SQUEEZE</span>
        <span class="th">SI%</span>
        <span class="th">DTC</span>
        <span class="th">BORROW</span>
        <span class="th">AVAILABLE</span>
        <span class="th">NÍVEL</span>
        <span class="th">FLAGS</span>
      </div>`;

    candidates.forEach(c => {
      const score  = c.squeeze_score || 0;
      const nivel  = c.squeeze_nivel || '--';
      const emoji  = nivel.charAt(0);
      const color  = colorMap[emoji] || '#94a3b8';
      const sf     = c.short_float_pct != null ? c.short_float_pct.toFixed(1) + '%' : '--';
      const dtc    = c.days_to_cover   != null ? c.days_to_cover.toFixed(1) + 'd' : '--';
      const borrow = c.borrow_fee      != null ? c.borrow_fee.toFixed(2) + '%' : '--';
      const avail  = c.available       != null ? (c.available/1e6).toFixed(1) + 'M' : '--';
      const flags  = (c.flags || []).join(' · ') || '--';

      html += `<div class="sig-row" style="border-left:2px solid #7c3aed">
        <span class="td"><b style="color:#e2e8f0">${c.ticker}</b></span>
        <span class="td"><span style="font-size:11px;font-weight:700;color:${color}">${score}/100</span></span>
        <span class="td" style="color:${parseFloat(sf)>=25?'#f87171':parseFloat(sf)>=15?'#fbbf24':'#94a3b8'}">${sf}</span>
        <span class="td" style="color:#94a3b8">${dtc}</span>
        <span class="td" style="color:${borrow!='--'&&parseFloat(borrow)>=20?'#f87171':parseFloat(borrow)>=5?'#fbbf24':'#94a3b8'}">${borrow}</span>
        <span class="td" style="color:#94a3b8">${avail}</span>
        <span class="td" style="color:${color};font-size:10px">${nivel}</span>
        <span class="td" style="font-size:9px;color:#666">${flags}</span>
      </div>`;
    });

    html += '</div></div>';
    document.getElementById('squeeze-rows').innerHTML = html;

  } catch(e) {
    document.getElementById('squeeze-rows').innerHTML = '<div style="color:#f87171;padding:20px">Erro ao carregar: ' + e.message + '</div>';
  }
}
</script>
"""

# Inserir antes do </body>
if '</body>' in content:
    content = content.replace('</body>', squeeze_div + squeeze_js + '\n</body>')
    print('Div+JS:', 'OK')
else:
    print('ERRO: </body> nao encontrado')

open('static/index.html', 'w', encoding='utf-8').write(content)
print('FEITO')
