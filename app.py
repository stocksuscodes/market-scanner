"""
=============================================================
  MARKET SCANNER PRO — Flask + Alpaca + SLJ + Wyckoff + Markov
=============================================================
  Integra:
  - Dashboard web (Scanner 3)
  - Lógica SLJ: Simons + Livermore + PTJ + Wyckoff + Markov (15 pts)
  - Watchlist 1530 símbolos organizada por sectores
  - Análise IA por ticker
=============================================================
"""

import os
import time
import warnings
import numpy as np
from datetime import datetime, timedelta

import pandas as pd
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

warnings.filterwarnings("ignore")

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
#  PARÂMETROS SLJ
# ─────────────────────────────────────────────
HISTORY_DAYS      = 365
VOLUME_MIN        = 50_000
VOLUME_MULTIPLIER = 1.5
RSI_OVERSOLD      = 35
RSI_OVERBOUGHT    = 65
PIVOT_LOOKBACK    = 10
MA_SHORT          = 20
MA_LONG           = 200
# ─────────────────────────────────────────────
#  SECTORES E TICKERS
# ─────────────────────────────────────────────
SECTORES = [
    {"etf": "XLK",  "nome": "Tecnologia",     "tickers": [
        "PLTR","SOFI","AMD","PINS","FSLR","SMCI","MARA","INTC","MU",
        "NVDA","QCOM","MRVL","ON","WOLF","AMBA","LSCC","RMBS","SITM",
        "APPS","DDOG","ESTC","GTLB","NEWR","CFLT","BIGC","DOCN","FSLY",
        "SOUN","BBAI","AI","GFAI","AITX","CXAI","IONQ","RGTI","QUBT","QBTS",
    ]},
    {"etf": "XLF",  "nome": "Financeiro",     "tickers": [
        "NU","HOOD","BBD","ITUB","SQ","AFRM","UPST","DAVE","CURO","PSFE",
        "SOFI","OPEN","PAYO","LPRO","STEP","ENFN","MGNI","IMXI","EVTC","RPAY",
    ]},
    {"etf": "XLE",  "nome": "Energia",        "tickers": [
        "RIG","CLNE","BORR","NOG","CIVI","SM","PTEN","PUMP","NGL","TALO",
        "TELL","SWN","RRC","EQT","CNX","AR","NGAS","NEXT","MGY","REI",
    ]},
    {"etf": "XLY",  "nome": "Cons. Discric.", "tickers": [
        "F","NIO","AAL","CCL","DKNG","LYFT","DASH","RIVN","LCID","XPEV",
        "LI","JOBY","ACHR","BLNK","CHPT","EVGO","GME","AMC","SKLZ","OPEN",
    ]},
    {"etf": "XLV",  "nome": "Saúde",          "tickers": [
        "PFE","TALK","GEHC","TDOC","HIMS","DOCS","ACCD","AMWL","OSCR","CLOV",
        "NVAX","ARCT","VXRT","SRNE","OCGN","BEAM","EDIT","NTLA","CRSP","FATE",
    ]},
    {"etf": "XLI",  "nome": "Industriais",    "tickers": [
        "AL","JOBY","BLNK","CHPT","KTOS","RKLB","ASTR","SPCE","AVAV","UAVS",
        "ZIM","DAC","GSL","SBLK","GOGL","EGLE","GNK","CTRM","SHIP","TOPS",
    ]},
    {"etf": "XLB",  "nome": "Materiais",      "tickers": [
        "FCX","CLF","MP","AA","X","VALE","MT","STLD","NUE","CENX",
        "PAAS","EGO","HL","CDE","SILV","FSM","SVM","SAND","SSRM","AUMN",
    ]},
    {"etf": "XLU",  "nome": "Utilities",      "tickers": [
        "NEE","SO","DUK","PCG","AES","EIX","CNP","CMS","NI","OGE",
        "CLNE","AMRC","REGI","GPRE","GEVO","REX","AMTX","STEM","FLNC","NOVA",
    ]},
    {"etf": "XLRE", "nome": "Real Estate",    "tickers": [
        "PLD","WELL","AMT","RDFN","OPEN","HOUS","EXPI","UWMC","RKT","PFSI",
        "NRZ","TWO","IVR","MITT","BXMT","GPMT","MAIN","HTGC","ARCC","GBDC",
    ]},
    {"etf": "XLC",  "nome": "Comunicação",    "tickers": [
        "SNAP","PINS","MTCH","BMBL","SPOT","TTD","FUBO","PARA","SIRI","DISH",
        "ATVI","TTWO","EA","ZNGA","DKNG","PENN","GME","AMC","SKLZ","NTES",
    ]},
    {"etf": "MARA", "nome": "Cripto/Miners",  "tickers": [
        "MARA","RIOT","CIFR","HUT","BITF","CLSK","IREN","BTBT","WULF","CORZ",
        "HIVE","BTCS","MSTR","COIN","HOOD","ARBK","SDIG","BTOG","BTCM","GREE",
    ]},
    {"etf": "TSLA", "nome": "EV Avançado",    "tickers": [
        "RIVN","LCID","NIO","XPEV","LI","FSR","GOEV","MULN","ZEV","RIDE",
        "WKHS","HYLN","SOLO","MVST","IDEX","NKLA","ACHR","JOBY","LILM","SPCE",
    ]},
]

TICKER_SECTOR_MAP = {}
for s in SECTORES:
    for t in s["tickers"]:
        TICKER_SECTOR_MAP[t] = {"etf": s["etf"], "sector": s["nome"]}
        # ─────────────────────────────────────────────
#  ALPACA — DADOS HISTÓRICOS
# ─────────────────────────────────────────────
def obter_dados_alpaca(ticker: str, dias: int = 260) -> pd.DataFrame:
    fim    = datetime.utcnow()
    inicio = fim - timedelta(days=dias + 60)
    params = {
        "start":     inicio.strftime("%Y-%m-%d"),
        "end":       fim.strftime("%Y-%m-%d"),
        "timeframe": "1Day",
        "limit":     1000,
        "feed":      "iex",
    }
    try:
        r = requests.get(f"{ALPACA_BASE_URL}/stocks/{ticker}/bars",
                         headers=ALPACA_HEADERS, params=params, timeout=10)
        r.raise_for_status()
        bars = r.json().get("bars", [])
        if not bars:
            return pd.DataFrame()
        df = pd.DataFrame(bars)
        df.rename(columns={"t":"Date","o":"Open","h":"High","l":"Low","c":"Close","v":"Volume"}, inplace=True)
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        return df[["Open","High","Low","Close","Volume"]].dropna()
    except Exception as e:
        print(f"  [ERRO] {ticker}: {e}")
        return pd.DataFrame()


def obter_preco_realtime(tickers: list) -> dict:
    try:
        r = requests.get(f"{ALPACA_BASE_URL}/stocks/snapshots",
                         headers=ALPACA_HEADERS,
                         params={"symbols": ",".join(tickers), "feed": "iex"}, timeout=10)
        r.raise_for_status()
        precos = {}
        for sym, snap in r.json().items():
            lp = snap.get("latestTrade", {}).get("p") or \
                 snap.get("minuteBar", {}).get("c") or \
                 snap.get("dailyBar", {}).get("c")
            if lp:
                precos[sym] = float(lp)
        return precos
    except:
        return {}


# ─────────────────────────────────────────────
#  INDICADORES TÉCNICOS
# ─────────────────────────────────────────────
def compute_rsi(series, period=14):
    delta = series.diff()
    gain  = delta.clip(lower=0).ewm(com=period-1, min_periods=period).mean()
    loss  = (-delta.clip(upper=0)).ewm(com=period-1, min_periods=period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return 100 - 100 / (1 + rs)

def compute_sma(series, period):
    return series.rolling(period).mean()

def compute_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def compute_atr(df, period=14):
    return (df["High"] - df["Low"]).rolling(period).mean()

def compute_adx(df, period=14):
    plus_dm  = df["High"].diff().clip(lower=0)
    minus_dm = (-df["Low"].diff()).clip(lower=0)
    tr       = (df["High"] - df["Low"]).rolling(period).mean()
    plus_di  = 100 * plus_dm.rolling(period).mean() / tr.replace(0, np.nan)
    minus_di = 100 * minus_dm.rolling(period).mean() / tr.replace(0, np.nan)
    dx       = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
    return dx.rolling(period).mean()

def compute_indicators(df):
    df = df.copy()
    c = df["Close"]
    df["ma20"]     = compute_sma(c, MA_SHORT)
    df["ma200"]    = compute_sma(c, MA_LONG)
    df["ema21"]    = compute_ema(c, 21)
    df["sma200"]   = compute_sma(c, 200)
    df["vol_ma20"] = df["Volume"].rolling(MA_SHORT).mean()
    df["rsi"]      = compute_rsi(c)
    df["atr"]      = compute_atr(df)
    df["adx"]      = compute_adx(df)
    return df


# ─────────────────────────────────────────────
#  MÓDULO SIMONS (0-3 pts)
# ─────────────────────────────────────────────
def score_simons(df):
    score, notes = 0, []
    last = df.iloc[-1]
    if pd.notna(last["vol_ma20"]) and last["vol_ma20"] > 0:
        if last["Volume"] > last["vol_ma20"] * VOLUME_MULTIPLIER:
            score += 1
            notes.append(f"Volume {last['Volume']/last['vol_ma20']:.1f}× acima da média 20d")
    if pd.notna(last["ma20"]) and last["ma20"] > 0:
        pct = (last["Close"] - last["ma20"]) / last["ma20"] * 100
        if abs(pct) > 3:
            score += 1
            notes.append(f"Preço {abs(pct):.1f}% {'acima' if pct>0 else 'abaixo'} da MA20")
    closes  = df["Close"].iloc[-5:]
    volumes = df["Volume"].iloc[-5:]
    if all(closes.diff().dropna() > 0) and all(volumes.diff().dropna() > 0):
        score += 1
        notes.append("Padrão Simons: 4d alta c/ volume crescente")
    elif all(closes.diff().dropna() < 0) and all(volumes.diff().dropna() > 0):
        score += 1
        notes.append("Padrão Simons: 4d queda c/ volume crescente")
    return score, notes


# ─────────────────────────────────────────────
#  MÓDULO LIVERMORE (0-3 pts)
# ─────────────────────────────────────────────
def score_livermore(df):
    score, notes = 0, []
    n = PIVOT_LOOKBACK
    if len(df) < n + 3:
        return 0, []
    recent = df.iloc[-n-1:-1]
    last   = df.iloc[-1]
    ph = recent["High"].max()
    pl = recent["Low"].min()
    bull = last["High"] > ph and last["Close"] > ph and last["Volume"] > last["vol_ma20"]
    bear = last["Low"] < pl and last["Close"] < pl and last["Volume"] > last["vol_ma20"]
    if bull:
        score += 1
        notes.append(f"Chave altista: rompeu máximo {n}d (${ph:.2f})")
    elif bear:
        score += 1
        notes.append(f"Chave baixista: rompeu mínimo {n}d (${pl:.2f})")
    rng = last["High"] - last["Low"]
    if rng > 0:
        cp = (last["Close"] - last["Low"]) / rng
        if bull and cp > 0.75:
            score += 1
            notes.append("Fecho confirmatório bullish")
        elif bear and cp < 0.25:
            score += 1
            notes.append("Fecho confirmatório bearish")
    last3l = df["Low"].iloc[-4:-1]
    last3h = df["High"].iloc[-4:-1]
    if bull and any((last3l <= ph*1.005) & (last3l >= ph*0.995)):
        score += 1
        notes.append("Reteste do pivô com suporte")
    elif bear and any((last3h >= pl*0.995) & (last3h <= pl*1.005)):
        score += 1
        notes.append("Reteste do pivô com resistência")
    return score, notes
# ─────────────────────────────────────────────
#  MÓDULO PTJ (0-3 pts)
# ─────────────────────────────────────────────
def score_ptj(df):
    score, notes = 0, []
    if len(df) < 30:
        return 0, []
    last  = df.iloc[-1]
    rsi   = df["rsi"]
    close = df["Close"]
    if pd.notna(last["ma200"]):
        pct = abs(last["Close"] / last["ma200"] - 1) * 100
        score += 1
        notes.append(f"{'Acima' if last['Close'] > last['ma200'] else 'Abaixo'} MA200 ({pct:.1f}%)")
    w = 20
    sc = close.iloc[-w:]; sr = rsi.iloc[-w:]
    pl1 = sc.iloc[:w//2].min(); pl2 = sc.iloc[w//2:].min()
    rl1 = sr.iloc[:w//2].min(); rl2 = sr.iloc[w//2:].min()
    if pl2 < pl1 and rl2 > rl1 and last["rsi"] < RSI_OVERSOLD + 15:
        score += 1
        notes.append(f"Divergência altista RSI ({last['rsi']:.0f})")
    elif sc.iloc[w//2:].max() > sc.iloc[:w//2].max() and \
         sr.iloc[w//2:].max() < sr.iloc[:w//2].max() and \
         last["rsi"] > RSI_OVERBOUGHT - 15:
        score += 1
        notes.append(f"Divergência baixista RSI ({last['rsi']:.0f})")
    if pd.notna(last["atr"]) and last["atr"] > 0:
        rr = last["atr"] / last["Close"] * 100
        if rr > 0.8:
            score += 1
            notes.append(f"Volatilidade {rr:.1f}% — R:R operável")
    return score, notes


# ─────────────────────────────────────────────
#  MÓDULO WYCKOFF (0-3 pts)
# ─────────────────────────────────────────────
def score_wyckoff_module(df):
    score, notes = 0, []
    if len(df) < 40:
        return 0, []
    rw   = 30
    last = df.iloc[-1]
    rec  = df.iloc[-rw:]
    hr   = rec["High"].max()
    lr   = rec["Low"].min()
    mid  = (hr + lr) / 2
    bw   = (hr - lr) / mid * 100
    if bw < 20:
        score += 1
        notes.append(f"Trading Range {bw:.1f}%")
    r5 = df.iloc[-6:-1]
    spring = any(r5.iloc[i]["Low"] < lr*0.99 and r5.iloc[i]["Close"] > lr for i in range(len(r5)))
    utad   = any(r5.iloc[i]["High"] > hr*1.01 and r5.iloc[i]["Close"] < hr for i in range(len(r5)))
    if spring:
        score += 1
        notes.append(f"Spring: acumulação (abaixo ${lr:.2f})")
    elif utad:
        score += 1
        notes.append(f"UTAD: distribuição (acima ${hr:.2f})")
    va = rec["Volume"].mean()
    if last["Close"] > hr and last["Volume"] > va * 1.3:
        score += 1
        notes.append(f"SOS: rompimento com volume forte")
    elif last["Close"] < lr and last["Volume"] > va * 1.3:
        score += 1
        notes.append(f"SOW: colapso com volume forte")
    return score, notes


# ─────────────────────────────────────────────
#  MÓDULO MARKOV (0-3 pts)
# ─────────────────────────────────────────────
def get_market_state(ret, vol_ratio):
    up = ret >= 0
    hv = vol_ratio >= 1.0
    if up and hv:     return 3
    if up and not hv: return 2
    if not up and hv: return 0
    return 1

def score_markov(df):
    score, notes = 0, []
    if len(df) < 60:
        return 0, []
    rets      = df["Close"].pct_change().fillna(0)
    vol_ratio = (df["Volume"] / df["vol_ma20"].replace(0, np.nan)).fillna(1.0)
    states    = [get_market_state(rets.iloc[i], vol_ratio.iloc[i]) for i in range(len(df))]
    matrix    = np.zeros((4, 4))
    for i in range(len(states)-1):
        matrix[states[i]][states[i+1]] += 1
    rs = matrix.sum(axis=1, keepdims=True)
    rs[rs == 0] = 1
    matrix /= rs
    cur = states[-1]
    names = {0:"Distribuição", 1:"Queda silenciosa", 2:"Recuperação", 3:"Força real"}
    notes.append(f"Estado: {names[cur]}")
    if cur in (2, 3):
        score += 1
        notes.append("Estado favorável")
    sv = np.zeros(4); sv[cur] = 1.0
    for _ in range(3): sv = sv @ matrix
    if sv[3] > 0.40:
        score += 1
        notes.append(f"Prob. força 3d: {sv[3]:.0%}")
    bull_days = sum(1 for s in states[-5:] if s in (2,3))
    if bull_days >= 4:
        score += 1
        notes.append(f"Regime bull: {bull_days}/5 dias")
    return score, notes


# ─────────────────────────────────────────────
#  FASE WYCKOFF
# ─────────────────────────────────────────────
def fase_wyckoff(preco, sma200, ema21, rsi, adx):
    d200 = (preco - sma200) / sma200 * 100
    d21  = (preco - ema21)  / ema21  * 100
    if d200 < -5:                               return "Distribuição"
    if d21 < -2 and rsi < 38:                  return "Spring"
    if d200 > 0 and abs(d21) < 3 and adx < 30: return "Acumulação"
    if d200 > 0 and rsi > 48 and adx > 25:     return "Markup"
    return "Test"
# ─────────────────────────────────────────────
#  ANALISAR UM ATIVO
# ─────────────────────────────────────────────
def analisar_ativo(ticker, etf, sector_nome, p_min, p_max, adx_min, rsi_max):
    df = obter_dados_alpaca(ticker, HISTORY_DAYS)
    if len(df) < 205:
        return None
    preco = float(df["Close"].iloc[-1])
    if not (p_min <= preco <= p_max):
        return None
    if float(df["Volume"].iloc[-1]) < VOLUME_MIN:
        return None
    df = compute_indicators(df)
    last = df.iloc[-1]
    sma200 = float(last["sma200"]) if pd.notna(last["sma200"]) else None
    ema21  = float(last["ema21"])  if pd.notna(last["ema21"])  else None
    rsi    = float(last["rsi"])    if pd.notna(last["rsi"])    else None
    atr    = float(last["atr"])    if pd.notna(last["atr"])    else None
    adx    = float(last["adx"])    if pd.notna(last["adx"])    else 0.0
    if any(v is None for v in [sma200, ema21, rsi, atr]):
        return None
    ss, sn = score_simons(df)
    ls, ln = score_livermore(df)
    ps, pn = score_ptj(df)
    ws, wn = score_wyckoff_module(df)
    ms, mn = score_markov(df)
    total  = ss + ls + ps + ws + ms
    fase = fase_wyckoff(preco, sma200, ema21, rsi, adx)
    pullback = preco <= ema21 * 1.015
    acima    = preco > sma200
    if fase in ("Acumulação", "Spring") and pullback and acima and 30 < rsi < rsi_max and adx > adx_min:
        slj = "LONG"
    elif fase == "Distribuição" and rsi > 58:
        slj = "SHORT"
    else:
        slj = "AGUARDAR"
    stop = round(preco - 2 * atr, 2)
    alvo = round(preco + 4 * atr, 2)
    rr   = round((alvo - preco) / (preco - stop), 1) if preco > stop else 0
    vol20 = float(df["Volume"].rolling(20).mean().iloc[-1])
    vol_r = round(float(df["Volume"].iloc[-1]) / vol20, 2) if vol20 > 0 else 1.0
    prev  = df.iloc[-2]
    chg   = round((preco / float(prev["Close"]) - 1) * 100, 2)
    return {
        "ticker": ticker, "etf": etf, "sector": sector_nome,
        "price": round(preco, 2), "chg_pct": chg,
        "sma200": round(sma200, 2), "ema21": round(ema21, 2),
        "rsi": round(rsi, 1), "adx": round(adx, 1),
        "atr": round(atr, 2), "vol_ratio": vol_r,
        "stop": stop, "alvo": alvo, "rr": rr,
        "fase": fase, "slj": slj,
        "score_total": total, "score_simons": ss, "score_livermore": ls,
        "score_ptj": ps, "score_wyckoff": ws, "score_markov": ms,
        "notes_simons": sn, "notes_livermore": ln, "notes_ptj": pn,
        "notes_wyckoff": wn, "notes_markov": mn,
        "signal_label": "FORTE" if total >= 12 else "MÉDIO" if total >= 7 else "FRACO",
    }


# ─────────────────────────────────────────────
#  RANKING SECTORIAL
# ─────────────────────────────────────────────
def calcular_ranking():
    ranking = []
    for sec in SECTORES:
        df = obter_dados_alpaca(sec["etf"], 30)
        perf = 0.0
        if len(df) >= 11:
            perf = round((float(df["Close"].iloc[-1]) - float(df["Close"].iloc[-10]))
                         / float(df["Close"].iloc[-10]) * 100, 2)
        ranking.append({**sec, "perf": perf})
        time.sleep(0.1)
    return sorted(ranking, key=lambda x: x["perf"], reverse=True)


# ─────────────────────────────────────────────
#  MERCADO GERAL (VTI)
# ─────────────────────────────────────────────
def mercado_favoravel() -> dict:
    df = obter_dados_alpaca("VTI", 50)
    if len(df) < 22:
        return {"ok": True, "preco": 0, "sma21": 0, "estado": "Desconhecido"}
    sma21 = float(compute_sma(df["Close"], 21).iloc[-1])
    preco = float(df["Close"].iloc[-1])
    return {
        "ok": preco > sma21, "preco": round(preco, 2), "sma21": round(sma21, 2),
        "estado": "Alta ▲" if preco > sma21 else "Baixa ▼",
    }


# ─────────────────────────────────────────────
#  ROTAS FLASK
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/api/sectores", methods=["GET"])
def api_sectores():
    return jsonify({"sectores": SECTORES})

@app.route("/api/mercado", methods=["GET"])
def api_mercado():
    return jsonify(mercado_favoravel())

@app.route("/api/ranking", methods=["GET"])
def api_ranking():
    return jsonify({"ranking": calcular_ranking()})

@app.route("/api/scan", methods=["POST"])
def api_scan():
    body    = request.get_json() or {}
    tickers = body.get("tickers", [])
    p_min   = float(body.get("p_min",   5))
    p_max   = float(body.get("p_max",  100))
    adx_min = float(body.get("adx_min", 10))
    rsi_max = float(body.get("rsi_max", 75))
    sinais = []
    for item in tickers:
        t   = item.get("ticker", "")
        etf = item.get("etf", "")
        sec = item.get("sector", "")
        print(f"  → {t} ...", flush=True)
        resultado = analisar_ativo(t, etf, sec, p_min, p_max, adx_min, rsi_max)
        if resultado:
            sinais.append(resultado)
        time.sleep(0.15)
    sinais.sort(key=lambda x: (-x["score_total"], -x["rr"]))
    return jsonify({"sinais": sinais, "total": len(tickers)})

@app.route("/api/preco/<ticker>", methods=["GET"])
def api_preco(ticker):
    precos = obter_preco_realtime([ticker.upper()])
    return jsonify({"ticker": ticker.upper(), "preco": precos.get(ticker.upper())})

@app.route("/api/ai-analysis", methods=["POST"])
def api_ai_analysis():
    ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    body   = request.get_json() or {}
    prompt = body.get("prompt", "")
    if not ANTHROPIC_KEY:
        return jsonify({"analysis": "ANTHROPIC_API_KEY não configurada."}), 200
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01",
                     "Content-Type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 500,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        r.raise_for_status()
        text = "".join(b.get("text","") for b in r.json().get("content",[]))
        return jsonify({"analysis": text})
    except Exception as e:
        return jsonify({"analysis": f"Erro IA: {e}"}), 200


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n══════════════════════════════════════════")
    print("  MARKET SCANNER PRO — Flask + Alpaca")
    print("  SLJ: Simons + Livermore + PTJ + Wyckoff + Markov")
    print("══════════════════════════════════════════")
    print(f"  API Key: OK")
    print("  A correr em: http://localhost:5000\n")
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
    # placeholder