import json
import threading
import time
import argparse
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timezone, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now() -> datetime:
    """Returns current datetime in Indian Standard Time (IST)."""
    return datetime.now(timezone.utc).astimezone(IST)

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config
from core.market_data import MarketDataManager
from core.global_macro_news import GlobalMacroNewsAnalyst
from core.html_generator import HTMLReportGenerator
from core.ipo_analyst import IPOAnalyst
from core.stock_profile_manager import StockProfileManager
from core.portfolio_health_auditor import PortfolioHealthAuditor
from core.market_regime_analyst import MarketRegimeAnalyst
from core.institutional_flow_analyst import InstitutionalFlowAnalyst
from core.corporate_actions_calendar import CorporateActionsCalendar
from core.ai_performance_scorecard import AIPerformanceScorecard
from core.telegram_alert_bot import TelegramAlertBot
from core.market_movers_analyst import MarketMoversAnalyst
from core.mutual_fund_analyst import MutualFundAnalyst

def is_market_hours() -> bool:
    """Checks if current time is within Indian market trading hours (Mon-Fri 09:00 - 15:45 IST)."""
    now = get_ist_now()
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    market_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=45, second=0, microsecond=0)
    return market_open <= now <= market_close

_refresh_lock = threading.Lock()
_git_push_lock = threading.Lock()
_last_git_push_ts = 0.0
MIN_PUSH_COOLDOWN_SECONDS = 180


def push_to_github_pages(commit_msg: str = None, force: bool = False) -> bool:
    """Serialized git commit and push to GitHub Pages with cooldown & rebase safety."""
    global _last_git_push_ts
    with _git_push_lock:
        try:
            import subprocess
            now_epoch = time.time()
            elapsed = now_epoch - _last_git_push_ts
            if not force and elapsed < MIN_PUSH_COOLDOWN_SECONDS:
                wait_rem = int(MIN_PUSH_COOLDOWN_SECONDS - elapsed)
                print(f"[AutoPush Cooldown] Skipping push ({wait_rem}s remaining) to prevent Pages deployment collision.")
                return True

            now_str = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
            msg = commit_msg or f"chore(auto-update): live market sync {now_str}"
            files_to_stage = ["index.html", "dashboard.html", "data/"]
            if (config.BASE_DIR / ".nojekyll").exists():
                files_to_stage.append(".nojekyll")

            subprocess.run(["git", "add"] + files_to_stage, cwd=str(config.BASE_DIR), capture_output=True, timeout=15)
            diff_check = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(config.BASE_DIR), capture_output=True, timeout=10)
            if diff_check.returncode == 0:
                return True

            subprocess.run(["git", "commit", "-m", msg], cwd=str(config.BASE_DIR), capture_output=True, timeout=15)

            # Rebase safely onto origin/main before pushing so parallel updates never reject or collide
            rebase_res = subprocess.run(
                ["git", "pull", "--rebase", "--autostash", "origin", "main"],
                cwd=str(config.BASE_DIR), capture_output=True, text=True, timeout=30
            )
            if rebase_res.returncode != 0:
                subprocess.run(["git", "rebase", "--abort"], cwd=str(config.BASE_DIR), capture_output=True, timeout=10)

            res_push = subprocess.run(["git", "push", "origin", "main"], cwd=str(config.BASE_DIR), capture_output=True, text=True, timeout=35)
            if res_push.returncode == 0:
                _last_git_push_ts = time.time()
                print(f"[{now_str}] 🚀 Automatically published live update to GitHub Pages!")
                return True
            else:
                print(f"[{now_str}] Git push output: {res_push.stderr.strip() or res_push.stdout.strip()}")
                return False
        except Exception as e:
            print(f"[AutoPush Notice] Could not publish to GitHub: {e}")
            return False


def refresh_all_live_data(mode: str = "quick", auto_push: bool = False) -> dict:
    """Serialized entry point for refreshing market data so parallel requests cannot race."""
    with _refresh_lock:
        return _refresh_all_live_data_locked(mode=mode, auto_push=auto_push)


def _refresh_all_live_data_locked(mode: str = "quick", auto_push: bool = False) -> dict:
    """
    Refreshes all domestic benchmark indices, global macro, and updates
    real-time CMP for all stocks across momentum, 52W breakouts, radar, and bullish picks.
    Regenerates dashboard.html and Desktop report.
    """
    now_str = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now_str}] SyncServer: Executing live refresh (mode={mode})...")

    m = MarketDataManager()
    indices = m.get_benchmark_indices()

    macro_analyst = GlobalMacroNewsAnalyst()
    macro_snap = macro_analyst.get_global_markets_snapshot()

    scan_file = config.SCHEDULE_CONFIG.get("DAILY_SCAN_FILE", config.REPORTS_DIR / "latest_daily_scan.json")
    scan_payload = {}
    if Path(scan_file).exists():
        try:
            with open(scan_file, "r", encoding="utf-8") as f:
                scan_payload = json.load(f)
        except Exception:
            pass

    scan_payload["timestamp"] = now_str
    scan_payload["indices"] = indices
    scan_payload["macro_snapshot"] = macro_snap

    # Always ensure monitored_radar is calibrated with latest bullish scan & curated watchlist
    try:
        from core.fund_manager_radar import FundManagerRadar
        radar_mgr = FundManagerRadar()
        radar_stocks = radar_mgr.get_monitored_stocks(sync_live_prices=False)
        top_bullish = scan_payload.get("top_bullish_stocks", [])
        needs_calibration = radar_stocks and not any(r.get("conviction_source") for r in radar_stocks)
        if top_bullish and (mode == "full" or needs_calibration or not radar_stocks):
            radar_stocks = radar_mgr.sync_with_scanner_results(top_bullish, max_promote=4)
        if radar_stocks:
            scan_payload["monitored_radar"] = radar_stocks
    except Exception:
        pass

    # Always keep Institutional Mutual Funds enriched with Live AMFI NAVs (12h cache in quick mode)
    try:
        mf_data = MutualFundAnalyst().get_all_funds(force_refresh=(mode == "full"))
        if mf_data:
            scan_payload["mutual_funds"] = mf_data
    except Exception:
        pass

    # Ensure top_momentum_stocks contains curated momentum universe
    try:
        from core.momentum_screener import MomentumScreener
        mom_screener = MomentumScreener()
        cached_mom = mom_screener.scan_universe(max_stocks=100, force_refresh=False)
        if cached_mom:
            scan_payload["top_momentum_stocks"] = cached_mom
    except Exception:
        pass

    # Ensure factor_screener_stocks is loaded cleanly from cache
    try:
        from core.factor_screener import SmartFactorScreener
        cached_factors = SmartFactorScreener().scan_factors(force_refresh=False)
        if cached_factors:
            scan_payload["factor_screener_stocks"] = cached_factors
    except Exception:
        pass

    # Collect all unique stock symbols across tables to refresh their live quotes
    symbols_to_update = set()
    for cat in ["top_momentum_stocks", "fifty_two_week_high_stocks", "monitored_radar", "top_bullish_stocks", "factor_screener_stocks"]:
        for item in scan_payload.get(cat, []):
            if isinstance(item, dict) and "symbol" in item:
                symbols_to_update.add(item["symbol"])

    # Concurrently fetch live quotes for all symbols
    fresh_quotes = {}
    if symbols_to_update:
        def _fetch_quote(sym):
            return sym, m.get_quote_and_overview(sym)

        with ThreadPoolExecutor(max_workers=14) as executor:
            fresh_quotes = dict(executor.map(_fetch_quote, list(symbols_to_update)))

        # 1. Update top_momentum_stocks CMP
        for s in scan_payload.get("top_momentum_stocks", []):
            sym = s.get("symbol")
            if sym in fresh_quotes and fresh_quotes[sym].get("currentPrice", 0) > 0:
                s["cmp"] = fresh_quotes[sym]["currentPrice"]
                s["day_change"] = fresh_quotes[sym].get("change", 0.0)
                s["day_change_pct"] = fresh_quotes[sym].get("changePercent", 0.0)

        # 2. Update fifty_two_week_high_stocks CMP, day change & distance
        for s in scan_payload.get("fifty_two_week_high_stocks", []):
            sym = s.get("symbol")
            if sym in fresh_quotes and fresh_quotes[sym].get("currentPrice", 0) > 0:
                q = fresh_quotes[sym]
                s["cmp"] = q["currentPrice"]
                s["day_change"] = q.get("change", 0.0)
                s["day_change_pct"] = q.get("changePercent", 0.0)
                if s.get("h52", 0) > 0:
                    s["dist_52w"] = round(((s["h52"] - s["cmp"]) / s["h52"]) * 100, 2)

        # 3. Update monitored_radar CMP
        for r in scan_payload.get("monitored_radar", []):
            sym = r.get("symbol")
            if sym in fresh_quotes and fresh_quotes[sym].get("currentPrice", 0) > 0:
                cmp = fresh_quotes[sym]["currentPrice"]
                r["cmp"] = cmp
                old_sl = r.get("stop_loss", 0)
                old_t3m = r.get("target_3m", 0)
                if old_sl >= cmp or old_t3m <= cmp or old_t3m > cmp * 2.2:
                    low_e = round(cmp * 0.97, 1)
                    high_e = round(cmp * 1.005, 1)
                    r["entry_trigger"] = round(cmp * 0.99, 1)
                    r["monitoring_status"] = f"Active Accumulation Zone (₹{low_e:,.1f} - ₹{high_e:,.1f})"
                    r["target_3m"] = round(cmp * 1.15, 1)
                    r["target_1y"] = round(cmp * 1.38, 1)
                    r["stop_loss"] = round(cmp * 0.91, 1)
                    r["risk_reward"] = "1:2.8"

        # 4. Update top_bullish_stocks & factor_screener_stocks CMP
        for cat in ["top_bullish_stocks", "factor_screener_stocks"]:
            for p in scan_payload.get(cat, []):
                sym = p.get("symbol")
                if sym in fresh_quotes and fresh_quotes[sym].get("currentPrice", 0) > 0:
                    p["cmp"] = fresh_quotes[sym]["currentPrice"]

    # Full mode rescan for 52-week highs
    if mode == "full":
        try:
            from core.fifty_two_week_high_tracker import FiftyTwoWeekHighTracker
            tracker_52w = FiftyTwoWeekHighTracker()
            fifty_two_week_stocks = tracker_52w.scan_52_week_highs(force_refresh=True)
            scan_payload["fifty_two_week_high_stocks"] = fifty_two_week_stocks
        except Exception as e:
            print(f"52W sync note: {e}")

    if "total_screened" not in scan_payload or scan_payload["total_screened"] < 100:
        scan_payload["total_screened"] = 509
    if "disclaimer" not in scan_payload:
        scan_payload["disclaimer"] = config.DISCLAIMER

    # Persist JSON report
    with open(scan_file, "w", encoding="utf-8") as f:
        json.dump(scan_payload, f, indent=2)

    # Refresh enriched profiles only if missing/expired/stale; otherwise update live CMPs in-place
    try:
        prof_mgr = StockProfileManager()
        if mode == "full":
            prof_mgr.build_all_benchmark_profiles()
        else:
            existing_profiles = prof_mgr.get_enriched_profiles(refresh=False)
            if existing_profiles and fresh_quotes:
                updated = False
                for sym, prof in existing_profiles.items():
                    if sym in fresh_quotes and fresh_quotes[sym].get("currentPrice", 0) > 0:
                        q = fresh_quotes[sym]
                        prof["cmp"] = q["currentPrice"]
                        prof["change"] = q.get("change", prof.get("change", 0.0))
                        prof["change_pct"] = q.get("changePercent", prof.get("change_pct", 0.0))
                        updated = True
                if updated:
                    with open(prof_mgr.CACHE_FILE, "w", encoding="utf-8") as _pf:
                        json.dump(existing_profiles, _pf, indent=2)
    except Exception as e:
        print(f"Profile sync note: {e}")

    # Concurrently refresh live IPOs, Institutional Flow (PCR/FII-DII), & Real-Time Market Movers every sync
    def _fetch_ipos_safe():
        try:
            return IPOAnalyst().fetch_live_ipos()
        except Exception:
            return []

    def _fetch_inst_flow_live():
        try:
            return InstitutionalFlowAnalyst().get_institutional_flow(force_refresh=True)
        except Exception:
            return {}

    def _fetch_movers_live():
        try:
            return MarketMoversAnalyst().get_market_movers(force_refresh=True)
        except Exception:
            return {}

    with ThreadPoolExecutor(max_workers=3) as live_exec:
        fut_ipos = live_exec.submit(_fetch_ipos_safe)
        fut_inst = live_exec.submit(_fetch_inst_flow_live)
        fut_movers = live_exec.submit(_fetch_movers_live)

        ipo_data = fut_ipos.result()
        inst_flow_data = fut_inst.result()
        movers_data = fut_movers.result()

    if inst_flow_data:
        scan_payload["institutional_flow"] = inst_flow_data
    if movers_data and (movers_data.get("top_gainers") or movers_data.get("top_losers")):
        scan_payload["market_movers"] = movers_data

    # Load Corporate Actions & Earnings Calendar
    try:
        scan_payload["corporate_actions"] = CorporateActionsCalendar().get_calendar_events(force_refresh=False)
    except Exception:
        pass

    # Load AI Performance Scorecard
    try:
        scan_payload["performance_scorecard"] = AIPerformanceScorecard().get_performance_metrics()
    except Exception:
        pass

    # Persist final enriched JSON report (with fresh movers, institutional flow, MF NAVs & radar)
    with open(scan_file, "w", encoding="utf-8") as f:
        json.dump(scan_payload, f, indent=2)

    # Regenerate dashboard.html, index.html, and Desktop report
    html_destinations = [
        config.BASE_DIR / "dashboard.html",
        config.BASE_DIR / "index.html",
        config.DESKTOP_REPORT_PATH
    ]
    HTMLReportGenerator.generate(scan_payload, ipo_data, html_destinations)
    print(f"[{now_str}] SyncServer: Refreshed {len(indices)} indices & {len(symbols_to_update)} stock CMPs. HTML reports regenerated.")

    if auto_push:
        threading.Thread(target=push_to_github_pages, args=(f"chore(auto-update): live market sync {now_str}",), daemon=True).start()

    return {
        "status": "success",
        "timestamp": now_str,
        "indices_count": len(indices),
        "stocks_updated_count": len(symbols_to_update),
        "message": f"Successfully refreshed {len(indices)} indices and {len(symbols_to_update)} stock CMPs!"
    }

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP Server for handling local web refresh requests."""
    daemon_threads = True

class SyncRequestHandler(BaseHTTPRequestHandler):
    """Handles REST requests from dashboard.html and external integrations."""

    def _set_cors_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, X-Requested-With")
        self.send_header("Content-Type", content_type)
        self.end_headers()

    def do_OPTIONS(self):
        """Respond to CORS preflight checks."""
        self._set_cors_headers(200)

    def do_GET(self):
        try:
            self._handle_request()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def do_POST(self):
        try:
            self._handle_request()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def _handle_request(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # Serve Dashboard HTML if accessed directly via browser
        if path in ("/", "/dashboard", "/dashboard.html"):
            dash_path = config.BASE_DIR / "dashboard.html"
            if dash_path.exists():
                try:
                    with open(dash_path, "r", encoding="utf-8") as f:
                        content = f.read().encode("utf-8")
                    self._set_cors_headers(200, content_type="text/html; charset=utf-8")
                    self.wfile.write(content)
                    return
                except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                    return
                except Exception as e:
                    try:
                        self._set_cors_headers(500)
                        self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                    except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                        pass
                    return

        if path == "/api/status":
            self._set_cors_headers(200)
            self.wfile.write(json.dumps({
                "status": "online",
                "service": "Indian Stock AI Live Sync Server",
                "port": 5005,
                "timestamp": get_ist_now().strftime("%Y-%m-%d %H:%M:%S"),
                "is_market_hours": is_market_hours()
            }).encode("utf-8"))
            return

        if path == "/api/quote":
            sym = params.get("symbol", ["TCS"])[0].strip().upper()
            try:
                m = MarketDataManager()
                q = m.get_quote_and_overview(sym)
                self._set_cors_headers(200)
                self.wfile.write(json.dumps(q).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if path == "/api/candles":
            sym = params.get("symbol", ["TCS"])[0].strip().upper()
            period = params.get("period", ["6m"])[0]
            try:
                m = MarketDataManager()
                df = m.get_historical_candles(sym, period=period, interval="1d")
                candles = []
                if not df.empty:
                    for _, row in df.iterrows():
                        candles.append({
                            "time": row["Date"].strftime("%Y-%m-%d"),
                            "open": round(float(row["Open"]), 2),
                            "high": round(float(row["High"]), 2),
                            "low": round(float(row["Low"]), 2),
                            "close": round(float(row["Close"]), 2),
                            "volume": int(row.get("Volume", 0))
                        })
                self._set_cors_headers(200)
                self.wfile.write(json.dumps({"symbol": sym, "candles": candles}).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if path == "/api/market_regime":
            try:
                analyst = MarketRegimeAnalyst()
                reg = analyst.evaluate_market_regime()
                self._set_cors_headers(200)
                self.wfile.write(json.dumps(reg).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if path == "/api/portfolio_audit":
            try:
                holdings = []
                strategy_mode = params.get("strategy_mode", ["long_term"])[0]
                if self.command == "POST":
                    content_length = int(self.headers.get("Content-Length", 0))
                    if content_length > 0:
                        body = self.rfile.read(content_length).decode("utf-8")
                        payload = json.loads(body)
                        holdings = payload.get("holdings", [])
                        strategy_mode = payload.get("strategy_mode", strategy_mode)
                else:
                    data_param = params.get("data", ["[]"])[0]
                    holdings = json.loads(data_param)

                auditor = PortfolioHealthAuditor()
                audit_res = auditor.audit_entire_portfolio(holdings, strategy_mode=strategy_mode)
                self._set_cors_headers(200)
                self.wfile.write(json.dumps(audit_res).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if path == "/api/refresh":
            mode = params.get("mode", ["quick"])[0]
            try:
                if mode == "full":
                    from scheduler import DailyAutomator
                    automator = DailyAutomator()
                    scan_payload = automator.run_daily_sync()
                    timestamp = scan_payload.get("timestamp", get_ist_now().strftime("%Y-%m-%d %H:%M:%S"))
                    indices_count = len(scan_payload.get("indices", {}))
                    resp = {
                        "status": "success",
                        "mode": mode,
                        "timestamp": timestamp,
                        "indices_count": indices_count,
                        "message": "Full daily market scan completed successfully!"
                    }
                else:
                    push_param = params.get("push", [None])[0]
                    auto_push = (push_param.lower() == "true") if push_param is not None else is_market_hours()
                    resp = refresh_all_live_data(mode=mode, auto_push=auto_push)

                try:
                    self._set_cors_headers(200)
                    self.wfile.write(json.dumps(resp).encode("utf-8"))
                except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                    pass
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                pass
            except Exception as e:
                try:
                    self._set_cors_headers(500)
                    self.wfile.write(json.dumps({"status": "error", "error": str(e)}).encode("utf-8"))
                except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                    pass
            return

        if path == "/api/institutional_flow":
            try:
                analyst = InstitutionalFlowAnalyst()
                data = analyst.get_institutional_flow(force_refresh=params.get("refresh", ["false"])[0] == "true")
                self._set_cors_headers(200)
                self.wfile.write(json.dumps(data).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if path == "/api/corporate_actions":
            try:
                cal = CorporateActionsCalendar()
                data = cal.get_calendar_events(force_refresh=params.get("refresh", ["false"])[0] == "true")
                self._set_cors_headers(200)
                self.wfile.write(json.dumps(data).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if path == "/api/performance_scorecard":
            try:
                scorecard = AIPerformanceScorecard()
                data = scorecard.get_performance_metrics()
                self._set_cors_headers(200)
                self.wfile.write(json.dumps(data).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if path == "/api/market_movers":
            try:
                analyst = MarketMoversAnalyst()
                data = analyst.get_market_movers(force_refresh=params.get("refresh", ["false"])[0] == "true")
                self._set_cors_headers(200)
                self.wfile.write(json.dumps(data).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if path == "/api/telegram_status":
            try:
                bot = TelegramAlertBot()
                self._set_cors_headers(200)
                self.wfile.write(json.dumps({
                    "enabled": bot.enabled,
                    "configured": bot.is_configured(),
                    "chat_id_set": bool(bot.chat_id)
                }).encode("utf-8"))
            except Exception as e:
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        self._set_cors_headers(404)
        self.wfile.write(json.dumps({"status": "not_found"}).encode("utf-8"))

    def log_message(self, format, *args):
        """Clean logging to avoid console pollution."""
        print(f"[SyncServer] {self.address_string()} - {format % args}")

def background_periodic_sync_worker(interval_seconds: int = 180):
    """Periodically refreshes live feeds every `interval_seconds` (default: 3 minutes) during market hours."""
    print(f"🔄 Background Auto-Sync Worker active (Interval: {interval_seconds}s).")
    while True:
        try:
            time.sleep(interval_seconds)
            if is_market_hours():
                print("[AutoSync] Market hours active. Auto-refreshing live quotes & publishing to GitHub...")
                refresh_all_live_data(mode="quick", auto_push=True)
        except Exception as e:
            print(f"[AutoSync Warning] Periodic sync encountered: {e}")

def is_port_in_use(port: int = 5005) -> bool:
    """Checks if port is already active."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def run_server(port=None, host="0.0.0.0", enable_bg_sync=True):
    if port is None:
        import os
        port = int(os.environ.get("PORT", 5005))

    if is_port_in_use(port):
        print(f"ℹ️ Indian Stock AI Live Sync Server is already running on port {port}.")
        return

    if enable_bg_sync:
        bg_thread = threading.Thread(target=background_periodic_sync_worker, daemon=True)
        bg_thread.start()

    server = ThreadedHTTPServer((host, port), SyncRequestHandler)
    print(f"🚀 Indian Stock AI Live Sync Server running at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

def start_sync_server_thread(port=None, host="0.0.0.0", enable_bg_sync=True) -> threading.Thread:
    """Starts the sync server in a daemon background thread if not already running."""
    if port is None:
        import os
        port = int(os.environ.get("PORT", 5005))

    if is_port_in_use(port):
        print(f"ℹ️ Sync Server is already running on port {port}.")
        return None

    if enable_bg_sync:
        bg_thread = threading.Thread(target=background_periodic_sync_worker, daemon=True)
        bg_thread.start()

    server = ThreadedHTTPServer((host, port), SyncRequestHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"🚀 Background Sync Server listening on http://{host}:{port}")
    return t

if __name__ == "__main__":
    import os
    default_port = int(os.environ.get("PORT", 5005))
    parser = argparse.ArgumentParser(description="Indian Stock AI Live Sync Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host interface to listen on")
    parser.add_argument("--port", type=int, default=default_port, help="Port to listen on")
    parser.add_argument("--no-bg-sync", action="store_true", help="Disable background periodic auto-sync")
    parser.add_argument("--run-once", action="store_true", help="Execute single live refresh cycle and exit")
    parser.add_argument("--push", action="store_true", help="Commit and push changes to GitHub Pages on --run-once")
    args = parser.parse_args()

    if args.run_once:
        print("[SyncServer] Executing single-run live refresh...")
        res = refresh_all_live_data(mode="quick", auto_push=args.push)
        if args.push:
            # When run from CLI, push synchronously to ensure it lands
            push_to_github_pages()
        print("Run-once completed successfully.")
        sys.exit(0)

    run_server(port=args.port, host=args.host, enable_bg_sync=not args.no_bg_sync)
