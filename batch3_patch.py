# -*- coding: utf-8 -*-
import os, base64

scanner_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Python", "scanner")

# ── PATCH app.py ──
app_path = os.path.join(scanner_dir, "app.py")
with open(app_path, 'r', encoding='utf-8') as f:
    app = f.read()

applied = 0

# PATCH 1: Sector rotation penalty
old1 = '''    score_100            = calc_score_100(total, rs_score_val, atr_comp, mkt["bullish"],
                                          vol_r, adx, fase, slj, ms_score)'''
new1 = '''    score_100            = calc_score_100(total, rs_score_val, atr_comp, mkt["bullish"],
                                          vol_r, adx, fase, slj, ms_score)
    # Sector rotation penalty
    top5_etfs = [s.get("etf","") for s in (_cache.get("top5_sectors") or [])]
    if etf and top5_etfs and etf not in top5_etfs:
        score_100 = max(0, score_100 - 10)'''

if old1 in app and 'Sector rotation penalty' not in app:
    app = app.replace(old1, new1)
    print("PATCH 1 OK -- sector rotation penalty")
    applied += 1
else:
    print("PATCH 1 SKIP")

# PATCH 2: Fake breakout melhorado
old2 = '''    # Volume insuficiente no breakout
    if vol_now < vol_ma * 1.2:
        return True
    # Extensão excessiva da EMA20 (pump emocional)
    extensao = abs(preco / ema20 - 1) * 100
    if extensao > 20:
        return True
    # Vela de reversão: abriu alto, fechou baixo (bearish engulf no breakout LONG)
    if slj == "LONG" and last["Close"] < last["Open"] and last["Close"] < prev["Close"]:
        return True
    return False'''

new2 = '''    vol_3d  = float(df["Volume"].iloc[-3:].mean())
    prev2   = df.iloc[-3]
    # Volume fraco nos ultimos 3 dias
    if vol_3d < vol_ma * 1.5 and slj == "LONG":
        return True
    # Extensao excessiva da EMA20
    extensao = abs(preco / ema20 - 1) * 100
    if extensao > 25:
        return True
    # Vela de reversao bearish
    if slj == "LONG" and last["Close"] < last["Open"] and last["Close"] < prev["Close"]:
        return True
    # Dois dias consecutivos de fraqueza
    if (last["Close"] < last["Open"] and prev["Close"] < prev["Open"]
            and last["Close"] < prev["Close"]):
        return True
    return False'''

if old2 in app:
    app = app.replace(old2, new2)
    print("PATCH 2 OK -- fake breakout melhorado")
    applied += 1
else:
    print("PATCH 2 SKIP")

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(app)

# ── PATCH index.html ──
html_path = os.path.join(scanner_dir, "static", "index.html")
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

old3 = "${s.atr_compression?'<br><span style=\"font-size:8px;color:#a5b4fc\">⊡ compressão</span>':''}"
new3 = "${s.atr_compression?'<br><span style=\"font-size:8px;color:#a5b4fc\">⊡ compr.</span>':''}${s.fake_breakout?'<br><span style=\"font-size:8px;color:#f87171;font-weight:800\">⚠ fake</span>':''}"

if old3 in html:
    html = html.replace(old3, new3)
    print("PATCH 3 OK -- fake badge HTML")
    applied += 1
else:
    print("PATCH 3 SKIP")

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\nConcluido -- {applied} patches aplicados")
