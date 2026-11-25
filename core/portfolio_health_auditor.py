from typing import Dict, Any, List, Optional
import math
import pandas as pd
from core.market_data import MarketDataManager
from core.technical_analyst import TechnicalAnalyst
from core.fundamental_analyst import FundamentalAnalyst, parse_float_safe
from core.news_sentiment_analyst import NewsSentimentAnalyst


class PortfolioHealthAuditor:
    """
    Institutional Chief Investment Officer (CIO) for Personal Portfolios.
    Supports two distinct portfolio management horizons:
    - "long_term" (default): Protects 3-5 year multibagger compounding by anchoring exits to the 200-EMA,
      catastrophe floors (-15%), fundamental thesis checks (OPM/PAT trajectory), and verified governance alerts
      instead of choking winners on 8% noise shakeouts or RSI spikes.
    - "swing": Tactical position protection anchored to 20/50-EMA, -8% stops, and partial profit booking.
    """

    def __init__(self):
        self.market_data = MarketDataManager()
        self.tech_analyst = TechnicalAnalyst()
        self.fund_analyst = FundamentalAnalyst()
        self.news_analyst = NewsSentimentAnalyst()

    def audit_holding(
        self,
        symbol: str,
        qty: int,
        buy_price: float,
        cached_cmp: Optional[float] = None,
        cached_change_pct: Optional[float] = None,
        strategy_mode: str = "long_term",
    ) -> Dict[str, Any]:
        """Runs comprehensive 360-degree audit on a single portfolio holding."""
        clean_sym = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
        mode = "swing" if str(strategy_mode).lower() == "swing" else "long_term"

        candles = self.market_data.get_historical_candles(clean_sym, period="1y", interval="1d")
        cmp = cached_cmp or buy_price

        if not candles.empty and len(candles) >= 20:
            last_close = float(candles["Close"].iloc[-1])
            if cached_cmp is None or cached_cmp <= 0:
                cmp = last_close
            tech_audit = self.tech_analyst.analyze(candles)
        else:
            tech_audit = {
                "score": 5.0,
                "rsi": 50.0,
                "ema_20": cmp,
                "ema_50": cmp * 0.98,
                "ema_200": cmp * 0.95,
                "volume_ratio": 1.0,
                "atr": cmp * 0.02,
                "bullish_signals": [],
                "bearish_signals": [],
            }

        rsi = float(tech_audit.get("rsi", 50.0))
        ema_20 = float(tech_audit.get("ema_20", cmp))
        ema_50 = float(tech_audit.get("ema_50", cmp))
        ema_200 = float(tech_audit.get("ema_200", cmp))
        atr = float(tech_audit.get("atr", cmp * 0.02))
        vol_ratio = float(tech_audit.get("volume_ratio", 1.0))

        highest_price = cmp
        if not candles.empty:
            highest_price = max(cmp, float(candles["High"].tail(60).max()))

        invested = qty * buy_price
        current_val = qty * cmp
        pnl = current_val - invested
        pnl_pct = ((cmp - buy_price) / (buy_price + 1e-6)) * 100 if buy_price > 0 else 0.0

        # Consolidated Fundamental Check (detects real business thesis breaks)
        fund_audit = self.fund_analyst.analyze(clean_sym)
        fund_score = float(fund_audit.get("score", 5.0))
        inflection = fund_audit.get("inflection", {})
        opm_exp_bps = inflection.get("opm_expansion_bps")
        qtr_pat_yoy = inflection.get("qtr_pat_yoy_pct")
        roce_num = parse_float_safe(fund_audit.get("metrics", {}).get("roce_pct"))
        fundamental_broken = (
            (opm_exp_bps is not None and opm_exp_bps <= -350)
            and (qtr_pat_yoy is not None and qtr_pat_yoy <= -25.0)
        )

        # News & Governance Catalyst Audit (full company name resolved internally)
        news_audit = self.news_analyst.analyze(clean_sym)
        has_critical_news = news_audit.get("has_critical_bearish_event", False)
        crit_alerts = news_audit.get("critical_alerts", [])
        top_bearish_news = news_audit.get("top_bearish_catalysts", [])

        # Dynamic Trailing Stop-Loss by Strategy Mode
        if mode == "long_term":
            if pnl_pct >= 50.0:
                trailing_sl = max(ema_200 * 0.98, highest_price * 0.85, buy_price * 1.15)
                sl_type = "Wealth Compounder Trail (200-EMA / Peak-15%)"
            elif pnl_pct >= 15.0:
                trailing_sl = max(ema_200 * 0.96, buy_price * 1.00)
                sl_type = "Long-Term Capital Protection (Breakeven / 200-EMA)"
            elif pnl_pct >= 0:
                trailing_sl = min(buy_price * 0.88, ema_200 * 0.95)
                sl_type = "Long-Term Structural Support (200-EMA)"
            else:
                trailing_sl = round(min(buy_price * 0.85, ema_200 * 0.93), 2)
                sl_type = "Catastrophe Risk Floor (-15% / Below 200-EMA)"
        else:
            if pnl_pct >= 35.0:
                trailing_sl = max(ema_20 * 0.985, highest_price * 0.91, buy_price * 1.15)
                sl_type = "Aggressive Swing Trail (20-EMA / Peak-9%)"
            elif pnl_pct >= 15.0:
                trailing_sl = max(ema_50 * 0.98, buy_price * 1.02)
                sl_type = "Capital Protected Swing Trail (50-EMA)"
            elif pnl_pct >= 0:
                trailing_sl = min(buy_price * 0.92, ema_50 * 0.97)
                sl_type = "Standard Swing Stop (-8%)"
            else:
                trailing_sl = round(buy_price * 0.92, 2)
                sl_type = "Strict Swing Risk Boundary (-8% Hard Stop)"

        trailing_sl = round(trailing_sl, 2)
        dist_to_sl_pct = round(((cmp - trailing_sl) / (cmp + 1e-6)) * 100, 1)

        # CIO Decision Matrix
        action_code = "STRONG_HOLD"
        action_badge = "🟢 STRONG HOLD"
        action_color = "#10b981"
        rationale = ""
        suggested_action_detail = ""

        if has_critical_news:
            action_code = "EMERGENCY_SELL"
            action_badge = "🔴 EMERGENCY EXIT (GOVERNANCE ALERT)"
            action_color = "#ef4444"
            headline_cue = crit_alerts[0] if crit_alerts else "Critical governance or regulatory sanction detected."
            rationale = (
                f"Verified severe corporate risk detected: '{headline_cue}'. "
                "Capital preservation takes precedence over all technicals."
            )
            suggested_action_detail = f"Review immediately and exit {qty} shares at CMP ₹{cmp} if thesis is impaired."

        elif mode == "long_term" and fundamental_broken and cmp < ema_200:
            action_code = "TREND_BREAKDOWN_SELL"
            action_badge = "🔴 THESIS BREAK (FUNDAMENTALS + 200-EMA)"
            action_color = "#ef4444"
            rationale = (
                f"Earnings thesis broke ({clean_sym}: OPM {opm_exp_bps:+.0f} bps, Qtr PAT {qtr_pat_yoy:+.1f}% YoY) "
                f"and price dropped below 200-EMA (₹{ema_200:.2f}). Reallocate capital to stronger compounders."
            )
            suggested_action_detail = f"Exit {qty} shares around ₹{cmp} due to fundamental & structural breakdown."

        elif cmp < trailing_sl:
            if pnl_pct > 0:
                action_code = "EXIT_TRAILING_SL"
                action_badge = "🔴 TRAILING STOP HIT (LOCK PROFIT)"
                action_color = "#f97316"
                rationale = (
                    f"Price (₹{cmp}) closed below your {mode.replace('_', ' ')} trailing floor of ₹{trailing_sl}. "
                    f"Lock in accumulated +{pnl_pct:.1f}% gains."
                )
                suggested_action_detail = f"Sell {qty} shares to protect +₹{pnl:,.2f} gain."
            else:
                action_code = "CUT_LOSS"
                action_badge = "🔴 RISK FLOOR BREACHED (CUT LOSS)"
                action_color = "#dc2626"
                rationale = (
                    f"Price (₹{cmp}) breached the {sl_type} threshold (₹{trailing_sl}). "
                    "Protect core portfolio equity against deeper capital drawdown."
                )
                suggested_action_detail = f"Exit {qty} shares to cap loss at -₹{abs(pnl):,.2f}."

        elif mode == "swing" and cmp < ema_50 and vol_ratio >= 1.4:
            action_code = "TREND_BREAKDOWN_SELL"
            action_badge = "🔴 TREND BREAKDOWN (50-EMA LOST)"
            action_color = "#ef4444"
            rationale = (
                f"{clean_sym} broke below its 50-day EMA (₹{ema_50:.2f}) on heavy volume ({vol_ratio:.1f}x avg)."
            )
            suggested_action_detail = f"Exit {qty} shares at ₹{cmp} or tighten stop to ₹{trailing_sl}."

        elif mode == "swing" and pnl_pct >= 40.0 and rsi >= 75.0:
            trim_qty = max(1, math.ceil(qty * 0.35))
            action_code = "BOOK_PARTIAL_PROFIT"
            action_badge = "🟠 BOOK 35% PROFIT (OVERBOUGHT)"
            action_color = "#f59e0b"
            rationale = (
                f"Swing gain +{pnl_pct:.1f}% with overbought RSI ({rsi:.1f}). Book 35% and trail remainder."
            )
            suggested_action_detail = f"Book profit on {trim_qty} shares at ₹{cmp}; trail {qty - trim_qty} shares."

        elif mode == "swing" and pnl_pct >= 25.0 and cmp < ema_20:
            trim_qty = max(1, math.ceil(qty * 0.25))
            action_code = "TRIM_ON_WEAKNESS"
            action_badge = "🟡 TRIM 25% (20-EMA SLIP)"
            action_color = "#eab308"
            rationale = f"Up +{pnl_pct:.1f}%, dipped under 20-EMA (₹{ema_20:.2f}). De-risk 25%."
            suggested_action_detail = f"Trim {trim_qty} shares; trail balance at ₹{trailing_sl}."

        elif mode == "long_term" and cmp >= ema_200 and fund_score >= 6.8:
            if abs(cmp - ema_20) / (ema_20 + 1e-6) <= 0.025 and 45 <= rsi <= 65:
                action_code = "ACCUMULATE_ON_DIP"
                action_badge = "🟢 PYRAMID ON DIP (COMPOUNDER)"
                action_color = "#22c55e"
                rationale = (
                    f"{clean_sym} holds strong fundamentals (Score {fund_score}/10, ROCE {roce_num or 'N/A'}%) "
                    f"while testing healthy 20-EMA support (₹{ema_20:.2f}). Ideal zone to pyramid long-term allocation."
                )
                suggested_action_detail = f"Hold {qty} shares; add 15–20% more on strength above ₹{ema_20:.2f}."
            else:
                action_code = "STRONG_HOLD"
                action_badge = "🟢 LET COMPOUNDER RIDE"
                action_color = "#10b981"
                inf_note = (
                    f" | OPM {opm_exp_bps:+.0f} bps, Qtr PAT {qtr_pat_yoy:+.1f}% YoY"
                    if (opm_exp_bps is not None and qtr_pat_yoy is not None)
                    else ""
                )
                rationale = (
                    f"Long-term wealth posture intact above 200-EMA (₹{ema_200:.2f}) with Fundamental Score "
                    f"{fund_score}/10{inf_note}. Ignore minor short-term dips and allow compounding."
                )
                suggested_action_detail = f"Hold all {qty} shares. Structural floor active at ₹{trailing_sl}."

        elif cmp >= ema_50 and abs(cmp - ema_20) / (ema_20 + 1e-6) <= 0.02 and pnl_pct > 0 and (45 <= rsi <= 65):
            action_code = "ACCUMULATE_ON_DIP"
            action_badge = "🟢 ACCUMULATE ON DIP (20-EMA)"
            action_color = "#22c55e"
            rationale = (
                f"Testing upward-trending 20-EMA (₹{ema_20:.2f}) with healthy RSI ({rsi:.1f})."
            )
            suggested_action_detail = f"Hold {qty} shares; candidate to add 15–20% with stop at ₹{trailing_sl}."

        else:
            action_code = "STRONG_HOLD"
            action_badge = "🟢 STRONG HOLD (TREND INTACT)"
            action_color = "#10b981"
            trend_str = "Above 20 & 200 EMA" if (cmp > ema_20 and cmp > ema_200) else "Consolidating above floor"
            rationale = (
                f"{clean_sym} maintains constructive structure ({trend_str}, Fund Score: {fund_score}/10). "
                f"Current P&L: {pnl_pct:+.1f}%. Keep protective floor at ₹{trailing_sl}."
            )
            suggested_action_detail = f"Hold {qty} shares. Structural stop at ₹{trailing_sl} ({dist_to_sl_pct}% away)."

        return {
            "symbol": clean_sym,
            "strategy_mode": mode,
            "company_name": clean_sym,
            "qty": qty,
            "buy_price": buy_price,
            "cmp": cmp,
            "invested": invested,
            "current_val": current_val,
            "pnl": pnl,
            "pnl_pct": round(pnl_pct, 2),
            "trailing_stop_loss": trailing_sl,
            "sl_type": sl_type,
            "dist_to_sl_pct": dist_to_sl_pct,
            "fund_score": fund_score,
            "roce_pct": roce_num,
            "opm_expansion_bps": opm_exp_bps,
            "qtr_pat_yoy_pct": qtr_pat_yoy,
            "action_code": action_code,
            "action_badge": action_badge,
            "action_color": action_color,
            "rationale": rationale,
            "suggested_action_detail": suggested_action_detail,
            "news_catalyst": crit_alerts[0] if crit_alerts else (top_bearish_news[0] if top_bearish_news else ""),
            "news_sentiment_score": news_audit.get("score", 5.0),
            "technicals": {
                "rsi": round(rsi, 1),
                "ema_20": round(ema_20, 2),
                "ema_50": round(ema_50, 2),
                "ema_200": round(ema_200, 2),
                "atr": round(atr, 2),
                "volume_ratio": round(vol_ratio, 2),
            },
        }

    def audit_entire_portfolio(self, holdings: List[Dict[str, Any]], strategy_mode: str = "long_term") -> Dict[str, Any]:
        """Audits all portfolio holdings under the chosen strategy horizon and computes aggregate KPIs."""
        audited_holdings = []
        total_invested = 0.0
        total_current = 0.0
        at_risk_count = 0
        profit_booking_count = 0
        urgent_alerts = []

        for h in holdings:
            sym = h.get("symbol", "").strip().upper()
            qty = int(h.get("qty", 0))
            buy_price = float(h.get("buyPrice", 0.0))
            cached_cmp = float(h.get("cmp", 0.0)) if h.get("cmp") else None

            if not sym or qty <= 0:
                continue

            audit_res = self.audit_holding(sym, qty, buy_price, cached_cmp=cached_cmp, strategy_mode=strategy_mode)
            audited_holdings.append(audit_res)

            total_invested += audit_res["invested"]
            total_current += audit_res["current_val"]

            if audit_res["action_code"] in ["EMERGENCY_SELL", "EXIT_TRAILING_SL", "CUT_LOSS", "TREND_BREAKDOWN_SELL"]:
                at_risk_count += 1
                urgent_alerts.append({
                    "symbol": sym,
                    "badge": audit_res["action_badge"],
                    "color": audit_res["action_color"],
                    "reason": audit_res["rationale"],
                    "detail": audit_res["suggested_action_detail"],
                })
            elif audit_res["action_code"] == "BOOK_PARTIAL_PROFIT":
                profit_booking_count += 1

        total_pnl = total_current - total_invested
        total_pnl_pct = round((total_pnl / (total_invested + 1e-6)) * 100, 2) if total_invested > 0 else 0.0
        health_score = round(((len(audited_holdings) - at_risk_count) / len(audited_holdings)) * 10.0, 1) if audited_holdings else 10.0

        return {
            "strategy_mode": strategy_mode,
            "total_holdings_count": len(audited_holdings),
            "total_invested": round(total_invested, 2),
            "total_current_val": round(total_current, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": total_pnl_pct,
            "portfolio_health_score": health_score,
            "at_risk_count": at_risk_count,
            "profit_booking_count": profit_booking_count,
            "urgent_alerts": urgent_alerts,
            "holdings": audited_holdings,
        }
