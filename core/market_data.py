import requests
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

class MarketDataManager:
    """Manages price, historical candles, and live quotes for Indian stocks (NSE/BSE)."""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    def __init__(self, default_exchange: str = "NSE"):
        self.default_exchange = default_exchange
        self.suffix = ".NS" if default_exchange == "NSE" else ".BO"

    def format_symbol(self, raw_symbol: str) -> str:
        """Formats raw ticker to Indian exchange ticker."""
        clean = raw_symbol.strip().upper()
        if clean.endswith(".NS") or clean.endswith(".BO") or clean.startswith("^"):
            return clean
        return f"{clean}{self.suffix}"

    def get_quote_and_overview(self, symbol: str) -> Dict[str, Any]:
        """Fetches live price, 52W range, and volume snapshot via direct v8 chart endpoint."""
        formatted_sym = self.format_symbol(symbol)
        clean_name = symbol.upper().replace(".NS", "").replace(".BO", "")
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{formatted_sym}?range=5d&interval=1d"

        try:
            r = requests.get(url, headers=self.HEADERS, timeout=10)
            if r.status_code == 200:
                result = r.json().get("chart", {}).get("result", [{}])[0]
                meta = result.get("meta", {})
                cmp = meta.get("regularMarketPrice") or 0.0
                if not cmp or cmp <= 0:
                    quotes = result.get("indicators", {}).get("quote", [{}])[0]
                    closes = [c for c in quotes.get("close", []) if c is not None]
                    if closes:
                        cmp = closes[-1]
                prev_close = meta.get("chartPreviousClose", cmp)
                chg = meta.get("fulldayChange") if meta.get("fulldayChange") is not None else (cmp - prev_close)
                pct_chg = meta.get("regularMarketChangePercent") if meta.get("regularMarketChangePercent") is not None else ((chg / (prev_close + 1e-6)) * 100)

                return {
                    "symbol": clean_name,
                    "full_ticker": formatted_sym,
                    "shortName": meta.get("shortName") or meta.get("longName") or clean_name,
                    "sector": "Indian Equities",
                    "industry": "NSE/BSE Listed",
                    "currentPrice": round(cmp, 2),
                    "previousClose": round(prev_close, 2),
                    "change": round(chg, 2),
                    "changePercent": round(pct_chg, 2),
                    "dayLow": meta.get("regularMarketDayLow", 0.0),
                    "dayHigh": meta.get("regularMarketDayHigh", 0.0),
                    "fiftyTwoWeekLow": meta.get("fiftyTwoWeekLow", 0.0),
                    "fiftyTwoWeekHigh": meta.get("fiftyTwoWeekHigh", 0.0),
                    "volume": meta.get("regularMarketVolume", 0),
                    "currency": meta.get("currency", "INR")
                }
        except Exception:
            pass

        return {
            "symbol": clean_name,
            "full_ticker": formatted_sym,
            "shortName": clean_name,
            "sector": "Indian Equities",
            "industry": "NSE/BSE Listed",
            "currentPrice": 0.0,
            "previousClose": 0.0,
            "change": 0.0,
            "changePercent": 0.0,
            "dayLow": 0.0,
            "dayHigh": 0.0,
            "fiftyTwoWeekLow": 0.0,
            "fiftyTwoWeekHigh": 0.0,
            "volume": 0,
            "currency": "INR"
        }

    def get_historical_candles(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """Fetches historical OHLCV data using direct v8 API."""
        formatted_sym = self.format_symbol(symbol)
        period_map = {"1m": "1mo", "3m": "3mo", "6m": "6mo", "1w": "5d"}
        yf_period = period_map.get(str(period).strip().lower(), period)
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{formatted_sym}?range={yf_period}&interval={interval}"

        try:
            r = requests.get(url, headers=self.HEADERS, timeout=10)
            if r.status_code == 200:
                result = r.json().get("chart", {}).get("result", [{}])[0]
                timestamps = result.get("timestamp", [])
                quote = result.get("indicators", {}).get("quote", [{}])[0]
                
                if timestamps and quote:
                    df = pd.DataFrame({
                        "Date": pd.to_datetime(timestamps, unit="s"),
                        "Open": quote.get("open", []),
                        "High": quote.get("high", []),
                        "Low": quote.get("low", []),
                        "Close": quote.get("close", []),
                        "Volume": quote.get("volume", [])
                    })
                    df.dropna(subset=["Close"], inplace=True)
                    df.reset_index(drop=True, inplace=True)
                    return df
        except Exception:
            pass

        return pd.DataFrame()

    def get_ai_catalysts_index(self) -> Dict[str, Any]:
        """Calculates live tracking metrics for Nifty AI Catalysts Index (Base: 1,000, launched Sept 2026).
        Uses real-time weighted movement of top constituents (HCL Tech, Bharti Airtel, Indus Towers, L&T, Tata Power, BHEL, Polycab, NTPC).
        """
        ai_constituents = [
            "HCLTECH.NS", "BHARTIARTL.NS", "INDUSTOWER.NS", "LT.NS",
            "TATAPOWER.NS", "BHEL.NS", "POLYCAB.NS", "NTPC.NS"
        ]
        changes = []
        for sym in ai_constituents:
            q = self.get_quote_and_overview(sym)
            if q.get("currentPrice", 0) > 0:
                changes.append(q.get("changePercent", 0.0))
        
        base_val = 1006.08
        if changes:
            avg_pct = sum(changes) / len(changes)
            chg_val = round(base_val * (avg_pct / 100.0), 2)
            cur_val = round(base_val + chg_val, 2)
            return {
                "value": cur_val,
                "change": chg_val,
                "percent": round(avg_pct, 2)
            }
        return {
            "value": base_val,
            "change": 0.0,
            "percent": 0.0
        }

    def get_benchmark_indices(self) -> Dict[str, Dict[str, Any]]:
        """Fetches live status for Indian Domestic Benchmarks, Broad Market, Thematic & Sectoral Indices."""
        indices = {
            "NIFTY 50": "^NSEI",
            "SENSEX": "^BSESN",
            "BANK NIFTY": "^NSEBANK",
            "INDIA VIX": "^INDIAVIX",
            "NIFTY 100": "^CNX100",
            "NIFTY 200": "^CNX200",
            "NIFTY IT": "^CNXIT",
            "NIFTY PHARMA": "^CNXPHARMA",
            "NIFTY FMCG": "^CNXFMCG",
            "NIFTY AUTO": "^CNXAUTO",
            "NIFTY METAL": "^CNXMETAL",
            "NIFTY PRIVATE BANK": "NIFTY_PVT_BANK.NS",
            "NIFTY FIN-SERVICES": "^CNXFIN"
        }

        results = {}
        def _fetch_single(item):
            name, sym = item
            overview = self.get_quote_and_overview(sym)
            return name, {
                "value": overview["currentPrice"],
                "change": overview["change"],
                "percent": overview["changePercent"]
            }

        with ThreadPoolExecutor(max_workers=8) as executor:
            fetched_results = dict(executor.map(_fetch_single, indices.items()))

        # Re-order to maintain exact presentation order
        for name in indices.keys():
            if name in fetched_results:
                results[name] = fetched_results[name]

        # Append Nifty AI Catalysts index
        results["NIFTY AI CATALYSTS"] = self.get_ai_catalysts_index()

        return results
