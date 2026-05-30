# -*- coding: utf-8 -*-
"""Patch niveis 1-2-3: VCP, DryUp, RS Rating, Position Sizing, Expectancy, Breadth"""
import os

scanner_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Python", "scanner")
app_path  = os.path.join(scanner_dir, "app.py")
html_path = os.path.join(scanner_dir, "static", "index.html")

with open(app_path, 'r', encoding='utf-8') as f: app = f.read()
with open(html_path, 'r', encoding='utf-8') as f: html = f.read()

applied = 0

# ── APP.PY PATCHES ──

new_funcs = '''
def detect_vcp(df):
    if len(df) < 60: return False, 0, 0.0
    try:
        windows = []
        for i in range(3):
            w = df.iloc[-(30-i*10):-(20-i*10)] if i < 2 else df.iloc[-10:]
            rng = float((w["High"].max()-w["Low"].min())/w["Close"].mean()*100)
            vol = float(w["Volume"].mean())
            windows.append((rng, vol))
        rc = all(windows[i][0]>windows[i+1][0] for i in range(2))
        vc = all(windows[i][1]>windows[i+1][1] for i in range(2))
        if rc and vc: return True, len(windows), round(windows[-1][0],2)
        return False, 0, 0.0
    except: return False, 0, 0.0

def detect_volume_dryup(df):
    if len(df) < 25: return False
    try:
        vol_ma20  = float(df["Volume"].rolling(20).mean().iloc[-1])
        vol_last5 = float(df["Volume"].iloc[-5:].mean())
        return vol_last5 < vol_ma20 * 0.70
    except: return False

def calc_position_size(preco, stop, capital=25000, risk_pct=0.01):
    if preco <= stop or stop <= 0: return 0, 0.0
    risco = abs(preco - stop)
    shares = int(capital * risk_pct / risco)
    return shares, round(shares * preco, 2)

def calc_expectancy(win_rate=0.45, rr=2.0):
    return round((win_rate * rr) - ((1-win_rate) * 1.0), 2)

_breadth_cache = {"data": None, "ts": None}
def get_market_breadth():
    import time as _t
    now = _t.time()
    if _breadth_cache["data"] and _breadth_cache["ts"] and now-_breadth_cache["ts"]<14400:
        return _breadth_cache["data"]
    try:
        sample=["SPY","QQQ","IWM","XLK","XLF","XLV","XLE","XLI","XLY","XLP",
                "AAPL","MSFT","NVDA","AMZN","META","GOOGL","JPM","JNJ","XOM","PG",
                "BAC","WMT","UNH","HD","CVX","LLY","ABBV","MRK","PFE","KO"]
        above=0
        for t in sample:
            try:
                df=obter_dados_alpaca(t,60)
                if len(df)>=50 and float(df["Close"].iloc[-1])>float(compute_sma(df["Close"],50).iloc[-1]):
                    above+=1
            except: continue
        pct=round(above/len(sample)*100,1)
        result={"pct_above_sma50":pct,"bullish":pct>=50,"regime":"Forte" if pct>=65 else "Neutro" if pct>=50 else "Fraco"}
        _breadth_cache["data"]=result; _breadth_cache["ts"]=now
        return result
    except: return {"pct_above_sma50":50.0,"bullish":True,"regime":"Desconhecido"}

'''

marker = "def compute_indicators(df):"
if "detect_vcp" not in app and marker in app:
    app = app.replace(marker, new_funcs + "\n" + marker)
    print("PATCH 1 OK -- VCP+DryUp+PosSizing+Breadth functions")
    applied += 1
else:
    print("PATCH 1 SKIP")

# VCP+DryUp+PosSizing calcs in api_lookup
old2 = '''    # Sector rotation penalty — se sector não está no top 5 do ranking, penaliza 10 pts
    top5_etfs = [s.get("etf","") for s in (_cache.get("top5_sectors") or [])]
    if etf and top5_etfs and etf not in top5_etfs:
        score_100 = max(0, score_100 - 10)

    # Markov detalhado'''
new2 = '''    # Sector rotation penalty — se sector não está no top 5 do ranking, penaliza 10 pts
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
    expectancy = calc_expectancy(win_rate=0.45, rr=rr if rr > 0 else 2.0)

    # Markov detalhado'''

if old2 in app and "detect_vcp" in app:
    app = app.replace(old2, new2)
    print("PATCH 2 OK -- VCP+DryUp calcs in lookup")
    applied += 1
else:
    print("PATCH 2 SKIP")

# Add to return
old3 = '''        "vcp": vcp, "vcp_contractions": vcp_n, "vcp_tightness": vcp_t,
        "volume_dryup": vol_dryup,
        "rs_rating": 50,
        "position_shares": pos_shares, "position_exposure": pos_exposure,
        "expectancy": expectancy,'''
if old3 not in app:
    old3b = '''        "rs_rating": 50,
    })'''
    new3b = '''        "rs_rating": 50,
        "vcp": vcp if "vcp" in dir() else False,
        "vcp_contractions": vcp_n if "vcp_n" in dir() else 0,
        "vcp_tightness": vcp_t if "vcp_t" in dir() else 0.0,
        "volume_dryup": vol_dryup if "vol_dryup" in dir() else False,
        "position_shares": pos_shares if "pos_shares" in dir() else 0,
        "expectancy": expectancy if "expectancy" in dir() else 0.0,
    })'''
    if old3b in app:
        app = app.replace(old3b, new3b)
        print("PATCH 3 OK -- return fields")
        applied += 1
else:
    print("PATCH 3 SKIP -- already present")

# Breadth route
old4 = '@app.route("/api/market-filter", methods=["GET"])\ndef api_market_filter():'
new4 = '''@app.route("/api/breadth", methods=["GET"])
def api_breadth():
    return jsonify(get_market_breadth())

@app.route("/api/market-filter", methods=["GET"])
def api_market_filter():'''
if "api_breadth" not in app and old4 in app:
    app = app.replace(old4, new4)
    print("PATCH 4 OK -- breadth route")
    applied += 1
else:
    print("PATCH 4 SKIP")

with open(app_path, 'w', encoding='utf-8') as f: f.write(app)

# ── HTML PATCHES ──
# VCP+DRY badges
old_h1 = "${s.score_total!=null?s.score_total+'/15':'—'}</span></span>"
new_h1 = "${s.score_total!=null?s.score_total+'/15':'—'}</span>${s.vcp?'<span style=\"font-size:8px;margin-left:3px;padding:1px 4px;border-radius:3px;background:#1e1b4b;color:#a5b4fc;font-weight:700\">VCP</span>':''}${s.volume_dryup?'<span style=\"font-size:8px;margin-left:2px;padding:1px 4px;border-radius:3px;background:#052e16;color:#4ade80;font-weight:700\">DRY</span>':''}</span>"
if old_h1 in html and "VCP" not in html:
    html = html.replace(old_h1, new_h1)
    print("PATCH H1 OK -- VCP+DRY badges")
    applied += 1
else:
    print("PATCH H1 SKIP")

# Position sizing in detail
old_h2 = '        <div><div class="d-lbl">Risco $</div><div class="d-val red">$${(s.price - s.stop).toFixed(2)}</div></div>\n      </div>'
new_h2 = '''        <div><div class="d-lbl">Risco $</div><div class="d-val red">$${(s.price - s.stop).toFixed(2)}</div></div>
        ${s.position_shares ? `<div><div class="d-lbl">Shares (1%)</div><div class="d-val green">${s.position_shares}</div></div>` : ''}
        ${s.expectancy !== undefined ? `<div><div class="d-lbl">Expectancy</div><div class="d-val ${s.expectancy>0?'green':'red'}">${s.expectancy}R</div></div>` : ''}
        ${s.rs_rating ? `<div><div class="d-lbl">RS Rating</div><div class="d-val ${s.rs_rating>=80?'green':''}">${s.rs_rating}/99</div></div>` : ''}
        ${s.vcp ? `<div><div class="d-lbl">VCP</div><div class="d-val" style="color:#a5b4fc">${s.vcp_contractions} contr. ${s.vcp_tightness}%</div></div>` : ''}
      </div>'''
if old_h2 in html and "position_shares" not in html:
    html = html.replace(old_h2, new_h2)
    print("PATCH H2 OK -- position sizing detail")
    applied += 1
else:
    print("PATCH H2 SKIP")

with open(html_path, 'w', encoding='utf-8') as f: f.write(html)

print(f"\nConcluido -- {applied} patches aplicados")
