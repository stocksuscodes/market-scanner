"""
=============================================================
  SQUEEZE SCANNER — Job Independente
=============================================================
  Corre todos os dias às 19:00 (Lisboa)
  1. Lê sinais do Market Scanner PRO via API local
  2. Corre squeeze overlay (iborrowdesk + yfinance)
  3. Guarda squeeze_candidates.json
  4. Mostra resumo no terminal
=============================================================
  Uso:
    py -3.12 squeeze_scanner.py           → corre imediatamente
    py -3.12 squeeze_scanner.py --schedule → agenda às 19:00
=============================================================
"""

import requests
import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path
from squeeze_overlay import calc_squeeze_score

# ── CONFIGURAÇÃO ─────────────────────────────────────────
SCANNER_URL      = "http://localhost:5000"
OUTPUT_FILE      = Path(__file__).parent / "squeeze_candidates.json"
MIN_SQUEEZE_SCORE = 25   # score mínimo para incluir
MIN_SHORT_FLOAT   = 8.0  # % mínimo de short float
SCHEDULE_HOUR     = 19   # hora de execução (Lisboa)
SCHEDULE_MINUTE   = 0
DELAY_BETWEEN_TICKERS = 0.5  # segundos entre chamadas


def get_scan_tickers() -> list:
    """
    Obtém tickers do scan principal via API.
    Tenta o cache primeiro, depois faz scan manual.
    """
    print("  [SQUEEZE SCANNER] A obter tickers do scanner...", flush=True)

    # 1. Tenta cache
    try:
        r = requests.get(f"{SCANNER_URL}/api/cache/status", timeout=10)
        data = r.json()
        sinais = data.get("sinais", [])
        if isinstance(sinais, list) and len(sinais) > 0:
            tickers = [s["ticker"] for s in sinais if s.get("ticker")]
            print(f"  [SQUEEZE SCANNER] {len(tickers)} tickers do cache", flush=True)
            return tickers
    except Exception as e:
        print(f"  [SQUEEZE SCANNER] Cache indisponível: {e}", flush=True)

    # 2. Tenta scan manual (top 5 sectores)
    try:
        r = requests.post(
            f"{SCANNER_URL}/api/scan",
            json={"p_min": 5, "p_max": 50, "adx_min": 10, "rsi_max": 75},
            timeout=300
        )
        data = r.json()
        sinais = data.get("sinais", [])
        if isinstance(sinais, list) and len(sinais) > 0:
            tickers = [s["ticker"] for s in sinais if s.get("ticker")]
            print(f"  [SQUEEZE SCANNER] {len(tickers)} tickers do scan manual", flush=True)
            return tickers
    except Exception as e:
        print(f"  [SQUEEZE SCANNER] Scan manual falhou: {e}", flush=True)

    # 3. Fallback — lista base de squeeze conhecidos
    fallback = [
        "GME", "AMC", "HIMS", "SPCE", "MARA", "RIOT", "CLSK", "CORZ",
        "WULF", "CIFR", "LUNR", "IONQ", "RGTI", "QBTS", "QUBT", "BBAI",
        "SOUN", "AITX", "CXAI", "ACHR", "JOBY", "LILM", "NKLA", "MULN",
        "LCID", "RIVN", "NIO", "XPEV", "OPEN", "DKNG", "SNAP", "FUBO",
    ]
    print(f"  [SQUEEZE SCANNER] A usar lista fallback ({len(fallback)} tickers)", flush=True)
    return fallback


def run_squeeze_scan(tickers: list) -> list:
    """
    Corre o squeeze overlay em todos os tickers.
    Retorna lista ordenada por squeeze_score.
    """
    print(f"\n  [SQUEEZE SCANNER] A analisar {len(tickers)} tickers...\n", flush=True)

    candidates = []
    errors = 0

    for i, ticker in enumerate(tickers, 1):
        try:
            sq = calc_squeeze_score(ticker, use_cache=False)

            score = sq.get("squeeze_score", 0)
            sf    = sq.get("short_float_pct")
            nivel = sq.get("squeeze_nivel", "")

            # Filtrar por score e short float mínimo
            if score >= MIN_SQUEEZE_SCORE and (sf is None or sf >= MIN_SHORT_FLOAT):
                candidates.append(sq)
                print(f"  ✅ {ticker:6} | Score: {score:3}/100 | SI%: {sf}% | {nivel}", flush=True)
            else:
                print(f"  ⬜ {ticker:6} | Score: {score:3}/100 | SI%: {sf}%", flush=True)

        except Exception as e:
            errors += 1
            print(f"  ❌ {ticker:6} | Erro: {e}", flush=True)

        # Delay entre tickers
        if i % 10 == 0:
            time.sleep(1.0)
        else:
            time.sleep(DELAY_BETWEEN_TICKERS)

    print(f"\n  [SQUEEZE SCANNER] Erros: {errors}", flush=True)
    return sorted(candidates, key=lambda x: x["squeeze_score"], reverse=True)


def save_candidates(candidates: list):
    """Guarda candidatos em JSON."""
    output = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date":      datetime.now().strftime("%Y-%m-%d"),
        "total":     len(candidates),
        "candidates": candidates
    }
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n  [SQUEEZE SCANNER] Guardado em: {OUTPUT_FILE}", flush=True)


def print_summary(candidates: list):
    """Mostra resumo no terminal."""
    print("\n" + "="*60, flush=True)
    print("  SQUEEZE SCANNER — RESULTADOS", flush=True)
    print("="*60, flush=True)
    print(f"  Data: {datetime.now().strftime('%Y-%m-%d %H:%M')}", flush=True)
    print(f"  Candidatos encontrados: {len(candidates)}", flush=True)
    print("="*60, flush=True)

    if not candidates:
        print("  Nenhum candidato encontrado.", flush=True)
        return

    print(f"\n  {'TICKER':<8} {'SCORE':>6} {'SI%':>8} {'DTC':>6} {'BORROW':>8} {'NIVEL'}", flush=True)
    print("  " + "-"*58, flush=True)

    for c in candidates[:20]:  # top 20
        ticker = c.get("ticker", "?")
        score  = c.get("squeeze_score", 0)
        sf     = c.get("short_float_pct")
        dtc    = c.get("days_to_cover")
        borrow = c.get("borrow_fee")
        nivel  = c.get("squeeze_nivel", "")

        sf_str     = f"{sf:.1f}%" if sf else "N/A"
        dtc_str    = f"{dtc:.1f}d" if dtc else "N/A"
        borrow_str = f"{borrow:.2f}%" if borrow else "N/A"

        print(f"  {ticker:<8} {score:>5}/100 {sf_str:>8} {dtc_str:>6} {borrow_str:>8}  {nivel}", flush=True)

    print("="*60 + "\n", flush=True)


def run():
    """Executa o scan completo."""
    print("\n" + "="*60, flush=True)
    print("  SQUEEZE SCANNER — A INICIAR", flush=True)
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("="*60 + "\n", flush=True)

    # 1. Obter tickers
    tickers = get_scan_tickers()
    if not tickers:
        print("  [SQUEEZE SCANNER] Nenhum ticker encontrado. A sair.", flush=True)
        return

    # 2. Correr squeeze overlay
    candidates = run_squeeze_scan(tickers)

    # 3. Guardar resultados
    save_candidates(candidates)

    # 4. Mostrar resumo
    print_summary(candidates)


def schedule_daily():
    """Agenda execução diária às 19:00."""
    print(f"  [SQUEEZE SCANNER] Agendado para as {SCHEDULE_HOUR:02d}:{SCHEDULE_MINUTE:02d} todos os dias", flush=True)
    print("  Prima Ctrl+C para parar.\n", flush=True)

    while True:
        now = datetime.now()
        if now.hour == SCHEDULE_HOUR and now.minute == SCHEDULE_MINUTE:
            run()
            time.sleep(61)  # evitar dupla execução no mesmo minuto
        else:
            # Calcular tempo até próxima execução
            from datetime import timedelta
            next_run = now.replace(hour=SCHEDULE_HOUR, minute=SCHEDULE_MINUTE, second=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            wait = (next_run - now).seconds
            print(f"  [SQUEEZE SCANNER] Próxima execução: {next_run.strftime('%Y-%m-%d %H:%M')} (em {wait//3600}h {(wait%3600)//60}m)", flush=True)
            time.sleep(60)  # verificar a cada minuto


# ── ENTRADA ───────────────────────────────────────────────
if __name__ == "__main__":
    if "--schedule" in sys.argv:
        schedule_daily()
    else:
        run()
