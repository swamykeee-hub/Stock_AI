# 🇮🇳 Indian Stock AI — Autonomous 360° Agentic Market Intelligence

An AI-driven autonomous stock analysis platform designed specifically for the **National Stock Exchange (NSE)** and **Bombay Stock Exchange (BSE)**. 

The system performs **360-degree stock verification** (Technicals, Fundamentals, News & Market Sentiment, and Risk Management), tracks **Indian IPOs & Grey Market Premiums (GMP)**, and executes **daily automated scans** to detect high-conviction bullish breakout stocks with buy/sell recommendations, target prices, and stop loss levels.

---

## 🌟 Key Capabilities

1. **360-Degree Stock Verification Engine**:
   - **Technical Analyst**: 20/50/200-day EMAs, RSI(14) momentum zones, MACD histogram crossovers, Bollinger Bands, Volume surges, and dynamic ATR-based targets and stop losses.
   - **Fundamental Analyst**: Evaluates P/E, PEG, Price-to-Book, Return on Equity (ROE), Debt-to-Equity ratios, Net Profit Margins, and YoY Revenue growth.
   - **News & Sentiment Analyst**: Real-time Google News RSS scraping of Indian financial media (Economic Times, LiveMint, Moneycontrol) to detect bullish catalysts and negative red flags.
   - **Synthesis Engine**: Generates a unified **Composite Score (0 to 10)** with clear Buy/Accumulate/Hold/Sell calls, risk-reward ratios, and time horizons.

2. **Autonomous Bullish Stock Scanner**:
   - Scans top NSE stocks in parallel using multi-threaded execution.
   - Identifies high-momentum breakout setups, volume accumulation, and pullback buys.
   - Generates actionable trade cards (CMP, Target 1, Target 2, Stop Loss).

3. **IPO Intelligence & GMP Tracker**:
   - Monitors upcoming, open, and recently listed Indian Mainboard & SME IPOs.
   - Tracks Issue Dates, Price Bands, Lot Sizes, Issue Size, Subscription rates, and Grey Market Premium (GMP).
   - Provides AI ratings (*Strong Apply*, *Apply for Listing Gains*, *Avoid*).

4. **Daily Autonomous Automation**:
   - Scheduled daily pre-market & post-market scans.
   - Generates an executive daily market briefing in Markdown (`data/reports/daily_briefing_YYYY-MM-DD.md`).

---

## 🚀 How to Run

### 1. Launch the Interactive Web Dashboard
Double-click `run_dashboard.bat` or run:
```bash
cd D:\STOCK_AI
py -3.14 -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

### 2. Run Daily Scan & Automation
Double-click `run_daily_scan.bat` or run:
```bash
cd D:\STOCK_AI
py -3.14 scheduler.py --run-now
```

To run as a continuous background daemon (monitoring pre-market at 08:45 AM and post-market at 15:45 PM):
```bash
py -3.14 scheduler.py --daemon
```

---

## 📁 Project Architecture

```
D:\STOCK_AI\
├── app.py                     # Streamlit interactive Web Application
├── scheduler.py               # Autonomous daily scan & sync runner
├── config.py                  # Thresholds, parameters, and paths
├── requirements.txt           # Dependencies list
├── run_dashboard.bat          # 1-Click launcher for Streamlit UI
├── run_daily_scan.bat         # 1-Click launcher for Daily Scan
├── core/
│   ├── market_data.py         # NSE/BSE price, OHLCV, and index feeds
│   ├── technical_analyst.py   # Indicators, trend, pivots, dynamic stop loss & target
│   ├── fundamental_analyst.py # Valuation, ROE, debt, margins, growth
│   ├── news_sentiment_analyst.py # News RSS, sentiment analysis & catalyst tracking
│   ├── ipo_analyst.py         # IPO tracker, subscription rates, GMP
│   ├── bullish_scanner.py     # Multi-threaded market scanner
│   └── synthesizer.py         # 360° decision engine & trade setup
└── data/
    ├── nse_stocks.json        # Curated list of top Indian stocks
    ├── cache/                 # Cached IPOs and quotes
    └── reports/               # Daily briefing reports
```

---

## ⚖️ Legal & SEBI Disclaimer
*This system is an AI-driven educational and research analytics tool. It does not provide SEBI-registered investment advice or guaranteed return recommendations. Stock markets involve risk. Always consult a certified financial advisor before trading.*

