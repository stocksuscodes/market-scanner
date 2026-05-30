# -*- coding: utf-8 -*-
"""
Limpa a pasta do scanner — move ficheiros fix_*.py e outros patches para _patches/
"""
import os, shutil
from pathlib import Path

scanner_dir = Path(__file__).parent

patches_dir = scanner_dir / "_patches"
patches_dir.mkdir(exist_ok=True)

# Padrões a mover
patterns = [
    "fix_*.py", "upgrade_*.py", "batch*.py", "instalar_*.py",
    "install*.py", "rm_*.py", "nova_paleta.py", "novos_setores.py",
    "probabilidade.py", "rotacao.py", "russell*.py", "markov.py",
    "combined_signal.py", "debug_ai.py", "estrategia.py",
    "grafico_rot.py", "quadro_rot.py", "resumo.py", "short_tab.py",
    "notif_russell.py", "btn_rotacao.py", "at.pdf", "market_scanner_pro.zip",
    "files.zip", "scanner*.zip",
]

moved = 0
for pattern in patterns:
    for f in scanner_dir.glob(pattern):
        if f.is_file() and f.name not in ("app.py", "requirements.txt"):
            dest = patches_dir / f.name
            shutil.move(str(f), str(dest))
            print(f"Movido: {f.name}")
            moved += 1

print(f"\nConcluido -- {moved} ficheiros movidos para _patches/")
