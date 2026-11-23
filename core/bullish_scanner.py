import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import concurrent.futures
from core.market_data import MarketDataManager
from core.technical_analyst import TechnicalAnalyst
from core.fundamental_analyst import FundamentalAnalyst
from core.news_sentiment_analyst import NewsSentimentAnalyst

class BullishScanner:
    """
    Scans Indian stock universes to identify high-probability bullish setups with 360-degree verification.
    Prioritizes high relative strength (RS) momentum leaders across all alphabet ranges (including Laurus Labs).
    """

    # Vetted priority universe of high-momentum midcaps and leaders
    PRIORITY_MOMENTUM_STOCKS = [
        {"symbol": "LAURUSLABS", "name": "Laurus Labs Ltd.", "sector": "Healthcare / CDMO"},
        {"symbol": "DIXON", "name": "Dixon Technologies Ltd.", "sector": "Consumer Electronics / EMS"},
        {"symbol": "TRENT", "name": "Trent Ltd.", "sector": "Retail & Apparel"},
        {"symbol": "SUZLON", "name": "Suzlon Energy Ltd.", "sector": "Renewable Energy / Wind"},
        {"symbol": "KAYNES", "name": "Kaynes Technology India Ltd.", "sector": "Defense & Aerospace Electronics"},
        {"symbol": "BSE", "name": "BSE Ltd.", "sector": "Capital Markets"},
        {"symbol": "HAL", "name": "Hindustan Aeronautics Ltd.", "sector": "Defense & Aerospace"},
        {"symbol": "BEL", "name": "Bharat Electronics Ltd.", "sector": "Defense Electronics"},
        {"symbol": "DIVISLAB", "name": "Divi's Laboratories Ltd.", "sector": "Healthcare / API"},
        {"symbol": "PERSISTENT", "name": "Persistent Systems Ltd.", "sector": "IT Services"},
        {"symbol": "POLYCAB", "name": "Polycab India Ltd.", "sector": "Cables & Infra"},
        {"symbol": "ZOMATO", "name": "Zomato Ltd.", "sector": "Internet / Quick Commerce"},
        {"symbol": "SOLARINDS", "name": "Solar Industries India Ltd.", "sector": "Defense / Explosives"},
        {"symbol": "APARINDS", "name": "Apar Industries Ltd.", "sector": "Power Conductors"},
        {"symbol": "BHEL", "name": "Bharat Heavy Electricals Ltd.", "sector": "Capital Goods / Power"},
        {"symbol": "MOTHERSON", "name": "Samvardhana Motherson Ltd.", "sector": "Auto Components"},
        {"symbol": "COCHINSHIP", "name": "Cochin Shipyard Ltd.", "sector": "Defense Shipbuilding"},
        {"symbol": "MAZDOCK", "name": "Mazagon Dock Shipbuilders Ltd.", "sector": "Defense Shipyard"},
        {"symbol": "TATAMOTORS", "name": "Tata Motors Ltd.", "sector": "Automobiles"},
        {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd.", "sector": "Telecom"}
    ]

    def __init__(self, data_path: Path = None):
        self.market_data = MarketDataManager()
        self.tech_analyst = TechnicalAnalyst()
        self.fund_analyst = FundamentalAnalyst()
        self.news_analyst = NewsSentimentAnalyst()
        if data_path is None:
            from config import DATA_DIR
            self.data_path = DATA_DIR / "nse_stocks.json"
        else:
            self.data_path = Path(data_path)

    def load_stock_universe(self) -> List[Dict[str, str]]:
        """Loads curated list of NSE stocks, ensuring high momentum leaders are first in queue."""
        full_universe = []
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    full_universe = json.load(f)
            except Exception:
                pass

        # Create combined list with priority momentum stocks at the front, deduplicated
        seen = set()
        combined = []
        for p in self.PRIORITY_MOMENTUM_STOCKS:
            sym = p["symbol"]
            seen.add(sym)
            combined.append(p)

        for item in full_universe:
            sym = item.get("symbol", "")
            if sym and sym not in seen:
                seen.add(sym)
                combined.append(item)

        return combined

    def scan_single_stock(self, item: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Runs technical and preliminary fundamental audit on one stock."""
        symbol = item["symbol"]
        try:
            # 1. Fetch candles
            candles = self.market_data.get_historical_candles(symbol, period="1y", interval="1d")
            if candles.empty or len(candles) < 30:
                return None

            # 2. Technical Audit
            tech_res = self.tech_analyst.analyze(candles)
            tech_score = tech_res["score"]

            # Filter for bullish criteria (Score >= 5.5)
            if tech_score < 5.5:
                return None

            # 3. Market Overview
            overview = self.market_data.get_quote_and_overview(symbol)
            cmp = overview["currentPrice"]
            if cmp <= 0:
                return None

            # 4. Fundamental Quick Check
            fund_res = self.fund_analyst.analyze(symbol)
            fund_score = fund_res["score"]

            # 5. Check if near 52-week high (breakout zone) & Calculate 1Y return
            h52 = overview.get("fiftyTwoWeekHigh", 0)
            distance_from_52w_high = round(((h52 - cmp) / (h52 + 1e-6)) * 100, 1) if h52 > 0 else 0
            
            c_first = candles['Close'].iloc[0]
            ret_1y = round(((cmp - c_first) / (c_first + 1e-6)) * 100, 1) if len(candles) >= 50 else 0.0

            # Minervini Stage-2 Mark-up check: Price > 20 EMA > 50 EMA
            is_stage_2 = (cmp > tech_res["ema_20"] > tech_res["ema_50"])
            stage2_boost = 0.5 if is_stage_2 else 0.0

            # Momentum boost for high relative strength stocks
            mom_boost = 1.0 if ret_1y > 50.0 else (0.5 if ret_1y > 20.0 else 0.0)

            # Combined Bullish Conviction Score
            conviction_score = min(round((tech_score * 0.45) + (fund_score * 0.35) + mom_boost + stage2_boost, 1), 10.0)

            return {
                "symbol": symbol,
                "name": item.get("name", symbol),
                "sector": item.get("sector", overview.get("sector", "N/A")),
                "cmp": cmp,
                "change_pct": overview["changePercent"],
                "ret_1y": ret_1y,
                "tech_score": tech_score,
                "fund_score": fund_score,
                "conviction_score": conviction_score,
                "rsi": tech_res["rsi"],
                "ema_20": tech_res["ema_20"],
                "volume_surge": tech_res["volume_ratio"],
                "distance_from_52w_high_pct": distance_from_52w_high,
                "stop_loss": tech_res["levels"]["stop_loss"],
                "target_1": tech_res["levels"]["target_1"],
                "target_2": tech_res["levels"]["target_2"],
                "risk_reward": tech_res["levels"]["risk_reward_ratio"],
                "bullish_signals": tech_res["bullish_signals"][:3],
                "fundamental_strengths": fund_res["strengths"][:2]
            }
        except Exception:
            return None

    def scan_market(self, max_stocks: int = 40, max_workers: int = 8) -> List[Dict[str, Any]]:
        """Multi-threaded high-speed scanner across the Indian stock universe."""
        universe = self.load_stock_universe()[:max_stocks]
        bullish_results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_stock = {executor.submit(self.scan_single_stock, item): item for item in universe}
            for future in concurrent.futures.as_completed(future_to_stock):
                res = future.result()
                if res is not None:
                    bullish_results.append(res)

        # Sort by highest conviction score first
        bullish_results.sort(key=lambda x: x["conviction_score"], reverse=True)
        return bullish_results
