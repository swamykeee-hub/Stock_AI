import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
REPORTS_DIR = DATA_DIR / "reports"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Standard Output Destinations
DESKTOP_REPORT_PATH = Path.home() / "Desktop" / "Indian_Stock_AI_Report.html"

# Market Settings
DEFAULT_EXCHANGE = "NSE"
EXCHANGE_SUFFIX = ".NS"  # Yahoo Finance suffix for NSE
BSE_SUFFIX = ".BO"

# Technical Analysis Parameters
TECH_CONFIG = {
    "RSI_PERIOD": 14,
    "RSI_BULLISH_MIN": 50,
    "RSI_BULLISH_MAX": 72,
    "EMA_FAST": 20,
    "EMA_MEDIUM": 50,
    "EMA_SLOW": 200,
    "MACD_FAST": 12,
    "MACD_SLOW": 26,
    "MACD_SIGNAL": 9,
    "VOLUME_BREAKOUT_MULTIPLIER": 1.5,  # 1.5x average 20-day volume
    "ATR_PERIOD": 14,
}

# Fundamental Criteria
FUNDAMENTAL_CONFIG = {
    "MIN_ROCE": 15.0,           # >= 15%
    "MIN_ROE": 12.0,            # >= 12%
    "MAX_DEBT_TO_EQUITY": 1.5,  # <= 1.5
    "MIN_PROMOTER_HOLDING": 45.0, # >= 45%
    "MAX_PROMOTER_PLEDGE": 5.0, # <= 5%
    "MIN_3YR_PROFIT_GROWTH": 10.0 # >= 10%
}

# Daily Automation Settings
SCHEDULE_CONFIG = {
    "MORNING_TIME": "08:45",        # Daily morning scan before market open
    "EVENING_TIME": "18:00",        # Daily evening scan at 6:00 PM post-market
    "DAILY_SCAN_FILE": REPORTS_DIR / "latest_daily_scan.json",
    "DAILY_IPO_FILE": REPORTS_DIR / "latest_ipos.json",
    "DAILY_INST_FLOW_FILE": CACHE_DIR / "institutional_flow.json",
    "DAILY_CORP_ACTIONS_FILE": CACHE_DIR / "corporate_actions.json",
    "PERFORMANCE_SCORECARD_FILE": CACHE_DIR / "performance_scorecard.json"
}

# Telegram Alert Configuration (Free Instant Phone Notifications)
TELEGRAM_CONFIG = {
    "ENABLED": os.environ.get("STOCK_AI_TELEGRAM_ENABLED", "false").lower() in ("true", "1", "yes"),
    "BOT_TOKEN": os.environ.get("STOCK_AI_TELEGRAM_TOKEN", ""),
    "CHAT_ID": os.environ.get("STOCK_AI_TELEGRAM_CHAT_ID", "")
}

# Legal Disclaimer
DISCLAIMER = (
    "DISCLAIMER: This system is an AI-driven educational and research analytics tool. "
    "It does not provide SEBI-registered investment advice or guaranteed return recommendations. "
    "Stock markets involve risk. Always consult a certified financial advisor before trading."
)

