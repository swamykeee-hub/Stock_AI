import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import pandas as pd
import concurrent.futures

class MomentumScreener:
    """
    Multi-timeframe trend and momentum screener for Indian stocks (NSE/BSE).
    Discovers super-trend stocks, 52-week high breakouts, and multi-year compounders
    across 3 Months, 6 Months, 1 Year, 2 Years, 3 Years, and 5 Years.
    """

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def __init__(self, cache_file: Path = None):
        if cache_file is None:
            from config import CACHE_DIR
            self.cache_file = CACHE_DIR / "momentum_cache.json"
        else:
            self.cache_file = Path(cache_file)
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        # Curated universe covering High-Growth Midcaps, Smallcaps, and Market Leaders
        self.curated_momentum_universe = [
            {"symbol": "LAURUSLABS", "name": "Laurus Labs Ltd.", "sector": "Healthcare / CDMO", "market_cap_type": "Mid Cap"},
            {"symbol": "DIXON", "name": "Dixon Technologies Ltd.", "sector": "Consumer Electronics / EMS", "market_cap_type": "Mid Cap"},
            {"symbol": "TRENT", "name": "Trent Ltd. (Tata Group)", "sector": "Retail & Apparel", "market_cap_type": "Large Cap"},
            {"symbol": "SUZLON", "name": "Suzlon Energy Ltd.", "sector": "Green Energy / Wind", "market_cap_type": "Mid Cap"},
            {"symbol": "KAYNES", "name": "Kaynes Technology India Ltd.", "sector": "Defense / Aerospace Electronics", "market_cap_type": "Mid Cap"},
            {"symbol": "POLYCAB", "name": "Polycab India Ltd.", "sector": "Cables & Infrastructure", "market_cap_type": "Large Cap"},
            {"symbol": "PERSISTENT", "name": "Persistent Systems Ltd.", "sector": "IT & Cloud Services", "market_cap_type": "Mid Cap"},
            {"symbol": "BSE", "name": "BSE Ltd.", "sector": "Capital Markets / Exchanges", "market_cap_type": "Mid Cap"},
            {"symbol": "CDSL", "name": "Central Depository Services Ltd.", "sector": "Capital Markets / FinTech", "market_cap_type": "Mid Cap"},
            {"symbol": "HAL", "name": "Hindustan Aeronautics Ltd.", "sector": "Defense & Aerospace", "market_cap_type": "Large Cap"},
            {"symbol": "BEL", "name": "Bharat Electronics Ltd.", "sector": "Defense Electronics", "market_cap_type": "Large Cap"},
            {"symbol": "ZOMATO", "name": "Zomato Ltd.", "sector": "Platform / Quick Commerce", "market_cap_type": "Large Cap"},
            {"symbol": "SOLARINDS", "name": "Solar Industries India Ltd.", "sector": "Industrial Explosives / Defense", "market_cap_type": "Mid Cap"},
            {"symbol": "MAZDOCK", "name": "Mazagon Dock Shipbuilders Ltd.", "sector": "Defense Shipyard", "market_cap_type": "Mid Cap"},
            {"symbol": "COCHINSHIP", "name": "Cochin Shipyard Ltd.", "sector": "Shipbuilding & Marine", "market_cap_type": "Mid Cap"},
            {"symbol": "AMBER", "name": "Amber Enterprises India Ltd.", "sector": "HVAC / Electronics", "market_cap_type": "Mid Cap"},
            {"symbol": "KPITTECH", "name": "KPIT Technologies Ltd.", "sector": "Automotive Software / Tech", "market_cap_type": "Mid Cap"},
            {"symbol": "TATAELXSI", "name": "Tata Elxsi Ltd.", "sector": "Design & Tech Services", "market_cap_type": "Mid Cap"},
            {"symbol": "APARINDS", "name": "Apar Industries Ltd.", "sector": "Conductors & Transformers", "market_cap_type": "Mid Cap"},
            {"symbol": "PRESTIGE", "name": "Prestige Estates Projects Ltd.", "sector": "Real Estate Development", "market_cap_type": "Mid Cap"},
            {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd.", "sector": "Telecommunications", "market_cap_type": "Large Cap"},
            {"symbol": "TATAMOTORS", "name": "Tata Motors Ltd.", "sector": "Automobiles / EV", "market_cap_type": "Large Cap"},
            {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Ltd.", "sector": "Healthcare / Specialty Pharma", "market_cap_type": "Large Cap"},
            {"symbol": "CIPLA", "name": "Cipla Ltd.", "sector": "Healthcare / Respiratory", "market_cap_type": "Large Cap"},
            {"symbol": "DIVISLAB", "name": "Divi's Laboratories Ltd.", "sector": "Healthcare / Active Pharma", "market_cap_type": "Large Cap"},
            {"symbol": "MOTHERSON", "name": "Samvardhana Motherson International Ltd.", "sector": "Auto Components", "market_cap_type": "Large Cap"},
            {"symbol": "CUMMINSIND", "name": "Cummins India Ltd.", "sector": "Power Generation & Engines", "market_cap_type": "Mid Cap"},
            {"symbol": "BHEL", "name": "Bharat Heavy Electricals Ltd.", "sector": "Power Equipment / Capital Goods", "market_cap_type": "Mid Cap"},
            {"symbol": "HUDCO", "name": "Housing & Urban Development Corp Ltd.", "sector": "Infrastructure Finance", "market_cap_type": "Mid Cap"},
            {"symbol": "IRFC", "name": "Indian Railway Finance Corp Ltd.", "sector": "Railway Finance", "market_cap_type": "Mid Cap"}
        ]

    def fetch_stock_multi_timeframe(self, item: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Calculates multi-timeframe returns for a stock using weekly candles over 5 years."""
        sym = item["symbol"]
        ticker = f"{sym}.NS"
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5y&interval=1wk"

        try:
            r = requests.get(url, headers=self.HEADERS, timeout=8)
            if r.status_code == 200:
                data = r.json()
                res = data.get("chart", {}).get("result", [{}])[0]
                meta = res.get("meta", {})
                quotes = res.get("indicators", {}).get("quote", [{}])[0]
                closes = [c for c in quotes.get("close", []) if c is not None]
                volumes = [v for v in quotes.get("volume", []) if v is not None]

                if not closes or len(closes) < 10:
                    return None

                cmp = round(meta.get("regularMarketPrice") or closes[-1], 2)
                h52 = round(meta.get("fiftyTwoWeekHigh", max(closes[-52:] if len(closes) >= 52 else closes)), 2)
                l52 = round(meta.get("fiftyTwoWeekLow", min(closes[-52:] if len(closes) >= 52 else closes)), 2)

                # Distance from 52-week high (%)
                dist_52w = round(((h52 - cmp) / (h52 + 1e-6)) * 100, 1)

                # Calculate returns
                ret_1m = round(((cmp - closes[-4]) / closes[-4]) * 100, 1) if len(closes) >= 4 else 0.0
                ret_3m = round(((cmp - closes[-13]) / closes[-13]) * 100, 1) if len(closes) >= 13 else 0.0
                ret_6m = round(((cmp - closes[-26]) / closes[-26]) * 100, 1) if len(closes) >= 26 else 0.0
                ret_1y = round(((cmp - closes[-52]) / closes[-52]) * 100, 1) if len(closes) >= 52 else 0.0
                ret_2y = round(((cmp - closes[-104]) / closes[-104]) * 100, 1) if len(closes) >= 104 else 0.0
                ret_3y = round(((cmp - closes[-156]) / closes[-156]) * 100, 1) if len(closes) >= 156 else 0.0
                ret_5y = round(((cmp - closes[-260]) / closes[-260]) * 100, 1) if len(closes) >= 260 else (
                    round(((cmp - closes[0]) / closes[0]) * 100, 1) if len(closes) > 0 else 0.0
                )

                # Volume Surge (latest week vs 20-week average)
                recent_vols = volumes[-20:] if len(volumes) >= 20 else volumes
                avg_vol = sum(recent_vols) / (len(recent_vols) + 1e-6)
                vol_surge = round(volumes[-1] / (avg_vol + 1e-6), 2) if volumes else 1.0

                # Trend classification
                if dist_52w <= 3.0 and ret_1y > 60.0:
                    trend_status = "🔥 52W High Super-Breakout"
                    conviction = "High (Stage-2 Mark-up)"
                elif ret_1y > 100.0:
                    trend_status = "🚀 Multibagger Compounder (+100%+)"
                    conviction = "Very High (Institutional Momentum)"
                elif ret_6m > 30.0 and ret_1m > 5.0:
                    trend_status = "⚡ Accelerating Momentum"
                    conviction = "High (Short/Medium Term)"
                elif ret_3y > 200.0:
                    trend_status = "🏛️ Multi-Year Structural Bull"
                    conviction = "Core Portfolio Compounder"
                elif dist_52w <= 7.0:
                    trend_status = "🎯 Near Breakout Zone"
                    conviction = "Watchlist / Accumulate"
                else:
                    trend_status = "📈 Positive Trend"
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
                    "volume_surge": vol_surge,
                    "trend_status": trend_status,
                    "conviction": conviction
                }
        except Exception:
            return None

    def scan_universe(self, max_stocks: int = 35, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Scans momentum universe with multithreading and local file caching."""
        if not force_refresh and self.cache_file.exists():
            try:
                # Check cache freshness (valid for 2 hours)
                mtime = self.cache_file.stat().st_mtime
                if (time.time() - mtime) < 7200:
                    with open(self.cache_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if data and len(data) >= 15:
                            return data
            except Exception:
                pass

        stocks_to_scan = self.curated_momentum_universe[:max_stocks]
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_stock = {executor.submit(self.fetch_stock_multi_timeframe, item): item for item in stocks_to_scan}
            for future in concurrent.futures.as_completed(future_to_stock):
                res = future.result()
                if res is not None:
                    results.append(res)

        # Sort by 1-Year return by default (descending)
        results.sort(key=lambda x: x["ret_1y"], reverse=True)

        # Save to cache
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
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
            "5Y": "ret_5y"
        }
        metric_key = key_map.get(horizon, "ret_1y")
        filtered = [x for x in results if x.get(metric_key, 0.0) >= min_gain]
        filtered.sort(key=lambda x: x.get(metric_key, 0.0), reverse=True)
        return filtered

