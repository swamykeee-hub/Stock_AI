import requests
import json
import sys
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

class TelegramAlertBot:
    """
    Automated Telegram Dispatcher for Indian Stock Market AI Intelligence.
    Sends:
      1. 08:45 AM Pre-Market CIO Intelligence & Global Cues
      2. 06:00 PM Post-Market Closing Wrap & Breakouts
      3. Instant Emergency Risk Alerts (Promoter selling, SEBI investigations)
    """

    def __init__(self):
        tele_cfg = getattr(config, "TELEGRAM_CONFIG", {})
        self.bot_token = tele_cfg.get("BOT_TOKEN", "").strip()
        self.chat_id = tele_cfg.get("CHAT_ID", "").strip()
        self.enabled = tele_cfg.get("ENABLED", False) and bool(self.bot_token) and bool(self.chat_id)

    def is_configured(self) -> bool:
        return bool(self.bot_token) and bool(self.chat_id)

    def send_raw_message(self, message: str) -> bool:
        """Sends an HTML-formatted message to the designated Telegram chat/channel."""
        if not self.is_configured():
            print("ℹ️ Telegram Alert Bot: Not configured yet. (Set TELEGRAM_CONFIG in config.py to activate free phone alerts).")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        try:
            r = requests.post(url, json=payload, timeout=8)
            if r.status_code == 200:
                print("✅ Telegram notification dispatched successfully!")
                return True
            else:
                print(f"⚠️ Telegram send notice: HTTP {r.status_code} - {r.text}")
        except Exception as e:
            print(f"⚠️ Telegram connection exception: {e}")
        return False

    def send_pre_market_pulse(self, indices: dict, macro_snap: dict, market_regime: dict, 
                              top_breakouts: list, ipos: list, inst_flow: dict = None) -> bool:
        """Sends comprehensive 08:45 AM Pre-Market Briefing."""
        date_str = datetime.now().strftime("%d %b %Y")
        
        # Global cues
        macro_lines = []
        macro_dict = macro_snap.get("macro", {})
        for k in ["S&P 500", "Nasdaq Composite", "Brent Crude ($/bbl)", "US 10-Yr Yield (%)", "Gold ($/oz)"]:
            if k in macro_dict:
                d = macro_dict[k]
                chg = d.get("change_pct", 0.0)
                sign = "+" if chg > 0 else ""
                macro_lines.append(f"  • <b>{k}:</b> {d.get('price')} ({sign}{chg}%)")

        # Top Breakouts
        breakout_lines = []
        for b in top_breakouts[:3]:
            breakout_lines.append(f"  ⚡ <b>{b.get('symbol')}</b>: CMP ₹{b.get('cmp')} | Near 52W High")

        # IPOs
        ipo_lines = []
        for ip in ipos[:2]:
            ipo_lines.append(f"  📋 <b>{ip.get('name')}</b>: GMP {ip.get('gmp_pct')}% ({ip.get('status')})")

        # Institutional
        inst_txt = ""
        if inst_flow:
            lat = inst_flow.get("fii_dii_latest", {})
            deriv = inst_flow.get("derivatives", {})
            inst_txt = f"\n🏛 <b>Institutional Positioning:</b>\n  • FII Net Cash: ₹{lat.get('fii_cash_net', '—')} Cr\n  • DII Net Cash: ₹{lat.get('dii_cash_net', '—')} Cr\n  • Nifty PCR: {deriv.get('pcr', '1.0')} (Max Pain: {deriv.get('max_pain_strike', '—')})"

        regime_title = market_regime.get("regime", "Trending Bullish")
        stance = market_regime.get("cio_stance", "Accumulate Alpha Leaders on Dips")

        msg = (
            f"🌅 <b>STOCK AI PRE-MARKET PULSE</b> ({date_str})\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"🧭 <b>Market Regime:</b> {regime_title}\n"
            f"💡 <b>CIO Stance:</b> {stance}\n"
            f"{inst_txt}\n\n"
            f"🌍 <b>Global Cues & Commodities:</b>\n" + "\n".join(macro_lines) + "\n\n"
            f"🚀 <b>Key Breakouts on Watch:</b>\n" + ("\n".join(breakout_lines) if breakout_lines else "  • Monitoring consolidation setups") + "\n\n"
            f"📋 <b>Active IPOs & GMP:</b>\n" + ("\n".join(ipo_lines) if ipo_lines else "  • No active issues today") + "\n\n"
            f"📊 <b>Live Web Dashboard:</b>\n"
            f"https://swamykeee-hub.github.io/Stock_AI/"
        )
        return self.send_raw_message(msg)

    def send_evening_wrap(self, indices: dict, momentum_leaders: list, bullish_picks: list) -> bool:
        """Sends comprehensive 06:00 PM Post-Market Closing Wrap."""
        date_str = datetime.now().strftime("%d %b %Y")
        
        idx_lines = []
        for idx in ["NIFTY 50", "NIFTY BANK", "NIFTY MIDCAP 100"]:
            if idx in indices:
                d = indices[idx]
                sign = "+" if d.get("percent", 0) > 0 else ""
                idx_lines.append(f"  • <b>{idx}:</b> {d.get('value')} ({sign}{d.get('percent', 0):.2f}%)")

        gainers = []
        for s in momentum_leaders[:3]:
            gainers.append(f"  🏆 <b>{s.get('symbol')}</b>: CMP ₹{s.get('cmp')} (3M: +{s.get('ret_3m')}%)")

        picks = []
        for p in bullish_picks[:3]:
            picks.append(f"  🎯 <b>{p.get('symbol')}</b>: Conviction {p.get('conviction_score')}/10 | Target ₹{p.get('target_1')}")

        msg = (
            f"🔔 <b>STOCK AI EVENING MARKET WRAP</b> ({date_str})\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"📈 <b>Indian Indices Closing:</b>\n" + "\n".join(idx_lines) + "\n\n"
            f"🚀 <b>Top Super-Trend Leaders:</b>\n" + ("\n".join(gainers) if gainers else "  • Market consolidating") + "\n\n"
            f"🎯 <b>Fresh 360° AI Picks:</b>\n" + ("\n".join(picks) if picks else "  • Strict capital preservation active") + "\n\n"
            f"📊 <b>Full Analysis & Portfolio Audit:</b>\n"
            f"https://swamykeee-hub.github.io/Stock_AI/"
        )
        return self.send_raw_message(msg)

    def send_emergency_risk_alert(self, symbol: str, headline: str, rationale: str) -> bool:
        """Sends immediate high-priority warning when risk is detected."""
        msg = (
            f"🚨 <b>PORTFOLIO EMERGENCY RISK ALERT</b> 🚨\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <b>Stock:</b> {symbol}\n"
            f"📰 <b>News Catalyst:</b> {headline}\n\n"
            f"🛡 <b>AI Action Rationale:</b>\n{rationale}\n\n"
            f"👉 <i>Review your holdings on https://swamykeee-hub.github.io/Stock_AI/</i>"
        )
        return self.send_raw_message(msg)

    def send_portfolio_catalyst_alerts(
        self,
        portfolio_audit: Dict[str, Any] = None,
        corporate_actions: Dict[str, Any] = None,
        radar_stocks: List[Dict[str, Any]] = None,
        bullish_picks: List[Dict[str, Any]] = None,
    ) -> bool:
        """
        Dispatches proactive Telegram alert digest for held/radar stocks covering:
        - Urgent CIO portfolio risk / exit warnings
        - Upcoming ex-dividend dates & quarterly earnings
        - High-conviction Laurus-Type Inflections (>= 9.2)
        """
        sections: List[str] = []

        urgent = (portfolio_audit or {}).get("urgent_alerts", [])
        if urgent:
            lines = [f"  • <b>{u['symbol']}</b>: {u['badge']} — {u['detail']}" for u in urgent[:4]]
            sections.append("🛑 <b>Urgent Portfolio Risk Alerts:</b>\n" + "\n".join(lines))

        conc = (portfolio_audit or {}).get("concentration_alerts", [])
        if conc:
            sections.append("⚠️ <b>Allocation Guardrails:</b>\n" + "\n".join(f"  • {c}" for c in conc[:3]))

        held_syms = {h.get("symbol", "").upper() for h in (portfolio_audit or {}).get("holdings", []) if h.get("symbol")}
        watch_syms = held_syms | {r.get("symbol", "").upper() for r in (radar_stocks or []) if r.get("symbol")}

        ca_hits: List[str] = []
        if watch_syms and corporate_actions:
            for d in corporate_actions.get("dividends", []):
                s = str(d.get("symbol", "")).upper()
                if s in watch_syms:
                    ca_hits.append(f"  💰 <b>{s}</b> Dividend {d.get('dividend_amount')} (Ex: {d.get('ex_date')})")
            for e in corporate_actions.get("earnings", []):
                s = str(e.get("symbol", "")).upper()
                if s in watch_syms:
                    ca_hits.append(f"  📊 <b>{s}</b> {e.get('result_type', 'Results')} on {e.get('date')}")
        if ca_hits:
            sections.append("📅 <b>Watchlist & Portfolio Catalysts:</b>\n" + "\n".join(ca_hits[:5]))

        inflections = [
            p for p in (bullish_picks or [])
            if float(p.get("conviction_score", 0.0)) >= 9.2
        ][:4]
        if inflections:
            inf_lines = [
                f"  🔥 <b>{p['symbol']}</b> ({p['conviction_score']}/10, {p.get('archetype_short', 'Breakout')}) @ ₹{p.get('cmp')}"
                for p in inflections
            ]
            sections.append("💎 <b>Top High-Conviction Inflections (>=9.2):</b>\n" + "\n".join(inf_lines))

        if not sections:
            return False

        date_str = datetime.now().strftime("%d %b %Y")
        msg = (
            f"📌 <b>STOCK AI PORTFOLIO & CATALYST BRIEF</b> ({date_str})\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            + "\n\n".join(sections)
            + "\n\n👉 https://swamykeee-hub.github.io/Stock_AI/"
        )
        return self.send_raw_message(msg)

if __name__ == "__main__":
    bot = TelegramAlertBot()
    print("Telegram Bot is configured:", bot.is_configured())
    if not bot.is_configured():
        print("Setup instructions:")
        print(" 1. In Telegram, search for @BotFather and message '/newbot'")
        print(" 2. Copy the HTTP API token into config.py under TELEGRAM_CONFIG['BOT_TOKEN']")
        print(" 3. Message @userinfobot to find your personal numeric Telegram Chat ID")
        print(" 4. Set ENABLED: True")
