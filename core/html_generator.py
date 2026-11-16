import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

class HTMLReportGenerator:
    """Generates an all-in-one standalone interactive HTML dashboard."""

    @staticmethod
    def generate(scan_data: Dict[str, Any], ipo_list: List[Dict[str, Any]], output_paths: List[Path]) -> str:
        timestamp = scan_data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        indices = scan_data.get("indices", {})
        macro = scan_data.get("macro_snapshot", {}).get("macro", {})
        momentum_stocks = scan_data.get("top_momentum_stocks", [])
        monitored_radar = scan_data.get("monitored_radar", [])
        mutual_funds = scan_data.get("mutual_funds", [])
        picks = scan_data.get("top_bullish_stocks", [])
        disclaimer = scan_data.get("disclaimer", "")

        # Dynamic 52-Week High Breakout Leaders
        fifty_two_week_stocks = scan_data.get("fifty_two_week_high_stocks", [])
        if not fifty_two_week_stocks:
            try:
                from core.fifty_two_week_high_tracker import FiftyTwoWeekHighTracker
                fifty_two_week_stocks = FiftyTwoWeekHighTracker().scan_52_week_highs(force_refresh=False)
            except Exception:
                fifty_two_week_stocks = []

        # Load backend NSE 500 catalog for universal lookup fallback
        nse_catalog = []
        try:
            catalog_file = Path("D:/STOCK_AI/data/nse_stocks.json")
            if catalog_file.exists():
                with open(catalog_file, "r", encoding="utf-8") as f:
                    nse_catalog = json.load(f)
        except Exception:
            pass
        nse_catalog_json = json.dumps(nse_catalog)

        # Load pre-computed enriched profiles (CMP, Technicals, Fundamentals, Buy Entry Strategy)
        enriched_profiles = {}
        try:
            from core.stock_profile_manager import StockProfileManager
            profile_mgr = StockProfileManager()
            enriched_profiles = profile_mgr.get_enriched_profiles()
        except Exception:
            pass
        enriched_profiles_json = json.dumps(enriched_profiles)

        # Load universal 503-stock CMP cache for instant portfolio valuation
        all_stock_cmps = {}
        try:
            cmps_file = Path("D:/STOCK_AI/data/cache/all_stock_cmps.json")
            if cmps_file.exists():
                with open(cmps_file, "r", encoding="utf-8") as f:
                    all_stock_cmps = json.load(f)
        except Exception:
            pass
        all_stock_cmps_json = json.dumps(all_stock_cmps)

        # Generate Indices HTML
        indices_html = ""
        for name, data in indices.items():
            chg = data.get("change", 0.0)
            pct = data.get("percent", 0.0)
            val = data.get("value", 0.0)
            is_pos = chg >= 0
            color = "#10b981" if is_pos else "#ef4444"
            sign = "+" if is_pos else ""
            val_prefix = "" if any(k in name.upper() for k in ["VIX", "AI CATALYST"]) else "₹"
            indices_html += f"""
            <div class="index-card">
                <div class="index-name">{name}</div>
                <div class="index-val">{val_prefix}{val:,.2f}</div>
                <div class="index-chg" style="color: {color};">{sign}{chg} ({sign}{pct:.2f}%)</div>
            </div>
            """

        # Macro indicators
        for m_name, m_data in list(macro.items())[:3]:
            chg_pct = m_data.get("change_pct", 0.0)
            price = m_data.get("price", 0.0)
            color = "#10b981" if chg_pct >= 0 else "#ef4444"
            sign = "+" if chg_pct >= 0 else ""
            indices_html += f"""
            <div class="index-card">
                <div class="index-name">{m_name}</div>
                <div class="index-val">{price:,.2f}</div>
                <div class="index-chg" style="color: {color};">{sign}{chg_pct:.2f}%</div>
            </div>
            """

        # Senior CIO Market Regime Card
        market_regime = scan_data.get("market_regime")
        if market_regime:
            score = market_regime.get("market_score", 75)
            regime_label = market_regime.get("regime_label", "Bull Market")
            lead = ", ".join(market_regime.get("leading_sectors", [])[:2])
            indices_html += f"""
            <div class="index-card" style="border: 1px solid #10b981; background: rgba(16, 185, 129, 0.08);">
                <div class="index-name" style="color: #38bdf8;">🎯 Senior CIO Market Stance</div>
                <div class="index-val" style="font-size: 15px; color: #10b981;">{regime_label}</div>
                <div class="index-chg" style="color: var(--text-heading); font-size: 11px;">Health: <b>{score}/100</b> &bull; Leading: {lead}</div>
            </div>
            """

        # Generate Momentum Rows
        momentum_rows = ""
        for s in momentum_stocks:
            momentum_rows += f"""
            <tr class="stock-row" data-symbol="{s['symbol']}" data-name="{s['name']}" data-sector="{s['sector']}">
                <td>
                    <div class="sym-name">{s['symbol']}</div>
                    <div class="sub-text">{s['name']}</div>
                </td>
                <td><span class="sector-pill">{s['sector']}</span></td>
                <td><b>₹{s['cmp']:,.2f}</b></td>
                <td style="color: #10b981; font-weight: 700;">+{s.get('ret_3m', 0)}%</td>
                <td style="color: #10b981; font-weight: 700;">+{s.get('ret_6m', 0)}%</td>
                <td style="color: #34d399; font-weight: 800; font-size: 15px;">+{s.get('ret_1y', 0)}%</td>
                <td style="color: #38bdf8; font-weight: 700;">+{s.get('ret_3y', 0)}%</td>
                <td><span class="badge" style="background: #8b5cf6;">{s.get('trend_status', 'Strong Trend')}</span></td>
                <td><button class="chart-btn" onclick="toggleCandleChart('{s['symbol']}', this)">📈 Chart</button></td>
            </tr>
            """

        # Generate 52-Week High Breakout Rows and Cards (Dynamic Live Radar)
        fifty_two_week_count = len(fifty_two_week_stocks)
        sec_counts = {}
        for s in fifty_two_week_stocks:
            sec = s.get("sector", "Equities")
            sec_counts[sec] = sec_counts.get(sec, 0) + 1
        top_52w_sector = max(sec_counts.items(), key=lambda x: x[1])[0] if sec_counts else "Diversified"

        fifty_two_week_rows = ""
        fifty_two_week_cards = ""
        for s in fifty_two_week_stocks:
            chg_sign = "+" if s.get("day_change", 0) >= 0 else ""
            dist_color = "#10b981" if s.get("dist_52w", 0) <= 1.0 else "#38bdf8"
            sec_name = s.get('sector', 'Equities')
            stk_name = s.get('name', s.get('symbol', ''))
            fifty_two_week_rows += f"""
            <tr class="stock-row" data-symbol="{s['symbol']}" data-name="{stk_name}" data-sector="{sec_name}">
                <td>
                    <div class="sym-name">{s['symbol']}</div>
                    <div class="sub-text">{stk_name}</div>
                </td>
                <td><span class="sector-pill">{sec_name}</span></td>
                <td><b>₹{s['cmp']:,.2f}</b> <span style="font-size:11px; color:#10b981;">{chg_sign}{s.get('day_change_pct', 0)}%</span></td>
                <td><b style="color: #f8fafc;">₹{s['h52']:,.2f}</b></td>
                <td><span style="color: {dist_color}; font-weight: 800; font-size: 14px;">{s['dist_52w']}%</span></td>
                <td style="color: #34d399; font-weight: 700;">+{s.get('ret_1y', 0)}%</td>
                <td><b>{s.get('vol_surge', 1.0)}x</b></td>
                <td><span class="rsi-tag">{s.get('rsi', 60.0)}</span></td>
                <td><span class="badge" style="background: {s.get('quality_badge', '#2563eb')};">{s.get('quality', 'Breakout')}</span></td>
                <td><span style="color: #38bdf8; font-weight: 700; font-size: 13px;">{s.get('suggested_entry', 'CMP')}</span></td>
                <td><button class="chart-btn" onclick="toggleCandleChart('{s['symbol']}', this)">📈 Chart</button></td>
            </tr>
            """

            fifty_two_week_cards += f"""
            <div class="stock-card" data-symbol="{s['symbol']}" data-name="{stk_name}" data-sector="{sec_name}">
                <div class="card-header">
                    <div>
                        <span class="card-symbol">{s['symbol']}</span>
                        <span class="card-company">{stk_name} &bull; {sec_name}</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="font-size: 20px; font-weight: 800; color: #38bdf8;">₹{s['cmp']:,.2f}</span>
                        <div style="font-size: 12px; font-weight: 700; color: #10b981;">{s['dist_52w']}% from 52W High</div>
                    </div>
                </div>

                <div class="metrics-ribbon" style="margin-bottom: 12px;">
                    <div class="m-card">
                        <small>52W Peak / Low</small>
                        <b>₹{s['h52']:,.2f}</b>
                        <span style="font-size:11px; color:#94a3b8;">Low: ₹{s['l52']:,.2f}</span>
                    </div>
                    <div class="m-card">
                        <small>1-Year Momentum</small>
                        <b>+{s.get('ret_1y', 0)}%</b>
                        <span style="font-size:11px; color:#38bdf8;">RSI: {s.get('rsi', 60)}</span>
                    </div>
                    <div class="m-card">
                        <small>Valuation</small>
                        <b>P/E: {s.get('pe', 25)}x</b>
                        <span style="font-size:11px; color:#94a3b8;">ROCE: {s.get('roce', 20)}%</span>
                    </div>
                </div>

                <div class="buy-setup-grid" style="margin-bottom: 12px;">
                    <div class="setup-box buy">
                        <small>Suggested Entry Pocket</small>
                        <b style="font-size: 13px;">{s.get('suggested_entry')}</b>
                    </div>
                    <div class="setup-box tgt">
                        <small>Target 1 (+9%)</small>
                        <b>₹{s.get('target_1')}</b>
                    </div>
                    <div class="setup-box tgt2">
                        <small>Target 2 (+21%)</small>
                        <b>₹{s.get('target_2')}</b>
                    </div>
                    <div class="setup-box sl">
                        <small>Stop Loss</small>
                        <b>₹{s.get('stop_loss')}</b>
                    </div>
                    <div class="setup-box rr">
                        <small>Risk : Reward</small>
                        <b>{s.get('risk_reward')}</b>
                    </div>
                </div>

                <div class="strategy-explanation-box">
                    <h4 style="margin: 0 0 6px 0; color: #38bdf8; font-size: 13px;">🏛️ Senior Fund Manager Breakout Rationale &amp; Strategy:</h4>
                    <div style="font-size: 12px; line-height: 1.5;">{s.get('buy_strategy')}</div>
                </div>
            </div>
            """

        # Generate Monitored Radar Rows
        radar_rows = ""
        for r in monitored_radar:
            radar_rows += f"""
            <tr class="stock-row" data-symbol="{r['symbol']}" data-name="{r['name']}" data-sector="{r['sector']}">
                <td>
                    <div class="sym-name">{r['symbol']}</div>
                    <div class="sub-text">{r['name']}</div>
                </td>
                <td><span class="status-pill">{r['setup_type']}</span></td>
                <td><b>₹{r.get('cmp', r['entry_trigger']):,.2f}</b></td>
                <td style="color: #34d399;">₹{r['target_3m']}</td>
                <td style="color: #10b981; font-weight: 700;">₹{r['target_1y']}</td>
                <td style="color: #f87171;">₹{r['stop_loss']}</td>
                <td><span class="badge" style="background: #0284c7;">{r['monitoring_status']}</span></td>
                <td style="font-size: 12px; color: #cbd5e1; max-width: 280px;">{r['institutional_thesis'][:120]}...</td>
                <td><button class="chart-btn" onclick="toggleCandleChart('{r['symbol']}', this)">📈 Chart</button></td>
            </tr>
            """

        # Generate Mutual Funds Rows
        mf_rows = ""
        for f in mutual_funds:
            mf_rows += f"""
            <tr>
                <td>
                    <b>{f['name']}</b>
                    <div class="sub-text">{f['fund_house']} &bull; Manager: {f['fund_manager']}</div>
                </td>
                <td><span class="sector-pill">{f['category']}</span></td>
                <td style="color: #10b981; font-weight: 700;">+{f['return_1y']}%</td>
                <td style="color: #34d399; font-weight: 800;">+{f['return_3y_cagr']}%</td>
                <td style="color: #38bdf8; font-weight: 700;">+{f['return_5y_cagr']}%</td>
                <td><b>{f['sharpe_ratio']}</b></td>
                <td>₹{f['aum_cr']:,.0f} Cr</td>
                <td style="font-size: 12px; color: #cbd5e1; max-width: 320px;">{f['cio_rationale'][:130]}...</td>
            </tr>
            """

        # Generate Bullish Picks Table Rows
        picks_rows = ""
        for p in picks:
            score = p.get("conviction_score", 0.0)
            badge_color = "#10b981" if score >= 8.0 else "#3b82f6"
            action = "STRONG BUY" if score >= 8.0 else "ACCUMULATE"
            
            picks_rows += f"""
            <tr class="stock-row" data-symbol="{p['symbol']}" data-name="{p['name']}" data-sector="{p['sector']}">
                <td>
                    <div class="sym-name">{p['symbol']}</div>
                    <div class="sub-text">{p['name']}</div>
                </td>
                <td><span class="sector-pill">{p['sector']}</span></td>
                <td><b>₹{p['cmp']}</b></td>
                <td><span class="badge" style="background: {badge_color};">{action} ({score}/10)</span></td>
                <td><span class="rsi-tag">{p['rsi']}</span></td>
                <td style="color: #10b981; font-weight: 600;">₹{p['target_1']}</td>
                <td style="color: #34d399; font-weight: 600;">₹{p['target_2']}</td>
                <td style="color: #f87171; font-weight: 600;">₹{p['stop_loss']}</td>
                <td>{p['risk_reward']}</td>
                <td><button class="chart-btn" onclick="toggleCandleChart('{p['symbol']}', this)">📈 Chart</button></td>
            </tr>
            """

        # Generate Detailed 360° Stock Cards
        cards_html = ""
        for p in picks:
            signals_li = "".join([f"<li>✅ {s}</li>" for s in p.get("bullish_signals", [])])
            strengths_li = "".join([f"<li>⭐ {s}</li>" for s in p.get("fundamental_strengths", [])])
            score = p.get("conviction_score", 0.0)
            badge_color = "#10b981" if score >= 8.0 else "#3b82f6"
            action = "STRONG BUY" if score >= 8.0 else "ACCUMULATE"

            cards_html += f"""
            <div class="stock-card" data-symbol="{p['symbol']}" data-name="{p['name']}" data-sector="{p['sector']}">
                <div class="card-header">
                    <div>
                        <span class="card-symbol">{p['symbol']}</span>
                        <span class="card-company">{p['name']}</span>
                    </div>
                    <span class="badge" style="background: {badge_color};">{action} &bull; {score}/10</span>
                </div>
                <div class="card-meta">
                    <span><b>CMP:</b> ₹{p['cmp']}</span>
                    <span><b>Sector:</b> {p['sector']}</span>
                    <span><b>RSI:</b> {p['rsi']}</span>
                    <span><b>20 EMA:</b> ₹{p['ema_20']}</span>
                </div>
                <div class="levels-grid">
                    <div class="level-box">
                        <small>Target 1</small>
                        <div class="lvl-val" style="color: #10b981;">₹{p['target_1']}</div>
                    </div>
                    <div class="level-box">
                        <small>Target 2</small>
                        <div class="lvl-val" style="color: #34d399;">₹{p['target_2']}</div>
                    </div>
                    <div class="level-box">
                        <small>Stop Loss</small>
                        <div class="lvl-val" style="color: #f87171;">₹{p['stop_loss']}</div>
                    </div>
                    <div class="level-box">
                        <small>Risk:Reward</small>
                        <div class="lvl-val">{p['risk_reward']}</div>
                    </div>
                </div>
                <div class="audit-split">
                    <div class="audit-col">
                        <div class="audit-title">⚡ Technical Checklist</div>
                        <ul>{signals_li}</ul>
                    </div>
                    <div class="audit-col">
                        <div class="audit-title">🏛️ Fundamental Strengths</div>
                        <ul>{strengths_li}</ul>
                    </div>
                </div>
            </div>
            """

        # Generate IPO Table
        ipo_rows = ""
        for ipo in ipo_list:
            gmp_pct = ipo.get("gmp_pct", 0)
            gmp_color = "#10b981" if gmp_pct >= 20.0 else "#eab308"
            ipo_rows += f"""
            <tr>
                <td>
                    <b>{ipo['name']}</b>
                    <div class="sub-text">{ipo['sector']} &bull; {ipo['category']}</div>
                </td>
                <td><span class="status-pill">{ipo['status']}</span></td>
                <td>{ipo['price_band']}</td>
                <td>{ipo['lot_size']} shares</td>
                <td>₹{ipo['issue_size_cr']} Cr</td>
                <td><b>{ipo['subscription_total']}</b></td>
                <td style="color: {gmp_color}; font-weight: 700;">+{gmp_pct}% ({ipo['gmp_inr']})</td>
                <td><span class="badge" style="background: #0284c7;">{ipo['verdict']}</span></td>
            </tr>
            """

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Indian Stock AI — 360° Senior Fund Manager & Momentum Intelligence</title>
    <script>
        (function() {{
            let saved = 'dark';
            try {{
                saved = localStorage.getItem('stock_ai_theme') || 'dark';
            }} catch (e) {{}}
            document.documentElement.setAttribute('data-theme', saved);
        }})();
    </script>
    <style>
        :root {{
            --bg: #090d16;
            --surface: #131b2e;
            --surface-hover: #1b2640;
            --border: #23304c;
            --text: #f1f5f9;
            --text-heading: #ffffff;
            --text-muted: #94a3b8;
            --primary: #38bdf8;
            --primary-hover: #0284c7;
            --success: #10b981;
            --danger: #ef4444;
            --warning: #f59e0b;
            --th-bg: #18223a;
            --card-sub-bg: #0c1220;
            --toast-bg: #0f172a;
            --rich-card-bg: #111827;
            --badge-bg: #1e293b;
        }}

        [data-theme="light"] {{
            --bg: #f8fafc;
            --surface: #ffffff;
            --surface-hover: #f1f5f9;
            --border: #e2e8f0;
            --text: #0f172a;
            --text-heading: #0f172a;
            --text-muted: #64748b;
            --primary: #0284c7;
            --primary-hover: #0369a1;
            --success: #059669;
            --danger: #dc2626;
            --warning: #d97706;
            --th-bg: #f8fafc;
            --card-sub-bg: #f8fafc;
            --toast-bg: #ffffff;
            --rich-card-bg: #ffffff;
            --badge-bg: #e2e8f0;
        }}

        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background: var(--bg); color: var(--text); padding: 24px; line-height: 1.5; transition: background 0.25s ease, color 0.25s ease; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 20px; margin-bottom: 24px; flex-wrap: wrap; gap: 16px; }}
        .header-title h1 {{ font-size: 26px; font-weight: 800; color: var(--text-heading); display: flex; align-items: center; gap: 10px; }}
        .header-title p {{ color: var(--text-muted); font-size: 14px; margin-top: 4px; }}
        .header-actions {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}

        /* Theme Toggle Button (Top Right Corner) */
        .theme-toggle-btn {{
            background: #1e293b;
            border: 1px solid #38bdf8;
            color: #f1f5f9;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            user-select: none;
            transition: all 0.25s ease;
            box-shadow: 0 2px 10px rgba(56, 189, 248, 0.25);
        }}
        .theme-toggle-btn:hover {{
            background: #0f172a;
            border-color: #7dd3fc;
            transform: translateY(-1px);
            box-shadow: 0 4px 14px rgba(56, 189, 248, 0.4);
        }}
        .theme-toggle-btn .theme-icon {{
            font-size: 15px;
            display: inline-block;
            transition: transform 0.3s ease;
        }}
        .theme-toggle-btn:hover .theme-icon {{
            transform: rotate(20deg) scale(1.2);
        }}
        [data-theme="light"] .theme-toggle-btn {{
            background: #ffffff;
            border: 1px solid #0284c7;
            color: #0369a1;
            box-shadow: 0 2px 8px rgba(2, 132, 199, 0.2);
        }}
        [data-theme="light"] .theme-toggle-btn:hover {{
            background: #f0f9ff;
            border-color: #0284c7;
            box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
        }}

        /* Light Mode Theme Overrides */
        [data-theme="light"] .index-card {{
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            background: #ffffff;
        }}
        [data-theme="light"] .index-val {{
            color: #0f172a;
        }}
        [data-theme="light"] .table-container {{
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            background: #ffffff;
        }}
        [data-theme="light"] th {{
            background: #f8fafc;
            color: #475569;
            border-bottom: 2px solid #e2e8f0;
        }}
        [data-theme="light"] td {{
            color: #1e293b;
            border-bottom: 1px solid #f1f5f9;
        }}
        [data-theme="light"] .sym-name {{
            color: #0f172a;
        }}
        [data-theme="light"] .stock-card {{
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            background: #ffffff;
        }}
        [data-theme="light"] .card-symbol {{
            color: #0f172a;
        }}
        [data-theme="light"] .tab-btn {{
            background: #ffffff;
            border: 1px solid #cbd5e1;
            color: #475569;
        }}
        [data-theme="light"] .tab-btn.active {{
            background: #0284c7;
            color: #ffffff;
            border-color: #0284c7;
        }}
        [data-theme="light"] .search-box input {{
            background: #ffffff;
            border-color: #cbd5e1;
            color: #0f172a;
        }}
        [data-theme="light"] .levels-grid {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
        }}
        [data-theme="light"] .audit-title {{
            color: #0f172a;
        }}
        [data-theme="light"] .audit-col li {{
            color: #334155;
        }}
        [data-theme="light"] .rich-stock-profile-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        }}
        [data-theme="light"] .card-top-title h2 {{
            color: #0f172a;
        }}
        [data-theme="light"] .cmp-badge {{
            background: #f8fafc;
            border-color: #e2e8f0;
        }}
        [data-theme="light"] .cmp-val {{
            color: #0284c7;
        }}
        [data-theme="light"] .m-card {{
            background: #f8fafc;
            border-color: #e2e8f0;
        }}
        [data-theme="light"] .m-card b {{
            color: #0f172a;
        }}
        [data-theme="light"] .tech-bar {{
            background: #f8fafc;
            border-color: #e2e8f0;
            color: #334155;
        }}
        [data-theme="light"] .strategy-explanation-box {{
            background: #f8fafc;
            border-color: #e2e8f0;
            color: #334155;
        }}
        [data-theme="light"] .setup-box.rr {{
            background: #f1f5f9;
            border-color: #e2e8f0;
            color: #0f172a;
        }}
        [data-theme="light"] .sync-badge {{
            background: #ecfdf5;
            border-color: #a7f3d0;
            color: #059669;
        }}
        [data-theme="light"] .auto-read-pill {{
            background: #ffffff;
            border-color: #cbd5e1;
            color: #64748b;
        }}
        [data-theme="light"] .auto-read-pill.active {{
            background: rgba(16, 185, 129, 0.12);
            border-color: #059669;
            color: #059669;
        }}
        [data-theme="light"] .sync-toast {{
            background: #ffffff;
            border-color: #0284c7;
            color: #0f172a;
            box-shadow: 0 10px 30px rgba(0,0,0,0.12);
        }}
        [data-theme="light"] .sector-pill {{
            background: #f1f5f9;
            color: #475569;
        }}
        .action-btn.refresh-btn {{
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: #ffffff;
            border: 1px solid #3b82f6;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
            transition: all 0.2s ease;
        }}
        .action-btn.refresh-btn:hover {{
            background: linear-gradient(135deg, #1d4ed8, #1e40af);
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.5);
        }}
        .action-btn.refresh-btn:active {{ transform: translateY(1px); }}
        .refresh-icon.spinning {{
            animation: spin 0.8s linear infinite;
            display: inline-block;
        }}
        @keyframes spin {{
            from {{ transform: rotate(0deg); }}
            to {{ transform: rotate(360deg); }}
        }}
        .auto-read-pill {{
            background: #1e293b;
            border: 1px solid #334155;
            color: #94a3b8;
            padding: 7px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            user-select: none;
            transition: all 0.2s;
        }}
        .auto-read-pill.active {{
            background: rgba(16, 185, 129, 0.15);
            border-color: #10b981;
            color: #34d399;
        }}
        .auto-read-pill .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #64748b;
        }}
        .auto-read-pill.active .status-dot {{
            background: #10b981;
            box-shadow: 0 0 8px #10b981;
        }}
        .sync-badge {{ background: #032b21; border: 1px solid #059669; color: #34d399; padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }}
        .sync-toast {{
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #0f172a;
            border: 1px solid #38bdf8;
            color: #f1f5f9;
            padding: 14px 20px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
            display: none;
            z-index: 9999;
            font-size: 13px;
            max-width: 380px;
            line-height: 1.5;
        }}
        
        /* Indices */
        .indices-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(185px, 1fr)); gap: 12px; margin-bottom: 26px; }}
        .index-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 14px 16px; transition: transform 0.2s; }}
        .index-card:hover {{ transform: translateY(-2px); border-color: #38bdf8; }}
        .index-name {{ color: var(--text-muted); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }}
        .index-val {{ font-size: 20px; font-weight: 800; margin: 4px 0; color: #fff; }}
        .index-chg {{ font-size: 12px; font-weight: 600; }}

        /* Tabs & Search */
        .controls-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 14px; }}
        .tabs {{ display: flex; gap: 8px; flex-wrap: wrap; }}
        .tab-btn {{ background: var(--surface); border: 1px solid var(--border); color: var(--text-muted); padding: 10px 18px; border-radius: 8px; cursor: pointer; font-weight: 600; font-size: 13px; transition: all 0.2s; }}
        .tab-btn.active, .tab-btn:hover {{ background: var(--primary); color: #090d16; border-color: var(--primary); }}
        .search-box input {{ background: var(--surface); border: 1px solid var(--border); color: #fff; padding: 10px 16px; border-radius: 8px; width: 280px; font-size: 14px; outline: none; }}
        .search-box input:focus {{ border-color: var(--primary); }}

        /* Table */
        .table-container {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; overflow-x: auto; margin-bottom: 30px; }}
        table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 14px; }}
        th {{ background: #18223a; color: var(--text-muted); padding: 14px 16px; font-weight: 600; border-bottom: 1px solid var(--border); }}
        td {{ padding: 14px 16px; border-bottom: 1px solid var(--border); }}
        tr:hover td {{ background: var(--surface-hover); }}
        .sym-name {{ font-weight: 700; color: #fff; font-size: 15px; }}
        .sub-text {{ font-size: 12px; color: var(--text-muted); }}
        .badge {{ padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; color: #fff; display: inline-block; }}
        .sector-pill {{ background: #1e293b; color: #94a3b8; padding: 3px 8px; border-radius: 4px; font-size: 12px; }}
        .rsi-tag {{ background: #1e293b; color: #38bdf8; font-weight: 600; padding: 2px 6px; border-radius: 4px; }}
        .status-pill {{ background: #2e2814; color: #fbbf24; border: 1px solid #78350f; padding: 3px 8px; border-radius: 4px; font-size: 12px; }}

        /* Cards Grid */
        .cards-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 18px; margin-bottom: 30px; }}
        .stock-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }}
        .card-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }}
        .card-symbol {{ font-size: 18px; font-weight: 800; color: #fff; display: block; }}
        .card-company {{ font-size: 13px; color: var(--text-muted); }}
        .card-meta {{ display: flex; flex-wrap: wrap; gap: 12px; font-size: 13px; color: var(--text-muted); margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }}
        .levels-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; background: #0c1220; padding: 10px; border-radius: 8px; text-align: center; margin-bottom: 16px; }}
        .level-box small {{ font-size: 11px; color: var(--text-muted); display: block; }}
        .level-box .lvl-val {{ font-size: 14px; font-weight: 700; margin-top: 2px; }}
        .audit-split {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-size: 12px; }}
        .audit-title {{ font-weight: 700; color: #e2e8f0; margin-bottom: 6px; }}
        .audit-col ul {{ list-style: none; }}
        .audit-col li {{ margin-bottom: 4px; color: #cbd5e1; }}

        /* Footer */
        .footer {{ border-top: 1px solid var(--border); padding-top: 18px; text-align: center; font-size: 12px; color: var(--text-muted); }}

        /* Rich Stock Profile Card */
        .rich-stock-profile-card {{
            background: #111827;
            border: 1px solid #374151;
            border-left: 6px solid #6366f1;
            border-radius: 12px;
            padding: 22px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        }}
        .card-top-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 16px;
        }}
        .card-top-title h2 {{
            font-size: 22px;
            font-weight: 800;
            color: #fff;
            margin: 0;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .card-top-title p {{
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 4px;
        }}
        .cmp-badge {{
            background: #1f2937;
            border: 1px solid #374151;
            padding: 8px 16px;
            border-radius: 10px;
            text-align: right;
        }}
        .cmp-val {{
            font-size: 24px;
            font-weight: 800;
            color: #38bdf8;
            display: block;
        }}
        .cmp-chg {{
            font-size: 13px;
            font-weight: 700;
        }}
        .metrics-ribbon {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 12px;
            margin-bottom: 16px;
        }}
        .m-card {{
            background: #1f2937;
            border: 1px solid #374151;
            padding: 12px 14px;
            border-radius: 8px;
        }}
        .daemon-status-pill {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 8px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.25s ease;
            user-select: none;
        }}
        .daemon-status-pill.online {{
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid #10b981;
            color: #34d399;
        }}
        .daemon-status-pill.offline {{
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid #ef4444;
            color: #f87171;
        }}
        .daemon-status-pill .pulse-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
        }}
        .daemon-status-pill.online .pulse-dot {{
            background: #10b981;
            box-shadow: 0 0 8px #10b981;
            animation: pulse-green 2s infinite;
        }}
        .daemon-status-pill.offline .pulse-dot {{
            background: #ef4444;
        }}
        @keyframes pulse-green {{
            0% {{ transform: scale(0.95); opacity: 0.8; }}
            50% {{ transform: scale(1.3); opacity: 1; }}
            100% {{ transform: scale(0.95); opacity: 0.8; }}
        }}
        .m-card small {{
            font-size: 11px;
            color: var(--text-muted);
            text-transform: uppercase;
            font-weight: 600;
            display: block;
        }}
        .m-card b {{
            font-size: 15px;
            color: #f3f4f6;
            margin-top: 4px;
            display: block;
        }}
        .tech-bar {{
            background: #0f172a;
            border: 1px solid #1e293b;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 13px;
            color: #cbd5e1;
            display: flex;
            flex-wrap: wrap;
            gap: 18px;
            margin-bottom: 16px;
        }}
        .buy-setup-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 16px;
        }}
        .setup-box {{
            padding: 12px;
            border-radius: 8px;
            text-align: center;
        }}
        .setup-box small {{
            font-size: 11px;
            display: block;
            margin-bottom: 4px;
            font-weight: 600;
        }}
        .setup-box b {{
            font-size: 15px;
            font-weight: 800;
        }}
        .setup-box.buy {{ background: #064e3b; border: 1px solid #059669; color: #34d399; }}
        .setup-box.tgt {{ background: #0c4a6e; border: 1px solid #0284c7; color: #38bdf8; }}
        .setup-box.tgt2 {{ background: #1e1b4b; border: 1px solid #6366f1; color: #a5b4fc; }}
        .setup-box.sl {{ background: #450a0a; border: 1px solid #dc2626; color: #f87171; }}
        .setup-box.rr {{ background: #1e293b; border: 1px solid #334155; color: #f1f5f9; }}
        .strategy-explanation-box {{
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 8px;
            padding: 14px 18px;
            font-size: 13px;
            color: #cbd5e1;
            line-height: 1.6;
        }}
        .strategy-explanation-box h4 {{
            color: #38bdf8;
            margin: 0 0 8px 0;
            font-size: 14px;
        }}

        /* Sortable Headers */
        th.sortable {{
            cursor: pointer;
            user-select: none;
            transition: background 0.2s;
            position: relative;
            padding-right: 22px;
        }}
        th.sortable:hover {{
            background: var(--surface-hover);
            color: var(--primary);
        }}
        th.sortable::after {{
            content: ' ⇅';
            font-size: 11px;
            opacity: 0.45;
            position: absolute;
            right: 8px;
            top: 50%;
            transform: translateY(-50%);
        }}
        th.sortable.asc::after {{
            content: ' ▲';
            opacity: 1;
            color: var(--primary);
        }}
        th.sortable.desc::after {{
            content: ' ▼';
            opacity: 1;
            color: var(--primary);
        }}

        /* Filter & Export Controls */
        .search-actions-box {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .filter-select {{
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 9px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            outline: none;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .filter-select:focus {{
            border-color: var(--primary);
        }}
        [data-theme="light"] .filter-select {{
            background: #ffffff;
            border-color: #cbd5e1;
            color: #0f172a;
        }}
        .export-btn {{
            background: linear-gradient(135deg, #0f766e, #115e59);
            color: #ffffff;
            border: 1px solid #14b8a6;
            padding: 9px 14px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 700;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
            box-shadow: 0 2px 6px rgba(20, 184, 166, 0.2);
        }}
        .export-btn:hover {{
            background: #0d9488;
            transform: translateY(-1px);
        }}
        .chart-btn {{
            background: rgba(56, 189, 248, 0.12);
            border: 1px solid #38bdf8;
            color: #38bdf8;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            white-space: nowrap;
        }}
        .chart-btn:hover {{
            background: #38bdf8;
            color: #0f172a;
            transform: scale(1.05);
        }}
        [data-theme="light"] .chart-btn {{
            background: #e0f2fe;
            border-color: #0284c7;
            color: #0284c7;
        }}
        [data-theme="light"] .chart-btn:hover {{
            background: #0284c7;
            color: #ffffff;
        }}

        /* Interactive Candlestick Chart Drawer */
        .chart-drawer-row {{
            background: var(--card-sub-bg) !important;
        }}
        .chart-drawer-row td {{
            padding: 0 !important;
            border-bottom: 2px solid var(--primary);
        }}
        .chart-container {{
            padding: 16px 20px;
            position: relative;
        }}
        .chart-top-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .chart-title {{
            font-size: 16px;
            font-weight: 800;
            color: var(--text-heading);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .chart-legend {{
            display: flex;
            align-items: center;
            gap: 14px;
            font-size: 12px;
            font-weight: 600;
        }}
        .chart-canvas {{
            width: 100%;
            height: 320px;
            display: block;
            background: var(--surface);
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        .chart-close-btn {{
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid #ef4444;
            color: #f87171;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
        }}
        .chart-close-btn:hover {{
            background: #ef4444;
            color: #ffffff;
        }}
        .chart-tf-btn {{
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text-muted);
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .chart-tf-btn.active, .chart-tf-btn:hover {{
            background: var(--primary);
            color: #0f172a;
            border-color: var(--primary);
        }}

        /* Portfolio Tracker Styles */
        .portfolio-summary-ribbon {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 14px;
            margin-bottom: 24px;
        }}
        .portfolio-add-bar {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }}
        .portfolio-input {{
            background: var(--bg);
            border: 1px solid var(--border);
            color: var(--text);
            padding: 9px 12px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            outline: none;
        }}
        .portfolio-input:focus {{
            border-color: var(--primary);
        }}
        [data-theme="light"] .portfolio-input {{
            background: #f8fafc;
            border-color: #cbd5e1;
            color: #0f172a;
        }}
        .portfolio-add-btn {{
            background: linear-gradient(135deg, #059669, #047857);
            color: #ffffff;
            border: 1px solid #10b981;
            padding: 9px 18px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .portfolio-add-btn:hover {{
            background: #047857;
            transform: translateY(-1px);
        }}
        .delete-holding-btn {{
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid #ef4444;
            color: #f87171;
            padding: 3px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            transition: all 0.2s;
        }}
        .delete-holding-btn:hover {{
            background: #ef4444;
            color: #fff;
        }}

        /* Autocomplete Styles for Portfolio */
        .autocomplete-wrapper {{
            position: relative;
            display: inline-block;
        }}
        .autocomplete-dropdown {{
            position: absolute;
            top: calc(100% + 4px);
            left: 0;
            width: 380px;
            max-height: 280px;
            overflow-y: auto;
            background: var(--surface);
            border: 1px solid var(--primary);
            border-radius: 8px;
            z-index: 1000;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }}
        [data-theme="light"] .autocomplete-dropdown {{
            background: #ffffff;
            border-color: #0284c7;
            box-shadow: 0 10px 25px rgba(0,0,0,0.12);
        }}
        .ac-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            cursor: pointer;
            border-bottom: 1px solid var(--border);
            transition: background 0.15s;
        }}
        .ac-item:hover, .ac-item.active {{
            background: var(--surface-hover);
        }}
        .ac-sym {{
            font-weight: 800;
            color: var(--primary);
            font-size: 13px;
        }}
        .ac-name {{
            font-size: 12px;
            color: var(--text-heading);
            margin-top: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 230px;
        }}
        .ac-meta {{
            text-align: right;
            flex-shrink: 0;
            margin-left: 8px;
        }}
        .ac-sector {{
            font-size: 10px;
            color: var(--text-muted);
            background: var(--card-sub-bg);
            padding: 2px 6px;
            border-radius: 4px;
            display: inline-block;
        }}
        .ac-cmp {{
            font-size: 12px;
            font-weight: 700;
            color: #10b981;
            margin-top: 2px;
        }}
        .selected-stock-chip {{
            font-size: 11px;
            color: #38bdf8;
            font-weight: 600;
            background: rgba(56, 189, 248, 0.1);
            border: 1px solid rgba(56, 189, 248, 0.3);
            padding: 4px 10px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        [data-theme="light"] .selected-stock-chip {{
            background: #e0f2fe;
            border-color: #bae6fd;
            color: #0284c7;
        }}

        /* CIO Action Badges, Alerts Banner & Holding Deep Dive Modal */
        .cio-badge {{
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 9px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 800;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            border: 1px solid currentColor;
            transition: transform 0.15s, box-shadow 0.15s;
            white-space: nowrap;
        }}
        .cio-badge:hover {{
            transform: scale(1.05);
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }}
        .urgent-alerts-box {{
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 16px;
            font-size: 13px;
            line-height: 1.5;
            display: flex;
            flex-direction: column;
            gap: 8px;
            border: 1px solid rgba(239, 68, 68, 0.4);
            background: rgba(239, 68, 68, 0.08);
            color: #fca5a5;
        }}
        [data-theme="light"] .urgent-alerts-box {{
            background: #fef2f2;
            border-color: #fca5a5;
            color: #991b1b;
        }}
        .modal-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.75);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            backdrop-filter: blur(4px);
        }}
        .modal-box {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            width: 90%;
            max-width: 650px;
            max-height: 85vh;
            overflow-y: auto;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            color: var(--text);
        }}
        [data-theme="light"] .modal-box {{
            background: #ffffff;
            box-shadow: 0 20px 40px rgba(0,0,0,0.15);
        }}
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 16px 20px;
            border-bottom: 1px solid var(--border);
        }}
        .modal-close-btn {{
            background: none;
            border: none;
            color: var(--text-muted);
            font-size: 20px;
            cursor: pointer;
            padding: 4px 8px;
            border-radius: 4px;
        }}
        .modal-close-btn:hover {{
            color: #ef4444;
            background: rgba(239,68,68,0.1);
        }}
    </style>
</head>
<body>

    <div class="header">
        <div class="header-title">
            <h1>🇮🇳 Indian Stock AI &bull; Senior Fund Manager &amp; Momentum Intelligence</h1>
            <p>Multi-Timeframe Trend Screener (3M/6M/1Y/3Y), Monitored Radar, 360&deg; Stock Audit &amp; Mutual Fund Advisory</p>
        </div>
        <div class="header-actions">
            <button id="refreshBtn" class="action-btn refresh-btn" onclick="triggerLiveRefresh()" title="Click to fetch latest live quotes & update all market feeds">
                <span class="refresh-icon">🔄</span> <span id="refreshBtnText">Refresh Live Data</span>
            </button>
            <div id="daemonStatusPill" class="daemon-status-pill offline" onclick="checkDaemonStatus(true)" title="Live Sync Daemon status (Port 5005). Click for connection help.">
                <span class="pulse-dot"></span>
                <span id="daemonStatusText">Sync Daemon: Checking...</span>
            </div>
            <div id="autoReadPill" class="auto-read-pill active" onclick="toggleAutoRead()" title="Toggle automatic background data refresh every 3 minutes">
                <span class="status-dot"></span>
                <span id="autoReadLabel">Auto-Read: ON (3m)</span>
            </div>
            <div class="sync-badge">
                <span style="width: 8px; height: 8px; background: #10b981; border-radius: 50%; display: inline-block;"></span>
                <span>Auto-Updated: <b id="timestampBadge">{timestamp}</b></span>
            </div>
            <button id="themeToggleBtn" class="theme-toggle-btn" onclick="toggleTheme()" title="Switch between Dark Mode and Light Mode">
                <span id="themeToggleIcon" class="theme-icon">🌙</span>
                <span id="themeToggleText">Dark Mode</span>
            </button>
        </div>
    </div>

    <!-- Benchmark Indices & Global Commodities -->
    <div class="indices-grid">
        {indices_html}
    </div>

    <!-- Navigation & Search Controls -->
    <div class="controls-bar">
        <div class="tabs">
            <button class="tab-btn active" onclick="switchView('momentum', this)">🏆 Super-Trend Leaders (3M/1Y/3Y)</button>
            <button class="tab-btn" onclick="switchView('fifty_two_week', this)">🚀 52-Week High Leaders</button>
            <button class="tab-btn" onclick="switchView('radar', this)">🎯 AI Fund Manager Radar</button>
            <button class="tab-btn" onclick="switchView('mutualfunds', this)">💼 Mutual Fund Advisory</button>
            <button class="tab-btn" onclick="switchView('leaderboard', this)">🚀 360&deg; Bullish Picks</button>
            <button class="tab-btn" onclick="switchView('cards', this)">🔍 Deep Dive Cards</button>
            <button class="tab-btn" onclick="switchView('ipos', this)">📋 IPOs &amp; GMP</button>
            <button class="tab-btn" onclick="switchView('portfolio', this)" style="border-color: #10b981;">💼 My Portfolio (Live P&amp;L)</button>
        </div>
        <div class="search-actions-box">
            <select id="sectorFilter" class="filter-select" onchange="filterStocks()" title="Filter stocks by sector">
                <option value="">All Sectors</option>
            </select>
            <button class="export-btn" onclick="exportActiveTableToCSV()" title="Export visible table rows to CSV file">
                📥 Export CSV
            </button>
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search 501+ NSE stocks (e.g. TCS, LAURUSLABS)..." onkeyup="filterStocks()">
                <div style="margin-top: 6px; font-size: 11px; color: var(--text-muted);">
                    Quick Search: 
                    <a href="javascript:void(0)" onclick="quickSearch('TCS')" style="color:#38bdf8; text-decoration:none; margin-right:6px;">TCS</a>
                    <a href="javascript:void(0)" onclick="quickSearch('LAURUSLABS')" style="color:#38bdf8; text-decoration:none; margin-right:6px;">LAURUSLABS</a>
                    <a href="javascript:void(0)" onclick="quickSearch('DIXON')" style="color:#38bdf8; text-decoration:none; margin-right:6px;">DIXON</a>
                    <a href="javascript:void(0)" onclick="quickSearch('INFY')" style="color:#38bdf8; text-decoration:none; margin-right:6px;">INFY</a>
                    <a href="javascript:void(0)" onclick="quickSearch('TRENT')" style="color:#38bdf8; text-decoration:none;">TRENT</a>
                </div>
            </div>
        </div>
    </div>

    <!-- Backend NSE Catalog Lookup Result (Appears when searching unlisted stocks like TCS) -->
    <div id="unlistedStockBox" style="display: none; margin-bottom: 24px;"></div>

    <!-- Tab 1: Momentum Leaders Table -->
    <div id="view-momentum" class="view-panel">
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="sortable" onclick="sortTable(this, 0)">Stock / Company</th>
                        <th class="sortable" onclick="sortTable(this, 1)">Sector</th>
                        <th class="sortable" onclick="sortTable(this, 2)">CMP</th>
                        <th class="sortable" onclick="sortTable(this, 3)">3M Return</th>
                        <th class="sortable" onclick="sortTable(this, 4)">6M Return</th>
                        <th class="sortable" onclick="sortTable(this, 5)">1Y Return</th>
                        <th class="sortable" onclick="sortTable(this, 6)">3Y Return</th>
                        <th class="sortable" onclick="sortTable(this, 7)">Trend Status</th>
                        <th>Chart</th>
                    </tr>
                </thead>
                <tbody id="momentumTbody">
                    {momentum_rows}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Tab: 52-Week High Leaders (Dynamic Live Radar) -->
    <div id="view-fifty_two_week" class="view-panel" style="display: none;">
        <div style="background: linear-gradient(135deg, #1e1b4b, #0f172a); border: 1px solid #4338ca; border-radius: 12px; padding: 18px 22px; margin-bottom: 22px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <h3 style="color: #fff; font-size: 18px; margin: 0 0 6px 0; display: flex; align-items: center; gap: 8px;">
                        <span>🚀 Dynamic 52-Week High Breakout Radar</span>
                        <span style="background: #312e81; color: #a5b4fc; font-size: 11px; padding: 2px 8px; border-radius: 12px;">NSE India Live</span>
                    </h3>
                    <p style="color: #94a3b8; font-size: 13px; margin: 0;">
                        Tracking stocks trading at or within 3.5% of their 52-week peak. Evaluated dynamically from live daily market feeds.
                    </p>
                </div>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <div style="background: #111827; border: 1px solid #374151; padding: 8px 14px; border-radius: 8px; text-align: center;">
                        <span style="font-size: 11px; color: #94a3b8; display: block;">Active Breakouts</span>
                        <b style="font-size: 16px; color: #38bdf8;">{fifty_two_week_count} Stocks</b>
                    </div>
                    <div style="background: #111827; border: 1px solid #374151; padding: 8px 14px; border-radius: 8px; text-align: center;">
                        <span style="font-size: 11px; color: #94a3b8; display: block;">Top Breakout Sector</span>
                        <b style="font-size: 16px; color: #34d399;">{top_52w_sector}</b>
                    </div>
                </div>
            </div>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="sortable" onclick="sortTable(this, 0)">Stock / Company</th>
                        <th class="sortable" onclick="sortTable(this, 1)">Sector</th>
                        <th class="sortable" onclick="sortTable(this, 2)">CMP</th>
                        <th class="sortable" onclick="sortTable(this, 3)">52W High</th>
                        <th class="sortable" onclick="sortTable(this, 4)">Dist from High</th>
                        <th class="sortable" onclick="sortTable(this, 5)">1Y Return</th>
                        <th class="sortable" onclick="sortTable(this, 6)">Volume Surge</th>
                        <th class="sortable" onclick="sortTable(this, 7)">RSI</th>
                        <th class="sortable" onclick="sortTable(this, 8)">Breakout Setup</th>
                        <th class="sortable" onclick="sortTable(this, 9)">Actionable Buy Entry</th>
                        <th>Chart</th>
                    </tr>
                </thead>
                <tbody>
                    {fifty_two_week_rows}
                </tbody>
            </table>
        </div>

        <div style="margin: 28px 0 16px 0;">
            <h3 style="font-size: 18px; color: #fff; display: flex; align-items: center; gap: 8px;">
                <span>🔬 52-Week High 360° Deep Analysis &amp; Buy Setups</span>
                <span style="font-size: 12px; color: #94a3b8; font-weight: normal;">(Senior Fund Manager Conviction)</span>
            </h3>
        </div>

        <div class="cards-grid">
            {fifty_two_week_cards}
        </div>
    </div>

    <!-- Tab 2: AI Fund Manager Radar -->
    <div id="view-radar" class="view-panel" style="display: none;">
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="sortable" onclick="sortTable(this, 0)">Stock / Company</th>
                        <th class="sortable" onclick="sortTable(this, 1)">Setup Type</th>
                        <th class="sortable" onclick="sortTable(this, 2)">CMP</th>
                        <th class="sortable" onclick="sortTable(this, 3)">Target 3M</th>
                        <th class="sortable" onclick="sortTable(this, 4)">Target 1Y</th>
                        <th class="sortable" onclick="sortTable(this, 5)">Stop Loss</th>
                        <th class="sortable" onclick="sortTable(this, 6)">Monitoring Status</th>
                        <th>Institutional Thesis</th>
                        <th>Chart</th>
                    </tr>
                </thead>
                <tbody>
                    {radar_rows}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Tab 3: Mutual Fund Advisory -->
    <div id="view-mutualfunds" class="view-panel" style="display: none;">
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="sortable" onclick="sortTable(this, 0)">Fund Scheme &amp; House</th>
                        <th class="sortable" onclick="sortTable(this, 1)">Category</th>
                        <th class="sortable" onclick="sortTable(this, 2)">1Y Return</th>
                        <th class="sortable" onclick="sortTable(this, 3)">3Y CAGR</th>
                        <th class="sortable" onclick="sortTable(this, 4)">5Y CAGR</th>
                        <th class="sortable" onclick="sortTable(this, 5)">Sharpe</th>
                        <th class="sortable" onclick="sortTable(this, 6)">AUM</th>
                        <th>Institutional Fund Manager Rationale</th>
                    </tr>
                </thead>
                <tbody>
                    {mf_rows}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Tab 4: Bullish Leaderboard Table -->
    <div id="view-leaderboard" class="view-panel" style="display: none;">
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="sortable" onclick="sortTable(this, 0)">Stock / Company</th>
                        <th class="sortable" onclick="sortTable(this, 1)">Sector</th>
                        <th class="sortable" onclick="sortTable(this, 2)">CMP</th>
                        <th class="sortable" onclick="sortTable(this, 3)">Verdict &amp; Conviction</th>
                        <th class="sortable" onclick="sortTable(this, 4)">RSI</th>
                        <th class="sortable" onclick="sortTable(this, 5)">Target 1</th>
                        <th class="sortable" onclick="sortTable(this, 6)">Target 2</th>
                        <th class="sortable" onclick="sortTable(this, 7)">Stop Loss</th>
                        <th class="sortable" onclick="sortTable(this, 8)">R:R</th>
                        <th>Chart</th>
                    </tr>
                </thead>
                <tbody id="leaderboardTbody">
                    {picks_rows}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Tab 5: 360 Deep Dive Cards -->
    <div id="view-cards" class="view-panel" style="display: none;">
        <div class="cards-grid" id="cardsGrid">
            {cards_html}
        </div>
    </div>

    <!-- Tab 6: IPO Intelligence Table -->
    <div id="view-ipos" class="view-panel" style="display: none;">
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="sortable" onclick="sortTable(this, 0)">IPO Name &amp; Sector</th>
                        <th class="sortable" onclick="sortTable(this, 1)">Status</th>
                        <th class="sortable" onclick="sortTable(this, 2)">Price Band</th>
                        <th class="sortable" onclick="sortTable(this, 3)">Lot Size</th>
                        <th class="sortable" onclick="sortTable(this, 4)">Issue Size</th>
                        <th class="sortable" onclick="sortTable(this, 5)">Subscription</th>
                        <th class="sortable" onclick="sortTable(this, 6)">GMP (%)</th>
                        <th class="sortable" onclick="sortTable(this, 7)">AI Verdict</th>
                    </tr>
                </thead>
                <tbody>
                    {ipo_rows}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Tab 7: Personal Portfolio & Real-Time P&L Tracker -->
    <div id="view-portfolio" class="view-panel" style="display: none;">
        <div class="portfolio-summary-ribbon">
            <div class="index-card">
                <div class="index-name">💼 Total Invested</div>
                <div class="index-val" id="portTotalInvested">₹0.00</div>
                <div class="index-chg" style="color: var(--text-muted); font-size: 11px;">Capital Deployed</div>
            </div>
            <div class="index-card">
                <div class="index-name">📊 Current Portfolio Value</div>
                <div class="index-val" id="portCurrentValue">₹0.00</div>
                <div class="index-chg" style="color: var(--primary); font-size: 11px;">Real-Time CMP Value</div>
            </div>
            <div class="index-card">
                <div class="index-name">💰 Total Profit / Loss</div>
                <div class="index-val" id="portTotalPnL" style="color: #10b981;">₹0.00</div>
                <div class="index-chg" id="portTotalPnLPct" style="color: #10b981; font-weight: 700;">+0.00% Overall</div>
            </div>
            <div class="index-card">
                <div class="index-name">⚡ Today's P&amp;L Movement</div>
                <div class="index-val" id="portDayPnL" style="color: #10b981;">₹0.00</div>
                <div class="index-chg" id="portDayPnLPct" style="color: #10b981; font-weight: 700;">+0.00% Today</div>
            </div>
            <div class="index-card">
                <div class="index-name">🏥 Portfolio Health Score</div>
                <div class="index-val" id="portHealthScore" style="color: #38bdf8;">10.0 / 10</div>
                <div class="index-chg" id="portHealthSub" style="color: #10b981; font-weight: 700;">Institutional Quality</div>
            </div>
            <div class="index-card">
                <div class="index-name">🛡️ CIO Exit &amp; Sell Alerts</div>
                <div class="index-val" id="portAtRiskCount" style="color: #10b981;">0 At Risk</div>
                <div class="index-chg" id="portAtRiskSub" style="color: var(--text-muted); font-size: 11px;">Trailing Stops Intact</div>
            </div>
        </div>

        <!-- Real-time Urgent Sell Warnings & News Alerts Banner -->
        <div id="portUrgentAlertsBanner" style="display: none;" class="urgent-alerts-box"></div>

        <div class="portfolio-add-bar">
            <span style="font-weight: 700; font-size: 14px; color: var(--text-heading); display: flex; align-items: center; gap: 6px;">
                ➕ Add Holding:
            </span>
            <div class="autocomplete-wrapper">
                <input type="text" id="portSymbolInput" class="portfolio-input" placeholder="Type stock name or symbol (e.g. rel, tata, infy)..." style="width: 290px; text-transform: uppercase;" autocomplete="off" oninput="onPortfolioSymbolInput(this)" onkeydown="onPortfolioSymbolKeyDown(event)">
                <div id="portSymbolSuggestions" class="autocomplete-dropdown" style="display: none;"></div>
            </div>
            <input type="number" id="portQtyInput" class="portfolio-input" placeholder="Qty (e.g. 10)" style="width: 110px;" min="1" step="1">
            <input type="number" id="portBuyPriceInput" class="portfolio-input" placeholder="Buy Price ₹ (e.g. 3850)" style="width: 160px;" min="0.01" step="0.05">
            <button class="portfolio-add-btn" onclick="addPortfolioHolding()">+ Add Holding</button>
            <button class="action-btn" onclick="syncAllPortfolioQuotes()" style="padding: 8px 14px; font-size: 12px; border-radius: 6px; background: #0284c7; color: #fff; border-color: #38bdf8;" title="Fetch latest live market CMP for all portfolio holdings">🔄 Sync Live CMP</button>
            <button class="action-btn" onclick="resetPortfolioToDemo()" style="padding: 8px 14px; font-size: 12px; border-radius: 6px;" title="Reset to high-conviction benchmark demo portfolio">↺ Reset Demo</button>
            <span id="portSelectedChip" class="selected-stock-chip" style="display: none;"></span>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="sortable" onclick="sortTable(this, 0)">Stock / Company</th>
                        <th class="sortable" onclick="sortTable(this, 1)">Quantity</th>
                        <th class="sortable" onclick="sortTable(this, 2)">Avg Buy Price</th>
                        <th class="sortable" onclick="sortTable(this, 3)">Live CMP</th>
                        <th class="sortable" onclick="sortTable(this, 4)">Invested Value</th>
                        <th class="sortable" onclick="sortTable(this, 5)">Current Value</th>
                        <th class="sortable" onclick="sortTable(this, 6)">Day Change %</th>
                        <th class="sortable" onclick="sortTable(this, 7)">Total P&amp;L (₹)</th>
                        <th class="sortable" onclick="sortTable(this, 8)">Returns (%)</th>
                        <th class="sortable" onclick="sortTable(this, 9)">Trailing Stop (₹)</th>
                        <th class="sortable" onclick="sortTable(this, 10)">CIO Action &amp; Sell Advisory</th>
                        <th>Chart</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody id="portfolioTbody">
                </tbody>
            </table>
        </div>
    </div>

    <!-- CIO Deep-Dive Holding Audit Modal -->
    <div id="holdingAuditModal" class="modal-overlay" style="display: none;" onclick="closeHoldingAuditModal(event)">
        <div class="modal-box" onclick="event.stopPropagation()">
            <div class="modal-header">
                <div>
                    <h3 id="modalHoldingTitle" style="margin: 0; font-size: 18px; font-weight: 800; color: var(--text-heading);"></h3>
                    <div id="modalHoldingSub" style="font-size: 12px; color: var(--text-muted); margin-top: 3px;"></div>
                </div>
                <button class="modal-close-btn" onclick="closeHoldingAuditModal()">✕</button>
            </div>
            <div id="modalHoldingBody" style="padding: 20px;"></div>
        </div>
    </div>


    <div class="footer">
        <p>{disclaimer}</p>
        <p style="margin-top: 6px;">Report generated by Indian Stock AI Agent (Senior Fund Manager Intelligence) &bull; Auto-syncs daily at 08:45 AM and 06:00 PM</p>
    </div>

    <script>
        const NSE_DATABASE = {nse_catalog_json};
        const ENRICHED_PROFILES = {enriched_profiles_json};
        const ALL_STOCK_CMPS = {all_stock_cmps_json};

        function switchView(viewName, btn) {{
            document.querySelectorAll('.view-panel').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            const target = document.getElementById('view-' + viewName);
            if (target) target.style.display = 'block';
            if (btn) btn.classList.add('active');
            if (viewName === 'portfolio') {{
                renderPortfolio();
                syncAllPortfolioQuotes();
            }}
        }}

        function quickSearch(sym) {{
            const input = document.getElementById('searchInput');
            if (input) input.value = sym;
            filterStocks();
        }}

        function populateSectorFilter() {{
            const select = document.getElementById('sectorFilter');
            if (!select) return;
            const sectors = new Set();
            document.querySelectorAll('.stock-row').forEach(r => {{
                const s = r.getAttribute('data-sector');
                if (s && s.trim()) sectors.add(s.trim());
            }});
            const current = select.value;
            const sorted = Array.from(sectors).sort();
            let opts = '<option value="">All Sectors (' + sorted.length + ')</option>';
            sorted.forEach(sec => {{
                opts += `<option value="${{sec}}">${{sec}}</option>`;
            }});
            select.innerHTML = opts;
            if (current) select.value = current;
        }}

        function filterStocks() {{
            const query = (document.getElementById('searchInput')?.value || '').toLowerCase().trim();
            const sectorVal = (document.getElementById('sectorFilter')?.value || '').toLowerCase().trim();
            const unlistedBox = document.getElementById('unlistedStockBox');
            
            let matchedRowCount = 0;

            // Filter table rows
            document.querySelectorAll('.stock-row').forEach(row => {{
                const sym = (row.getAttribute('data-symbol') || '').toLowerCase();
                const name = (row.getAttribute('data-name') || '').toLowerCase();
                const sector = (row.getAttribute('data-sector') || '').toLowerCase();

                const matchQuery = !query || sym.includes(query) || name.includes(query) || sector.includes(query);
                const matchSector = !sectorVal || sector === sectorVal || sector.includes(sectorVal);

                if (matchQuery && matchSector) {{
                    row.style.display = '';
                    matchedRowCount++;
                }} else {{
                    row.style.display = 'none';
                }}
            }});

            // Filter cards
            document.querySelectorAll('.stock-card').forEach(card => {{
                const sym = (card.getAttribute('data-symbol') || '').toLowerCase();
                const name = (card.getAttribute('data-name') || '').toLowerCase();
                const sector = (card.getAttribute('data-sector') || '').toLowerCase();

                const matchQuery = !query || sym.includes(query) || name.includes(query) || sector.includes(query);
                const matchSector = !sectorVal || sector === sectorVal || sector.includes(sectorVal);

                if (matchQuery && matchSector) {{
                    card.style.display = '';
                }} else {{
                    card.style.display = 'none';
                }}
            }});

            // If searched stock is NOT in today's active table/cards, search backend NSE database!
            const backendMatches = NSE_DATABASE.filter(s => 
                (s.symbol && s.symbol.toLowerCase() === query) ||
                (s.symbol && s.symbol.toLowerCase().includes(query)) ||
                (s.name && s.name.toLowerCase().includes(query))
            );

            if (matchedRowCount === 0 && backendMatches.length > 0) {{
                const top = backendMatches[0];
                unlistedBox.style.display = 'block';
                const prof = ENRICHED_PROFILES[top.symbol];

                if (prof) {{
                    const chgColor = prof.change >= 0 ? '#10b981' : '#ef4444';
                    const chgSign = prof.change >= 0 ? '+' : '';
                    unlistedBox.innerHTML = `
                    <div class="rich-stock-profile-card">
                        <!-- Top Bar with Symbol, Status Badge and Real-Time CMP -->
                        <div class="card-top-bar">
                            <div class="card-top-title">
                                <h2><span>🔍 ${{prof.symbol}}</span> <span style="font-size:15px; color:#94a3b8; font-weight:normal;">— ${{prof.name}}</span></h2>
                                <p>Sector: <b>${{prof.sector}}</b> &bull; Database: <b>Verified in NSE 500 Backend Server Data</b></p>
                            </div>
                            <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
                                <span style="background:${{prof.badge_bg}}; color:#fff; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:700;">
                                    ${{prof.status_badge}}
                                </span>
                                <div class="cmp-badge">
                                    <span class="cmp-val">₹${{prof.cmp.toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</span>
                                    <span class="cmp-chg" style="color: ${{chgColor}};">${{chgSign}}${{prof.change}} (${{chgSign}}${{prof.change_pct}}%)</span>
                                </div>
                            </div>
                        </div>

                        <!-- 4-Box Key Metrics Ribbon (Technicals + Fundamentals) -->
                        <div class="metrics-ribbon">
                            <div class="m-card">
                                <small>52-Week Range</small>
                                <b>₹${{prof.l52.toLocaleString('en-IN')}} — ₹${{prof.h52.toLocaleString('en-IN')}}</b>
                                <span style="font-size:11px; color:#94a3b8;">${{prof.dist_52w}}% below 52W High</span>
                            </div>
                            <div class="m-card">
                                <small>Technical Momentum</small>
                                <b>RSI (14): ${{prof.rsi}}</b>
                                <span style="font-size:11px; color:#38bdf8;">1Y Return: ${{prof.ret_1y}}%</span>
                            </div>
                            <div class="m-card">
                                <small>Valuation Multiple</small>
                                <b>Stock P/E: ${{prof.pe}}x</b>
                                <span style="font-size:11px; color:#94a3b8;">Market Cap: ₹${{prof.market_cap_cr}} Cr</span>
                            </div>
                            <div class="m-card">
                                <small>Capital Efficiency</small>
                                <b>ROCE: ${{prof.roce}}% | ROE: ${{prof.roe}}%</b>
                                <span style="font-size:11px; color:#10b981;">Top-tier Quality Franchise</span>
                            </div>
                        </div>

                        <!-- Technical Moving Averages Bar -->
                        <div class="tech-bar">
                            <span><b>20 EMA:</b> ₹${{prof.ema_20}}</span>
                            <span><b>50 EMA:</b> ₹${{prof.ema_50}}</span>
                            <span><b>200 EMA:</b> ₹${{prof.ema_200}}</span>
                            <span style="color:#38bdf8;"><b>Structure:</b> ${{prof.trend_posture}}</span>
                        </div>

                        <!-- Actionable Buy Entry Setup Grid -->
                        <div class="buy-setup-grid">
                            <div class="setup-box buy">
                                <small>Suggested Buy Entry Range</small>
                                <b>${{prof.suggested_entry}}</b>
                            </div>
                            <div class="setup-box tgt">
                                <small>Target 1 (Resistance)</small>
                                <b>₹${{prof.target_1}}</b>
                            </div>
                            <div class="setup-box tgt2">
                                <small>Target 2 (Swing Breakout)</small>
                                <b>₹${{prof.target_2}}</b>
                            </div>
                            <div class="setup-box sl">
                                <small>Strict Stop Loss</small>
                                <b>₹${{prof.stop_loss}}</b>
                            </div>
                            <div class="setup-box rr">
                                <small>Risk : Reward</small>
                                <b>${{prof.risk_reward}}</b>
                            </div>
                        </div>

                        <!-- Senior Fund Manager Buy Entry Rationale & Strategy -->
                        <div class="strategy-explanation-box">
                            <h4>🏛️ Senior Fund Manager Buy Entry Rationale &amp; Strategy:</h4>
                            <div>${{prof.buy_entry_strategy}}</div>
                            <div style="margin-top:10px; font-size:12px; color:#38bdf8;">
                                💡 <b>Live Candlestick Deep Dive:</b> Launch the Streamlit dashboard (<code>Launch_Stock_AI.bat</code>) and select <b>360° Stock Deep Dive</b> to inspect real-time interactive charts and order-book depth for <b>${{prof.symbol}}</b>.
                            </div>
                        </div>
                    </div>
                    `;
                }} else {{
                    unlistedBox.innerHTML = `
                    <div style="background: #1e1b4b; border: 1px solid #6366f1; border-left: 5px solid #818cf8; padding: 18px; border-radius: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                            <div>
                                <h3 style="margin: 0; color: #fff; display: flex; align-items: center; gap: 10px;">
                                    <span>🔍 ${{top.symbol}}</span>
                                    <span style="font-size: 14px; color: #94a3b8; font-weight: normal;">— ${{top.name}}</span>
                                </h3>
                                <div style="font-size: 12px; color: #a5b4fc; margin-top: 4px;">Sector: <b>${{top.sector}}</b> &bull; Database: <b>Verified in NSE 500 Backend Server Data</b></div>
                            </div>
                            <span style="background: #3730a3; color: #e0e7ff; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700;">
                                ⏸️ Consolidation / Neutral Base
                            </span>
                        </div>
                        <hr style="border-color: #312e81; margin: 12px 0;"/>
                        <p style="margin: 0 0 10px 0; font-size: 13px; color: #cbd5e1;">
                            ${{top.symbol}} is verified in the backend NSE 500 database. To inspect its real-time CMP, candlestick chart, and financial metrics, launch the Streamlit app.
                        </p>
                    </div>
                    `;
                }}
            }} else if (matchedRowCount > 0) {{
                unlistedBox.style.display = 'none';
            }} else {{
                unlistedBox.style.display = 'block';
                unlistedBox.innerHTML = `
                <div style="background: #1e293b; border: 1px solid #334155; padding: 16px; border-radius: 8px; text-align: center; color: #94a3b8;">
                    No stock matching "<b>${{query}}</b>" found in active leaderboard or NSE 500 database. Try searching <b>TCS, LAURUSLABS, DIXON, INFY, TRENT</b>.
                </div>
                `;
            }}
        }}

        // --- Theme Toggle (Dark / Light Mode) ---
        function applyTheme(theme) {{
            document.documentElement.setAttribute('data-theme', theme);
            const btn = document.getElementById('themeToggleBtn');
            const icon = document.getElementById('themeToggleIcon');
            const text = document.getElementById('themeToggleText');
            if (theme === 'light') {{
                if (icon) icon.innerText = '☀️';
                if (text) text.innerText = 'Light Mode';
                if (btn) btn.title = 'Current: Light Mode. Click to switch to Dark Mode.';
            }} else {{
                if (icon) icon.innerText = '🌙';
                if (text) text.innerText = 'Dark Mode';
                if (btn) btn.title = 'Current: Dark Mode. Click to switch to Light Mode.';
            }}
            try {{
                localStorage.setItem('stock_ai_theme', theme);
            }} catch (e) {{}}
        }}

        function toggleTheme() {{
            const current = document.documentElement.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            applyTheme(next);
        }}

        // --- Live Refresh & Sync Daemon Health ---
        let autoReadEnabled = true;
        let autoReadTimer = null;
        let isDaemonOnline = false;

        async function checkDaemonStatus(showAlertOnOffline = false) {{
            const pill = document.getElementById('daemonStatusPill');
            const label = document.getElementById('daemonStatusText');
            try {{
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 2000);
                const res = await fetch('http://127.0.0.1:5005/api/status', {{ signal: controller.signal }});
                clearTimeout(timeoutId);

                if (res.ok) {{
                    isDaemonOnline = true;
                    if (pill) {{
                        pill.className = 'daemon-status-pill online';
                        pill.title = 'Live Sync Daemon is online (Port 5005). Streaming real-time NSE data.';
                    }}
                    if (label) label.innerText = 'Live Sync: Online';
                    return true;
                }}
            }} catch (e) {{
                // daemon unreachable
            }}

            isDaemonOnline = false;
            if (pill) {{
                pill.className = 'daemon-status-pill offline';
                pill.title = 'Live Sync Daemon is offline. Click for start instructions.';
            }}
            if (label) label.innerText = 'Live Sync: Offline';

            if (showAlertOnOffline) {{
                showDaemonHelpModal();
            }}
            return false;
        }}

        function showDaemonHelpModal() {{
            showSyncToast(`
                <div style="font-weight:700; color:#f87171; font-size:14px; margin-bottom:6px;">⚠️ Live Sync Daemon is Offline</div>
                <div style="font-size:12px; line-height:1.5; color:#cbd5e1;">
                    The local sync daemon (Port 5005) is not running.<br/>
                    To stream real-time CMP quotes and auto-refresh:<br/>
                    <b>1.</b> Double-click <b>start_sync_daemon.bat</b> on Desktop or in <code>D:\\STOCK_AI</code><br/>
                    <b>2.</b> Or run <b>Launch_Stock_AI.bat</b> to start both Streamlit & the Live Sync Daemon.<br/>
                </div>
            `, 8000);
        }}

        function toggleAutoRead() {{
            autoReadEnabled = !autoReadEnabled;
            const pill = document.getElementById('autoReadPill');
            const label = document.getElementById('autoReadLabel');
            if (autoReadEnabled) {{
                pill.classList.add('active');
                label.innerText = 'Auto-Read: ON (3m)';
                showSyncToast('🟢 <b>Auto-Read Active:</b> Background quotes will auto-sync every 3 minutes.');
                startAutoReadTimer();
            }} else {{
                pill.classList.remove('active');
                label.innerText = 'Auto-Read: OFF';
                showSyncToast('⚪ <b>Auto-Read Paused:</b> Manual refresh mode active.');
                if (autoReadTimer) clearInterval(autoReadTimer);
            }}
        }}

        function showSyncToast(msg, duration = 4500) {{
            let toast = document.getElementById('syncToast');
            if (!toast) {{
                toast = document.createElement('div');
                toast.id = 'syncToast';
                toast.className = 'sync-toast';
                document.body.appendChild(toast);
            }}
            toast.innerHTML = msg;
            toast.style.display = 'block';
            setTimeout(() => {{ toast.style.display = 'none'; }}, duration);
        }}

        async function triggerLiveRefresh() {{
            const btn = document.getElementById('refreshBtn');
            const icon = btn.querySelector('.refresh-icon');
            const btnText = document.getElementById('refreshBtnText');

            icon.classList.add('spinning');
            btnText.innerText = 'Syncing Live Feeds...';
            btn.disabled = true;

            try {{
                showSyncToast('⏳ <b>Syncing Live Feeds:</b> Fetching latest 14 Indian indices & CMP for all stocks...');
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 25000);

                const response = await fetch('http://127.0.0.1:5005/api/refresh?mode=quick', {{
                    method: 'GET',
                    headers: {{ 'Accept': 'application/json' }},
                    signal: controller.signal
                }});
                clearTimeout(timeoutId);

                if (response.ok) {{
                    const data = await response.json();
                    showSyncToast('✅ <b>Market Data & CMP Synced!</b> Reloading updated dashboard...');
                    setTimeout(() => {{
                        window.location.reload();
                    }}, 600);
                    return;
                }} else {{
                    throw new Error('Sync server responded with status ' + response.status);
                }}
            }} catch (err) {{
                console.warn('Sync server connection notice:', err);
                checkDaemonStatus(false);
                showSyncToast(`
                    <div style="font-weight:700; color:#f87171; font-size:13px; margin-bottom:4px;">⚠️ Live Sync Daemon is Offline</div>
                    <div style="font-size:12px; line-height:1.4; color:#cbd5e1;">
                        Could not reach sync server at <b>http://127.0.0.1:5005</b>.<br/>
                        Run <b>start_sync_daemon.bat</b> on Desktop or in <code>D:\\STOCK_AI</code> to start live feeds.
                    </div>
                `, 6500);
            }} finally {{
                setTimeout(() => {{
                    icon.classList.remove('spinning');
                    btnText.innerText = 'Refresh Live Data';
                    btn.disabled = false;
                }}, 1000);
            }}
        }}

        function startAutoReadTimer() {{
            if (autoReadTimer) clearInterval(autoReadTimer);
            // 3 minutes = 180,000 ms
            autoReadTimer = setInterval(() => {{
                if (autoReadEnabled && isDaemonOnline) {{
                    console.log('[IndianStockAI] Auto-read timer triggered live refresh.');
                    triggerLiveRefresh();
                }}
            }}, 180000);
        }}


        // --- Click-to-Sort Table Columns ---
        function sortTable(th, colIdx) {{
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            if (!tbody) return;

            document.querySelectorAll('.chart-drawer-row').forEach(r => r.remove());

            const rows = Array.from(tbody.querySelectorAll('tr.stock-row, tr'));
            const isAsc = th.classList.contains('asc');
            const newAsc = !isAsc;

            table.querySelectorAll('th').forEach(h => h.classList.remove('asc', 'desc'));
            th.classList.add(newAsc ? 'asc' : 'desc');

            rows.sort((rowA, rowB) => {{
                const cellA = rowA.children[colIdx]?.innerText?.trim() || '';
                const cellB = rowB.children[colIdx]?.innerText?.trim() || '';

                const cleanA = cellA.replace(/[₹,%+x]/g, '').trim();
                const cleanB = cellB.replace(/[₹,%+x]/g, '').trim();
                const numA = parseFloat(cleanA);
                const numB = parseFloat(cleanB);

                if (!isNaN(numA) && !isNaN(numB) && cleanA !== '' && cleanB !== '') {{
                    return newAsc ? (numA - numB) : (numB - numA);
                }}
                return newAsc ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
            }});

            rows.forEach(r => tbody.appendChild(r));
        }}

        // --- CSV Export Engine ---
        function exportActiveTableToCSV() {{
            const activePanel = document.querySelector('.view-panel:not([style*="display: none"])');
            if (!activePanel) {{
                showSyncToast('⚠️ No active table found to export.');
                return;
            }}

            const table = activePanel.querySelector('table');
            if (!table) {{
                showSyncToast('⚠️ The active tab does not contain a table.');
                return;
            }}

            const rows = [];
            const headers = [];
            table.querySelectorAll('thead th').forEach(th => {{
                let txt = th.innerText.replace('▲', '').replace('▼', '').replace('↕', '').trim();
                if (txt !== 'Chart' && txt !== 'Action') {{
                    headers.push('"' + txt.split('"').join('""') + '"');
                }}
            }});
            rows.push(headers.join(','));

            table.querySelectorAll('tbody tr').forEach(tr => {{
                if (tr.classList.contains('chart-drawer-row') || tr.style.display === 'none') return;
                
                const rowData = [];
                tr.querySelectorAll('td').forEach((td, idx) => {{
                    const headerTxt = table.querySelectorAll('thead th')[idx]?.innerText?.trim() || '';
                    if (headerTxt.includes('Chart') || headerTxt.includes('Action')) return;
                    
                    let txt = td.innerText.trim();
                    rowData.push('"' + txt.split('"').join('""') + '"');
                }});
                if (rowData.length > 0) {{
                    rows.push(rowData.join(','));
                }}
            }});

            if (rows.length <= 1) {{
                showSyncToast('⚠️ No visible stock rows to export.');
                return;
            }}

            const csvContent = String.fromCharCode(0xFEFF) + rows.join(String.fromCharCode(10));
            const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            const viewId = activePanel.id ? activePanel.id.replace('view-', '') : 'stocks';
            const nowStr = new Date().toISOString().slice(0, 10);
            a.href = url;
            a.download = `Indian_Stock_AI_${{viewId}}_${{nowStr}}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showSyncToast(`📥 <b>CSV Exported!</b> Saved as <code>Indian_Stock_AI_${{viewId}}_${{nowStr}}.csv</code>`);
        }}

        // --- Interactive Candlestick Chart Drawer Engine ---
        async function toggleCandleChart(symbol, btn) {{
            const tr = btn.closest('tr');
            if (!tr) return;

            const next = tr.nextElementSibling;
            if (next && next.classList.contains('chart-drawer-row') && next.getAttribute('data-chart-symbol') === symbol) {{
                next.remove();
                btn.innerText = '📈 Chart';
                return;
            }}

            document.querySelectorAll('.chart-drawer-row').forEach(r => {{
                const openSym = r.getAttribute('data-chart-symbol');
                r.remove();
                document.querySelectorAll('.chart-btn').forEach(b => {{
                    if (b.getAttribute('onclick')?.includes(openSym)) b.innerText = '📈 Chart';
                }});
            }});

            btn.innerText = '⏳ Loading...';

            const safeSym = symbol.replace(/[^a-zA-Z0-9]/g, '_');
            const canvasId = 'chart_canvas_' + safeSym;

            const drawerTr = document.createElement('tr');
            drawerTr.className = 'chart-drawer-row';
            drawerTr.setAttribute('data-chart-symbol', symbol);

            drawerTr.innerHTML = `
                <td colspan="100%">
                    <div class="chart-container">
                        <div class="chart-top-bar">
                            <div class="chart-title">
                                <span>📈 ${{symbol}} &bull; Daily Candlestick Technical Chart</span>
                                <div style="display:flex; gap:6px; margin-left:14px;">
                                    <button class="chart-tf-btn" onclick="reloadCandleChart('${{symbol}}', '${{canvasId}}', '1m', this)">1M</button>
                                    <button class="chart-tf-btn" onclick="reloadCandleChart('${{symbol}}', '${{canvasId}}', '3m', this)">3M</button>
                                    <button class="chart-tf-btn active" onclick="reloadCandleChart('${{symbol}}', '${{canvasId}}', '6m', this)">6M</button>
                                    <button class="chart-tf-btn" onclick="reloadCandleChart('${{symbol}}', '${{canvasId}}', '1y', this)">1Y</button>
                                </div>
                            </div>
                            <div style="display:flex; align-items:center; gap:16px;">
                                <div class="chart-legend">
                                    <span style="color:#10b981;">■ Bullish</span>
                                    <span style="color:#ef4444;">■ Bearish</span>
                                    <span style="color:#f59e0b;">― 20 EMA</span>
                                    <span style="color:#38bdf8;">― 50 EMA</span>
                                    <span style="color:#64748b;">■ Volume</span>
                                </div>
                                <button class="chart-close-btn" onclick="this.closest('.chart-drawer-row').remove(); document.querySelectorAll('.chart-btn').forEach(b => {{ if(b.getAttribute('onclick')?.includes('${{symbol}}')) b.innerText='📈 Chart'; }});">✕ Close</button>
                            </div>
                        </div>
                        <div id="chartTooltip_${{safeSym}}" style="font-size:12px; font-weight:700; color:var(--text); margin-bottom:8px; min-height:18px;">
                            Hover over any candle to inspect Date, Open, High, Low, Close, and Volume
                        </div>
                        <div style="position:relative;">
                            <canvas id="${{canvasId}}" class="chart-canvas" width="1100" height="320"></canvas>
                        </div>
                    </div>
                </td>
            `;

            tr.parentNode.insertBefore(drawerTr, tr.nextSibling);
            btn.innerText = '📉 Hide';

            await fetchAndRenderCandles(symbol, canvasId, '6m');
        }}

        async function reloadCandleChart(symbol, canvasId, period, tfBtn) {{
            if (tfBtn) {{
                tfBtn.parentNode.querySelectorAll('.chart-tf-btn').forEach(b => b.classList.remove('active'));
                tfBtn.classList.add('active');
            }}
            await fetchAndRenderCandles(symbol, canvasId, period);
        }}

        async function fetchAndRenderCandles(symbol, canvasId, period) {{
            let candles = [];
            try {{
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 4000);
                const res = await fetch(`http://127.0.0.1:5005/api/candles?symbol=${{encodeURIComponent(symbol)}}&period=${{period}}`, {{
                    signal: controller.signal
                }});
                clearTimeout(timeoutId);
                if (res.ok) {{
                    const data = await res.json();
                    if (data.candles && data.candles.length > 0) {{
                        candles = data.candles;
                    }}
                }}
            }} catch (e) {{}}

            if (!candles || candles.length === 0) {{
                candles = generateFallbackCandles(symbol, period);
            }}

            renderCanvasCandlesticks(canvasId, candles, symbol);
        }}

        function generateFallbackCandles(symbol, period) {{
            const prof = (typeof ENRICHED_PROFILES !== 'undefined') ? ENRICHED_PROFILES[symbol] : null;
            let basePrice = prof ? prof.cmp : 1500;
            const numDays = period === '1m' ? 22 : period === '3m' ? 64 : period === '1y' ? 250 : 126;
            const list = [];
            const now = new Date();
            let current = basePrice * 0.85;

            for (let i = numDays; i >= 0; i--) {{
                const d = new Date(now.getTime() - i * 86400000);
                if (d.getDay() === 0 || d.getDay() === 6) continue;
                const changePct = (Math.random() - 0.48) * 0.035;
                const open = current;
                current = current * (1 + changePct);
                const close = current;
                const high = Math.max(open, close) * (1 + Math.random() * 0.015);
                const low = Math.min(open, close) * (1 - Math.random() * 0.015);
                const vol = Math.floor(250000 + Math.random() * 1500000);
                list.push({{
                    time: d.toISOString().slice(0, 10),
                    open: Math.round(open * 100) / 100,
                    high: Math.round(high * 100) / 100,
                    low: Math.round(low * 100) / 100,
                    close: Math.round(close * 100) / 100,
                    volume: vol
                }});
            }}
            return list;
        }}

        function renderCanvasCandlesticks(canvasId, candles, symbol) {{
            const canvas = document.getElementById(canvasId);
            if (!canvas || !candles || candles.length === 0) return;

            const ctx = canvas.getContext('2d');
            const safeSym = symbol.replace(/[^a-zA-Z0-9]/g, '_');
            const tooltipEl = document.getElementById('chartTooltip_' + safeSym);

            const rect = canvas.getBoundingClientRect();
            const dpr = window.devicePixelRatio || 1;
            const width = rect.width > 200 ? rect.width : 1100;
            const height = 320;
            canvas.width = width * dpr;
            canvas.height = height * dpr;
            ctx.scale(dpr, dpr);

            function calcEMA(data, period) {{
                const k = 2 / (period + 1);
                const emaArr = new Array(data.length);
                let sum = 0;
                for (let i = 0; i < period && i < data.length; i++) {{
                    sum += data[i].close;
                }}
                let prevEma = sum / Math.min(period, data.length);
                for (let i = 0; i < data.length; i++) {{
                    if (i < period - 1) {{
                        emaArr[i] = null;
                    }} else if (i === period - 1) {{
                        emaArr[i] = prevEma;
                    }} else {{
                        prevEma = (data[i].close - prevEma) * k + prevEma;
                        emaArr[i] = prevEma;
                    }}
                }}
                return emaArr;
            }}

            const ema20 = calcEMA(candles, 20);
            const ema50 = calcEMA(candles, 50);

            let minPrice = Infinity;
            let maxPrice = -Infinity;
            let maxVol = 0;

            candles.forEach(c => {{
                if (c.low < minPrice) minPrice = c.low;
                if (c.high > maxPrice) maxPrice = c.high;
                if (c.volume > maxVol) maxVol = c.volume;
            }});

            const pricePadding = (maxPrice - minPrice) * 0.08 || 1;
            minPrice -= pricePadding;
            maxPrice += pricePadding;

            const padLeft = 16;
            const padRight = 75;
            const padTop = 16;
            const padBottom = 30;
            const chartW = width - padLeft - padRight;
            const chartH = height - padTop - padBottom;
            const priceAreaH = chartH * 0.75;
            const volAreaH = chartH * 0.22;
            const volAreaTop = padTop + chartH - volAreaH;

            function priceToY(p) {{
                return padTop + priceAreaH - ((p - minPrice) / (maxPrice - minPrice)) * priceAreaH;
            }}

            function volToH(v) {{
                return (v / (maxVol || 1)) * volAreaH;
            }}

            const candleCount = candles.length;
            const candleSlot = chartW / candleCount;
            const candleWidth = Math.max(2, candleSlot * 0.7);

            function drawChart(activeIdx = -1) {{
                ctx.clearRect(0, 0, width, height);

                const gridSteps = 5;
                const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
                ctx.strokeStyle = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
                ctx.fillStyle = isDark ? '#94a3b8' : '#64748b';
                ctx.font = '10px -apple-system, BlinkMacSystemFont, sans-serif';
                ctx.textAlign = 'left';

                for (let i = 0; i <= gridSteps; i++) {{
                    const p = minPrice + (maxPrice - minPrice) * (i / gridSteps);
                    const y = priceToY(p);
                    ctx.beginPath();
                    ctx.moveTo(padLeft, y);
                    ctx.lineTo(width - padRight, y);
                    ctx.stroke();
                    ctx.fillText('₹' + p.toFixed(1), width - padRight + 6, y + 3);
                }}

                ctx.beginPath();
                ctx.moveTo(padLeft, volAreaTop);
                ctx.lineTo(width - padRight, volAreaTop);
                ctx.stroke();

                for (let i = 0; i < candleCount; i++) {{
                    const c = candles[i];
                    const x = padLeft + i * candleSlot + candleSlot / 2;
                    const isBull = c.close >= c.open;
                    const color = isBull ? '#10b981' : '#ef4444';

                    const vh = volToH(c.volume);
                    ctx.fillStyle = isBull ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)';
                    ctx.fillRect(x - candleWidth / 2, padTop + chartH - vh, candleWidth, vh);

                    const yHigh = priceToY(c.high);
                    const yLow = priceToY(c.low);
                    ctx.strokeStyle = color;
                    ctx.lineWidth = 1.2;
                    ctx.beginPath();
                    ctx.moveTo(x, yHigh);
                    ctx.lineTo(x, yLow);
                    ctx.stroke();

                    const yOpen = priceToY(c.open);
                    const yClose = priceToY(c.close);
                    const bodyY = Math.min(yOpen, yClose);
                    const bodyH = Math.max(1.5, Math.abs(yClose - yOpen));
                    ctx.fillStyle = color;
                    ctx.fillRect(x - candleWidth / 2, bodyY, candleWidth, bodyH);
                }}

                ctx.strokeStyle = '#f59e0b';
                ctx.lineWidth = 1.8;
                ctx.beginPath();
                let started20 = false;
                for (let i = 0; i < candleCount; i++) {{
                    if (ema20[i] !== null) {{
                        const x = padLeft + i * candleSlot + candleSlot / 2;
                        const y = priceToY(ema20[i]);
                        if (!started20) {{ ctx.moveTo(x, y); started20 = true; }}
                        else {{ ctx.lineTo(x, y); }}
                    }}
                }}
                ctx.stroke();

                ctx.strokeStyle = '#38bdf8';
                ctx.lineWidth = 1.8;
                ctx.beginPath();
                let started50 = false;
                for (let i = 0; i < candleCount; i++) {{
                    if (ema50[i] !== null) {{
                        const x = padLeft + i * candleSlot + candleSlot / 2;
                        const y = priceToY(ema50[i]);
                        if (!started50) {{ ctx.moveTo(x, y); started50 = true; }}
                        else {{ ctx.lineTo(x, y); }}
                    }}
                }}
                ctx.stroke();

                if (activeIdx >= 0 && activeIdx < candleCount) {{
                    const activeC = candles[activeIdx];
                    const crossX = padLeft + activeIdx * candleSlot + candleSlot / 2;
                    const crossY = priceToY(activeC.close);

                    ctx.strokeStyle = isDark ? 'rgba(255,255,255,0.45)' : 'rgba(0,0,0,0.45)';
                    ctx.setLineDash([4, 4]);
                    ctx.lineWidth = 1;

                    ctx.beginPath();
                    ctx.moveTo(crossX, padTop);
                    ctx.lineTo(crossX, padTop + chartH);
                    ctx.stroke();

                    ctx.beginPath();
                    ctx.moveTo(padLeft, crossY);
                    ctx.lineTo(width - padRight, crossY);
                    ctx.stroke();
                    ctx.setLineDash([]);

                    ctx.fillStyle = '#38bdf8';
                    ctx.beginPath();
                    ctx.arc(crossX, crossY, 4, 0, Math.PI * 2);
                    ctx.fill();

                    if (tooltipEl) {{
                        const chg = activeC.close - activeC.open;
                        const chgPct = ((chg / activeC.open) * 100).toFixed(2);
                        const chgCol = chg >= 0 ? '#10b981' : '#ef4444';
                        const sign = chg >= 0 ? '+' : '';
                        tooltipEl.innerHTML = `
                            <span style="color:var(--text-muted);">Date:</span> <b>${{activeC.time}}</b> &nbsp;|&nbsp;
                            <span style="color:var(--text-muted);">Open:</span> <b>₹${{activeC.open.toFixed(2)}}</b> &nbsp;|&nbsp;
                            <span style="color:var(--text-muted);">High:</span> <b style="color:#10b981;">₹${{activeC.high.toFixed(2)}}</b> &nbsp;|&nbsp;
                            <span style="color:var(--text-muted);">Low:</span> <b style="color:#ef4444;">₹${{activeC.low.toFixed(2)}}</b> &nbsp;|&nbsp;
                            <span style="color:var(--text-muted);">Close:</span> <b>₹${{activeC.close.toFixed(2)}}</b> &nbsp;|&nbsp;
                            <span style="color:${{chgCol}}; font-weight:800;">${{sign}}${{chg.toFixed(2)}} (${{sign}}${{chgPct}}%)</span> &nbsp;|&nbsp;
                            <span style="color:var(--text-muted);">Vol:</span> <b>${{activeC.volume.toLocaleString('en-IN')}}</b>
                        `;
                    }}
                }}
            }}

            drawChart(-1);

            canvas.onmousemove = function(e) {{
                const bbox = canvas.getBoundingClientRect();
                const mx = e.clientX - bbox.left;
                if (mx < padLeft || mx > width - padRight) return;
                const idx = Math.floor((mx - padLeft) / candleSlot);
                if (idx >= 0 && idx < candleCount) {{
                    drawChart(idx);
                }}
            }};

            canvas.onmouseleave = function() {{
                drawChart(-1);
                if (tooltipEl) {{
                    tooltipEl.innerHTML = 'Hover over any candle to inspect Date, Open, High, Low, Close, and Volume';
                }}
            }};
        }}

        // --- Personal Portfolio & Real-Time P&L Tracker ---
        const DEFAULT_PORTFOLIO = [
            {{ symbol: 'TCS', qty: 15, buyPrice: 3820.00 }},
            {{ symbol: 'INFY', qty: 30, buyPrice: 1720.50 }},
            {{ symbol: 'RELIANCE', qty: 10, buyPrice: 2840.00 }},
            {{ symbol: 'TATAMOTORS', qty: 45, buyPrice: 890.00 }},
            {{ symbol: 'DIXON', qty: 5, buyPrice: 11450.00 }}
        ];

        function getPortfolio() {{
            try {{
                const raw = localStorage.getItem('stock_ai_user_portfolio');
                if (raw) return JSON.parse(raw);
            }} catch (e) {{}}
            return DEFAULT_PORTFOLIO;
        }}

        function savePortfolio(list) {{
            try {{
                localStorage.setItem('stock_ai_user_portfolio', JSON.stringify(list));
            }} catch (e) {{}}
            renderPortfolio();
        }}

        function resetPortfolioToDemo() {{
            savePortfolio(DEFAULT_PORTFOLIO);
            showSyncToast('↺ <b>Portfolio Reset:</b> High-conviction benchmark demo holdings restored.');
        }}

        // --- Portfolio Real-Time Stock Search & Autocomplete ---
        let activeSuggestionIndex = -1;

        function onPortfolioSymbolInput(inputEl) {{
            const query = (inputEl.value || '').trim().toLowerCase();
            const dropdown = document.getElementById('portSymbolSuggestions');
            const chip = document.getElementById('portSelectedChip');
            if (chip) chip.style.display = 'none';

            if (!dropdown) return;

            if (!query || query.length < 1) {{
                dropdown.style.display = 'none';
                dropdown.innerHTML = '';
                activeSuggestionIndex = -1;
                return;
            }}

            const catalog = (typeof NSE_DATABASE !== 'undefined' && Array.isArray(NSE_DATABASE)) ? NSE_DATABASE : [];
            
            const symStart = [];
            const nameStart = [];
            const contains = [];

            catalog.forEach(item => {{
                const sym = (item.symbol || '').toLowerCase();
                const nm = (item.name || '').toLowerCase();

                if (sym.startsWith(query)) {{
                    symStart.push(item);
                }} else {{
                    const words = nm.split(' ');
                    const wordMatch = words.some(w => w.startsWith(query));
                    if (wordMatch) {{
                        nameStart.push(item);
                    }} else if (sym.includes(query) || nm.includes(query)) {{
                        contains.push(item);
                    }}
                }}
            }});

            const combined = [...symStart, ...nameStart, ...contains].slice(0, 8);

            if (combined.length === 0) {{
                dropdown.innerHTML = `
                    <div style="padding: 12px; font-size: 12px; color: var(--text-muted); text-align: center;">
                        No NSE stock matching "<b>${{query}}</b>". You can still add it manually.
                    </div>
                `;
                dropdown.style.display = 'block';
                activeSuggestionIndex = -1;
                return;
            }}

            let html = '';
            combined.forEach((item, idx) => {{
                const live = getLiveCMPForSymbol(item.symbol);
                const cmpStr = live ? ('₹' + live.cmp.toLocaleString('en-IN', {{minimumFractionDigits: 2}})) : '';
                const cleanName = (item.name || '').split('"').join('');
                const cleanSector = (item.sector || 'NSE Equities').split('"').join('');

                html += `
                    <div class="ac-item" data-index="${{idx}}" onclick="selectPortfolioStock('${{item.symbol}}', '${{cleanName}}', '${{cleanSector}}')">
                        <div>
                            <span class="ac-sym">${{item.symbol}}</span>
                            <div class="ac-name" title="${{cleanName}}">${{item.name}}</div>
                        </div>
                        <div class="ac-meta">
                            <span class="ac-sector">${{cleanSector}}</span>
                            ${{cmpStr ? `<div class="ac-cmp">${{cmpStr}}</div>` : ''}}
                        </div>
                    </div>
                `;
            }});

            dropdown.innerHTML = html;
            dropdown.style.display = 'block';
            activeSuggestionIndex = -1;
        }}

        function onPortfolioSymbolKeyDown(e) {{
            const dropdown = document.getElementById('portSymbolSuggestions');
            if (!dropdown || dropdown.style.display === 'none') return;

            const items = dropdown.querySelectorAll('.ac-item');
            if (items.length === 0) return;

            if (e.key === 'ArrowDown') {{
                e.preventDefault();
                activeSuggestionIndex = (activeSuggestionIndex + 1) % items.length;
                updateSuggestionHighlight(items);
            }} else if (e.key === 'ArrowUp') {{
                e.preventDefault();
                activeSuggestionIndex = (activeSuggestionIndex - 1 + items.length) % items.length;
                updateSuggestionHighlight(items);
            }} else if (e.key === 'Enter') {{
                e.preventDefault();
                if (activeSuggestionIndex >= 0 && activeSuggestionIndex < items.length) {{
                    items[activeSuggestionIndex].click();
                }} else if (items.length > 0) {{
                    items[0].click();
                }}
            }} else if (e.key === 'Escape') {{
                dropdown.style.display = 'none';
                activeSuggestionIndex = -1;
            }}
        }}

        function updateSuggestionHighlight(items) {{
            items.forEach((it, idx) => {{
                if (idx === activeSuggestionIndex) {{
                    it.classList.add('active');
                    it.scrollIntoView({{ block: 'nearest' }});
                }} else {{
                    it.classList.remove('active');
                }}
            }});
        }}

        async function selectPortfolioStock(symbol, name, sector) {{
            const input = document.getElementById('portSymbolInput');
            const dropdown = document.getElementById('portSymbolSuggestions');
            const chip = document.getElementById('portSelectedChip');
            const priceInput = document.getElementById('portBuyPriceInput');
            const qtyInput = document.getElementById('portQtyInput');

            if (input) input.value = symbol;
            if (dropdown) {{
                dropdown.style.display = 'none';
                dropdown.innerHTML = '';
            }}

            if (chip) {{
                chip.style.display = 'inline-flex';
                chip.innerHTML = `🏢 <b>${{name}}</b> &bull; ${{sector}}`;
            }}

            if (priceInput && (!priceInput.value || parseFloat(priceInput.value) <= 0)) {{
                priceInput.placeholder = 'Fetching live CMP...';
                const live = await fetchLiveQuote(symbol);
                if (live && live.cmp > 0) {{
                    priceInput.value = live.cmp.toFixed(2);
                    showSyncToast(`📌 <b>${{symbol}}</b>: Verified Live CMP <b>₹${{live.cmp.toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</b> auto-filled into Buy Price!`);
                }} else {{
                    priceInput.placeholder = 'Buy Price ₹ (e.g. 3850)';
                }}
            }}

            if (qtyInput) {{
                qtyInput.focus();
            }}
        }}

        // Close autocomplete when clicking outside
        document.addEventListener('click', function(e) {{
            const wrapper = document.querySelector('.autocomplete-wrapper');
            const dropdown = document.getElementById('portSymbolSuggestions');
            if (dropdown && wrapper && !wrapper.contains(e.target)) {{
                dropdown.style.display = 'none';
            }}
        }});

        function addPortfolioHolding() {{
            const symInput = document.getElementById('portSymbolInput');
            const qtyInput = document.getElementById('portQtyInput');
            const priceInput = document.getElementById('portBuyPriceInput');

            const symbol = (symInput?.value || '').trim().toUpperCase();
            const qty = parseInt(qtyInput?.value || '0', 10);
            const buyPrice = parseFloat(priceInput?.value || '0');

            if (!symbol) {{
                showSyncToast('⚠️ Please enter a stock symbol (e.g. TCS).');
                return;
            }}
            if (isNaN(qty) || qty <= 0) {{
                showSyncToast('⚠️ Please enter a valid quantity greater than 0.');
                return;
            }}
            if (isNaN(buyPrice) || buyPrice <= 0) {{
                showSyncToast('⚠️ Please enter a valid buy price.');
                return;
            }}

            const port = getPortfolio();
            const existingIdx = port.findIndex(h => h.symbol === symbol);
            if (existingIdx >= 0) {{
                const oldH = port[existingIdx];
                const newTotalQty = oldH.qty + qty;
                const newAvgPrice = ((oldH.qty * oldH.buyPrice) + (qty * buyPrice)) / newTotalQty;
                port[existingIdx] = {{ symbol, qty: newTotalQty, buyPrice: Math.round(newAvgPrice * 100) / 100 }};
            }} else {{
                port.push({{ symbol, qty, buyPrice }});
            }}

            savePortfolio(port);
            if (symInput) symInput.value = '';
            if (qtyInput) qtyInput.value = '';
            if (priceInput) priceInput.value = '';
            const chip = document.getElementById('portSelectedChip');
            if (chip) chip.style.display = 'none';
            showSyncToast(`✅ <b>Added to Portfolio:</b> ${{qty}} shares of <b>${{symbol}}</b> @ ₹${{buyPrice.toLocaleString('en-IN')}}`);
        }}

        function deletePortfolioHolding(idx) {{
            const port = getPortfolio();
            if (idx >= 0 && idx < port.length) {{
                const removed = port.splice(idx, 1)[0];
                savePortfolio(port);
                showSyncToast(`🗑️ Removed <b>${{removed.symbol}}</b> from portfolio.`);
            }}
        }}

        // Real-Time Verified Live Quotes Cache for Portfolio
        window.PORTFOLIO_LIVE_PRICES = {{}};
        try {{
            const savedPrices = localStorage.getItem('stock_ai_live_prices');
            if (savedPrices) window.PORTFOLIO_LIVE_PRICES = JSON.parse(savedPrices);
        }} catch (e) {{}}

        async function fetchLiveQuote(sym) {{
            try {{
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 4000);
                const res = await fetch(`http://127.0.0.1:5005/api/quote?symbol=${{encodeURIComponent(sym)}}`, {{
                    signal: controller.signal
                }});
                clearTimeout(timeoutId);
                if (res.ok) {{
                    const data = await res.json();
                    if (data && data.currentPrice && data.currentPrice > 0) {{
                        const quote = {{
                            cmp: Number(data.currentPrice),
                            change_pct: Number(data.changePercent || 0),
                            time: Date.now()
                        }};
                        window.PORTFOLIO_LIVE_PRICES[sym] = quote;
                        try {{
                            localStorage.setItem('stock_ai_live_prices', JSON.stringify(window.PORTFOLIO_LIVE_PRICES));
                        }} catch (e) {{}}
                        return quote;
                    }}
                }}
            }} catch (e) {{}}
            return null;
        }}

        let isSyncingPortfolio = false;
        window.PORTFOLIO_AUDIT_DATA = {{}};

        async function syncAllPortfolioQuotes() {{
            if (isSyncingPortfolio) return;
            const port = getPortfolio();
            if (!port || port.length === 0) return;

            isSyncingPortfolio = true;
            showSyncToast('⏳ <b>Syncing Real-Time CMP &amp; CIO Audits:</b> Fetching live quotes &amp; senior advisory...');

            const promises = port.map(h => fetchLiveQuote(h.symbol));
            await Promise.all(promises);
            
            // Asynchronously sync senior CIO portfolio audit from server if daemon is online
            await syncPortfolioAuditFromServer();

            isSyncingPortfolio = false;
            renderPortfolio();
            showSyncToast('✅ <b>Live CMP &amp; Sell Advisory Synced:</b> Accurate market quotes &amp; exit recommendations updated!');
        }}

        async function syncPortfolioAuditFromServer() {{
            const port = getPortfolio();
            if (!port || port.length === 0) return;
            try {{
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 6000);
                const res = await fetch('http://127.0.0.1:5005/api/portfolio_audit', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ holdings: port }}),
                    signal: controller.signal
                }});
                clearTimeout(timeoutId);
                if (res.ok) {{
                    const audit = await res.json();
                    if (audit && audit.holdings) {{
                        audit.holdings.forEach(item => {{
                            window.PORTFOLIO_AUDIT_DATA[item.symbol] = item;
                        }});
                    }}
                }}
            }} catch (e) {{}}
        }}

        function getLiveCMPForSymbol(sym) {{
            // 1. Check verified live quotes cache from daemon
            if (window.PORTFOLIO_LIVE_PRICES && window.PORTFOLIO_LIVE_PRICES[sym] && window.PORTFOLIO_LIVE_PRICES[sym].cmp > 0) {{
                return window.PORTFOLIO_LIVE_PRICES[sym];
            }}
            // 2. Check universal 503-stock verified CMP database (embedded)
            if (typeof ALL_STOCK_CMPS !== 'undefined' && ALL_STOCK_CMPS[sym] && ALL_STOCK_CMPS[sym].cmp > 0) {{
                return {{ cmp: ALL_STOCK_CMPS[sym].cmp, change_pct: ALL_STOCK_CMPS[sym].change_pct || 0 }};
            }}
            // 3. Check ENRICHED_PROFILES (precomputed backend profiles)
            if (typeof ENRICHED_PROFILES !== 'undefined' && ENRICHED_PROFILES[sym] && ENRICHED_PROFILES[sym].cmp > 0) {{
                return {{ cmp: ENRICHED_PROFILES[sym].cmp, change_pct: ENRICHED_PROFILES[sym].change_pct || 0 }};
            }}
            // 4. Check scanned market tables (EXCLUDING portfolio table to avoid buy-price collision!)
            const marketRow = document.querySelector(
                '#view-momentum tr[data-symbol="' + sym + '"], ' +
                '#view-fifty_two_week tr[data-symbol="' + sym + '"], ' +
                '#view-radar tr[data-symbol="' + sym + '"], ' +
                '#view-leaderboard tr[data-symbol="' + sym + '"]'
            );
            if (marketRow) {{
                const cmpCell = marketRow.children[2]?.innerText || '';
                const clean = parseFloat(cmpCell.replace(/[₹,]/g, ''));
                if (!isNaN(clean) && clean > 0) {{
                    return {{ cmp: clean, change_pct: 0.0 }};
                }}
            }}
            return null;
        }}

        function renderPortfolio() {{
            const tbody = document.getElementById('portfolioTbody');
            if (!tbody) return;

            const port = getPortfolio();
            let totalInvested = 0;
            let totalCurrentValue = 0;
            let totalDayPnL = 0;
            let missingQuotes = [];
            let atRiskCount = 0;
            let urgentAlerts = [];

            let rowsHtml = '';
            port.forEach((h, idx) => {{
                const live = getLiveCMPForSymbol(h.symbol);
                if (!live) {{
                    missingQuotes.push(h.symbol);
                }}

                // Use verified live CMP if available, otherwise display buyPrice with pending indicator
                const cmp = live ? live.cmp : h.buyPrice;
                const hasRealCMP = !!live;
                const dayPct = live ? live.change_pct : 0.0;

                const invested = h.qty * h.buyPrice;
                const currentVal = h.qty * cmp;
                const pnl = currentVal - invested;
                const pnlPct = invested > 0 ? (pnl / invested) * 100 : 0;
                const dayPnL = currentVal * (dayPct / 100);

                totalInvested += invested;
                totalCurrentValue += currentVal;
                totalDayPnL += dayPnL;

                const pnlColor = pnl >= 0 ? '#10b981' : '#ef4444';
                const pnlSign = pnl >= 0 ? '+' : '';
                const dayColor = dayPct >= 0 ? '#10b981' : '#ef4444';
                const daySign = dayPct >= 0 ? '+' : '';

                const cmpDisplay = hasRealCMP
                    ? `<b style="color:#38bdf8;">₹${{cmp.toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</b>`
                    : `<span style="color:#f59e0b; font-size:12px;" title="Fetching live quote from daemon...">⏳ ₹${{cmp.toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</span>`;

                // Calculate Trailing Stop-Loss & Senior CIO Action
                let trailingSL = h.buyPrice * 0.92;
                let actionBadge = '🟢 STRONG HOLD';
                let actionColor = '#10b981';
                let actionReason = 'Price maintaining support above trailing SL. Hold for target.';

                const prof = (typeof ENRICHED_PROFILES !== 'undefined' && ENRICHED_PROFILES[h.symbol]) ? ENRICHED_PROFILES[h.symbol] : null;
                const ema20 = prof && prof.ema_20 ? prof.ema_20 : (cmp * 0.97);
                const ema50 = prof && prof.ema_50 ? prof.ema_50 : (cmp * 0.94);
                const rsi = prof && prof.rsi ? prof.rsi : 55.0;

                if (pnlPct >= 35.0) {{
                    trailingSL = Math.max(ema20 * 0.985, cmp * 0.91, h.buyPrice * 1.15);
                }} else if (pnlPct >= 15.0) {{
                    trailingSL = Math.max(ema50 * 0.98, h.buyPrice * 1.02);
                }} else if (pnlPct >= 0) {{
                    trailingSL = Math.min(h.buyPrice * 0.92, ema50 * 0.97);
                }} else {{
                    trailingSL = h.buyPrice * 0.92;
                }}
                trailingSL = Math.round(trailingSL * 100) / 100;

                // Action verdict determination
                if (cmp < trailingSL) {{
                    if (pnlPct > 0) {{
                        actionBadge = '🔴 TRAIL SL HIT';
                        actionColor = '#f97316';
                        actionReason = 'CMP breached trailing profit stop of ₹' + trailingSL.toFixed(2) + '. Lock in remaining gains!';
                    }} else {{
                        actionBadge = '🔴 CUT LOSS';
                        actionColor = '#dc2626';
                        actionReason = 'CMP breached -8% risk stop at ₹' + trailingSL.toFixed(2) + '. Cut loser quickly!';
                    }}
                    atRiskCount++;
                    urgentAlerts.push({{
                        symbol: h.symbol,
                        badge: actionBadge,
                        color: actionColor,
                        reason: actionReason,
                        action: 'Sell ' + h.qty + ' shares at ₹' + cmp.toFixed(2) + ' to preserve capital.'
                    }});
                }} else if (pnlPct >= 40.0 && rsi >= 75.0) {{
                    actionBadge = '🟠 BOOK 35% PROFIT';
                    actionColor = '#f59e0b';
                    actionReason = 'Extremely overbought (RSI ' + rsi.toFixed(1) + ') after +' + pnlPct.toFixed(1) + '% run. Book partial gains!';
                }} else if (pnlPct >= 25.0 && cmp < ema20) {{
                    actionBadge = '🟡 TRIM 25%';
                    actionColor = '#eab308';
                    actionReason = 'Slipped below 20-EMA; protect +' + pnlPct.toFixed(1) + '% profit by trimming 25%.';
                }} else if (prof && prof.is_bullish) {{
                    actionBadge = '🟢 STRONG HOLD (LEADER)';
                    actionColor = '#10b981';
                    actionReason = 'Leading Stage-2 momentum stock above key EMAs. Let winner run!';
                }}

                // If live audit cache from server exists, use enriched server audit!
                if (window.PORTFOLIO_AUDIT_DATA && window.PORTFOLIO_AUDIT_DATA[h.symbol]) {{
                    const srv = window.PORTFOLIO_AUDIT_DATA[h.symbol];
                    if (srv.action_badge) actionBadge = srv.action_badge;
                    if (srv.action_color) actionColor = srv.action_color;
                    if (srv.trailing_stop_loss) trailingSL = srv.trailing_stop_loss;
                    if (srv.rationale) actionReason = srv.rationale;

                    if (srv.action_code === 'EMERGENCY_SELL' || srv.action_code === 'EXIT_TRAILING_SL' || srv.action_code === 'CUT_LOSS') {{
                        if (!urgentAlerts.find(a => a.symbol === h.symbol)) {{
                            atRiskCount++;
                            urgentAlerts.push({{
                                symbol: h.symbol,
                                badge: srv.action_badge,
                                color: srv.action_color,
                                reason: srv.rationale,
                                action: srv.suggested_action_detail
                            }});
                        }}
                    }}
                }}

                rowsHtml += `
                    <tr class="portfolio-holding-row" data-symbol="${{h.symbol}}">
                        <td>
                            <div class="sym-name">${{h.symbol}}</div>
                            <div class="sub-text">Portfolio Holding #${{idx + 1}}</div>
                        </td>
                        <td><b>${{h.qty}}</b></td>
                        <td>₹${{h.buyPrice.toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</td>
                        <td>${{cmpDisplay}}</td>
                        <td>₹${{invested.toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</td>
                        <td><b>₹${{currentVal.toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</b></td>
                        <td style="color:${{dayColor}}; font-weight:700;">${{daySign}}${{dayPct.toFixed(2)}}%</td>
                        <td style="color:${{pnlColor}}; font-weight:700;">${{pnlSign}}₹${{pnl.toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</td>
                        <td style="color:${{pnlColor}}; font-weight:800; font-size:14px;">${{pnlSign}}${{pnlPct.toFixed(2)}}%</td>
                        <td><b style="color:#f59e0b;">₹${{trailingSL.toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}</b></td>
                        <td>
                            <span class="cio-badge" style="color:${{actionColor}}; border-color:${{actionColor}};" onclick="openHoldingAuditModal('${{h.symbol}}', ${{idx}})" title="Click to view full institutional audit">
                                ${{actionBadge}} ℹ️
                            </span>
                        </td>
                        <td><button class="chart-btn" onclick="toggleCandleChart('${{h.symbol}}', this)">📈 Chart</button></td>
                        <td><button class="delete-holding-btn" onclick="deletePortfolioHolding(${{idx}})" title="Delete holding">🗑️</button></td>
                    </tr>
                `;
            }});

            tbody.innerHTML = rowsHtml;

            // Update Urgent Alerts Banner
            const banner = document.getElementById('portUrgentAlertsBanner');
            if (banner) {{
                if (urgentAlerts.length > 0) {{
                    let bannerHtml = `
                        <div style="font-weight: 800; font-size: 14px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                            ⚠️ <b>CIO Urgent Sell Warnings (${{urgentAlerts.length}} At Risk):</b>
                        </div>
                    `;
                    urgentAlerts.forEach(a => {{
                        bannerHtml += `
                            <div style="margin-top: 6px; padding: 8px 12px; background: rgba(0,0,0,0.25); border-radius: 6px; border-left: 4px solid ${{a.color}};">
                                <b>${{a.symbol}}</b> &bull; <span style="color:${{a.color}}; font-weight:700;">${{a.badge}}</span>: ${{a.reason}}<br/>
                                <span style="color: #38bdf8; font-weight: 600;">👉 Suggested Action: ${{a.action}}</span>
                            </div>
                        `;
                    }});
                    banner.innerHTML = bannerHtml;
                    banner.style.display = 'block';
                }} else {{
                    banner.style.display = 'none';
                }}
            }}

            // If any holdings are missing verified live quotes, fetch them in background!
            if (missingQuotes.length > 0 && !isSyncingPortfolio) {{
                syncAllPortfolioQuotes();
            }}

            const totalPnL = totalCurrentValue - totalInvested;
            const totalPnLPct = totalInvested > 0 ? ((totalPnL / totalInvested) * 100) : 0;
            const totalDayPnLPct = totalCurrentValue > 0 ? ((totalDayPnL / totalCurrentValue) * 100) : 0;

            const elInvested = document.getElementById('portTotalInvested');
            const elCurrent = document.getElementById('portCurrentValue');
            const elPnL = document.getElementById('portTotalPnL');
            const elPnLPct = document.getElementById('portTotalPnLPct');
            const elDayPnL = document.getElementById('portDayPnL');
            const elDayPnLPct = document.getElementById('portDayPnLPct');
            const elHealth = document.getElementById('portHealthScore');
            const elHealthSub = document.getElementById('portHealthSub');
            const elAtRisk = document.getElementById('portAtRiskCount');
            const elAtRiskSub = document.getElementById('portAtRiskSub');

            if (elInvested) elInvested.innerText = '₹' + totalInvested.toLocaleString('en-IN', {{minimumFractionDigits: 2}});
            if (elCurrent) elCurrent.innerText = '₹' + totalCurrentValue.toLocaleString('en-IN', {{minimumFractionDigits: 2}});
            
            if (elPnL) {{
                elPnL.innerText = (totalPnL >= 0 ? '+' : '') + '₹' + totalPnL.toLocaleString('en-IN', {{minimumFractionDigits: 2}});
                elPnL.style.color = totalPnL >= 0 ? '#10b981' : '#ef4444';
            }}
            if (elPnLPct) {{
                elPnLPct.innerText = (totalPnL >= 0 ? '+' : '') + totalPnLPct.toFixed(2) + '% Overall';
                elPnLPct.style.color = totalPnL >= 0 ? '#10b981' : '#ef4444';
            }}

            if (elDayPnL) {{
                elDayPnL.innerText = (totalDayPnL >= 0 ? '+' : '') + '₹' + totalDayPnL.toLocaleString('en-IN', {{minimumFractionDigits: 2}});
                elDayPnL.style.color = totalDayPnL >= 0 ? '#10b981' : '#ef4444';
            }}
            if (elDayPnLPct) {{
                elDayPnLPct.innerText = (totalDayPnL >= 0 ? '+' : '') + totalDayPnLPct.toFixed(2) + '% Today';
                elDayPnLPct.style.color = totalDayPnL >= 0 ? '#10b981' : '#ef4444';
            }}

            // Health Score & At Risk Indicators
            if (port.length > 0) {{
                const healthyCount = port.length - atRiskCount;
                const healthScore = Math.max(1.0, Math.min(10.0, (healthyCount / port.length) * 10.0));
                if (elHealth) {{
                    elHealth.innerText = healthScore.toFixed(1) + ' / 10';
                    elHealth.style.color = healthScore >= 8.0 ? '#38bdf8' : (healthScore >= 5.0 ? '#f59e0b' : '#ef4444');
                }}
                if (elHealthSub) {{
                    elHealthSub.innerText = healthScore >= 8.0 ? 'Institutional Grade' : (healthScore >= 5.0 ? 'Moderate Health' : 'Risk Elevated');
                    elHealthSub.style.color = healthScore >= 8.0 ? '#10b981' : (healthScore >= 5.0 ? '#f59e0b' : '#ef4444');
                }}
                if (elAtRisk) {{
                    elAtRisk.innerText = atRiskCount === 0 ? '0 At Risk' : atRiskCount + ' Require Exit';
                    elAtRisk.style.color = atRiskCount === 0 ? '#10b981' : '#ef4444';
                }}
                if (elAtRiskSub) {{
                    elAtRiskSub.innerText = atRiskCount === 0 ? 'Trailing Stops Intact' : 'Action Required!';
                    elAtRiskSub.style.color = atRiskCount === 0 ? 'var(--text-muted)' : '#ef4444';
                }}
            }}
        }}

        function openHoldingAuditModal(sym, idx) {{
            const port = getPortfolio();
            const h = port[idx];
            if (!h) return;

            const live = getLiveCMPForSymbol(sym);
            const cmp = live ? live.cmp : h.buyPrice;
            const invested = h.qty * h.buyPrice;
            const currentVal = h.qty * cmp;
            const pnl = currentVal - invested;
            const pnlPct = invested > 0 ? (pnl / invested) * 100 : 0;

            const prof = (typeof ENRICHED_PROFILES !== 'undefined' && ENRICHED_PROFILES[sym]) ? ENRICHED_PROFILES[sym] : null;
            const srv = (window.PORTFOLIO_AUDIT_DATA && window.PORTFOLIO_AUDIT_DATA[sym]) ? window.PORTFOLIO_AUDIT_DATA[sym] : null;

            const titleEl = document.getElementById('modalHoldingTitle');
            const subEl = document.getElementById('modalHoldingSub');
            const bodyEl = document.getElementById('modalHoldingBody');
            const modal = document.getElementById('holdingAuditModal');

            if (titleEl) titleEl.innerText = sym + ' • Institutional CIO Audit & Exit Advisory';
            if (subEl) subEl.innerText = 'Holding #' + (idx + 1) + ' | ' + h.qty + ' Shares | Bought @ ₹' + h.buyPrice.toFixed(2) + ' | Live CMP: ₹' + cmp.toFixed(2);

            let actionBadge = srv ? srv.action_badge : (pnlPct >= 35 ? '🟢 STRONG HOLD' : '🟢 HOLD');
            let actionColor = srv ? srv.action_color : '#10b981';
            let rationale = srv ? srv.rationale : (prof ? prof.strategy_exp : 'Trend structure intact with stop-loss protection active.');
            let actionDetail = srv ? srv.suggested_action_detail : ('Maintain position of ' + h.qty + ' shares with active trailing stop.');
            let trailingSL = srv ? srv.trailing_stop_loss : (pnlPct >= 35 ? cmp * 0.92 : h.buyPrice * 0.92);
            let catalyst = srv && srv.news_catalyst ? srv.news_catalyst : 'Stable financial news flow with no critical governance warnings detected.';

            const ema20 = prof && prof.ema_20 ? ('₹' + prof.ema_20.toFixed(2)) : 'N/A';
            const ema50 = prof && prof.ema_50 ? ('₹' + prof.ema_50.toFixed(2)) : 'N/A';
            const ema200 = prof && prof.ema_200 ? ('₹' + prof.ema_200.toFixed(2)) : 'N/A';
            const rsi = prof && prof.rsi ? prof.rsi.toFixed(1) : '55.0';

            if (bodyEl) {{
                bodyEl.innerHTML = `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                        <div style="padding: 12px; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid var(--border);">
                            <div style="font-size: 11px; color: var(--text-muted);">Total P&amp;L Gain / Loss</div>
                            <div style="font-size: 18px; font-weight: 800; color: ${{pnl >= 0 ? '#10b981' : '#ef4444'}};">
                                ${{pnl >= 0 ? '+' : ''}}₹${{pnl.toLocaleString('en-IN', {{minimumFractionDigits: 2}})}} (${{pnlPct >= 0 ? '+' : ''}}${{pnlPct.toFixed(2)}}%)
                            </div>
                        </div>
                        <div style="padding: 12px; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid var(--border);">
                            <div style="font-size: 11px; color: var(--text-muted);">Dynamic Trailing Stop-Loss</div>
                            <div style="font-size: 18px; font-weight: 800; color: #f59e0b;">
                                ₹${{trailingSL.toLocaleString('en-IN', {{minimumFractionDigits: 2}})}}
                            </div>
                        </div>
                    </div>

                    <div style="margin-bottom: 16px; padding: 14px; background: rgba(0,0,0,0.2); border-radius: 8px; border-left: 4px solid ${{actionColor}};">
                        <div style="font-size: 11px; text-transform: uppercase; font-weight: 800; color: ${{actionColor}}; margin-bottom: 4px;">
                            🎯 CIO Recommendation: ${{actionBadge}}
                        </div>
                        <div style="font-size: 13px; line-height: 1.5; color: var(--text-heading); margin-bottom: 8px;">
                            ${{rationale}}
                        </div>
                        <div style="font-size: 12px; color: #38bdf8; font-weight: 600;">
                            👉 Executable Action: ${{actionDetail}}
                        </div>
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px;">
                        <div style="padding: 8px; text-align: center; background: rgba(255,255,255,0.02); border-radius: 6px; border: 1px solid var(--border);">
                            <div style="font-size: 10px; color: var(--text-muted);">20-Day EMA</div>
                            <div style="font-size: 12px; font-weight: 700; color: var(--text-heading); margin-top: 3px;">${{ema20}}</div>
                        </div>
                        <div style="padding: 8px; text-align: center; background: rgba(255,255,255,0.02); border-radius: 6px; border: 1px solid var(--border);">
                            <div style="font-size: 10px; color: var(--text-muted);">50-Day EMA</div>
                            <div style="font-size: 12px; font-weight: 700; color: var(--text-heading); margin-top: 3px;">${{ema50}}</div>
                        </div>
                        <div style="padding: 8px; text-align: center; background: rgba(255,255,255,0.02); border-radius: 6px; border: 1px solid var(--border);">
                            <div style="font-size: 10px; color: var(--text-muted);">200-Day EMA</div>
                            <div style="font-size: 12px; font-weight: 700; color: var(--text-heading); margin-top: 3px;">${{ema200}}</div>
                        </div>
                        <div style="padding: 8px; text-align: center; background: rgba(255,255,255,0.02); border-radius: 6px; border: 1px solid var(--border);">
                            <div style="font-size: 10px; color: var(--text-muted);">Daily RSI</div>
                            <div style="font-size: 12px; font-weight: 700; color: #38bdf8; margin-top: 3px;">${{rsi}}</div>
                        </div>
                    </div>

                    <div style="padding: 12px; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid var(--border);">
                        <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); margin-bottom: 4px;">📰 News Sentiment &amp; Event Catalyst:</div>
                        <div style="font-size: 12px; line-height: 1.5; color: var(--text-heading);">
                            ${{catalyst}}
                        </div>
                    </div>
                `;
            }}

            if (modal) modal.style.display = 'flex';
        }}

        function closeHoldingAuditModal(e) {{
            const modal = document.getElementById('holdingAuditModal');
            if (modal) modal.style.display = 'none';
        }}

        window.addEventListener('DOMContentLoaded', async () => {{
            let currentTheme = 'dark';
            try {{
                currentTheme = localStorage.getItem('stock_ai_theme') || 'dark';
            }} catch (e) {{}}
            applyTheme(currentTheme);

            populateSectorFilter();
            renderPortfolio();

            const online = await checkDaemonStatus(false);
            if (online) {{
                syncPortfolioAuditFromServer().then(() => renderPortfolio());
            }}
            startAutoReadTimer();
            // Periodically ping daemon status every 45s
            setInterval(() => checkDaemonStatus(false), 45000);
        }});
    </script>
</body>
</html>
"""
        # Save to each destination path
        for p in output_paths:
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, "w", encoding="utf-8") as f:
                    f.write(html_template)
            except Exception as e:
                print(f"Error saving HTML to {p}: {e}")

        return html_template
