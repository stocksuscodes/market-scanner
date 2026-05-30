# -*- coding: utf-8 -*-
"""Corrige threshold do fake breakout — estava demasiado agressivo"""
import os

app_path = os.path.join(os.path.expanduser("~"), "Desktop", "Python", "scanner", "app.py")
with open(app_path, 'r', encoding='utf-8') as f: app = f.read()

# Problema: vol_3d < vol_ma * 1.5 apanha tickers normais
# Correcção: só marcar fake se vol_3d < vol_ma * 0.8 (volume claramente fraco)
# E remover a condição de 2 dias consecutivos que é demasiado genérica

old = '''    vol_3d  = float(df["Volume"].iloc[-3:].mean())
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

new = '''    vol_3d  = float(df["Volume"].iloc[-3:].mean())
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

if old in app:
    app = app.replace(old, new)
    print("OK -- fake breakout threshold corrigido")
else:
    print("NOT FOUND")

with open(app_path, 'w', encoding='utf-8') as f: f.write(app)
