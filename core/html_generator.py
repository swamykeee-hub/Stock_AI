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
        from config import DISCLAIMER, DEVELOPER_ATTRIBUTION
        disclaimer = scan_data.get("disclaimer") or DISCLAIMER
        if DEVELOPER_ATTRIBUTION not in disclaimer:
            disclaimer = f"{DEVELOPER_ATTRIBUTION}. {disclaimer}"

        # Dynamic 52-Week High Breakout Leaders
        fifty_two_week_stocks = scan_data.get("fifty_two_week_high_stocks", [])
        if not fifty_two_week_stocks:
            try:
                from core.fifty_two_week_high_tracker import FiftyTwoWeekHighTracker
                fifty_two_week_stocks = FiftyTwoWeekHighTracker().scan_52_week_highs(force_refresh=False)
            except Exception:
                fifty_two_week_stocks = []

        # Dedicated 5-Factor Value & Promoter Inflection Candidates
        factor_stocks = scan_data.get("factor_screener_stocks", [])
        if not factor_stocks:
            try:
                from core.factor_screener import SmartFactorScreener
                factor_stocks = SmartFactorScreener().scan_factors(force_refresh=False)
            except Exception:
                factor_stocks = []

        # Small & Mid-Cap Hidden Gems (Auto-updated on market movements)
        hidden_gems = scan_data.get("hidden_gems", [])
        if not hidden_gems:
            try:
                from core.hidden_gems_screener import HiddenGemsScreener
                hidden_gems = HiddenGemsScreener().scan_hidden_gems(force_refresh=False, sync_live_prices=False)
            except Exception:
                hidden_gems = []

        # Load backend NSE 500 catalog for universal lookup fallback
        nse_catalog = []
        try:
            from config import DATA_DIR, CACHE_DIR
            catalog_file = DATA_DIR / "nse_stocks.json"
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
            from config import CACHE_DIR
            cmps_file = CACHE_DIR / "all_stock_cmps.json"
            if cmps_file.exists():
                with open(cmps_file, "r", encoding="utf-8") as f:
                    all_stock_cmps = json.load(f)
        except Exception:
            pass
        all_stock_cmps_json = json.dumps(all_stock_cmps)

        # Generate Indices HTML with Animated Sector Backdrops
        from core.index_visuals import get_index_visual_backdrop
        indices_html = ""
        for name, data in indices.items():
            chg = data.get("change", 0.0)
            pct = data.get("percent", 0.0)
            val = data.get("value", 0.0)
            is_pos = chg >= 0
            color = "#10b981" if is_pos else "#ef4444"
            sign = "+" if is_pos else ""
            val_prefix = "" if any(k in name.upper() for k in ["VIX", "AI CATALYST"]) else "₹"
            bg_art, theme_cls = get_index_visual_backdrop(name)
            indices_html += f"""
            <div class="index-card {theme_cls}">
                {bg_art}
                <div class="index-card-content">
                    <div class="index-name">{name}</div>
                    <div class="index-val">{val_prefix}{val:,.2f}</div>
                    <div class="index-chg" style="color: {color};">{sign}{chg} ({sign}{pct:.2f}%)</div>
                </div>
            </div>
            """

        # Macro indicators
        for m_name, m_data in list(macro.items())[:3]:
            chg_pct = m_data.get("change_pct", 0.0)
            price = m_data.get("price", 0.0)
            color = "#10b981" if chg_pct >= 0 else "#ef4444"
            sign = "+" if chg_pct >= 0 else ""
            bg_art, theme_cls = get_index_visual_backdrop(m_name)
            indices_html += f"""
            <div class="index-card {theme_cls}">
                {bg_art}
                <div class="index-card-content">
                    <div class="index-name">{m_name}</div>
                    <div class="index-val">{price:,.2f}</div>
                    <div class="index-chg" style="color: {color};">{sign}{chg_pct:.2f}%</div>
                </div>
            </div>
            """

        # Senior CIO Market Regime Card
        market_regime = scan_data.get("market_regime")
        if market_regime:
            score = market_regime.get("market_score", 75)
            regime_label = market_regime.get("regime_label", "Bull Market")
            short_regime = regime_label.replace("High-Confidence ", "").replace("Moderate ", "")
            lead = ", ".join(s.replace("Nifty ", "") for s in market_regime.get("leading_sectors", [])[:2])
            bg_art, theme_cls = get_index_visual_backdrop("SENIOR CIO MARKET STANCE")
            indices_html += f"""
            <div class="index-card {theme_cls}" style="border: 1px solid #10b981; background: rgba(16, 185, 129, 0.08);" title="{regime_label} | Health: {score}/100 | Leading: {lead}">
                {bg_art}
                <div class="index-card-content">
                    <div class="index-name" style="color: #38bdf8;">🎯 CIO Market Stance</div>
                    <div class="index-val" style="font-size: 14px; color: #10b981;">{short_regime}</div>
                    <div class="index-chg" style="color: var(--text-heading); font-size: 11px;">Health: <b>{score}/100</b> &bull; {lead}</div>
                </div>
            </div>
            """

        # Institutional Smart Money & Derivatives Card (FII/DII + PCR)
        inst_flow = scan_data.get("institutional_flow")
        if not inst_flow:
            try:
                from core.institutional_flow_analyst import InstitutionalFlowAnalyst
                inst_flow = InstitutionalFlowAnalyst().get_institutional_flow(force_refresh=False)
            except Exception:
                inst_flow = {}

        if inst_flow:
            lat = inst_flow.get("fii_dii_latest", {})
            deriv = inst_flow.get("derivatives", {})
            pcr_val = deriv.get("pcr", 1.0)
            pcr_color = "#10b981" if pcr_val > 1.0 else ("#f59e0b" if pcr_val > 0.75 else "#ef4444")
            fii_val = lat.get("fii_cash_net", "0")
            dii_val = lat.get("dii_cash_net", "0")
            max_pain = deriv.get("max_pain_strike", "—")
            bg_art, theme_cls = get_index_visual_backdrop("INSTITUTIONAL FLOW & PCR")
            indices_html += f"""
            <div class="index-card {theme_cls}" style="border: 1px solid #38bdf8; background: rgba(56, 189, 248, 0.08);" title="Nifty PCR: {pcr_val} | Max Pain: {max_pain} | FII: ₹{fii_val} Cr | DII: ₹{dii_val} Cr">
                {bg_art}
                <div class="index-card-content">
                    <div class="index-name" style="color: #a78bfa;">🏛 Inst. Flow &amp; PCR</div>
                    <div class="index-val" style="font-size: 14px; color: {pcr_color};">PCR: {pcr_val} &bull; MP: {max_pain}</div>
                    <div class="index-chg" style="color: var(--text-heading); font-size: 11px;">FII: <b>{fii_val}</b> &bull; DII: <b>{dii_val}</b></div>
                </div>
            </div>
            """

        # Generate Radar Score Map for quick lookup
        radar_score_map = {r['symbol']: float(r.get('cio_conviction', 8.5)) for r in monitored_radar}

        # Generate Momentum Rows
        momentum_rows = ""
        for s in momentum_stocks:
            sym = s.get('symbol', '')
            if sym in radar_score_map:
                cio_score = radar_score_map[sym]
            else:
                ret1y = float(s.get('ret_1y', 0))
                cio_score = 8.5 if ret1y > 45 else (8.0 if ret1y > 15 else 7.5)
            score_color = "#10b981" if cio_score >= 9.0 else ("#38bdf8" if cio_score >= 8.0 else "#f59e0b")
            score_bg = "rgba(16, 185, 129, 0.15)" if cio_score >= 9.0 else ("rgba(56, 189, 248, 0.15)" if cio_score >= 8.0 else "rgba(245, 158, 11, 0.15)")

            momentum_rows += f"""
            <tr class="stock-row" data-symbol="{s['symbol']}" data-name="{s['name']}" data-sector="{s['sector']}">
                <td>
                    <div class="sym-name">{s['symbol']}</div>
                    <div class="sub-text">{s['name']}</div>
                </td>
                <td><span class="sector-pill">{s['sector']}</span></td>
                <td>
                    <span style="display:inline-flex; align-items:center; gap:4px; background: {score_bg}; color: {score_color}; border: 1px solid {score_color}55; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 12px;">
                        ⭐ {cio_score:.1f}
                    </span>
                </td>
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
            cio_score = float(r.get("cio_conviction", 9.0))
            score_color = "#10b981" if cio_score >= 9.0 else "#38bdf8"
            score_bg = "rgba(16, 185, 129, 0.15)" if cio_score >= 9.0 else "rgba(56, 189, 248, 0.15)"
            conv_src = r.get("conviction_source", "")
            src_label = f'<div style="font-size: 10px; color: #94a3b8; margin-top: 3px;">{conv_src}</div>' if conv_src else ""
            radar_rows += f"""
            <tr class="stock-row" data-symbol="{r['symbol']}" data-name="{r['name']}" data-sector="{r['sector']}">
                <td>
                    <div class="sym-name">{r['symbol']}</div>
                    <div class="sub-text">{r['name']}</div>
                </td>
                <td><span class="status-pill">{r['setup_type']}</span></td>
                <td><span style="display:inline-flex; align-items:center; gap:5px; background: {score_bg}; color: {score_color}; border: 1px solid {score_color}55; padding: 4px 8px; border-radius: 6px; font-weight: 800; font-size: 13px;">⭐ {cio_score:.1f} / 10</span>{src_label}</td>
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
            nav_val = f.get("nav")
            nav_display = f"₹{float(nav_val):,.2f}" if nav_val else "N/A"
            nav_date = f.get("nav_date", "Baseline")
            nav_badge = "🟢 AMFI Live" if f.get("is_live_nav") else "Baseline Ref"
            r1 = float(f.get("return_1y", 0.0))
            r3 = float(f.get("return_3y_cagr", 0.0))
            r5 = float(f.get("return_5y_cagr", 0.0))
            c1 = "#10b981" if r1 >= 0 else "#f87171"
            c3 = "#34d399" if r3 >= 0 else "#f87171"
            c5 = "#38bdf8" if r5 >= 0 else "#f87171"
            mf_rows += f"""
            <tr>
                <td>
                    <b>{f['name']}</b>
                    <div class="sub-text">{f['fund_house']} &bull; Manager: {f['fund_manager']}</div>
                </td>
                <td><span class="sector-pill">{f['category']}</span></td>
                <td>
                    <b style="color: #f8fafc;">{nav_display}</b>
                    <div class="sub-text" style="font-size: 11px;">{nav_badge} ({nav_date})</div>
                </td>
                <td style="color: {c1}; font-weight: 700;">{r1:+.1f}%</td>
                <td style="color: {c3}; font-weight: 800;">{r3:+.1f}%</td>
                <td style="color: {c5}; font-weight: 700;">{r5:+.1f}%</td>
                <td><b>{f['sharpe_ratio']}</b></td>
                <td>₹{f['aum_cr']:,.0f} Cr</td>
                <td style="font-size: 12px; color: #cbd5e1; max-width: 320px;">{f['cio_rationale'][:130]}...</td>
            </tr>
            """

        # Generate Bullish Picks Table Rows (Whole-Market 509-Stock Multibagger & Inflection Scanner)
        picks_rows = ""
        for p in picks:
            score = float(p.get("conviction_score", 0.0))
            badge_color = "#059669" if score >= 8.0 else ("#2563eb" if score >= 7.0 else "#4f46e5")
            arch_short = p.get("archetype_short", "Stage-2 Breakout")
            arch_bg = "#065f46" if "Inflection" in arch_short else ("#1e3a8a" if "Compounder" in arch_short else "#4c1d95")
            mcap_tier = p.get("mcap_tier", "Mid/Large Cap")
            roce_val = p.get("roce_pct", "—")
            de_val = p.get("debt_to_equity")
            de_str = f"D/E: {de_val:.2f}x" if isinstance(de_val, (int, float)) else "D/E: —"
            opm_bps = p.get("opm_expansion_bps")
            pat_yoy = p.get("qtr_pat_yoy_pct")
            fii_dii = p.get("inst_4q_delta_pct", 0.0)

            inf_parts = []
            if pat_yoy is not None:
                inf_parts.append(f"PAT: <b style='color:{'#34d399' if pat_yoy >= 0 else '#f87171'};'>{pat_yoy:+.1f}%</b>")
            if opm_bps is not None:
                inf_parts.append(f"OPM: <b style='color:{'#38bdf8' if opm_bps >= 0 else '#f87171'};'>{opm_bps:+.0f}bps</b>")
            if fii_dii:
                inf_parts.append(f"Inst: <b>{fii_dii:+.1f}%</b>")
            inf_html = " &bull; ".join(inf_parts) if inf_parts else f"1Y: {p.get('ret_1y', 0):+.1f}%"

            picks_rows += f"""
            <tr class="stock-row" data-symbol="{p['symbol']}" data-name="{p['name']}" data-sector="{p['sector']}">
                <td>
                    <div class="sym-name">{p['symbol']}</div>
                    <div class="sub-text">{p['name']} &bull; <span style="color:#38bdf8;">{mcap_tier}</span></div>
                </td>
                <td><span class="sector-pill">{p['sector']}</span></td>
                <td><span class="badge" style="background: {arch_bg}; font-size: 11px;">{arch_short}</span></td>
                <td><b>₹{p['cmp']:,.2f}</b></td>
                <td><span style="display:inline-flex; align-items:center; gap:4px; background: {badge_color}22; color: #34d399; border: 1px solid {badge_color}; padding: 3px 8px; border-radius: 6px; font-weight: 800; font-size: 13px;">⭐ {score:.1f} / 10</span></td>
                <td><b>{roce_val}%</b><div class="sub-text">{de_str}</div></td>
                <td style="font-size: 12px;">{inf_html}</td>
                <td style="color: #10b981; font-weight: 600;">₹{p['target_1']:,.2f}</td>
                <td style="color: #34d399; font-weight: 700;">₹{p['target_2']:,.2f}</td>
                <td style="color: #f87171; font-weight: 600;">₹{p['stop_loss']:,.2f}</td>
                <td><button class="chart-btn" onclick="toggleCandleChart('{p['symbol']}', this)">📈 Chart</button></td>
            </tr>
            """

        # Generate Detailed 360° Stock Cards
        cards_html = ""
        for p in picks:
            signals_li = "".join([f"<li>✅ {s}</li>" for s in p.get("bullish_signals", []) if s])
            strengths_li = "".join([f"<li>⭐ {s}</li>" for s in p.get("fundamental_strengths", []) if s])
            score = float(p.get("conviction_score", 0.0))
            badge_color = "#059669" if score >= 8.0 else "#2563eb"
            arch_label = p.get("archetype", "Stage-2 Breakout")
            roce_val = p.get("roce_pct", "—")
            de_val = p.get("debt_to_equity")
            de_str = f"{de_val:.2f}x" if isinstance(de_val, (int, float)) else "N/A"
            opm_bps = p.get("opm_expansion_bps")
            opm_str = f"{opm_bps:+.0f} bps" if opm_bps is not None else "—"
            pat_yoy = p.get("qtr_pat_yoy_pct")
            pat_str = f"{pat_yoy:+.1f}%" if pat_yoy is not None else "—"

            cards_html += f"""
            <div class="stock-card" data-symbol="{p['symbol']}" data-name="{p['name']}" data-sector="{p['sector']}">
                <div class="card-header">
                    <div>
                        <span class="card-symbol">{p['symbol']}</span>
                        <span class="card-company">{p['name']} &bull; {p.get('mcap_tier', 'NSE')}</span>
                    </div>
                    <span class="badge" style="background: {badge_color};">{arch_label} &bull; ⭐ {score:.1f}/10</span>
                </div>
                <div class="card-meta">
                    <span><b>CMP:</b> ₹{p['cmp']:,.2f}</span>
                    <span><b>Sector:</b> {p['sector']}</span>
                    <span><b>ROCE:</b> {roce_val}%</span>
                    <span><b>D/E:</b> {de_str}</span>
                    <span><b>Qtr PAT YoY:</b> {pat_str}</span>
                    <span><b>OPM Exp:</b> {opm_str}</span>
                </div>
                <div class="levels-grid">
                    <div class="level-box">
                        <small>Entry Zone</small>
                        <div class="lvl-val" style="color: #38bdf8; font-size:12px;">{p.get('suggested_entry', 'Near CMP')}</div>
                    </div>
                    <div class="level-box">
                        <small>Target 1</small>
                        <div class="lvl-val" style="color: #10b981;">₹{p['target_1']:,.2f}</div>
                    </div>
                    <div class="level-box">
                        <small>Target 2 (Long-Term)</small>
                        <div class="lvl-val" style="color: #34d399;">₹{p['target_2']:,.2f}</div>
                    </div>
                    <div class="level-box">
                        <small>Stop Loss</small>
                        <div class="lvl-val" style="color: #f87171;">₹{p['stop_loss']:,.2f}</div>
                    </div>
                </div>
                <div class="audit-split">
                    <div class="audit-col">
                        <div class="audit-title">⚡ Weekly &amp; Technical Checklist</div>
                        <ul>{signals_li}</ul>
                    </div>
                    <div class="audit-col">
                        <div class="audit-title">🏛️ Consolidated Inflection &amp; Quality</div>
                        <ul>{strengths_li}</ul>
                    </div>
                </div>
            </div>
            """

        # Generate Dedicated 5-Factor Value & Promoter Inflection Rows
        fac_multi4 = sum(1 for f in factor_stocks if f.get("matches_count", 0) >= 4)
        fac_vol_up = sum(1 for f in factor_stocks if f.get("flag_vol"))
        fac_prom_up = sum(1 for f in factor_stocks if f.get("flag_promoter"))
        fac_pat_up = sum(1 for f in factor_stocks if f.get("flag_profit_high"))
        fac_eff_up = sum(1 for f in factor_stocks if f.get("flag_eff_up"))
        fac_val_low = sum(1 for f in factor_stocks if f.get("flag_low_value"))

        factor_rows = ""
        for f in factor_stocks:
            sym = f["symbol"]
            fscore = float(f.get("factor_score", 5.0))
            mcount = int(f.get("matches_count", 0))
            badge_col = "#10b981" if mcount >= 4 else ("#38bdf8" if mcount == 3 else "#8b5cf6")

            chips = []
            if f.get("flag_vol"):
                chips.append("<span style='color:#34d399;'>✓Vol</span>")
            if f.get("flag_promoter"):
                chips.append("<span style='color:#fbbf24;'>✓Prom</span>")
            elif f.get("flag_smart_money"):
                chips.append("<span style='color:#38bdf8;'>✓Inst</span>")
            if f.get("flag_profit_high"):
                chips.append("<span style='color:#34d399;'>✓PAT</span>")
            if f.get("flag_eff_up"):
                chips.append("<span style='color:#a78bfa;'>✓ROCE/ROE</span>")
            if f.get("flag_low_value"):
                chips.append("<span style='color:#38bdf8;'>✓Value</span>")
            chips_html = " ".join(chips)

            vol_badge = "🔥 " if f.get("flag_vol") else ""
            prom_4q = float(f.get("promoter_4q_delta", 0.0))
            prom_qoq = float(f.get("promoter_qoq_delta", 0.0))
            best_prom_d = prom_4q if abs(prom_4q) >= abs(prom_qoq) else prom_qoq
            prom_col = "#10b981" if f.get("flag_promoter") else "#94a3b8"
            inst_d = float(f.get("inst_4q_delta", 0.0))

            pat_qoq = f.get("qtr_pat_qoq_pct")
            pat_yoy = f.get("qtr_pat_yoy_pct")
            pat_qoq_str = f"{pat_qoq:+.1f}%" if pat_qoq is not None else "—"
            pat_yoy_str = f"{pat_yoy:+.1f}%" if pat_yoy is not None else "—"
            pat_q_col = "#34d399" if (pat_qoq or 0) >= 10 else ("#f87171" if (pat_qoq or 0) < 0 else "#cbd5e1")
            pat_y_col = "#10b981" if (pat_yoy or 0) >= 20 else ("#f87171" if (pat_yoy or 0) < 0 else "#cbd5e1")

            roce_v = f.get("roce_latest", 0.0)
            roce_d = f.get("roce_delta")
            roe_v = f.get("roe_latest", 0.0)
            roe_d = f.get("roe_delta")
            roce_str = f"{roce_v:.1f}% (<b style='color:{'#34d399' if (roce_d or 0)>0 else '#94a3b8'};'>{roce_d:+.1f}%</b>)" if roce_d is not None else f"{roce_v:.1f}%"
            roe_str = f"{roe_v:.1f}% (<b style='color:{'#34d399' if (roe_d or 0)>0 else '#94a3b8'};'>{roe_d:+.1f}%</b>)" if roe_d is not None else f"{roe_v:.1f}%"

            pe_v = f.get("pe", 0.0)
            peg_v = f.get("peg")
            peg_str = f"PEG: {peg_v:.2f}" if peg_v is not None else f"Off 52W: -{f.get('dist_52w', 0)}%"
            val_tag = f.get("valuation_tag", "⚖️ Fair")
            de_v = f.get("debt_to_equity")
            de_lbl = f"D/E: {de_v:.2f}x" if isinstance(de_v, (int, float)) else ""
            mcap_v = f.get("mcap_cr", 0)
            mcap_lbl = f"₹{mcap_v:,.0f} Cr" if mcap_v else ""

            factor_rows += f"""
            <tr class="stock-row factor-row"
                data-symbol="{sym}" data-name="{f.get('name', sym)}" data-sector="{f.get('sector', 'Equities')}"
                data-vol="{1 if f.get('flag_vol') else 0}"
                data-prom="{1 if f.get('flag_promoter') else 0}"
                data-sm="{1 if f.get('flag_smart_money') else 0}"
                data-pat="{1 if f.get('flag_profit_high') else 0}"
                data-eff="{1 if f.get('flag_eff_up') else 0}"
                data-val="{1 if f.get('flag_low_value') else 0}"
                data-matches="{mcount}">
                <td>
                    <div class="sym-name">{sym}</div>
                    <div class="sub-text">{f.get('name', sym)}</div>
                    <div class="sub-text" style="color:#64748b;">{mcap_lbl} {('• ' + de_lbl) if de_lbl else ''}</div>
                </td>
                <td><span class="sector-pill">{f.get('sector', 'Equities')}</span></td>
                <td>
                    <span style="display:inline-flex; align-items:center; gap:4px; background:{badge_col}22; color:{badge_col}; border:1px solid {badge_col}; padding:3px 8px; border-radius:6px; font-weight:800; font-size:12px;">
                        ⭐ {fscore:.1f} ({mcount}/5)
                    </span>
                    <div style="font-size:10px; margin-top:4px; line-height:1.3;">{chips_html}</div>
                </td>
                <td>
                    <b>₹{f['cmp']:,.2f}</b>
                    <div class="sub-text" style="color:#38bdf8;">-{f.get('dist_52w', 0)}% off 52W</div>
                </td>
                <td>
                    <b style="color:{'#10b981' if f.get('flag_vol') else '#cbd5e1'};">{vol_badge}{f.get('vol_trend_4w', 1.0)}x (4W)</b>
                    <div class="sub-text">Wk Surge: {f.get('vol_surge', 1.0)}x</div>
                </td>
                <td>
                    <b style="color:{prom_col};">{f.get('promoter_pct', 0)}% ({best_prom_d:+.2f}%)</b>
                    <div class="sub-text" style="color:{'#34d399' if inst_d > 0 else '#94a3b8'};">FII+DII 4Q: {inst_d:+.1f}%</div>
                </td>
                <td>
                    <div>QoQ: <b style="color:{pat_q_col};">{pat_qoq_str}</b></div>
                    <div>YoY: <b style="color:{pat_y_col};">{pat_yoy_str}</b></div>
                </td>
                <td style="font-size:12px;">
                    <div>ROCE: {roce_str}</div>
                    <div>ROE: {roe_str}</div>
                </td>
                <td>
                    <b>P/E: {pe_v:.1f}x</b> <span style="font-size:11px; color:#94a3b8;">({peg_str})</span>
                    <div style="font-size:11px; color:{'#10b981' if f.get('flag_low_value') else '#94a3b8'}; font-weight:700; margin-top:2px;">{val_tag}</div>
                </td>
                <td><button class="chart-btn" onclick="toggleCandleChart('{sym}', this)">📈 Chart</button></td>
            </tr>
            """

        # Generate Small & Mid-Cap Hidden Gems Rows
        hg_total = len(hidden_gems)
        hg_small = sum(1 for g in hidden_gems if g.get("cap_tier") == "Small Cap")
        hg_mid = sum(1 for g in hidden_gems if g.get("cap_tier") == "Mid Cap")
        hg_ready = sum(1 for g in hidden_gems if g.get("status_key") in ("breakout", "pullback"))
        hg_avg_roce = round(sum(float(g.get("roce") or 0.0) for g in hidden_gems) / hg_total, 1) if hg_total else 0.0

        hidden_gems_rows = ""
        for g in hidden_gems:
            sym = g.get("symbol", "")
            cap_tier = g.get("cap_tier", "Mid Cap")
            cap_key = "small" if cap_tier == "Small Cap" else "mid"
            cap_col = "#34d399" if cap_key == "small" else "#38bdf8"
            mcap_cr = float(g.get("mcap_cr") or 0.0)
            g_score = float(g.get("gem_score") or 7.0)
            g_col = "#10b981" if g_score >= 8.5 else ("#38bdf8" if g_score >= 7.5 else "#a78bfa")
            day_pct = float(g.get("day_change_pct") or 0.0)
            day_col = "#10b981" if day_pct >= 0 else "#ef4444"
            day_sign = "+" if day_pct >= 0 else ""
            s_key = g.get("status_key", "pullback")
            s_col = g.get("status_color", "#38bdf8")
            pe_v = float(g.get("pe") or 0.0)
            peg_v = g.get("peg")
            peg_lbl = f"PEG {peg_v:.2f}" if isinstance(peg_v, (int, float)) else "GARP"
            cfo_v = g.get("cfo_to_pat_3y")
            cfo_lbl = f"{cfo_v:.2f}x" if isinstance(cfo_v, (int, float)) else "—"
            sales_yoy = g.get("qtr_sales_yoy_pct")
            pat_yoy = g.get("qtr_pat_yoy_pct")
            sales_str = f"{sales_yoy:+.1f}%" if isinstance(sales_yoy, (int, float)) else "—"
            pat_str = f"{pat_yoy:+.1f}%" if isinstance(pat_yoy, (int, float)) else "—"
            de_v = g.get("debt_to_equity")
            de_str = f"{de_v:.2f}x" if isinstance(de_v, (int, float)) else "—"
            opm_bps = g.get("opm_expansion_bps")
            opm_str = f" • OPM {int(opm_bps):+d} bps" if isinstance(opm_bps, (int, float)) and opm_bps != 0 else ""
            ret1y = float(g.get("ret_1y") or 0.0)
            ret1y_col = "#34d399" if ret1y >= 0 else "#f87171"

            hidden_gems_rows += f"""
            <tr class="stock-row gem-row"
                data-symbol="{sym}" data-name="{g.get('name', sym)}" data-sector="{g.get('sector', 'Equities')}"
                data-cap="{cap_key}" data-status="{s_key}">
                <td>
                    <div class="sym-name">{sym} <span style="font-size:10px; padding:1px 6px; border-radius:10px; background:{cap_col}22; color:{cap_col}; border:1px solid {cap_col}66; font-weight:700;">{cap_tier}</span></div>
                    <div class="sub-text">{g.get('name', sym)}</div>
                    <div class="sub-text" style="color:#94a3b8;">MCap: ₹{mcap_cr:,.0f} Cr • D/E: {de_str}</div>
                </td>
                <td><span class="sector-pill">{g.get('sector', 'Equities')}</span></td>
                <td>
                    <span style="display:inline-flex; align-items:center; gap:4px; background:{g_col}22; color:{g_col}; border:1px solid {g_col}; padding:3px 8px; border-radius:6px; font-weight:800; font-size:12px;">
                        💎 {g_score:.1f}/10
                    </span>
                    <div style="margin-top:4px;"><span style="font-size:11px; font-weight:700; color:{s_col};">{g.get('setup_status', '')}</span></div>
                </td>
                <td>
                    <b>₹{float(g.get('cmp') or 0):,.2f}</b>
                    <div class="sub-text" style="color:{day_col}; font-weight:700;">{day_sign}{day_pct:.2f}% Today</div>
                    <div class="sub-text" style="color:#94a3b8;">-{g.get('dist_52w', 0)}% off 52W</div>
                </td>
                <td>
                    <b>{pe_v:.1f}x</b>
                    <div class="sub-text" style="color:#38bdf8;">{peg_lbl}</div>
                </td>
                <td>
                    <div><b>ROCE:</b> <span style="color:#34d399;">{g.get('roce', 0)}%</span></div>
                    <div class="sub-text"><b>ROE:</b> {g.get('roe', 0)}% • <b>CFO/PAT:</b> {cfo_lbl}</div>
                </td>
                <td>
                    <div>Sales: <b style="color:#38bdf8;">{sales_str}</b></div>
                    <div>PAT: <b style="color:#10b981;">{pat_str}</b><span class="sub-text">{opm_str}</span></div>
                </td>
                <td style="font-size:12px;">
                    <div>RSI: <b>{g.get('rsi', 50)}</b> • <span style="color:{ret1y_col}; font-weight:700;">1Y: {ret1y:+.1f}%</span></div>
                    <div class="sub-text">20E: ₹{g.get('ema_20', 0):,.0f} • 50E: ₹{g.get('ema_50', 0):,.0f}</div>
                </td>
                <td style="font-size:12px;">
                    <div style="color:#38bdf8; font-weight:700;">Entry: {g.get('suggested_entry', '')}</div>
                    <div class="sub-text"><span style="color:#10b981;">T1: ₹{g.get('target_1', 0):,.1f}</span> • <span style="color:#ef4444;">SL: ₹{g.get('stop_loss', 0):,.1f}</span></div>
                </td>
                <td><button class="chart-btn" onclick="toggleCandleChart('{sym}', this)">📈 Chart</button></td>
            </tr>
            """

        # Generate IPO Table
        ipo_rows = ""
        for ipo in ipo_list:
            gmp_pct = ipo.get("gmp_pct", 0)
            gmp_inr = str(ipo.get("gmp_inr", "—"))
            gmp_sign = "+" if gmp_pct > 0 else ("-" if gmp_pct < 0 else "")
            gmp_color = "#10b981" if gmp_pct >= 20.0 else ("#eab308" if gmp_pct > 0 else "#ef4444")
            gmp_text = f"{gmp_sign}{abs(gmp_pct)}% ({gmp_inr})" if gmp_pct != 0 else (f"{gmp_inr} (0.0%)" if gmp_inr != "—" else "—")

            # Clean Lot Size display
            raw_lot = str(ipo.get("lot_size", "TBA")).replace("shares", "").strip()
            lot_str = f"{raw_lot} shares" if raw_lot.isdigit() else raw_lot

            # Clean Issue Size display
            raw_sz = str(ipo.get("issue_size_cr", "TBA")).replace("Cr", "").replace("₹", "").strip()
            size_str = f"₹{raw_sz} Cr" if raw_sz.replace(".", "").isdigit() else raw_sz

            # Status pill styling
            st_lower = str(ipo.get("status", "")).lower()
            if "upcoming" in st_lower or "open" in st_lower:
                st_color = "#f59e0b"
            elif "listed" in st_lower:
                st_color = "#38bdf8"
            else:
                st_color = "#10b981"

            # Verdict badge color
            v_text = str(ipo.get("verdict", "APPLY"))
            if any(k in v_text.upper() for k in ["STRONG APPLY", "MULTIBAGGER"]):
                v_bg = "#16a34a"
            elif any(k in v_text.upper() for k in ["APPLY", "POSITIVE"]):
                v_bg = "#0284c7"
            elif any(k in v_text.upper() for k in ["DISCOUNT", "AVOID"]):
                v_bg = "#dc2626"
            else:
                v_bg = "#d97706"

            ipo_rows += f"""
            <tr>
                <td>
                    <b>{ipo['name']}</b>
                    <div class="sub-text">{ipo['sector']} &bull; {ipo['category']}</div>
                </td>
                <td><span class="status-pill" style="border-color: {st_color}; color: {st_color};">{ipo['status']}</span></td>
                <td><b>{ipo['price_band']}</b></td>
                <td>{lot_str}</td>
                <td>{size_str}</td>
                <td><b>{ipo['subscription_total']}</b></td>
                <td style="color: {gmp_color}; font-weight: 700;">{gmp_text}</td>
                <td><span class="badge" style="background: {v_bg};">{ipo['verdict']}</span></td>
            </tr>
            """

        # Generate Institutional & FII/DII Table Rows
        fii_dii_rows = ""
        fii_history = inst_flow.get("fii_dii_history", []) if inst_flow else []
        for r in fii_history:
            fii_val = r.get("fii_cash_net", "0.0")
            dii_val = r.get("dii_cash_net", "0.0")
            fii_col = "#10b981" if not fii_val.startswith("-") else "#ef4444"
            dii_col = "#10b981" if not dii_val.startswith("-") else "#ef4444"
            n_chg = r.get("nifty_change_pct", "0.0")
            n_col = "#10b981" if not n_chg.startswith("-") else "#ef4444"
            fii_dii_rows += f"""
            <tr>
                <td><b>{r.get('formatted_date', r.get('date'))}</b></td>
                <td style="color: {fii_col}; font-weight: 700;">₹{fii_val} Cr</td>
                <td style="color: {dii_col}; font-weight: 700;">₹{dii_val} Cr</td>
                <td>₹{r.get('fii_index_futures', '—')} Cr</td>
                <td>₹{r.get('fii_index_options', '—')} Cr</td>
                <td>₹{r.get('fii_stock_futures', '—')} Cr</td>
                <td><b>{r.get('nifty_close', '—')}</b> <span style="color: {n_col}; font-size: 11px;">({n_chg}%)</span></td>
            </tr>
            """

        # Generate Corporate Actions & Dividends
        corp_actions = scan_data.get("corporate_actions")
        if not corp_actions:
            try:
                from core.corporate_actions_calendar import CorporateActionsCalendar
                corp_actions = CorporateActionsCalendar().get_calendar_events(force_refresh=False)
            except Exception:
                corp_actions = {"dividends": [], "earnings": [], "splits_and_actions": []}

        dividend_rows = ""
        for d in corp_actions.get("dividends", []):
            dividend_rows += f"""
            <tr>
                <td><b>{d.get('stock_name')}</b> <span class="sub-text">({d.get('symbol')})</span></td>
                <td><span class="status-pill" style="border-color: #10b981; color: #10b981;">{d.get('event_type')}</span></td>
                <td><b>{d.get('ex_date')}</b></td>
                <td style="color: #10b981; font-weight: 800; font-size: 14px;">{d.get('dividend_amount')}</td>
                <td>{d.get('cmp')}</td>
                <td style="color: #38bdf8; font-weight: 700;">{d.get('estimated_yield')}</td>
                <td>{d.get('announcement_date', '—')}</td>
            </tr>
            """

        earnings_rows = ""
        for e in corp_actions.get("earnings", []):
            earnings_rows += f"""
            <tr>
                <td><b>{e.get('date')}</b></td>
                <td><b>{e.get('stock_name')}</b> <span class="sub-text">({e.get('symbol')})</span></td>
                <td><span class="badge" style="background: #0284c7;">{e.get('result_type')}</span></td>
                <td><b>{e.get('ltp')}</b></td>
                <td>{e.get('market_cap')}</td>
            </tr>
            """

        splits_rows = ""
        for s in corp_actions.get("splits_and_actions", []):
            splits_rows += f"""
            <tr>
                <td><b>{s.get('stock_name')}</b> <span class="sub-text">({s.get('symbol')})</span></td>
                <td><span class="status-pill" style="border-color: #8b5cf6; color: #a78bfa;">{s.get('action_type')}</span></td>
                <td><b>{s.get('ex_date')}</b></td>
                <td style="color: #f59e0b; font-weight: 800; font-size: 14px;">{s.get('ratio')}</td>
                <td>{s.get('announcement_date', '—')}</td>
            </tr>
            """

        # Generate AI Recommendation Performance Scorecard & Feed Freshness Strip
        scorecard_data = scan_data.get("performance_scorecard")
        if not scorecard_data:
            try:
                from core.ai_performance_scorecard import AIPerformanceScorecard
                scorecard_data = AIPerformanceScorecard().get_performance_metrics()
            except Exception:
                scorecard_data = {}

        arch_stats = scorecard_data.get("archetype_breakdown", {}) or {}
        arch_pills = []
        for arch_name, st_info in list(arch_stats.items())[:6]:
            wr = st_info.get("win_rate")
            wr_lbl = f"{wr:.1f}% Win" if wr is not None else "Active"
            arch_pills.append(
                f"<span class='feed-pill'><b>{arch_name}</b>: {st_info.get('count', 0)} setups ({wr_lbl})</span>"
            )
        archetype_strip_html = (
            f"<div class='feed-health-ribbon' style='margin-bottom:14px;'><span class='feed-health-title'>📊 Strategy Breakdown:</span>{''.join(arch_pills)}</div>"
            if arch_pills
            else ""
        )

        feed_health_data = scan_data.get("feed_health")
        if not feed_health_data:
            try:
                from core.feed_health import collect_feed_health
                feed_health_data = collect_feed_health(scan_data)
            except Exception:
                feed_health_data = {"healthy_count": 0, "total_feeds": 0, "feeds": []}
        feed_pills = []
        for fd in feed_health_data.get("feeds", []):
            feed_pills.append(
                f"<span class='feed-pill' title=\"{fd.get('detail', '')} • Updated: {fd.get('updated_at', '')}\">"
                f"<span class='feed-dot' style='background:{fd.get('color', '#94a3b8')};'></span>"
                f"<b>{fd.get('feed')}:</b> {fd.get('status')} ({fd.get('age')})</span>"
            )
        feed_health_html = (
            f"<span class='feed-health-title'>📡 Feeds ({feed_health_data.get('healthy_count', 0)}/{feed_health_data.get('total_feeds', 0)} Healthy):</span>"
            + "".join(feed_pills)
        )

        scorecard_rows = ""
        for p in scorecard_data.get("top_historical_setups", []):
            out_class = p.get("outcome_class", "outcome-win")
            gain_val = p.get("gain_pct", "+0.0%")
            gain_color = "#10b981" if not gain_val.startswith("-") else "#ef4444"
            alpha_val = p.get("alpha_vs_nifty_pct")
            alpha_sub = f"<div class='sub-text'>Alpha vs Nifty: {alpha_val:+.1f}%</div>" if alpha_val is not None else ""
            scorecard_rows += f"""
            <tr>
                <td><b>{p.get('symbol')}</b><div class="sub-text">{p.get('sector')}</div></td>
                <td><span class="sector-pill">{p.get('setup_name')}</span></td>
                <td>{p.get('entry_date')}</td>
                <td><b>₹{p.get('entry_price', 0):,.2f}</b></td>
                <td style="color: #38bdf8; font-weight: 700;">₹{p.get('target_1', 0):,.2f}</td>
                <td style="color: #f59e0b;">₹{p.get('stop_loss', 0):,.2f}</td>
                <td><b>₹{p.get('cmp', p.get('entry_price', 0)):,.2f}</b></td>
                <td style="color: {gain_color}; font-weight: 800; font-size: 14px;">{gain_val}{alpha_sub}</td>
                <td><span class="status-pill {out_class}">{p.get('outcome', p.get('status'))}</span></td>
            </tr>
            """

        # Load Market Movers (Top Gainers & Losers)
        movers_data = scan_data.get("market_movers")
        if not movers_data:
            try:
                from core.market_movers_analyst import MarketMoversAnalyst
                movers_data = MarketMoversAnalyst().get_market_movers(force_refresh=False)
            except Exception:
                movers_data = {"top_gainers": [], "top_losers": []}

        top_gainers = movers_data.get("top_gainers", [])
        top_losers = movers_data.get("top_losers", [])

        # Generate Detailed Movers Table Rows (Sl No, Stock Name, CMP, % of Gain / Loss)
        gainer_rows = ""
        for idx, g in enumerate(top_gainers, 1):
            sym = g.get('symbol', '')
            name = g.get('name', sym)
            price = g.get('price', '-')
            pct = g.get('change_pct', '+0.0%')
            chg = g.get('change_val', '-')
            high = g.get('high', '-')
            low = g.get('low', '-')
            vol = g.get('volume', '-')
            gainer_rows += f"""
            <tr class="stock-row mover-row" data-symbol="{sym}" data-name="{name}" data-sector="NSE Top Gainer">
                <td style="text-align: center; font-weight: 800; font-size: 14px; color: var(--text-muted);">#{idx}</td>
                <td>
                    <div style="font-weight: 800; font-size: 15px; color: var(--text-heading); letter-spacing: -0.2px;">{name}</div>
                    <span style="display: inline-block; margin-top: 3px; font-size: 11px; font-weight: 700; color: #0284c7; background: rgba(2, 132, 199, 0.12); padding: 2px 7px; border-radius: 4px; font-family: monospace;">NSE: {sym}</span>
                </td>
                <td style="font-weight: 800; font-size: 15px; color: var(--text-heading);">{price}</td>
                <td style="color: #10b981; font-weight: 800; font-size: 14px;">{pct}</td>
                <td style="color: #10b981; font-weight: 700;">{chg}</td>
                <td style="font-weight: 600; color: var(--text-main);">{high}</td>
                <td style="font-weight: 600; color: var(--text-main);">{low}</td>
                <td style="font-weight: 600; color: var(--text-main);">{vol}</td>
                <td><button class="chart-btn" onclick="toggleCandleChart('{sym}', this)">📈 Chart</button></td>
            </tr>
            """

        loser_rows = ""
        for idx, l in enumerate(top_losers, 1):
            sym = l.get('symbol', '')
            name = l.get('name', sym)
            price = l.get('price', '-')
            pct = l.get('change_pct', '-0.0%')
            chg = l.get('change_val', '-')
            high = l.get('high', '-')
            low = l.get('low', '-')
            vol = l.get('volume', '-')
            loser_rows += f"""
            <tr class="stock-row mover-row" data-symbol="{sym}" data-name="{name}" data-sector="NSE Top Loser">
                <td style="text-align: center; font-weight: 800; font-size: 14px; color: var(--text-muted);">#{idx}</td>
                <td>
                    <div style="font-weight: 800; font-size: 15px; color: var(--text-heading); letter-spacing: -0.2px;">{name}</div>
                    <span style="display: inline-block; margin-top: 3px; font-size: 11px; font-weight: 700; color: #ef4444; background: rgba(239, 68, 68, 0.12); padding: 2px 7px; border-radius: 4px; font-family: monospace;">NSE: {sym}</span>
                </td>
                <td style="font-weight: 800; font-size: 15px; color: var(--text-heading);">{price}</td>
                <td style="color: #ef4444; font-weight: 800; font-size: 14px;">{pct}</td>
                <td style="color: #ef4444; font-weight: 700;">{chg}</td>
                <td style="font-weight: 600; color: var(--text-main);">{high}</td>
                <td style="font-weight: 600; color: var(--text-main);">{low}</td>
                <td style="font-weight: 600; color: var(--text-main);">{vol}</td>
                <td><button class="chart-btn" onclick="toggleCandleChart('{sym}', this)">📈 Chart</button></td>
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
    __STYLES_PLACEHOLDER__
</head>
<body>

    <div class="header">
        <div class="header-title">
            <h1>🇮🇳 Indian Stock AI &bull; Senior Fund Manager &amp; Momentum Intelligence</h1>
            <p>Multi-Timeframe Trend Screener (3M/6M/1Y/3Y), Monitored Radar, 360&deg; Stock Audit &amp; Mutual Fund Advisory</p>
            <div style="margin-top: 6px; font-size: 13px; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 8px;">
                <span>👨‍💻 Application Designed and Developed by <b>Swamy Chouhan</b></span>
                <span style="opacity: 0.5;">•</span>
                <span>📞 <b>9000632912</b></span>
            </div>
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
            <button class="action-btn" onclick="openTelegramModal()" style="background: rgba(14, 165, 233, 0.15); border-color: #0ea5e9; color: #38bdf8;" title="Set up free Telegram Bot alerts on your phone">
                📱 Free Phone Alerts
            </button>
            <button id="themeToggleBtn" class="theme-toggle-btn" onclick="toggleTheme()" title="Switch between Dark Mode and Light Mode">
                <span id="themeToggleIcon" class="theme-icon">🌙</span>
                <span id="themeToggleText">Dark Mode</span>
            </button>
        </div>
    </div>

    <!-- Upstream Feed Health & Freshness Telemetry -->
    <div id="feedHealthRibbon" class="feed-health-ribbon">
        {feed_health_html}
    </div>

    <!-- Benchmark Indices & Global Commodities -->
    <div class="indices-grid">
        {indices_html}
    </div>

    <!-- Navigation & Search Controls -->
    <div class="controls-bar">
        <div class="tabs">
            <button class="tab-btn active" onclick="switchView('momentum', this)">🏆 Super-Trend Leaders (3M/1Y/3Y)</button>
            <button id="tabBtnHiddenGems" class="tab-btn" onclick="switchView('hidden_gems', this)" style="border-color: #a855f7; color: #c084fc; font-weight: 700;">💎 Hidden Gems (Small &amp; Mid Cap)</button>
            <button class="tab-btn" onclick="switchView('factor_screener', this)" style="border-color: #10b981; color: #34d399; font-weight: 700;">💎 Factor &amp; Value Finder</button>
            <button id="tabBtnMovers" class="tab-btn" onclick="switchView('movers', this)" style="border-color: #f59e0b; color: #f59e0b; font-weight: 700;">⚡ Top Movers (Gainers &amp; Losers)</button>
            <button class="tab-btn" onclick="switchView('fifty_two_week', this)">🚀 52-Week High Leaders</button>
            <button class="tab-btn" onclick="switchView('radar', this)">🎯 AI Fund Manager Radar</button>
            <button class="tab-btn" onclick="switchView('mutualfunds', this)">💼 Mutual Fund Advisory</button>
            <button class="tab-btn" onclick="switchView('leaderboard', this)">🚀 360&deg; Bullish Picks</button>
            <button class="tab-btn" onclick="switchView('cards', this)">🔍 Deep Dive Cards</button>
            <button class="tab-btn" onclick="switchView('ipos', this)">📋 IPOs &amp; GMP</button>
            <button class="tab-btn" onclick="switchView('portfolio', this)" style="border-color: #10b981;">💼 My Portfolio (Live P&amp;L)</button>
            <button class="tab-btn" onclick="switchView('institutional', this)">🏛 Smart Money &amp; FII/DII</button>
            <button class="tab-btn" onclick="switchView('corporate_actions', this)">📅 Earnings &amp; Dividends</button>
            <button class="tab-btn" onclick="switchView('scorecard', this)">🎯 AI Win-Rate Scorecard</button>
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
                    <a href="javascript:void(0)" onclick="quickSearch('LAURUSLABS')" style="color:#38bdf8; text-decoration:none; margin-right:6px;">LAURUSLABS</a>
                    <a href="javascript:void(0)" onclick="quickSearch('TRENT')" style="color:#38bdf8; text-decoration:none; margin-right:6px;">TRENT</a>
                    <a href="javascript:void(0)" onclick="quickSearch('HAL')" style="color:#38bdf8; text-decoration:none; margin-right:6px;">HAL</a>
                    <a href="javascript:void(0)" onclick="quickSearch('MCX')" style="color:#38bdf8; text-decoration:none; margin-right:6px;">MCX</a>
                    <a href="javascript:void(0)" onclick="quickSearch('BSE')" style="color:#38bdf8; text-decoration:none; margin-right:6px;">BSE</a>
                    <a href="javascript:void(0)" onclick="quickSearch('DIXON')" style="color:#38bdf8; text-decoration:none; margin-right:6px;">DIXON</a>
                    <a href="javascript:void(0)" onclick="quickSearch('PERSISTENT')" style="color:#38bdf8; text-decoration:none;">PERSISTENT</a>
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
                        <th class="sortable" onclick="sortTable(this, 2)">CIO Rating</th>
                        <th class="sortable" onclick="sortTable(this, 3)">CMP</th>
                        <th class="sortable" onclick="sortTable(this, 4)">3M Return</th>
                        <th class="sortable" onclick="sortTable(this, 5)">6M Return</th>
                        <th class="sortable" onclick="sortTable(this, 6)">1Y Return</th>
                        <th class="sortable" onclick="sortTable(this, 7)">3Y Return</th>
                        <th class="sortable" onclick="sortTable(this, 8)">Trend Status</th>
                        <th>Chart</th>
                    </tr>
                </thead>
                <tbody id="momentumTbody">
                    {momentum_rows}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Tab 1B: Dedicated 5-Factor Value, Promoter & Earnings Inflection Finder -->
    <div id="view-factor_screener" class="view-panel" style="display: none;">
        <div style="background: linear-gradient(135deg, #064e3b, #0f172a); border: 1px solid #10b981; border-radius: 12px; padding: 18px 22px; margin-bottom: 18px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <h3 style="color: #fff; font-size: 18px; margin: 0 0 6px 0; display: flex; align-items: center; gap: 8px;">
                        <span>💎 Smart 5-Factor Multibagger &amp; Undervalued Turnaround Finder</span>
                        <span style="background: #065f46; color: #34d399; font-size: 11px; padding: 2px 8px; border-radius: 12px;">NSE 509 Screened</span>
                    </h3>
                    <p style="color: #cbd5e1; font-size: 13px; margin: 0;">
                        Traces <b>Volume Rising</b> &bull; <b>Promoter Stake Increasing</b> &bull; <b>QoQ &amp; YoY Profit Surge</b> &bull; <b>ROCE &amp; ROE Up</b> &bull; <b>Low Valuation / Discounted GARP</b> in one unified screen.
                    </p>
                </div>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <div style="background: #111827; border: 1px solid #10b98155; padding: 8px 12px; border-radius: 8px; text-align: center;">
                        <span style="font-size: 10px; color: #94a3b8; display: block;">4+/5 Factor Hits</span>
                        <b style="font-size: 15px; color: #34d399;">{fac_multi4} Stocks</b>
                    </div>
                    <div style="background: #111827; border: 1px solid #374151; padding: 8px 12px; border-radius: 8px; text-align: center;">
                        <span style="font-size: 10px; color: #94a3b8; display: block;">Promoter Buying</span>
                        <b style="font-size: 15px; color: #fbbf24;">{fac_prom_up}</b>
                    </div>
                    <div style="background: #111827; border: 1px solid #374151; padding: 8px 12px; border-radius: 8px; text-align: center;">
                        <span style="font-size: 10px; color: #94a3b8; display: block;">QoQ &amp; YoY PAT Up</span>
                        <b style="font-size: 15px; color: #10b981;">{fac_pat_up}</b>
                    </div>
                    <div style="background: #111827; border: 1px solid #374151; padding: 8px 12px; border-radius: 8px; text-align: center;">
                        <span style="font-size: 10px; color: #94a3b8; display: block;">ROCE &amp; ROE Up</span>
                        <b style="font-size: 15px; color: #a78bfa;">{fac_eff_up}</b>
                    </div>
                    <div style="background: #111827; border: 1px solid #374151; padding: 8px 12px; border-radius: 8px; text-align: center;">
                        <span style="font-size: 10px; color: #94a3b8; display: block;">Low Valuation</span>
                        <b style="font-size: 15px; color: #38bdf8;">{fac_val_low}</b>
                    </div>
                </div>
            </div>
        </div>

        <!-- Interactive 5-Factor Filter Controls & Quick Presets -->
        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 14px 18px; margin-bottom: 18px;">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px; margin-bottom: 12px;">
                <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
                    <span style="font-size: 12px; font-weight: 800; color: var(--text-heading);">⚡ Quick Presets:</span>
                    <button class="sip-preset-btn" onclick="applyFactorPreset('all')" style="font-weight:700; color:#38bdf8;">All Screened</button>
                    <button class="sip-preset-btn" onclick="applyFactorPreset('multi3')" style="font-weight:700; color:#34d399;">🔥 3+ Factors Matched</button>
                    <button class="sip-preset-btn" onclick="applyFactorPreset('prom_pat')" style="font-weight:700; color:#fbbf24;">🤝 Promoter Up + High Profit</button>
                    <button class="sip-preset-btn" onclick="applyFactorPreset('val_eff')" style="font-weight:700; color:#38bdf8;">💎 Undervalued + ROCE/ROE Up</button>
                    <button class="sip-preset-btn" onclick="applyFactorPreset('vol_pat')" style="font-weight:700; color:#a78bfa;">📈 Volume Surge + High Profit</button>
                </div>
                <span id="factorMatchCountBadge" class="badge" style="background: #0284c7;">Showing {len(factor_stocks)} Stocks</span>
            </div>

            <div style="display: flex; gap: 16px; flex-wrap: wrap; align-items: center; font-size: 13px; color: var(--text-heading);">
                <label style="cursor:pointer; display:inline-flex; align-items:center; gap:6px;"><input type="checkbox" id="fltVolUp" onchange="filterFactorScreener()"> 📈 Volume Increasing</label>
                <label style="cursor:pointer; display:inline-flex; align-items:center; gap:6px;"><input type="checkbox" id="fltPromUp" onchange="filterFactorScreener()"> 🤝 Promoter Shares Increasing</label>
                <label style="cursor:pointer; display:inline-flex; align-items:center; gap:6px;"><input type="checkbox" id="fltSmartMoneyUp" onchange="filterFactorScreener()"> 🏛️ Promoter or FII/DII Up</label>
                <label style="cursor:pointer; display:inline-flex; align-items:center; gap:6px;"><input type="checkbox" id="fltPatHigh" onchange="filterFactorScreener()"> 🚀 QoQ &amp; YoY High Profit</label>
                <label style="cursor:pointer; display:inline-flex; align-items:center; gap:6px;"><input type="checkbox" id="fltEffUp" onchange="filterFactorScreener()"> ⚡ ROCE &amp; ROE Increased</label>
                <label style="cursor:pointer; display:inline-flex; align-items:center; gap:6px;"><input type="checkbox" id="fltLowVal" onchange="filterFactorScreener()"> 💎 Trading Under Low Value</label>
            </div>
        </div>

        <div class="table-container">
            <table id="factorScreenerTable">
                <thead>
                    <tr>
                        <th class="sortable" onclick="sortTable(this, 0)">Stock / Company</th>
                        <th class="sortable" onclick="sortTable(this, 1)">Sector</th>
                        <th class="sortable" onclick="sortTable(this, 2)">Factor Score</th>
                        <th class="sortable" onclick="sortTable(this, 3)">CMP &amp; Off-High</th>
                        <th class="sortable" onclick="sortTable(this, 4)">Volume Trend</th>
                        <th class="sortable" onclick="sortTable(this, 5)">Promoter &amp; Inst &Delta;</th>
                        <th>QoQ &amp; YoY PAT</th>
                        <th>ROCE &amp; ROE &Delta;</th>
                        <th class="sortable" onclick="sortTable(this, 8)">Low Valuation</th>
                        <th>Chart</th>
                    </tr>
                </thead>
                <tbody id="factorScreenerTbody">
                    {factor_rows}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Tab 1C: Small & Mid-Cap Hidden Gems (Auto-Updated with Market Movements) -->
    <div id="view-hidden_gems" class="view-panel" style="display: none;">
        <div style="background: linear-gradient(135deg, #3b0764, #0f172a); border: 1px solid #a855f7; border-radius: 12px; padding: 18px 22px; margin-bottom: 18px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <h3 style="color: #fff; font-size: 18px; margin: 0 0 6px 0; display: flex; align-items: center; gap: 8px;">
                        <span>💎 Small &amp; Mid-Cap Hidden Gems Radar</span>
                        <span style="background: #581c87; color: #e9d5ff; font-size: 11px; padding: 2px 8px; border-radius: 12px;">Auto-Syncs With Live Market Moves</span>
                    </h3>
                    <p style="color: #cbd5e1; font-size: 13px; margin: 0;">
                        High-ROCE, low-debt, cash-generative Small &amp; Mid-Cap compounders (MCap ₹500–₹35,000 Cr, P/E &le; 88x, 3Y CFO/PAT &ge; 0.65x). Live prices, breakout status, entry zones &amp; stops update automatically with market movements.
                    </p>
                </div>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <div style="background: #111827; border: 1px solid #a855f755; padding: 8px 12px; border-radius: 8px; text-align: center;">
                        <span style="font-size: 10px; color: #94a3b8; display: block;">Small-Cap Gems</span>
                        <b style="font-size: 15px; color: #34d399;">{hg_small} Stocks</b>
                    </div>
                    <div style="background: #111827; border: 1px solid #38bdf855; padding: 8px 12px; border-radius: 8px; text-align: center;">
                        <span style="font-size: 10px; color: #94a3b8; display: block;">Mid-Cap Gems</span>
                        <b style="font-size: 15px; color: #38bdf8;">{hg_mid} Stocks</b>
                    </div>
                    <div style="background: #111827; border: 1px solid #10b98155; padding: 8px 12px; border-radius: 8px; text-align: center;">
                        <span style="font-size: 10px; color: #94a3b8; display: block;">Breakout / Buy Ready</span>
                        <b style="font-size: 15px; color: #10b981;">{hg_ready}</b>
                    </div>
                    <div style="background: #111827; border: 1px solid #374151; padding: 8px 12px; border-radius: 8px; text-align: center;">
                        <span style="font-size: 10px; color: #94a3b8; display: block;">Avg ROCE</span>
                        <b style="font-size: 15px; color: #c084fc;">{hg_avg_roce}%</b>
                    </div>
                </div>
            </div>
        </div>

        <div style="background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 12px 18px; margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
            <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
                <span style="font-size: 12px; font-weight: 800; color: var(--text-heading);">🎯 Quick Filters:</span>
                <button class="sip-preset-btn" onclick="applyHiddenGemFilter('all')" style="font-weight:700; color:#c084fc;">All Hidden Gems ({hg_total})</button>
                <button class="sip-preset-btn" onclick="applyHiddenGemFilter('small')" style="font-weight:700; color:#34d399;">🌱 Small Cap (&lt;₹15k Cr)</button>
                <button class="sip-preset-btn" onclick="applyHiddenGemFilter('mid')" style="font-weight:700; color:#38bdf8;">🏛️ Mid Cap (₹15k–35k Cr)</button>
                <button class="sip-preset-btn" onclick="applyHiddenGemFilter('breakout')" style="font-weight:700; color:#10b981;">🔥 Stage-2 Breakouts</button>
                <button class="sip-preset-btn" onclick="applyHiddenGemFilter('pullback')" style="font-weight:700; color:#38bdf8;">🎯 Pullback Buy</button>
                <button class="sip-preset-btn" onclick="applyHiddenGemFilter('turnaround')" style="font-weight:700; color:#a78bfa;">⚡ Base Reclaim / Watch</button>
            </div>
            <span id="hiddenGemsCountBadge" class="badge" style="background: #7e22ce;">Showing {hg_total} Gems</span>
        </div>

        <div class="table-container">
            <table id="hiddenGemsTable">
                <thead>
                    <tr>
                        <th class="sortable" onclick="sortTable(this, 0)">Stock / Cap Tier</th>
                        <th class="sortable" onclick="sortTable(this, 1)">Sector</th>
                        <th class="sortable" onclick="sortTable(this, 2)">Gem Score &amp; Live Setup</th>
                        <th class="sortable" onclick="sortTable(this, 3)">Live CMP &amp; Move</th>
                        <th class="sortable" onclick="sortTable(this, 4)">P/E &amp; PEG</th>
                        <th class="sortable" onclick="sortTable(this, 5)">ROCE / CFO Quality</th>
                        <th>Qtr Growth (YoY)</th>
                        <th>RSI &amp; EMAs</th>
                        <th>Buy Zone / Target / SL</th>
                        <th>Chart</th>
                    </tr>
                </thead>
                <tbody id="hiddenGemsTbody">
                    {hidden_gems_rows}
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
                        <th class="sortable" onclick="sortTable(this, 2)">CIO Rating</th>
                        <th class="sortable" onclick="sortTable(this, 3)">CMP</th>
                        <th class="sortable" onclick="sortTable(this, 4)">Target 3M</th>
                        <th class="sortable" onclick="sortTable(this, 5)">Target 1Y</th>
                        <th class="sortable" onclick="sortTable(this, 6)">Stop Loss</th>
                        <th class="sortable" onclick="sortTable(this, 7)">Monitoring Status</th>
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
        <!-- Interactive Smart SIP & Step-Up Compounding Calculator -->
        <div class="sip-calculator-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px;">
                <div>
                    <h3 style="margin: 0; font-size: 18px; font-weight: 800; color: var(--text-heading); display: flex; align-items: center; gap: 8px;">
                        🌱 Smart SIP &amp; Step-Up Wealth Compounding Planner
                    </h3>
                    <p style="margin: 4px 0 0; font-size: 12px; color: var(--text-muted);">
                        Simulate long-term wealth creation with annual step-up contributions vs Nifty 50 and Stock AI Alpha.
                    </p>
                </div>
                <div id="sipMilestoneBadge" class="badge" style="background: #16a34a; font-size: 13px; padding: 6px 14px;">
                    🏆 ₹1 Crore Goal Target
                </div>
            </div>

            <div class="sip-control-row">
                <div class="sip-control-group">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 13px; font-weight: 700; color: var(--text-heading);">Monthly SIP Amount:</span>
                        <div style="display: flex; align-items: center; gap: 4px;">
                            <button class="sip-inc-btn" onclick="adjustSipAmount(-1000)" title="Decrease by ₹1,000">−1k</button>
                            <span id="sipAmountVal" class="sip-slider-val" style="min-width: 80px; text-align: center; margin: 0 2px;">₹15,000</span>
                            <button class="sip-inc-btn" onclick="adjustSipAmount(1000)" title="Increase by ₹1,000">+1k</button>
                        </div>
                    </div>
                    <input type="range" id="sipAmountSlider" class="sip-slider" min="1000" max="200000" step="1000" value="15000" oninput="onSipSliderChange()">
                    <div style="margin-top: 8px; display: flex; align-items: center; gap: 4px; flex-wrap: wrap;">
                        <button class="sip-preset-btn" onclick="adjustSipAmount(-1000)" style="font-weight: 800; color: var(--primary);">−1k</button>
                        <button class="sip-preset-btn" onclick="adjustSipAmount(1000)" style="font-weight: 800; color: var(--primary);">+1k</button>
                        <button class="sip-preset-btn" onclick="setSipAmount(5000)">₹5k</button>
                        <button class="sip-preset-btn" onclick="setSipAmount(15000)">₹15k</button>
                        <button class="sip-preset-btn" onclick="setSipAmount(25000)">₹25k</button>
                        <button class="sip-preset-btn" onclick="setSipAmount(50000)">₹50k</button>
                        <button class="sip-preset-btn" onclick="setSipAmount(100000)">₹1 Lakh</button>
                    </div>
                </div>

                <div class="sip-control-group">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 13px; font-weight: 700; color: var(--text-heading);">Investment Horizon:</span>
                        <div style="display: flex; align-items: center; gap: 4px;">
                            <button class="sip-inc-btn" onclick="adjustSipYears(-1)" title="Decrease by 1 Year">−</button>
                            <span id="sipYearsVal" class="sip-slider-val" style="min-width: 75px; text-align: center; margin: 0 2px;">10 Years</span>
                            <button class="sip-inc-btn" onclick="adjustSipYears(1)" title="Increase by 1 Year">+</button>
                        </div>
                    </div>
                    <input type="range" id="sipYearsSlider" class="sip-slider" min="1" max="30" step="1" value="10" oninput="onSipSliderChange()">
                    <div style="margin-top: 8px; display: flex; align-items: center; gap: 4px; flex-wrap: wrap;">
                        <button class="sip-preset-btn" onclick="adjustSipYears(-1)" style="font-weight: 800; color: var(--primary);">−1Y</button>
                        <button class="sip-preset-btn" onclick="adjustSipYears(1)" style="font-weight: 800; color: var(--primary);">+1Y</button>
                        <button class="sip-preset-btn" onclick="setSipYears(3)">3Y</button>
                        <button class="sip-preset-btn" onclick="setSipYears(5)">5Y</button>
                        <button class="sip-preset-btn" onclick="setSipYears(8)">8Y</button>
                        <button class="sip-preset-btn" onclick="setSipYears(10)">10Y</button>
                        <button class="sip-preset-btn" onclick="setSipYears(15)">15Y</button>
                        <button class="sip-preset-btn" onclick="setSipYears(20)">20Y</button>
                    </div>
                </div>

                <div class="sip-control-group">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 13px; font-weight: 700; color: var(--text-heading);">Annual Step-Up (%):</span>
                        <div style="display: flex; align-items: center; gap: 4px;">
                            <button class="sip-inc-btn" onclick="adjustSipStepUp(-1)" title="Decrease by 1%">−</button>
                            <span id="sipStepUpVal" class="sip-slider-val" style="min-width: 85px; text-align: center; margin: 0 2px;">10% / year</span>
                            <button class="sip-inc-btn" onclick="adjustSipStepUp(1)" title="Increase by 1%">+</button>
                        </div>
                    </div>
                    <input type="range" id="sipStepUpSlider" class="sip-slider" min="0" max="30" step="1" value="10" oninput="onSipSliderChange()">
                    <div style="margin-top: 8px; display: flex; align-items: center; gap: 4px; flex-wrap: wrap;">
                        <button class="sip-preset-btn" onclick="adjustSipStepUp(-1)" style="font-weight: 800; color: var(--primary);">−1%</button>
                        <button class="sip-preset-btn" onclick="adjustSipStepUp(1)" style="font-weight: 800; color: var(--primary);">+1%</button>
                        <button class="sip-preset-btn" onclick="setSipStepUp(0)">0% (Flat)</button>
                        <button class="sip-preset-btn" onclick="setSipStepUp(5)">+5%</button>
                        <button class="sip-preset-btn" onclick="setSipStepUp(10)">+10%</button>
                        <button class="sip-preset-btn" onclick="setSipStepUp(15)">+15%</button>
                        <button class="sip-preset-btn" onclick="setSipStepUp(20)">+20%</button>
                    </div>
                </div>
            </div>

            <!-- Compounding Result Tiers -->
            <div class="sip-compounding-grid">
                <div class="sip-tier-card">
                    <div class="sip-tier-title">💼 Total Capital Invested</div>
                    <div class="sip-tier-val" id="sipTotalInvested" style="color: var(--text-heading);">₹31.56 L</div>
                    <div class="sip-tier-sub">Principal from Savings</div>
                </div>
                <div class="sip-tier-card">
                    <div class="sip-tier-title">🏦 Fixed Deposit (7.0% p.a.)</div>
                    <div class="sip-tier-val" id="sipFdWealth" style="color: #94a3b8;">₹46.20 L</div>
                    <div class="sip-tier-sub" id="sipFdGain">Gain: +₹14.64 L</div>
                </div>
                <div class="sip-tier-card" style="border-color: #38bdf8;">
                    <div class="sip-tier-title" style="color: #38bdf8;">📈 Nifty 50 Index (12.5% p.a.)</div>
                    <div class="sip-tier-val" id="sipNiftyWealth" style="color: #38bdf8;">₹66.85 L</div>
                    <div class="sip-tier-sub" id="sipNiftyGain" style="color: #38bdf8;">Gain: +₹35.29 L</div>
                </div>
                <div class="sip-tier-card" style="border-color: #10b981; background: rgba(16, 185, 129, 0.06);">
                    <div class="sip-tier-title" style="color: #10b981;">🚀 Stock AI Alpha (18.5% p.a.)</div>
                    <div class="sip-tier-val" id="sipAlphaWealth" style="color: #10b981;">₹1.06 Cr</div>
                    <div class="sip-tier-sub" id="sipAlphaGain" style="color: #10b981; font-weight: 700;">Gain: +₹74.44 L</div>
                </div>
                <div class="sip-tier-card" style="border-color: #8b5cf6; background: rgba(139, 92, 246, 0.06);">
                    <div class="sip-tier-title" style="color: #a78bfa;">⚡ AI Outperformance Bonus</div>
                    <div class="sip-tier-val" id="sipAlphaBonus" style="color: #a78bfa;">+₹39.15 L</div>
                    <div class="sip-tier-sub">Extra Wealth vs Nifty 50</div>
                </div>
            </div>
        </div>

        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th class="sortable" onclick="sortTable(this, 0)">Fund Scheme &amp; House</th>
                        <th class="sortable" onclick="sortTable(this, 1)">Category</th>
                        <th class="sortable" onclick="sortTable(this, 2)">Live NAV (AMFI)</th>
                        <th class="sortable" onclick="sortTable(this, 3)">1Y Return</th>
                        <th class="sortable" onclick="sortTable(this, 4)">3Y CAGR</th>
                        <th class="sortable" onclick="sortTable(this, 5)">5Y CAGR</th>
                        <th class="sortable" onclick="sortTable(this, 6)">Sharpe</th>
                        <th class="sortable" onclick="sortTable(this, 7)">AUM</th>
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
                        <th class="sortable" onclick="sortTable(this, 2)">Setup Archetype</th>
                        <th class="sortable" onclick="sortTable(this, 3)">CMP</th>
                        <th class="sortable" onclick="sortTable(this, 4)">Multibagger Score</th>
                        <th class="sortable" onclick="sortTable(this, 5)">ROCE &amp; D/E</th>
                        <th>Qtr Inflection &amp; Flow</th>
                        <th class="sortable" onclick="sortTable(this, 7)">Target 1</th>
                        <th class="sortable" onclick="sortTable(this, 8)">Target 2</th>
                        <th class="sortable" onclick="sortTable(this, 9)">Stop Loss</th>
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
        <div id="portConcentrationBanner" class="conc-alert-box" style="display: none;"></div>

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
            <input type="date" id="portBuyDateInput" class="portfolio-input" title="Optional Buy Date (enables Indian STCG vs LTCG tax alerts)" style="width: 145px;">
            <button class="portfolio-add-btn" onclick="addPortfolioHolding()">+ Add Holding</button>
            <label class="action-btn" style="padding: 8px 14px; font-size: 12px; border-radius: 6px; background: #8b5cf6; color: #fff; cursor: pointer; display: inline-flex; align-items: center; gap: 6px;" title="Upload Zerodha, Groww, Angel One, or Upstox holdings CSV">
                📂 Import Broker CSV
                <input type="file" id="brokerCsvFileInput" accept=".csv" style="display: none;" onchange="handleBrokerCsvUpload(this)">
            </label>
            <button class="action-btn" onclick="syncAllPortfolioQuotes()" style="padding: 8px 14px; font-size: 12px; border-radius: 6px; background: #0284c7; color: #fff; border-color: #38bdf8;" title="Fetch latest live market CMP for all portfolio holdings">🔄 Sync Live CMP</button>
            <select id="portStrategyMode" class="portfolio-input" onchange="onPortfolioStrategyChange()" style="padding: 8px 10px; font-size: 12px; font-weight: 700; color: #38bdf8;" title="Switch between Long-Term Multibagger Compounder protection (200-EMA) and Tactical Swing (20/50-EMA)">
                <option value="long_term" selected>🏛️ Strategy: Long-Term Compounder (200-EMA)</option>
                <option value="swing">⚡ Strategy: Tactical Swing (20/50-EMA)</option>
            </select>
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

    <!-- Tab: Smart Money & Institutional FII/DII Flows -->
    <div id="view-institutional" class="view-panel" style="display: none;">
        <div style="background: var(--surface); border: 1px solid #38bdf8; border-radius: 12px; padding: 20px; margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
                <div>
                    <h3 style="margin: 0; font-size: 18px; font-weight: 800; color: var(--text-heading); display: flex; align-items: center; gap: 8px;">
                        🏛 Institutional Smart Money &amp; Derivatives Positioning
                    </h3>
                    <p style="margin: 4px 0 0; font-size: 12px; color: var(--text-muted);">
                        Real-time tracking of FII &amp; DII Cash Market flows and Nifty Option Chain derivatives sentiment.
                    </p>
                </div>
                <div>
                    <span class="badge" style="font-size: 13px; padding: 6px 14px; background: #0284c7;">
                        {inst_flow.get('sentiment_badge', '🔵 BALANCED')}
                    </span>
                </div>
            </div>
            <div style="margin-top: 12px; padding: 12px 16px; background: var(--bg); border-radius: 8px; font-size: 13px; color: var(--text);">
                💡 <b>Smart Money Thesis:</b> {inst_flow.get('sentiment_rationale', 'Institutional flows balanced around key strikes.')}
            </div>
        </div>

        <div class="table-container">
            <h4 style="margin: 0 0 12px 4px; font-size: 15px; font-weight: 700; color: var(--text-heading);">
                📊 15-Day FII &amp; DII Institutional Cash &amp; Derivatives Trading Log (₹ Crores)
            </h4>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>FII Cash Net</th>
                        <th>DII Cash Net</th>
                        <th>FII Index Futures</th>
                        <th>FII Index Options</th>
                        <th>FII Stock Futures</th>
                        <th>Nifty Close &amp; Change</th>
                    </tr>
                </thead>
                <tbody>
                    {fii_dii_rows}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Tab: Corporate Actions & Earnings Calendar -->
    <div id="view-corporate_actions" class="view-panel" style="display: none;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; margin-bottom: 24px;">
            <!-- Upcoming Dividends -->
            <div class="table-container" style="margin-bottom: 0;">
                <h4 style="margin: 0 0 12px 4px; font-size: 15px; font-weight: 700; color: #10b981; display: flex; align-items: center; gap: 6px;">
                    💰 Declared Upcoming Dividends
                </h4>
                <table>
                    <thead>
                        <tr>
                            <th>Company</th>
                            <th>Type</th>
                            <th>Ex-Date</th>
                            <th>Dividend</th>
                            <th>CMP</th>
                            <th>Yield</th>
                            <th>Announced</th>
                        </tr>
                    </thead>
                    <tbody>
                        {dividend_rows}
                    </tbody>
                </table>
            </div>

            <!-- Upcoming Quarterly Results -->
            <div class="table-container" style="margin-bottom: 0;">
                <h4 style="margin: 0 0 12px 4px; font-size: 15px; font-weight: 700; color: #38bdf8; display: flex; align-items: center; gap: 6px;">
                    📅 Upcoming Quarterly Results (Earnings Calendar)
                </h4>
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Company</th>
                            <th>Result Type</th>
                            <th>LTP</th>
                            <th>Market Cap</th>
                        </tr>
                    </thead>
                    <tbody>
                        {earnings_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Stock Splits & Rights Issues -->
        <div class="table-container">
            <h4 style="margin: 0 0 12px 4px; font-size: 15px; font-weight: 700; color: #a78bfa; display: flex; align-items: center; gap: 6px;">
                🔄 Stock Splits, Rights Issues &amp; Corporate Actions
            </h4>
            <table>
                <thead>
                    <tr>
                        <th>Company</th>
                        <th>Action Type</th>
                        <th>Ex-Date</th>
                        <th>Ratio</th>
                        <th>Announced</th>
                    </tr>
                </thead>
                <tbody>
                    {splits_rows}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Tab: AI Win-Rate & Track Record Scorecard -->
    <div id="view-scorecard" class="view-panel" style="display: none;">
        <div class="portfolio-summary-ribbon" style="margin-bottom: 20px;">
            <div class="index-card">
                <div class="index-name">🎯 Model Win Rate</div>
                <div class="index-val" style="color: #10b981;">{scorecard_data.get('win_rate_pct', 0.0)}%</div>
                <div class="index-chg" style="color: #10b981; font-weight: 700;">{scorecard_data.get('resolved_trades_count', 0)} Resolved / {scorecard_data.get('active_setups_count', 0)} Live</div>
            </div>
            <div class="index-card">
                <div class="index-name">⚡ Profit Factor</div>
                <div class="index-val" style="color: #38bdf8;">{scorecard_data.get('profit_factor', '0.00x')}</div>
                <div class="index-chg" style="color: var(--text-muted); font-size: 11px;">Gross Profit / Loss Ratio</div>
            </div>
            <div class="index-card">
                <div class="index-name">📈 Avg Gain on Winners</div>
                <div class="index-val" style="color: #10b981;">{scorecard_data.get('avg_gain_on_winners', '0.0%')}</div>
                <div class="index-chg" style="color: var(--text-muted); font-size: 11px;">Alpha per Winning Setup</div>
            </div>
            <div class="index-card">
                <div class="index-name">🛑 Avg Loss on Stops</div>
                <div class="index-val" style="color: #ef4444;">{scorecard_data.get('avg_loss_on_stops', '0.0%')}</div>
                <div class="index-chg" style="color: var(--text-muted); font-size: 11px;">Disciplined Stop Loss</div>
            </div>
            <div class="index-card">
                <div class="index-name">🏆 Top Single Gain</div>
                <div class="index-val" style="color: #f59e0b;">{scorecard_data.get('max_single_gain', '0.0%')}</div>
                <div class="index-chg" style="color: var(--text-muted); font-size: 11px;">Peak Multi-Bag Outlier</div>
            </div>
            <div class="index-card">
                <div class="index-name">📊 Alpha vs NIFTY 50</div>
                <div class="index-val" style="color: #a78bfa;">{scorecard_data.get('avg_alpha_vs_nifty', 'Tracking Live')}</div>
                <div class="index-chg" style="color: var(--text-muted); font-size: 11px;">Benchmark Outperformance</div>
            </div>
        </div>
        {archetype_strip_html}

        <div class="table-container">
            <h4 style="margin: 0 0 12px 4px; font-size: 15px; font-weight: 700; color: var(--text-heading);">
                📋 Historical Track Record &amp; Audited Setups (30 to 90-Day Rolling Log)
            </h4>
            <table>
                <thead>
                    <tr>
                        <th>Stock / Sector</th>
                        <th>Setup Model</th>
                        <th>Entry Date</th>
                        <th>Entry (₹)</th>
                        <th>Target 1 (₹)</th>
                        <th>Stop Loss (₹)</th>
                        <th>CMP / Exit (₹)</th>
                        <th>Max Gain (%)</th>
                        <th>Outcome Status</th>
                    </tr>
                </thead>
                <tbody>
                    {scorecard_rows}
                </tbody>
            </table>
        </div>
    </div>

    <!-- Tab: Top Gainers & Losers Detailed Tables -->
    <div id="view-movers" class="view-panel" style="display: none;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(420px, 1fr)); gap: 20px;">
            <!-- Top Gainers Table -->
            <div class="table-container" style="border: 1px solid rgba(16, 185, 129, 0.35);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding: 4px;">
                    <h3 style="margin: 0; font-size: 16px; font-weight: 800; color: #10b981; display: flex; align-items: center; gap: 8px;">
                        🟢 NSE Top Gainers Today
                    </h3>
                    <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid #10b981;">High Momentum</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 60px; text-align: center;">Sl No</th>
                            <th>Stock Name</th>
                            <th>CMP</th>
                            <th>% of Gain</th>
                            <th>Day Change (₹)</th>
                            <th>High</th>
                            <th>Low</th>
                            <th>Volume</th>
                            <th>Chart</th>
                        </tr>
                    </thead>
                    <tbody>
                        {gainer_rows}
                    </tbody>
                </table>
            </div>

            <!-- Top Losers Table -->
            <div class="table-container" style="border: 1px solid rgba(239, 68, 68, 0.35);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding: 4px;">
                    <h3 style="margin: 0; font-size: 16px; font-weight: 800; color: #ef4444; display: flex; align-items: center; gap: 8px;">
                        🔴 NSE Top Losers Today
                    </h3>
                    <span class="badge" style="background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid #ef4444;">Profit Booking</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th style="width: 60px; text-align: center;">Sl No</th>
                            <th>Stock Name</th>
                            <th>CMP</th>
                            <th>% of Loss</th>
                            <th>Day Change (₹)</th>
                            <th>High</th>
                            <th>Low</th>
                            <th>Volume</th>
                            <th>Chart</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loser_rows}
                    </tbody>
                </table>
            </div>
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
        <p style="font-size: 14px; font-weight: 800; color: #38bdf8; margin-bottom: 8px;">🚀 Application Designed and Developed by <b>Swamy Chouhan</b> • 📞 <b>9000632912</b></p>
        <p>{disclaimer}</p>
        <p style="margin-top: 6px;">Report generated by Indian Stock AI Agent (Senior Fund Manager Intelligence) &bull; Auto-syncs daily at 08:45 AM and 06:00 PM</p>
    </div>

    __SCRIPTS_PLACEHOLDER__
    <!-- Telegram Alerts Setup Modal -->
    <div id="telegramModal" class="modal-overlay" style="display: none;" onclick="closeTelegramModal(event)">
        <div class="modal-box" onclick="event.stopPropagation()" style="max-width: 580px;">
            <div class="modal-header">
                <div>
                    <h3 style="margin: 0; font-size: 18px; font-weight: 800; color: var(--text-heading); display: flex; align-items: center; gap: 8px;">
                        📱 Free Instant Phone Alerts via Telegram Bot
                    </h3>
                    <div style="font-size: 12px; color: var(--text-muted); margin-top: 3px;">
                        Get 08:45 AM Pre-Market intelligence, 06:00 PM market wrap &amp; emergency risk alerts on your phone.
                    </div>
                </div>
                <button class="modal-close-btn" onclick="closeTelegramModal()">✕</button>
            </div>
            <div style="padding: 20px; font-size: 13px; line-height: 1.6; color: var(--text);">
                <div style="background: rgba(14, 165, 233, 0.08); border: 1px solid #0ea5e9; border-radius: 8px; padding: 14px; margin-bottom: 16px;">
                    <b style="color: #38bdf8;">Why Telegram?</b> Telegram bots are 100% free, private, instant, and require no subscription or credit card.
                </div>
                
                <h4 style="margin: 12px 0 6px; color: var(--text-heading);">⚡ 2-Minute Quick Setup:</h4>
                <ol style="margin: 0 0 16px 20px; padding: 0;">
                    <li>Open Telegram and search for <b>@BotFather</b>. Send the command <code>/newbot</code>.</li>
                    <li>Choose a name (e.g. <i>My Stock AI</i>) and username. BotFather will give you an <b>HTTP API Token</b>.</li>
                    <li>Search for <b>@userinfobot</b> in Telegram and message it to see your personal numeric <b>Chat ID</b>.</li>
                    <li>Set environment variables on your machine (keeps tokens safe outside Git):
                        <pre style="background: var(--bg); padding: 10px; border-radius: 6px; font-size: 11px; margin-top: 6px; overflow-x: auto;">
STOCK_AI_TELEGRAM_ENABLED=true
STOCK_AI_TELEGRAM_TOKEN=your_bot_token_here
STOCK_AI_TELEGRAM_CHAT_ID=your_chat_id_here</pre>
                    </li>
                </ol>
                <div style="text-align: right; margin-top: 16px;">
                    <button class="action-btn" onclick="closeTelegramModal()" style="background: var(--primary); color: #090d16; font-weight: 700;">Got It, Close</button>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""
        import config
        web_dir = config.BASE_DIR / "web"
        web_dir.mkdir(parents=True, exist_ok=True)
        styles_file = web_dir / "styles.css"
        js_file = web_dir / "dashboard.js"
        stock_data_file = web_dir / "stock_data.js"

        stock_data_js = (
            f"const NSE_DATABASE = {nse_catalog_json};\n"
            f"const ENRICHED_PROFILES = {enriched_profiles_json};\n"
            f"const ALL_STOCK_CMPS = {all_stock_cmps_json};\n"
        )
        try:
            stock_data_file.write_text(stock_data_js, encoding="utf-8")
        except Exception as e:
            print(f"Error saving stock_data.js: {e}")

        css_content = styles_file.read_text(encoding="utf-8") if styles_file.exists() else ""
        js_content = js_file.read_text(encoding="utf-8") if js_file.exists() else ""

        external_html = (
            html_template
            .replace("__STYLES_PLACEHOLDER__", '<link rel="stylesheet" href="web/styles.css">')
            .replace(
                "__SCRIPTS_PLACEHOLDER__",
                '<script src="web/stock_data.js"></script>\n    <script src="web/dashboard.js"></script>',
            )
        )
        standalone_html = (
            html_template
            .replace("__STYLES_PLACEHOLDER__", f"<style>\n{css_content}\n    </style>")
            .replace("__SCRIPTS_PLACEHOLDER__", f"<script>\n{stock_data_js}\n{js_content}\n    </script>")
        )

        # Save externalized slim HTML inside repo (dashboard.html / index.html) and single-file standalone HTML elsewhere (Desktop)
        repo_root = config.BASE_DIR.resolve()
        for p in output_paths:
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
                use_external = (p.resolve().parent == repo_root) and styles_file.exists() and js_file.exists()
                content_to_write = external_html if use_external else standalone_html
                with open(p, "w", encoding="utf-8") as f:
                    f.write(content_to_write)
            except Exception as e:
                print(f"Error saving HTML to {p}: {e}")

        return standalone_html
