import concurrent.futures
import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import config
from core.fundamental_analyst import FundamentalAnalyst, parse_float_safe
from core.market_data import MarketDataManager
from core.technical_analyst import TechnicalAnalyst

IST = timezone(timedelta(hours=5, minutes=30))


def _wilder_rsi(closes, period: int = 14) -> float:
    """Computes Wilder's RSI(14) safely from a pandas Series of close prices."""
    if len(closes) < period + 2:
        return 50.0
    delta = closes.diff()
    gain = delta.clip(lower=0.0).ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    loss = (-delta.clip(upper=0.0)).ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    rs = gain / (loss + 1e-9)
    val = (100.0 - (100.0 / (1.0 + rs))).iloc[-1]
    return round(float(val), 1) if val == val else 50.0


class HiddenGemsScreener:
    """
    Autonomous Small & Mid-Cap Hidden Gems Screener (Market Cap ₹500 – ₹35,000 Cr).

    Combines anti-bubble quality filters (ROCE >= 16%, ROE >= 14%, D/E <= 0.60x,
    3Y CFO/PAT >= 0.65x, P/E <= 88x, PEG <= 1.65x, Qtr Sales/PAT growth) with
    live technical alignment (20/50/200 EMAs, Wilder RSI, ATR targets & stop loss).

    Automatically refreshes prices, day change %, distance from 52W high,
    setup classification, and ranking as market prices move, and rotates newly
    qualifying NSE small/mid-caps in during full universe scans.
    """

    CACHE_FILE = Path(
        config.SCHEDULE_CONFIG.get("DAILY_HIDDEN_GEMS_FILE", config.CACHE_DIR / "hidden_gems_cache.json")
    )
    NSE_CATALOG = config.DATA_DIR / "nse_stocks.json"
    SMALL_CAP_MAX_CR = 15000.0
    MID_CAP_MAX_CR = 35000.0
    MIN_MCAP_CR = 500.0

    # Curated small & mid-cap hidden-gem seed universe merged with full NSE catalog
    HIDDEN_GEMS_SEED_STOCKS: List[Dict[str, str]] = [
        {"symbol": "FIEMIND", "name": "Fiem Industries Ltd.", "sector": "Automobile and Auto Components"},
        {"symbol": "SJS", "name": "SJS Enterprises Ltd.", "sector": "Automobile and Auto Components"},
        {"symbol": "BAJAJCON", "name": "Bajaj Consumer Care Ltd.", "sector": "Fast Moving Consumer Goods"},
        {"symbol": "MARKSANS", "name": "Marksans Pharma Ltd.", "sector": "Healthcare"},
        {"symbol": "IGIL", "name": "International Gemological Institute (India) Ltd.", "sector": "Services"},
        {"symbol": "KAJARIACER", "name": "Kajaria Ceramics Ltd.", "sector": "Consumer Durables"},
        {"symbol": "CEMPRO", "name": "Cemindia Projects Ltd.", "sector": "Construction"},
        {"symbol": "ACUTAAS", "name": "Acutaas Chemicals Ltd.", "sector": "Healthcare"},
        {"symbol": "STYLAMIND", "name": "Stylam Industries Ltd.", "sector": "Consumer Durables"},
        {"symbol": "SHAILY", "name": "Shaily Engineering Plastics Ltd.", "sector": "Capital Goods"},
        {"symbol": "HONASA", "name": "Honasa Consumer Ltd.", "sector": "Fast Moving Consumer Goods"},
        {"symbol": "RRKABEL", "name": "R R Kabel Ltd.", "sector": "Capital Goods"},
    ]

    def __init__(self):
        self.market_data = MarketDataManager()
        self.tech_analyst = TechnicalAnalyst()
        self.fund_analyst = FundamentalAnalyst()
        self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    def _load_catalog_map(self) -> Dict[str, Dict[str, str]]:
        """Loads NSE catalog merged with curated small/mid-cap seed stocks."""
        catalog: Dict[str, Dict[str, str]] = {}
        if self.NSE_CATALOG.exists():
            try:
                with open(self.NSE_CATALOG, "r", encoding="utf-8") as f:
                    for item in json.load(f):
                        sym = str(item.get("symbol", "")).strip().upper()
                        if sym:
                            catalog[sym] = {
                                "symbol": sym,
                                "name": item.get("name", sym),
                                "sector": item.get("sector", "Equities"),
                            }
            except Exception:
                pass
        for item in self.HIDDEN_GEMS_SEED_STOCKS:
            sym = item["symbol"].strip().upper()
            if sym not in catalog:
                catalog[sym] = dict(item)
        return catalog

    @classmethod
    def classify_cap_tier(cls, mcap_cr: float) -> str:
        """Categorizes market capitalization into Small Cap vs Mid Cap."""
        if mcap_cr <= 0:
            return "Small / Mid Cap"
        if mcap_cr < cls.SMALL_CAP_MAX_CR:
            return "Small Cap"
        if mcap_cr <= cls.MID_CAP_MAX_CR:
            return "Mid Cap"
        return "Large Cap"

    @classmethod
    def passes_fundamental_gate(cls, fund: Dict[str, Any], is_seed: bool = False) -> bool:
        """Applies Small/Mid-Cap quality, cash-conversion, growth, and anti-bubble valuation gates."""
        if not isinstance(fund, dict) or not fund.get("metrics"):
            return False

        m = fund.get("metrics", {})
        inf = fund.get("inflection", {})
        bi = fund.get("balance_inst", {})

        mcap_cr = parse_float_safe(m.get("market_cap_cr")) or 0.0
        pe = parse_float_safe(m.get("stock_pe")) or 0.0
        peg = parse_float_safe(m.get("peg_ratio"))
        roce = parse_float_safe(m.get("roce_pct")) or 0.0
        roe = parse_float_safe(m.get("roe_pct")) or 0.0
        de = bi.get("debt_to_equity")
        pledge = float(bi.get("promoter_pledge_pct") or 0.0)
        cfo_pat = bi.get("cfo_to_pat_3y")
        is_fin = bool(bi.get("is_financial_sector"))

        pat_yoy = inf.get("qtr_pat_yoy_pct")
        sales_yoy = inf.get("qtr_sales_yoy_pct")

        max_mcap = cls.MID_CAP_MAX_CR if not is_seed else 38000.0
        if not (cls.MIN_MCAP_CR <= mcap_cr <= max_mcap):
            return False
        if roce < 16.0 or roe < 14.0:
            return False
        if not is_fin and de is not None and de > 0.60:
            return False
        if pledge > 5.0:
            return False
        if not is_fin and cfo_pat is not None and cfo_pat < 0.65:
            return False
        if pe <= 0 or pe > 88.0:
            return False
        if peg is not None and peg > 1.65:
            return False

        has_growth = ((pat_yoy or 0.0) >= 12.0) or ((sales_yoy or 0.0) >= 15.0 and (pat_yoy or 0.0) >= 8.0)
        if not has_growth:
            return False

        return True

    @staticmethod
    def _evaluate_dynamic_setup(
        cmp: float,
        ema20: float,
        ema50: float,
        ema200: float,
        h52: float,
        rsi: float,
        atr: float,
        fund_score: float,
        roce: float,
        pe: float,
        peg: Optional[float],
        day_change_pct: float = 0.0,
        vol_ratio: float = 1.0,
    ) -> Dict[str, Any]:
        """Recomputes live setup status, entry pocket, targets, stop loss, and gem score from current price."""
        dist_52w = round(((h52 - cmp) / (h52 + 1e-6)) * 100.0, 2) if h52 > 0 else 0.0
        safe_atr = atr if atr > 0 else round(cmp * 0.025, 2)

        # Dynamic setup classification driven by live price vs EMAs & 52W High
        if rsi > 72.0 or (ema20 > 0 and cmp > ema20 * 1.12):
            setup_status = "⚠️ Extended — Wait for Dip"
            status_key = "extended"
            status_color = "#f59e0b"
            tech_pts = 6.2
            entry_low = round(max(ema20 * 0.99, cmp * 0.94), 2)
            entry_high = round(max(ema20 * 1.015, cmp * 0.97), 2)
        elif cmp >= ema20 and ema20 >= ema50 * 0.995 and cmp >= ema200 and dist_52w <= 10.0:
            setup_status = "🔥 Stage-2 Breakout"
            status_key = "breakout"
            status_color = "#10b981"
            tech_pts = 8.6 + (0.6 if vol_ratio >= 1.25 else 0.0) + (0.4 if day_change_pct > 1.0 else 0.0)
            entry_low = round(max(ema20 * 0.99, cmp * 0.97), 2)
            entry_high = round(cmp * 1.005, 2)
        elif cmp >= ema200 * 0.98 and (cmp >= ema50 * 0.97 or (ema20 > 0 and abs(cmp - ema20) / ema20 <= 0.045)):
            setup_status = "🎯 Pullback Buy (EMA Support)"
            status_key = "pullback"
            status_color = "#38bdf8"
            tech_pts = 7.6 + (0.5 if 45.0 <= rsi <= 62.0 else 0.0)
            entry_low = round(min(cmp * 0.985, ema20 if ema20 > 0 else cmp * 0.97), 2)
            entry_high = round(cmp * 1.005, 2)
        else:
            setup_status = "🌱 Base Reclaim / Turnaround Watch"
            status_key = "turnaround"
            status_color = "#a78bfa"
            tech_pts = 5.4 + (0.8 if day_change_pct >= 1.5 and vol_ratio >= 1.2 else 0.0)
            reclaim_lvl = round(max(ema20, cmp * 1.01), 2)
            entry_low = round(cmp * 0.98, 2)
            entry_high = reclaim_lvl

        target_1 = round(max(cmp + (2.4 * safe_atr), cmp * 1.12), 2)
        target_2 = round(max(cmp + (4.5 * safe_atr), cmp * 1.28), 2)
        stop_loss = round(min(cmp - (1.8 * safe_atr), (ema50 * 0.97 if cmp >= ema50 else cmp * 0.91)), 2)
        if stop_loss >= cmp:
            stop_loss = round(cmp * 0.92, 2)

        risk = max(0.01, cmp - stop_loss)
        reward = max(0.01, target_1 - cmp)
        rr_ratio = f"1:{round(reward / risk, 2)}"

        # Live Gem Score (blends Fundamental Quality 55%, Live Technical Structure 30%, GARP Value 15%)
        val_pts = 8.5 if (pe <= 26.0 or (peg is not None and peg <= 0.6)) else (7.0 if pe <= 40.0 else 5.2)
        roce_bonus = 0.4 if roce >= 28.0 else 0.0
        tech_clamped = max(1.0, min(round(tech_pts, 1), 10.0))
        gem_score = max(
            1.0,
            min(round((fund_score * 0.55) + (tech_clamped * 0.30) + (val_pts * 0.15) + roce_bonus, 1), 10.0),
        )

        return {
            "dist_52w": dist_52w,
            "setup_status": setup_status,
            "status_key": status_key,
            "status_color": status_color,
            "tech_score": tech_clamped,
            "gem_score": gem_score,
            "suggested_entry": f"₹{entry_low:,.2f} — ₹{entry_high:,.2f}",
            "target_1": target_1,
            "target_2": target_2,
            "stop_loss": stop_loss,
            "risk_reward": rr_ratio,
        }

    def _collect_candidate_pool(self) -> List[Dict[str, Any]]:
        """Collects seed gems plus any qualifying small/mid-caps from fundamentals cache."""
        catalog = self._load_catalog_map()
        seed_syms = {s["symbol"].upper() for s in self.HIDDEN_GEMS_SEED_STOCKS}
        pool: Dict[str, Dict[str, Any]] = {}

        # 1. Always audit curated seed small/mid-cap gems
        for sym in seed_syms:
            meta = catalog.get(sym, {"symbol": sym, "name": sym, "sector": "Equities"})
            fund = self.fund_analyst.analyze(sym)
            if self.passes_fundamental_gate(fund, is_seed=True):
                pool[sym] = {"meta": meta, "fund": fund, "is_seed": True}

        # 2. Scan cached Screener fundamental audits across the 509+ NSE universe for rotating discoveries
        fund_dir = self.fund_analyst.CACHE_DIR
        if fund_dir.exists():
            for fp in fund_dir.glob("*.json"):
                sym = fp.stem.upper()
                if sym in pool:
                    continue
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        fund = json.load(f)
                    if self.passes_fundamental_gate(fund, is_seed=False):
                        meta = catalog.get(sym, {"symbol": sym, "name": sym, "sector": "Equities"})
                        pool[sym] = {"meta": meta, "fund": fund, "is_seed": False}
                except Exception:
                    continue

        return list(pool.values())

    def _audit_gem_live(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Combines verified fundamental audit with live market price & technical structure."""
        meta = item["meta"]
        fund = item["fund"]
        sym = meta["symbol"]

        try:
            q = self.market_data.get_quote_and_overview(sym)
            df = self.market_data.get_historical_candles(sym, period="1y", interval="1d")
            cmp = float(q.get("currentPrice") or 0.0)
            if cmp <= 0 and not df.empty:
                cmp = float(df["Close"].iloc[-1])
            if cmp <= 0:
                return None

            h52 = float(q.get("fiftyTwoWeekHigh") or (df["High"].max() if not df.empty else cmp))
            l52 = float(q.get("fiftyTwoWeekLow") or (df["Low"].min() if not df.empty else cmp))
            day_chg = float(q.get("change") or 0.0)
            day_chg_pct = float(q.get("changePercent") or 0.0)

            tech = self.tech_analyst.analyze(df) if (not df.empty and len(df) >= 30) else {}
            ema20 = float(tech.get("ema_20") or round(cmp * 0.98, 2))
            ema50 = float(tech.get("ema_50") or round(cmp * 0.95, 2))
            ema200 = float(tech.get("ema_200") or round(cmp * 0.90, 2))
            atr = float(tech.get("atr") or round(cmp * 0.025, 2))
            vol_ratio = float(tech.get("volume_ratio") or 1.0)
            rsi = _wilder_rsi(df["Close"], 14) if not df.empty else 50.0

            ret_1m = 0.0
            ret_3m = 0.0
            ret_1y = 0.0
            if not df.empty and len(df) >= 2:
                closes = df["Close"]
                ret_1m = round(((cmp / float(closes.iloc[-min(22, len(closes))])) - 1.0) * 100.0, 1)
                ret_3m = round(((cmp / float(closes.iloc[-min(64, len(closes))])) - 1.0) * 100.0, 1)
                ret_1y = round(((cmp / float(closes.iloc[0])) - 1.0) * 100.0, 1)

            m = fund.get("metrics", {})
            inf = fund.get("inflection", {})
            bi = fund.get("balance_inst", {})

            # Recompute dynamic MCap & P/E scaling if CMP drifted materially from Screener baseline
            base_cmp = parse_float_safe(m.get("current_price")) or cmp
            base_mcap = parse_float_safe(m.get("market_cap_cr")) or 0.0
            base_pe = parse_float_safe(m.get("stock_pe")) or 0.0
            price_ratio = (cmp / base_cmp) if base_cmp > 0 else 1.0
            live_mcap = round(base_mcap * price_ratio, 0) if base_mcap > 0 else 0.0
            live_pe = round(base_pe * price_ratio, 1) if base_pe > 0 else 0.0
            peg = parse_float_safe(m.get("peg_ratio"))
            if peg is not None and base_pe > 0 and live_pe > 0:
                peg = round(peg * (live_pe / base_pe), 2)

            roce = parse_float_safe(m.get("roce_pct")) or 0.0
            roe = parse_float_safe(m.get("roe_pct")) or 0.0
            fund_score = float(fund.get("score") or 7.0)
            cap_tier = self.classify_cap_tier(live_mcap)

            dyn = self._evaluate_dynamic_setup(
                cmp=cmp,
                ema20=ema20,
                ema50=ema50,
                ema200=ema200,
                h52=h52,
                rsi=rsi,
                atr=atr,
                fund_score=fund_score,
                roce=roce,
                pe=live_pe,
                peg=peg,
                day_change_pct=day_chg_pct,
                vol_ratio=vol_ratio,
            )

            strengths = fund.get("strengths", [])[:3]
            thesis_summary = "; ".join(strengths) if strengths else f"ROCE {roce:.1f}%, Low Debt & Earnings Inflection"

            return {
                "symbol": sym,
                "name": meta.get("name", sym),
                "sector": meta.get("sector", "Equities"),
                "cap_tier": cap_tier,
                "mcap_cr": live_mcap,
                "base_screener_cmp": base_cmp,
                "base_mcap_cr": base_mcap,
                "base_pe": base_pe,
                "base_peg": parse_float_safe(m.get("peg_ratio")),
                "cmp": round(cmp, 2),
                "day_change": round(day_chg, 2),
                "day_change_pct": round(day_chg_pct, 2),
                "h52": round(h52, 2),
                "l52": round(l52, 2),
                "dist_52w": dyn["dist_52w"],
                "pe": live_pe,
                "peg": peg,
                "roce": round(roce, 1),
                "roe": round(roe, 1),
                "debt_to_equity": bi.get("debt_to_equity"),
                "cfo_to_pat_3y": bi.get("cfo_to_pat_3y"),
                "qtr_sales_yoy_pct": inf.get("qtr_sales_yoy_pct"),
                "qtr_pat_yoy_pct": inf.get("qtr_pat_yoy_pct"),
                "opm_latest_pct": inf.get("opm_latest_pct"),
                "opm_expansion_bps": inf.get("opm_expansion_bps"),
                "promoter_pct": bi.get("promoter_pct"),
                "inst_4q_delta_pct": bi.get("inst_4q_delta_pct", 0.0),
                "fund_score": fund_score,
                "tech_score": dyn["tech_score"],
                "gem_score": dyn["gem_score"],
                "rsi": rsi,
                "ema_20": round(ema20, 2),
                "ema_50": round(ema50, 2),
                "ema_200": round(ema200, 2),
                "atr": round(atr, 2),
                "volume_ratio": round(vol_ratio, 2),
                "ret_1m": ret_1m,
                "ret_3m": ret_3m,
                "ret_1y": ret_1y,
                "setup_status": dyn["setup_status"],
                "status_key": dyn["status_key"],
                "status_color": dyn["status_color"],
                "suggested_entry": dyn["suggested_entry"],
                "target_1": dyn["target_1"],
                "target_2": dyn["target_2"],
                "stop_loss": dyn["stop_loss"],
                "risk_reward": dyn["risk_reward"],
                "thesis": thesis_summary,
                "is_seed": item.get("is_seed", False),
            }
        except Exception:
            return None

    def _save_cache(self, stocks: List[Dict[str, Any]]) -> None:
        payload = {
            "timestamp": datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S"),
            "total_found": len(stocks),
            "stocks": stocks,
        }
        try:
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception:
            pass

    def refresh_live_market_movements(
        self,
        gems: Optional[List[Dict[str, Any]]] = None,
        quotes_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Updates CMP, Day Change %, Market Cap, P/E, Distance from 52W High,
        Setup Status, Entry/Targets/Stop-Loss, and ranking dynamically as market moves.
        """
        if gems is None:
            gems = self.scan_hidden_gems(force_refresh=False, sync_live_prices=False)
        if not gems:
            return []

        if quotes_map is None:
            quotes_map = {}
            syms = [g["symbol"] for g in gems if g.get("symbol")]
            if syms:
                with ThreadPoolExecutor(max_workers=10) as ex:
                    for sym, q in ex.map(lambda s: (s, self.market_data.get_quote_and_overview(s)), syms):
                        quotes_map[sym] = q

        updated: List[Dict[str, Any]] = []
        for g in gems:
            row = dict(g)
            sym = row.get("symbol", "")
            q = quotes_map.get(sym, {})
            new_cmp = float(q.get("currentPrice") or 0.0)
            if new_cmp > 0:
                row["cmp"] = round(new_cmp, 2)
                row["day_change"] = round(float(q.get("change") or row.get("day_change") or 0.0), 2)
                row["day_change_pct"] = round(float(q.get("changePercent") or row.get("day_change_pct") or 0.0), 2)
                if q.get("fiftyTwoWeekHigh", 0) > 0:
                    row["h52"] = round(float(q["fiftyTwoWeekHigh"]), 2)
                if q.get("fiftyTwoWeekLow", 0) > 0:
                    row["l52"] = round(float(q["fiftyTwoWeekLow"]), 2)

                base_cmp = float(row.get("base_screener_cmp") or row["cmp"] or 1.0)
                ratio = (row["cmp"] / base_cmp) if base_cmp > 0 else 1.0
                if row.get("base_mcap_cr"):
                    row["mcap_cr"] = round(float(row["base_mcap_cr"]) * ratio, 0)
                    row["cap_tier"] = self.classify_cap_tier(row["mcap_cr"])
                if row.get("base_pe"):
                    row["pe"] = round(float(row["base_pe"]) * ratio, 1)
                    if row.get("base_peg") is not None and float(row["base_pe"]) > 0:
                        row["peg"] = round(float(row["base_peg"]) * (row["pe"] / float(row["base_pe"])), 2)

            dyn = self._evaluate_dynamic_setup(
                cmp=float(row.get("cmp") or 0.0),
                ema20=float(row.get("ema_20") or row.get("cmp") or 0.0),
                ema50=float(row.get("ema_50") or row.get("cmp") or 0.0),
                ema200=float(row.get("ema_200") or row.get("cmp") or 0.0),
                h52=float(row.get("h52") or row.get("cmp") or 0.0),
                rsi=float(row.get("rsi") or 50.0),
                atr=float(row.get("atr") or (float(row.get("cmp") or 100.0) * 0.025)),
                fund_score=float(row.get("fund_score") or 7.0),
                roce=float(row.get("roce") or 20.0),
                pe=float(row.get("pe") or 25.0),
                peg=row.get("peg"),
                day_change_pct=float(row.get("day_change_pct") or 0.0),
                vol_ratio=float(row.get("volume_ratio") or 1.0),
            )
            row.update(dyn)
            updated.append(row)

        updated.sort(
            key=lambda x: (
                x.get("gem_score", 0.0),
                1 if x.get("status_key") in ("breakout", "pullback") else 0,
                x.get("fund_score", 0.0),
                x.get("day_change_pct", 0.0),
            ),
            reverse=True,
        )
        self._save_cache(updated)
        return updated

    def scan_hidden_gems(self, force_refresh: bool = False, sync_live_prices: bool = False) -> List[Dict[str, Any]]:
        """Returns live-updated Small & Mid-Cap Hidden Gems list from NSE universe + curated seeds."""
        if not force_refresh and self.CACHE_FILE.exists():
            try:
                age_sec = time.time() - self.CACHE_FILE.stat().st_mtime
                with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                    cached = json.load(f)
                stocks = cached.get("stocks", []) if isinstance(cached, dict) else []
                if stocks and age_sec < 1800:
                    if sync_live_prices and age_sec > 120:
                        return self.refresh_live_market_movements(stocks)
                    return stocks
            except Exception:
                pass

        pool = self._collect_candidate_pool()
        results: List[Dict[str, Any]] = []
        if pool:
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                for res in executor.map(self._audit_gem_live, pool):
                    if res is not None:
                        results.append(res)

        results.sort(
            key=lambda x: (
                x.get("gem_score", 0.0),
                1 if x.get("status_key") in ("breakout", "pullback") else 0,
                x.get("fund_score", 0.0),
                x.get("roce", 0.0),
            ),
            reverse=True,
        )
        self._save_cache(results)
        return results
