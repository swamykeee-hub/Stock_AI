from typing import Dict, Any, List, Optional
import math
import pandas as pd
from core.market_data import MarketDataManager
from core.technical_analyst import TechnicalAnalyst
from core.news_sentiment_analyst import NewsSentimentAnalyst

class PortfolioHealthAuditor:
    """
    Acts as an Institutional Chief Investment Officer (CIO) for Personal Portfolios.
    Continuously audits user-held stocks against Technical Health, Trailing Stop-Loss levels,
    Real-Time News Events, and Profit-Booking targets to generate authoritative
    BUY / ACCUMULATE / HOLD / TRIM / SELL / EMERGENCY EXIT recommendations.
    """

    def __init__(self):
        self.market_data = MarketDataManager()
        self.tech_analyst = TechnicalAnalyst()
        self.news_analyst = NewsSentimentAnalyst()

    def audit_holding(
        self,
        symbol: str,
        qty: int,
        buy_price: float,
        cached_cmp: Optional[float] = None,
        cached_change_pct: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Runs comprehensive 360-degree audit on a single portfolio holding.
        """
        clean_sym = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
        formatted_sym = self.market_data.format_symbol(clean_sym)

        # 1. Fetch live quotes & candles
        candles = self.market_data.get_historical_candles(clean_sym, period="1y", interval="1d")
        
        cmp = cached_cmp or buy_price
        day_chg_pct = cached_change_pct or 0.0
        company_name = clean_sym

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
                "bearish_signals": []
            }

        # 2. Extract technical parameters
        rsi = tech_audit.get("rsi", 50.0)
        ema_20 = tech_audit.get("ema_20", cmp)
        ema_50 = tech_audit.get("ema_50", cmp)
        ema_200 = tech_audit.get("ema_200", cmp)
        atr = tech_audit.get("atr", cmp * 0.02)
        vol_ratio = tech_audit.get("volume_ratio", 1.0)

        # Highest price reached since purchase (or in last 52 weeks)
        highest_price = cmp
        if not candles.empty:
            highest_price = float(candles["High"].tail(60).max())
            if highest_price < cmp:
                highest_price = cmp

        # 3. Calculate P&L metrics
        invested = qty * buy_price
        current_val = qty * cmp
        pnl = current_val - invested
        pnl_pct = ((cmp - buy_price) / (buy_price + 1e-6)) * 100 if buy_price > 0 else 0.0

        # 4. News & Regulatory Catalyst Audit
        news_audit = self.news_analyst.analyze(clean_sym, company_name)
        has_critical_news = news_audit.get("has_critical_bearish_event", False)
        crit_alerts = news_audit.get("critical_alerts", [])
        sell_risk_score = news_audit.get("sell_risk_score", 3.0)
        top_bearish_news = news_audit.get("top_bearish_catalysts", [])

        # 5. Determine Dynamic Trailing Stop-Loss
        # A smart fund manager protects capital progressively:
        # - In loss or slight gain (< 12%): Initial SL at max(buy_price * 0.92, ema_50 * 0.98)
        # - In solid gain (12% to 35%): Trail to breakeven (buy_price * 1.03) or 50-EMA
        # - In large gain (> 35%): Trail to 20-EMA or 8% below 60-day peak
        if pnl_pct >= 35.0:
            trailing_sl = max(ema_20 * 0.985, highest_price * 0.91, buy_price * 1.15)
            sl_type = "Aggressive Profit Trail (20-EMA / Peak-8%)"
        elif pnl_pct >= 15.0:
            trailing_sl = max(ema_50 * 0.98, buy_price * 1.02)
            sl_type = "Capital Protected Trail (Breakeven+ / 50-EMA)"
        elif pnl_pct >= 0:
            trailing_sl = min(buy_price * 0.92, ema_50 * 0.97)
            sl_type = "Standard Stop-Loss (8% Risk Buffer)"
        else:
            # Losing position
            trailing_sl = round(buy_price * 0.92, 2)
            sl_type = "Strict Risk Boundary (-8% Hard Stop)"

        trailing_sl = round(trailing_sl, 2)
        dist_to_sl_pct = round(((cmp - trailing_sl) / (cmp + 1e-6)) * 100, 1)

        # 6. Senior CIO Decision Matrix (Sell / Hold / Trim / Accumulate)
        action_code = "HOLD"
        action_badge = "🟢 STRONG HOLD"
        action_color = "#10b981"
        rationale = ""
        suggested_action_detail = ""

        # Check conditions in priority order:
        # Priority 1: Emergency News / Regulatory Risk
        if has_critical_news:
            action_code = "EMERGENCY_SELL"
            action_badge = "🔴 EMERGENCY EXIT (HIGH RISK NEWS)"
            action_color = "#ef4444"
            headline_cue = crit_alerts[0] if crit_alerts else "Critical governance or regulatory penalty detected."
            rationale = (
                f"Severe risk detected in news flow: '{headline_cue}'. "
                f"Senior fund managers do not hold through governance probes or regulatory sanctions. "
                f"Capital preservation requires closing position immediately."
            )
            suggested_action_detail = f"Exit all {qty} shares at market CMP ₹{cmp} to safeguard capital."

        # Priority 2: Stop-Loss Breached (Cut Losers or Lock Profits)
        elif cmp < trailing_sl:
            if pnl_pct > 0:
                action_code = "EXIT_TRAILING_SL"
                action_badge = "🔴 TRAILING STOP HIT (LOCK PROFIT)"
                action_color = "#f97316"
                rationale = (
                    f"Price (₹{cmp}) has sliced below the trailing profit stop of ₹{trailing_sl}. "
                    f"Lock in remaining accumulated profits of +{pnl_pct:.1f}% before trend erosion continues."
                )
                suggested_action_detail = f"Sell full holding of {qty} shares to lock +₹{pnl:,.2f} gain."
            else:
                action_code = "CUT_LOSS"
                action_badge = "🔴 HARD STOP HIT (CUT LOSS)"
                action_color = "#dc2626"
                rationale = (
                    f"Price (₹{cmp}) has breached the -8% risk threshold (₹{trailing_sl}). "
                    f"Rule #1 of smart investing: Never let a minor 8% loss become a paralyzing 30% loss. Cut swift."
                )
                suggested_action_detail = f"Sell all {qty} shares to cap loss at -₹{abs(pnl):,.2f}."

        # Priority 3: Severe Technical Breakdown (Below 50 EMA on Volume or Death Cross)
        elif cmp < ema_50 and vol_ratio >= 1.4:
            action_code = "TREND_BREAKDOWN_SELL"
            action_badge = "🔴 TREND BREAKDOWN (50-EMA LOST)"
            action_color = "#ef4444"
            rationale = (
                f"{clean_sym} broke decisively below its 50-day EMA (₹{ema_50:.2f}) on heavy volume ({vol_ratio:.1f}x avg). "
                f"Institutional support has broken down. High probability of further slide toward 200-EMA (₹{ema_200:.2f})."
            )
            suggested_action_detail = f"Exit {qty} shares at ₹{cmp} or place strict stop at ₹{trailing_sl}."

        # Priority 4: Profit Booking / Climax Zone (Huge Gain + Overbought)
        elif pnl_pct >= 40.0 and rsi >= 75.0:
            trim_qty = max(1, math.ceil(qty * 0.35))
            action_code = "BOOK_PARTIAL_PROFIT"
            action_badge = "🟠 BOOK 35% PROFIT (OVERBOUGHT)"
            action_color = "#f59e0b"
            rationale = (
                f"Superb return of +{pnl_pct:.1f}% with RSI at {rsi:.1f} (Extreme Overbought). "
                f"Smart money takes money off the table into euphoric strength. Book 35% profit and let remainder ride."
            )
            suggested_action_detail = f"Book profit on {trim_qty} shares at ₹{cmp} (+₹{pnl:,.2f}); trail stop on balance {qty - trim_qty} shares at ₹{trailing_sl}."

        # Priority 5: Milestone Target 1 Achieved (+25% to +35%)
        elif pnl_pct >= 25.0 and cmp < ema_20:
            trim_qty = max(1, math.ceil(qty * 0.25))
            action_code = "TRIM_ON_WEAKNESS"
            action_badge = "🟡 TRIM 25% (20-EMA SLIP)"
            action_color = "#eab308"
            rationale = (
                f"Position is up +{pnl_pct:.1f}%, but price has dipped under short-term 20-EMA (₹{ema_20:.2f}). "
                f"De-risk by taking 25% off the table and moving stop-loss on remaining shares to breakeven + cushion."
            )
            suggested_action_detail = f"Trim {trim_qty} shares; maintain trailing stop on {qty - trim_qty} shares at ₹{trailing_sl}."

        # Priority 6: Healthy Consolidation Pullback (Accumulation Zone)
        elif cmp >= ema_50 and abs(cmp - ema_20) / (ema_20 + 1e-6) <= 0.015 and pnl_pct > 0 and (45 <= rsi <= 65):
            action_code = "ACCUMULATE_ON_DIP"
            action_badge = "🟢 ACCUMULATE ON DIP (20-EMA)"
            action_color = "#22c55e"
            rationale = (
                f"Price is testing the upward-trending 20-EMA (₹{ema_20:.2f}) with healthy RSI ({rsi:.1f}). "
                f"This is an institutional buy-the-dip zone for multi-quarter compounders."
            )
            suggested_action_detail = f"Hold current {qty} shares; candidate to add 15-20% more quantity with stop at ₹{trailing_sl}."

        # Priority 7: Solid Trend Intact (Default Strong Hold)
        else:
            action_code = "STRONG_HOLD"
            action_badge = "🟢 STRONG HOLD (TREND INTACT)"
            action_color = "#10b981"
            trend_str = "Above 20 & 50 EMA" if (cmp > ema_20 and cmp > ema_50) else "Consolidating above support"
            rationale = (
                f"{clean_sym} maintains a bullish structural posture ({trend_str}) with RSI at {rsi:.1f}. "
                f"Current P&L is {pnl_pct:+.1f}%. Risk-reward favors holding with stop loss at ₹{trailing_sl}."
            )
            suggested_action_detail = f"Hold {qty} shares. Keep trailing stop at ₹{trailing_sl} ({dist_to_sl_pct}% away)."

        return {
            "symbol": clean_sym,
            "company_name": company_name,
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
                "volume_ratio": round(vol_ratio, 2)
            }
        }

    def audit_entire_portfolio(self, holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Audits all holdings in the user portfolio and computes aggregate risk and health KPIs.
        """
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

            audit_res = self.audit_holding(sym, qty, buy_price, cached_cmp=cached_cmp)
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
                    "detail": audit_res["suggested_action_detail"]
                })
            elif audit_res["action_code"] == "BOOK_PARTIAL_PROFIT":
                profit_booking_count += 1

        total_pnl = total_current - total_invested
        total_pnl_pct = round((total_pnl / (total_invested + 1e-6)) * 100, 2) if total_invested > 0 else 0.0

        # Portfolio Health Score (0 to 10 scale)
        if audited_holdings:
            healthy_count = len(audited_holdings) - at_risk_count
            health_ratio = healthy_count / len(audited_holdings)
            health_score = round(health_ratio * 10.0, 1)
        else:
            health_score = 10.0

        return {
            "total_holdings_count": len(audited_holdings),
            "total_invested": round(total_invested, 2),
            "total_current_val": round(total_current, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": total_pnl_pct,
            "portfolio_health_score": health_score,
            "at_risk_count": at_risk_count,
            "profit_booking_count": profit_booking_count,
            "urgent_alerts": urgent_alerts,
            "holdings": audited_holdings
        }
