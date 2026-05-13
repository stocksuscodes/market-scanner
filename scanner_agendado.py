"""
=============================================================
  WYCKOFF + SLJ SCANNER — Agendado + Email
=============================================================
  Corre automaticamente e envia resultado por email.

  Configurar:
    1. Preenche ALPACA_API_KEY e ALPACA_SECRET_KEY
    2. Preenche EMAIL_REMETENTE e EMAIL_PASSWORD
       (usa uma App Password do Gmail — ver README abaixo)
    3. Agenda no Windows Task Scheduler (ver instrucoes no fim)
=============================================================
"""

import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
import pandas_ta as ta
import requests

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO — PREENCHE AQUI
# ─────────────────────────────────────────────
ALPACA_API_KEY    = "PKL65VVV4RDXSP5LKZZEUEBIK7"
ALPACA_SECRET_KEY = "GvDL6TQw6kvX2UhtiVFxjo3bb2pufwzjYR3KUFMC82yd"

EMAIL_REMETENTE   = "stocks.us.codes@gmail.com"   # 
EMAIL_PASSWORD    = "nomz tzqt ntyg shra"   # 
EMAIL_DESTINATARIO = "stocks.us.codes@gmail.com"

TELEGRAM_TOKEN   = "8941761236:AAHpn30XTAJf9aDYc0foyM4MbFd_m9oP-dU"
TELEGRAM_CHAT_ID = "2070793836"

# Parâmetros do scan
PRECO_MIN = 5
PRECO_MAX = 100
ADX_MIN   = 10
RSI_MAX   = 75

ALPACA_BASE_URL = "https://data.alpaca.markets/v2"
ALPACA_HEADERS  = {
    "APCA-API-KEY-ID":     ALPACA_API_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET_KEY,
}

SECTORES = [
    {"etf": "XLK",  "nome": "Tecnologia",     "tickers": ["PLTR","SOFI","AMD","PINS","FSLR","SMCI","MARA","INTC","MU"]},
    {"etf": "XLF",  "nome": "Financeiro",      "tickers": ["NU","HOOD","BBD","ITUB","SQ","AFRM","UPST"]},
    {"etf": "XLE",  "nome": "Energia",         "tickers": ["RIG","CLNE","BORR","NOG","CIVI","SM"]},
    {"etf": "XLY",  "nome": "Cons. Discric.",  "tickers": ["F","NIO","AAL","CCL","DKNG","LYFT","DASH"]},
    {"etf": "XLV",  "nome": "Saúde",           "tickers": ["PFE","TALK","GEHC","TDOC","HIMS"]},
    {"etf": "XLI",  "nome": "Industriais",     "tickers": ["AL","JOBY","BLNK","CHPT"]},
    {"etf": "XLB",  "nome": "Materiais",       "tickers": ["FCX","CLF","MP","AA","X"]},
    {"etf": "XLU",  "nome": "Utilities",       "tickers": ["NEE","SO","DUK","PCG","AES"]},
    {"etf": "XLRE", "nome": "Real Estate",     "tickers": ["PLD","WELL","AMT","RDFN"]},
    {"etf": "XLC",  "nome": "Comunicação",     "tickers": ["SNAP","PINS","MTCH","BMBL","SPOT","TTD"]},
]


# ─────────────────────────────────────────────
#  ALPACA — DADOS HISTÓRICOS
# ─────────────────────────────────────────────
def obter_dados(ticker, dias=260):
    from datetime import timedelta
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
    except:
        return pd.DataFrame()


# ─────────────────────────────────────────────
#  MERCADO GERAL (VTI)
# ─────────────────────────────────────────────
def mercado_favoravel():
    df = obter_dados("VTI", 50)
    if len(df) < 22:
        return True, 0, 0
    sma21 = float(ta.sma(df["Close"], length=21).iloc[-1])
    preco = float(df["Close"].iloc[-1])
    return preco > sma21, round(preco, 2), round(sma21, 2)


# ─────────────────────────────────────────────
#  RANKING SECTORIAL
# ─────────────────────────────────────────────
def calcular_ranking():
    ranking = []
    for sec in SECTORES:
        df = obter_dados(sec["etf"], 30)
        perf = 0.0
        if len(df) >= 11:
            perf = round((float(df["Close"].iloc[-1]) - float(df["Close"].iloc[-10]))
                         / float(df["Close"].iloc[-10]) * 100, 2)
        ranking.append({**sec, "perf": perf})
        time.sleep(0.1)
    return sorted(ranking, key=lambda x: x["perf"], reverse=True)


# ─────────────────────────────────────────────
#  FASE WYCKOFF + SINAL SLJ
# ─────────────────────────────────────────────
def fase_wyckoff(preco, sma200, ema21, rsi, adx):
    d200 = (preco - sma200) / sma200 * 100
    d21  = (preco - ema21)  / ema21  * 100
    if d200 < -5:                               return "Distribuição"
    if d21 < -2 and rsi < 38:                  return "Spring"
    if d200 > 0 and abs(d21) < 3 and adx < 30: return "Acumulação"
    if d200 > 0 and rsi > 48 and adx > 25:     return "Markup"
    return "Test"

def sinal_slj(fase, preco, ema21, sma200, rsi, adx):
    if fase in ("Acumulação","Spring") and preco <= ema21*1.015 and preco > sma200 \
            and 30 < rsi < RSI_MAX and adx > ADX_MIN:
        return "LONG"
    if fase == "Distribuição" and rsi > 58:
        return "SHORT"
    return "AGUARDAR"


# ─────────────────────────────────────────────
#  ANALISAR ATIVO
# ─────────────────────────────────────────────
def analisar(ticker, etf, sector):
    df = obter_dados(ticker)
    if len(df) < 205:
        return None
    preco = float(df["Close"].iloc[-1])
    if not (PRECO_MIN <= preco <= PRECO_MAX):
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
    if not (preco > sma200): return None
    if not (preco <= ema21 * 1.02): return None
    fase  = fase_wyckoff(preco, sma200, ema21, rsi, adx)
    sinal = sinal_slj(fase, preco, ema21, sma200, rsi, adx)
    stop  = round(preco - 2 * atr, 2)
    alvo  = round(preco + 4 * atr, 2)
    rr    = round((alvo - preco) / (preco - stop), 1) if preco > stop else 0
    if rr < 1.2:
        return None
    return {"ticker": ticker, "etf": etf, "sector": sector,
            "preco": round(preco,2), "rsi": round(rsi,1), "adx": round(adx,1),
            "fase": fase, "slj": sinal, "stop": stop, "alvo": alvo, "rr": rr}


# ─────────────────────────────────────────────
#  GERAR EMAIL HTML
# ─────────────────────────────────────────────
def gerar_html(sinais, ranking, vti_ok, vti_preco, vti_sma21):
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")
    vti_cor   = "#16a34a" if vti_ok else "#dc2626"
    vti_texto = f"▲ VTI ${vti_preco} acima da SMA21 ${vti_sma21} — Mercado favorável" if vti_ok \
                else f"▼ VTI ${vti_preco} abaixo da SMA21 ${vti_sma21} — Mercado perigoso"

    # Ranking HTML
    rank_html = ""
    for i, s in enumerate(ranking[:10]):
        cor   = "#16a34a" if s["perf"] >= 0 else "#dc2626"
        label = f"★ Top {i+1}" if i < 5 else f"Rank {i+1}"
        bg    = "#dcfce7" if i < 5 else "#f7f7f7"
        rank_html += f"""
        <td style="padding:8px;text-align:center;background:{bg};border-radius:6px;border:1px solid #e0e0e0;">
          <div style="font-size:9px;color:#888;">{label} {s['etf']}</div>
          <div style="font-size:13px;font-weight:700;color:{cor};">{'+' if s['perf']>=0 else ''}{s['perf']}%</div>
          <div style="font-size:9px;color:#aaa;">{s['nome']}</div>
        </td>"""

    # Sinais HTML
    sinais_html = ""
    longs   = [s for s in sinais if s["slj"] == "LONG"]
    aguarda = [s for s in sinais if s["slj"] == "AGUARDAR"]

    def linha(s, top5):
        cor_borda = "#16a34a" if s["slj"] == "LONG" else "#f59e0b"
        badge_slj = f'<span style="background:#dcfce7;color:#15803d;padding:2px 6px;border-radius:3px;font-size:9px;font-weight:700;">{s["slj"]}</span>' \
                    if s["slj"] == "LONG" else \
                    f'<span style="background:#f3f4f6;color:#6b7280;padding:2px 6px;border-radius:3px;font-size:9px;font-weight:700;">{s["slj"]}</span>'
        fase_cores = {"Acumulação":"#dcfce7;color:#15803d","Spring":"#d9f99d;color:#3f6212",
                      "Markup":"#ccfbf1;color:#0f766e","Distribuição":"#fee2e2;color:#b91c1c","Test":"#fef9c3;color:#854d0e"}
        fc = fase_cores.get(s["fase"], "#f3f4f6;color:#555")
        badge_fase = f'<span style="background:{fc};padding:2px 6px;border-radius:3px;font-size:9px;font-weight:700;">{s["fase"]}</span>'
        star = " ★" if top5 and s["etf"] in top5 else ""
        return f"""
        <tr>
          <td style="padding:8px 10px;border-left:3px solid {cor_borda};font-size:14px;font-weight:700;">{s['ticker']}</td>
          <td style="padding:8px 10px;font-size:10px;color:#888;">{s['sector']}{star}</td>
          <td style="padding:8px 10px;">${s['preco']}</td>
          <td style="padding:8px 10px;color:{'#16a34a' if s['rsi']<42 else '#dc2626' if s['rsi']>55 else '#888'};">{s['rsi']}</td>
          <td style="padding:8px 10px;">{s['adx']}</td>
          <td style="padding:8px 10px;">{badge_fase}</td>
          <td style="padding:8px 10px;">{badge_slj}</td>
          <td style="padding:8px 10px;color:{'#16a34a' if s['rr']>=2 else '#888'};">{s['rr']}:1</td>
          <td style="padding:8px 10px;font-size:10px;"><span style="color:#dc2626;">▼${s['stop']}</span><br><span style="color:#16a34a;">▲${s['alvo']}</span></td>
        </tr>"""

    top5etfs = [s["etf"] for s in ranking[:5]]
    for s in longs + aguarda:
        sinais_html += linha(s, top5etfs)

    sem_sinais = '<tr><td colspan="9" style="text-align:center;padding:2rem;color:#aaa;">Nenhum sinal com os critérios actuais.</td></tr>' \
                 if not sinais else ""

    return f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family:'Courier New',monospace;background:#f7f7f7;padding:20px;color:#111;">
<div style="max-width:900px;margin:0 auto;background:#fff;border-radius:10px;padding:24px;border:1px solid #e0e0e0;">

  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
    <div>
      <h1 style="font-size:18px;font-weight:700;letter-spacing:.08em;margin:0;">MARKET SCANNER</h1>
      <p style="font-size:10px;color:#888;margin:3px 0 0;letter-spacing:.1em;">WYCKOFF · SLJ · SECTOR ROTATION · {ts}</p>
    </div>
    <div style="font-size:10px;padding:4px 10px;border-radius:4px;background:#dcfce7;color:#16a34a;border:1px solid #86efac;">ALPACA LIVE</div>
  </div>

  <div style="background:{vti_cor}15;border:1px solid {vti_cor}44;border-radius:20px;padding:6px 14px;display:inline-block;font-size:11px;font-weight:600;color:{vti_cor};margin-bottom:16px;">
    {vti_texto}
  </div>

  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:20px;">
    <div style="background:#f7f7f7;border:1px solid #e0e0e0;border-radius:8px;padding:12px;">
      <div style="font-size:9px;color:#888;text-transform:uppercase;margin-bottom:4px;">Analisados</div>
      <div style="font-size:22px;font-weight:700;">{len(sinais)}</div>
      <div style="font-size:9px;color:#aaa;">sinais encontrados</div>
    </div>
    <div style="background:#f7f7f7;border:1px solid #e0e0e0;border-radius:8px;padding:12px;">
      <div style="font-size:9px;color:#888;text-transform:uppercase;margin-bottom:4px;">Sinais LONG</div>
      <div style="font-size:22px;font-weight:700;color:#16a34a;">{len(longs)}</div>
      <div style="font-size:9px;color:#aaa;">compra</div>
    </div>
    <div style="background:#f7f7f7;border:1px solid #e0e0e0;border-radius:8px;padding:12px;">
      <div style="font-size:9px;color:#888;text-transform:uppercase;margin-bottom:4px;">Melhor R/R</div>
      <div style="font-size:22px;font-weight:700;">{max((s['rr'] for s in sinais), default=0)}x</div>
      <div style="font-size:9px;color:#aaa;">risco/recomp.</div>
    </div>
    <div style="background:#f7f7f7;border:1px solid #e0e0e0;border-radius:8px;padding:12px;">
      <div style="font-size:9px;color:#888;text-transform:uppercase;margin-bottom:4px;">VTI / Mercado</div>
      <div style="font-size:22px;font-weight:700;color:{vti_cor};">{'Alta ▲' if vti_ok else 'Baixa ▼'}</div>
      <div style="font-size:9px;color:#aaa;">VTI ${vti_preco} / SMA21 ${vti_sma21}</div>
    </div>
  </div>

  <div style="margin-bottom:20px;">
    <div style="font-size:9px;color:#888;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;">Ranking Sectorial — Momentum 10 Dias</div>
    <table style="width:100%;border-collapse:separate;border-spacing:4px;"><tr>{rank_html}</tr></table>
  </div>

  <table style="width:100%;border-collapse:collapse;">
    <tr style="background:#eeeeee;">
      <th style="padding:7px 10px;text-align:left;font-size:9px;color:#888;text-transform:uppercase;">Ticker</th>
      <th style="padding:7px 10px;text-align:left;font-size:9px;color:#888;text-transform:uppercase;">Sector</th>
      <th style="padding:7px 10px;text-align:left;font-size:9px;color:#888;text-transform:uppercase;">Preço $</th>
      <th style="padding:7px 10px;text-align:left;font-size:9px;color:#888;text-transform:uppercase;">RSI</th>
      <th style="padding:7px 10px;text-align:left;font-size:9px;color:#888;text-transform:uppercase;">ADX</th>
      <th style="padding:7px 10px;text-align:left;font-size:9px;color:#888;text-transform:uppercase;">Fase Wyckoff</th>
      <th style="padding:7px 10px;text-align:left;font-size:9px;color:#888;text-transform:uppercase;">Sinal SLJ</th>
      <th style="padding:7px 10px;text-align:left;font-size:9px;color:#888;text-transform:uppercase;">R/R</th>
      <th style="padding:7px 10px;text-align:left;font-size:9px;color:#888;text-transform:uppercase;">Stop / Alvo</th>
    </tr>
    {sinais_html}{sem_sinais}
  </table>

  <div style="margin-top:20px;padding-top:12px;border-top:1px solid #e0e0e0;font-size:9px;color:#aaa;">
    Filtro: ${PRECO_MIN}–${PRECO_MAX} · SMA200 · EMA21 pullback · ADX>{ADX_MIN} · RSI 30–{RSI_MAX} · Wyckoff · SLJ · Alpaca IEX
  </div>
</div>
</body>
</html>"""


# ─────────────────────────────────────────────
#  ENVIAR EMAIL
# ─────────────────────────────────────────────
def enviar_email(html, n_sinais):
    ts  = datetime.now().strftime("%d/%m/%Y %H:%M")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 Market Scanner — {n_sinais} sinais — {ts}"
    msg["From"]    = EMAIL_REMETENTE
    msg["To"]      = EMAIL_DESTINATARIO
    msg.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(EMAIL_REMETENTE, EMAIL_PASSWORD)
            s.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
        print(f"  ✓ Email enviado para {EMAIL_DESTINATARIO}")
    except Exception as e:
        print(f"  ✗ Erro ao enviar email: {e}")



# ─────────────────────────────────────────────
#  ENVIAR TELEGRAM
# ─────────────────────────────────────────────
def enviar_telegram(sinais, ranking, vti_ok, vti_preco, vti_sma21):
    if TELEGRAM_TOKEN == "COLOCA_AQUI_NOVO_TOKEN":
        print("  [Telegram] Token não configurado — a saltar.")
        return
    ts = datetime.now().strftime("%d/%m/%Y %H:%M")
    longs = [s for s in sinais if s["slj"] == "LONG"]
    vti_emoji = "🟢" if vti_ok else "🔴"
    top5 = [s["etf"] for s in ranking[:5]]

    msg = f"📊 *MARKET SCANNER — {ts}*\n"
    msg += f"{vti_emoji} VTI ${vti_preco} | SMA21 ${vti_sma21}\n"
    msg += f"🏆 Top sectores: {', '.join(top5)}\n\n"

    if not sinais:
        msg += "Nenhum sinal encontrado hoje."
    else:
        msg += f"*{len(longs)} sinais LONG | {len(sinais)} total*\n\n"
        for s in sinais[:10]:
            emoji = "🟢" if s["slj"] == "LONG" else "🟡"
            star  = " ★" if s["etf"] in top5 else ""
            msg += f"{emoji} *{s['ticker']}*{star} — {s['sector']}\n"
            msg += f"   ${s['preco']} | RSI {s['rsi']} | ADX {s['adx']} | {s['fase']}\n"
            msg += f"   Stop: ${s['stop']} | Alvo: ${s['alvo']} | R/R {s['rr']}:1\n\n"

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        print(f"  ✓ Telegram enviado")
    except Exception as e:
        print(f"  ✗ Erro Telegram: {e}")

# ─────────────────────────────────────────────
#  EXECUÇÃO PRINCIPAL
# ─────────────────────────────────────────────
def executar():
    print(f"\n{'='*50}")
    print(f"  SCANNER AGENDADO — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*50}")

    print("\n[1/4] A verificar mercado (VTI)...")
    vti_ok, vti_preco, vti_sma21 = mercado_favoravel()
    print(f"  VTI ${vti_preco} | SMA21 ${vti_sma21} | {'FAVORÁVEL ▲' if vti_ok else 'PERIGOSO ▼'}")

    print("\n[2/4] A calcular ranking sectorial...")
    ranking = calcular_ranking()
    for i, s in enumerate(ranking[:5]):
        print(f"  #{i+1} {s['etf']} {'+' if s['perf']>=0 else ''}{s['perf']}%")

    print("\n[3/4] A scanear tickers...")
    sinais = []
    for sec in SECTORES:
        for ticker in sec["tickers"]:
            print(f"  → {ticker}...", end=" ", flush=True)
            r = analisar(ticker, sec["etf"], sec["nome"])
            if r:
                sinais.append(r)
                print(f"✓ {r['fase']} | {r['slj']} | R/R {r['rr']}x")
            else:
                print("sem sinal")
            time.sleep(0.2)

    sinais.sort(key=lambda x: -x["rr"])
    print(f"\n  → {len(sinais)} sinais encontrados")

    print("\n[4/4] A enviar email...")
    html = gerar_html(sinais, ranking, vti_ok, vti_preco, vti_sma21)
    enviar_email(html, len(sinais))
    enviar_telegram(sinais, ranking, vti_ok, vti_preco, vti_sma21)

    print(f"\n  Concluído às {datetime.now().strftime('%H:%M:%S')}\n")


if __name__ == "__main__":
    executar()