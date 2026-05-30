# -*- coding: utf-8 -*-
"""Adiciona coluna DIAS_REST ao app.py e index.html"""
import os

scanner_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Python", "scanner")
app_path  = os.path.join(scanner_dir, "app.py")
html_path = os.path.join(scanner_dir, "static", "index.html")

with open(app_path,  'r', encoding='utf-8') as f: app  = f.read()
with open(html_path, 'r', encoding='utf-8') as f: html = f.read()

applied = 0

# ── APP.PY ──

# PATCH 1: Adicionar funcao calcular_dias_restantes antes de compute_indicators
new_func = '''
# ─────────────────────────────────────────────
#  DIAS RESTANTES NA FASE (WYCKOFF)
# ─────────────────────────────────────────────
DURACOES_MEDIAS = {
    "Acumulacao": 35, "Acumulação": 35,
    "Spring":     12,
    "Markup":     45,
    "Test":       10,
    "Distribuicao": 25, "Distribuição": 25,
    "Markdown":   20,
    "UTAD":        8,
}

def calcular_dias_restantes(fase, sinal, rsi, adx, preco, ma200):
    """
    Estima dias restantes na fase actual.
    Maturidade = RSI(40%) + ADX(30%) + DistMA200(30%)
    Dias restantes = duracao_media * (1 - maturidade)
    """
    try:
        dur = DURACOES_MEDIAS.get(fase, 20)

        # RSI maturidade: LONG sobrecomprado = mais maduro
        if sinal == "LONG":
            rsi_mat = max(0, min(1, (rsi - 50) / 30))
        elif sinal == "SHORT":
            rsi_mat = max(0, min(1, (50 - rsi) / 30))
        else:
            rsi_mat = max(0, min(1, abs(rsi - 50) / 30))

        # ADX maturidade: ADX alto = tendencia forte mas pode estar a acabar
        adx_mat = max(0, min(1, (adx - 20) / 40))

        # Distancia MA200 maturidade
        if ma200 and ma200 > 0:
            dist_pct = abs((preco / ma200 - 1) * 100)
            dist_mat = max(0, min(1, dist_pct / 40))
        else:
            dist_mat = 0.0

        maturidade = rsi_mat * 0.4 + adx_mat * 0.3 + dist_mat * 0.3
        dias = max(1, round(dur * (1 - maturidade)))
        return f"~{dias}d"
    except:
        return "N/A"

'''

marker = "def compute_indicators(df):"
if "calcular_dias_restantes" not in app and marker in app:
    app = app.replace(marker, new_func + "\n" + marker)
    print("PATCH 1 OK -- calcular_dias_restantes")
    applied += 1
else:
    print("PATCH 1 SKIP")

# PATCH 2: Chamar dias_rest em api_lookup e adicionar ao return
old_lookup_ret = '''        "rs_score": rs_score_val, "rs_pct": rs_pct,'''
new_lookup_ret = '''        "dias_rest": calcular_dias_restantes(fase, slj, rsi, adx, preco, sma200),
        "rs_score": rs_score_val, "rs_pct": rs_pct,'''

if old_lookup_ret in app and '"dias_rest"' not in app:
    app = app.replace(old_lookup_ret, new_lookup_ret)
    print("PATCH 2 OK -- dias_rest no return do lookup")
    applied += 1
else:
    print("PATCH 2 SKIP")

# PATCH 3: Adicionar ao return do analisar_ativo
old_ativ_ret = '''        "signal_label": "FORTE" if total >= 12 else "MÉDIO" if total >= 7 else "FRACO",'''
new_ativ_ret = '''        "signal_label": "FORTE" if total >= 12 else "MÉDIO" if total >= 7 else "FRACO",
        "dias_rest": calcular_dias_restantes(fase, slj, rsi, adx, preco, sma200),'''

if old_ativ_ret in app and '"dias_rest"' not in app:
    app = app.replace(old_ativ_ret, new_ativ_ret)
    print("PATCH 3 OK -- dias_rest em analisar_ativo")
    applied += 1
elif '"dias_rest"' in app:
    print("PATCH 2/3 já aplicados")
else:
    print("PATCH 3 SKIP")

with open(app_path, 'w', encoding='utf-8') as f: f.write(app)

# ── HTML ──
# PATCH 4: Adicionar coluna DIAS ao header
old_header = '<span class="th">S100</span><span class="th">RS/SPY</span>'
new_header = '<span class="th">S100</span><span class="th">RS/SPY</span><span class="th">Dias</span>'

if old_header in html and '<span class="th">Dias</span>' not in html:
    html = html.replace(old_header, new_header)
    print("PATCH 4 OK -- coluna Dias no header")
    applied += 1
else:
    print("PATCH 4 SKIP")

# PATCH 5: Adicionar célula DIAS na linha de dados
old_rs_cell = "      <span class=\"td\" style=\"font-size:10px;font-weight:600;color:${s.rs_pct>=0?'#4ade80':'#f87171'}\">${s.rs_pct!=null?(s.rs_pct>=0?'+':'')+s.rs_pct+'%':'—'}${s.atr_compression?'<br><span style=\"font-size:8px;color:#a5b4fc\">⊡ compr.</span>':''}${s.fake_breakout?'<br><span style=\"font-size:8px;color:#f87171;font-weight:800\">⚠ fake</span>':''}</span>"
new_rs_cell = old_rs_cell + "\n      <span class=\"td\" style=\"font-size:10px;color:${s.dias_rest&&s.dias_rest!='N/A'?(parseInt(s.dias_rest)<=10?'#f87171':parseInt(s.dias_rest)<=25?'#f59e0b':'#4ade80'):'#666'}\">${s.dias_rest||'—'}</span>"

if old_rs_cell in html and '"dias_rest"' not in html:
    html = html.replace(old_rs_cell, new_rs_cell)
    print("PATCH 5 OK -- célula Dias na tabela")
    applied += 1
else:
    print("PATCH 5 SKIP")

with open(html_path, 'w', encoding='utf-8') as f: f.write(html)

print(f"\nConcluido -- {applied} patches aplicados")
