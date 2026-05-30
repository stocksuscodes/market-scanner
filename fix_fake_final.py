# -*- coding: utf-8 -*-
"""Fix definitivo fake breakout — assinatura correcta + excepção RS>40%"""
import os

app_path = os.path.join(os.path.expanduser("~"), "Desktop", "Python", "scanner", "app.py")
with open(app_path, 'r', encoding='utf-8') as f: app = f.read()

applied = 0

# PATCH 1: Substituir a funcao is_fake_breakout completa
old_func = '''def is_fake_breakout(df, slj):
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
    prev2   = df.iloc[-3]
    vol_ma  = float(df["Volume"].rolling(20).mean().iloc[-1])
    vol_3d  = float(df["Volume"].iloc[-3:].mean())
    ema20   = float(compute_ema(df["Close"], 20).iloc[-1])
    preco   = float(last["Close"])

    # Volume fraco nos últimos 3 dias (não confirma movimento)
    if vol_3d < vol_ma * 1.5 and slj == "LONG":
        return True
    # Extensão excessiva da EMA20
    extensao = abs(preco / ema20 - 1) * 100
    if extensao > 25:
        return True
    # Vela de reversão bearish no topo (LONG)
    if slj == "LONG" and last["Close"] < last["Open"] and last["Close"] < prev["Close"]:
        return True
    # Dois dias consecutivos a fechar abaixo da abertura (fraqueza)
    if (last["Close"] < last["Open"] and prev["Close"] < prev["Open"]
            and last["Close"] < prev["Close"]):
        return True
    return False'''

new_func = '''def is_fake_breakout(df, slj, rs_pct=0, in_top5=True):
    """
    Detecta breakouts falsos.
    Excepção: líderes com RS > 40% em sectores top 5 nunca são fake.
    Só avalia breakouts recentes (subida > 15% nos últimos 10 dias).
    """
    if len(df) < 22:
        return False
    # Excepção para líderes fortes em sectores top 5
    if rs_pct > 40 and in_top5:
        return False
    last    = df.iloc[-1]
    prev    = df.iloc[-2]
    vol_ma  = float(df["Volume"].rolling(20).mean().iloc[-1])
    vol_3d  = float(df["Volume"].iloc[-3:].mean())
    ema20   = float(compute_ema(df["Close"], 20).iloc[-1])
    preco   = float(last["Close"])

    # Só avaliar fake em breakouts recentes (subida > 15% nos últimos 10 dias)
    preco_10d = float(df["Close"].iloc[-10]) if len(df) >= 10 else preco
    subida_10d = (preco / preco_10d - 1) * 100 if preco_10d > 0 else 0
    if slj == "LONG" and subida_10d < 15:
        return False

    # Volume claramente fraco num breakout recente
    if vol_3d < vol_ma * 0.8 and slj == "LONG":
        return True
    # Extensão excessiva da EMA20
    extensao = abs(preco / ema20 - 1) * 100
    if extensao > 35:
        return True
    # Vela de reversão bearish forte no topo
    corpo = abs(last["Close"] - last["Open"])
    rng   = last["High"] - last["Low"]
    if (slj == "LONG" and last["Close"] < last["Open"]
            and corpo > rng * 0.7 and last["Close"] < prev["Close"]
            and subida_10d >= 15):
        return True
    return False'''

if old_func in app:
    app = app.replace(old_func, new_func)
    print("PATCH 1 OK -- is_fake_breakout substituida")
    applied += 1
else:
    print("PATCH 1 NOT FOUND")

# PATCH 2: passar rs_pct em analisar_ativo
old2 = '    fake_bo = is_fake_breakout(df, slj)'
new2 = '    _rs_fb, _ = calc_rs_vs_spy(df)\n    fake_bo = is_fake_breakout(df, slj, rs_pct=_rs_fb, in_top5=True)'
if old2 in app and '_rs_fb' not in app:
    app = app.replace(old2, new2)
    print("PATCH 2 OK -- rs_pct em analisar_ativo")
    applied += 1
else:
    print("PATCH 2 SKIP")

# PATCH 3: passar rs_pct em api_lookup (ja tem _rs_pct_fb ou similar)
old3 = '    fake_bo              = is_fake_breakout(df, slj)'
new3 = '''    _top5_etfs_fb = [s.get("etf","") for s in (_cache.get("top5_sectors") or [])]
    _in_top5_fb   = etf in _top5_etfs_fb if _top5_etfs_fb else True
    fake_bo       = is_fake_breakout(df, slj, rs_pct=rs_score_val, in_top5=_in_top5_fb)'''
if old3 in app:
    app = app.replace(old3, new3)
    print("PATCH 3 OK -- rs_pct em api_lookup")
    applied += 1
else:
    print("PATCH 3 SKIP")

import ast
ast.parse(app)
print("SYNTAX OK")

with open(app_path, 'w', encoding='utf-8') as f: f.write(app)
print(f"Concluido -- {applied} patches")
