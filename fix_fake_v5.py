# -*- coding: utf-8 -*-
"""Fix fake breakout v5 — passar rs_pct ao scan principal tambem"""
import os

app_path = os.path.join(os.path.expanduser("~"), "Desktop", "Python", "scanner", "app.py")
with open(app_path, 'r', encoding='utf-8') as f: app = f.read()

applied = 0

# Fix 1: analisar_ativo — calcular rs antes do fake check e passar rs_pct
old1 = '    fake_bo = is_fake_breakout(df, slj)'
new1 = '''    _rs_pct_fb, _ = calc_rs_vs_spy(df)
    fake_bo = is_fake_breakout(df, slj, rs_pct=_rs_pct_fb, in_top5=True)'''

count = app.count(old1)
print(f"Occurrences: {count}")
if count >= 1 and "rs_pct_fb" not in app:
    app = app.replace(old1, new1)
    print("PATCH 1 OK -- rs_pct passado ao fake check em analisar_ativo")
    applied += 1
else:
    print("PATCH 1 SKIP")

import ast
ast.parse(app)
print("SYNTAX OK")

with open(app_path, 'w', encoding='utf-8') as f: f.write(app)
print(f"Concluido -- {applied} patches")
