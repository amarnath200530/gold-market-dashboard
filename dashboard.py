import fredapi
import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timezone

FRED_API_KEY = os.environ.get("FRED_API_KEY")
fred = fredapi.Fred(api_key=FRED_API_KEY)

output_lines = []

def section(title):
    output_lines.append(f"\n## {title}\n")

def log(text):
    output_lines.append(text)

# ============ REAL INTEREST RATES ============
section("US Real Interest Rates")
real_10y = fred.get_series('DFII10').dropna()
real_10y_chg = real_10y.iloc[-1] - real_10y.iloc[-22]
log(f"- **10Y TIPS Real Yield:** {real_10y.iloc[-1]:.2f}% (as of {real_10y.index[-1].date()})")
log(f"- **1-Month Change:** {real_10y_chg:.2f} pts")

# ============ INFLATION EXPECTATIONS ============
section("Inflation Expectations")
breakeven_10y = fred.get_series('T10YIE').dropna()
breakeven_5y = fred.get_series('T5YIE').dropna()
breakeven_10y_chg = breakeven_10y.iloc[-1] - breakeven_10y.iloc[-22]
log(f"- **10Y Breakeven Inflation:** {breakeven_10y.iloc[-1]:.2f}%")
log(f"- **5Y Breakeven Inflation:** {breakeven_5y.iloc[-1]:.2f}%")

# ============ DOLLAR STRENGTH (DXY) ============
section("US Dollar Index (DXY)")
dxy = yf.Ticker("DX-Y.NYB").history(period="1mo")
dxy_chg = (dxy['Close'].iloc[-1] / dxy['Close'].iloc[0] - 1) * 100
log(f"- **DXY Latest:** {dxy['Close'].iloc[-1]:.2f}")
log(f"- **1-Month Change:** {dxy_chg:.2f}%")

# ============ SAFE-HAVEN PROXY ============
section("Safe-Haven Demand Proxy (VIX & Gold)")
vix = yf.Ticker("^VIX").history(period="5d")
vix_now = vix['Close'].iloc[-1]
log(f"- **VIX Latest:** {vix_now:.2f}")

gold = yf.Ticker("GC=F").history(period="1mo")
gold_price = gold['Close'].iloc[-1]
gold_chg = (gold['Close'].iloc[-1] / gold['Close'].iloc[0] - 1) * 100
log(f"- **Gold Spot (Futures):** ${gold_price:.2f}")
log(f"- **1-Month Change:** {gold_chg:.2f}%")

# ============ FED POLICY ============
section("Fed Policy Expectations")
fed_funds = fred.get_series('DFF').dropna()
log(f"- **Current Effective Fed Funds Rate:** {fed_funds.iloc[-1]:.2f}%")
log("- Check CME FedWatch for rate cut/hike probabilities: [link](https://www.cmegroup.com/markets/interest-rates/cme-fedwatch-tool.html)")

# ============ FOMC ============
section("Next FOMC Meeting")
log("Check calendar: [Federal Reserve FOMC Calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm)")

# ============ CPI ============
section("Latest CPI Data")
cpi = fred.get_series('CPIAUCSL').dropna()
cpi_yoy = (cpi.iloc[-1] / cpi.iloc[-13] - 1) * 100
log(f"- **CPI Index Latest:** {cpi.iloc[-1]:.2f}")
log(f"- **YoY CPI Inflation:** {cpi_yoy:.2f}%")
log("- Release calendar: [BLS CPI Schedule](https://www.bls.gov/schedule/news_release/cpi.htm)")

# ============ CENTRAL BANK BUYING ============
section("Central Bank Gold Demand")
log("No free real-time API available. Check manually:")
log("- [World Gold Council](https://www.gold.org/goldhub/data/gold-demand-by-country)")
log("- [IMF IFS Official Reserves](https://data.imf.org)")

# ============ ETF FLOWS / COT ============
section("ETF Flows & COT Positioning")
log("- [SPDR Gold Shares (GLD) Holdings](https://www.spdrgoldshares.com)")
log("- [CFTC COT Report](https://www.cftc.gov/dea/futures/other_lf.htm) (updated weekly, Fridays 3:30pm ET)")

# ============ GOLD BIAS SCORE ============
section("Gold Bias Score (rule-based signal, NOT a forecast)")
score = 0
rows = []

if real_10y_chg < -0.10:   s = 1;  note = "Real yields falling"
elif real_10y_chg > 0.10:  s = -1; note = "Real yields rising"
else:                      s = 0;  note = "Real yields flat"
score += s; rows.append(("Real yields (1M chg)", f"{real_10y_chg:+.2f}", s, note))

if breakeven_10y_chg > 0.10:    s = 1;  note = "Inflation expectations rising"
elif breakeven_10y_chg < -0.10: s = -1; note = "Inflation expectations falling"
else:                           s = 0;  note = "Inflation expectations stable"
score += s; rows.append(("10Y breakeven (1M chg)", f"{breakeven_10y_chg:+.2f}", s, note))

if dxy_chg < -1:     s = 1;  note = "Dollar weakening"
elif dxy_chg > 1:    s = -1; note = "Dollar strengthening"
else:                s = 0;  note = "Dollar flat"
score += s; rows.append(("DXY (1M % chg)", f"{dxy_chg:+.2f}%", s, note))

if vix_now > 25:     s = 1;  note = "Elevated fear - safe-haven demand"
else:                s = 0;  note = "No significant fear"
score += s; rows.append(("VIX", f"{vix_now:.2f}", s, note))

log("| Factor | Value | Score | Reading |")
log("|---|---|---|---|")
for name, val, s, note in rows:
    log(f"| {name} | {val} | {s:+d} | {note} |")

if score >= 2:    verdict = "BULLISH pressure on gold"
elif score <= -2: verdict = "BEARISH pressure on gold"
else:             verdict = "NEUTRAL / mixed signals"
log(f"\n**Total score: {score:+d} -> {verdict}**")
log("\n_Note: Excludes central bank buying, COT and geopolitics (no live data). Not financial advice._")

# ============ WRITE MARKDOWN REPORT ============
now_utc = datetime.now(timezone.utc)
report = f"# Gold Market Dashboard\n\n_Last updated: {now_utc} UTC_\n" + "\n".join(output_lines)

os.makedirs("output", exist_ok=True)
with open("output/latest_report.md", "w") as f:
    f.write(report)

# ============ APPEND TO HISTORICAL CSV ============
history_path = "output/history.csv"

row = {
    "timestamp_utc": now_utc.isoformat(),
    "real_yield_10y": real_10y.iloc[-1],
    "real_yield_10y_1m_chg": real_10y_chg,
    "breakeven_10y": breakeven_10y.iloc[-1],
    "breakeven_5y": breakeven_5y.iloc[-1],
    "breakeven_10y_1m_chg": breakeven_10y_chg,
    "dxy": dxy['Close'].iloc[-1],
    "dxy_1m_chg_pct": dxy_chg,
    "vix": vix_now,
    "gold_price": gold_price,
    "gold_1m_chg_pct": gold_chg,
    "fed_funds_rate": fed_funds.iloc[-1],
    "cpi_yoy_pct": cpi_yoy,
    "bias_score": score,
    "bias_verdict": verdict,
}

df_row = pd.DataFrame([row])

if os.path.exists(history_path):
    df_row.to_csv(history_path, mode='a', header=False, index=False)
else:
    df_row.to_csv(history_path, mode='w', header=True, index=False)

print("Report generated and history logged successfully.")


import json

signal = {
    "timestamp_utc": now_utc.isoformat(),
    "score": score,
    "verdict": verdict,
    "real_yield_10y": float(real_10y.iloc[-1]),
    "real_yield_10y_1m_chg": float(real_10y_chg),
    "dxy": float(dxy['Close'].iloc[-1]),
    "dxy_1m_chg_pct": float(dxy_chg),
    "vix": float(vix_now),
    "gold_price": float(gold_price),
}

with open("output/latest_signal.json", "w") as f:
    json.dump(signal, f)

import requests
import csv
from datetime import datetime, timezone

def fetch_news_calendar():
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        events = resp.json()
    except Exception as e:
        print(f"News calendar fetch failed: {e}")
        return

    rows = []
    for ev in events:
        impact = ev.get("impact", "")
        currency = ev.get("country", "")
        if impact != "High" or currency != "USD":
            continue  # Only high-impact USD events matter for XAUUSD

        # ForexFactory feed gives date/time in various formats; normalize to UTC
        try:
            dt_str = ev.get("date")  # e.g. "2026-09-28T12:30:00-04:00"
            dt = datetime.fromisoformat(dt_str)
            dt_utc = dt.astimezone(timezone.utc)
        except Exception:
            continue

        rows.append({
            "date_utc": dt_utc.strftime("%Y.%m.%d"),
            "time_utc": dt_utc.strftime("%H:%M"),
            "event": ev.get("title", "Unknown"),
            "impact": impact,
            "currency": currency
        })

    with open("output/news_calendar.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date_utc","time_utc","event","impact","currency"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"News calendar updated: {len(rows)} high-impact USD events this week.")

fetch_news_calendar()
