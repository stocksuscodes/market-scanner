# -*- coding: utf-8 -*-
"""Fix erro JS linha 1534 — nested backtick em renderWatchlist"""
import os

html_path = os.path.join(os.path.expanduser("~"), "Desktop", "Python", "scanner", "static", "index.html")
with open(html_path, 'r', encoding='utf-8') as f: html = f.read()

old = """    const badge = sig ? `<span style=\"font-size:9px;padding:1px 5px;border-radius:3px;margin-left:6px;background:${sig.slj==='LONG'?'#052e16':sig.slj==='SHORT'?'#7f1d1d':'#1c1917'};color:${sig.slj==='LONG'?'#4ade80':sig.slj==='SHORT'?'#f87171':'#888'}">${sig.slj}</span>` : '';"""

new = """    const badgeBg = sig.slj==='LONG'?'#052e16':sig.slj==='SHORT'?'#7f1d1d':'#1c1917';
    const badgeClr = sig.slj==='LONG'?'#4ade80':sig.slj==='SHORT'?'#f87171':'#888';
    const badge = sig ? '<span style="font-size:9px;padding:1px 5px;border-radius:3px;margin-left:6px;background:'+badgeBg+';color:'+badgeClr+'">'+sig.slj+'</span>' : '';"""

if old in html:
    html = html.replace(old, new)
    print("OK -- JS syntax fix aplicado")
else:
    print("NOT FOUND -- ja aplicado ou diferente")

with open(html_path, 'w', encoding='utf-8') as f: f.write(html)
