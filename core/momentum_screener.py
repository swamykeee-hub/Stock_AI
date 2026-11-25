import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import pandas as pd
import concurrent.futures


class MomentumScreener:
    """
    Multi-timeframe weekly trend, relative-strength, and Volatility Contraction Pattern (VCP) screener
    for Indian stocks (NSE/BSE). Evaluates 1M/3M/6M/1Y/2Y/3Y/5Y performance, 40-Week EMA (~200 DMA),
    RS vs Nifty 50, max drawdown, and liquidity across curated and full 509+ stock universes.
    """

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }

    def __init__(self, cache_file: Path = None):
        from config import CACHE_DIR, DATA_DIR
        self.cache_dir = CACHE_DIR
        self.data_dir = DATA_DIR
        self.cache_file = Path(cache_file) if cache_file else (CACHE_DIR / "momentum_cache.json")
        self.full_universe_cache_file = CACHE_DIR / "weekly_universe_scan.json"
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        self.curated_momentum_universe = self._load_catalog(DATA_DIR / "top_100_curated_stocks.json")

    @staticmethod
    def _load_catalog(filepath: Path) -> List[Dict[str, str]]:
        """Loads a stock JSON catalog and annotates default cap tiers."""
        if not filepath.exists():
            return []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return [
                {
                    "symbol": s["symbol"],
                    "name": s.get("name", s["symbol"]),
                    "sector": s.get("sector", "Equities"),
                    "market_cap_type": s.get(
                        "market_cap_type",
                        "Large Cap" if idx < 35 else ("Mid Cap" if idx < 75 else "Small / High Growth"),
                    ),
                }
                for idx, s in enumerate(raw)
                if s.get("symbol")
            ]
        except Exception:
            return []

    def fetch_nifty_benchmark_returns(self) -> Dict[str, float]:
        """Fetches Nifty 50 (^NSEI) multi-horizon baseline returns for Relative Strength (RS) calculation."""
        url = "https://query1.finance.yahoo.com/v8/finance/chart/^NSEI?range=5y&interval=1wk"
        defaults = {"ret_3m": 0.0, "ret_6m": 0.0, "ret_1y": 0.0, "ret_3y": 0.0}
        try:
            r = requests.get(url, headers=self.HEADERS, timeout=8)
            if r.status_code != 200:
                return defaults
            res = r.json().get("chart", {}).get("result", [{}])[0]
            meta = res.get("meta", {})
            closes = [c for c in res.get("indicators", {}).get("quote", [{}])[0].get("close", []) if c is not None]
            if len(closes) < 15:
                return defaults
            cmp = float(meta.get("regularMarketPrice") or closes[-1])
            return {
                "ret_3m": round(((cmp - closes[-13]) / closes[-13]) * 100, 1) if len(closes) >= 13 else 0.0,
                "ret_6m": round(((cmp - closes[-26]) / closes[-26]) * 100, 1) if len(closes) >= 26 else 0.0,
                "ret_1y": round(((cmp - closes[-52]) / closes[-52]) * 100, 1) if len(closes) >= 52 else 0.0,
                "ret_3y": round(((cmp - closes[-156]) / closes[-156]) * 100, 1) if len(closes) >= 156 else 0.0,
            }
        except Exception:
            return defaults

    @staticmethod
    def _calc_weekly_rsi(closes: pd.Series, period: int = 14) -> float:
        if len(closes) < period + 2:
            return 50.0
        delta = closes.diff()
        gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-9)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        val = rsi.iloc[-1]
        return round(float(val), 1) if pd.notna(val) else 50.0

    def fetch_stock_multi_timeframe(
        self,
        item: Dict[str, str],
        nifty_bench: Optional[Dict[str, float]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Calculates multi-timeframe returns, weekly EMAs, VCP tightness, max drawdown, and RS vs Nifty 50."""
        sym = item["symbol"]
        ticker = f"{sym}.NS" if not sym.endswith((".NS", ".BO")) else sym
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5y&interval=1wk"
        bench = nifty_bench or {"ret_3m": 0.0, "ret_6m": 0.0, "ret_1y": 0.0, "ret_3y": 0.0}

        try:
            r = requests.get(url, headers=self.HEADERS, timeout=8)
            if r.status_code != 200:
                return None

            res = r.json().get("chart", {}).get("result", [{}])[0]
            meta = res.get("meta", {})
            q = res.get("indicators", {}).get("quote", [{}])[0]
            raw_closes = q.get("close", [])
            raw_highs = q.get("high", [])
            raw_lows = q.get("low", [])
            raw_vols = q.get("volume", [])

            df = pd.DataFrame({
                "Close": raw_closes,
                "High": raw_highs,
                "Low": raw_lows,
                "Volume": raw_vols,
            }).dropna(subset=["Close"]).reset_index(drop=True)

            if len(df) < 15:
                return None

            closes = df["Close"].tolist()
            cmp = round(float(meta.get("regularMarketPrice") or closes[-1]), 2)
            tail_52 = df.tail(52)
            h52 = round(float(meta.get("fiftyTwoWeekHigh") or tail_52["High"].max()), 2)
            l52 = round(float(meta.get("fiftyTwoWeekLow") or tail_52["Low"].min()), 2)
            dist_52w = round(((h52 - cmp) / (h52 + 1e-6)) * 100, 1)

            def _pct(lag: int) -> float:
                if len(closes) > lag and closes[-lag] > 0:
                    return round(((cmp - closes[-lag]) / closes[-lag]) * 100, 1)
                return 0.0

            ret_1m = _pct(4)
            ret_3m = _pct(13)
            ret_6m = _pct(26)
            ret_1y = _pct(52)
            ret_2y = _pct(104)
            ret_3y = _pct(156)
            ret_5y = _pct(260) if len(closes) > 260 else (
                round(((cmp - closes[0]) / closes[0]) * 100, 1) if closes[0] > 0 else 0.0
            )

            # Weekly EMAs & Stage-2 Trend Architecture
            close_s = df["Close"].astype(float)
            ema10w_s = close_s.ewm(span=10, adjust=False).mean()
            ema20w_s = close_s.ewm(span=20, adjust=False).mean()
            ema40w_s = close_s.ewm(span=min(40, len(close_s)), adjust=False).mean()

            ema_10w = round(float(ema10w_s.iloc[-1]), 2)
            ema_20w = round(float(ema20w_s.iloc[-1]), 2)
            ema_40w = round(float(ema40w_s.iloc[-1]), 2)
            ema_40w_prev8 = float(ema40w_s.iloc[-9]) if len(ema40w_s) >= 9 else float(ema40w_s.iloc[0])
            ema_40w_rising = ema_40w > ema_40w_prev8
            pct_above_ema20w = round(((cmp - ema_20w) / (ema_20w + 1e-6)) * 100, 1)

            weekly_rsi = self._calc_weekly_rsi(close_s, 14)

            # Volume Surge, 4-Week Volume Expansion & Daily Average Liquidity (in INR Crore)
            vols = df["Volume"].fillna(0).astype(float).tolist()
            recent_vols = vols[-20:] if len(vols) >= 20 else vols
            avg_vol_w = sum(recent_vols) / (len(recent_vols) + 1e-6)
            vol_surge = round(vols[-1] / (avg_vol_w + 1e-6), 2) if vols else 1.0
            recent_4w_vols = vols[-4:] if len(vols) >= 4 else vols
            avg_vol_4w = sum(recent_4w_vols) / (len(recent_4w_vols) + 1e-6)
            vol_trend_4w = round(avg_vol_4w / (avg_vol_w + 1e-6), 2) if vols else 1.0
            avg_daily_turnover_cr = round(((avg_vol_w / 5.0) * cmp) / 1e7, 2)

            # Volatility Contraction Pattern (VCP) check: recent 4w range vs prior 8w range
            is_vcp_tight = False
            if len(df) >= 12 and cmp > 0:
                hi_4w = float(df["High"].tail(4).max())
                lo_4w = float(df["Low"].tail(4).min())
                spread_4w = (hi_4w - lo_4w) / cmp
                prior_8 = df.iloc[-12:-4]
                hi_8w = float(prior_8["High"].max())
                lo_8w = float(prior_8["Low"].min())
                spread_8w = (hi_8w - lo_8w) / cmp
                is_vcp_tight = (spread_4w <= 0.12) and (spread_4w < spread_8w * 0.85) and (cmp >= ema_20w * 0.97)

            # 1-Year Max Drawdown (%)
            c52 = tail_52["Close"].astype(float)
            roll_max = c52.cummax()
            drawdown_1y = round(abs(float(((c52 - roll_max) / (roll_max + 1e-6)).min()) * 100), 1)

            # Relative Strength vs Nifty 50
            rs_3m = round(ret_3m - bench["ret_3m"], 1)
            rs_6m = round(ret_6m - bench["ret_6m"], 1)
            rs_1y = round(ret_1y - bench["ret_1y"], 1)
            rs_3y = round(ret_3y - bench["ret_3y"], 1)

            # Trend classification
            if dist_52w <= 3.5 and ret_1y > 50.0 and cmp > ema_40w:
                trend_status = "🔥 52W High Super-Breakout"
                conviction = "High (Stage-2 Mark-up)"
            elif ret_1y > 90.0 and cmp > ema_40w:
                trend_status = "🚀 Multibagger Compounder"
                conviction = "Very High (Institutional Momentum)"
            elif cmp > ema_40w and ema_40w_rising and is_vcp_tight and rs_6m > 8.0:
                trend_status = "⚡ Weekly VCP Stage-2 Base"
                conviction = "High (Tight Volatility Contraction)"
            elif ret_6m > 25.0 and ret_1m > 4.0 and cmp > ema_20w:
                trend_status = "⚡ Accelerating Momentum"
                conviction = "High (Medium/Long Term)"
            elif ret_3y > 150.0 and cmp > ema_40w:
                trend_status = "🏛️ Multi-Year Structural Bull"
                conviction = "Core Portfolio Compounder"
            elif dist_52w <= 8.0 and cmp > ema_40w:
                trend_status = "🎯 Near Breakout Zone"
                conviction = "Watchlist / Accumulate"
            elif cmp >= ema_40w * 0.96 and ret_3m >= 10.0 and weekly_rsi >= 50:
                trend_status = "🌱 Early Stage-1→2 Reversal"
                conviction = "Turnaround Breakout Watch"
            else:
                trend_status = "📈 Positive Trend" if cmp > ema_40w else "⏸️ Base Building"
                conviction = "Moderate"

            return {
                "symbol": sym,
                "name": item.get("name", meta.get("shortName", sym)),
                "sector": item.get("sector", "Equities"),
                "market_cap_type": item.get("market_cap_type", "Mid/Large Cap"),
                "cmp": cmp,
                "ret_1m": ret_1m,
                "ret_3m": ret_3m,
                "ret_6m": ret_6m,
                "ret_1y": ret_1y,
                "ret_2y": ret_2y,
                "ret_3y": ret_3y,
                "ret_5y": ret_5y,
                "fifty_two_week_high": h52,
                "fifty_two_week_low": l52,
                "distance_from_52w_high": dist_52w,
                "ema_10w": ema_10w,
                "ema_20w": ema_20w,
                "ema_40w": ema_40w,
                "ema_40w_rising": ema_40w_rising,
                "pct_above_ema20w": pct_above_ema20w,
                "weekly_rsi": weekly_rsi,
                "volume_surge": vol_surge,
                "vol_trend_4w": vol_trend_4w,
                "avg_daily_turnover_cr": avg_daily_turnover_cr,
                "is_vcp_tight": is_vcp_tight,
                "max_drawdown_1y": drawdown_1y,
                "rs_vs_nifty_3m": rs_3m,
                "rs_vs_nifty_6m": rs_6m,
                "rs_vs_nifty_1y": rs_1y,
                "rs_vs_nifty_3y": rs_3y,
                "trend_status": trend_status,
                "conviction": conviction,
            }
        except Exception:
            return None

    def scan_universe(self, max_stocks: int = 100, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Scans curated Top 100 momentum universe with weekly technicals & caching."""
        if not force_refresh and self.cache_file.exists():
            try:
                if (time.time() - self.cache_file.stat().st_mtime) < 7200:
                    with open(self.cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data and len(data) >= 20 and "vol_trend_4w" in data[0]:
                            return data
            except Exception:
                pass

        nifty_bench = self.fetch_nifty_benchmark_returns()
        stocks_to_scan = self.curated_momentum_universe[:max_stocks]
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.fetch_stock_multi_timeframe, item, nifty_bench) for item in stocks_to_scan]
            for fut in concurrent.futures.as_completed(futures):
                res = fut.result()
                if res is not None:
                    results.append(res)

        results.sort(key=lambda x: x["ret_1y"], reverse=True)
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
        except Exception:
            pass
        return results

    def scan_full_nse_weekly(self, universe: List[Dict[str, str]], force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Pass-1 Discovery Engine: Scans the entire 509+ NSE universe on 5Y weekly candles
        (cached for 4 hours) to surface Stage-2 leaders and early turnaround inflections.
        """
        if not force_refresh and self.full_universe_cache_file.exists():
            try:
                if (time.time() - self.full_universe_cache_file.stat().st_mtime) < 14400:
                    with open(self.full_universe_cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data and len(data) >= max(50, int(len(universe) * 0.5)) and "vol_trend_4w" in data[0]:
                            return data
            except Exception:
                pass

        nifty_bench = self.fetch_nifty_benchmark_returns()
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=14) as executor:
            futures = [executor.submit(self.fetch_stock_multi_timeframe, item, nifty_bench) for item in universe]
            for fut in concurrent.futures.as_completed(futures):
                res = fut.result()
                if res is not None:
                    results.append(res)

        results.sort(key=lambda x: (x.get("rs_vs_nifty_6m", 0) + (x.get("ret_1y", 0) * 0.5)), reverse=True)
        try:
            with open(self.full_universe_cache_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2)
        except Exception:
            pass
        return results

    def filter_by_horizon(self, results: List[Dict[str, Any]], horizon: str = "1Y", min_gain: float = 0.0) -> List[Dict[str, Any]]:
        """Filters and sorts stocks by a selected timeframe (3M, 6M, 1Y, 2Y, 3Y, 5Y)."""
        key_map = {
            "1M": "ret_1m",
            "3M": "ret_3m",
            "6M": "ret_6m",
            "1Y": "ret_1y",
            "2Y": "ret_2y",
            "3Y": "ret_3y",
            "5Y": "ret_5y",
        }
        metric_key = key_map.get(horizon, "ret_1y")
        filtered = [x for x in results if x.get(metric_key, 0.0) >= min_gain]
        filtered.sort(key=lambda x: x.get(metric_key, 0.0), reverse=True)
        return filtered
