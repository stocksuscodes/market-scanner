# -*- coding: utf-8 -*-
"""Fix patches 2 e H1 que ficaram em SKIP"""
import os

scanner_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Python", "scanner")
app_path  = os.path.join(scanner_dir, "app.py")
html_path = os.path.join(scanner_dir, "static", "index.html")

with open(app_path, 'r', encoding='utf-8') as f: app = f.read()
with open(html_path, 'r', encoding='utf-8') as f: html = f.read()

applied = 0

# PATCH 2: VCP+DryUp+PosSizing calcs em api_lookup
# Procurar o bloco sector rotation penalty
import re

old2 = '''    # Sector rotation penalty
    top5_etfs = [s.get("etf","") for s in (_cache.get("top5_sectors") or [])]
    if etf and top5_etfs and etf not in top5_etfs:
        score_100 = max(0, score_100 - 10)'''

new2 = '''    # Sector rotation penalty
    top5_etfs = [s.get("etf","") for s in (_cache.get("top5_sectors") or [])]
    if etf and top5_etfs and etf not in top5_etfs:
        score_100 = max(0, score_100 - 10)
    # VCP + Volume dry-up
    vcp, vcp_n, vcp_t = detect_vcp(df)
    vol_dryup = detect_volume_dryup(df)
    if vcp: score_100 = min(100, score_100 + 8)
    if vol_dryup: score_100 = min(100, score_100 + 5)
    # Position sizing + expectancy
    pos_shares, pos_exposure = calc_position_size(preco, stop)
    expectancy = calc_expectancy(win_rate=0.45, rr=rr if rr > 0 else 2.0)'''

# Count occurrences to patch the right one (api_lookup, not analisar_ativo)
count = app.count(old2)
print(f"Occurrences of sector rotation block: {count}")

if count >= 1 and "detect_vcp(df)" not in app:
    # Replace last occurrence (api_lookup)
    last_idx = app.rfind(old2)
    app = app[:last_idx] + new2 + app[last_idx+len(old2):]
    print("PATCH 2 OK -- VCP calcs in api_lookup")
    applied += 1
elif "detect_vcp(df)" in app:
    print("PATCH 2 SKIP -- already applied")
else:
    print("PATCH 2 NOT FOUND")

# Add vcp fields to return if missing
old_ret = '''        "rs_rating": 50,
    })'''
new_ret = '''        "rs_rating": 50,
        "vcp": vcp, "vcp_contractions": vcp_n, "vcp_tightness": vcp_t,
        "volume_dryup": vol_dryup,
        "position_shares": pos_shares, "position_exposure": pos_exposure,
        "expectancy": expectancy,
    })'''
if old_ret in app and '"vcp":' not in app:
    app = app.replace(old_ret, new_ret)
    print("PATCH 2b OK -- return fields added")
    applied += 1
else:
    print("PATCH 2b SKIP")

with open(app_path, 'w', encoding='utf-8') as f: f.write(app)

# PATCH H1: VCP+DRY badges na tabela
old_h1 = "${s.score_total!=null?s.score_total+'/15':'—'}</span></span>"
new_h1 = "${s.score_total!=null?s.score_total+'/15':'—'}</span>${s.vcp?'<span style=\"font-size:8px;margin-left:3px;padding:1px 4px;border-radius:3px;background:#1e1b4b;color:#a5b4fc;font-weight:700\">VCP</span>':''}${s.volume_dryup?'<span style=\"font-size:8px;margin-left:2px;padding:1px 4px;border-radius:3px;background:#052e16;color:#4ade80;font-weight:700\">DRY</span>':''}</span>"

if old_h1 in html:
    html = html.replace(old_h1, new_h1)
    print("PATCH H1 OK -- VCP+DRY badges")
    applied += 1
else:
    print("PATCH H1 NOT FOUND -- checking variant")
    # Try finding without the closing span
    idx = html.find("score_total+'/15':'—'}</span>")
    if idx != -1:
        print(f"Found at idx {idx}:", repr(html[idx:idx+50]))

with open(html_path, 'w', encoding='utf-8') as f: f.write(html)

print(f"\nConcluido -- {applied} patches aplicados")
