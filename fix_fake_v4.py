# -*- coding: utf-8 -*-
"""Fix fake breakout v4 — excepção para líderes RS>40% em top 5"""
import os

app_path = os.path.join(os.path.expanduser("~"), "Desktop", "Python", "scanner", "app.py")
with open(app_path, 'r', encoding='utf-8') as f: app = f.read()

old = '''def is_fake_breakout(df, slj):
    """
    Detecta breakouts falsos:
    - Breakout sem volume confirmado (vol < 1.5x média nos últimos 3 dias)
    - Preço demasiado longe da EMA20 (>25% extensão)
    - Vela de reversão bearish no topo
    - Gap sem seguimento (fechou abaixo da abertura 2 dias seguidos)
    Retorna fake=True se for breakout falso.
    """
    if len(df) < 22:
        return False
    last    = df.iloc[-1]
    prev    = df.iloc[-2]
    vol_ma  = float(df["Volume"].rolling(20).mean().iloc[-1])
    vol_now = float(last["Volume"])
    ema20   = float(compute_ema(df["Close"], 20).iloc[-1])
    preco   = float(last["Close"])'''

new = '''def is_fake_breakout(df, slj, rs_pct=0, in_top5=True):
    """
    Detecta breakouts falsos.
    Excepção: líderes com RS > 40% em sectores top 5 nunca são fake.
    """
    if len(df) < 22:
        return False
    # Excepção para líderes fortes em sectores top 5
    if rs_pct > 40 and in_top5:
        return False
    last    = df.iloc[-1]
    prev    = df.iloc[-2]
    vol_ma  = float(df["Volume"].rolling(20).mean().iloc[-1])
    vol_now = float(last["Volume"])
    ema20   = float(compute_ema(df["Close"], 20).iloc[-1])
    preco   = float(last["Close"])'''

if old in app:
    app = app.replace(old, new)
    print("PATCH 1 OK -- is_fake_breakout com excepção RS")
else:
    print("PATCH 1 NOT FOUND")

# Pass rs_pct and in_top5 to is_fake_breakout in api_lookup
old2 = '    fake_bo              = is_fake_breakout(df, slj)'
new2 = '''    _top5_etfs = [s.get("etf","") for s in (_cache.get("top5_sectors") or [])]
    _in_top5   = etf in _top5_etfs if _top5_etfs else True
    fake_bo    = is_fake_breakout(df, slj, rs_pct=rs_pct, in_top5=_in_top5)'''

if old2 in app:
    app = app.replace(old2, new2)
    print("PATCH 2 OK -- passar rs_pct e in_top5")
else:
    print("PATCH 2 NOT FOUND")

# Also fix in analisar_ativo if present
old3 = '    fake_bo = is_fake_breakout(df, slj)'
new3 = '    fake_bo = is_fake_breakout(df, slj)'  # keep same in analisar_ativo
# No change needed in analisar_ativo as rs_pct not available there

import ast
ast.parse(app)
print("SYNTAX OK")

with open(app_path, 'w', encoding='utf-8') as f: f.write(app)
