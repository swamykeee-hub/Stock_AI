import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import concurrent.futures
import config
from core.market_data import MarketDataManager
from core.technical_analyst import TechnicalAnalyst
from core.fundamental_analyst import FundamentalAnalyst, parse_float_safe
from core.momentum_screener import MomentumScreener


class BullishScanner:
    """
    Two-Pass Whole-Market Multibagger & Inflection Discovery Engine across all 509+ NSE stocks.
    - Pass 1: Fast weekly Stage-2, Relative Strength (vs Nifty 50), and early Stage-1->2 base reclaim screen.
    - Pass 2: Deep consolidated Screener.in audit (ROCE, Debt/Equity, OPM expansion, Quarterly PAT surge,
              CFO/EBITDA cash quality, CWIP capex runway, FII/DII accumulation, and GARP/PEG valuation)
              combined with daily entry/target/stop-loss precision.
    """

    PRIORITY_MOMENTUM_STOCKS = [
        {"symbol": "LAURUSLABS", "name": "Laurus Labs Ltd.", "sector": "Healthcare"},
        {"symbol": "DIXON", "name": "Dixon Technologies (India) Ltd.", "sector": "Consumer Durables"},
        {"symbol": "TRENT", "name": "Trent Ltd.", "sector": "Consumer Services"},
        {"symbol": "SUZLON", "name": "Suzlon Energy Ltd.", "sector": "Capital Goods"},
        {"symbol": "KAYNES", "name": "Kaynes Technology India Ltd.", "sector": "Capital Goods"},
        {"symbol": "BSE", "name": "BSE Ltd.", "sector": "Financial Services"},
        {"symbol": "HAL", "name": "Hindustan Aeronautics Ltd.", "sector": "Capital Goods"},
        {"symbol": "BEL", "name": "Bharat Electronics Ltd.", "sector": "Capital Goods"},
        {"symbol": "DIVISLAB", "name": "Divi's Laboratories Ltd.", "sector": "Healthcare"},
        {"symbol": "PERSISTENT", "name": "Persistent Systems Ltd.", "sector": "Information Technology"},
        {"symbol": "MCX", "name": "Multi Commodity Exchange of India Ltd.", "sector": "Financial Services"},
        {"symbol": "COFORGE", "name": "Coforge Ltd.", "sector": "Information Technology"},
        {"symbol": "POLYCAB", "name": "Polycab India Ltd.", "sector": "Capital Goods"},
        {"symbol": "SOLARINDS", "name": "Solar Industries India Ltd.", "sector": "Chemicals"},
        {"symbol": "APARINDS", "name": "Apar Industries Ltd.", "sector": "Capital Goods"},
    ]

    def __init__(self, data_path: Path = None):
        self.market_data = MarketDataManager()
        self.tech_analyst = TechnicalAnalyst()
        self.fund_analyst = FundamentalAnalyst()
        self.momentum_screener = MomentumScreener()
        self.data_path = Path(data_path) if data_path else (config.DATA_DIR / "nse_stocks.json")

    def load_stock_universe(self) -> List[Dict[str, str]]:
        """Loads complete NSE stock universe with priority leaders deduplicated at the top."""
        full_universe = []
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    full_universe = json.load(f)
            except Exception:
                pass

        seen = set()
        combined = []
        for p in self.PRIORITY_MOMENTUM_STOCKS:
            sym = p["symbol"].strip().upper()
            seen.add(sym)
            combined.append({"symbol": sym, "name": p["name"], "sector": p["sector"]})

        for item in full_universe:
            sym = item.get("symbol", "").strip().upper()
            if sym and sym not in seen:
                seen.add(sym)
                combined.append({
                    "symbol": sym,
                    "name": item.get("name", sym),
                    "sector": item.get("sector", "Equities"),
                })

        return combined

    @staticmethod
    def _qualifies_pass1_candidate(w: Dict[str, Any], is_priority: bool) -> bool:
        """Pass-1 filter: Keeps liquid Stage-2 leaders, VCP tight bases, and early base-reclaim turnarounds."""
        if is_priority:
            return True
        if w.get("avg_daily_turnover_cr", 0.0) < 2.0:
            return False

        cmp = w.get("cmp", 0.0)
        ema_40w = w.get("ema_40w", cmp)
        dist_52w = w.get("distance_from_52w_high", 100.0)
        ret_3m = w.get("ret_3m", 0.0)
        ret_6m = w.get("ret_6m", 0.0)
        ret_1y = w.get("ret_1y", 0.0)
        rs_6m = w.get("rs_vs_nifty_6m", 0.0)
        w_rsi = w.get("weekly_rsi", 50.0)

        stage2_or_near_high = (cmp > ema_40w) and (dist_52w <= 18.0 or rs_6m >= 8.0 or ret_1y >= 22.0)
        early_turnaround_reclaim = (cmp >= ema_40w * 0.96) and (ret_3m >= 8.0 or ret_6m >= 12.0) and (48.0 <= w_rsi <= 76.0)
        return stage2_or_near_high or early_turnaround_reclaim

    def _pass2_deep_audit(self, weekly_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Pass-2 audit: Consolidated Screener inflection + quality + GARP + daily entry calibration."""
        symbol = weekly_data["symbol"]
        try:
            cmp = weekly_data["cmp"]
            if cmp <= 0:
                return None

            # 1. Consolidated Fundamental & Inflection Audit
            fund_res = self.fund_analyst.analyze(symbol)
            metrics = fund_res.get("metrics", {})
            ranges = fund_res.get("ranges", {})
            inflection = fund_res.get("inflection", {})
            balance_inst = fund_res.get("balance_inst", {})

            fund_score = float(fund_res.get("score", 5.0))
            quality_score = float(fund_res.get("quality_score", 5.0))
            inflection_score = float(fund_res.get("inflection_score", 5.0))
            valuation_score = float(fund_res.get("valuation_score", 5.0))

            # Hygiene Gate 1: Leverage safety for non-financials
            sector_str = str(weekly_data.get("sector", ""))
            is_fin = balance_inst.get("is_financial_sector", False) or any(
                k in sector_str.lower() for k in ("bank", "financ", "insurance")
            )
            de_ratio = balance_inst.get("debt_to_equity")
            if not is_fin and de_ratio is not None and de_ratio > 1.25:
                return None

            # Hygiene Gate 2: Promoter Pledge safety
            pledge_pct = balance_inst.get("promoter_pledge_pct", 0.0)
            if pledge_pct > 10.0:
                return None

            # Hygiene Gate 3: Cash flow sanity (block deep cash burners without turnaround proof)
            cfo_pat = balance_inst.get("cfo_to_pat_3y")
            if not is_fin and cfo_pat is not None and cfo_pat < 0.15 and (inflection.get("qtr_pat_yoy_pct") or 0) < 20.0:
                return None

            # 2. Daily Technicals for exact Swing/Pullback Entry, Stop Loss, and Targets
            candles = self.market_data.get_historical_candles(symbol, period="1y", interval="1d")
            if candles.empty or len(candles) < 30:
                return None
            tech_res = self.tech_analyst.analyze(candles)
            tech_score = float(tech_res.get("score", 5.0))

            # Must show constructive medium/long-term price structure
            ema_20 = float(tech_res.get("ema_20", cmp))
            ema_50 = float(tech_res.get("ema_50", cmp))
            ema_200 = float(tech_res.get("ema_200", cmp))
            if cmp < ema_200 * 0.96 and tech_score < 5.5:
                return None

            # 3. Extract Quantitative Multibagger Signals
            roce_num = parse_float_safe(metrics.get("roce_pct")) or 0.0
            roe_num = parse_float_safe(metrics.get("roe_pct")) or 0.0
            pe_num = parse_float_safe(metrics.get("stock_pe")) or 0.0
            peg_num = parse_float_safe(metrics.get("peg_ratio"))
            mcap_cr = parse_float_safe(metrics.get("market_cap_cr")) or 0.0

            opm_latest = inflection.get("opm_latest_pct")
            opm_exp_bps = inflection.get("opm_expansion_bps")
            qtr_pat_yoy = inflection.get("qtr_pat_yoy_pct")
            qtr_sales_yoy = inflection.get("qtr_sales_yoy_pct")
            inst_delta = balance_inst.get("inst_4q_delta_pct", 0.0)
            cwip_growth = balance_inst.get("cwip_growth_pct", 0.0)
            cfo_ebitda = balance_inst.get("cfo_ebitda_pct")

            # Market Cap Tier Tag
            if mcap_cr > 0 and mcap_cr <= config.MULTIBAGGER_CONFIG["MIDCAP_SWEET_SPOT_MAX_CR"]:
                mcap_tier = "Mid/Small-Cap Alpha"
                runway_bonus = 0.6 if mcap_cr >= config.MULTIBAGGER_CONFIG["MIDCAP_SWEET_SPOT_MIN_CR"] else 0.3
            elif mcap_cr > 0:
                mcap_tier = "Large-Cap Core"
                runway_bonus = 0.1
            else:
                mcap_tier = weekly_data.get("market_cap_type", "Mid/Large Cap")
                runway_bonus = 0.2

            # 4. Weekly Stage-2 & VCP Structure Score (0-10)
            w_score = 4.5
            if cmp > weekly_data.get("ema_40w", cmp):
                w_score += 1.5
            if weekly_data.get("ema_40w_rising"):
                w_score += 1.0
            if weekly_data.get("is_vcp_tight"):
                w_score += 1.2
            if weekly_data.get("distance_from_52w_high", 100) <= 10.0:
                w_score += 0.8
            if weekly_data.get("rs_vs_nifty_6m", 0) >= 12.0:
                w_score += 1.0
            elif weekly_data.get("rs_vs_nifty_6m", 0) >= 5.0:
                w_score += 0.5
            if weekly_data.get("volume_surge", 1.0) >= 1.35:
                w_score += 0.6
            if weekly_data.get("pct_above_ema20w", 0.0) > 25.0:
                w_score -= 1.0  # Penalize overextended chases
            w_score = max(1.0, min(round(w_score, 1), 10.0))

            # Smart Money & Runway Component Score (0-10)
            sm_score = 5.0 + runway_bonus
            if inst_delta >= 2.0:
                sm_score += 2.2
            elif inst_delta >= 0.5:
                sm_score += 1.0
            elif inst_delta <= -2.5:
                sm_score -= 1.2
            if cwip_growth >= 20.0:
                sm_score += 0.8
            if balance_inst.get("promoter_pct") and balance_inst["promoter_pct"] >= 50.0:
                sm_score += 0.6
            sm_score = max(1.0, min(round(sm_score, 1), 10.0))

            # Combined Multibagger Conviction Score (0-10):
            # 30% Quality, 30% Inflection/Growth, 20% Smart Money/GARP, 20% Weekly Stage-2/VCP
            garp_smart = (valuation_score * 0.55) + (sm_score * 0.45)
            multibagger_score = round(
                min(
                    10.0,
                    max(
                        1.0,
                        (quality_score * 0.30)
                        + (inflection_score * 0.30)
                        + (garp_smart * 0.20)
                        + (w_score * 0.20),
                    ),
                ),
                1,
            )

            # Filter out weak setups that shouldn't appear in top bullish picks
            if multibagger_score < 6.2:
                return None

            # Classify Archetype Badge
            is_laurus_inflection = (
                (opm_exp_bps is not None and opm_exp_bps >= 150)
                and (qtr_pat_yoy is not None and qtr_pat_yoy >= 20.0)
                and cmp >= ema_200 * 0.98
            )
            if is_laurus_inflection:
                archetype = "🚀 Multibagger Inflection (Laurus-Type)"
                archetype_short = "Laurus-Type Inflection"
            elif weekly_data.get("is_vcp_tight") and weekly_data.get("distance_from_52w_high", 100) <= 10.0:
                archetype = "🔥 VCP Stage-2 Breakout"
                archetype_short = "VCP Breakout"
            elif quality_score >= 7.2 and roce_num >= 18.0:
                archetype = "🏛️ High-ROCE Compounder"
                archetype_short = "High-ROCE Compounder"
            else:
                archetype = "⚡ Stage-2 Momentum Breakout"
                archetype_short = "Stage-2 Breakout"

            # Entry, Target & Stop Loss calibration (supports both tactical swing & long-term runway)
            atr = float(tech_res.get("atr", cmp * 0.02))
            entry_low = round(min(cmp * 0.98, ema_20 * 0.995), 2)
            entry_high = round(cmp * 1.005, 2)
            target_1 = round(max(cmp + (2.5 * atr), cmp * 1.12), 2)
            target_2 = round(max(cmp + (5.0 * atr), cmp * 1.32), 2)
            stop_loss = round(min(cmp - (1.8 * atr), ema_50 * 0.985), 2)
            risk_v = cmp - stop_loss
            rew_v = target_1 - cmp
            rr = f"1:{round(rew_v / (risk_v + 1e-6), 2)}" if risk_v > 0 else "1:2.0"

            return {
                "symbol": symbol,
                "name": weekly_data.get("name", symbol),
                "sector": weekly_data.get("sector", "Equities"),
                "mcap_tier": mcap_tier,
                "mcap_cr": round(mcap_cr, 0),
                "archetype": archetype,
                "archetype_short": archetype_short,
                "cmp": cmp,
                "change_pct": round(float(candles["Close"].pct_change().iloc[-1] * 100), 2) if len(candles) >= 2 else 0.0,
                "ret_3m": weekly_data.get("ret_3m", 0.0),
                "ret_6m": weekly_data.get("ret_6m", 0.0),
                "ret_1y": weekly_data.get("ret_1y", 0.0),
                "ret_3y": weekly_data.get("ret_3y", 0.0),
                "rs_vs_nifty_6m": weekly_data.get("rs_vs_nifty_6m", 0.0),
                "tech_score": tech_score,
                "fund_score": fund_score,
                "quality_score": quality_score,
                "inflection_score": inflection_score,
                "conviction_score": multibagger_score,
                "roce_pct": roce_num,
                "roe_pct": roe_num,
                "pe": pe_num,
                "peg_ratio": peg_num,
                "debt_to_equity": de_ratio,
                "opm_latest_pct": opm_latest,
                "opm_expansion_bps": opm_exp_bps,
                "qtr_sales_yoy_pct": qtr_sales_yoy,
                "qtr_pat_yoy_pct": qtr_pat_yoy,
                "cfo_ebitda_pct": cfo_ebitda,
                "inst_4q_delta_pct": inst_delta,
                "sales_cagr_3y": ranges.get("sales_cagr_3y"),
                "profit_cagr_3y": ranges.get("profit_cagr_3y"),
                "rsi": tech_res.get("rsi", 55.0),
                "weekly_rsi": weekly_data.get("weekly_rsi", 55.0),
                "ema_20": round(ema_20, 2),
                "ema_50": round(ema_50, 2),
                "ema_200": round(ema_200, 2),
                "ema_40w": weekly_data.get("ema_40w", round(ema_200, 2)),
                "volume_surge": tech_res.get("volume_ratio", 1.0),
                "weekly_vol_surge": weekly_data.get("volume_surge", 1.0),
                "is_vcp_tight": weekly_data.get("is_vcp_tight", False),
                "distance_from_52w_high_pct": weekly_data.get("distance_from_52w_high", 0.0),
                "suggested_entry": f"₹{entry_low} — ₹{entry_high}",
                "stop_loss": stop_loss,
                "target_1": target_1,
                "target_2": target_2,
                "risk_reward": rr,
                "bullish_signals": (tech_res.get("bullish_signals", []) + [weekly_data.get("trend_status", "")])[:4],
                "fundamental_strengths": fund_res.get("strengths", [])[:4],
            }
        except Exception:
            return None

    def scan_market(
        self,
        max_stocks: int = 509,
        max_workers: int = 6,
        pass2_limit: int = 160,
        force_refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Executes Two-Pass Whole-Market Scan across up to 509+ NSE stocks:
        1. Pass 1: Weekly Stage-2, RS vs Nifty 50 & VCP base pre-filter across full universe.
        2. Pass 2: Deep Screener consolidated fundamental + inflection scoring on top survivors.
        """
        universe = self.load_stock_universe()[:max_stocks]
        priority_syms = {p["symbol"] for p in self.PRIORITY_MOMENTUM_STOCKS}

        weekly_universe = self.momentum_screener.scan_full_nse_weekly(universe, force_refresh=force_refresh)
        survivors = [w for w in weekly_universe if self._qualifies_pass1_candidate(w, w["symbol"] in priority_syms)]

        # Prioritize Turnaround/RS leaders + priority stocks up to pass2_limit
        survivors.sort(
            key=lambda w: (
                1 if w["symbol"] in priority_syms else 0,
                w.get("rs_vs_nifty_6m", 0.0) + (8.0 if w.get("is_vcp_tight") else 0.0) + (w.get("ret_3m", 0.0) * 0.4),
            ),
            reverse=True,
        )
        candidates = survivors[:pass2_limit]

        bullish_results: List[Dict[str, Any]] = []
        # Rate-polite worker pool (Screener cache absorbs most repeat runs cleanly)
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, 6)) as executor:
            futures = {executor.submit(self._pass2_deep_audit, w): w["symbol"] for w in candidates}
            for fut in concurrent.futures.as_completed(futures):
                res = fut.result()
                if res is not None:
                    bullish_results.append(res)

        bullish_results.sort(
            key=lambda x: (x["conviction_score"], x.get("inflection_score", 5.0), x.get("rs_vs_nifty_6m", 0.0)),
            reverse=True,
        )
        return bullish_results
