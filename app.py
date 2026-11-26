import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import json
from pathlib import Path

# Set page config
st.set_page_config(
    page_title="Indian Stock AI — 360° Senior Fund Manager & Momentum Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .metric-card {
        background-color: #1e293b;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 14px;
        border: 1px solid #334155;
    }
    .badge-buy {
        background-color: #16a34a;
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 700;
    }
    .badge-sell {
        background-color: #dc2626;
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 700;
    }
    .badge-hold {
        background-color: #d97706;
        color: white;
        padding: 4px 12px;
        border-radius: 6px;
        font-weight: 700;
    }
    .badge-momentum {
        background-color: #8b5cf6;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .badge-positive {
        color: #22c55e;
        font-weight: 700;
    }
    .badge-negative {
        color: #ef4444;
        font-weight: 700;
    }
    .explanation-box {
        background-color: #0f172a;
        border-left: 5px solid #3b82f6;
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 18px;
    }
</style>
""", unsafe_allow_html=True)

import config
from core.market_data import MarketDataManager
from core.synthesizer import Stock360Synthesizer
from core.bullish_scanner import BullishScanner
from core.momentum_screener import MomentumScreener
from core.fund_manager_radar import FundManagerRadar
from core.global_macro_news import GlobalMacroNewsAnalyst
from core.mutual_fund_analyst import MutualFundAnalyst
from core.ipo_analyst import IPOAnalyst
from core.fifty_two_week_high_tracker import FiftyTwoWeekHighTracker
from core.factor_screener import SmartFactorScreener
from core.hidden_gems_screener import HiddenGemsScreener
from scheduler import DailyAutomator

# Initialize core agents
@st.cache_resource
def get_agents():
    market_data = MarketDataManager()
    synthesizer = Stock360Synthesizer()
    scanner = BullishScanner()
    momentum_screener = MomentumScreener()
    fund_radar = FundManagerRadar()
    macro_news = GlobalMacroNewsAnalyst()
    mf_analyst = MutualFundAnalyst()
    ipo_analyst = IPOAnalyst()
    automator = DailyAutomator()
    tracker_52w = FiftyTwoWeekHighTracker()
    factor_screener = SmartFactorScreener()
    hidden_gems_screener = HiddenGemsScreener()
    return market_data, synthesizer, scanner, momentum_screener, fund_radar, macro_news, mf_analyst, ipo_analyst, automator, tracker_52w, factor_screener, hidden_gems_screener

market_data, synthesizer, scanner, momentum_screener, fund_radar, macro_news, mf_analyst, ipo_analyst, automator, tracker_52w, factor_screener, hidden_gems_screener = get_agents()

# Load 501+ NSE Universe from Backend Server Data for Autocomplete & Tracking
@st.cache_data
def load_nse_stock_options():
    try:
        stocks_path = config.DATA_DIR / "nse_stocks.json"
        if stocks_path.exists():
            with open(stocks_path, "r", encoding="utf-8") as f:
                stocks = json.load(f)
                options = [f"{s['symbol']} — {s['name']} ({s['sector']})" for s in stocks]
                sym_map = {s['symbol']: s for s in stocks}
                return options, sym_map
    except Exception:
        pass
    return [], {}

stock_catalog_options, nse_symbol_map = load_nse_stock_options()

# Sidebar
st.sidebar.title("🇮🇳 Indian Stock AI Agent")
st.sidebar.caption("Autonomous Senior Fund Manager & 360° Market Intelligence")

st.sidebar.markdown("""
### 🧠 System Capabilities:
- 🏆 **Multi-Timeframe Momentum**: 3M, 6M, 1Y, 2Y, 3Y, 5Y Trend Ranking
- 💎 **Hidden Gems (Small & Mid Cap)**: Auto-Updating High-ROCE, Low-Debt Compounders
- 🎯 **AI Fund Manager Radar**: Future Breakout & Pullback Setups
- 🔍 **360° Stock Deep Dive**: Technical + Fundamental + News
- 🌍 **Global Macro & News**: S&P 500, Crude, Yields & Stock Impact News
- 💼 **Mutual Fund Advisory**: Curated Funds + Institutional Rationale
""")

# Top Header with Refresh & Auto-Read Action
col_title, col_actions = st.columns([3, 1])
with col_title:
    st.markdown("### 🇮🇳 Indian Stock AI &bull; Senior Fund Manager & Momentum Intelligence")
with col_actions:
    if st.button("🔄 Refresh Live Feeds", use_container_width=True, type="primary"):
        st.cache_data.clear()
        try:
            m = MarketDataManager()
            m.get_benchmark_indices()
            st.toast("✅ Live market feeds & indices refreshed successfully!", icon="🚀")
        except Exception as e:
            st.toast(f"Feeds refreshed: {e}", icon="ℹ️")
        st.rerun()

# Automatically ensure local sync server is available in background for HTML dashboard integration
try:
    from core.sync_server import start_sync_server_thread
    if "sync_server_started" not in st.session_state:
        start_sync_server_thread(port=5005)
        st.session_state["sync_server_started"] = True
except Exception:
    pass

# Top Indices & Global Commodities Banner
try:
    indices = market_data.get_benchmark_indices()
    idx_items = list(indices.items())
    row1_items = idx_items[:7]
    row2_items = idx_items[7:]

    row1_cols = st.columns(len(row1_items))
    for col, (idx_name, idx_info) in zip(row1_cols, row1_items):
        chg_sign = "+" if idx_info["change"] >= 0 else ""
        val_prefix = "" if any(k in idx_name.upper() for k in ["VIX", "AI CATALYST"]) else "₹"
        col.metric(
            label=idx_name,
            value=f"{val_prefix}{idx_info['value']:,.2f}",
            delta=f"{chg_sign}{idx_info['change']} ({chg_sign}{idx_info['percent']}%)"
        )

    if row2_items:
        row2_cols = st.columns(len(row2_items))
        for col, (idx_name, idx_info) in zip(row2_cols, row2_items):
            chg_sign = "+" if idx_info["change"] >= 0 else ""
            val_prefix = "" if any(k in idx_name.upper() for k in ["VIX", "AI CATALYST"]) else "₹"
            col.metric(
                label=idx_name,
                value=f"{val_prefix}{idx_info['value']:,.2f}",
                delta=f"{chg_sign}{idx_info['change']} ({chg_sign}{idx_info['percent']}%)"
            )
except Exception as e:
    st.info(f"Live market feeds connecting ({e})...")

st.markdown("---")

# Navigation Tabs
tab_momentum, tab_hidden_gems, tab_factors, tab_52w, tab_radar, tab_deep_dive, tab_macro_news, tab_mutual_funds, tab_scanner, tab_ipo, tab_automation = st.tabs([
    "🏆 Super-Trend & Momentum Scanner (3M/6M/1Y/2Y/3Y)",
    "💎 Hidden Gems (Small & Mid Cap)",
    "💎 Factor & Value Finder (Vol/Promoter/PAT/ROCE/Val)",
    "🚀 52-Week High Leaders (Dynamic Live Radar)",
    "🎯 AI Fund Manager Radar (Monitored Stocks)",
    "🔍 360° Stock Deep Dive",
    "🌍 Global Macro & Stock Impact News",
    "💼 Mutual Fund Advisory & Rationale",
    "🚀 Bullish Breakout Scanner",
    "📋 IPO Intelligence & GMP",
    "⚙️ Automation & Settings"
])

# ==============================================================================
# TAB 1: MULTI-TIMEFRAME SUPER-TREND & MOMENTUM SCANNER (LAURUS LABS RESOLUTION)
# ==============================================================================
with tab_momentum:
    st.subheader("🏆 Multi-Timeframe Super-Trend & Momentum Screener")
    
    # Diagnostic explanation answering user's query directly
    st.markdown("""
    <div class="explanation-box">
        <h4>💡 Why was the previous system missing stocks like <b>Laurus Labs (+138.8% in 1Y)</b>?</h4>
        <ol style="margin-bottom: 0;">
            <li><b>Alphabetical Universe Slicing:</b> The original scanner sliced <code>universe[:30]</code> from an alphabetical list, which ended at 'A' (e.g. <code>AMBUJACEM</code>). Stocks starting with 'L' (like <b>LAURUSLABS</b>) or 'T' (like <b>TRENT</b>) were never even scanned!</li>
            <li><b>Absence of Multi-Timeframe Percentage Return Engine:</b> Standard technical oscillators (RSI, MACD) miss secular multi-baggers unless measured across <b>3 Months, 6 Months, 1 Year, 2 Years, 3 Years</b>.</li>
            <li><b>High P/E Valuation Penalty:</b> Turnaround growth compounders often trade at elevated trailing P/E ratios (Laurus Labs P/E is ~94) during aggressive expansion phases. Value filters penalized them instead of identifying institutional Stage-2 markup!</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    # Screener Controls
    m_col1, m_col2, m_col3 = st.columns([2, 2, 1.2])
    with m_col1:
        selected_horizon = st.selectbox(
            "Select Performance Timeframe:",
            ["1Y (1 Year Super-Movers)", "6M (6 Months Momentum)", "3M (3 Months Short-Term Trend)", "2Y (2 Years Compounders)", "3Y (3 Years Multibaggers)", "5Y (5 Years Secular Bulls)"],
            index=0
        )
        horizon_key = selected_horizon.split()[0]
    with m_col2:
        min_gain = st.slider("Minimum Gain Threshold (%):", min_value=-20, max_value=150, value=20, step=5)
    with m_col3:
        st.write("")
        st.write("")
        refresh_mom = st.button("🔄 Refresh Data", type="primary", use_container_width=True)

    with st.spinner("Screening Indian stock universe across 3M, 6M, 1Y, 2Y, 3Y, 5Y timeframes..."):
        all_momentum_stocks = momentum_screener.scan_universe(force_refresh=refresh_mom)
        filtered_stocks = momentum_screener.filter_by_horizon(all_momentum_stocks, horizon=horizon_key, min_gain=float(min_gain))

    if filtered_stocks:
        st.success(f"Discovered **{len(filtered_stocks)}** strongly trending stocks matching **{selected_horizon} >= {min_gain}%**.")

        # Top 3 Momentum Leaders Cards
        st.markdown("#### 🌟 Top Upside Movement Leaders")
        top_cards = st.columns(min(3, len(filtered_stocks)))
        for i, s in enumerate(filtered_stocks[:3]):
            with top_cards[i]:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="margin:0;">{s['symbol']}</h3>
                        <span class="badge-buy">{s['trend_status']}</span>
                    </div>
                    <p style="color:#94a3b8; margin:4px 0 10px 0;">{s['name']} ({s['sector']})</p>
                    <h2 style="margin:0; color:#38bdf8;">₹{s['cmp']:,.2f}</h2>
                    <hr style="border-color:#334155; margin:10px 0;"/>
                    <div style="display:flex; justify-content:space-between; font-size:0.9rem;">
                        <span><b>3M:</b> <span class="badge-positive">+{s['ret_3m']}%</span></span>
                        <span><b>6M:</b> <span class="badge-positive">+{s['ret_6m']}%</span></span>
                        <span><b>1Y:</b> <span class="badge-positive">+{s['ret_1y']}%</span></span>
                    </div>
                    <div style="display:flex; justify-content:space-between; font-size:0.9rem; margin-top:6px;">
                        <span><b>2Y:</b> <span class="badge-positive">+{s['ret_2y']}%</span></span>
                        <span><b>3Y:</b> <span class="badge-positive">+{s['ret_3y']}%</span></span>
                        <span><b>Dist from 52W:</b> {s['distance_from_52w_high']}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # Full Interactive Table
        st.markdown("#### 📊 Comprehensive Multi-Timeframe Ranking Table")
        table_rows = []
        for s in filtered_stocks:
            table_rows.append({
                "Symbol": s["symbol"],
                "Company": s["name"],
                "Sector": s["sector"],
                "CMP (₹)": f"₹{s['cmp']:,.2f}",
                "1M (%)": f"{'+' if s['ret_1m']>=0 else ''}{s['ret_1m']}%",
                "3M (%)": f"{'+' if s['ret_3m']>=0 else ''}{s['ret_3m']}%",
                "6M (%)": f"{'+' if s['ret_6m']>=0 else ''}{s['ret_6m']}%",
                "1Y (%)": f"{'+' if s['ret_1y']>=0 else ''}{s['ret_1y']}%",
                "2Y (%)": f"{'+' if s['ret_2y']>=0 else ''}{s['ret_2y']}%",
                "3Y (%)": f"{'+' if s['ret_3y']>=0 else ''}{s['ret_3y']}%",
                "5Y (%)": f"{'+' if s['ret_5y']>=0 else ''}{s['ret_5y']}%",
                "52W High (₹)": f"₹{s['fifty_two_week_high']:,.2f}",
                "Dist from 52W High": f"{s['distance_from_52w_high']}%",
                "Trend Status": s["trend_status"]
            })

        df_mom = pd.DataFrame(table_rows)
        st.dataframe(df_mom, use_container_width=True)
    else:
        st.warning(f"No stocks found with {selected_horizon} >= {min_gain}%. Try lowering the gain threshold.")

    # Universal Stock Status Quick-Checker across Backend Database
    st.markdown("---")
    with st.expander("🔎 Check Any Stock's Multi-Timeframe Status (e.g. TCS, INFY, WIPRO)", expanded=False):
        q_col1, q_col2 = st.columns([3, 1])
        with q_col1:
            quick_check_sym = st.selectbox(
                "Select / Search Stock from 501+ NSE Universe:",
                ["-- Select Stock --"] + stock_catalog_options,
                key="quick_mom_select"
            )
        with q_col2:
            st.write("")
            st.write("")
            btn_quick_mom = st.button("Inspect Multi-Horizon", type="primary", use_container_width=True)

        if quick_check_sym and not quick_check_sym.startswith("--"):
            sym_clean = quick_check_sym.split(" — ")[0].strip().upper()
            with st.spinner(f"Computing multi-horizon returns for {sym_clean}..."):
                res_tf = synthesizer.fetch_multi_timeframe_returns(sym_clean)
                overview_q = market_data.get_quote_and_overview(sym_clean)

            qc1, qc2, qc3, qc4, qc5 = st.columns(5)
            qc1.metric("CMP", f"₹{overview_q.get('currentPrice', 0):,.2f}")
            qc2.metric("3 Months", f"{'+' if res_tf.get('ret_3m', 0)>=0 else ''}{res_tf.get('ret_3m', 0)}%")
            qc3.metric("6 Months", f"{'+' if res_tf.get('ret_6m', 0)>=0 else ''}{res_tf.get('ret_6m', 0)}%")
            qc4.metric("1 Year", f"{'+' if res_tf.get('ret_1y', 0)>=0 else ''}{res_tf.get('ret_1y', 0)}%")
            qc5.metric("3 Years", f"{'+' if res_tf.get('ret_3y', 0)>=0 else ''}{res_tf.get('ret_3y', 0)}%")

            if res_tf.get("ret_1y", 0) < 0 or res_tf.get("dist_52w", 0) > 18.0:
                st.info(f"ℹ️ **Status for {sym_clean}:** 1-Year return is {res_tf.get('ret_1y')}% (trading {res_tf.get('dist_52w')}% below 52W high). It is currently in sideways consolidation/base-building and is omitted from top momentum breakout lists until Stage-2 momentum resumes.")
            else:
                st.success(f"✅ **Status for {sym_clean}:** In positive multi-horizon momentum (+{res_tf.get('ret_1y')}% 1Y). Trading {res_tf.get('dist_52w')}% from 52-week high.")

# ==============================================================================
# TAB 1A: SMALL & MID-CAP HIDDEN GEMS (AUTO-UPDATED WITH MARKET MOVEMENTS)
# ==============================================================================
with tab_hidden_gems:
    st.subheader("💎 Small & Mid-Cap Hidden Gems (Live Auto-Updating)")
    st.caption(
        "Screens Small Caps (<₹15,000 Cr) & Mid Caps (₹15,000–₹35,000 Cr) for ROCE >= 16%, low debt, "
        "strong 3Y cash conversion (>=0.65x), quarterly earnings acceleration, and reasonable GARP valuations. "
        "Prices, breakout status, entry zones, and rankings update dynamically with market movements."
    )

    hg_col1, hg_col2 = st.columns([3, 1.2])
    with hg_col2:
        refresh_gems = st.button("🔄 Rescan Hidden Gems (Live)", type="primary", use_container_width=True)

    with st.spinner("Syncing live market quotes & Small/Mid-Cap Hidden Gems..."):
        gems_data = hidden_gems_screener.scan_hidden_gems(force_refresh=refresh_gems, sync_live_prices=True)

    if gems_data:
        sm_cnt = sum(1 for g in gems_data if g.get("cap_tier") == "Small Cap")
        md_cnt = sum(1 for g in gems_data if g.get("cap_tier") == "Mid Cap")
        ready_cnt = sum(1 for g in gems_data if g.get("status_key") in ("breakout", "pullback"))
        avg_roce = round(sum(float(g.get("roce") or 0.0) for g in gems_data) / len(gems_data), 1)

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Total Gems Tracked", len(gems_data))
        k2.metric("Small Cap (<₹15k Cr)", sm_cnt)
        k3.metric("Mid Cap (₹15k–35k Cr)", md_cnt)
        k4.metric("Breakout / Pullback Ready", ready_cnt)
        k5.metric("Avg ROCE", f"{avg_roce}%")

        st.markdown("---")
        f1, f2, f3, f4 = st.columns([1.2, 1.4, 1.4, 1.2])
        with f1:
            cap_flt = st.selectbox("Cap Tier:", ["All Tiers", "Small Cap", "Mid Cap"], key="hg_cap_flt")
        with f2:
            status_opts = ["All Setups"] + sorted(list({g.get("setup_status", "") for g in gems_data if g.get("setup_status")}))
            status_flt = st.selectbox("Live Setup Status:", status_opts, key="hg_status_flt")
        with f3:
            sec_opts = ["All Sectors"] + sorted(list({g.get("sector", "") for g in gems_data if g.get("sector")}))
            sec_flt = st.selectbox("Sector:", sec_opts, key="hg_sec_flt")
        with f4:
            max_pe_flt = st.slider("Max P/E (x):", min_value=15, max_value=90, value=85, step=5, key="hg_pe_flt")

        filtered_gems = [
            g for g in gems_data
            if (cap_flt == "All Tiers" or g.get("cap_tier") == cap_flt)
            and (status_flt == "All Setups" or g.get("setup_status") == status_flt)
            and (sec_flt == "All Sectors" or g.get("sector") == sec_flt)
            and (float(g.get("pe") or 0.0) <= max_pe_flt)
        ]

        st.success(f"Showing **{len(filtered_gems)}** Small & Mid-Cap Hidden Gems (auto-ranked by Gem Score & live market movement).")
        if filtered_gems:
            gem_rows = []
            for g in filtered_gems:
                gem_rows.append({
                    "Symbol": g["symbol"],
                    "Company": g["name"],
                    "Cap Tier": g["cap_tier"],
                    "MCap (₹ Cr)": f"₹{g.get('mcap_cr', 0):,.0f}",
                    "Gem Score": f"{g['gem_score']}/10",
                    "Live CMP (₹)": f"₹{g['cmp']:,.2f}",
                    "Today %": f"{g.get('day_change_pct', 0):+.2f}%",
                    "Off 52W High": f"-{g.get('dist_52w', 0)}%",
                    "P/E | PEG": f"{g['pe']}x | {g['peg'] if g.get('peg') is not None else '—'}",
                    "ROCE / ROE": f"{g['roce']}% / {g['roe']}%",
                    "3Y CFO/PAT": f"{g['cfo_to_pat_3y']}x" if g.get("cfo_to_pat_3y") is not None else "—",
                    "Qtr PAT YoY": f"{g['qtr_pat_yoy_pct']:+.1f}%" if g.get("qtr_pat_yoy_pct") is not None else "—",
                    "RSI (14)": g.get("rsi", 50),
                    "Live Setup": g["setup_status"],
                    "Buy Zone": g["suggested_entry"],
                    "Target 1": f"₹{g['target_1']:,.2f}",
                    "Stop Loss": f"₹{g['stop_loss']:,.2f}",
                })
            st.dataframe(pd.DataFrame(gem_rows), use_container_width=True)

            st.markdown("#### 🔬 Deep-Dive Gem Cards & Live Levels")
            for g in filtered_gems:
                day_p = g.get("day_change_pct", 0.0)
                with st.expander(
                    f"💎 {g['symbol']} — {g['name']} ({g['cap_tier']} • ₹{g['cmp']:,.2f} [{day_p:+.2f}%]) | {g['setup_status']} | Score: {g['gem_score']}/10",
                    expanded=(g.get("status_key") == "breakout"),
                ):
                    gc1, gc2, gc3, gc4 = st.columns(4)
                    gc1.metric("Live CMP", f"₹{g['cmp']:,.2f}", f"{day_p:+.2f}% Today")
                    gc2.metric("MCap / Tier", f"₹{g.get('mcap_cr', 0):,.0f} Cr", g["cap_tier"])
                    gc3.metric("P/E & PEG", f"{g['pe']}x", f"PEG: {g.get('peg') if g.get('peg') is not None else 'N/A'}")
                    gc4.metric("ROCE / CFO-PAT", f"{g['roce']}%", f"3Y CFO/PAT: {g.get('cfo_to_pat_3y', 'N/A')}x")

                    st.write(
                        f"**EMAs:** 20 EMA ₹{g['ema_20']:,.2f} • 50 EMA ₹{g['ema_50']:,.2f} • 200 EMA ₹{g['ema_200']:,.2f} • "
                        f"**RSI:** `{g['rsi']}` • **1Y Return:** `{g['ret_1y']:+.1f}%` • **D/E:** `{g.get('debt_to_equity', 'N/A')}x`"
                    )
                    st.info(
                        f"**Actionable Levels (Auto-Updated):** Buy Zone `{g['suggested_entry']}` | "
                        f"Target 1: `₹{g['target_1']:,.2f}` | Target 2: `₹{g['target_2']:,.2f}` | "
                        f"Stop Loss: `₹{g['stop_loss']:,.2f}` (R:R `{g['risk_reward']}`)"
                    )
                    st.caption(f"**Key Strengths:** {g.get('thesis', '')}")
    else:
        st.info("Click 'Rescan Hidden Gems (Live)' to scan Small & Mid-Cap opportunities.")

# ==============================================================================
# TAB 1B: DEDICATED 5-FACTOR VALUE & PROMOTER INFLECTION FINDER
# ==============================================================================
with tab_factors:
    st.subheader("💎 5-Factor Value, Promoter Buying & Earnings Inflection Finder")
    st.caption(
        "Traces Volume Increasing + Promoter Shares Increasing + QoQ & YoY Profit Surge + "
        "ROCE & ROE Expansion + Undervalued / Low Multiple setups across 509 NSE stocks."
    )

    fc_col1, fc_col2 = st.columns([3, 1])
    with fc_col2:
        refresh_fac = st.button("🔄 Rescan 5-Factor Screener", type="primary", use_container_width=True)

    with st.spinner("Scanning NSE 509 universe for 5-Factor Value & Inflection setups..."):
        factor_rows_data = factor_screener.scan_factors(force_refresh=refresh_fac)

    if factor_rows_data:
        ff1, ff2, ff3, ff4, ff5 = st.columns(5)
        chk_vol = ff1.checkbox("📈 Volume Up", value=False)
        chk_prom = ff2.checkbox("🤝 Promoter Buying", value=False)
        chk_pat = ff3.checkbox("🚀 QoQ & YoY PAT Surge", value=False)
        chk_eff = ff4.checkbox("⚡ ROCE & ROE Up", value=False)
        chk_val = ff5.checkbox("💎 Low Valuation", value=False)

        filtered_fac = []
        for row in factor_rows_data:
            if chk_vol and not row.get("flag_vol"):
                continue
            if chk_prom and not row.get("flag_promoter"):
                continue
            if chk_pat and not row.get("flag_profit_high"):
                continue
            if chk_eff and not row.get("flag_eff_up"):
                continue
            if chk_val and not row.get("flag_low_value"):
                continue
            filtered_fac.append(row)

        st.success(f"Found **{len(filtered_fac)}** matching candidates (out of {len(factor_rows_data)} multi-signal stocks).")
        df_fac = []
        for r in filtered_fac:
            df_fac.append({
                "Symbol": r["symbol"],
                "Sector": r["sector"],
                "Matches": f"{r['matches_count']}/5",
                "Score": f"{r['factor_score']}/10",
                "CMP (₹)": r["cmp"],
                "4W Vol": f"{r['vol_trend_4w']}x",
                "Prom % (4Q Δ)": f"{r['promoter_pct']}% ({r['promoter_4q_delta']:+.2f}%)",
                "FII+DII 4Q Δ": f"{r['inst_4q_delta']:+.1f}%",
                "Qtr PAT QoQ": f"{r['qtr_pat_qoq_pct']:+.1f}%" if r.get("qtr_pat_qoq_pct") is not None else "—",
                "Qtr PAT YoY": f"{r['qtr_pat_yoy_pct']:+.1f}%" if r.get("qtr_pat_yoy_pct") is not None else "—",
                "ROCE (Δ)": f"{r['roce_latest']}% ({r['roce_delta']:+.1f}%)" if r.get("roce_delta") is not None else f"{r['roce_latest']}%",
                "ROE (Δ vs 3Y)": f"{r['roe_latest']}% ({r['roe_delta']:+.1f}%)" if r.get("roe_delta") is not None else f"{r['roe_latest']}%",
                "P/E | PEG": f"{r['pe']}x | {r['peg'] if r.get('peg') is not None else '—'}",
                "Valuation Tag": r["valuation_tag"],
            })
        if df_fac:
            st.dataframe(pd.DataFrame(df_fac), use_container_width=True)
    else:
        st.info("Click 'Rescan 5-Factor Screener' to run a fresh scan across NSE 509.")

# ==============================================================================
# TAB: 52-WEEK HIGH LEADERS (DYNAMIC LIVE RADAR & DEEP ANALYSIS)
# ==============================================================================
with tab_52w:
    st.subheader("🚀 Dynamic 52-Week High Breakout Radar & Deep Analysis")
    st.caption("Auto-updated dynamically from live NSE market feeds • Identifies Stage-2 breakouts within 3.5% of 52W high")

    col_btn, col_info = st.columns([1.2, 3])
    with col_btn:
        refresh_52w = st.button("🔄 Scan 52W Highs Freshly", type="primary", use_container_width=True)
    with col_info:
        st.info("💡 Stocks trading at 52-week highs indicate strong institutional sponsorship. This list updates daily from live market quotes.")

    try:
        stocks_52w = tracker_52w.scan_52_week_highs(force_refresh=refresh_52w)
    except Exception as e:
        stocks_52w = []
        st.error(f"Error scanning 52-week highs: {e}")

    if stocks_52w:
        # Top Metrics Bar
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Stocks Near 52W High", f"{len(stocks_52w)}")
        avg_dist = round(sum(s.get("dist_52w", 0) for s in stocks_52w) / len(stocks_52w), 2)
        m2.metric("Avg Distance from High", f"{avg_dist}%")
        avg_1y = round(sum(s.get("ret_1y", 0) for s in stocks_52w) / len(stocks_52w), 1)
        m3.metric("Avg 1-Year Gain", f"+{avg_1y}%")
        sec_counts = {}
        for s in stocks_52w:
            sec_counts[s.get("sector", "Other")] = sec_counts.get(s.get("sector", "Other"), 0) + 1
        top_sec = max(sec_counts.items(), key=lambda x: x[1])[0] if sec_counts else "Equities"
        m4.metric("Leading Breakout Sector", top_sec)

        st.markdown("---")

        # Filters
        c_filter1, c_filter2 = st.columns([2, 2])
        with c_filter1:
            qual_opts = ["All Breakout Types"] + sorted(list(set(s.get("quality", "") for s in stocks_52w if s.get("quality"))))
            selected_qual = st.selectbox("Filter by Breakout Quality:", qual_opts)
        with c_filter2:
            sec_opts = ["All Sectors"] + sorted(list(set(s.get("sector", "") for s in stocks_52w if s.get("sector"))))
            selected_sec = st.selectbox("Filter by Sector:", sec_opts)

        filtered_52w = stocks_52w
        if selected_qual != "All Breakout Types":
            filtered_52w = [s for s in filtered_52w if s.get("quality") == selected_qual]
        if selected_sec != "All Sectors":
            filtered_52w = [s for s in filtered_52w if s.get("sector") == selected_sec]

        # Leaderboard Table
        st.markdown("#### 📋 52-Week High Breakout Leaderboard")
        table_data = []
        for s in filtered_52w:
            table_data.append({
                "Symbol": s["symbol"],
                "Company Name": s["name"],
                "Sector": s["sector"],
                "CMP (₹)": f"₹{s['cmp']:,.2f}",
                "52W High (₹)": f"₹{s['h52']:,.2f}",
                "Dist from High": f"{s['dist_52w']}%",
                "1Y Return": f"+{s.get('ret_1y', 0)}%",
                "RSI (14)": s.get("rsi", 60),
                "Breakout Quality": s.get("quality", ""),
                "Suggested Buy Pocket": s.get("suggested_entry", "")
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True)

        # Deep Dive Analysis Cards
        st.markdown("---")
        st.markdown("#### 🔬 52-Week High Deep Analysis & Senior Fund Manager Strategy")

        for s in filtered_52w:
            with st.expander(f"🚀 {s['symbol']} — {s['name']} (CMP: ₹{s['cmp']:,.2f} | {s['dist_52w']}% from 52W High)", expanded=(s['dist_52w'] <= 1.0)):
                col_left, col_right = st.columns([2, 1.2])
                with col_left:
                    st.markdown(f"**Sector:** {s['sector']} &nbsp;|&nbsp; **Market Cap:** ₹{s.get('mcap_cr', 0):,.0f} Cr &nbsp;|&nbsp; **P/E:** {s.get('pe', 0)}x &nbsp;|&nbsp; **ROCE:** {s.get('roce', 0)}%")
                    st.markdown(f"""
                    <div style="background: #0f172a; border-left: 5px solid #38bdf8; padding: 14px 18px; border-radius: 8px; margin: 12px 0;">
                        <h5 style="color: #38bdf8; margin: 0 0 6px 0;">🏛️ Senior Fund Manager Breakout Rationale &amp; Strategy:</h5>
                        <p style="color: #cbd5e1; font-size: 14px; margin: 0; line-height: 1.6;">{s.get('buy_strategy')}</p>
                    </div>
                    """, unsafe_allow_html=True)

                with col_right:
                    st.markdown("**Actionable Buy Entry Setup:**")
                    st.success(f"**Suggested Entry:** {s.get('suggested_entry')}")
                    st.info(f"**Target 1 (+9%):** ₹{s.get('target_1'):,.2f}")
                    st.info(f"**Target 2 (+21%):** ₹{s.get('target_2'):,.2f}")
                    st.error(f"**Stop Loss:** ₹{s.get('stop_loss'):,.2f}")
                    st.caption(f"Risk : Reward Ratio: **{s.get('risk_reward')}**")
    else:
        st.info("No stocks currently within 3.5% of 52W high in the screened universe. Click 'Scan 52W Highs Freshly' to run a live scan.")

# ==============================================================================
# TAB 2: AI FUND MANAGER RADAR (MONITORED STOCKS FOR FUTURE SUGGESTIONS)
# ==============================================================================
with tab_radar:
    st.subheader("🎯 Agentic AI Senior Fund Manager Radar")
    st.write("Live institutional monitoring matrix of high-conviction stocks tracked for future breakout entries, pullback buys, and multi-year compounders.")

    # CIO Strategy Overview
    regime = fund_radar.get_cio_market_regime()
    with st.expander("🏛️ Chief Investment Officer (CIO) Stance & Allocation Framework", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Current Market Stance:** `{regime['market_stance']}`")
            st.markdown("**Dominant Institutional Themes:**")
            for t in regime["dominant_themes"]:
                st.write(f"- {t}")
        with c2:
            st.markdown("**Target Portfolio Sizing:**")
            for cat, alloc in regime["asset_allocation_rule"].items():
                st.write(f"- **{cat}:** `{alloc}`")
            st.info(f"💡 **Risk Creed:** {regime['risk_management_creed']}")

    monitored_stocks = fund_radar.get_monitored_stocks(sync_live_prices=True)

    # Filter / Search
    r_f1, r_f2 = st.columns([3, 1])
    with r_f1:
        st.markdown(f"Currently tracking **{len(monitored_stocks)}** institutional candidates for upcoming setups:")
    with r_f2:
        status_filter = st.selectbox("Filter by Setup Status:", ["All", "Active Breakout", "Pullback Buy", "Consolidation Watch"])

    for s in monitored_stocks:
        if status_filter != "All" and status_filter.lower() not in s["monitoring_status"].lower():
            continue

        with st.expander(f"📌 {s['symbol']} — {s['name']} | Status: {s['monitoring_status']} | CIO Score: {s['cio_conviction']}/10", expanded=True):
            sc1, sc2, sc3, sc4 = st.columns([1.5, 1.2, 1.2, 1.5])
            sc1.metric("Current Market Price (CMP)", f"₹{s.get('cmp', s['entry_trigger']):,.2f}", delta=f"{s.get('day_change_pct', 0.0)}%")
            sc2.metric("Target (3 Months)", f"₹{s['target_3m']:,.2f}", delta=f"R:R {s['risk_reward']}")
            sc3.metric("Target (1 Year)", f"₹{s['target_1y']:,.2f}", delta=f"Stop: ₹{s['stop_loss']:,.2f}")
            sc4.write(f"**Sector:** {s['sector']}")
            sc4.write(f"**Setup Type:** `{s['setup_type']}`")

            st.markdown("##### 🏛️ Senior Fund Manager Investment Thesis:")
            st.write(s["institutional_thesis"])

            st.markdown("##### 🚀 Key Forward Catalysts:")
            cat_cols = st.columns(len(s.get("catalysts", [])))
            for ci, cat_item in enumerate(s.get("catalysts", [])):
                with cat_cols[ci]:
                    st.info(f"⚡ {cat_item}")

    # Add custom stock to radar
    st.markdown("---")
    st.markdown("#### ➕ Add New Stock to AI Monitoring Radar")
    with st.form("add_radar_form"):
        ar1, ar2, ar3 = st.columns(3)
        with ar1:
            new_sym = st.text_input("Stock Symbol (e.g. DIXON, SUZLON, TATAINVEST):").upper().strip()
            new_setup = st.text_input("Setup Type (e.g. 52W High Breakout, 20 EMA Pullback):")
        with ar2:
            new_tgt3m = st.number_input("Target 3M (₹):", min_value=1.0, value=2500.0)
            new_tgt1y = st.number_input("Target 1Y (₹):", min_value=1.0, value=3000.0)
        with ar3:
            new_sl = st.number_input("Stop Loss (₹):", min_value=1.0, value=2200.0)
            new_thesis = st.text_area("Fund Manager Investment Thesis:")

        submitted = st.form_submit_button("Track in AI Radar", type="primary")
        if submitted and new_sym and new_thesis:
            ok = fund_radar.add_to_radar(new_sym, new_setup, new_thesis, new_tgt3m, new_tgt1y, new_sl)
            if ok:
                st.success(f"Added {new_sym} to the active AI Monitoring Radar!")
                st.rerun()
            else:
                st.warning(f"{new_sym} is already on the radar.")

# ==============================================================================
# TAB 3: 360° STOCK DEEP DIVE
# ==============================================================================
with tab_deep_dive:
    st.subheader("Autonomous 360° Stock Evaluation")
    st.write("Enter any Indian stock symbol (NSE/BSE) for real-time technical, momentum, fundamental, news, and CIO trade setup analysis.")

    # Popular suggestions chips
    st.write("Quick Select Popular Market Leaders & Key Stocks:")
    chip_cols = st.columns(8)
    sample_symbols = ["LAURUSLABS", "TCS", "DIXON", "TRENT", "SUZLON", "KAYNES", "INFY", "RELIANCE"]
    for i, sym in enumerate(sample_symbols):
        if chip_cols[i].button(sym, use_container_width=True):
            st.session_state["analyzed_stock"] = sym

    c1, c2 = st.columns([3, 1])
    with c1:
        default_sym = st.session_state.get("analyzed_stock", "LAURUSLABS")

        # Autocomplete search selectbox from 501+ NSE backend database
        selected_from_catalog = st.selectbox(
            "🔍 Search & Track 501+ NSE Stocks (Autocomplete from Backend Server Data):",
            ["-- Select from 501+ NSE Stocks --"] + stock_catalog_options,
            index=0,
            key="catalog_search_box"
        )
        if selected_from_catalog and not selected_from_catalog.startswith("--"):
            default_sym = selected_from_catalog.split(" — ")[0].strip().upper()
            st.session_state["analyzed_stock"] = default_sym

        selected_symbol = st.text_input("Or Enter Any NSE Stock Symbol Manually:", value=default_sym).upper().strip()
    with c2:
        st.write("")
        st.write("")
        analyze_btn = st.button("🚀 Analyze 360°", type="primary", use_container_width=True)

    if selected_symbol and (analyze_btn or st.session_state.get("analyzed_stock") == selected_symbol):
        st.session_state["analyzed_stock"] = selected_symbol
        with st.spinner(f"Agentic AI verifying 360° signals & multi-timeframe trend for {selected_symbol}..."):
            report = synthesizer.run_full_360_analysis(selected_symbol)

        overview = report["overview"]
        plan = report["trade_plan"]
        tech = report["technicals"]
        fund = report["fundamentals"]
        news = report["news_sentiment"]
        tf = report.get("timeframes", {})
        diag = report.get("status_diagnostic", {})

        # Header Card
        st.markdown(f"### {report['company_name']} ({report['symbol']})")
        st.caption(f"Sector: **{overview.get('sector')}** | Industry: **{overview.get('industry')}** | Currency: **{overview.get('currency')}**")

        # Stock Status & Radar Presence Diagnostic Banner (Answers user's query for non-bullish stocks like TCS)
        if diag:
            st.markdown(f"""
            <div style="background-color: #0f172a; border-left: 5px solid {diag.get('status_color', '#3b82f6')}; padding: 14px 18px; border-radius: 8px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                    <h4 style="margin: 0; color: {diag.get('status_color', '#38bdf8')}; display: flex; align-items: center; gap: 8px;">
                        <span>{diag.get('presence_label')}</span>
                    </h4>
                    <span style="font-size: 0.8rem; background: #1e293b; border: 1px solid #334155; padding: 3px 10px; border-radius: 12px; color: #94a3b8;">
                        Backend Server Database: Tracked
                    </span>
                </div>
                <p style="margin: 8px 0 6px 0; color: #e2e8f0; font-size: 0.95rem; line-height: 1.5;">
                    <b>Status Assessment &amp; Reason:</b><br/>{diag.get('reason')}
                </p>
                <div style="font-size: 0.88rem; color: #94a3b8;">
                    <b>Institutional Guidance:</b> {diag.get('action_advice')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not diag.get("in_radar") and diag.get("qualifying_triggers"):
                with st.expander("🎯 What triggers will elevate this stock into the AI Recommendation Radar?", expanded=False):
                    for trig in diag["qualifying_triggers"]:
                        st.write(f"- ⚡ {trig}")

        # Top Highlight: Verdict & Composite Score
        v_col1, v_col2, v_col3, v_col4, v_col5 = st.columns([2, 1.2, 1.2, 1.2, 1.2])
        with v_col1:
            badge_class = "badge-buy" if report["action_tag"] == "BUY" else ("badge-sell" if report["action_tag"] == "SELL" else "badge-hold")
            st.markdown(f"**AI Recommendation:** <span class='{badge_class}'>{report['verdict']}</span>", unsafe_allow_html=True)
            st.write(f"⏱️ **Horizon:** {plan['time_horizon']}")
        with v_col2:
            st.metric("360° Composite Score", f"{report['composite_score']} / 10")
        with v_col3:
            st.metric("Momentum Score", f"{report['breakdown_scores']['momentum_score']} / 10")
        with v_col4:
            st.metric("Technical Score", f"{report['breakdown_scores']['technical_score']} / 10")
        with v_col5:
            st.metric("Fundamental Score", f"{report['breakdown_scores']['fundamental_score']} / 10")

        # Multi-Timeframe Performance Ribbon
        st.markdown("#### 📈 Multi-Timeframe Performance Horizon")
        p_c1, p_c2, p_c3, p_c4, p_c5, p_c6, p_c7 = st.columns(7)
        p_c1.metric("1 Month", f"{'+' if tf.get('ret_1m', 0)>=0 else ''}{tf.get('ret_1m', 0)}%")
        p_c2.metric("3 Months", f"{'+' if tf.get('ret_3m', 0)>=0 else ''}{tf.get('ret_3m', 0)}%")
        p_c3.metric("6 Months", f"{'+' if tf.get('ret_6m', 0)>=0 else ''}{tf.get('ret_6m', 0)}%")
        p_c4.metric("1 Year", f"{'+' if tf.get('ret_1y', 0)>=0 else ''}{tf.get('ret_1y', 0)}%")
        p_c5.metric("2 Years", f"{'+' if tf.get('ret_2y', 0)>=0 else ''}{tf.get('ret_2y', 0)}%")
        p_c6.metric("3 Years", f"{'+' if tf.get('ret_3y', 0)>=0 else ''}{tf.get('ret_3y', 0)}%")
        p_c7.metric("5 Years", f"{'+' if tf.get('ret_5y', 0)>=0 else ''}{tf.get('ret_5y', 0)}%")

        # Senior Fund Manager Institutional Takeaway
        st.info(f"🏛️ **CIO Institutional Takeaway:** {report.get('cio_thesis', '')}")

        # Trade Setup Box
        st.markdown("#### 🎯 Actionable Trade Setup & Levels")
        t_col1, t_col2, t_col3, t_col4, t_col5 = st.columns(5)
        t_col1.metric("CMP", f"₹{plan['current_market_price']}")
        t_col2.metric("Suggested Entry Range", plan['suggested_entry'])
        t_col3.metric("Target 1 (Conservative)", f"₹{plan['target_1']}")
        t_col4.metric("Target 2 (Aggressive)", f"₹{plan['target_2']}")
        t_col5.metric("Stop Loss (Strict)", f"₹{plan['stop_loss']}", delta=f"R:R {plan['risk_reward_ratio']}")
        st.caption(f"💼 **Recommended Allocation:** {plan.get('portfolio_sizing')}")

        # Buy Entry Rationale & Strategy Guidance
        st.markdown("##### 🏛️ Buy Entry Rationale & Strategy Guidance")
        if report.get("action_tag") == "BUY":
            st.success(f"**Momentum & Compounder Entry:** High institutional conviction confirmed. Accumulate in tranches across **{plan['suggested_entry']}** with stop loss at **₹{plan['stop_loss']}** targeting **₹{plan['target_1']}** and **₹{plan['target_2']}**.")
        else:
            ret1y_val = tf.get('ret_1y', 0.0)
            st.info(f"**Value Accumulation / Base-Building Entry:** {report['symbol']} is currently consolidating ({ret1y_val:+.1f}% 1Y). For long-term investors, accumulating on dips near the 200 EMA support (**{plan['suggested_entry']}**) provides a margin of safety with stop loss at **₹{plan['stop_loss']}**. For momentum breakout traders, wait for a confirmed weekly close above **₹{plan['target_1']}** on expanding volume.")

        # Interactive Candlestick Chart
        candles = tech.get("df_indicators")
        if candles is not None and not candles.empty:
            st.markdown("#### 📊 Interactive Price Chart (with EMAs & Volume)")
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=candles['Date'],
                open=candles['Open'],
                high=candles['High'],
                low=candles['Low'],
                close=candles['Close'],
                name='Candlestick'
            ))
            if 'EMA_20' in candles.columns:
                fig.add_trace(go.Scatter(x=candles['Date'], y=candles['EMA_20'], line=dict(color='orange', width=1.5), name='20 EMA'))
            if 'EMA_50' in candles.columns:
                fig.add_trace(go.Scatter(x=candles['Date'], y=candles['EMA_50'], line=dict(color='cyan', width=1.5), name='50 EMA'))
            if 'EMA_200' in candles.columns:
                fig.add_trace(go.Scatter(x=candles['Date'], y=candles['EMA_200'], line=dict(color='red', width=1.5), name='200 EMA'))

            fig.update_layout(
                height=480,
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis_rangeslider_visible=False,
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)

        # 3-Column Breakdown (Technicals, Fundamentals, News)
        b_col1, b_col2, b_col3 = st.columns(3)

        with b_col1:
            st.markdown("#### ⚡ Technical Checklist")
            st.write(f"- **RSI (14):** `{tech.get('rsi')}`")
            st.write(f"- **20 EMA:** `₹{tech.get('ema_20')}`")
            st.write(f"- **50 EMA:** `₹{tech.get('ema_50')}`")
            st.write(f"- **200 EMA:** `₹{tech.get('ema_200')}`")
            st.write(f"- **Volume Ratio:** `{tech.get('volume_ratio')}x`")
            st.write("**Key Signals:**")
            for sig in tech.get("bullish_signals", []):
                st.write(f"✅ {sig}")
            for sig in tech.get("bearish_signals", []):
                st.write(f"⚠️ {sig}")

        with b_col2:
            st.markdown("#### 🏛️ Fundamental Health")
            metrics = fund.get("metrics", {})
            st.write(f"- **Trailing P/E:** `{metrics.get('stock_pe')}`")
            st.write(f"- **ROCE:** `{metrics.get('roce_pct')}%`")
            st.write(f"- **ROE:** `{metrics.get('roe_pct')}%`")
            st.write(f"- **Book Value:** `₹{metrics.get('book_value')}`")
            st.write(f"- **Dividend Yield:** `{metrics.get('dividend_yield_pct')}%`")
            st.write("**Key Strengths:**")
            for st_item in fund.get("strengths", []):
                st.write(f"⭐ {st_item}")
            for rf in fund.get("red_flags", []):
                st.write(f"🚩 {rf}")

        with b_col3:
            st.markdown("#### 📰 News & Catalysts")
            st.write(f"- **Sentiment:** `{news.get('sentiment_label')}`")
            st.write(f"- **Bullish Articles:** `{news.get('bullish_count')}` | **Bearish:** `{news.get('bearish_count')}`")
            st.write("**Recent Headlines:**")
            for art in news.get("articles", [])[:4]:
                st.markdown(f"- [{art['title']}]({art['link']}) *({art['source']})*")

        st.caption(report["disclaimer"])

# ==============================================================================
# TAB 4: GLOBAL MACRO & STOCK IMPACT NEWS
# ==============================================================================
with tab_macro_news:
    st.subheader("🌍 Global Market Pulse & Stock Impact News")
    st.write("Tracks global benchmark indices, commodities, bond yields, and assesses impact on Indian equities and specific stocks.")

    # Global Snapshot
    with st.spinner("Fetching global market indicators..."):
        macro_snap = macro_news.get_global_markets_snapshot()

    # Macro Indicators Cards
    st.markdown("#### 🌐 Global Benchmark Indices")
    gi_cols = st.columns(len(macro_snap["indices"]))
    for i, (g_name, g_data) in enumerate(macro_snap["indices"].items()):
        with gi_cols[i]:
            c_sign = "+" if g_data["change"] >= 0 else ""
            st.metric(
                label=g_name,
                value=f"{g_data['price']:,.2f}",
                delta=f"{c_sign}{g_data['change_pct']}%"
            )

    from core.global_macro_news import format_inr_number
    st.markdown("#### 🛢️ Macro Commodities, Yields, Bullion (24K/22K/Silver) & Currencies")
    macro_items = list(macro_snap["macro"].items())
    for row_start in range(0, len(macro_items), 5):
        row_chunk = macro_items[row_start:row_start + 5]
        mc_cols = st.columns(len(row_chunk))
        for col, (m_name, m_data) in zip(mc_cols, row_chunk):
            with col:
                chg_pct = m_data.get("change_pct", 0.0)
                chg_val = m_data.get("change", 0.0)
                pct_sign = "+" if chg_pct >= 0 else ""
                if "₹" in m_name:
                    val_str = f"₹{format_inr_number(m_data['price'], decimals=0)}"
                    chg_sign = "+" if chg_val >= 0 else "-"
                    delta_str = f"{chg_sign}{format_inr_number(abs(chg_val), decimals=0)} ({pct_sign}{chg_pct:.2f}%)" if chg_val != 0 else f"{pct_sign}{chg_pct:.2f}%"
                else:
                    val_str = f"{m_data['price']:,.2f}"
                    delta_str = f"{pct_sign}{chg_pct}%"
                st.metric(
                    label=m_name,
                    value=val_str,
                    delta=delta_str
                )

    # Fund Manager Macro Takeaways
    st.markdown("#### 🏛️ Senior Fund Manager Macro Interpretations")
    for t_item in macro_snap["fund_manager_takeaways"]:
        st.write(f"- {t_item}")

    st.markdown("---")
    st.markdown("#### ⚡ Real-Time Stock Impact News & Catalyst Scanner")
    news_stock_input = st.text_input("Enter Stock Symbol for Catalyst & Impact News:", value="LAURUSLABS").upper().strip()

    if news_stock_input:
        impact_news = macro_news.fetch_stock_impact_news(news_stock_input, limit=8)
        if impact_news:
            for item in impact_news:
                st.markdown(f"""
                <div class="metric-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="badge-momentum">{item['catalyst_type']}</span>
                        <span style="color:{item['impact_color']}; font-weight:700;">{item['impact']}</span>
                    </div>
                    <h4 style="margin:8px 0;"><a href="{item['link']}" target="_blank" style="text-decoration:none; color:#f8fafc;">{item['title']}</a></h4>
                    <p style="color:#94a3b8; font-size:0.85rem; margin:0;">Source: {item['source']} | Published: {item['pub_date']}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No breaking news catalysts found for {news_stock_input}.")

# ==============================================================================
# TAB 5: MUTUAL FUND ADVISORY & RATIONALE
# ==============================================================================
with tab_mutual_funds:
    st.subheader("💼 Institutional Mutual Fund Advisory & Recommendations")
    st.write("Curated mutual fund recommendations with live AMFI NAV tracking, real 1Y/3Y/5Y CAGR calculations, Sharpe ratios, and institutional manager reasoning.")

    # Category Filter & Live AMFI Refresh
    mf_c1, mf_c2, mf_c3 = st.columns([2, 1.5, 1])
    with mf_c1:
        selected_mf_cat = st.selectbox("Select Mutual Fund Category:", ["All", "Flexi Cap", "Mid Cap", "Small Cap", "Thematic / Healthcare", "Thematic / Manufacturing"])
    with mf_c2:
        risk_model = st.selectbox("View Asset Allocation Model:", ["Aggressive", "Moderate"])
    with mf_c3:
        st.write("")
        if st.button("🔄 Refresh Live AMFI NAVs"):
            with st.spinner("Fetching daily NAV series from AMFI (api.mfapi.in)..."):
                mf_analyst.get_all_funds(force_refresh=True)
            st.success("AMFI NAVs updated!")

    # Asset Allocation Model
    alloc_data = mf_analyst.get_portfolio_allocation_model(risk_model)
    with st.expander(f"📊 Recommended Portfolio Model: {alloc_data['profile']}", expanded=True):
        st.write(f"**SIP Strategy:** {alloc_data['sip_advice']}")
        a_cols = st.columns(len(alloc_data["allocation"]))
        for i, a_item in enumerate(alloc_data["allocation"]):
            with a_cols[i]:
                st.metric(label=a_item["category"], value=f"{a_item['percentage']}%", delta=a_item["purpose"])

    st.markdown("---")
    st.markdown("#### 🌟 Top Recommended Funds (Live AMFI NAV Enriched)")

    funds = mf_analyst.filter_funds(category=selected_mf_cat)
    for f in funds:
        nav_val = f.get("nav")
        nav_str = f"₹{float(nav_val):,.2f}" if nav_val else "N/A"
        nav_date = f.get("nav_date", "Baseline")
        nav_src = "AMFI Live" if f.get("is_live_nav") else "Baseline Ref"
        r1 = float(f.get("return_1y", 0.0))
        r3 = float(f.get("return_3y_cagr", 0.0))
        r5 = float(f.get("return_5y_cagr", 0.0))
        with st.expander(f"🏆 {f['name']} ({f['fund_house']}) — NAV: {nav_str} | 3Y CAGR: {r3:+.1f}% | Alpha: {f['alpha']}", expanded=True):
            fc1, fc2, fc3, fc4, fc5 = st.columns(5)
            fc1.metric("Live NAV", nav_str, nav_date)
            fc1.write(f"**Feed:** {nav_src}")
            fc2.metric("1-Year Return", f"{r1:+.1f}%")
            fc2.write(f"**Fund Manager:** {f['fund_manager']}")
            fc3.metric("3-Year CAGR", f"{r3:+.1f}%")
            fc3.write(f"**AUM:** ₹{f['aum_cr']:,.0f} Cr")
            fc4.metric("5-Year CAGR", f"{r5:+.1f}%")
            fc4.write(f"**Expense Ratio:** {f['expense_ratio_pct']}%")
            fc5.metric("Sharpe Ratio", f"{f['sharpe_ratio']}")
            fc5.write(f"**Min Horizon:** {f['min_horizon']}")

            st.markdown("##### 🏛️ Senior Fund Manager Investment Rationale (Why Recommended?):")
            st.info(f["cio_rationale"])

            st.write(f"**Top Holdings:** {', '.join(f['top_holdings'])}")
            st.caption(f"💡 **Suitable For:** {f['suitable_for']}")

# ==============================================================================
# TAB 6: BULLISH BREAKOUT SCANNER
# ==============================================================================
with tab_scanner:
    st.subheader("Autonomous Bullish Stock Scanner (360° Filtered)")
    st.write("Continuously scans the Indian stock universe (including top momentum leaders like Laurus Labs, Dixon, Trent, Suzlon) for breakout setups.")

    scan_col1, scan_col2 = st.columns([2, 1])
    with scan_col1:
        st.write("Click below to run a fresh scan of top Indian stocks:")
    with scan_col2:
        trigger_scan = st.button("🔄 Run Live Bullish Scan", type="primary")

    if trigger_scan or "latest_scan_results" not in st.session_state:
        with st.spinner("Two-Pass Multibagger Scanner analyzing all 509+ NSE stocks for Laurus-Type Inflections & Compounders..."):
            st.session_state["latest_scan_results"] = scanner.scan_market(max_stocks=509, max_workers=6)

    picks = st.session_state.get("latest_scan_results", [])

    if picks:
        st.success(f"Discovered **{len(picks)}** multibagger / Stage-2 bullish setups across the full 509-stock NSE universe.")
        
        table_data = []
        for p in picks:
            opm_exp = p.get("opm_expansion_bps")
            pat_yoy = p.get("qtr_pat_yoy_pct")
            table_data.append({
                "Symbol": p["symbol"],
                "Archetype": p.get("archetype_short", "Stage-2 Breakout"),
                "MCap Tier": p.get("mcap_tier", "Mid/Large Cap"),
                "Sector": p["sector"],
                "CMP (₹)": p["cmp"],
                "Conviction": f"{p['conviction_score']}/10",
                "ROCE (%)": p.get("roce_pct", 0.0),
                "D/E": p.get("debt_to_equity", "N/A"),
                "OPM Exp": f"{opm_exp:+.0f} bps" if opm_exp is not None else "—",
                "Qtr PAT YoY": f"{pat_yoy:+.1f}%" if pat_yoy is not None else "—",
                "1Y Return": f"{p.get('ret_1y', 0.0):+.1f}%",
                "Target 1 (₹)": p["target_1"],
                "Stop Loss (₹)": p["stop_loss"],
                "R:R": p["risk_reward"]
            })
        
        df_display = pd.DataFrame(table_data)
        st.dataframe(df_display, use_container_width=True)

        st.markdown("#### 🌟 Top Conviction Breakout Cards")
        card_cols = st.columns(3)
        for i, p in enumerate(picks[:6]):
            with card_cols[i % 3]:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{p['symbol']} <span class="badge-buy">BUY</span></h4>
                    <p style="margin: 0; color: #94a3b8;">{p['name']}</p>
                    <p><b>CMP:</b> ₹{p['cmp']} | <b>Conviction:</b> {p['conviction_score']}/10</p>
                    <p>🎯 <b>Target:</b> ₹{p['target_1']} | 🛑 <b>SL:</b> ₹{p['stop_loss']}</p>
                    <small>1Y Ret: +{p.get('ret_1y', 0.0)}% | RSI: {p['rsi']} | Vol Surge: {p['volume_surge']}x</small>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("No stocks passed the strict 360° bullish filter today. The AI is preserving capital.")

# ==============================================================================
# TAB 7: IPO INTELLIGENCE & GMP
# ==============================================================================
with tab_ipo:
    st.subheader("Indian IPO Intelligence & GMP Tracker")
    st.write("Real-time tracker of Mainboard & SME IPOs, price bands, Grey Market Premium (GMP), subscription demand, and AI verdicts.")

    ipo_summary = ipo_analyst.get_summary()
    i_col1, i_col2, i_col3, i_col4 = st.columns(4)
    i_col1.metric("Total Tracked", ipo_summary["total_tracked"])
    i_col2.metric("Upcoming IPOs", ipo_summary["upcoming_count"])
    i_col3.metric("Active / Open", ipo_summary["active_count"])
    i_col4.metric("High GMP (>20%)", ipo_summary["high_conviction_count"])

    st.markdown("---")
    for ipo in ipo_summary["ipos"]:
        with st.expander(f"📦 {ipo['name']} — {ipo['status']} | GMP: +{ipo.get('gmp_pct', 0)}% ({ipo['gmp_inr']})", expanded=True):
            ic1, ic2, ic3, ic4 = st.columns(4)
            ic1.write(f"**Sector:** {ipo['sector']}")
            ic1.write(f"**Category:** {ipo['category']}")
            ic2.write(f"**Price Band:** {ipo['price_band']}")
            ic2.write(f"**Lot Size:** {ipo['lot_size']} shares")
            ic3.write(f"**Issue Size:** ₹{ipo['issue_size_cr']} Cr")
            ic3.write(f"**Subscription:** {ipo['subscription_total']}")
            ic4.write(f"**Grey Market Premium:** {ipo['gmp_inr']} (+{ipo.get('gmp_pct', 0)}%)")
            ic4.write(f"**AI Verdict:** `{ipo['verdict']}`")
            st.info(f"💡 **AI Analysis:** {ipo['analysis']}")

# ==============================================================================
# TAB 8: AUTOMATION & SETTINGS
# ==============================================================================
with tab_automation:
    st.subheader("Autonomous Scheduler & Synchronization")
    st.write("Configure autonomous daily scans, post-market reports, and background intelligence triggers.")

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("#### ⏰ Daily Auto-Scan Schedule")
        st.write(f"- **Morning Sync:** `{config.SCHEDULE_CONFIG['MORNING_TIME']} AM`")
        st.write(f"- **Evening Sync (6:00 PM):** `{config.SCHEDULE_CONFIG['EVENING_TIME']}`")
        st.write(f"- **Daily Briefing Output:** `{config.REPORTS_DIR}`")

        if st.button("⚡ Run Full Daily Sync Now"):
            with st.spinner("Executing full market sync, IPO updates, and report generation..."):
                sync_result = automator.run_daily_sync()
                st.success("Daily synchronization completed successfully! Latest briefing saved.")

    with col_a2:
        st.markdown("#### 📡 Upstream Feed Health & Telegram Readiness")
        try:
            from core.feed_health import collect_feed_health
            fh = collect_feed_health()
            st.caption(f"Checked at {fh['checked_at']} — {fh['healthy_count']}/{fh['total_feeds']} feeds healthy")
            for fd in fh["feeds"]:
                st.write(f"- **{fd['feed']}**: `{fd['status']}` ({fd['age']}) — {fd['detail']}")
        except Exception as e:
            st.caption(f"Feed health unavailable: {e}")

        from core.telegram_alert_bot import TelegramAlertBot
        tg = TelegramAlertBot()
        st.write(
            f"- **Telegram Phone Alerts:** `{'ACTIVE' if tg.enabled else ('CONFIGURED (Disabled)' if tg.is_configured() else 'NOT CONFIGURED')}` "
            "(via `STOCK_AI_TELEGRAM_ENABLED`, `STOCK_AI_TELEGRAM_TOKEN`, `STOCK_AI_TELEGRAM_CHAT_ID`)"
        )

        st.markdown("#### ⚖️ Compliance & Disclaimers")
        st.warning(config.DISCLAIMER)
        st.markdown(f"""
        **Developer Information**:
        - Codebase Location: `{config.BASE_DIR}`
        - Exchange Feeds: NSE / BSE India & Global Benchmarks
        - Engine: Agentic Multi-Model Financial Analytics & Senior Fund Manager Intelligence
        """)
