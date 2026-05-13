"""
=============================================================
  WYCKOFF + SLJ SCANNER — Flask Backend + Alpaca Markets
=============================================================
  Instalar:
    pip install flask flask-cors alpaca-trade-api pandas pandas_ta requests

  Configurar:
    Edita ALPACA_API_KEY e ALPACA_SECRET_KEY abaixo
    (ou define como variáveis de ambiente)

  Correr:
    python app.py

  Acede em:
    http://localhost:5000
=============================================================
"""

import os
import time
from datetime import datetime, timedelta

import pandas as pd
import pandas_ta as ta
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__, static_folder="static", template_folder="static")
CORS(app)

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO ALPACA
# ─────────────────────────────────────────────
ALPACA_API_KEY    = os.getenv("ALPACA_API_KEY",    "PKL65VVV4RDXSP5LKZZEUEBIK7")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "GvDL6TQw6kvX2UhtiVFxjo3bb2pufwzjYR3KUFMC82yd")
ALPACA_BASE_URL   = "https://data.alpaca.markets/v2"
ALPACA_HEADERS    = {
    "APCA-API-KEY-ID":     ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
}

# ─────────────────────────────────────────────
#  SECTORES E TICKERS
# ─────────────────────────────────────────────
SECTORES = [
    {"etf": "XLK",  "nome": "Tecnologia",      "tickers": ["PLTR","SOFI","AMD","PINS","FSLR","SMCI","MARA","INTC","MU"]},
    {"etf": "XLF",  "nome": "Financeiro",       "tickers": ["NU","HOOD","BBD","ITUB","SQ","AFRM","UPST"]},
    {"etf": "XLE",  "nome": "Energia",          "tickers": ["RIG","CLNE","BORR","NOG","CIVI","SM"]},
    {"etf": "XLY",  "nome": "Cons. Discric.",   "tickers": ["F","NIO","AAL","CCL","DKNG","LYFT","DASH"]},
    {"etf": "XLV",  "nome": "Saúde",            "tickers": ["PFE","TALK","GEHC","TDOC","HIMS"]},
    {"etf": "XLI",  "nome": "Industriais",      "tickers": ["AL","JOBY","BLNK","CHPT"]},
    {"etf": "XLB",  "nome": "Materiais",        "tickers": ["FCX","CLF","MP","AA","X"]},
    {"etf": "XLU",  "nome": "Utilities",        "tickers": ["NEE","SO","DUK","PCG","AES"]},
    {"etf": "XLRE", "nome": "Real Estate",      "tickers": ["PLD","WELL","AMT","RDFN"]},
    {"etf": "XLC",  "nome": "Comunicação",      "tickers": ["SNAP","PINS","MTCH","BMBL","SPOT","TTD"]},
]

# ─────────────────────────────────────────────
#  ALPACA — OBTER DADOS HISTÓRICOS
# ─────────────────────────────────────────────
def obter_dados_alpaca(ticker: str, dias: int = 260) -> pd.DataFrame:
    """Obtém dados OHLCV do Alpaca Markets Data API v2."""
    fim   = datetime.utcnow()
    inicio = fim - timedelta(days=dias + 60)   # margem para fins-de-semana/feriados

    params = {
        "start":     inicio.strftime("%Y-%m-%d"),
        "end":       fim.strftime("%Y-%m-%d"),
        "timeframe": "1Day",
        "limit":     1000,
        "feed":      "iex",   # iex = gratuito; sip = pago
    }

    url = f"{ALPACA_BASE_URL}/stocks/{ticker}/bars"
    try:
        r = requests.get(url, headers=ALPACA_HEADERS, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        bars = data.get("bars", [])
        if not bars:
            return pd.DataFrame()

        df = pd.DataFrame(bars)
        df.rename(columns={"t":"Date","o":"Open","h":"High","l":"Low","c":"Close","v":"Volume"}, inplace=True)
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        df = df[["Open","High","Low","Close","Volume"]].dropna()
        return df

    except Exception as e:
        print(f"  [ERRO Alpaca] {ticker}: {e}")
        return pd.DataFrame()


# ─────────────────────────────────────────────
#  ALPACA — PREÇO EM TEMPO REAL (SNAPSHOT)
# ─────────────────────────────────────────────
def obter_preco_realtime(tickers: list[str]) -> dict:
    """Obtém o último preço de múltiplos tickers via Alpaca snapshot."""
    symbols = ",".join(tickers)
    url = f"{ALPACA_BASE_URL}/stocks/snapshots"
    try:
        r = requests.get(url, headers=ALPACA_HEADERS,
                         params={"symbols": symbols, "feed": "iex"}, timeout=10)
        r.raise_for_status()
        data = r.json()
        precos = {}
        for sym, snap in data.items():
            lp = snap.get("latestTrade", {}).get("p") or \
                 snap.get("minuteBar", {}).get("c") or \
                 snap.get("dailyBar", {}).get("c")
            if lp:
                precos[sym] = float(lp)
        return precos
    except Exception as e:
        print(f"  [ERRO snapshot] {e}")
        return {}


# ─────────────────────────────────────────────
#  FASE WYCKOFF
# ─────────────────────────────────────────────
def fase_wyckoff(preco, sma200, ema21, rsi, adx) -> str:
    d200 = (preco - sma200) / sma200 * 100
    d21  = (preco - ema21)  / ema21  * 100
    if d200 < -5:                                   return "Distribuição"
    if d21 < -2 and rsi < 38:                       return "Spring"
    if d200 > 0 and abs(d21) < 3 and adx < 30:     return "Acumulação"
    if d200 > 0 and rsi > 48 and adx > 25:         return "Markup"
    return "Test"


# ─────────────────────────────────────────────
#  SINAL SLJ
# ─────────────────────────────────────────────
def sinal_slj(fase, preco, ema21, sma200, rsi, adx, adx_min, rsi_max) -> str:
    pullback = preco <= ema21 * 1.015
    acima    = preco > sma200
    if fase in ("Acumulação", "Spring") and pullback and acima and 30 < rsi < rsi_max and adx > adx_min:
        return "LONG"
    if fase == "Distribuição" and rsi > 58:
        return "SHORT"
    return "AGUARDAR"


# ─────────────────────────────────────────────
#  ANALISAR UM ATIVO
# ─────────────────────────────────────────────
def analisar_ativo(ticker, etf, sector_nome, p_min, p_max, adx_min, rsi_max):
    df = obter_dados_alpaca(ticker, 260)
    if len(df) < 205:
        return None

    preco = float(df["Close"].iloc[-1])
    if not (p_min <= preco <= p_max):
        return None

    df["SMA200"] = ta.sma(df["Close"], length=200)
    df["EMA21"]  = ta.ema(df["Close"], length=21)
    df["RSI"]    = ta.rsi(df["Close"], length=14)
    df["ATR"]    = ta.atr(df["High"], df["Low"], df["Close"], length=14)
    adx_df       = ta.adx(df["High"], df["Low"], df["Close"], length=14)

    sma200 = float(df["SMA200"].iloc[-1])
    ema21  = float(df["EMA21"].iloc[-1])
    rsi    = float(df["RSI"].iloc[-1])
    atr    = float(df["ATR"].iloc[-1])
    adx    = float(adx_df["ADX_14"].iloc[-1]) if "ADX_14" in adx_df else 0.0

    if any(pd.isna(v) for v in [sma200, ema21, rsi, atr, adx]):
        return None

    # Filtros base
    if not (preco > sma200):          return None
    if not (preco <= ema21 * 1.02):   return None
    if adx < adx_min:                 return None
    if not (30 < rsi < rsi_max):      return None

    fase  = fase_wyckoff(preco, sma200, ema21, rsi, adx)
    sinal = sinal_slj(fase, preco, ema21, sma200, rsi, adx, adx_min, rsi_max)

    stop = round(preco - 2 * atr, 2)
    alvo = round(preco + 4 * atr, 2)
    rr   = round((alvo - preco) / (preco - stop), 1) if preco > stop else 0
    if rr < 1.2:
        return None

    # Volume ratio
    vol20 = float(df["Volume"].rolling(20).mean().iloc[-1])
    vol_r = round(float(df["Volume"].iloc[-1]) / vol20, 2) if vol20 > 0 else 1.0

    return {
        "ticker":    ticker,
        "etf":       etf,
        "sector":    sector_nome,
        "price":     round(preco, 2),
        "sma200":    round(sma200, 2),
        "ema21":     round(ema21, 2),
        "rsi":       round(rsi, 1),
        "adx":       round(adx, 1),
        "atr":       round(atr, 2),
        "vol_ratio": vol_r,
        "stop":      stop,
        "alvo":      alvo,
        "rr":        rr,
        "fase":      fase,
        "slj":       sinal,
    }


# ─────────────────────────────────────────────
#  RANKING SECTORIAL
# ─────────────────────────────────────────────
def calcular_ranking():
    ranking = []
    for sec in SECTORES:
        df = obter_dados_alpaca(sec["etf"], 30)
        if len(df) < 11:
            perf = 0.0
        else:
            perf = round(
                (float(df["Close"].iloc[-1]) - float(df["Close"].iloc[-10]))
                / float(df["Close"].iloc[-10]) * 100, 2
            )
        ranking.append({**sec, "perf": perf})
        time.sleep(0.1)
    return sorted(ranking, key=lambda x: x["perf"], reverse=True)


# ─────────────────────────────────────────────
#  FILTRO DE MERCADO GERAL (VTI)
# ─────────────────────────────────────────────
def mercado_favoravel() -> dict:
    df = obter_dados_alpaca("VTI", 50)
    if len(df) < 22:
        return {"ok": True, "preco": 0, "sma21": 0, "estado": "Desconhecido"}
    sma21 = float(ta.sma(df["Close"], length=21).iloc[-1])
    preco = float(df["Close"].iloc[-1])
    return {
        "ok":    preco > sma21,
        "preco": round(preco, 2),
        "sma21": round(sma21, 2),
        "estado": "Alta ▲" if preco > sma21 else "Baixa ▼",
    }


# ─────────────────────────────────────────────
#  ROTAS FLASK
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/api/scan", methods=["POST"])
def api_scan():
    """Executa o scan completo. Recebe JSON com parâmetros."""
    body    = request.get_json() or {}
    tickers = body.get("tickers", [])   # lista de {ticker, etf, sector}
    p_min   = float(body.get("p_min",   5))
    p_max   = float(body.get("p_max",  50))
    adx_min = float(body.get("adx_min", 20))
    rsi_max = float(body.get("rsi_max", 55))

    sinais = []
    for item in tickers:
        t   = item.get("ticker", "")
        etf = item.get("etf", "")
        sec = item.get("sector", "")
        print(f"  → {t} ...", flush=True)
        resultado = analisar_ativo(t, etf, sec, p_min, p_max, adx_min, rsi_max)
        if resultado:
            sinais.append(resultado)
        time.sleep(0.15)   # rate limit

    sinais.sort(key=lambda x: -x["rr"])
    return jsonify({"sinais": sinais, "total": len(tickers)})


@app.route("/api/ranking", methods=["GET"])
def api_ranking():
    """Retorna o ranking sectorial por momentum 10 dias."""
    ranking = calcular_ranking()
    return jsonify({"ranking": ranking})


@app.route("/api/mercado", methods=["GET"])
def api_mercado():
    """Retorna o estado do mercado geral (VTI)."""
    return jsonify(mercado_favoravel())


@app.route("/api/sectores", methods=["GET"])
def api_sectores():
    """Retorna a lista de sectores e tickers."""
    return jsonify({"sectores": SECTORES})


@app.route("/api/preco/<ticker>", methods=["GET"])
def api_preco(ticker):
    """Retorna o preço real-time de um ticker."""
    precos = obter_preco_realtime([ticker.upper()])
    preco  = precos.get(ticker.upper())
    return jsonify({"ticker": ticker.upper(), "preco": preco})


@app.route("/api/ai-analysis", methods=["POST"])
def api_ai_analysis():
    """Proxy para a API Anthropic — análise Wyckoff/SLJ por IA."""
    ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    body   = request.get_json() or {}
    prompt = body.get("prompt", "")

    if not ANTHROPIC_KEY:
        return jsonify({"analysis": "ANTHROPIC_API_KEY não configurada no ambiente."}), 200

    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type":      "application/json",
            },
            json={
                "model":      "claude-sonnet-4-20250514",
                "max_tokens": 500,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        text = "".join(b.get("text", "") for b in data.get("content", []))
        return jsonify({"analysis": text})
    except Exception as e:
        return jsonify({"analysis": f"Erro IA: {e}"}), 200


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n══════════════════════════════════════════")
    print("  WYCKOFF + SLJ SCANNER — Flask + Alpaca")
    print("══════════════════════════════════════════")
    print(f"  API Key configurada: {'Sim' if ALPACA_API_KEY != 'COLOCA_AQUI_A_TUA_KEY' else 'NÃO — edita app.py'}")
    print("  A correr em: http://localhost:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
