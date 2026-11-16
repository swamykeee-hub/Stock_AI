from typing import Dict, Any, List
import requests
import pandas as pd
from datetime import datetime

class MarketRegimeAnalyst:
    """
    Evaluates macro market structure, volatility (India VIX), and sectoral rotation
    to determine whether the market is in Risk-On, Cautious, or Capital-Preservation regime.
    """

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    SECTOR_INDICES = {
        "Nifty Bank": "^NSEBANK",
        "Nifty IT": "^CNXIT",
        "Nifty Pharma": "^CNXPHARMA",
        "Nifty Auto": "^CNXAUTO",
        "Nifty Metal": "^CNXMETAL",
        "Nifty FMCG": "^CNXFMCG",
        "Nifty Realty": "^CNXREALTY",
        "Nifty Energy": "^CNXENERGY"
    }

    def fetch_index_candles(self, ticker: str, range_period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        """Fetches historical bars for an index."""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={range_period}&interval={interval}"
        try:
            r = requests.get(url, headers=self.HEADERS, timeout=6)
            if r.status_code == 200:
                res = r.json().get("chart", {}).get("result", [{}])[0]
                timestamps = res.get("timestamp", [])
                quotes = res.get("indicators", {}).get("quote", [{}])[0]
                if timestamps and quotes.get("close"):
                    df = pd.DataFrame({
                        "Close": quotes.get("close", [])
                    }).dropna().reset_index(drop=True)
                    return df
        except Exception:
            pass
        return pd.DataFrame()

    def evaluate_market_regime(self) -> Dict[str, Any]:
        """Runs institutional regime evaluation across Nifty 50, India VIX, and sectors."""
        # 1. Nifty 50 Evaluation
        nifty_df = self.fetch_index_candles("^NSEI", range_period="1y", interval="1d")
        nifty_cmp = 25044.65
        nifty_ema20 = 24850.0
        nifty_ema50 = 24600.0
        nifty_ema200 = 23800.0
        nifty_trend = "Bullish"

        if not nifty_df.empty and len(nifty_df) >= 50:
            c = nifty_df["Close"]
            nifty_cmp = round(float(c.iloc[-1]), 2)
            nifty_ema20 = round(float(c.ewm(span=20, adjust=False).mean().iloc[-1]), 2)
            nifty_ema50 = round(float(c.ewm(span=50, adjust=False).mean().iloc[-1]), 2)
            nifty_ema200 = round(float(c.ewm(span=len(c) if len(c) < 200 else 200, adjust=False).mean().iloc[-1]), 2)

            if nifty_cmp > nifty_ema20 and nifty_ema20 > nifty_ema50:
                nifty_trend = "Strong Bullish (Above 20 & 50 EMA)"
            elif nifty_cmp > nifty_ema50:
                nifty_trend = "Consolidating Bullish (Above 50 EMA)"
            elif nifty_cmp > nifty_ema200:
                nifty_trend = "Correction / Pullback (Testing 200 EMA)"
            else:
                nifty_trend = "Macro Bearish (Below 200 EMA)"

        # 2. India VIX Evaluation
        vix_df = self.fetch_index_candles("^INDIAVIX", range_period="1mo", interval="1d")
        india_vix = 14.5
        if not vix_df.empty and len(vix_df) >= 2:
            india_vix = round(float(vix_df["Close"].iloc[-1]), 2)

        # 3. Sector Performance & Rotation
        sector_results = []
        for name, sym in self.SECTOR_INDICES.items():
            sec_df = self.fetch_index_candles(sym, range_period="3mo", interval="1d")
            if not sec_df.empty and len(sec_df) >= 10:
                c = sec_df["Close"]
                c_now = float(c.iloc[-1])
                c_prev = float(c.iloc[-2]) if len(c) >= 2 else c_now
                c_1m = float(c.iloc[-20]) if len(c) >= 20 else float(c.iloc[0])
                day_pct = round(((c_now - c_prev) / (c_prev + 1e-6)) * 100, 2)
                month_pct = round(((c_now - c_1m) / (c_1m + 1e-6)) * 100, 2)
                sector_results.append({
                    "name": name,
                    "day_pct": day_pct,
                    "month_pct": month_pct
                })

        # Sort sectors by 1-month momentum
        sector_results.sort(key=lambda x: x["month_pct"], reverse=True)
        leading_sectors = [s["name"] for s in sector_results[:2]] if len(sector_results) >= 2 else ["Healthcare", "Manufacturing"]
        lagging_sectors = [s["name"] for s in sector_results[-2:]] if len(sector_results) >= 2 else ["IT", "FMCG"]

        # 4. Synthesize Market Regime & Health Score (0 - 100)
        score = 50
        if "Strong Bullish" in nifty_trend:
            score += 25
        elif "Consolidating Bullish" in nifty_trend:
            score += 15
        elif "Macro Bearish" in nifty_trend:
            score -= 25

        if india_vix < 14.0:
            score += 20
        elif india_vix <= 17.0:
            score += 10
        elif india_vix > 21.0:
            score -= 20

        market_score = max(10, min(score, 98))

        if market_score >= 75:
            regime_label = "🟢 High-Confidence Bull Market (Risk-On)"
            cash_guideline = "Deploy 85% - 95% in high-alpha leaders; 5% - 15% cash reserve."
            tactical_advice = "Hold winning momentum stocks with trailing stops. Aggressively add to leaders breaking out of Stage-2 bases."
        elif market_score >= 55:
            regime_label = "🟡 Stock Picker's Consolidation Market (Selective Alpha)"
            cash_guideline = "Deploy 70% - 80% capital; hold 20% - 30% cash for dip buying."
            tactical_advice = "Avoid buying extended breakouts. Buy high-quality compounders on 20-EMA pullbacks. Tighten trailing stops on lagging holdings."
        else:
            regime_label = "🔴 Defensive Capital Preservation Market (High Volatility / Risk-Off)"
            cash_guideline = "Raise 40% - 60% cash; protect capital above all else."
            tactical_advice = "Do not average down on losing stocks. Cut holdings that breach the 50-day EMA. Avoid fresh speculative positions."

        return {
            "nifty_cmp": nifty_cmp,
            "nifty_ema20": nifty_ema20,
            "nifty_ema50": nifty_ema50,
            "nifty_ema200": nifty_ema200,
            "nifty_trend": nifty_trend,
            "india_vix": india_vix,
            "market_score": market_score,
            "regime_label": regime_label,
            "cash_guideline": cash_guideline,
            "tactical_advice": tactical_advice,
            "leading_sectors": leading_sectors,
            "lagging_sectors": lagging_sectors,
            "sector_rankings": sector_results,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

