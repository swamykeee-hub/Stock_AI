from typing import List, Dict, Any, Optional
import json
from pathlib import Path

class MutualFundAnalyst:
    """
    Acts as a Senior Mutual Fund Research Analyst and Wealth Allocator.
    Provides institutional-grade mutual fund recommendations with comprehensive
    quantitative metrics, risk-adjusted ratios, and fund manager rationale.
    """

    RECOMMENDED_FUNDS = [
        # ==========================================
        # 1. FLEXI CAP & LARGE CAP (Core Compounders)
        # ==========================================
        {
            "id": "ppfas_flexi",
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
                "The fund uniquely holds a ~15-20% allocation in global mega-cap tech cash machines (Alphabet, Microsoft) acting as a natural currency hedge against INR depreciation. "
                "Its ultra-low portfolio turnover and high cash buffer during euphoric markets provides superior downside protection."
            ),
            "suitable_for": "Core long-term SIP portfolio for all conservative and aggressive equity investors."
        },
        {
            "id": "hdfc_flexi",
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
                "The fund aggressively capitalizes on market mispricings in out-of-favor large and mid-cap sectors before the broad street catches on. "
                "Maintains high conviction overweights in domestic private banks, manufacturing capex, and healthcare turnaround plays."
            ),
            "suitable_for": "Investors seeking aggressive alpha from cyclical turnaround and value-unlocking themes."
        },

        # ==========================================
        # 2. MID CAP FUNDS (High Growth Momentum)
        # ==========================================
        {
            "id": "motilal_midcap",
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
                "The top-performing high-momentum mid-cap fund in India. "
                "Niket Shah implements a high active-share, concentrated strategy targeting businesses at the inflection point of exponential earnings growth. "
                "The fund heavily participated in massive multibaggers like Trent, Dixon, and healthcare leaders like Laurus Labs and Persistent Systems. "
                "Exceptional portfolio EPS growth velocity (>25%) justifies higher portfolio valuation multiples."
            ),
            "suitable_for": "Aggressive growth investors wanting direct institutional exposure to explosive midcap market leaders."
        },
        {
            "id": "kotak_emerging",
            "name": "Kotak Emerging Equity Fund",
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
                "The most resilient mid-cap fund with best-in-class downside risk management. "
                "Unlike peers who chase ephemeral momentum, Kotak focuses rigorously on companies with dominant economic moats, clean corporate governance, and high ROCE (>18%). "
                "Heavy structural tilt towards domestic capital goods, precision engineering, and specialized industrial manufacturing."
            ),
            "suitable_for": "Long-term wealth builders who want midcap returns without excessive volatility during market drawdowns."
        },

        # ==========================================
        # 3. SMALL CAP FUNDS (Aggressive Wealth Multipliers)
        # ==========================================
        {
            "id": "nippon_smallcap",
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
                "India's largest and most battle-hardened small-cap fund. "
                "Samir Rachh maintains hyper-diversification across 180+ small businesses, effectively mitigating individual stock insolvency or liquidity risks. "
                "Unequalled proprietary bottom-up research capabilities that discover hidden market gems 18-24 months before institutional coverage initiates."
            ),
            "suitable_for": "Disciplined monthly SIP investors looking to build generational wealth over 7 to 10 year horizons."
        },
        {
            "id": "quant_smallcap",
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
                "Operates on Quant AMC's proprietary VLRT framework (Valuation, Liquidity, Risk appetite, and Timing). "
                "Aggressively rotates capital into high-velocity momentum sectors and does not hesitate to hold high cash or liquid large caps when small-cap valuations froth. "
                "Produces blistering upside capture during raging bull markets."
            ),
            "suitable_for": "High-risk tolerance investors comfortable with frequent portfolio churn and quantitative factor rotation."
        },

        # ==========================================
        # 4. SECTORAL & THEMATIC FUNDS (Megatrends)
        # ==========================================
        {
            "id": "nippon_pharma",
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
                "Direct sectoral vehicle to capture the multi-year secular bull market in Indian CDMO, API manufacturing, and formulations. "
                "Directly holds high-flying momentum stocks like Laurus Labs (+139% 1Y) and Divi's Lab along with defensive domestic pharma powerhouses. "
                "US FDA clearance cycles, patent expiries in the US/EU, and China+1 supply chain diversification make this a must-have tactical satellite allocation."
            ),
            "suitable_for": "Tactical thematic investors wanting focused participation in the pharmaceutical and CDMO revival supercycle."
        },
        {
            "id": "icici_infra",
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
                "Riding India's massive ₹111 lakh crore National Infrastructure Pipeline and private capex expansion. "
                "Heavy investments into power transmission, railway electrification, defense fabrication, and telecom infrastructure. "
                "Top-tier earnings visibility backed by record multi-year order books."
            ),
            "suitable_for": "Investors seeking high-octane growth driven by Government capex and domestic industrial revitalization."
        }
    ]

    def get_all_funds(self) -> List[Dict[str, Any]]:
        """Returns all curated institutional fund recommendations."""
        return self.RECOMMENDED_FUNDS

    def filter_funds(self, category: Optional[str] = None, min_3y_cagr: float = 0.0) -> List[Dict[str, Any]]:
        """Filters mutual funds by category and historical CAGR threshold."""
        funds = self.RECOMMENDED_FUNDS
        if category and category != "All":
            funds = [f for f in funds if category.lower() in f["category"].lower()]
        if min_3y_cagr > 0:
            funds = [f for f in funds if f["return_3y_cagr"] >= min_3y_cagr]
        return funds

    def get_fund_by_id(self, fund_id: str) -> Optional[Dict[str, Any]]:
        """Returns single fund details by ID."""
        for f in self.RECOMMENDED_FUNDS:
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
        else:
            return {
                "profile": "Balanced / Moderate Growth (12-14% Target CAGR)",
                "allocation": [
                    {"category": "Flexi Cap Funds (Parag Parikh & HDFC)", "percentage": 50, "purpose": "Rock-Solid Core Wealth Compounder"},
                    {"category": "Mid Cap Funds (Kotak Emerging Equity)", "percentage": 30, "purpose": "Controlled Beta Growth"},
                    {"category": "Small Cap Funds (Nippon India Small Cap)", "percentage": 10, "purpose": "High-Growth Booster"},
                    {"category": "Arbitrage / Liquid Reserve", "percentage": 10, "purpose": "Capital Preservation & Volatility Cushion"}
                ],
                "sip_advice": "Ideal for 5+ year horizons with low portfolio volatility and peace of mind."
            }

