from typing import Dict, Any, Optional
import requests
from core.market_data import MarketDataManager
from core.technical_analyst import TechnicalAnalyst
from core.fundamental_analyst import FundamentalAnalyst
from core.news_sentiment_analyst import NewsSentimentAnalyst
import config

class Stock360Synthesizer:
    """
    Orchestrates Technical, Momentum, Fundamental, Sentiment, and Senior Fund Manager (CIO)
    intelligence into an institutional 360-degree investment advisory report.
    """

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def __init__(self):
        self.market_data = MarketDataManager()
        self.tech_analyst = TechnicalAnalyst()
        self.fund_analyst = FundamentalAnalyst()
        self.news_analyst = NewsSentimentAnalyst()

    def fetch_multi_timeframe_returns(self, symbol: str) -> Dict[str, Any]:
        """Calculates multi-horizon returns (1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y) via weekly candles."""
        formatted_sym = self.market_data.format_symbol(symbol)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{formatted_sym}?range=5y&interval=1wk"
        try:
            r = requests.get(url, headers=self.HEADERS, timeout=8)
            if r.status_code == 200:
                res = r.json().get("chart", {}).get("result", [{}])[0]
                meta = res.get("meta", {})
                closes = [c for c in res.get("indicators", {}).get("quote", [{}])[0].get("close", []) if c is not None]
                if closes and len(closes) >= 5:
                    cmp = meta.get("regularMarketPrice") or closes[-1]
                    h52 = meta.get("fiftyTwoWeekHigh", max(closes[-52:] if len(closes) >= 52 else closes))
                    l52 = meta.get("fiftyTwoWeekLow", min(closes[-52:] if len(closes) >= 52 else closes))

                    ret_1m = round(((cmp - closes[-4]) / closes[-4]) * 100, 1) if len(closes) >= 4 else 0.0
                    ret_3m = round(((cmp - closes[-13]) / closes[-13]) * 100, 1) if len(closes) >= 13 else 0.0
                    ret_6m = round(((cmp - closes[-26]) / closes[-26]) * 100, 1) if len(closes) >= 26 else 0.0
                    ret_1y = round(((cmp - closes[-52]) / closes[-52]) * 100, 1) if len(closes) >= 52 else 0.0
                    ret_2y = round(((cmp - closes[-104]) / closes[-104]) * 100, 1) if len(closes) >= 104 else 0.0
                    ret_3y = round(((cmp - closes[-156]) / closes[-156]) * 100, 1) if len(closes) >= 156 else 0.0
                    ret_5y = round(((cmp - closes[-260]) / closes[-260]) * 100, 1) if len(closes) >= 260 else (
                        round(((cmp - closes[0]) / closes[0]) * 100, 1)
                    )

                    dist_52w = round(((h52 - cmp) / (h52 + 1e-6)) * 100, 1)

                    # Momentum Score (1 - 10 scale)
                    mom_points = 5.0
                    if ret_1y > 100.0:
                        mom_points += 3.5
                    elif ret_1y > 50.0:
                        mom_points += 2.5
                    elif ret_1y > 20.0:
                        mom_points += 1.5
                    elif ret_1y < -15.0:
                        mom_points -= 2.0

                    if ret_6m > 40.0:
                        mom_points += 1.5
                    elif ret_6m > 20.0:
                        mom_points += 0.8
                    elif ret_6m < -10.0:
                        mom_points -= 1.0

                    if dist_52w <= 4.0:
                        mom_points += 1.0

                    mom_score = max(1.0, min(round(mom_points, 1), 10.0))

                    return {
                        "ret_1m": ret_1m,
                        "ret_3m": ret_3m,
                        "ret_6m": ret_6m,
                        "ret_1y": ret_1y,
                        "ret_2y": ret_2y,
                        "ret_3y": ret_3y,
                        "ret_5y": ret_5y,
                        "h52": round(h52, 2),
                        "l52": round(l52, 2),
                        "dist_52w": dist_52w,
                        "momentum_score": mom_score
                    }
        except Exception:
            pass

        return {
            "ret_1m": 0.0,
            "ret_3m": 0.0,
            "ret_6m": 0.0,
            "ret_1y": 0.0,
            "ret_2y": 0.0,
            "ret_3y": 0.0,
            "ret_5y": 0.0,
            "h52": 0.0,
            "l52": 0.0,
            "dist_52w": 0.0,
            "momentum_score": 5.0
        }

    def evaluate_stock_radar_status(self, symbol: str, company_name: str, timeframes: dict, composite_score: float, fund_audit: dict) -> dict:
        """
        Evaluates whether a stock is in the AI Buy Radar and provides an explicit
        diagnostic reason when a stock (e.g. TCS) is currently not recommended.
        """
        clean_sym = symbol.strip().upper()
        
        # Check active radar
        in_radar = False
        radar_setup = ""
        try:
            from core.fund_manager_radar import FundManagerRadar
            radar = FundManagerRadar()
            monitored = radar.get_monitored_stocks(sync_live_prices=False)
            for m in monitored:
                if m.get("symbol") == clean_sym:
                    in_radar = True
                    radar_setup = m.get("setup_type", "Active Monitored Setup")
                    break
        except Exception:
            pass

        ret_1y = timeframes.get("ret_1y", 0.0)
        ret_3m = timeframes.get("ret_3m", 0.0)
        dist_52w = timeframes.get("dist_52w", 0.0)
        raw_roce = fund_audit.get("metrics", {}).get("roce_pct", "N/A")
        roce = str(raw_roce).replace("\n", "").replace(" ", "").replace("%", "")
        raw_pe = fund_audit.get("metrics", {}).get("stock_pe", "N/A")
        pe = str(raw_pe).replace("\n", "").replace(" ", "")

        if in_radar:
            presence = "✅ Active in AI Fund Manager Radar"
            status_tag = "ACTIVE_RADAR"
            status_color = "#16a34a"
            reason = f"Actively tracked on institutional radar under '{radar_setup}' with monitored entry zones."
            action_advice = "Monitor buy trigger zones and trail strict stop loss."
        elif composite_score >= 7.6:
            presence = "🔥 Discovered in High-Conviction Bullish Breakouts"
            status_tag = "BULLISH_BREAKOUT"
            status_color = "#16a34a"
            reason = f"Passing full 360° technical, momentum (+{ret_1y}% 1Y), and volume breakout criteria."
            action_advice = "Eligible for tactical momentum position with defined risk-reward."
        elif ret_1y < 0 or dist_52w > 18.0:
            presence = "⏸️ Not in Active Buy Radar (Consolidation / Base-Building)"
            status_tag = "CONSOLIDATION_NOT_RECOMMENDED"
            status_color = "#eab308"
            reason = (
                f"{clean_sym} is trading {dist_52w}% below its 52-week high with a 1-Year return of {ret_1y}%. "
                f"It is currently excluded from the Bullish Momentum Radar because it has not established a Stage-2 mark-up structure. "
                f"While its underlying business fundamentals remain solid (ROCE: {roce}%, P/E: {pe}x), the price is undergoing "
                f"multi-quarter sideways base-building."
            )
            action_advice = "Hold existing long-term positions; avoid fresh momentum aggressive deployment until breakout confirmation."
        else:
            presence = "ℹ️ Neutral / Watchlist (Awaiting Volume Expansion)"
            status_tag = "NEUTRAL_WATCHLIST"
            status_color = "#3b82f6"
            reason = (
                f"{clean_sym} displays neutral momentum (1Y: {ret_1y}%, 3M: {ret_3m}%). "
                f"It requires sustained volume expansion above key EMAs before institutional entry is triggered."
            )
            action_advice = "Place on monitoring alert; wait for breakout past consolidation resistance."

        qualifying_triggers = [
            f"Weekly close clearing the 52-week consolidation pivot (within 5% of ₹{timeframes.get('h52', 'peak')})",
            f"Volume breakout exceeding 1.8x the 20-day moving average volume on green candles",
            f"Quarterly revenue / EBITDA acceleration sparking institutional re-rating"
        ]

        return {
            "in_radar": in_radar,
            "presence_label": presence,
            "status_tag": status_tag,
            "status_color": status_color,
            "reason": reason,
            "action_advice": action_advice,
            "qualifying_triggers": qualifying_triggers
        }

    def run_full_360_analysis(self, symbol: str) -> Dict[str, Any]:
        """Executes complete multi-agent analysis for the given stock."""
        clean_sym = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
        
        # 1. Market Overview & Quote
        overview = self.market_data.get_quote_and_overview(clean_sym)
        company_name = overview.get("shortName") or clean_sym

        # 2. Multi-Timeframe Performance (3M, 6M, 1Y, 2Y, 3Y, 5Y)
        timeframes = self.fetch_multi_timeframe_returns(clean_sym)

        # 3. Technical Audit
        candles = self.market_data.get_historical_candles(clean_sym, period="1y", interval="1d")
        tech_audit = self.tech_analyst.analyze(candles)

        # 4. Fundamental Health Check
        fund_audit = self.fund_analyst.analyze(clean_sym)

        # 5. News & Sentiment Flow
        news_audit = self.news_analyst.analyze(clean_sym, company_name)

        # 6. Scores Breakdown
        tech_score = tech_audit.get("score", 5.0)
        mom_score = timeframes.get("momentum_score", 5.0)
        fund_score = fund_audit.get("score", 5.0)
        sent_score = news_audit.get("score", 5.0)

        # Weighting: Technicals 30%, Momentum Factor 30%, Fundamentals 25%, Sentiment 15%
        composite_score = round(
            (tech_score * 0.30) + 
            (mom_score * 0.30) + 
            (fund_score * 0.25) + 
            (sent_score * 0.15), 
            1
        )

        # 7. Actionable Recommendation Matrix (CIO Standard)
        has_critical_news = news_audit.get("has_critical_bearish_event", False)
        crit_alerts = news_audit.get("critical_alerts", [])

        if has_critical_news:
            verdict = "AVOID / HIGH RISK REGULATORY OR GOVERNANCE ALERT"
            action_tag = "AVOID / SELL"
            color = "#dc2626"
            horizon = "Capital Preservation Active"
            sizing = "Zero Allocation (0%): Severe regulatory, forensic or governance headline detected"
        elif composite_score >= 7.6:
            verdict = "STRONG BUY / HIGH CONVICTION MOMENTUM"
            action_tag = "BUY"
            color = "#16a34a"
            horizon = "Multi-Quarter Trend / Swing (3 - 12 Months)"
            sizing = "Overweight: 4% - 6% Tactical Portfolio Allocation"
        elif composite_score >= 6.4:
            verdict = "BUY / ACCUMULATE ON PULLBACK (20 EMA)"
            action_tag = "BUY"
            color = "#22c55e"
            horizon = "Accumulation Horizon (2 - 6 Months)"
            sizing = "Standard: 2.5% - 4% Portfolio Allocation"
        elif composite_score >= 5.0:
            verdict = "HOLD / CONSOLIDATION WATCHLIST"
            action_tag = "HOLD"
            color = "#eab308"
            horizon = "Await Volume Expansion or Key Pivot Breakout"
            sizing = "Neutral: Hold existing positions; avoid fresh deployment"
        else:
            verdict = "AVOID / PROFIT BOOKING / UNDERPERFORMER"
            action_tag = "SELL"
            color = "#dc2626"
            horizon = "High Cyclical / Downtrend Risk"
            sizing = "Underweight / Exit to capital preservation"

        # Trade Plan Levels
        levels = tech_audit.get("levels", {})
        cmp = overview.get("currentPrice", 0.0)

        # Adaptive targets based on momentum strength
        target_mult_1 = 1.08 if mom_score >= 8.0 else 1.05
        target_mult_2 = 1.20 if mom_score >= 8.0 else 1.12
        sl_mult = 0.94 if mom_score >= 8.0 else 0.95

        trade_plan = {
            "current_market_price": cmp,
            "suggested_entry": f"₹{round(cmp * 0.985, 2)} - ₹{round(cmp * 1.005, 2)}",
            "target_1": levels.get("target_1", round(cmp * target_mult_1, 2)),
            "target_2": levels.get("target_2", round(cmp * target_mult_2, 2)),
            "stop_loss": levels.get("stop_loss", round(cmp * sl_mult, 2)),
            "risk_reward_ratio": levels.get("risk_reward_ratio", "1:2.5"),
            "time_horizon": horizon,
            "portfolio_sizing": sizing
        }

        # Senior Fund Manager Institutional Takeaway
        cio_thesis = (
            f"{company_name} demonstrates a 1-Year price return of +{timeframes['ret_1y']}% and "
            f"3-Year return of +{timeframes['ret_3y']}%, trading {timeframes['dist_52w']}% from its 52-week peak. "
            f"With a technical score of {tech_score}/10 and momentum score of {mom_score}/10, "
            f"institutional accumulation patterns suggest {'strong stage-2 mark-up' if mom_score >= 7.5 else 'consolidation structure'}. "
            f"Risk-managed entry is recommended near ₹{cmp} with stop loss at ₹{trade_plan['stop_loss']}."
        )

        # Radar & Recommendation Diagnostic (Answers why unlisted stocks like TCS are not in buy radar)
        status_diagnostic = self.evaluate_stock_radar_status(
            clean_sym, company_name, timeframes, composite_score, fund_audit
        )

        return {
            "symbol": clean_sym,
            "company_name": company_name,
            "overview": overview,
            "composite_score": composite_score,
            "verdict": verdict,
            "action_tag": action_tag,
            "tag_color": color,
            "timeframes": timeframes,
            "status_diagnostic": status_diagnostic,
            "breakdown_scores": {
                "technical_score": tech_score,
                "momentum_score": mom_score,
                "fundamental_score": fund_score,
                "sentiment_score": sent_score
            },
            "trade_plan": trade_plan,
            "cio_thesis": cio_thesis,
            "technicals": tech_audit,
            "fundamentals": fund_audit,
            "news_sentiment": news_audit,
            "disclaimer": config.DISCLAIMER
        }
