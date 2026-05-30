# -*- coding: utf-8 -*-
"""Fix: data not defined em renderResults — guardar ranking_snapshot globalmente"""
import os

html_path = os.path.join(os.path.expanduser("~"), "Desktop", "Python", "scanner", "static", "index.html")
with open(html_path, 'r', encoding='utf-8') as f: html = f.read()

applied = 0

# Fix 1: adicionar variável global lastRanking
old_globals = "let lastSignals = [];"
new_globals = "let lastSignals = [];\nlet lastRanking = [];"
if "lastRanking" not in html and old_globals in html:
    html = html.replace(old_globals, new_globals)
    print("FIX 1 OK -- lastRanking global")
    applied += 1
else:
    print("FIX 1 SKIP")

# Fix 2: guardar ranking_snapshot quando chega do servidor
# Procurar onde lastSignals é atribuído após o scan
old_lastsig = "lastSignals = data.sinais || [];"
new_lastsig = "lastSignals = data.sinais || [];\n    lastRanking = data.ranking_snapshot || [];"
if old_lastsig in html and "lastRanking = data.ranking" not in html:
    html = html.replace(old_lastsig, new_lastsig)
    print("FIX 2 OK -- guardar lastRanking")
    applied += 1
else:
    print("FIX 2 SKIP")

# Fix 3: usar lastRanking em vez de data.ranking_snapshot
old_render = "if (data.ranking_snapshot) renderHeatmap(data.ranking_snapshot);"
new_render = "if (lastRanking && lastRanking.length) renderHeatmap(lastRanking);"
if old_render in html:
    html = html.replace(old_render, new_render)
    print("FIX 3 OK -- renderHeatmap usa lastRanking")
    applied += 1
else:
    print("FIX 3 SKIP")

with open(html_path, 'w', encoding='utf-8') as f: f.write(html)
print(f"\nConcluido -- {applied} fixes aplicados")
