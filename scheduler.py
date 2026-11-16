import time
import json
import argparse
from datetime import datetime
from pathlib import Path
import schedule
import config
from core.market_data import MarketDataManager
from core.bullish_scanner import BullishScanner
from core.momentum_screener import MomentumScreener
from core.fund_manager_radar import FundManagerRadar
from core.global_macro_news import GlobalMacroNewsAnalyst
from core.mutual_fund_analyst import MutualFundAnalyst
from core.ipo_analyst import IPOAnalyst
from core.html_generator import HTMLReportGenerator
from core.market_regime_analyst import MarketRegimeAnalyst

class DailyAutomator:
    """Manages autonomous daily scans, IPO updates, momentum rankings, and market intelligence generation."""

    def __init__(self):
        self.market_data = MarketDataManager()
        self.scanner = BullishScanner()
        self.momentum_screener = MomentumScreener()
        self.fund_radar = FundManagerRadar()
        self.macro_news = GlobalMacroNewsAnalyst()
        self.mf_analyst = MutualFundAnalyst()
        self.ipo_analyst = IPOAnalyst()
        self.regime_analyst = MarketRegimeAnalyst()

    def run_daily_sync(self):
        """Executes full daily automation pipeline."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_stamp = datetime.now().strftime("%Y-%m-%d")
        print(f"\n[{now_str}] Starting Autonomous Daily Stock AI Cycle...")

        # 1. Benchmark Indices Update
        print("  -> Fetching Indian Benchmark Indices...")
        indices = self.market_data.get_benchmark_indices()

        # 2. Global Macro Snapshot
        print("  -> Fetching Global Macro & Commodities...")
        macro_snap = self.macro_news.get_global_markets_snapshot()

        # 2b. CIO Market Regime & Sector Rotation
        print("  -> Evaluating Market Regime & Sector Rotation...")
        market_regime = self.regime_analyst.evaluate_market_regime()

        # 3. Multi-Timeframe Momentum Ranking (Laurus Labs, etc.)
        print("  -> Screened Multi-Timeframe Super-Trend Stocks (3M, 6M, 1Y, 3Y)...")
        momentum_stocks = self.momentum_screener.scan_universe(force_refresh=True)

        # 4. Bullish Stock Scanning (360° Setups)
        print("  -> Scanning Indian market for Bullish 360-degree setups...")
        bullish_picks = self.scanner.scan_market(max_stocks=35, max_workers=8)
        print(f"  -> Discovered {len(bullish_picks)} high-conviction bullish candidates.")

        # 5. AI Fund Manager Radar
        print("  -> Updating AI Fund Manager Monitored Radar...")
        monitored_radar = self.fund_radar.get_monitored_stocks(sync_live_prices=True)

        # 6. Mutual Fund Advisory Recommendations
        print("  -> Syncing Institutional Mutual Fund Picks...")
        mutual_funds = self.mf_analyst.get_all_funds()

        # 7. Pre-compute Enriched Stock Profiles (TCS, INFY, etc. with Buy Entry Strategy)
        print("  -> Compiling Enriched Stock Profiles & Buy Entry Intelligence...")
        try:
            from core.stock_profile_manager import StockProfileManager
            profile_mgr = StockProfileManager()
            profile_mgr.build_all_benchmark_profiles()
        except Exception as e:
            print(f"  -> Profile build notice: {e}")

        # 8. Dynamic 52-Week High Breakouts & Deep Analysis (Fresh Daily Tracking)
        print("  -> Tracking & Analyzing Dynamic 52-Week High Breakout Leaders...")
        fifty_two_week_stocks = []
        try:
            from core.fifty_two_week_high_tracker import FiftyTwoWeekHighTracker
            tracker_52w = FiftyTwoWeekHighTracker()
            fifty_two_week_stocks = tracker_52w.scan_52_week_highs(force_refresh=True)
            print(f"  -> Discovered {len(fifty_two_week_stocks)} stocks at/near 52-Week High.")
        except Exception as e:
            print(f"  -> 52W High tracker note: {e}")

        # 9. IPO Updates
        print("  -> Syncing latest Indian IPOs and GMP trends...")
        ipo_data = self.ipo_analyst.fetch_live_ipos()
        print(f"  -> Tracked {len(ipo_data)} active/upcoming IPOs.")

        # 10. Save Structured Scan Output
        scan_payload = {
            "timestamp": now_str,
            "indices": indices,
            "macro_snapshot": macro_snap,
            "market_regime": market_regime,
            "top_momentum_stocks": momentum_stocks[:15],
            "fifty_two_week_high_stocks": fifty_two_week_stocks,
            "top_bullish_stocks": bullish_picks,
            "monitored_radar": monitored_radar,
            "mutual_funds": mutual_funds,
            "total_screened": 35,
            "disclaimer": config.DISCLAIMER
        }

        with open(config.SCHEDULE_CONFIG["DAILY_SCAN_FILE"], "w", encoding="utf-8") as f:
            json.dump(scan_payload, f, indent=2)

        # 9. Generate Markdown Daily Briefing Report
        report_file = config.REPORTS_DIR / f"daily_briefing_{date_stamp}.md"
        self._generate_briefing_markdown(report_file, now_str, indices, macro_snap, momentum_stocks, bullish_picks, monitored_radar, mutual_funds, ipo_data)

        # 10. Generate Standalone Interactive HTML Dashboards
        html_destinations = [
            config.BASE_DIR / "dashboard.html",
            config.BASE_DIR / "index.html",
            config.DESKTOP_REPORT_PATH
        ]
        HTMLReportGenerator.generate(scan_payload, ipo_data, html_destinations)
        print(f"  -> Generated standalone HTML report at {html_destinations[0]} and Desktop.")

        # 11. Auto-push updated web application to GitHub Pages
        try:
            import subprocess
            subprocess.run(["git", "add", "index.html", "dashboard.html", "data/"], cwd=str(config.BASE_DIR), capture_output=True, timeout=15)
            subprocess.run(["git", "commit", "-m", f"chore(auto-update): market scan {now_str}"], cwd=str(config.BASE_DIR), capture_output=True, timeout=15)
            res = subprocess.run(["git", "push", "origin", "main"], cwd=str(config.BASE_DIR), capture_output=True, text=True, timeout=30)
            if res.returncode == 0:
                print("  -> Automatically published updated website to GitHub Pages!")
        except Exception as e:
            print(f"  -> GitHub Pages auto-publish notice: {e}")

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Daily AI Cycle Completed Successfully!")
        print(f"Report saved to: {report_file}\n")
        return scan_payload

    def _generate_briefing_markdown(self, filepath: Path, timestamp: str, indices: dict, macro_snap: dict, momentum_stocks: list, bullish_picks: list, monitored_radar: list, mutual_funds: list, ipos: list):
        """Generates executive markdown summary of the daily scan."""
        lines = [
            f"# Daily Indian Market AI Intelligence Briefing",
            f"**Generated:** {timestamp} | **Powered by Stock AI Agent (CIO Intelligence)**\n",
            "---",
            "## 1. Domestic & Global Market Overview",
            "### Domestic Indices",
            "| Index | Value | Change (%) |",
            "| :--- | :--- | :--- |"
        ]
        for idx_name, data in indices.items():
            lines.append(f"| **{idx_name}** | {data['value']} | {data['percent']:+.2f}% |")

        lines.append("\n### Global Macro & Commodities")
        lines.append("| Commodity / Index | Price | Change (%) |")
        lines.append("| :--- | :--- | :--- |")
        for m_name, m_data in macro_snap.get("macro", {}).items():
            lines.append(f"| **{m_name}** | {m_data['price']} | {m_data['change_pct']:+.2f}% |")

        lines.append("\n## 2. Multi-Timeframe Super-Trend & Momentum Leaders (3M / 1Y / 3Y)")
        lines.append("| Symbol | CMP (₹) | 3M Return | 6M Return | 1Y Return | 3Y Return | Trend Status |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for s in momentum_stocks[:10]:
            lines.append(f"| **{s['symbol']}** | ₹{s['cmp']} | +{s['ret_3m']}% | +{s['ret_6m']}% | +{s['ret_1y']}% | +{s['ret_3y']}% | {s['trend_status']} |")

        lines.append("\n## 3. Agentic AI Monitored Radar (Future Setups)")
        lines.append("| Symbol | Setup Type | Status | CMP (₹) | Target (3M) | Target (1Y) | Stop Loss |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for r in monitored_radar:
            lines.append(f"| **{r['symbol']}** | {r['setup_type']} | {r['monitoring_status']} | ₹{r.get('cmp', r['entry_trigger'])} | ₹{r['target_3m']} | ₹{r['target_1y']} | ₹{r['stop_loss']} |")

        lines.append("\n## 4. Top Bullish Stock Picks (360° Verified)")
        if not bullish_picks:
            lines.append("*No stocks met the strict 360-degree bullish confluence criteria today. Capital preservation active.*")
        else:
            lines.append("| Symbol | CMP (₹) | Conviction | RSI | Target 1 (₹) | Stop Loss (₹) | R:R |")
            lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
            for pick in bullish_picks[:8]:
                lines.append(f"| **{pick['symbol']}** | ₹{pick['cmp']} | {pick['conviction_score']}/10 | {pick['rsi']} | ₹{pick['target_1']} | ₹{pick['stop_loss']} | {pick['risk_reward']} |")

        lines.append("\n## 5. Curated Mutual Fund Recommendations & Rationale")
        lines.append("| Fund Name | Category | 1Y Return | 3Y CAGR | 5Y CAGR | Sharpe | Key Rationale |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
        for f in mutual_funds[:5]:
            lines.append(f"| **{f['name']}** | {f['category']} | +{f['return_1y']}% | +{f['return_3y_cagr']}% | +{f['return_5y_cagr']}% | {f['sharpe_ratio']} | {f['cio_rationale'][:90]}... |")

        lines.append("\n## 6. Indian IPO Updates & GMP")
        lines.append("| IPO Name | Status | Price Band | GMP (%) | Verdict |")
        lines.append("| :--- | :--- | :--- | :--- | :--- |")
        for ipo in ipos:
            lines.append(f"| **{ipo['name']}** | {ipo['status']} | {ipo['price_band']} | +{ipo.get('gmp_pct', 0)}% | {ipo['verdict']} |")

        lines.append(f"\n---\n*{config.DISCLAIMER}*")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

def main():
    parser = argparse.ArgumentParser(description="Stock AI Daily Automation Daemon")
    parser.add_argument("--run-now", action="store_true", help="Run the daily scan immediately and exit")
    parser.add_argument("--daemon", action="store_true", help="Run indefinitely and trigger at scheduled market times")
    args = parser.parse_args()

    automator = DailyAutomator()

    if args.run_now or not args.daemon:
        automator.run_daily_sync()

    if args.daemon:
        print(f"Stock AI Scheduler active. Running daily in morning at {config.SCHEDULE_CONFIG['MORNING_TIME']} and evening at {config.SCHEDULE_CONFIG['EVENING_TIME']} (6:00 PM)...")
        schedule.every().day.at(config.SCHEDULE_CONFIG["MORNING_TIME"]).do(automator.run_daily_sync)
        schedule.every().day.at(config.SCHEDULE_CONFIG["EVENING_TIME"]).do(automator.run_daily_sync)

        while True:
            schedule.run_pending()
            time.sleep(30)

if __name__ == "__main__":
    main()
