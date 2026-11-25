from typing import Dict, Any
import config
from core.market_data import MarketDataManager
from core.technical_analyst import TechnicalAnalyst
from core.fundamental_analyst import FundamentalAnalyst, parse_float_safe
from core.news_sentiment_analyst import NewsSentimentAnalyst
from core.momentum_screener import MomentumScreener


class Stock360Synthesizer:
    """
    Orchestrates Consolidated Fundamentals (Quality, Quarterly Inflection, GARP, CWIP, Smart Money),
    Multi-Horizon Weekly Momentum & RS vs Nifty 50, Daily Technicals, and News Catalysts into
    an institutional 360-degree Long-Term Compounder & Tactical advisory report.
    """

    def __init__(self):
        self.market_data = MarketDataManager()
        self.tech_analyst = TechnicalAnalyst()
        self.fund_analyst = FundamentalAnalyst()
        self.news_analyst = NewsSentimentAnalyst()
        self.momentum_screener = MomentumScreener()

    def fetch_multi_timeframe_returns(self, symbol: str) -> Dict[str, Any]:
        """Reuses MomentumScreener's weekly engine for multi-horizon returns, 40W EMA, and RS vs Nifty."""
        clean_sym = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
        nifty = self.momentum_screener.fetch_nifty_benchmark_returns()
        res = self.momentum_screener.fetch_stock_multi_timeframe({"symbol": clean_sym}, nifty_bench=nifty)
        if not res:
            return {
                "ret_1m": 0.0, "ret_3m": 0.0, "ret_6m": 0.0,
                "ret_1y": 0.0, "ret_2y": 0.0, "ret_3y": 0.0, "ret_5y": 0.0,
                "h52": 0.0, "l52": 0.0, "dist_52w": 0.0,
                "rs_vs_nifty_6m": 0.0, "ema_40w": 0.0, "is_vcp_tight": False,
                "momentum_score": 5.0,
            }

        ret_1y = res.get("ret_1y", 0.0)
        ret_6m = res.get("ret_6m", 0.0)
        dist_52w = res.get("distance_from_52w_high", 0.0)
        rs_6m = res.get("rs_vs_nifty_6m", 0.0)

        mom_points = 5.0
        if ret_1y > 90.0:
            mom_points += 3.2
        elif ret_1y > 45.0:
            mom_points += 2.3
        elif ret_1y > 18.0:
            mom_points += 1.4
        elif ret_1y < -15.0:
            mom_points -= 1.8

        if rs_6m > 15.0:
            mom_points += 1.2
        elif rs_6m > 5.0:
            mom_points += 0.6
        elif rs_6m < -15.0:
            mom_points -= 1.0

        if dist_52w <= 5.0 and res.get("cmp", 0) > res.get("ema_40w", 0):
            mom_points += 1.0
        if res.get("is_vcp_tight"):
            mom_points += 0.5

        res["h52"] = res.get("fifty_two_week_high", 0.0)
        res["l52"] = res.get("fifty_two_week_low", 0.0)
        res["dist_52w"] = dist_52w
        res["momentum_score"] = max(1.0, min(round(mom_points, 1), 10.0))
        return res

    def evaluate_stock_radar_status(
        self, symbol: str, company_name: str, timeframes: dict, composite_score: float, fund_audit: dict
    ) -> dict:
        """Evaluates AI Buy Radar presence and explains why any stock qualifies or awaits breakout."""
        clean_sym = symbol.strip().upper()
        in_radar = False
        radar_setup = ""
        try:
            from core.fund_manager_radar import FundManagerRadar
            radar = FundManagerRadar()
            for m in radar.get_monitored_stocks(sync_live_prices=False):
                if m.get("symbol") == clean_sym:
                    in_radar = True
                    radar_setup = m.get("setup_type", "Active Monitored Setup")
                    break
        except Exception:
            pass

        ret_1y = timeframes.get("ret_1y", 0.0)
        ret_3m = timeframes.get("ret_3m", 0.0)
        dist_52w = timeframes.get("dist_52w", 0.0)
        metrics = fund_audit.get("metrics", {})
        roce = metrics.get("roce_pct", "N/A")
        pe = metrics.get("stock_pe", "N/A")
        inf = fund_audit.get("inflection", {})
        opm_exp = inf.get("opm_expansion_bps")
        pat_yoy = inf.get("qtr_pat_yoy_pct")

        if in_radar:
            presence = "✅ Active in AI Fund Manager Radar"
            status_tag = "ACTIVE_RADAR"
            status_color = "#16a34a"
            reason = f"Actively tracked on institutional radar under '{radar_setup}' with monitored entry zones."
            action_advice = "Monitor pullback buy triggers and hold above structural support."
        elif (opm_exp or 0) >= 150 and (pat_yoy or 0) >= 20.0 and composite_score >= 7.0:
            presence = "🚀 Discovered: Multibagger Inflection Candidate (Laurus-Type)"
            status_tag = "BULLISH_INFLECTION"
            status_color = "#16a34a"
            reason = (
                f"Exhibits sharp operating-leverage inflection (OPM {opm_exp:+.0f} bps, Qtr PAT {pat_yoy:+.1f}% YoY) "
                f"with {ret_1y:+.1f}% 1Y price trend and ROCE {roce}%."
            )
            action_advice = "Strong candidate for staggered long-term accumulation on 20-EMA dips."
        elif composite_score >= 7.3:
            presence = "🔥 Discovered in High-Conviction Compounders"
            status_tag = "BULLISH_BREAKOUT"
            status_color = "#16a34a"
            reason = f"Passing full 360° fundamental quality, Stage-2 structure ({ret_1y:+.1f}% 1Y), and RS vs Nifty 50."
            action_advice = "Eligible for long-term portfolio deployment with defined support floor."
        elif ret_1y < 0 or dist_52w > 18.0:
            presence = "⏸️ Not in Active Buy Radar (Consolidation / Base-Building)"
            status_tag = "CONSOLIDATION_NOT_RECOMMENDED"
            status_color = "#eab308"
            reason = (
                f"{clean_sym} sits {dist_52w}% below its 52W peak (1Y Return: {ret_1y:+.1f}%). "
                f"While fundamentals show ROCE {roce}% & P/E {pe}x, price has not yet confirmed a Stage-2 weekly breakout."
            )
            action_advice = "Accumulate selectively only if quarterly OPM/PAT accelerates; await 40-Week EMA reclaim."
        else:
            presence = "ℹ️ Neutral / Watchlist (Awaiting Earnings or Volume Catalyst)"
            status_tag = "NEUTRAL_WATCHLIST"
            status_color = "#3b82f6"
            reason = f"{clean_sym} displays moderate momentum (1Y: {ret_1y:+.1f}%, 3M: {ret_3m:+.1f}%)."
            action_advice = "Track next quarterly OPM & PAT growth alongside weekly volume expansion."

        qualifying_triggers = [
            f"Weekly close clearing consolidation pivot (within 8% of ₹{timeframes.get('h52', 'peak')}) above rising 40-Week EMA",
            "Weekly volume surge >= 1.5x average signaling institutional accumulation",
            "Quarterly OPM % expansion (+150 bps YoY) with PAT growth >= +20% YoY",
        ]

        return {
            "in_radar": in_radar,
            "presence_label": presence,
            "status_tag": status_tag,
            "status_color": status_color,
            "reason": reason,
            "action_advice": action_advice,
            "qualifying_triggers": qualifying_triggers,
        }

    def run_full_360_analysis(self, symbol: str) -> Dict[str, Any]:
        """Executes complete multi-agent Long-Term Compounder & Tactical analysis for any NSE stock."""
        clean_sym = symbol.strip().upper().replace(".NS", "").replace(".BO", "")

        overview = self.market_data.get_quote_and_overview(clean_sym)
        company_name = overview.get("shortName") or clean_sym
        timeframes = self.fetch_multi_timeframe_returns(clean_sym)
        candles = self.market_data.get_historical_candles(clean_sym, period="1y", interval="1d")
        tech_audit = self.tech_analyst.analyze(candles)
        fund_audit = self.fund_analyst.analyze(clean_sym)
        news_audit = self.news_analyst.analyze(clean_sym, company_name)

        tech_score = float(tech_audit.get("score", 5.0))
        mom_score = float(timeframes.get("momentum_score", 5.0))
        fund_score = float(fund_audit.get("score", 5.0))
        sent_score = float(news_audit.get("score", 5.0))

        # Dual Scoring Lenses:
        # 1. Long-Term Compounder Score (Primary CIO Score): 55% Consolidated Fund/Inflection, 25% Weekly RS/Mom, 15% Tech, 5% News
        long_term_score = round(
            (fund_score * 0.55) + (mom_score * 0.25) + (tech_score * 0.15) + (sent_score * 0.05),
            1,
        )
        # 2. Tactical Swing Score: 35% Tech, 35% Momentum, 20% Fund, 10% News
        swing_score = round(
            (tech_score * 0.35) + (mom_score * 0.35) + (fund_score * 0.20) + (sent_score * 0.10),
            1,
        )
        composite_score = long_term_score

        has_critical_news = news_audit.get("has_critical_bearish_event", False)
        if has_critical_news:
            verdict = "AVOID / HIGH RISK GOVERNANCE OR REGULATORY ALERT"
            action_tag = "AVOID / SELL"
            color = "#dc2626"
            horizon = "Capital Preservation Active"
            sizing = "Zero Allocation (0%): Verified governance/regulatory risk headline detected"
        elif long_term_score >= 7.5:
            verdict = "STRONG BUY / MULTIBAGGER COMPOUNDER"
            action_tag = "BUY"
            color = "#16a34a"
            horizon = "Long-Term Structural Compounder (2 - 5 Years)"
            sizing = "Overweight: 4% - 6% Core Portfolio Allocation"
        elif long_term_score >= 6.4:
            verdict = "BUY / ACCUMULATE ON 20-EMA DIPS"
            action_tag = "BUY"
            color = "#22c55e"
            horizon = "Medium-to-Long Term Accumulation (1 - 3 Years)"
            sizing = "Standard: 2.5% - 4% Portfolio Allocation"
        elif long_term_score >= 5.0:
            verdict = "HOLD / CONSOLIDATION WATCHLIST"
            action_tag = "HOLD"
            color = "#eab308"
            horizon = "Await OPM Expansion or Weekly Breakout"
            sizing = "Neutral: Hold existing quality positions; avoid aggressive fresh adds"
        else:
            verdict = "AVOID / WEAK FUNDAMENTALS OR DOWNTREND"
            action_tag = "SELL"
            color = "#dc2626"
            horizon = "Structural / Fundamental Underperformer"
            sizing = "Underweight / Reallocate capital"

        levels = tech_audit.get("levels", {})
        cmp = overview.get("currentPrice", 0.0)
        metrics = fund_audit.get("metrics", {})
        inflection = fund_audit.get("inflection", {})
        bal = fund_audit.get("balance_inst", {})

        trade_plan = {
            "current_market_price": cmp,
            "suggested_entry": f"₹{round(cmp * 0.985, 2)} - ₹{round(cmp * 1.005, 2)}",
            "target_1": round(max(levels.get("target_1", cmp * 1.10), cmp * 1.12), 2),
            "target_2": round(max(levels.get("target_2", cmp * 1.25), cmp * 1.30), 2),
            "stop_loss": round(min(levels.get("stop_loss", cmp * 0.93), tech_audit.get("ema_50", cmp * 0.94)), 2),
            "risk_reward_ratio": levels.get("risk_reward_ratio", "1:2.2"),
            "time_horizon": horizon,
            "portfolio_sizing": sizing,
        }

        opm_bps = inflection.get("opm_expansion_bps")
        pat_yoy = inflection.get("qtr_pat_yoy_pct")
        opm_note = f"OPM YoY: {opm_bps:+.0f} bps, Qtr PAT YoY: {pat_yoy:+.1f}%" if (opm_bps is not None and pat_yoy is not None) else ""
        cio_thesis = (
            f"{company_name} shows 1Y return of {timeframes['ret_1y']:+.1f}% (3Y: {timeframes['ret_3y']:+.1f}%), "
            f"trading {timeframes['dist_52w']}% off its 52W high. ROCE: {metrics.get('roce_pct', 'N/A')}%, "
            f"D/E: {metrics.get('debt_to_equity', 'N/A')}, PEG: {metrics.get('peg_ratio', 'N/A')}, "
            f"FII+DII 4Q Flow: {bal.get('inst_4q_delta_pct', 0.0):+.1f}%. {opm_note}"
        ).strip()

        status_diagnostic = self.evaluate_stock_radar_status(
            clean_sym, company_name, timeframes, composite_score, fund_audit
        )

        return {
            "symbol": clean_sym,
            "company_name": company_name,
            "overview": overview,
            "composite_score": composite_score,
            "long_term_score": long_term_score,
            "swing_score": swing_score,
            "verdict": verdict,
            "action_tag": action_tag,
            "tag_color": color,
            "timeframes": timeframes,
            "status_diagnostic": status_diagnostic,
            "breakdown_scores": {
                "long_term_score": long_term_score,
                "swing_score": swing_score,
                "technical_score": tech_score,
                "momentum_score": mom_score,
                "fundamental_score": fund_score,
                "quality_score": fund_audit.get("quality_score", fund_score),
                "inflection_score": fund_audit.get("inflection_score", 5.0),
                "sentiment_score": sent_score,
            },
            "trade_plan": trade_plan,
            "cio_thesis": cio_thesis,
            "technicals": tech_audit,
            "fundamentals": fund_audit,
            "news_sentiment": news_audit,
            "disclaimer": config.DISCLAIMER,
        }
