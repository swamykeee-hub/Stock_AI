import inspect
import json
import sys
import tempfile
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from bs4 import BeautifulSoup
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import config
from core.ai_performance_scorecard import AIPerformanceScorecard
from core.feed_health import collect_feed_health
from core.fund_manager_radar import FundManagerRadar
from core.hidden_gems_screener import HiddenGemsScreener
from core.html_generator import HTMLReportGenerator
from core.market_data import MarketDataManager
from core.mutual_fund_analyst import MutualFundAnalyst
from core.portfolio_health_auditor import PortfolioHealthAuditor
from core.sync_server import (
    _load_portfolio_file,
    _save_portfolio_file,
    push_to_github_pages,
    run_server,
)
from core.telegram_alert_bot import TelegramAlertBot


class TestMutualFundAnalyst(unittest.TestCase):
    def test_amfi_enrichment_cagr_and_sharpe(self):
        # Build synthetic 6-year descending NAV history (~18% CAGR)
        today = datetime(2026, 11, 23)
        rows = []
        for i in range(0, 365 * 6, 7):
            dt = today - timedelta(days=i)
            years_back = i / 365.0
            nav = 200.0 / ((1.18) ** years_back)
            rows.append({"date": dt.strftime("%d-%m-%Y"), "nav": f"{nav:.4f}"})

        mock_resp = MagicMock(status_code=200)
        mock_resp.json.return_value = {"data": rows}

        with tempfile.TemporaryDirectory() as tmp:
            mf = MutualFundAnalyst()
            mf.CACHE_FILE = Path(tmp) / "mf_cache.json"
            with patch("core.mutual_fund_analyst.requests.get", return_value=mock_resp):
                funds = mf.get_all_funds(force_refresh=True)

            self.assertEqual(len(funds), 8)
            first = funds[0]
            self.assertTrue(first["is_live_nav"])
            self.assertAlmostEqual(first["nav"], 200.0, places=1)
            self.assertGreater(first["return_3y_cagr"], 15.0)
            self.assertGreater(first["sharpe_ratio"], 0.5)

            # Cached read does not hit network
            with patch("core.mutual_fund_analyst.requests.get", side_effect=AssertionError("Should hit cache")):
                cached = mf.get_all_funds(force_refresh=False)
            self.assertEqual(len(cached), 8)


class TestFundManagerRadar(unittest.TestCase):
    def test_sync_preserves_core_and_promotes_top_inflections(self):
        with tempfile.TemporaryDirectory() as tmp:
            radar = FundManagerRadar()
            radar.RADAR_FILE = Path(tmp) / "monitored_stocks.json"
            # Force re-init with defaults + a stale promoted entry
            base = [dict(x) for x in radar.DEFAULT_MONITORED_STOCKS[:4]]
            base.append({
                "symbol": "STALE_PROMO",
                "name": "Stale Promoted Ltd",
                "sector": "Chemicals",
                "setup_type": "Old",
                "monitoring_status": "Watch",
                "entry_trigger": 100.0,
                "target_3m": 120.0,
                "target_1y": 140.0,
                "stop_loss": 90.0,
                "cio_conviction": 9.1,
                "auto_promoted": True,
                "institutional_thesis": "Old",
                "catalysts": [],
            })
            radar.RADAR_FILE.write_text(json.dumps(base), encoding="utf-8")

            picks = [
                {
                    "symbol": "TESTINFLECT",
                    "name": "Test Inflect Ltd",
                    "sector": "Pharma",
                    "archetype_short": "Laurus-Type Inflection",
                    "conviction_score": 9.6,
                    "inflection_score": 9.5,
                    "cmp": 500.0,
                    "target_1": 580.0,
                    "target_2": 690.0,
                    "stop_loss": 455.0,
                    "ret_1y": 82.0,
                    "roce_pct": 24.5,
                    "opm_expansion_bps": 240,
                    "qtr_pat_yoy_pct": 55.0,
                    "inst_4q_delta_pct": 3.2,
                    "fundamental_strengths": ["OPM surge"],
                },
                {
                    "symbol": "LOWPICK",
                    "name": "Low Pick",
                    "sector": "IT",
                    "conviction_score": 7.5,
                    "cmp": 200.0,
                },
            ]

            merged = radar.sync_with_scanner_results(picks, max_promote=2)
            syms = [m["symbol"] for m in merged]
            self.assertIn("TESTINFLECT", syms)
            self.assertNotIn("STALE_PROMO", syms)
            self.assertNotIn("LOWPICK", syms)
            for core_s in base[:4]:
                self.assertIn(core_s["symbol"], syms)


class TestAIPerformanceScorecard(unittest.TestCase):
    def test_record_refresh_resolve_and_honest_empty_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            hist_path = Path(tmp) / "history.json"
            hist_path.write_text("[]", encoding="utf-8")
            sc = AIPerformanceScorecard(history_file=hist_path)

            # Empty metrics must be 0.0 (no fake hardcoded defaults)
            empty_m = sc.get_performance_metrics()
            self.assertEqual(empty_m["win_rate_pct"], 0.0)
            self.assertEqual(empty_m["resolved_trades_count"], 0)

            picks = [
                {
                    "symbol": "WINCO",
                    "archetype_short": "Laurus-Type Inflection",
                    "conviction_score": 9.4,
                    "cmp": 100.0,
                    "target_1": 115.0,
                    "stop_loss": 92.0,
                    "sector": "Pharma",
                },
                {
                    "symbol": "LOSSCO",
                    "archetype_short": "Stage-2 Breakout",
                    "conviction_score": 8.9,
                    "cmp": 200.0,
                    "target_1": 230.0,
                    "stop_loss": 185.0,
                    "sector": "Auto",
                },
            ]
            added = sc.record_new_signals(picks, nifty_close=25000.0)
            self.assertEqual(added, 2)
            # Duplicate call same day should add 0
            self.assertEqual(sc.record_new_signals(picks, nifty_close=25000.0), 0)

            quotes = {
                "WINCO": {"currentPrice": 118.0, "dayHigh": 119.0, "dayLow": 112.0},
                "LOSSCO": {"currentPrice": 180.0, "dayHigh": 195.0, "dayLow": 179.0},
            }
            res = sc.refresh_outcomes(quotes_map=quotes, nifty_close=25500.0)
            self.assertEqual(res["resolved_trades_count"], 2)
            self.assertEqual(res["win_rate_pct"], 50.0)
            self.assertIn("avg_alpha_vs_nifty", res)
            self.assertNotEqual(res["avg_alpha_vs_nifty"], "Tracking Live")


class TestPortfolioHealthAuditor(unittest.TestCase):
    def test_tax_status_and_concentration_guardrails(self):
        near_ltcg_date = (datetime.now().date() - timedelta(days=350)).strftime("%Y-%m-%d")
        ltcg_date = (datetime.now().date() - timedelta(days=400)).strftime("%Y-%m-%d")
        self.assertIn("Near-LTCG", PortfolioHealthAuditor._evaluate_tax_status(near_ltcg_date)["tax_status"])
        self.assertIn("LTCG Eligible", PortfolioHealthAuditor._evaluate_tax_status(ltcg_date)["tax_status"])

        auditor = PortfolioHealthAuditor()
        # Synthetic bullish candles for 2 holdings (unequal weighting > 35% + > 25%)
        dates = pd.date_range(end=datetime.now(), periods=210, freq="D")
        candles = pd.DataFrame({
            "Date": dates,
            "Open": [100.0] * 210,
            "High": [105.0] * 210,
            "Low": [98.0] * 210,
            "Close": [100.0 + i * 0.2 for i in range(210)],
            "Volume": [100000] * 210,
        })
        auditor.market_data.get_historical_candles = MagicMock(return_value=candles)
        auditor.fund_analyst.analyze = MagicMock(return_value={"score": 7.5, "metrics": {"roce_pct": 20}, "inflection": {}})
        auditor.news_analyst.analyze = MagicMock(return_value={"has_critical_bearish_event": False, "critical_alerts": [], "top_bearish_catalysts": [], "score": 6.0})

        holdings = [
            {"symbol": "TCS", "qty": 100, "buyPrice": 120.0, "cached_cmp": 140.0, "buyDate": near_ltcg_date},
            {"symbol": "INFY", "qty": 100, "buyPrice": 120.0, "cached_cmp": 140.0, "buyDate": ltcg_date},
            {"symbol": "HDFCBANK", "qty": 10, "buyPrice": 120.0, "cached_cmp": 140.0, "buyDate": ltcg_date},
        ]
        res = auditor.audit_entire_portfolio(holdings, strategy_mode="long_term")
        self.assertEqual(res["total_holdings_count"], 3)
        self.assertTrue(len(res["sector_allocation"]) >= 2)
        self.assertTrue(any("Concentration" in msg or "Overweight" in msg for msg in res["concentration_alerts"]))
        self.assertIsNotNone(res["diversification_score"])


class TestFeedHealthSyncAndAlerts(unittest.TestCase):
    def test_localhost_default_cooldown_portfolio_io_and_telegram(self):
        sig = inspect.signature(run_server)
        self.assertEqual(sig.parameters["host"].default, "127.0.0.1")

        fh = collect_feed_health()
        self.assertIn("feeds", fh)
        self.assertEqual(fh["total_feeds"], 5)

        # Cooldown skips redundant push
        import core.sync_server as ss
        old_ts = ss._last_git_push_ts
        try:
            ss._last_git_push_ts = time.time()
            self.assertTrue(push_to_github_pages("test", force=False))
        finally:
            ss._last_git_push_ts = old_ts

        # Portfolio persistence helper test using temp path
        with tempfile.TemporaryDirectory() as tmp:
            orig_pf = ss.PORTFOLIO_FILE
            try:
                ss.PORTFOLIO_FILE = Path(tmp) / "port.json"
                saved = _save_portfolio_file([
                    {"symbol": "lauruslabs.ns", "qty": 10, "buyPrice": 500.5, "buyDate": "2026-01-10"},
                    {"symbol": "", "qty": 0, "buyPrice": 10},
                ])
                self.assertEqual(len(saved), 1)
                self.assertEqual(saved[0]["symbol"], "LAURUSLABS")
                loaded = _load_portfolio_file()
                self.assertEqual(loaded[0]["buyDate"], "2026-01-10")
            finally:
                ss.PORTFOLIO_FILE = orig_pf

        # Telegram catalyst alert digest builder
        bot = TelegramAlertBot()
        with patch.object(bot, "send_raw_message", return_value=True) as mock_send:
            sent = bot.send_portfolio_catalyst_alerts(
                portfolio_audit={"holdings": [{"symbol": "TCS"}], "urgent_alerts": [], "concentration_alerts": ["Overweight"]},
                corporate_actions={"dividends": [{"symbol": "TCS", "dividend_amount": "₹25", "ex_date": "01-Dec"}], "earnings": []},
                bullish_picks=[{"symbol": "ACUTAAS", "conviction_score": 9.6, "archetype_short": "Laurus-Type Inflection", "cmp": 1950}],
            )
            self.assertTrue(sent)
            msg = mock_send.call_args[0][0]
            self.assertIn("TCS", msg)
            self.assertIn("ACUTAAS", msg)


class TestHTMLReportGeneratorModular(unittest.TestCase):
    def test_external_vs_standalone_outputs_and_dom_invariants(self):
        scan_file = Path(config.SCHEDULE_CONFIG["DAILY_SCAN_FILE"])
        with open(scan_file, "r", encoding="utf-8") as f:
            scan_data = json.load(f)

        with tempfile.TemporaryDirectory() as tmp:
            ext_repo_test = config.BASE_DIR / "_test_ext_dashboard.html"
            standalone_test = Path(tmp) / "standalone_report.html"
            try:
                HTMLReportGenerator.generate(scan_data, [], [ext_repo_test, standalone_test])
                ext_html = ext_repo_test.read_text(encoding="utf-8")
                std_html = standalone_test.read_text(encoding="utf-8")

                # Repo HTML references external assets and is substantially smaller
                self.assertIn('href="web/styles.css"', ext_html)
                self.assertIn('src="web/stock_data.js"', ext_html)
                self.assertIn('src="web/dashboard.js"', ext_html)
                self.assertLess(len(ext_html), len(std_html) - 250000)

                # Standalone HTML embeds inline style & script
                self.assertIn("<style>", std_html)
                self.assertIn("const NSE_DATABASE =", std_html)

                # DOM & SVG invariants on generated HTML
                soup = BeautifulSoup(ext_html, "html.parser")
                self.assertGreaterEqual(len(soup.select(".index-card")), 19)
                self.assertIsNotNone(soup.select_one("#feedHealthRibbon"))
                self.assertIsNotNone(soup.select_one("#portBuyDateInput"))
                self.assertIsNotNone(soup.select_one("#portConcentrationBanner"))
                self.assertIn("iv-met-sheet", ext_html)
                self.assertIn("iv-met-rod", ext_html)
                self.assertIn("Swamy Chouhan - 9000632912", ext_html)
                self.assertIn("Alpha vs NIFTY 50", ext_html)
                self.assertIn("switchView('hidden_gems', this)", ext_html)
                self.assertIsNotNone(soup.select_one("#view-hidden_gems"))
                self.assertIsNotNone(soup.select_one("#hiddenGemsTable"))
                css_txt = (config.BASE_DIR / "web" / "styles.css").read_text(encoding="utf-8")
                self.assertIn("grid-auto-rows: 108px;", css_txt)
                self.assertIn("height: 108px;", css_txt)
            finally:
                if ext_repo_test.exists():
                    ext_repo_test.unlink()


class TestCandleRangeNormalization(unittest.TestCase):
    def test_period_aliases_map_to_yahoo_months(self):
        md = MarketDataManager()
        called_urls = []

        def _fake_get(url, headers=None, timeout=10):
            called_urls.append(url)
            resp = MagicMock(status_code=200)
            resp.json.return_value = {
                "chart": {
                    "result": [{
                        "timestamp": [1760000000, 1760086400],
                        "indicators": {"quote": [{"open": [100, 101], "high": [102, 103], "low": [99, 100], "close": [101, 102], "volume": [1000, 1200]}]},
                    }]
                }
            }
            return resp

        with patch("core.market_data.requests.get", side_effect=_fake_get):
            for p in ["1m", "3m", "6m", "1y"]:
                df = md.get_historical_candles("RUBICON", period=p, interval="1d")
                self.assertEqual(len(df), 2)

        self.assertIn("range=1mo&", called_urls[0])
        self.assertIn("range=3mo&", called_urls[1])
        self.assertIn("range=6mo&", called_urls[2])
        self.assertIn("range=1y&", called_urls[3])


class TestHiddenGemsScreener(unittest.TestCase):
    def test_gate_filtering_and_live_market_movement_updates(self):
        # Anti-bubble gate rejects extreme valuation & weak cash-conversion stocks (like 297x P/E)
        bubble_fund = {
            "score": 8.7,
            "metrics": {"market_cap_cr": "49342", "stock_pe": "291", "roce_pct": "33.9", "roe_pct": "27.6"},
            "inflection": {"qtr_pat_yoy_pct": 133.3, "qtr_sales_yoy_pct": 122.0},
            "balance_inst": {"debt_to_equity": 0.2, "cfo_to_pat_3y": 0.23, "promoter_pledge_pct": 0.0},
        }
        self.assertFalse(HiddenGemsScreener.passes_fundamental_gate(bubble_fund, is_seed=False))

        # Quality small-cap gate accepts high-ROCE, low-debt, cash-rich, reasonably valued stocks
        gem_fund = {
            "score": 9.6,
            "metrics": {"market_cap_cr": "5311", "stock_pe": "18.7", "peg_ratio": "0.60", "roce_pct": "29.3", "roe_pct": "22.6"},
            "inflection": {"qtr_pat_yoy_pct": 31.2, "qtr_sales_yoy_pct": 31.0},
            "balance_inst": {"debt_to_equity": 0.05, "cfo_to_pat_3y": 0.84, "promoter_pledge_pct": 0.0},
        }
        self.assertTrue(HiddenGemsScreener.passes_fundamental_gate(gem_fund, is_seed=True))
        self.assertEqual(HiddenGemsScreener.classify_cap_tier(5311), "Small Cap")
        self.assertEqual(HiddenGemsScreener.classify_cap_tier(18922), "Mid Cap")

        with tempfile.TemporaryDirectory() as tmp:
            scr = HiddenGemsScreener()
            scr.CACHE_FILE = Path(tmp) / "hidden_gems.json"

            sample_gems = [
                {
                    "symbol": "FIEMIND",
                    "name": "Fiem Industries Ltd.",
                    "sector": "Automobile and Auto Components",
                    "cap_tier": "Small Cap",
                    "mcap_cr": 5311.0,
                    "base_screener_cmp": 2000.0,
                    "base_mcap_cr": 5300.0,
                    "base_pe": 18.7,
                    "base_peg": 0.60,
                    "cmp": 2000.0,
                    "h52": 2200.0,
                    "l52": 1500.0,
                    "ema_20": 2010.0,
                    "ema_50": 1980.0,
                    "ema_200": 1950.0,
                    "atr": 45.0,
                    "rsi": 52.0,
                    "fund_score": 9.6,
                    "roce": 29.3,
                    "pe": 18.7,
                    "peg": 0.60,
                    "volume_ratio": 1.4,
                }
            ]
            # Simulate market rally moving CMP from 2000 -> 2150 (+7.5% toward 52W high)
            quotes_map = {
                "FIEMIND": {"currentPrice": 2150.0, "change": 150.0, "changePercent": 7.5, "fiftyTwoWeekHigh": 2200.0, "fiftyTwoWeekLow": 1500.0}
            }
            updated = scr.refresh_live_market_movements(sample_gems, quotes_map=quotes_map)
            self.assertEqual(len(updated), 1)
            g = updated[0]
            self.assertEqual(g["cmp"], 2150.0)
            self.assertEqual(g["day_change_pct"], 7.5)
            self.assertEqual(g["status_key"], "breakout")
            self.assertGreater(g["target_1"], 2150.0)
            self.assertLess(g["stop_loss"], 2150.0)
            self.assertTrue(scr.CACHE_FILE.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
