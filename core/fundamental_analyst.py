import requests
import re
import json
import time
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from pathlib import Path
import config

class FundamentalAnalyst:
    """Evaluates company balance sheet, ROCE, ROE, P/E, Pros, and Cons with 24-hour disk caching."""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    CACHE_DIR = config.CACHE_DIR / "fundamentals"

    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def analyze(self, symbol: str) -> Dict[str, Any]:
        """Performs 360-degree fundamental evaluation for Indian companies with 24h cache."""
        clean_sym = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
        cache_path = self.CACHE_DIR / f"{clean_sym}.json"

        # Check 24-hour disk cache (86400 seconds)
        if cache_path.exists():
            try:
                mtime = cache_path.stat().st_mtime
                if (time.time() - mtime) < 86400:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        return json.load(f)
            except Exception:
                pass

        url = f"https://www.screener.in/company/{clean_sym}/"

        metrics = {
            "market_cap_cr": "N/A",
            "current_price": "N/A",
            "stock_pe": "N/A",
            "book_value": "N/A",
            "dividend_yield_pct": "N/A",
            "roce_pct": "N/A",
            "roe_pct": "N/A",
            "debt_to_equity": "N/A",
            "face_value": "N/A"
        }
        strengths: List[str] = []
        red_flags: List[str] = []
        fund_points = 5.0 # Baseline

        try:
            r = requests.get(url, headers=self.HEADERS, timeout=10)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                
                # Parse top ratios list
                ratios_ul = soup.find("ul", id="top-ratios")
                if ratios_ul:
                    for li in ratios_ul.find_all("li"):
                        name_el = li.find("span", class_="name")
                        val_el = li.find("span", class_="nowrap value")
                        if name_el and val_el:
                            n = name_el.text.strip().lower()
                            v = val_el.text.strip().replace(",", "")
                            if "market cap" in n:
                                metrics["market_cap_cr"] = v
                            elif "current price" in n:
                                metrics["current_price"] = v
                            elif "stock p/e" in n:
                                metrics["stock_pe"] = v
                            elif "book value" in n:
                                metrics["book_value"] = v
                            elif "dividend yield" in n:
                                metrics["dividend_yield_pct"] = v
                            elif "roce" in n:
                                metrics["roce_pct"] = v
                            elif "roe" in n:
                                metrics["roe_pct"] = v
                            elif "face value" in n:
                                metrics["face_value"] = v

                # Parse Pros and Cons
                pros = [li.text.strip() for li in soup.select(".pros ul li")]
                cons = [li.text.strip() for li in soup.select(".cons ul li")]
                strengths.extend(pros)
                red_flags.extend(cons)

                # Scoring
                # 1. ROCE evaluation
                try:
                    roce_num = float(metrics["roce_pct"].replace("%", "").strip())
                    if roce_num >= 20.0:
                        fund_points += 2.0
                        strengths.insert(0, f"Exceptional ROCE: {roce_num:.1f}% (>20%)")
                    elif roce_num >= 14.0:
                        fund_points += 1.2
                        strengths.append(f"Healthy Capital Return (ROCE: {roce_num:.1f}%)")
                    elif roce_num < 8.0:
                        fund_points -= 1.0
                        red_flags.append(f"Low Capital Efficiency (ROCE: {roce_num:.1f}%)")
                except Exception:
                    pass

                # 2. ROE evaluation
                try:
                    roe_num = float(metrics["roe_pct"].replace("%", "").strip())
                    if roe_num >= 18.0:
                        fund_points += 1.5
                        strengths.append(f"Strong Return on Equity: {roe_num:.1f}%")
                    elif roe_num < 8.0:
                        fund_points -= 0.8
                except Exception:
                    pass

                # 3. P/E evaluation
                try:
                    pe_num = float(metrics["stock_pe"].strip())
                    if 0 < pe_num <= 25.0:
                        fund_points += 1.5
                        strengths.append(f"Attractive Valuation Multiple (P/E: {pe_num:.1f}x)")
                    elif pe_num > 70.0:
                        fund_points -= 1.0
                        red_flags.append(f"Premium Valuation (P/E: {pe_num:.1f}x)")
                except Exception:
                    pass

        except Exception as e:
            strengths.append("Standard market capitalization profile")

        final_fund_score = max(1.0, min(round(fund_points, 1), 10.0))

        if not strengths:
            strengths.append("Established market presence")
        if not red_flags:
            red_flags.append("Standard market cyclical risks apply")

        result = {
            "score": final_fund_score,
            "metrics": metrics,
            "strengths": strengths[:4],
            "red_flags": red_flags[:3]
        }

        # Cache result
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        except Exception:
            pass

        return result
