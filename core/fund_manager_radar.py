from typing import List, Dict, Any, Optional
import json
from pathlib import Path
from datetime import datetime
from core.market_data import MarketDataManager

class FundManagerRadar:
    """
    Acts as a Senior Chief Investment Officer (CIO) / Veteran Fund Manager.
    Maintains an active institutional monitoring radar of stocks tracked for
    future breakout entries, pullback buys, and multi-year compounding.
    """

    from config import DATA_DIR
    RADAR_FILE = DATA_DIR / "monitored_stocks.json"

    DEFAULT_MONITORED_STOCKS = [
        {
            "symbol": "LAURUSLABS",
            "name": "Laurus Labs Ltd.",
            "sector": "Healthcare / CDMO & API",
            "setup_type": "Turnaround Growth & 52W Breakout",
            "monitoring_status": "Active Breakout / Buy on Dip (₹2,280 - ₹2,320)",
            "entry_trigger": 2340.0,
            "target_3m": 2650.0,
            "target_1y": 3200.0,
            "stop_loss": 2180.0,
            "risk_reward": "1:3.2",
            "cio_conviction": 9.4,
            "institutional_thesis": (
                "Turnaround leader in CDMO & Active Pharmaceutical Ingredients (API). "
                "Operating leverage kicking in post-capex with strong recovery in commercial batches. "
                "US FDA clearance at Visakhapatnam formulations unit provides multi-year revenue visibility. "
                "High relative strength (+139% 1Y return) with sustained institutional accumulation."
            ),
            "catalysts": [
                "Biotech CDMO commercial ramp-up",
                "Operating margin expansion from 15% towards 22%",
                "US FDA non-critical inspection clearance",
                "Non-ARV API diversification"
            ]
        },
        {
            "symbol": "DIXON",
            "name": "Dixon Technologies Ltd.",
            "sector": "Electronics Manufacturing Services (EMS)",
            "setup_type": "PLI-Led High Growth Momentum",
            "monitoring_status": "Approaching New 52W High Breakout",
            "entry_trigger": 14200.0,
            "target_3m": 16000.0,
            "target_1y": 18500.0,
            "stop_loss": 13300.0,
            "risk_reward": "1:2.8",
            "cio_conviction": 9.1,
            "institutional_thesis": (
                "Primary beneficiary of Government of India's Electronics PLI schemes. "
                "Mobile phone assembly contracts with global smartphone giants creating massive scale. "
                "Backward integration into display modules and precision components expanding margins."
            ),
            "catalysts": [
                "Export ramp-up to US/Europe",
                "IT Hardware PLI 2.0 contract executions",
                "Operating leverage in high-volume smartphone segment"
            ]
        },
        {
            "symbol": "TRENT",
            "name": "Trent Ltd. (Tata Group)",
            "sector": "Retail & Fast Fashion",
            "setup_type": "Structural Trend Compounder",
            "monitoring_status": "Accumulate on 20/50 EMA Pullbacks",
            "entry_trigger": 7100.0,
            "target_3m": 8200.0,
            "target_1y": 9500.0,
            "stop_loss": 6650.0,
            "risk_reward": "1:3.0",
            "cio_conviction": 9.3,
            "institutional_thesis": (
                "Zudio format represents the biggest retail success story in India with phenomenal unit economics. "
                "Westside maintaining industry-leading same-store sales growth. "
                "Zero long-term debt and continuous internal cash flow funding 200+ store additions annually."
            ),
            "catalysts": [
                "Zudio international expansion (Dubai/Middle East)",
                "Star Bazaar grocery retail turning EBITDA positive",
                "Rapid store addition pace accelerating market share"
            ]
        },
        {
            "symbol": "SUZLON",
            "name": "Suzlon Energy Ltd.",
            "sector": "Renewable Energy / Wind Equipment",
            "setup_type": "Debt-Free Turnaround & Capacity Expansion",
            "monitoring_status": "Stage-2 Consolidation Breakout Watch",
            "entry_trigger": 68.0,
            "target_3m": 84.0,
            "target_1y": 105.0,
            "stop_loss": 61.5,
            "risk_reward": "1:3.4",
            "cio_conviction": 8.8,
            "institutional_thesis": (
                "Complete balance sheet transformation from debt-heavy to net cash surplus. "
                "Order book at historical highs (>5.5 GW) with robust demand from C&I and PSU tenders. "
                "3.x MW turbine technology commanding high pricing power and superior execution margins."
            ),
            "catalysts": [
                "Quarterly execution ramp-up exceeding 400 MW",
                "High margin offshore/C&I order inflows",
                "Clean balance sheet driving institutional re-rating"
            ]
        },
        {
            "symbol": "KAYNES",
            "name": "Kaynes Technology India Ltd.",
            "sector": "Aerospace, Defense & OSAT Semiconductor",
            "setup_type": "High-Alpha High-Tech Breakout",
            "monitoring_status": "Active Buy Zone (₹5,600 - ₹5,850)",
            "entry_trigger": 5750.0,
            "target_3m": 6600.0,
            "target_1y": 7800.0,
            "stop_loss": 5250.0,
            "risk_reward": "1:2.7",
            "cio_conviction": 9.0,
            "institutional_thesis": (
                "High-mix, high-value electronics manufacturing for defense, space, railways, and industrial IoT. "
                "Setting up an advanced OSAT semiconductor testing facility backed by Central/State subsidies. "
                "Revenue CAGR exceeding 40% with industry-leading EBITDA margins (>14%)."
            ),
            "catalysts": [
                "OSAT chip packaging plant commercialization",
                "Execution of massive Kavach railway safety system electronics",
                "Global aerospace export certifications"
            ]
        },
        {
            "symbol": "BSE",
            "name": "BSE Ltd.",
            "sector": "Capital Markets / Exchange Infrastructure",
            "setup_type": "Market Share Re-Rating & Derivative Boom",
            "monitoring_status": "Pullback Buy Zone near 20-EMA",
            "entry_trigger": 3800.0,
            "target_3m": 4400.0,
            "target_1y": 5200.0,
            "stop_loss": 3520.0,
            "risk_reward": "1:2.9",
            "cio_conviction": 8.9,
            "institutional_thesis": (
                "Bankex and Sensex derivative contracts continuing to capture market share from NSE. "
                "StAR MF mutual fund platform processing over 45% of India's digital mutual fund transactions. "
                "High operating leverage ensures almost 80% of incremental revenue flows directly to operating profit."
            ),
            "catalysts": [
                "Sustained derivative volume market share gains (>22%)",
                "Monetization of StAR MF platform transaction fees",
                "New commodity and interest rate derivative product rollouts"
            ]
        },
        {
            "symbol": "HAL",
            "name": "Hindustan Aeronautics Ltd.",
            "sector": "Defense & Aerospace Manufacturing",
            "setup_type": "Multi-Year Indigenization Super-Cycle",
            "monitoring_status": "Consolidation Accumulation (₹4,850 - ₹5,000)",
            "entry_trigger": 4980.0,
            "target_3m": 5700.0,
            "target_1y": 6800.0,
            "stop_loss": 4620.0,
            "risk_reward": "1:3.1",
            "cio_conviction": 9.2,
            "institutional_thesis": (
                "Monopoly aircraft & helicopter manufacturer for Indian Armed Forces. "
                "Order book visibility exceeding ₹1.2 lakh crore covering Tejas Mk1A, Prachand LCH, and ALH. "
                "High return on equity (>28%), zero debt, and robust dividend yield."
            ),
            "catalysts": [
                "Tejas Mk1A engine delivery acceleration",
                "Export agreements with friendly foreign nations (SE Asia / Africa)",
                "Fifth-generation AMCA fighter jet development milestone"
            ]
        },
        {
            "symbol": "DIVISLAB",
            "name": "Divi's Laboratories Ltd.",
            "sector": "Healthcare / Custom Synthesis & API",
            "setup_type": "Big Pharma Outsourcing Breakout",
            "monitoring_status": "Momentum Breakout above ₹10,200",
            "entry_trigger": 10320.0,
            "target_3m": 11800.0,
            "target_1y": 13500.0,
            "stop_loss": 9700.0,
            "risk_reward": "1:2.8",
            "cio_conviction": 9.0,
            "institutional_thesis": (
                "Global leader in custom synthesis for top 10 pharmaceutical multinationals. "
                "Heavy investments into GLP-1 peptide intermediates creating huge multi-year revenue runway. "
                "Near-monopoly in contrast media APIs with fortress balance sheet."
            ),
            "catalysts": [
                "GLP-1 peptide commercial scale-up for global weight loss drugs",
                "Kakinada mega-facility commercial batch commencement",
                "EBITDA margins reverting to historical 38-40% band"
            ]
        }
    ]

    def __init__(self):
        self.market_data = MarketDataManager()
        self._ensure_radar_file()

    def _ensure_radar_file(self):
        """Initializes radar storage file with vetted monitored stocks."""
        self.RADAR_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not self.RADAR_FILE.exists():
            with open(self.RADAR_FILE, "w", encoding="utf-8") as f:
                json.dump(self.DEFAULT_MONITORED_STOCKS, f, indent=2)

    def get_monitored_stocks(self, sync_live_prices: bool = True) -> List[Dict[str, Any]]:
        """Retrieves active monitoring radar with updated live quotes."""
        try:
            with open(self.RADAR_FILE, "r", encoding="utf-8") as f:
                stocks = json.load(f)
        except Exception:
            stocks = self.DEFAULT_MONITORED_STOCKS

        if sync_live_prices:
            for s in stocks:
                try:
                    overview = self.market_data.get_quote_and_overview(s["symbol"])
                    cmp = overview.get("currentPrice", 0.0)
                    if cmp > 0:
                        s["cmp"] = cmp
                        s["day_change_pct"] = overview.get("changePercent", 0.0)
                        s["fifty_two_week_high"] = overview.get("fiftyTwoWeekHigh", 0.0)
                        s["fifty_two_week_low"] = overview.get("fiftyTwoWeekLow", 0.0)
                        h52 = s["fifty_two_week_high"]
                        s["dist_from_52w_high"] = round(((h52 - cmp) / (h52 + 1e-6)) * 100, 1) if h52 > 0 else 0.0

                        # Auto-synchronize entry_trigger, status, targets & stop loss if baseline misaligned with live CMP
                        old_sl = s.get("stop_loss", 0)
                        old_t3m = s.get("target_3m", 0)
                        if old_sl >= cmp or old_t3m <= cmp or old_t3m > cmp * 2.2:
                            low_e = round(cmp * 0.97, 1)
                            high_e = round(cmp * 1.005, 1)
                            s["entry_trigger"] = round(cmp * 0.99, 1)
                            s["monitoring_status"] = f"Active Accumulation Zone (₹{low_e:,.1f} - ₹{high_e:,.1f})"
                            s["target_3m"] = round(cmp * 1.15, 1)
                            s["target_1y"] = round(cmp * 1.38, 1)
                            s["stop_loss"] = round(cmp * 0.91, 1)
                            s["risk_reward"] = "1:2.8"
                except Exception:
                    pass

        return stocks

    def sync_with_scanner_results(self, bullish_picks: List[Dict[str, Any]], max_promote: int = 4) -> List[Dict[str, Any]]:
        """
        Automatically synchronizes Radar CIO conviction ratings with live BullishScanner results
        and auto-promotes top newly discovered Stage-2 / Laurus-Type Inflection setups into the watchlist.
        Preserves all manually curated core stocks while rotating auto-promoted slots daily.
        """
        stocks = self.get_monitored_stocks(sync_live_prices=False)
        # Keep manually curated core entries intact; rotate prior auto-promoted entries cleanly
        core_stocks = [s for s in stocks if not s.get("auto_promoted")]
        core_syms = {s["symbol"] for s in core_stocks}
        pick_map = {p["symbol"]: p for p in bullish_picks if p.get("symbol")}

        # 1. Dynamically recalibrate CIO conviction & prices on curated core radar stocks
        for s in core_stocks:
            sym = s["symbol"]
            if "baseline_conviction" not in s:
                s["baseline_conviction"] = float(s.get("cio_conviction", 8.5))
            if sym in pick_map:
                p = pick_map[sym]
                live_sc = float(p.get("conviction_score", s["baseline_conviction"]))
                s["cio_conviction"] = round((float(s["baseline_conviction"]) * 0.45) + (live_sc * 0.55), 1)
                s["cmp"] = p.get("cmp", s.get("cmp", s.get("entry_trigger", 0)))
                s["day_change_pct"] = p.get("change_pct", s.get("day_change_pct", 0.0))
                s["conviction_source"] = "Live Auto-Synced"
            else:
                s["conviction_source"] = "Core Curated"

        # 2. Auto-promote top new high-conviction whole-market discoveries (Score >= 9.0)
        promoted: List[Dict[str, Any]] = []
        eligible = [
            p for p in bullish_picks
            if p.get("symbol") not in core_syms and float(p.get("conviction_score", 0.0)) >= 9.0
        ]
        # Prefer Laurus-Type Inflections first, then highest conviction score
        eligible.sort(
            key=lambda x: (
                1 if "Inflection" in str(x.get("archetype_short", "")) else 0,
                float(x.get("conviction_score", 0.0)),
                float(x.get("inflection_score", 0.0)),
            ),
            reverse=True,
        )

        for p in eligible[:max_promote]:
            cmp_val = float(p.get("cmp", 0.0))
            if cmp_val <= 0:
                continue
            roce_v = p.get("roce_pct", "N/A")
            opm_bps = p.get("opm_expansion_bps")
            pat_yoy = p.get("qtr_pat_yoy_pct")
            inst_d = p.get("inst_4q_delta_pct", 0.0)
            opm_str = f"OPM {opm_bps:+.0f} bps, " if opm_bps is not None else ""
            pat_str = f"Qtr PAT {pat_yoy:+.1f}% YoY, " if pat_yoy is not None else ""
            thesis = (
                f"Auto-promoted from 509-stock whole-market scan ({p.get('mcap_tier', 'NSE')}). "
                f"Trading with 1Y return {p.get('ret_1y', 0):+.1f}%, ROCE {roce_v}%, "
                f"{opm_str}{pat_str}and FII+DII 4Q accumulation {inst_d:+.1f}%."
            )
            catalysts = [c for c in p.get("fundamental_strengths", [])[:3] if c] or [
                "Margin & EPS acceleration",
                "Stage-2 institutional breakout",
            ]
            promoted.append({
                "symbol": p["symbol"],
                "name": p.get("name", p["symbol"]),
                "sector": p.get("sector", "Equities"),
                "setup_type": f"Auto-Promoted {p.get('archetype_short', 'Stage-2 Leader')}",
                "monitoring_status": f"Auto-Discovered Entry ({p.get('suggested_entry', 'Near CMP')})",
                "entry_trigger": cmp_val,
                "target_3m": p.get("target_1", round(cmp_val * 1.14, 2)),
                "target_1y": p.get("target_2", round(cmp_val * 1.35, 2)),
                "stop_loss": p.get("stop_loss", round(cmp_val * 0.91, 2)),
                "risk_reward": p.get("risk_reward", "1:2.5"),
                "cio_conviction": p.get("conviction_score", 9.0),
                "conviction_source": "Auto-Promoted Discovery",
                "auto_promoted": True,
                "institutional_thesis": thesis,
                "catalysts": catalysts,
                "cmp": cmp_val,
                "day_change_pct": p.get("change_pct", 0.0),
            })

        merged = core_stocks + promoted
        merged.sort(key=lambda x: float(x.get("cio_conviction", 0.0)), reverse=True)

        try:
            with open(self.RADAR_FILE, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=2)
        except Exception:
            pass

        return merged

    def add_to_radar(self, symbol: str, setup_type: str, thesis: str, target_3m: float, target_1y: float, stop_loss: float) -> bool:
        """Adds a new stock to the agentic AI monitoring list."""
        stocks = self.get_monitored_stocks(sync_live_prices=False)
        clean_sym = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
        
        # Check if already in list
        if any(s["symbol"] == clean_sym for s in stocks):
            return False

        overview = self.market_data.get_quote_and_overview(clean_sym)
        cmp = overview.get("currentPrice", 0.0)

        new_entry = {
            "symbol": clean_sym,
            "name": overview.get("shortName", clean_sym),
            "sector": overview.get("sector", "Indian Equities"),
            "setup_type": setup_type,
            "monitoring_status": f"Monitoring near ₹{cmp}",
            "entry_trigger": cmp,
            "target_3m": target_3m,
            "target_1y": target_1y,
            "stop_loss": stop_loss,
            "risk_reward": f"1:{round((target_3m - cmp) / (cmp - stop_loss + 1e-6), 1)}",
            "cio_conviction": 8.5,
            "institutional_thesis": thesis,
            "catalysts": ["Earnings acceleration", "Institutional accumulation"]
        }

        stocks.append(new_entry)
        with open(self.RADAR_FILE, "w", encoding="utf-8") as f:
            json.dump(stocks, f, indent=2)
        return True

    def get_cio_market_regime(self) -> Dict[str, Any]:
        """Provides senior fund manager macroeconomic perspective and portfolio guidelines."""
        return {
            "market_stance": "Cautiously Bullish with Sector Rotation (Stock Picker's Market)",
            "dominant_themes": [
                "Healthcare & CDMO Turnaround (Laurus Labs, Divi's Lab) benefiting from global supply chain de-risking",
                "Domestic Manufacturing & Electronics PLI (Dixon, Kaynes)",
                "Power Grid & Renewable Energy Capex (BHEL, Suzlon)",
                "Capital Market Financialization (BSE, CDSL, Mutual Funds)"
            ],
            "asset_allocation_rule": {
                "Core Compounding Equities (High ROCE, Secular Leaders)": "55% - 65%",
                "Tactical Alpha & High Momentum Breakouts": "25% - 30%",
                "Cash / Liquid Arbitrage Reserve for Dip Buying": "10% - 15%"
            },
            "risk_management_creed": (
                "Never compromise on risk-reward. Protect downside first; profits take care of themselves. "
                "Trail stops aggressively once a stock clears its 52-week breakout pivot."
            )
        }

