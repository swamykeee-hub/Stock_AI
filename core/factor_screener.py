import json
import time
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Optional
import config
from core.momentum_screener import MomentumScreener
from core.fundamental_analyst import FundamentalAnalyst, parse_float_safe


class SmartFactorScreener:
    """
    Dedicated 5-Factor Value & Growth Inflection Screener across the full 509-stock NSE universe:
    1. Volume Increasing (4W volume expansion / weekly surge)
    2. Promoter Shares Increasing (QoQ / 4Q promoter holding delta + FII/DII accumulation)
    3. QoQ & YoY High Profit Growth (Net Profit QoQ & YoY acceleration)
    4. ROCE & ROE Increased (Historical ROCE delta from #ratios + ROE expansion vs 3Y average)
    5. Trading Under Low Valuation (Low P/E, Low PEG GARP, Reasonable P/B, or Discount off 52W High)
    """

    CACHE_FILE = config.CACHE_DIR / "factor_screener_cache.json"
    SCHEMA_VERSION = 1

    def __init__(self):
        self.momentum_screener = MomentumScreener()
        self.fund_analyst = FundamentalAnalyst()
        self.nse_catalog_path = config.DATA_DIR / "nse_stocks.json"
        self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _load_full_universe(self) -> List[Dict[str, str]]:
        if not self.nse_catalog_path.exists():
            return []
        try:
            with open(self.nse_catalog_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    @staticmethod
    def _build_factor_row(w: Dict[str, Any], fund: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Combines weekly volume/price metrics with consolidated Screener fundamentals into a 5-factor row."""
        sym = w.get("symbol", "")
        cmp = float(w.get("cmp", 0.0))
        if not sym or cmp <= 0:
            return None

        dist_52w = float(w.get("distance_from_52w_high", 0.0))
        vol_surge = float(w.get("volume_surge", 1.0))
        vol_trend_4w = float(w.get("vol_trend_4w", vol_surge))
        vol_increasing = bool(vol_trend_4w >= 1.10 or vol_surge >= 1.25)

        metrics = fund.get("metrics", {})
        ranges = fund.get("ranges", {})
        inf = fund.get("inflection", {})
        bi = fund.get("balance_inst", {})

        # Promoter & Institutional accumulation
        promoter_pct = bi.get("promoter_pct")
        prom_pct_val = round(float(promoter_pct), 2) if promoter_pct is not None else 0.0
        prom_qoq = float(bi.get("promoter_qoq_delta_pct") or 0.0)
        prom_4q = float(bi.get("promoter_4q_delta_pct") or 0.0)
        promoter_increasing = bool(prom_qoq > 0.01 or prom_4q > 0.05)

        inst_total = float(bi.get("inst_total_pct") or 0.0)
        inst_4q_delta = float(bi.get("inst_4q_delta_pct") or 0.0)
        smart_money_up = bool(promoter_increasing or inst_4q_delta >= 0.75)

        # QoQ & YoY Profit Growth
        qtr_pat_qoq = inf.get("qtr_pat_qoq_pct")
        qtr_pat_yoy = inf.get("qtr_pat_yoy_pct")
        qtr_sales_yoy = inf.get("qtr_sales_yoy_pct")
        opm_latest = inf.get("opm_latest_pct")
        opm_exp_bps = inf.get("opm_expansion_bps")

        pat_qoq_high = bool(qtr_pat_qoq is not None and qtr_pat_qoq >= 10.0)
        pat_yoy_high = bool(qtr_pat_yoy is not None and qtr_pat_yoy >= 20.0)
        high_profit_growth = bool(
            (pat_qoq_high and pat_yoy_high)
            or (qtr_pat_yoy is not None and qtr_pat_yoy >= 25.0 and (qtr_pat_qoq or 0) > 0.0)
        )

        # ROCE & ROE Increasing
        roce_latest = parse_float_safe(metrics.get("roce_pct")) or 0.0
        roce_prev = bi.get("roce_prev_pct")
        roce_delta = bi.get("roce_delta_pct")
        if roce_delta is None and roce_prev is not None and roce_latest > 0:
            roce_delta = round(roce_latest - roce_prev, 1)

        roe_latest = parse_float_safe(metrics.get("roe_pct")) or 0.0
        roe_3y = ranges.get("roe_3y")
        roe_delta = round(roe_latest - roe_3y, 1) if (roe_latest > 0 and roe_3y is not None) else None

        roce_up = bool(roce_delta is not None and roce_delta > 0.0)
        roe_up = bool(roe_delta is not None and roe_delta > 0.0)
        roce_roe_increased = bool(
            (roce_up and roe_up)
            or ((roce_delta or 0) >= 1.5 and roce_latest >= 14.0)
            or ((roe_delta or 0) >= 1.5 and roe_latest >= 14.0)
        )

        # Trading Under Low Value (Undervalued / Low Multiple / Discounted GARP)
        pe = parse_float_safe(metrics.get("stock_pe")) or 0.0
        pb = parse_float_safe(metrics.get("pb_ratio")) or 0.0
        peg = parse_float_safe(metrics.get("peg_ratio"))
        de_ratio = parse_float_safe(metrics.get("debt_to_equity"))
        mcap_cr = parse_float_safe(metrics.get("market_cap_cr")) or 0.0

        is_low_pe = bool(0 < pe <= 28.0)
        is_low_peg = bool(peg is not None and 0 < peg <= 1.35)
        is_low_pb_quality = bool(0 < pb <= 4.2 and roe_latest >= 14.0)
        is_discounted_peak = bool(dist_52w >= 12.0)
        undervalued = bool(
            is_low_peg
            or is_low_pe
            or is_low_pb_quality
            or (is_discounted_peak and (peg is None or peg <= 2.0) and (pe == 0 or pe <= 45.0))
        )

        if is_low_peg and is_low_pe:
            valuation_tag = "💎 Deep Undervalued GARP"
        elif is_low_pe or is_low_peg:
            valuation_tag = "🏷️ Undervalued / Low Multiple"
        elif is_discounted_peak and (roce_roe_increased or pat_yoy_high):
            valuation_tag = "🎯 Discounted Turnaround"
        else:
            valuation_tag = "⚖️ Premium Multiple"

        # 5-Factor Match Count & Score
        core_flags = [vol_increasing, promoter_increasing, high_profit_growth, roce_roe_increased, undervalued]
        matches_count = sum(1 for f in core_flags if f)

        # Require at least 2 active signals to keep noise out of the dedicated screener
        if matches_count < 2 and not (smart_money_up and pat_yoy_high):
            return None

        score = 3.0 + (matches_count * 1.15)
        if pat_qoq_high and pat_yoy_high:
            score += 0.6
        if roce_up and roe_up:
            score += 0.5
        if promoter_increasing:
            score += 0.6
        elif inst_4q_delta >= 1.5:
            score += 0.4
        if vol_trend_4w >= 1.25:
            score += 0.4
        if is_low_peg and peg <= 1.0:
            score += 0.5
        if de_ratio is not None and de_ratio > 1.5 and not bi.get("is_financial_sector"):
            score -= 0.8

        factor_score = max(1.0, min(round(score, 1), 10.0))

        return {
            "symbol": sym,
            "name": w.get("name", sym),
            "sector": w.get("sector", "Equities"),
            "cmp": cmp,
            "h52": w.get("fifty_two_week_high", cmp),
            "dist_52w": dist_52w,
            "ret_3m": w.get("ret_3m", 0.0),
            "ret_1y": w.get("ret_1y", 0.0),
            "pe": pe,
            "pb": pb,
            "peg": peg,
            "mcap_cr": round(mcap_cr, 0),
            "debt_to_equity": de_ratio,
            # Factor 1: Volume
            "vol_surge": vol_surge,
            "vol_trend_4w": vol_trend_4w,
            "flag_vol": vol_increasing,
            # Factor 2: Promoter / Smart Money
            "promoter_pct": prom_pct_val,
            "promoter_qoq_delta": round(prom_qoq, 2),
            "promoter_4q_delta": round(prom_4q, 2),
            "inst_total_pct": round(inst_total, 2),
            "inst_4q_delta": round(inst_4q_delta, 2),
            "flag_promoter": promoter_increasing,
            "flag_smart_money": smart_money_up,
            # Factor 3: QoQ & YoY High Profit Growth
            "qtr_pat_qoq_pct": qtr_pat_qoq,
            "qtr_pat_yoy_pct": qtr_pat_yoy,
            "qtr_sales_yoy_pct": qtr_sales_yoy,
            "opm_latest_pct": opm_latest,
            "opm_expansion_bps": opm_exp_bps,
            "flag_pat_qoq": pat_qoq_high,
            "flag_pat_yoy": pat_yoy_high,
            "flag_profit_high": high_profit_growth,
            # Factor 4: ROCE & ROE Increased
            "roce_latest": roce_latest,
            "roce_prev": roce_prev,
            "roce_delta": roce_delta,
            "roe_latest": roe_latest,
            "roe_3y": roe_3y,
            "roe_delta": roe_delta,
            "flag_roce_up": roce_up,
            "flag_roe_up": roe_up,
            "flag_eff_up": roce_roe_increased,
            # Factor 5: Low Valuation
            "flag_low_value": undervalued,
            "valuation_tag": valuation_tag,
            # Composite Summary
            "matches_count": matches_count,
            "factor_score": factor_score,
        }

    def scan_factors(self, max_candidates: int = 240, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Screens all liquid NSE 509 stocks for Volume Surge, Promoter Buying, QoQ/YoY PAT Growth,
        ROCE/ROE Expansion, and Low Valuation / Discounted Value.
        """
        if not force_refresh and self.CACHE_FILE.exists():
            try:
                if (time.time() - self.CACHE_FILE.stat().st_mtime) < 10800:
                    with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                        if (
                            isinstance(cached, dict)
                            and cached.get("schema_version") == self.SCHEMA_VERSION
                            and cached.get("stocks")
                        ):
                            return cached["stocks"]
            except Exception:
                pass

        universe = self._load_full_universe()
        weekly_list = self.momentum_screener.scan_full_nse_weekly(universe, force_refresh=force_refresh)

        # Include liquid stocks showing rising volume, value discounts, or already in cached/curated leaders
        curated_syms = {s["symbol"] for s in self.momentum_screener.curated_momentum_universe}
        prioritized = []
        others = []
        for w in weekly_list:
            if w.get("avg_daily_turnover_cr", 0.0) < 1.0:
                continue
            has_vol_or_val = (
                w.get("vol_trend_4w", 1.0) >= 1.05
                or w.get("volume_surge", 1.0) >= 1.10
                or w.get("distance_from_52w_high", 0.0) >= 12.0
                or w["symbol"] in curated_syms
            )
            if has_vol_or_val:
                prioritized.append(w)
            else:
                others.append(w)

        # Balance selection so undervalued/volume candidates + all curated leaders get audited
        prioritized.sort(
            key=lambda x: (
                1 if x["symbol"] in curated_syms else 0,
                max(x.get("vol_trend_4w", 1.0), x.get("volume_surge", 1.0))
                + (0.5 if 12.0 <= x.get("distance_from_52w_high", 0.0) <= 45.0 else 0.0),
            ),
            reverse=True,
        )
        pool = (prioritized + others)[:max_candidates]

        results: List[Dict[str, Any]] = []

        def _audit_one(w_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
            fund = self.fund_analyst.analyze(w_item["symbol"])
            return self._build_factor_row(w_item, fund)

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(_audit_one, item) for item in pool]
            for fut in concurrent.futures.as_completed(futures):
                try:
                    row = fut.result()
                    if row is not None:
                        results.append(row)
                except Exception:
                    pass

        results.sort(
            key=lambda x: (x["matches_count"], x["factor_score"], x.get("qtr_pat_yoy_pct") or -999.0),
            reverse=True,
        )

        try:
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "schema_version": self.SCHEMA_VERSION,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "total_found": len(results),
                        "stocks": results,
                    },
                    f,
                    indent=2,
                )
        except Exception:
            pass

        return results
