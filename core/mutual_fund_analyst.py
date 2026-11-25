import json
import math
import time
import concurrent.futures
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import config


class MutualFundAnalyst:
    """
    Senior Mutual Fund Research Analyst & Wealth Allocator.
    Enriches curated institutional mutual funds with live AMFI NAVs, real 1Y returns,
    real 3Y & 5Y annualized CAGRs, and calculated 3-Year Sharpe ratios via api.mfapi.in
    with 12-hour disk caching and safe offline fallback.
    """

    CACHE_FILE = config.CACHE_DIR / "mutual_funds_cache.json"

    RECOMMENDED_FUNDS = [
        {
            "id": "ppfas_flexi",
            "amfi_code": 122639,
            "name": "Parag Parikh Flexi Cap Fund",
            "fund_house": "PPFAS Mutual Fund",
            "category": "Flexi Cap",
            "risk_profile": "Moderate to High",
            "min_horizon": "5+ Years",
            "aum_cr": 72450.0,
            "expense_ratio_pct": 0.63,
            "fund_manager": "Rajeev Thakkar & Raunak Onkar",
            "benchmark": "NIFTY 500 TRI",
            "return_1y": 28.4,
            "return_3y_cagr": 22.8,
            "return_5y_cagr": 24.2,
            "sharpe_ratio": 1.42,
            "alpha": 4.85,
            "beta": 0.76,
            "top_holdings": ["HDFC Bank", "Bajaj Holdings", "ITC", "Power Grid", "Alphabet (Google)", "Microsoft"],
            "cio_rationale": (
                "The undisputed gold standard for core equity wealth compounding in India. "
                "Manager Rajeev Thakkar exercises legendary discipline with a value-oriented 'Growth at Reasonable Price' (GARP) philosophy. "
                "The fund uniquely holds a ~15-20% allocation in global mega-cap tech cash machines (Alphabet, Microsoft) acting as a natural currency hedge against INR depreciation."
            ),
            "suitable_for": "Core long-term SIP portfolio for all conservative and aggressive equity investors."
        },
        {
            "id": "hdfc_flexi",
            "amfi_code": 118955,
            "name": "HDFC Flexi Cap Fund",
            "fund_house": "HDFC Mutual Fund",
            "category": "Flexi Cap",
            "risk_profile": "High",
            "min_horizon": "5+ Years",
            "aum_cr": 64800.0,
            "expense_ratio_pct": 0.81,
            "fund_manager": "Roshi Jain",
            "benchmark": "NIFTY 500 TRI",
            "return_1y": 32.1,
            "return_3y_cagr": 26.4,
            "return_5y_cagr": 23.5,
            "sharpe_ratio": 1.51,
            "alpha": 6.12,
            "beta": 0.94,
            "top_holdings": ["ICICI Bank", "HDFC Bank", "Infosys", "Cipla", "Larsen & Toubro", "SBI"],
            "cio_rationale": (
                "Roshi Jain's contrarian and cash-flow-driven stock-picking has established this fund as an alpha juggernaut. "
                "Capitalizes on market mispricings in domestic private banks, manufacturing capex, and healthcare turnaround plays."
            ),
            "suitable_for": "Investors seeking aggressive alpha from cyclical turnaround and value-unlocking themes."
        },
        {
            "id": "motilal_midcap",
            "amfi_code": 127042,
            "name": "Motilal Oswal Midcap Fund",
            "fund_house": "Motilal Oswal Mutual Fund",
            "category": "Mid Cap",
            "risk_profile": "Very High",
            "min_horizon": "5 - 7 Years",
            "aum_cr": 19500.0,
            "expense_ratio_pct": 0.68,
            "fund_manager": "Niket Shah",
            "benchmark": "NIFTY Midcap 150 TRI",
            "return_1y": 48.6,
            "return_3y_cagr": 34.2,
            "return_5y_cagr": 28.7,
            "sharpe_ratio": 1.74,
            "alpha": 9.40,
            "beta": 0.98,
            "top_holdings": ["Trent Ltd", "Persistent Systems", "Laurus Labs", "Kaynes Tech", "Dixon Tech", "Polycab"],
            "cio_rationale": (
                "High active-share, concentrated mid-cap strategy targeting businesses at the inflection point of exponential earnings growth. "
                "Heavily participated in multibaggers like Trent, Dixon, Persistent Systems, and healthcare leaders."
            ),
            "suitable_for": "Aggressive growth investors wanting direct institutional exposure to explosive midcap market leaders."
        },
        {
            "id": "kotak_emerging",
            "amfi_code": 119775,
            "name": "Kotak Mid Cap Fund (Emerging Equity)",
            "fund_house": "Kotak Mahindra Mutual Fund",
            "category": "Mid Cap",
            "risk_profile": "Very High",
            "min_horizon": "5+ Years",
            "aum_cr": 48200.0,
            "expense_ratio_pct": 0.72,
            "fund_manager": "Harsha Upadhyaya & Atul Bhole",
            "benchmark": "NIFTY Midcap 150 TRI",
            "return_1y": 36.4,
            "return_3y_cagr": 25.8,
            "return_5y_cagr": 24.9,
            "sharpe_ratio": 1.48,
            "alpha": 4.60,
            "beta": 0.82,
            "top_holdings": ["Supreme Industries", "Cummins India", "Schaeffler India", "Solar Industries", "Thermax"],
            "cio_rationale": (
                "Resilient mid-cap compounder focusing rigorously on dominant economic moats, clean governance, and high ROCE (>18%) "
                "across domestic capital goods and precision industrial manufacturing."
            ),
            "suitable_for": "Long-term wealth builders seeking midcap compounding with controlled drawdown risk."
        },
        {
            "id": "nippon_smallcap",
            "amfi_code": 118778,
            "name": "Nippon India Small Cap Fund",
            "fund_house": "Nippon Life India AMC",
            "category": "Small Cap",
            "risk_profile": "Very High",
            "min_horizon": "7+ Years",
            "aum_cr": 58600.0,
            "expense_ratio_pct": 0.70,
            "fund_manager": "Samir Rachh & Kinjal Desai",
            "benchmark": "NIFTY Smallcap 250 TRI",
            "return_1y": 42.8,
            "return_3y_cagr": 31.5,
            "return_5y_cagr": 33.4,
            "sharpe_ratio": 1.62,
            "alpha": 7.80,
            "beta": 0.88,
            "top_holdings": ["Tube Investments", "Apar Industries", "HBL Power", "Voltamp Transformers", "Karur Vysya Bank"],
            "cio_rationale": (
                "India's largest battle-hardened small-cap wealth multiplier maintaining hyper-diversification across emerging businesses, "
                "capturing bottom-up leaders 18-24 months before institutional coverage initiates."
            ),
            "suitable_for": "Disciplined monthly SIP investors looking to build generational wealth over 7 to 10 year horizons."
        },
        {
            "id": "quant_smallcap",
            "amfi_code": 120828,
            "name": "Quant Small Cap Fund",
            "fund_house": "Quant Mutual Fund",
            "category": "Small Cap",
            "risk_profile": "Extremely High (Dynamic Quant)",
            "min_horizon": "5 - 7 Years",
            "aum_cr": 24200.0,
            "expense_ratio_pct": 0.64,
            "fund_manager": "Sandeep Tandon & Sanjeev Sharma",
            "benchmark": "NIFTY Smallcap 250 TRI",
            "return_1y": 45.2,
            "return_3y_cagr": 36.1,
            "return_5y_cagr": 38.6,
            "sharpe_ratio": 1.69,
            "alpha": 10.85,
            "beta": 1.12,
            "top_holdings": ["Reliance Industries", "Bikaji Foods", "Jio Financial", "Adani Power", "HFCL"],
            "cio_rationale": (
                "Operates on Quant AMC's proprietary VLRT framework (Valuation, Liquidity, Risk appetite, Timing), dynamically rotating capital "
                "into high-velocity momentum sectors during bull expansions."
            ),
            "suitable_for": "High-risk tolerance investors comfortable with quantitative factor rotation."
        },
        {
            "id": "nippon_pharma",
            "amfi_code": 118759,
            "name": "Nippon India Pharma & Healthcare Fund",
            "fund_house": "Nippon Life India AMC",
            "category": "Thematic / Healthcare & CDMO",
            "risk_profile": "High (Sector Specific)",
            "min_horizon": "3 - 5 Years",
            "aum_cr": 8450.0,
            "expense_ratio_pct": 0.95,
            "fund_manager": "Sailesh Raj Bhan",
            "benchmark": "BSE Healthcare TRI",
            "return_1y": 46.5,
            "return_3y_cagr": 24.2,
            "return_5y_cagr": 23.8,
            "sharpe_ratio": 1.58,
            "alpha": 5.40,
            "beta": 0.79,
            "top_holdings": ["Sun Pharma", "Cipla", "Laurus Labs", "Divi's Laboratories", "Dr. Reddy's", "Lupin"],
            "cio_rationale": (
                "Direct sectoral vehicle capturing the multi-year secular bull run in Indian CDMO, API manufacturing, and formulations "
                "benefiting from China+1 outsourcing and specialty launches."
            ),
            "suitable_for": "Tactical thematic investors wanting focused participation in the pharmaceutical and CDMO supercycle."
        },
        {
            "id": "icici_infra",
            "amfi_code": 120621,
            "name": "ICICI Prudential Infrastructure Fund",
            "fund_house": "ICICI Prudential AMC",
            "category": "Thematic / Manufacturing & Infra",
            "risk_profile": "High (Sector Specific)",
            "min_horizon": "3 - 5 Years",
            "aum_cr": 6800.0,
            "expense_ratio_pct": 0.92,
            "fund_manager": "Ihab Dalwai",
            "benchmark": "NIFTY Infrastructure TRI",
            "return_1y": 52.4,
            "return_3y_cagr": 38.6,
            "return_5y_cagr": 31.2,
            "sharpe_ratio": 1.82,
            "alpha": 11.20,
            "beta": 0.96,
            "top_holdings": ["Larsen & Toubro", "NTPC", "Bharti Airtel", "BHEL", "Adani Ports", "Siemens India"],
            "cio_rationale": (
                "Riding India's massive National Infrastructure Pipeline, power transmission, railways, and defense fabrication "
                "backed by record multi-year capex order books."
            ),
            "suitable_for": "Investors seeking high-octane growth driven by domestic industrial capex revitalization."
        }
    ]

    def __init__(self):
        self.CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _find_nav_at_offset(entries: List[tuple], target_dt: datetime) -> Optional[float]:
        """Finds closest trading day NAV on or before target_dt (entries sorted newest first)."""
        for dt, nav in entries:
            if dt <= target_dt and nav > 0:
                return nav
        return entries[-1][1] if entries else None

    def _enrich_single_fund_live(self, base_fund: Dict[str, Any]) -> Dict[str, Any]:
        """Fetches live AMFI NAV series via api.mfapi.in and calculates real 1Y/3Y/5Y CAGR and Sharpe."""
        fund = dict(base_fund)
        code = fund.get("amfi_code")
        if not code:
            return fund

        try:
            url = f"https://api.mfapi.in/mf/{code}"
            r = requests.get(url, timeout=8)
            if r.status_code != 200:
                return fund
            payload = r.json()
            raw_data = payload.get("data", [])
            if not raw_data:
                return fund

            parsed: List[tuple] = []
            for row in raw_data:
                try:
                    dt = datetime.strptime(row["date"], "%d-%m-%Y")
                    nv = float(row["nav"])
                    if nv > 0:
                        parsed.append((dt, nv))
                except Exception:
                    continue

            if len(parsed) < 20:
                return fund

            # AMFI returns newest first, verify sort descending
            parsed.sort(key=lambda x: x[0], reverse=True)
            latest_dt, nav_now = parsed[0]

            nav_1y = self._find_nav_at_offset(parsed, latest_dt - timedelta(days=365))
            nav_3y = self._find_nav_at_offset(parsed, latest_dt - timedelta(days=365 * 3))
            nav_5y = self._find_nav_at_offset(parsed, latest_dt - timedelta(days=365 * 5))

            if nav_1y and nav_1y > 0:
                fund["return_1y"] = round(((nav_now / nav_1y) - 1.0) * 100.0, 1)
            if nav_3y and nav_3y > 0 and (latest_dt - parsed[-1][0]).days >= 950:
                fund["return_3y_cagr"] = round((((nav_now / nav_3y) ** (1.0 / 3.0)) - 1.0) * 100.0, 1)
            if nav_5y and nav_5y > 0 and (latest_dt - parsed[-1][0]).days >= 1700:
                fund["return_5y_cagr"] = round((((nav_now / nav_5y) ** (1.0 / 5.0)) - 1.0) * 100.0, 1)

            # Calculate 3-Year Sharpe Ratio from daily returns (Risk-Free Rate = 6.5% p.a.)
            cutoff_3y = latest_dt - timedelta(days=365 * 3)
            chrono_3y = sorted([(d, v) for d, v in parsed if d >= cutoff_3y], key=lambda x: x[0])
            if len(chrono_3y) >= 120:
                rets = [
                    (chrono_3y[i][1] - chrono_3y[i - 1][1]) / chrono_3y[i - 1][1]
                    for i in range(1, len(chrono_3y))
                ]
                mean_d = sum(rets) / len(rets)
                var_d = sum((x - mean_d) ** 2 for x in rets) / max(1, len(rets) - 1)
                ann_vol = math.sqrt(var_d) * math.sqrt(252.0)
                if ann_vol > 1e-4:
                    ann_ret = fund["return_3y_cagr"] / 100.0
                    fund["sharpe_ratio"] = round((ann_ret - 0.065) / ann_vol, 2)

            fund["nav"] = round(nav_now, 2)
            fund["nav_date"] = latest_dt.strftime("%d-%b-%Y")
            fund["is_live_nav"] = True
        except Exception:
            pass

        return fund

    def get_all_funds(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Returns institutional fund recommendations enriched with live AMFI NAVs & CAGRs (12h cache)."""
        if not force_refresh and self.CACHE_FILE.exists():
            try:
                if (time.time() - self.CACHE_FILE.stat().st_mtime) < 43200:
                    with open(self.CACHE_FILE, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                        if cached and isinstance(cached, list) and cached[0].get("is_live_nav"):
                            return cached
            except Exception:
                pass

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            enriched = list(executor.map(self._enrich_single_fund_live, self.RECOMMENDED_FUNDS))

        try:
            with open(self.CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(enriched, f, indent=2)
        except Exception:
            pass

        return enriched

    def filter_funds(self, category: Optional[str] = None, min_3y_cagr: float = 0.0) -> List[Dict[str, Any]]:
        """Filters live-enriched mutual funds by category and historical CAGR threshold."""
        funds = self.get_all_funds(force_refresh=False)
        if category and category != "All":
            funds = [f for f in funds if category.lower() in f["category"].lower()]
        if min_3y_cagr > 0:
            funds = [f for f in funds if f["return_3y_cagr"] >= min_3y_cagr]
        return funds

    def get_fund_by_id(self, fund_id: str) -> Optional[Dict[str, Any]]:
        """Returns single fund details by ID."""
        for f in self.get_all_funds(force_refresh=False):
            if f["id"] == fund_id:
                return f
        return None

    def get_portfolio_allocation_model(self, risk_profile: str = "Aggressive") -> Dict[str, Any]:
        """Provides senior fund manager asset allocation recommendation for mutual funds."""
        if risk_profile == "Aggressive":
            return {
                "profile": "Aggressive Wealth Creation (15%+ Target CAGR)",
                "allocation": [
                    {"category": "Mid Cap Funds (e.g. Motilal Oswal Midcap)", "percentage": 35, "purpose": "High-Alpha Market Leaders"},
                    {"category": "Small Cap Funds (e.g. Nippon India Small Cap)", "percentage": 25, "purpose": "Multi-Year Wealth Multipliers"},
                    {"category": "Flexi Cap Funds (e.g. Parag Parikh Flexi Cap)", "percentage": 25, "purpose": "Core Stability & Global Hedge"},
                    {"category": "Thematic / Healthcare (e.g. Nippon Pharma)", "percentage": 15, "purpose": "Tactical Trend Participation (Laurus Labs theme)"}
                ],
                "sip_advice": "Maintain disciplined monthly SIPs. Add 20% lumpsum top-up whenever Nifty corrects 4-6% from all-time highs."
            }
        return {
            "profile": "Balanced / Moderate Growth (12-14% Target CAGR)",
            "allocation": [
                {"category": "Flexi Cap Funds (Parag Parikh & HDFC)", "percentage": 50, "purpose": "Rock-Solid Core Wealth Compounder"},
                {"category": "Mid Cap Funds (Kotak Mid Cap)", "percentage": 30, "purpose": "Controlled Beta Growth"},
                {"category": "Small Cap Funds (Nippon India Small Cap)", "percentage": 10, "purpose": "High-Growth Booster"},
                {"category": "Arbitrage / Liquid Reserve", "percentage": 10, "purpose": "Capital Preservation & Volatility Cushion"}
            ],
            "sip_advice": "Ideal for 5+ year horizons with low portfolio volatility and peace of mind."
        }
