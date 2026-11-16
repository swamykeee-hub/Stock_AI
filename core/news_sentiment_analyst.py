import urllib.parse
import xml.etree.ElementTree as ET
import requests
from typing import List, Dict, Any, Tuple
from datetime import datetime

class NewsSentimentAnalyst:
    """
    Advanced financial news & sentiment analyst.
    Queries real-time Indian financial news (Google News RSS), classifies events by severity,
    and detects critical corporate governance, forensic, regulatory, and earnings catalysts
    for both Buy discovery and Portfolio Sell/Exit warnings.
    """

    CRITICAL_BEARISH_KEYWORDS = [
        "sebi probe", "sebi notice", "cbi probe", "ed probe", "fraud", "auditor resigns",
        "forensic audit", "debt default", "insolvency", "nclt", "us fda warning", "import alert",
        "oai status", "promoter pledged", "pledge increased", "strike", "delisting",
        "q1 net loss", "q2 net loss", "q3 net loss", "q4 net loss", "profit sinks", "crash",
        "tax evasion", "cfo resigns", "ceo resigns abruptly", "governance lapse", "fined by sebi"
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

    def fetch_stock_news(self, symbol: str, company_name: str = "", limit: int = 12) -> List[Dict[str, Any]]:
        """Queries Google News RSS for Indian market context."""
        clean_sym = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
        query_term = f"{clean_sym} share price OR {company_name} NSE stock" if company_name else f"{clean_sym} share price NSE"
        encoded_query = urllib.parse.quote(query_term)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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

                    sentiment, score_contrib, is_critical = self._evaluate_headline_event(title)
                    articles.append({
                        "title": title,
                        "source": source,
                        "pubDate": pub_date,
                        "link": link,
                        "sentiment": sentiment,
                        "weight": score_contrib,
                        "is_critical": is_critical
                    })
        except Exception as e:
            articles.append({
                "title": f"Live market news feed momentarily offline ({str(e)})",
                "source": "Market Feed",
                "pubDate": str(datetime.now()),
                "link": "#",
                "sentiment": "Neutral",
                "weight": 0,
                "is_critical": False
            })

        return articles

    def _evaluate_headline_event(self, text: str) -> Tuple[str, float, bool]:
        """Classifies headline sentiment with severity grading for senior fund manager auditing."""
        lower = text.lower()

        # Check critical events first
        for kw in self.CRITICAL_BEARISH_KEYWORDS:
            if kw in lower:
                return "Critical Bearish", -4.0, True

        for kw in self.CRITICAL_BULLISH_KEYWORDS:
            if kw in lower:
                return "Strong Bullish", +3.0, False

        # Regular catalysts
        bear_matches = sum(1 for kw in self.BEARISH_KEYWORDS if kw in lower)
        bull_matches = sum(1 for kw in self.BULLISH_KEYWORDS if kw in lower)

        if bear_matches > bull_matches:
            return "Bearish", -2.0, False
        elif bull_matches > bear_matches:
            return "Bullish", +1.5, False

        return "Neutral", 0.0, False

    def analyze(self, symbol: str, company_name: str = "") -> Dict[str, Any]:
        """Generates comprehensive news sentiment audit and sell risk evaluation."""
        articles = self.fetch_stock_news(symbol, company_name)
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
                "sell_risk_score": 3.0,
                "top_bearish_catalysts": [],
                "top_bullish_catalysts": []
            }

        crit_bear_count = sum(1 for a in articles if a["sentiment"] == "Critical Bearish")
        reg_bear_count = sum(1 for a in articles if a["sentiment"] == "Bearish")
        crit_bull_count = sum(1 for a in articles if a["sentiment"] == "Strong Bullish")
        reg_bull_count = sum(1 for a in articles if a["sentiment"] == "Bullish")

        total_bull = crit_bull_count + reg_bull_count
        total_bear = crit_bear_count + reg_bear_count
        neutral_count = len(articles) - total_bull - total_bear

        critical_alerts = [a["title"] for a in articles if a.get("is_critical", False)]
        has_critical = len(critical_alerts) > 0

        # Sentiment Delta Calculation:
        # Critical bearish events heavily penalize score
        sentiment_delta = (crit_bull_count * 2.5) + (reg_bull_count * 1.5) - (crit_bear_count * 4.0) - (reg_bear_count * 2.0)
        raw_score = 5.0 + sentiment_delta
        final_score = max(1.0, min(round(raw_score, 1), 10.0))

        # Sell risk score (1.0 = safe, 10.0 = emergency sell risk)
        raw_sell_risk = 2.0 + (crit_bear_count * 4.0) + (reg_bear_count * 1.5) - (total_bull * 1.0)
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
            "critical_alerts": critical_alerts,
            "sell_risk_score": sell_risk,
            "top_bearish_catalysts": top_bear,
            "top_bullish_catalysts": top_bull
        }
