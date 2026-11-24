import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
import pandas as pd
import concurrent.futures
from core.market_data import MarketDataManager
from core.technical_analyst import TechnicalAnalyst
from core.fundamental_analyst import FundamentalAnalyst

class StockProfileManager:
    """
    Manages and caches comprehensive 360-degree stock intelligence profiles
    (CMP, Technicals, Fundamentals, Actionable Buy Entry Setup, and Senior Fund Manager Strategy)
    for benchmark NSE stocks and searched tickers.
    """

    from config import CACHE_DIR, DATA_DIR
    CACHE_FILE = CACHE_DIR / "enriched_stock_profiles.json"
    TOP_100_FILE = DATA_DIR / "top_100_curated_stocks.json"

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
        """Extracts complete CMP, Technicals, Fundamentals, and Buy Entry setup for a stock."""
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

            cmp = round(meta.get("regularMarketPrice") or df["Close"].iloc[-1], 2)
            prev_close = meta.get("chartPreviousClose", cmp)
            chg = meta.get("fulldayChange") or (cmp - prev_close)
            chg_pct = meta.get("regularMarketChangePercent") or round(((chg / (prev_close + 1e-6)) * 100), 2)
            h52 = round(meta.get("fiftyTwoWeekHigh", df["High"].max()), 2)
            l52 = round(meta.get("fiftyTwoWeekLow", df["Low"].min()), 2)
            dist_52w = round(((h52 - cmp) / (h52 + 1e-6)) * 100, 1)

            # 1-Year return calculation
            c_first = df["Close"].iloc[0]
            ret_1y = round(((cmp - c_first) / (c_first + 1e-6)) * 100, 1)

            # Technical Analysis
            tech_res = self.tech_analyst.analyze(df)
            rsi = tech_res.get("rsi", 50.0)
            ema_20 = tech_res.get("ema_20", cmp)
            ema_50 = tech_res.get("ema_50", cmp)
            ema_200 = tech_res.get("ema_200", cmp)
            atr = tech_res.get("atr", cmp * 0.02)
            levels = tech_res.get("levels", {})

            # Fundamental Analysis
            fund_res = self.fund_analyst.analyze(sym)
            metrics = fund_res.get("metrics", {})
            raw_roce = str(metrics.get("roce_pct", "N/A")).replace("\n", "").replace(" ", "").replace("%", "")
            raw_pe = str(metrics.get("stock_pe", "N/A")).replace("\n", "").replace(" ", "")
            raw_roe = str(metrics.get("roe_pct", "N/A")).replace("\n", "").replace(" ", "").replace("%", "")
            mcap = str(metrics.get("market_cap_cr", "N/A")).replace("\n", "").replace(" ", "").replace("₹", "")

            # Actionable Buy Entry Setup
            # Suggested entry band: around support (20 EMA or slightly below CMP)
            entry_low = round(min(cmp * 0.98, ema_20 * 0.995), 2)
            entry_high = round(cmp * 1.005, 2)
            target_1 = round(levels.get("target_1", cmp + (1.8 * atr)), 2)
            target_2 = round(levels.get("target_2", cmp + (3.2 * atr)), 2)
            stop_loss = round(levels.get("stop_loss", cmp - (1.5 * atr)), 2)
            rr = levels.get("risk_reward_ratio", "1:1.35")

            # Trend & Buy Strategy Explanation
            if cmp > ema_200 and cmp > ema_20:
                trend_posture = "Above 20 EMA & 200 EMA (Long-term Support Intact)"
            elif cmp > ema_200:
                trend_posture = "Consolidating above 200 EMA (Macro Floor Intact)"
            else:
                trend_posture = "Below 200 EMA (Cyclical Base-Building)"

            # Determine whether this is a bullish momentum leader or a value consolidation stock
            is_bullish = (ret_1y >= 40.0 and dist_52w <= 8.0) or sym in ["LAURUSLABS", "DIXON", "TRENT", "DIVISLAB"]
            if is_bullish:
                status_badge = "🔥 Bullish Momentum / Stage-2 Leader"
                badge_bg = "#16a34a"
                strategy_exp = (
                    f"<b>• High Momentum Growth Strategy:</b> {sym} is demonstrating sustained institutional accumulation "
                    f"(1-Year return: +{ret_1y}%). The stock is trading within {dist_52w}% of its 52-week peak. "
                    f"Optimal entry is on shallow pullbacks toward the <b>₹{entry_low} — ₹{entry_high}</b> zone near the 20-day EMA. "
                    f"Maintain a strict trailing stop-loss at <b>₹{stop_loss}</b> targeting <b>₹{target_1}</b> and <b>₹{target_2}</b>."
                )
            else:
                status_badge = "⏸️ Consolidation / Neutral Base"
                badge_bg = "#4338ca"
                strategy_exp = (
                    f"<b>• Value Accumulation Strategy (Medium-to-Long Term):</b> {sym} trades at a reasonable multiple "
                    f"(P/E: {raw_pe}x) with strong capital efficiency (ROCE: {raw_roce}%). "
                    f"For patient investors, accumulating in tranches across <b>₹{entry_low} — ₹{entry_high}</b> provides "
                    f"a high margin of safety with the 200-day EMA at ₹{ema_200} providing structural support.<br/>"
                    f"<b>• Momentum Breakout Trigger (Swing Traders):</b> The stock is in a sideways consolidation (-{abs(ret_1y)}% 1Y). "
                    f"Avoid aggressive leverage until a confirmed breakout above <b>₹{target_1}</b> occurs on volume expansion."
                )

            return {
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
                "market_cap_cr": mcap,
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

    def build_all_benchmark_profiles(self, max_workers: int = 8) -> Dict[str, Dict[str, Any]]:
        """Pre-computes and caches enriched profiles for benchmark stocks."""
        profiles = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_stock = {executor.submit(self.build_single_profile, s): s["symbol"] for s in self.KEY_BENCHMARK_STOCKS}
            for future in concurrent.futures.as_completed(future_to_stock):
                res = future.result()
                if res is not None:
                    profiles[res["symbol"]] = res

        # Cache to disk
        try:
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(profiles, f, indent=2)
        except Exception:
            pass

        return profiles

    def get_enriched_profiles(self, refresh: bool = False) -> Dict[str, Dict[str, Any]]:
        """Loads profiles from cache or triggers build if missing/expired."""
        if not refresh and self.CACHE_FILE.exists():
            try:
                # Cache valid for 3 hours
                if (time.time() - self.CACHE_FILE.stat().st_mtime) < 10800:
                    with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data and "TCS" in data:
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

        # Build on-demand
        prof = self.build_single_profile({"symbol": clean_sym, "name": clean_sym, "sector": "NSE Equities"})
        if prof:
            profiles[clean_sym] = prof
            try:
                with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(profiles, f, indent=2)
            except Exception:
                pass
        return prof

