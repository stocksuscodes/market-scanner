# -*- coding: utf-8 -*-
"""Fix 2: guardar lastRanking nos 3 locais onde lastSignals é atribuído"""
import os

html_path = os.path.join(os.path.expanduser("~"), "Desktop", "Python", "scanner", "static", "index.html")
with open(html_path, 'r', encoding='utf-8') as f: html = f.read()

applied = 0

# Patch all 3 occurrences of lastSignals = signals
old = "    lastSignals = signals;\n\n    clearInterval(progInterval);"
new = "    lastSignals = signals;\n    lastRanking = (typeof data !== 'undefined' && data.ranking_snapshot) ? data.ranking_snapshot : lastRanking;\n\n    clearInterval(progInterval);"
if old in html:
    html = html.replace(old, new)
    print("FIX A OK")
    applied += 1

old2 = "    clearInterval(russellPolling);\n    russellPolling = null;\n    const signals = data.sinais || [];\n    lastSignals = signals;"
new2 = "    clearInterval(russellPolling);\n    russellPolling = null;\n    const signals = data.sinais || [];\n    lastSignals = signals;\n    lastRanking = data.ranking_snapshot || lastRanking;"
if old2 in html:
    html = html.replace(old2, new2)
    print("FIX B OK")
    applied += 1

old3 = "    if (!data.message) {\n      // Results already available\n      const signals = data.sinais || [];\n      lastSignals = signals;"
new3 = "    if (!data.message) {\n      // Results already available\n      const signals = data.sinais || [];\n      lastSignals = signals;\n      lastRanking = data.ranking_snapshot || lastRanking;"
if old3 in html:
    html = html.replace(old3, new3)
    print("FIX C OK")
    applied += 1

with open(html_path, 'w', encoding='utf-8') as f: f.write(html)
print(f"\nConcluido -- {applied} fixes")
