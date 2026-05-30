# -*- coding: utf-8 -*-
import os, re

path = os.path.join(os.path.expanduser("~"), "Desktop", "Python", "scanner", "app.py")
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# PATCH 1: imports json e pathlib
old1 = 'from flask import Flask, jsonify, request'
new1 = '''from flask import Flask, jsonify, request
import json
from pathlib import Path

HISTORY_FILE = Path(__file__).parent / "scan_history.json"

def save_scan_history(sinais, timestamp):
    try:
        history = []
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        entry = {
            "date": timestamp.strftime("%Y-%m-%d"),
            "time": timestamp.strftime("%H:%M"),
            "total_long": sum(1 for s in sinais if s.get("slj") == "LONG"),
            "total_short": sum(1 for s in sinais if s.get("slj") == "SHORT"),
            "total_aguardar": sum(1 for s in sinais if s.get("slj") == "AGUARDAR"),
            "top_long": [{"ticker": s["ticker"], "score_100": s.get("score_100",0), "rs_pct": s.get("rs_pct",0)} for s in sinais if s.get("slj") == "LONG"][:10],
            "top_short": [{"ticker": s["ticker"], "score_100": s.get("score_100",0)} for s in sinais if s.get("slj") == "SHORT"][:5],
        }
        history = [h for h in history if h["date"] != entry["date"]]
        history.append(entry)
        history = sorted(history, key=lambda x: x["date"], reverse=True)[:30]
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"  [HISTORY] Guardado: {entry['date']}", flush=True)
    except Exception as e:
        print(f"  [HISTORY] Erro: {e}", flush=True)

def load_scan_history():
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return []'''

# PATCH 2: scan auto 9h30
old2 = '''def _schedule_cache_refresh():
    """Refreshes cache every 2 hours."""
    _run_full_scan_background()
    timer = threading.Timer(7200, _schedule_cache_refresh)
    timer.daemon = True
    timer.start()'''

new2 = '''def _schedule_cache_refresh():
    """Refreshes cache every 2 hours or at 9h30 EST (14h30 UTC)."""
    from datetime import timedelta
    _run_full_scan_background()
    now_utc = datetime.utcnow()
    target = now_utc.replace(hour=14, minute=30, second=0, microsecond=0)
    if now_utc >= target:
        target += timedelta(days=1)
    delay = min(7200, (target - now_utc).total_seconds())
    timer = threading.Timer(delay, _schedule_cache_refresh)
    timer.daemon = True
    timer.start()'''

# PATCH 3: chamar save_scan_history apos scan
old3 = '        print(f"  [CACHE] Scan completo: {len(sinais)} sinais de {len(all_tickers)} tickers (Top 5 sectores)", flush=True)'
new3 = '        print(f"  [CACHE] Scan completo: {len(sinais)} sinais de {len(all_tickers)} tickers (Top 5 sectores)", flush=True)\n        save_scan_history(sinais, _cache["timestamp"])'

applied = 0
for old, new, label in [(old1,new1,"imports+history"), (old2,new2,"scan auto 9h30"), (old3,new3,"save history")]:
    if old in content and new not in content:
        content = content.replace(old, new)
        print(f"OK -- {label}")
        applied += 1
    elif new in content:
        print(f"JA EXISTE -- {label}")
    else:
        print(f"NAO ENCONTRADO -- {label}")

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Concluido -- {applied} patches aplicados")
