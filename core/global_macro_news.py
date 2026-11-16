import requests
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from datetime import datetime

class GlobalMacroNewsAnalyst:
    """
    Tracks Global Market Indices, Macro Commodities (Crude, US 10Y Yield, DXY, Gold),
    and delivers institutional Fund Manager impact assessments on Indian equities and individual stocks.
    """

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    GLOBAL_TICKERS = {
        "S&P 500": "^GSPC",
        "Nasdaq Composite": "^IXIC",
        "Dow Jones": "^DJI",
        "Nikkei 225": "^N225",
        "FTSE 100": "^FTSE",
        "DAX": "^GDAXI",
        "Hang Seng": "^HSI"
    }

    COMMODITY_TICKERS = {
        "Brent Crude ($/bbl)": "BZ=F",
        "US 10-Yr Yield (%)": "^TNX",
        "US Dollar Index (DXY)": "DX-Y.NYB",
        "Gold ($/oz)": "GC=F",
        "USD / INR": "INR=X"
    }

    def fetch_quote_fast(self, ticker: str) -> Dict[str, Any]:
        """Fetches live price and change from Yahoo Finance v8 chart."""
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=2d&interval=1d"
        try:
            r = requests.get(url, headers=self.HEADERS, timeout=5)
            if r.status_code == 200:
                meta = r.json().get("chart", {}).get("result", [{}])[0].get("meta", {})
                cmp = meta.get("regularMarketPrice", 0.0)
                prev = meta.get("chartPreviousClose", cmp)
                chg = meta.get("fulldayChange") or (cmp - prev)
                chg_pct = meta.get("regularMarketChangePercent") or ((chg / (prev + 1e-6)) * 100)
                return {
                    "price": round(cmp, 2),
                    "change": round(chg, 2),
                    "change_pct": round(chg_pct, 2)
                }
        except Exception:
            pass
        return {"price": 0.0, "change": 0.0, "change_pct": 0.0}

    def get_global_markets_snapshot(self) -> Dict[str, Any]:
        """Collects live snapshot of global indices and commodities."""
        indices_data = {}
        for name, ticker in self.GLOBAL_TICKERS.items():
            indices_data[name] = self.fetch_quote_fast(ticker)

        macro_data = {}
        for name, ticker in self.COMMODITY_TICKERS.items():
            macro_data[name] = self.fetch_quote_fast(ticker)

        # Senior Fund Manager Macro Assessment
        crude_price = macro_data.get("Brent Crude ($/bbl)", {}).get("price", 75.0)
        yield_10y = macro_data.get("US 10-Yr Yield (%)", {}).get("price", 4.3)
        dxy = macro_data.get("US Dollar Index (DXY)", {}).get("price", 103.0)

        fund_manager_takeaways = []
        if crude_price > 85.0:
            fund_manager_takeaways.append("⚠️ Elevated Crude Oil (> $85): Margin headwinds for Paints, Aviation, and OMCs; adds pressure on CAD.")
        else:
            fund_manager_takeaways.append(f"✅ Softening / Stable Crude (~${crude_price}/bbl): Strong margin tailwinds for domestic manufacturing, paints, and tire sectors.")

        if yield_10y < 4.2:
            fund_manager_takeaways.append(f"✅ US 10-Yr Yield at {yield_10y}%: Easing global yields trigger FII risk-on appetite for high-growth Indian Midcaps.")
        else:
            fund_manager_takeaways.append(f"ℹ️ US 10-Yr Yield at {yield_10y}%: Kept tight global liquidity; favors domestic earnings compounders over speculative valuation multiples.")

        if dxy < 103.0:
            fund_manager_takeaways.append("✅ Soft US Dollar Index (DXY): Historically bullish for Emerging Market capital flows into India.")

        return {
            "indices": indices_data,
            "macro": macro_data,
            "fund_manager_takeaways": fund_manager_takeaways,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def fetch_stock_impact_news(self, symbol: str, limit: int = 8) -> List[Dict[str, Any]]:
        """
        Fetches stock-specific news and evaluates impact on share price and business fundamentals.
        """
        clean_sym = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
        query = f"{clean_sym} share price NSE OR {clean_sym} quarterly results OR {clean_sym} FDA order"
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"

        articles = []
        try:
            r = requests.get(url, headers=self.HEADERS, timeout=8)
            if r.status_code == 200:
                root = ET.fromstring(r.content)
                for item in root.findall(".//item")[:limit]:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    pub = item.find("pubDate").text if item.find("pubDate") is not None else ""
                    source = item.find("source").text if item.find("source") is not None else "Financial Media"

                    # Impact & Catalyst Analysis
                    lower = title.lower()
                    impact = "Neutral"
                    impact_color = "#94a3b8"
                    catalyst_type = "Corporate Update"

                    if any(w in lower for w in ["fda", "usfda", "eir", "inspection", "clearance"]):
                        catalyst_type = "US FDA / Regulatory"
                        if any(w in lower for w in ["clear", "vair", "nai", "zero observation", "approv"]):
                            impact = "High Positive (Re-Rating Catalyst)"
                            impact_color = "#16a34a"
                        elif any(w in lower for w in ["warning", "import alert", "form 483", "oai"]):
                            impact = "Negative Regulatory Headwind"
                            impact_color = "#dc2626"
                    elif any(w in lower for w in ["profit up", "profit jumps", "revenue up", "q1", "q2", "q3", "q4", "earnings"]):
                        catalyst_type = "Quarterly Financials"
                        if any(w in lower for w in ["jump", "surge", "beat", "record", "double", "grows"]):
                            impact = "Positive Earnings Inflection"
                            impact_color = "#16a34a"
                        elif any(w in lower for w in ["fall", "drop", "miss", "loss"]):
                            impact = "Earnings Miss / Headwind"
                            impact_color = "#dc2626"
                    elif any(w in lower for w in ["order", "bag", "wins", "contract", "deal", "pli"]):
                        catalyst_type = "Order Win / Expansion"
                        impact = "Positive Growth Visibility"
                        impact_color = "#16a34a"
                    elif any(w in lower for w in ["target", "buy", "upgrade", "outperform"]):
                        catalyst_type = "Brokerage Upgrade"
                        impact = "Positive Institutional View"
                        impact_color = "#16a34a"

                    articles.append({
                        "title": title,
                        "source": source,
                        "pub_date": pub,
                        "link": link,
                        "catalyst_type": catalyst_type,
                        "impact": impact,
                        "impact_color": impact_color
                    })
        except Exception:
            pass

        return articles

