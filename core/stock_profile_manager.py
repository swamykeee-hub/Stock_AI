import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
import pandas as pd
import concurrent.futures
from core.market_data import MarketDataManager
from core.technical_analyst import TechnicalAnalyst
from core.fundamental_analyst import FundamentalAnalyst, parse_float_safe


class StockProfileManager:
    """
    Manages and caches comprehensive 360-degree stock intelligence profiles
    (CMP, Technicals, Consolidated Fundamentals, Inflection Signals, Actionable Buy Entry Setup,
    and Senior Fund Manager Strategy) for benchmark NSE stocks and searched tickers.
    """

    from config import CACHE_DIR, DATA_DIR
    CACHE_FILE = CACHE_DIR / "enriched_stock_profiles.json"
    TOP_100_FILE = DATA_DIR / "top_100_curated_stocks.json"
    SCHEMA_VERSION = 2

    KEY_BENCHMARK_STOCKS = []
    if TOP_100_FILE.exists():
        try:
            with open(TOP_100_FILE, "r", encoding="utf-8") as _f:
                KEY_BENCHMARK_STOCKS = json.load(_f)
        except Exception:
            KEY_BENCHMARK_STOCKS = []

    def __init__(self):
        self.market_data = MarketDataManager()
        self.tech_analyst = TechnicalAnalyst()
        self.fund_analyst = FundamentalAnalyst()
        self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    def build_single_profile(self, item: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Extracts complete CMP, Technicals, Consolidated Fundamentals, Inflection, and Buy Entry setup."""
        sym = item["symbol"]
        formatted_sym = self.market_data.format_symbol(sym)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{formatted_sym}?range=1y&interval=1d"

        try:
            r = requests.get(url, headers=self.market_data.HEADERS, timeout=8)
            if r.status_code != 200:
                return None

            data = r.json()
            res = data.get("chart", {}).get("result", [{}])[0]
            meta = res.get("meta", {})
            timestamps = res.get("timestamp", [])
            q = res.get("indicators", {}).get("quote", [{}])[0]

            if not timestamps or not q.get("close"):
                return None

            df = pd.DataFrame({
                "Date": pd.to_datetime(timestamps, unit="s"),
                "Open": q.get("open", []),
                "High": q.get("high", []),
                "Low": q.get("low", []),
                "Close": q.get("close", []),
                "Volume": q.get("volume", [])
            }).dropna(subset=["Close"]).reset_index(drop=True)

            if len(df) < 30:
                return None

            cmp = round(meta.get("regularMarketPrice") or float(df["Close"].iloc[-1]), 2)
            prev_close = meta.get("chartPreviousClose", cmp)
            chg = meta.get("fulldayChange") or (cmp - prev_close)
            chg_pct = meta.get("regularMarketChangePercent") or round(((chg / (prev_close + 1e-6)) * 100), 2)
            h52 = round(meta.get("fiftyTwoWeekHigh", float(df["High"].max())), 2)
            l52 = round(meta.get("fiftyTwoWeekLow", float(df["Low"].min())), 2)
            dist_52w = round(((h52 - cmp) / (h52 + 1e-6)) * 100, 1)

            c_first = float(df["Close"].iloc[0])
            ret_1y = round(((cmp - c_first) / (c_first + 1e-6)) * 100, 1)

            # Technical Analysis
            tech_res = self.tech_analyst.analyze(df)
            tech_score = float(tech_res.get("score", 5.0))
            rsi = tech_res.get("rsi", 50.0)
            ema_20 = tech_res.get("ema_20", cmp)
            ema_50 = tech_res.get("ema_50", cmp)
            ema_200 = tech_res.get("ema_200", cmp)
            atr = tech_res.get("atr", cmp * 0.02)
            levels = tech_res.get("levels", {})

            # Consolidated Fundamental & Inflection Analysis
            fund_res = self.fund_analyst.analyze(sym)
            metrics = fund_res.get("metrics", {})
            ranges = fund_res.get("ranges", {})
            inflection = fund_res.get("inflection", {})
            balance_inst = fund_res.get("balance_inst", {})

            fund_score = float(fund_res.get("score", 5.0))
            quality_score = float(fund_res.get("quality_score", 5.0))
            inflection_score = float(fund_res.get("inflection_score", 5.0))

            raw_roce = str(metrics.get("roce_pct", "N/A"))
            raw_pe = str(metrics.get("stock_pe", "N/A"))
            raw_roe = str(metrics.get("roe_pct", "N/A"))
            mcap_num = parse_float_safe(metrics.get("market_cap_cr"))
            mcap = f"{int(round(mcap_num))}" if mcap_num is not None else "N/A"
            raw_de = str(metrics.get("debt_to_equity", "N/A"))
            raw_peg = str(metrics.get("peg_ratio", "N/A"))

            opm_latest = inflection.get("opm_latest_pct")
            opm_exp_bps = inflection.get("opm_expansion_bps")
            qtr_pat_yoy = inflection.get("qtr_pat_yoy_pct")
            inst_delta = balance_inst.get("inst_4q_delta_pct", 0.0)
            cfo_ebitda = balance_inst.get("cfo_ebitda_pct")

            # Long-Term Wealth Score (65% Fundamentals/Inflection, 35% Trend & Multi-Year Return)
            mom_norm = 5.0
            if ret_1y >= 80:
                mom_norm = 9.2
            elif ret_1y >= 40:
                mom_norm = 8.4
            elif ret_1y >= 15:
                mom_norm = 7.2
            elif ret_1y < -15:
                mom_norm = 3.5

            long_term_score = round(
                min(10.0, max(1.0, (fund_score * 0.65) + (((tech_score * 0.5) + (mom_norm * 0.5)) * 0.35))),
                1
            )

            # Actionable Buy Entry Setup (20/50 EMA pocket + Long-term / Structural targets)
            entry_low = round(min(cmp * 0.98, ema_20 * 0.995), 2)
            entry_high = round(cmp * 1.005, 2)
            # Tactical targets use max of ATR expansion or 12%/28% structural runway for Stage-2 leaders
            target_1 = round(max(levels.get("target_1", cmp * 1.08), cmp * 1.12), 2)
            target_2 = round(max(levels.get("target_2", cmp * 1.18), cmp * 1.28), 2)
            stop_loss = round(min(levels.get("stop_loss", cmp * 0.94), ema_50 * 0.985), 2)
            risk_v = cmp - stop_loss
            rew_v = target_1 - cmp
            rr = f"1:{round(rew_v / (risk_v + 1e-6), 2)}" if risk_v > 0 else "1:2.0"

            # Trend Posture
            if cmp > ema_200 and cmp > ema_20:
                trend_posture = "Above 20 EMA & 200 EMA (Stage-2 Uptrend Intact)"
            elif cmp > ema_200:
                trend_posture = "Consolidating above 200 EMA (Structural Floor Intact)"
            else:
                trend_posture = "Below 200 EMA (Cyclical Base-Building)"

            # Systematic classification (no hardcoded ticker exceptions)
            is_inflection_leader = (
                (opm_exp_bps is not None and opm_exp_bps >= 150)
                and (qtr_pat_yoy is not None and qtr_pat_yoy >= 20.0)
                and cmp >= ema_50
            )
            is_stage2_leader = (cmp > ema_200 and ret_1y >= 25.0 and dist_52w <= 15.0)
            is_quality_compounder = (fund_score >= 7.0 and cmp >= ema_200)
            is_bullish = bool(is_inflection_leader or is_stage2_leader or (is_quality_compounder and ret_1y > 0))

            opm_str = f"{opm_latest:.0f}%" if opm_latest is not None else "N/A"
            opm_exp_str = f" ({opm_exp_bps:+.0f} bps YoY)" if opm_exp_bps is not None else ""
            pat_str = f"{qtr_pat_yoy:+.1f}% YoY" if qtr_pat_yoy is not None else "N/A"
            inst_str = f"{inst_delta:+.1f}%" if inst_delta else "0.0%"

            if is_inflection_leader and is_stage2_leader:
                status_badge = "🚀 Multibagger Inflection / Stage-2 Leader"
                badge_bg = "#059669"
                strategy_exp = (
                    f"<b>• Laurus-Type Operating Leverage Inflection:</b> {sym} combines sustained institutional momentum "
                    f"(1Y: <b>{ret_1y:+.1f}%</b>, {dist_52w}% off 52W High) with sharp fundamental acceleration "
                    f"(Quarterly PAT: <b>{pat_str}</b>, OPM: <b>{opm_str}{opm_exp_str}</b>, FII+DII 4Q Flow: <b>{inst_str}</b>). "
                    f"Accumulate in tranches across <b>₹{entry_low} — ₹{entry_high}</b> (near 20-EMA), "
                    f"holding with 200-EMA structural floor at <b>₹{ema_200}</b> targeting <b>₹{target_1}</b> and <b>₹{target_2}</b>."
                )
            elif is_stage2_leader:
                status_badge = "🔥 Bullish Momentum / Stage-2 Leader"
                badge_bg = "#16a34a"
                strategy_exp = (
                    f"<b>• High-Conviction Compounder Strategy:</b> {sym} demonstrates Stage-2 institutional accumulation "
                    f"(1-Year return: <b>{ret_1y:+.1f}%</b>, within {dist_52w}% of 52-week peak) backed by ROCE {raw_roce}%. "
                    f"Optimal entry is on shallow pullbacks toward <b>₹{entry_low} — ₹{entry_high}</b> near the 20-day EMA. "
                    f"Trail protective stop at <b>₹{stop_loss}</b> targeting <b>₹{target_1}</b> and <b>₹{target_2}</b>."
                )
            elif is_inflection_leader:
                status_badge = "⚡ Early Turnaround Inflection Watch"
                badge_bg = "#0284c7"
                strategy_exp = (
                    f"<b>• Early Inflection Setup:</b> {sym} shows fundamental margin/earnings inflection before extended price crowds in "
                    f"(Quarterly PAT: <b>{pat_str}</b>, OPM: <b>{opm_str}{opm_exp_str}</b>, 1Y: <b>{ret_1y:+.1f}%</b>). "
                    f"Gradual long-term accumulation across <b>₹{entry_low} — ₹{entry_high}</b> with strict support at <b>₹{stop_loss}</b>."
                )
            elif is_quality_compounder:
                status_badge = "🏛️ Quality Compounder / Accumulation"
                badge_bg = "#2563eb"
                strategy_exp = (
                    f"<b>• Quality GARP Accumulation:</b> {sym} holds elite fundamentals (ROCE: {raw_roce}%, D/E: {raw_de}x, PEG: {raw_peg}) "
                    f"while maintaining its 200-day EMA structural uptrend (₹{ema_200}). Accumulate on dips across <b>₹{entry_low} — ₹{entry_high}</b> "
                    f"for 3–5 year wealth compounding toward <b>₹{target_1}</b> and <b>₹{target_2}</b>."
                )
            else:
                status_badge = "⏸️ Consolidation / Base-Building"
                badge_bg = "#4338ca"
                strategy_exp = (
                    f"<b>• Base-Building / Value Strategy:</b> {sym} trades at P/E {raw_pe}x (ROCE: {raw_roce}%, D/E: {raw_de}x) with 1-Year return of "
                    f"<b>{ret_1y:+.1f}%</b> ({dist_52w}% below 52W high). Patient long-term investors may stagger buys near structural support "
                    f"(200-EMA ₹{ema_200}), while momentum investors should wait for a volume-backed close above <b>₹{target_1}</b>."
                )

            return {
                "schema_version": self.SCHEMA_VERSION,
                "symbol": sym,
                "name": item.get("name", meta.get("shortName", sym)),
                "sector": item.get("sector", "Equities"),
                "cmp": cmp,
                "change": round(chg, 2),
                "change_pct": round(chg_pct, 2),
                "h52": h52,
                "l52": l52,
                "dist_52w": dist_52w,
                "ret_1y": ret_1y,
                "rsi": round(rsi, 1),
                "ema_20": round(ema_20, 2),
                "ema_50": round(ema_50, 2),
                "ema_200": round(ema_200, 2),
                "trend_posture": trend_posture,
                "pe": raw_pe,
                "roce": raw_roce,
                "roe": raw_roe,
                "pb": str(metrics.get("pb_ratio", "N/A")),
                "peg": raw_peg,
                "debt_to_equity": raw_de,
                "opm_latest": opm_str,
                "opm_expansion_bps": opm_exp_bps,
                "qtr_pat_yoy_pct": qtr_pat_yoy,
                "fii_dii_delta_pct": inst_delta,
                "cfo_ebitda_pct": cfo_ebitda,
                "sales_cagr_3y": ranges.get("sales_cagr_3y"),
                "profit_cagr_3y": ranges.get("profit_cagr_3y"),
                "market_cap_cr": mcap,
                "fund_score": fund_score,
                "quality_score": quality_score,
                "inflection_score": inflection_score,
                "long_term_score": long_term_score,
                "is_bullish": is_bullish,
                "entry_low": entry_low,
                "entry_high": entry_high,
                "suggested_entry": f"₹{entry_low} — ₹{entry_high}",
                "target_1": target_1,
                "target_2": target_2,
                "stop_loss": stop_loss,
                "risk_reward": rr,
                "status_badge": status_badge,
                "badge_bg": badge_bg,
                "buy_entry_strategy": strategy_exp
            }
        except Exception:
            return None

    def build_all_benchmark_profiles(self, max_workers: int = 6) -> Dict[str, Dict[str, Any]]:
        """Pre-computes and caches enriched profiles for benchmark stocks."""
        profiles: Dict[str, Dict[str, Any]] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_stock = {executor.submit(self.build_single_profile, s): s["symbol"] for s in self.KEY_BENCHMARK_STOCKS}
            for future in concurrent.futures.as_completed(future_to_stock):
                res = future.result()
                if res is not None:
                    profiles[res["symbol"]] = res

        try:
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(profiles, f, indent=2)
        except Exception:
            pass

        return profiles

    def get_enriched_profiles(self, refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """Loads profiles from cache or triggers build if missing/expired/stale schema."""
        if not refresh and self.CACHE_FILE.exists():
            try:
                if (time.time() - self.CACHE_FILE.stat().st_mtime) < 10800:
                    with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        min_expected = max(10, int(len(self.KEY_BENCHMARK_STOCKS) * 0.6))
                        if isinstance(data, dict) and len(data) >= min_expected:
                            sample = next(iter(data.values()), {})
                            if sample.get("schema_version") == self.SCHEMA_VERSION:
                                return data
            except Exception:
                pass

        return self.build_all_benchmark_profiles()

    def get_or_build_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Gets profile for any symbol, building on-demand if not already cached."""
        clean_sym = symbol.strip().upper()
        profiles = self.get_enriched_profiles(refresh=False)
        if clean_sym in profiles:
            return profiles[clean_sym]

        prof = self.build_single_profile({"symbol": clean_sym, "name": clean_sym, "sector": "NSE Equities"})
        if prof:
            profiles[clean_sym] = prof
            try:
                with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(profiles, f, indent=2)
            except Exception:
                pass
        return prof
