# -*- coding: utf-8 -*-
"""Fix fake breakout v3 — só activa em breakouts recentes, não em tendências estabelecidas"""
import os

app_path = os.path.join(os.path.expanduser("~"), "Desktop", "Python", "scanner", "app.py")
with open(app_path, 'r', encoding='utf-8') as f: app = f.read()

old = '''    vol_3d  = float(df["Volume"].iloc[-3:].mean())
    # Volume claramente fraco no breakout (< 80% da media) — fake
    if vol_3d < vol_ma * 0.8 and slj == "LONG":
        return True
    # Extensao excessiva da EMA20 (pump emocional)
    extensao = abs(preco / ema20 - 1) * 100
    if extensao > 30:
        return True
    # Vela de reversao bearish forte no topo (corpo > 60% do range)
    corpo = abs(last["Close"] - last["Open"])
    rng   = last["High"] - last["Low"]
    if (slj == "LONG" and last["Close"] < last["Open"]
            and corpo > rng * 0.6 and last["Close"] < prev["Close"]):
        return True
    return False'''

new = '''    vol_3d  = float(df["Volume"].iloc[-3:].mean())

    # Só avaliar fake em breakouts recentes (subida > 15% nos últimos 10 dias)
    preco_10d = float(df["Close"].iloc[-10])
    subida_10d = (preco / preco_10d - 1) * 100 if preco_10d > 0 else 0

    # Tendência estabelecida (subida < 15% recente) — não é fake, é continuação
    if slj == "LONG" and subida_10d < 15:
        return False

    # Volume claramente fraco num breakout recente (< 80% da media)
    if vol_3d < vol_ma * 0.8 and slj == "LONG" and subida_10d >= 15:
        return True
    # Extensao excessiva da EMA20 num breakout recente (pump emocional)
    extensao = abs(preco / ema20 - 1) * 100
    if extensao > 35 and subida_10d >= 20:
        return True
    # Vela de reversao bearish forte no topo de breakout recente
    corpo = abs(last["Close"] - last["Open"])
    rng   = last["High"] - last["Low"]
    if (slj == "LONG" and last["Close"] < last["Open"]
            and corpo > rng * 0.7 and last["Close"] < prev["Close"]
            and subida_10d >= 15):
        return True
    return False'''

if old in app:
    app = app.replace(old, new)
    print("OK -- fake breakout v3 aplicado")
else:
    print("NOT FOUND")

with open(app_path, 'w', encoding='utf-8') as f: f.write(app)
