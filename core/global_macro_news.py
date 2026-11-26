import requests
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, Any, List
from datetime import datetime

def format_inr_number(val: float, decimals: int = 0) -> str:
    """Format a numeric value using the Indian numbering system (e.g. 1,24,800)."""
    neg = val < 0
    abs_val = abs(float(val))
    int_str = f"{round(abs_val):d}" if decimals == 0 else f"{abs_val:.{decimals}f}"
    whole, *frac = int_str.split(".")
    if len(whole) > 3:
        last3 = whole[-3:]
        rest = whole[:-3]
        groups = []
        while len(rest) > 2:
            groups.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.append(rest)
        whole = ",".join(reversed(groups)) + "," + last3
    formatted = f"{whole}.{frac[0]}" if frac else whole
    return f"-{formatted}" if neg else formatted


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
        "Silver ($/oz)": "SI=F",
        "USD / INR": "INR=X"
    }

    BULLION_URLS = {
        "gold": "https://www.goodreturns.in/gold-rates/",
        "silver": "https://www.goodreturns.in/silver-rates/",
    }

    @staticmethod
    def _parse_inr_number(raw: str) -> float:
        import re
        if not raw:
            return 0.0
        cleaned = re.sub(r"[₹,\s]", "", str(raw))
        m = re.search(r"[+\-]?\d+(?:\.\d+)?", cleaned)
        return float(m.group(0)) if m else 0.0

    @classmethod
    def _parse_price_and_delta(cls, cell_text: str):
        parts = str(cell_text or "").split("(", 1)
        price = cls._parse_inr_number(parts[0])
        change = cls._parse_inr_number(parts[1]) if len(parts) > 1 else 0.0
        return price, change

    @staticmethod
    def _build_bullion_entry(
        price: float, change: float = 0.0, prev_close: float = 0.0, source: str = "GoodReturns"
    ) -> Dict[str, Any]:
        price = round(float(price), 2)
        if prev_close > 0:
            change = round(price - prev_close, 2)
            chg_pct = round((change / prev_close) * 100.0, 2)
        else:
            change = round(float(change), 2)
            base = price - change
            chg_pct = round((change / base) * 100.0, 2) if base > 0 else 0.0
        return {
            "price": price,
            "change": change,
            "change_pct": chg_pct,
            "source": source,
        }

    @classmethod
    def _parse_goodreturns_gold_html(cls, html: str) -> Dict[str, Dict[str, Any]]:
        import re
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for table in soup.find_all("table"):
            rows = [
                [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
                for tr in table.find_all("tr")
            ]
            rows = [r for r in rows if r]
            if not rows:
                continue
            headers = [h.upper() for h in rows[0]]
            idx_24 = next((i for i, h in enumerate(headers) if "24K" in h), None)
            idx_22 = next((i for i, h in enumerate(headers) if "22K" in h), None)
            if idx_24 is None or idx_22 is None:
                continue

            row_10, row_1 = None, None
            for r in rows[1:]:
                qty = r[0].strip().lower()
                if re.match(r"^10(?:\s*g(?:m|ms|ram|rams)?)?$", qty):
                    row_10 = r
                    break
                if re.match(r"^1(?:\s*g(?:m|ms|ram|rams)?)?$", qty):
                    row_1 = r

            target_row, mult = (row_10, 1.0) if row_10 else (row_1, 10.0)
            if not target_row or max(idx_24, idx_22) >= len(target_row):
                continue

            p24, d24 = cls._parse_price_and_delta(target_row[idx_24])
            p22, d22 = cls._parse_price_and_delta(target_row[idx_22])
            p24, d24 = p24 * mult, d24 * mult
            p22, d22 = p22 * mult, d22 * mult
            if 40000 <= p24 <= 500000 and 35000 <= p22 <= 480000 and p24 > p22:
                return {
                    "Gold 24K (₹/10g)": cls._build_bullion_entry(p24, change=d24),
                    "Gold 22K (₹/10g)": cls._build_bullion_entry(p22, change=d22),
                }
        return {}

    @classmethod
    def _parse_goodreturns_silver_html(cls, html: str) -> Dict[str, Dict[str, Any]]:
        import re
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for table in soup.find_all("table"):
            rows = [
                [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
                for tr in table.find_all("tr")
            ]
            rows = [r for r in rows if r]
            if not rows:
                continue
            headers = [h.upper() for h in rows[0]]
            if "TODAY" not in " ".join(headers):
                continue
            idx_today = next((i for i, h in enumerate(headers) if "TODAY" in h), 1)
            idx_yest = next((i for i, h in enumerate(headers) if "YESTERDAY" in h), None)
            idx_chg = next((i for i, h in enumerate(headers) if "CHANGE" in h), None)

            row_1kg, row_10g, row_1g = None, None, None
            for r in rows[1:]:
                qty = r[0].strip().lower()
                if re.match(r"^(?:1000(?:\s*g.*)?|1\s*kg)$", qty):
                    row_1kg = r
                    break
                if re.match(r"^10(?:\s*g.*)?$", qty):
                    row_10g = r
                elif re.match(r"^1(?:\s*g.*)?$", qty):
                    row_1g = r

            target_row, mult = (row_1kg, 1.0) if row_1kg else ((row_10g, 100.0) if row_10g else (row_1g, 1000.0))
            if not target_row or idx_today >= len(target_row):
                continue

            price, inline_delta = cls._parse_price_and_delta(target_row[idx_today])
            price, inline_delta = price * mult, inline_delta * mult
            prev_close = 0.0
            change = inline_delta
            if idx_yest is not None and idx_yest < len(target_row):
                prev_close = cls._parse_inr_number(target_row[idx_yest]) * mult
            elif idx_chg is not None and idx_chg < len(target_row):
                change = cls._parse_inr_number(target_row[idx_chg]) * mult

            if 40000 <= price <= 500000:
                return {
                    "Silver (₹/kg)": cls._build_bullion_entry(price, change=change, prev_close=prev_close)
                }
        return {}

    @classmethod
    def _derive_bullion_from_fx(
        cls,
        usd_quote: Dict[str, Any],
        usd_inr: Dict[str, Any],
        grams: float,
        duty_premium_factor: float,
        purity_ratio: float = 1.0,
    ) -> Optional[Dict[str, Any]]:
        metal_p = usd_quote.get("price", 0.0)
        inr_p = usd_inr.get("price", 0.0)
        if metal_p <= 0 or inr_p <= 0:
            return None
        inr_per_gram = (metal_p * inr_p) / 31.1034768
        est_price = round((inr_per_gram * grams * duty_premium_factor * purity_ratio) / 10.0) * 10.0
        m_chg = usd_quote.get("change_pct", 0.0)
        fx_chg = usd_inr.get("change_pct", 0.0)
        combo_pct = ((1.0 + m_chg / 100.0) * (1.0 + fx_chg / 100.0) - 1.0) * 100.0
        prev_close = est_price / (1.0 + combo_pct / 100.0) if (1.0 + combo_pct / 100.0) > 0 else est_price
        return cls._build_bullion_entry(est_price, prev_close=prev_close, source="COMEX+FX Derived")

    def fetch_indian_bullion_rates(
        self,
        gold_usd: Optional[Dict[str, Any]] = None,
        silver_usd: Optional[Dict[str, Any]] = None,
        usd_inr: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch live Indian Gold 24K (₹/10g), Gold 22K (₹/10g), and Silver (₹/kg) rates with COMEX+FX fallback."""
        import requests
        from concurrent.futures import ThreadPoolExecutor

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        gold_usd = gold_usd or self.fetch_quote_fast("GC=F")
        silver_usd = silver_usd or self.fetch_quote_fast("SI=F")
        usd_inr = usd_inr or self.fetch_quote_fast("INR=X")

        def _fetch_html(url: str) -> str:
            try:
                resp = requests.get(url, headers=headers, timeout=6)
                return resp.text if resp.status_code == 200 else ""
            except Exception:
                return ""

        with ThreadPoolExecutor(max_workers=2) as pool:
            f_gold = pool.submit(_fetch_html, self.BULLION_URLS["gold"])
            f_silver = pool.submit(_fetch_html, self.BULLION_URLS["silver"])
            gold_html = f_gold.result()
            silver_html = f_silver.result()

        results: Dict[str, Dict[str, Any]] = {}
        if gold_html:
            results.update(self._parse_goodreturns_gold_html(gold_html))
        if silver_html:
            results.update(self._parse_goodreturns_silver_html(silver_html))

        if "Gold 24K (₹/10g)" not in results:
            g24 = self._derive_bullion_from_fx(gold_usd, usd_inr, grams=10.0, duty_premium_factor=1.167, purity_ratio=1.0)
            if g24:
                results["Gold 24K (₹/10g)"] = g24
        if "Gold 22K (₹/10g)" not in results:
            if "Gold 24K (₹/10g)" in results:
                g24_entry = results["Gold 24K (₹/10g)"]
                ratio = 22.0 / 24.0
                results["Gold 22K (₹/10g)"] = self._build_bullion_entry(
                    round((g24_entry["price"] * ratio) / 10.0) * 10.0,
                    change=round(g24_entry["change"] * ratio, 2),
                    source=g24_entry.get("source", "Derived"),
                )
            else:
                g22 = self._derive_bullion_from_fx(
                    gold_usd, usd_inr, grams=10.0, duty_premium_factor=1.167, purity_ratio=22.0 / 24.0
                )
                if g22:
                    results["Gold 22K (₹/10g)"] = g22
        if "Silver (₹/kg)" not in results:
            sil = self._derive_bullion_from_fx(silver_usd, usd_inr, grams=1000.0, duty_premium_factor=1.328, purity_ratio=1.0)
            if sil:
                results["Silver (₹/kg)"] = sil

        return results

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

        raw_macro = {}
        for name, ticker in self.COMMODITY_TICKERS.items():
            raw_macro[name] = self.fetch_quote_fast(ticker)

        bullion_rates = self.fetch_indian_bullion_rates(
            gold_usd=raw_macro.get("Gold ($/oz)", {}),
            silver_usd=raw_macro.get("Silver ($/oz)", {}),
            usd_inr=raw_macro.get("USD / INR", {}),
        )

        # Keep display order: Brent, 10Y Yield, DXY -> Indian 24K Gold, 22K Gold, Silver -> Global spot & FX
        macro_data = {}
        for k in ["Brent Crude ($/bbl)", "US 10-Yr Yield (%)", "US Dollar Index (DXY)"]:
            if k in raw_macro:
                macro_data[k] = raw_macro[k]
        for k in ["Gold 24K (₹/10g)", "Gold 22K (₹/10g)", "Silver (₹/kg)"]:
            if k in bullion_rates:
                macro_data[k] = bullion_rates[k]
        for k, v in raw_macro.items():
            if k not in macro_data:
                macro_data[k] = v

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

