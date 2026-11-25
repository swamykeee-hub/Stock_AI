import json
import urllib.parse
import xml.etree.ElementTree as ET
import requests
from typing import List, Dict, Any, Tuple
from datetime import datetime
import config


class NewsSentimentAnalyst:
    """
    Financial news & governance risk analyst.
    Resolves full company names from NSE catalog to prevent ticker acronym collisions,
    filters out generic market-wide crash listicles / past recovery headlines,
    and isolates genuine company-specific regulatory, forensic, and earnings catalysts.
    """

    STRICT_GOVERNANCE_KEYWORDS = [
        "sebi probe", "sebi notice", "cbi probe", "ed probe", "fraud", "auditor resigns",
        "forensic audit", "debt default", "insolvency", "nclt", "us fda warning", "import alert",
        "oai status", "tax evasion", "cfo resigns", "ceo resigns abruptly", "governance lapse",
        "fined by sebi", "delisting"
    ]

    CONTEXTUAL_NEGATIVE_KEYWORDS = [
        "q1 net loss", "q2 net loss", "q3 net loss", "q4 net loss", "profit sinks",
        "pledge increased", "strike", "crash"
    ]

    GENERIC_MARKET_NOISE_PHRASES = [
        "stock market crash", "sensex falls", "nifty falls", "top losers today",
        "why sensex", "market crash", "rebounds", "recovers after", "bounces back"
    ]

    BEARISH_KEYWORDS = [
        "slump", "fall", "plunge", "loss", "profit drops", "profit falls", "downgrade",
        "selloff", "sell rating", "probe", "penalty", "margin pressure", "margin contracts",
        "weak guidance", "cut target", "fii sell", "underperform", "subdued", "cautious",
        "tax notice", "curbs", "headwinds", "slowdown", "weak demand", "inventory pileup"
    ]

    CRITICAL_BULLISH_KEYWORDS = [
        "record profit", "profit surges", "order win", "bags order", "us fda approval",
        "eir received", "expansion", "acquisition", "upgrade", "buy rating", "target raised",
        "debt free", "multibagger", "fii buy", "q1 profit surges", "q2 profit surges",
        "q3 profit surges", "q4 profit surges", "margin expands", "pli approval"
    ]

    BULLISH_KEYWORDS = [
        "surge", "jump", "rally", "high growth", "dividend", "outperform", "breakout",
        "green light", "turnaround", "capacity expansion", "capex", "market share gain",
        "block deal", "bulk deal", "promoter buying", "insider buy"
    ]

    _COMPANY_NAME_MAP: Dict[str, str] = {}

    @classmethod
    def _resolve_company_name(cls, clean_sym: str, company_name: str = "") -> str:
        """Resolves official company name from nse_stocks.json to eliminate short-ticker ambiguity."""
        if company_name and company_name.strip().upper() != clean_sym:
            return company_name.strip()
        if not cls._COMPANY_NAME_MAP:
            try:
                catalog_path = config.DATA_DIR / "nse_stocks.json"
                if catalog_path.exists():
                    with open(catalog_path, "r", encoding="utf-8") as f:
                        for item in json.load(f):
                            s = item.get("symbol", "").strip().upper()
                            n = item.get("name", "").strip()
                            if s and n:
                                cls._COMPANY_NAME_MAP[s] = n
            except Exception:
                pass
        return cls._COMPANY_NAME_MAP.get(clean_sym, clean_sym)

    def fetch_stock_news(self, symbol: str, company_name: str = "", limit: int = 12) -> List[Dict[str, Any]]:
        """Queries Google News RSS using resolved company name + exchange context."""
        clean_sym = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
        resolved_name = self._resolve_company_name(clean_sym, company_name)
        short_brand = resolved_name.replace(" Ltd.", "").replace(" Limited", "").strip()

        query_term = (
            f'"{short_brand}" OR {clean_sym} NSE share'
            if short_brand and short_brand.upper() != clean_sym
            else f"{clean_sym} share price NSE"
        )
        encoded_query = urllib.parse.quote(query_term)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        }

        articles = []
        try:
            resp = requests.get(rss_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall(".//item")[:limit]:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                    source = item.find("source").text if item.find("source") is not None else "Financial News"

                    sentiment, score_contrib, is_strict_gov, is_ctx_neg = self._evaluate_headline_event(
                        title, clean_sym, short_brand
                    )
                    articles.append({
                        "title": title,
                        "source": source,
                        "pubDate": pub_date,
                        "link": link,
                        "sentiment": sentiment,
                        "weight": score_contrib,
                        "is_strict_governance": is_strict_gov,
                        "is_critical": is_strict_gov or is_ctx_neg,
                    })
        except Exception as e:
            articles.append({
                "title": f"Live market news feed momentarily offline ({str(e)})",
                "source": "Market Feed",
                "pubDate": str(datetime.now()),
                "link": "#",
                "sentiment": "Neutral",
                "weight": 0,
                "is_strict_governance": False,
                "is_critical": False,
            })

        return articles

    def _evaluate_headline_event(
        self, text: str, clean_sym: str = "", brand_name: str = ""
    ) -> Tuple[str, float, bool, bool]:
        """Classifies headline sentiment while guarding against generic roundup false positives."""
        lower = text.lower()
        is_generic_roundup = any(p in lower for p in self.GENERIC_MARKET_NOISE_PHRASES)

        mentions_company = True
        if clean_sym or brand_name:
            first_word = brand_name.split()[0].lower() if brand_name else ""
            mentions_company = (
                (clean_sym.lower() in lower)
                or (len(first_word) >= 4 and first_word in lower)
            )

        # 1. Strict governance / regulatory hazards (explicit company attribution required)
        if mentions_company and any(kw in lower for kw in self.STRICT_GOVERNANCE_KEYWORDS):
            return "Critical Bearish", -4.0, True, False

        # 2. Severe operational negative headlines (suppress generic market-crash roundups)
        if mentions_company and not is_generic_roundup and any(kw in lower for kw in self.CONTEXTUAL_NEGATIVE_KEYWORDS):
            return "Critical Bearish", -3.0, False, True

        # 3. Structural bullish catalysts
        if not is_generic_roundup and any(kw in lower for kw in self.CRITICAL_BULLISH_KEYWORDS):
            return "Strong Bullish", +3.0, False, False

        bear_matches = sum(1 for kw in self.BEARISH_KEYWORDS if kw in lower)
        bull_matches = sum(1 for kw in self.BULLISH_KEYWORDS if kw in lower)

        if bear_matches > bull_matches:
            return "Bearish", -1.8 if not is_generic_roundup else -0.5, False, False
        if bull_matches > bear_matches:
            return "Bullish", +1.5, False, False

        return "Neutral", 0.0, False, False

    def analyze(self, symbol: str, company_name: str = "") -> Dict[str, Any]:
        """Generates news sentiment audit with multi-article confirmation for critical alerts."""
        clean_sym = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
        resolved_name = self._resolve_company_name(clean_sym, company_name)
        articles = self.fetch_stock_news(clean_sym, resolved_name)

        if not articles:
            return {
                "score": 5.0,
                "sentiment_label": "Balanced / Neutral News Flow",
                "articles": [],
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
                "catalysts": [],
                "has_critical_bearish_event": False,
                "critical_alerts": [],
                "sell_risk_score": 2.5,
                "top_bearish_catalysts": [],
                "top_bullish_catalysts": [],
            }

        strict_gov_alerts = [a["title"] for a in articles if a.get("is_strict_governance")]
        all_crit_alerts = [a["title"] for a in articles if a.get("is_critical")]
        # Require either strict governance probe/fraud alert OR >=2 corroborated critical bearish articles
        has_critical = (len(strict_gov_alerts) >= 1) or (len(all_crit_alerts) >= 2)

        crit_bear_count = sum(1 for a in articles if a["sentiment"] == "Critical Bearish")
        reg_bear_count = sum(1 for a in articles if a["sentiment"] == "Bearish")
        crit_bull_count = sum(1 for a in articles if a["sentiment"] == "Strong Bullish")
        reg_bull_count = sum(1 for a in articles if a["sentiment"] == "Bullish")

        total_bull = crit_bull_count + reg_bull_count
        total_bear = crit_bear_count + reg_bear_count
        neutral_count = len(articles) - total_bull - total_bear

        sentiment_delta = (crit_bull_count * 2.2) + (reg_bull_count * 1.2) - (crit_bear_count * 3.5) - (reg_bear_count * 1.5)
        final_score = max(1.0, min(round(5.0 + sentiment_delta, 1), 10.0))

        raw_sell_risk = 2.0 + (len(strict_gov_alerts) * 4.5) + (crit_bear_count * 2.0) + (reg_bear_count * 1.0) - (total_bull * 0.8)
        sell_risk = max(1.0, min(round(raw_sell_risk, 1), 10.0))

        if has_critical:
            sentiment_label = "⚠️ HIGH-RISK BEARISH NEWS ALERT (Governance/Regulatory)"
        elif final_score >= 7.0:
            sentiment_label = "🔥 Strong Bullish News Catalyst"
        elif final_score >= 6.0:
            sentiment_label = "Positive / Bullish News Flow"
        elif final_score <= 3.5:
            sentiment_label = "Bearish News Flow / Headwinds"
        else:
            sentiment_label = "Balanced / Neutral News Flow"

        catalysts = [a["title"] for a in articles if a["sentiment"] in ["Strong Bullish", "Bullish", "Critical Bearish", "Bearish"]][:5]
        top_bear = [a["title"] for a in articles if a["sentiment"] in ["Critical Bearish", "Bearish"]][:3]
        top_bull = [a["title"] for a in articles if a["sentiment"] in ["Strong Bullish", "Bullish"]][:3]

        return {
            "score": final_score,
            "sentiment_label": sentiment_label,
            "articles": articles,
            "bullish_count": total_bull,
            "bearish_count": total_bear,
            "neutral_count": neutral_count,
            "catalysts": catalysts,
            "has_critical_bearish_event": has_critical,
            "critical_alerts": all_crit_alerts if has_critical else [],
            "sell_risk_score": sell_risk,
            "top_bearish_catalysts": top_bear,
            "top_bullish_catalysts": top_bull,
        }
