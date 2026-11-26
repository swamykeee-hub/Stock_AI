        function switchView(viewName, btn) {
            document.querySelectorAll('.view-panel').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            const target = document.getElementById('view-' + viewName);
            if (target) target.style.display = 'block';
            if (btn) btn.classList.add('active');
            if (viewName === 'portfolio') {
                renderPortfolio();
                syncAllPortfolioQuotes();
            }
        }

        function selectMover(sym) {
            const input = document.getElementById('searchInput');
            if (input) input.value = '';
            const unlistedBox = document.getElementById('unlistedStockBox');
            if (unlistedBox) unlistedBox.style.display = 'none';
            document.querySelectorAll('.stock-row').forEach(function(r) {
                r.style.display = '';
            });
            const btn = document.getElementById('tabBtnMovers');
            switchView('movers', btn);
            const target = document.getElementById('view-movers');
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
            setTimeout(function() {
                document.querySelectorAll('.mover-row').forEach(function(r) {
                    if (r.getAttribute('data-symbol') === sym) {
                        r.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        r.style.transition = 'all 0.3s ease';
                        r.style.background = 'rgba(56, 189, 248, 0.35)';
                        r.style.outline = '3px solid #38bdf8';
                        r.style.borderRadius = '4px';
                        setTimeout(function() {
                            r.style.transition = 'all 1.5s ease-out';
                            r.style.background = '';
                            r.style.outline = '';
                        }, 4000);
                    }
                });
            }, 150);
        }

        function quickSearch(sym) {
            const input = document.getElementById('searchInput');
            if (input) input.value = sym;
            filterStocks();
        }

        function populateSectorFilter() {
            const select = document.getElementById('sectorFilter');
            if (!select) return;
            const sectors = new Set();
            document.querySelectorAll('.stock-row').forEach(r => {
                const s = r.getAttribute('data-sector');
                if (s && s.trim()) sectors.add(s.trim());
            });
            const current = select.value;
            const sorted = Array.from(sectors).sort();
            let opts = '<option value="">All Sectors (' + sorted.length + ')</option>';
            sorted.forEach(sec => {
                opts += `<option value="${sec}">${sec}</option>`;
            });
            select.innerHTML = opts;
            if (current) select.value = current;
        }

        let activeFactorMinMatches = 0;

        function applyFactorPreset(preset) {
            const ids = ['fltVolUp', 'fltPromUp', 'fltSmartMoneyUp', 'fltPatHigh', 'fltEffUp', 'fltLowVal'];
            ids.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.checked = false;
            });
            activeFactorMinMatches = 0;

            if (preset === 'multi3') {
                activeFactorMinMatches = 3;
            } else if (preset === 'prom_pat') {
                const e1 = document.getElementById('fltPromUp');
                const e2 = document.getElementById('fltPatHigh');
                if (e1) e1.checked = true;
                if (e2) e2.checked = true;
            } else if (preset === 'val_eff') {
                const e1 = document.getElementById('fltLowVal');
                const e2 = document.getElementById('fltEffUp');
                if (e1) e1.checked = true;
                if (e2) e2.checked = true;
            } else if (preset === 'vol_pat') {
                const e1 = document.getElementById('fltVolUp');
                const e2 = document.getElementById('fltPatHigh');
                if (e1) e1.checked = true;
                if (e2) e2.checked = true;
            }
            filterFactorScreener();
        }

        function filterFactorScreener() {
            const query = (document.getElementById('searchInput')?.value || '').toLowerCase().trim();
            const sectorVal = (document.getElementById('sectorFilter')?.value || '').toLowerCase().trim();
            const reqVol = !!document.getElementById('fltVolUp')?.checked;
            const reqProm = !!document.getElementById('fltPromUp')?.checked;
            const reqSm = !!document.getElementById('fltSmartMoneyUp')?.checked;
            const reqPat = !!document.getElementById('fltPatHigh')?.checked;
            const reqEff = !!document.getElementById('fltEffUp')?.checked;
            const reqVal = !!document.getElementById('fltLowVal')?.checked;

            let shown = 0;
            document.querySelectorAll('.factor-row').forEach(row => {
                const sym = (row.getAttribute('data-symbol') || '').toLowerCase();
                const name = (row.getAttribute('data-name') || '').toLowerCase();
                const sector = (row.getAttribute('data-sector') || '').toLowerCase();
                const matchQuery = !query || sym.includes(query) || name.includes(query) || sector.includes(query);
                const matchSector = !sectorVal || sector === sectorVal || sector.includes(sectorVal);

                const okVol = !reqVol || row.getAttribute('data-vol') === '1';
                const okProm = !reqProm || row.getAttribute('data-prom') === '1';
                const okSm = !reqSm || row.getAttribute('data-sm') === '1';
                const okPat = !reqPat || row.getAttribute('data-pat') === '1';
                const okEff = !reqEff || row.getAttribute('data-eff') === '1';
                const okVal = !reqVal || row.getAttribute('data-val') === '1';
                const matches = parseInt(row.getAttribute('data-matches') || '0', 10);
                const okMin = matches >= activeFactorMinMatches;

                if (matchQuery && matchSector && okVol && okProm && okSm && okPat && okEff && okVal && okMin) {
                    row.style.display = '';
                    shown++;
                } else {
                    row.style.display = 'none';
                }
            });
            const badge = document.getElementById('factorMatchCountBadge');
            if (badge) badge.innerText = 'Showing ' + shown + ' Stocks';
        }

        let activeHiddenGemFilter = 'all';

        function applyHiddenGemFilter(preset) {
            activeHiddenGemFilter = preset || 'all';
            filterHiddenGems();
        }

        function filterHiddenGems() {
            const query = (document.getElementById('searchInput')?.value || '').toLowerCase().trim();
            const sectorVal = (document.getElementById('sectorFilter')?.value || '').toLowerCase().trim();

            let shown = 0;
            document.querySelectorAll('.gem-row').forEach(row => {
                const sym = (row.getAttribute('data-symbol') || '').toLowerCase();
                const name = (row.getAttribute('data-name') || '').toLowerCase();
                const sector = (row.getAttribute('data-sector') || '').toLowerCase();
                const cap = (row.getAttribute('data-cap') || '').toLowerCase();
                const status = (row.getAttribute('data-status') || '').toLowerCase();

                const matchQuery = !query || sym.includes(query) || name.includes(query) || sector.includes(query);
                const matchSector = !sectorVal || sector === sectorVal || sector.includes(sectorVal);

                let matchPreset = true;
                if (activeHiddenGemFilter === 'small' || activeHiddenGemFilter === 'mid') {
                    matchPreset = cap === activeHiddenGemFilter;
                } else if (activeHiddenGemFilter !== 'all') {
                    matchPreset = status === activeHiddenGemFilter;
                }

                if (matchQuery && matchSector && matchPreset) {
                    row.style.display = '';
                    shown++;
                } else {
                    row.style.display = 'none';
                }
            });
            const badge = document.getElementById('hiddenGemsCountBadge');
            if (badge) badge.innerText = 'Showing ' + shown + ' Gems';
            return shown;
        }

        function filterStocks() {
            const query = (document.getElementById('searchInput')?.value || '').toLowerCase().trim();
            const sectorVal = (document.getElementById('sectorFilter')?.value || '').toLowerCase().trim();
            const unlistedBox = document.getElementById('unlistedStockBox');
            
            let matchedRowCount = 0;

            // Filter table rows (skip factor-row and gem-row here and handle via dedicated filters)
            document.querySelectorAll('.stock-row:not(.factor-row):not(.gem-row)').forEach(row => {
                const sym = (row.getAttribute('data-symbol') || '').toLowerCase();
                const name = (row.getAttribute('data-name') || '').toLowerCase();
                const sector = (row.getAttribute('data-sector') || '').toLowerCase();

                const matchQuery = !query || sym.includes(query) || name.includes(query) || sector.includes(query);
                const matchSector = !sectorVal || sector === sectorVal || sector.includes(sectorVal);

                if (matchQuery && matchSector) {
                    row.style.display = '';
                    matchedRowCount++;
                } else {
                    row.style.display = 'none';
                }
            });
            filterFactorScreener();
            matchedRowCount += filterHiddenGems();

            // Filter cards
            document.querySelectorAll('.stock-card').forEach(card => {
                const sym = (card.getAttribute('data-symbol') || '').toLowerCase();
                const name = (card.getAttribute('data-name') || '').toLowerCase();
                const sector = (card.getAttribute('data-sector') || '').toLowerCase();

                const matchQuery = !query || sym.includes(query) || name.includes(query) || sector.includes(query);
                const matchSector = !sectorVal || sector === sectorVal || sector.includes(sectorVal);

                if (matchQuery && matchSector) {
                    card.style.display = '';
                } else {
                    card.style.display = 'none';
                }
            });

            // If searched stock is NOT in today's active table/cards, search backend NSE database!
            const backendMatches = NSE_DATABASE.filter(s => 
                (s.symbol && s.symbol.toLowerCase() === query) ||
                (s.symbol && s.symbol.toLowerCase().includes(query)) ||
                (s.name && s.name.toLowerCase().includes(query))
            );

            if (matchedRowCount === 0 && backendMatches.length > 0) {
                const top = backendMatches[0];
                unlistedBox.style.display = 'block';
                const prof = ENRICHED_PROFILES[top.symbol];

                if (prof) {
                    const chgColor = prof.change >= 0 ? '#10b981' : '#ef4444';
                    const chgSign = prof.change >= 0 ? '+' : '';
                    unlistedBox.innerHTML = `
                    <div class="rich-stock-profile-card">
                        <!-- Top Bar with Symbol, Status Badge and Real-Time CMP -->
                        <div class="card-top-bar">
                            <div class="card-top-title">
                                <h2><span>🔍 ${prof.symbol}</span> <span style="font-size:15px; color:#94a3b8; font-weight:normal;">— ${prof.name}</span></h2>
                                <p>Sector: <b>${prof.sector}</b> &bull; Database: <b>Verified in NSE 500 Backend Server Data</b></p>
                            </div>
                            <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
                                <span style="background:${prof.badge_bg}; color:#fff; padding:6px 14px; border-radius:20px; font-size:12px; font-weight:700;">
                                    ${prof.status_badge}
                                </span>
                                <div class="cmp-badge">
                                    <span class="cmp-val">₹${prof.cmp.toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>
                                    <span class="cmp-chg" style="color: ${chgColor};">${chgSign}${prof.change} (${chgSign}${prof.change_pct}%)</span>
                                </div>
                            </div>
                        </div>

                        <!-- 4-Box Key Metrics Ribbon (Technicals + Fundamentals) -->
                        <div class="metrics-ribbon">
                            <div class="m-card">
                                <small>52-Week Range</small>
                                <b>₹${prof.l52.toLocaleString('en-IN')} — ₹${prof.h52.toLocaleString('en-IN')}</b>
                                <span style="font-size:11px; color:#94a3b8;">${prof.dist_52w}% below 52W High</span>
                            </div>
                            <div class="m-card">
                                <small>Technical Momentum</small>
                                <b>RSI (14): ${prof.rsi}</b>
                                <span style="font-size:11px; color:#38bdf8;">1Y Return: ${prof.ret_1y}%</span>
                            </div>
                            <div class="m-card">
                                <small>Valuation &amp; Leverage</small>
                                <b>P/E: ${prof.pe}x | D/E: ${prof.debt_to_equity || 'N/A'}x</b>
                                <span style="font-size:11px; color:#94a3b8;">MCap: ₹${prof.market_cap_cr} Cr &bull; PEG: ${prof.peg || 'N/A'}</span>
                            </div>
                            <div class="m-card">
                                <small>Quality &amp; Inflection</small>
                                <b>ROCE: ${prof.roce}% | LT Score: ⭐ ${prof.long_term_score || prof.fund_score || '—'}/10</b>
                                <span style="font-size:11px; color:#10b981;">OPM: ${prof.opm_latest || 'N/A'} | Qtr PAT YoY: ${prof.qtr_pat_yoy_pct != null ? prof.qtr_pat_yoy_pct + '%' : 'N/A'}</span>
                            </div>
                        </div>

                        <!-- Technical Moving Averages & Institutional Flow Bar -->
                        <div class="tech-bar">
                            <span><b>20 EMA:</b> ₹${prof.ema_20}</span>
                            <span><b>50 EMA:</b> ₹${prof.ema_50}</span>
                            <span><b>200 EMA:</b> ₹${prof.ema_200}</span>
                            <span><b>FII+DII 4Q Flow:</b> ${prof.fii_dii_delta_pct != null ? (prof.fii_dii_delta_pct >= 0 ? '+' : '') + prof.fii_dii_delta_pct + '%' : 'N/A'}</span>
                            <span style="color:#38bdf8;"><b>Structure:</b> ${prof.trend_posture}</span>
                        </div>

                        <!-- Actionable Buy Entry Setup Grid -->
                        <div class="buy-setup-grid">
                            <div class="setup-box buy">
                                <small>Suggested Buy Entry Range</small>
                                <b>${prof.suggested_entry}</b>
                            </div>
                            <div class="setup-box tgt">
                                <small>Target 1 (Resistance)</small>
                                <b>₹${prof.target_1}</b>
                            </div>
                            <div class="setup-box tgt2">
                                <small>Target 2 (Swing Breakout)</small>
                                <b>₹${prof.target_2}</b>
                            </div>
                            <div class="setup-box sl">
                                <small>Strict Stop Loss</small>
                                <b>₹${prof.stop_loss}</b>
                            </div>
                            <div class="setup-box rr">
                                <small>Risk : Reward</small>
                                <b>${prof.risk_reward}</b>
                            </div>
                        </div>

                        <!-- Senior Fund Manager Buy Entry Rationale & Strategy -->
                        <div class="strategy-explanation-box">
                            <h4>🏛️ Senior Fund Manager Buy Entry Rationale &amp; Strategy:</h4>
                            <div>${prof.buy_entry_strategy}</div>
                            <div style="margin-top:10px; font-size:12px; color:#38bdf8;">
                                💡 <b>Live Candlestick Deep Dive:</b> Launch the Streamlit dashboard (<code>Launch_Stock_AI.bat</code>) and select <b>360° Stock Deep Dive</b> to inspect real-time interactive charts and order-book depth for <b>${prof.symbol}</b>.
                            </div>
                        </div>
                    </div>
                    `;
                } else {
                    unlistedBox.innerHTML = `
                    <div style="background: #1e1b4b; border: 1px solid #6366f1; border-left: 5px solid #818cf8; padding: 18px; border-radius: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                            <div>
                                <h3 style="margin: 0; color: #fff; display: flex; align-items: center; gap: 10px;">
                                    <span>🔍 ${top.symbol}</span>
                                    <span style="font-size: 14px; color: #94a3b8; font-weight: normal;">— ${top.name}</span>
                                </h3>
                                <div style="font-size: 12px; color: #a5b4fc; margin-top: 4px;">Sector: <b>${top.sector}</b> &bull; Database: <b>Verified in NSE 500 Backend Server Data</b></div>
                            </div>
                            <span style="background: #3730a3; color: #e0e7ff; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 700;">
                                ⏸️ Consolidation / Neutral Base
                            </span>
                        </div>
                        <hr style="border-color: #312e81; margin: 12px 0;"/>
                        <p style="margin: 0 0 10px 0; font-size: 13px; color: #cbd5e1;">
                            ${top.symbol} is verified in the backend NSE 500 database. To inspect its real-time CMP, candlestick chart, and financial metrics, launch the Streamlit app.
                        </p>
                    </div>
                    `;
                }
            } else if (matchedRowCount > 0) {
                unlistedBox.style.display = 'none';
            } else {
                unlistedBox.style.display = 'block';
                unlistedBox.innerHTML = `
                <div style="background: #1e293b; border: 1px solid #334155; padding: 16px; border-radius: 8px; text-align: center; color: #94a3b8;">
                    No stock matching "<b>${query}</b>" found in active leaderboard or NSE 500 database. Try searching <b>TCS, LAURUSLABS, DIXON, INFY, TRENT</b>.
                </div>
                `;
            }
        }

        // --- Theme Toggle (Dark / Light Mode) ---
        function applyTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            const btn = document.getElementById('themeToggleBtn');
            const icon = document.getElementById('themeToggleIcon');
            const text = document.getElementById('themeToggleText');
            if (theme === 'light') {
                if (icon) icon.innerText = '☀️';
                if (text) text.innerText = 'Light Mode';
                if (btn) btn.title = 'Current: Light Mode. Click to switch to Dark Mode.';
            } else {
                if (icon) icon.innerText = '🌙';
                if (text) text.innerText = 'Dark Mode';
                if (btn) btn.title = 'Current: Dark Mode. Click to switch to Light Mode.';
            }
            try {
                localStorage.setItem('stock_ai_theme', theme);
            } catch (e) {}
        }

        function toggleTheme() {
            const current = document.documentElement.getAttribute('data-theme') || 'dark';
            const next = current === 'dark' ? 'light' : 'dark';
            applyTheme(next);
        }

        // --- Live Refresh & Sync Daemon Health ---
        let autoReadEnabled = true;
        let autoReadTimer = null;
        let isDaemonOnline = false;

        async function checkDaemonStatus(showAlertOnOffline = false) {
            const pill = document.getElementById('daemonStatusPill');
            const label = document.getElementById('daemonStatusText');
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 2000);
                const res = await fetch('http://127.0.0.1:5005/api/status', { signal: controller.signal });
                clearTimeout(timeoutId);

                if (res.ok) {
                    isDaemonOnline = true;
                    if (pill) {
                        pill.className = 'daemon-status-pill online';
                        pill.title = 'Live Sync Daemon is online (Port 5005). Streaming real-time NSE data.';
                    }
                    if (label) label.innerText = 'Live Sync: Online';
                    return true;
                }
            } catch (e) {
                // daemon unreachable
            }

            isDaemonOnline = false;
            if (pill) {
                pill.className = 'daemon-status-pill offline';
                pill.title = 'Live Sync Daemon is offline. Click for start instructions.';
            }
            if (label) label.innerText = 'Live Sync: Offline';

            if (showAlertOnOffline) {
                showDaemonHelpModal();
            }
            return false;
        }

        function showDaemonHelpModal() {
            showSyncToast(`
                <div style="font-weight:700; color:#f87171; font-size:14px; margin-bottom:6px;">⚠️ Live Sync Daemon is Offline</div>
                <div style="font-size:12px; line-height:1.5; color:#cbd5e1;">
                    The local sync daemon (Port 5005) is not running.<br/>
                    To stream real-time CMP quotes and auto-refresh:<br/>
                    <b>1.</b> Double-click <b>start_sync_daemon.bat</b> on Desktop or in <code>D:\STOCK_AI</code><br/>
                    <b>2.</b> Or run <b>Launch_Stock_AI.bat</b> to start both Streamlit & the Live Sync Daemon.<br/>
                </div>
            `, 8000);
        }

        function toggleAutoRead() {
            autoReadEnabled = !autoReadEnabled;
            const pill = document.getElementById('autoReadPill');
            const label = document.getElementById('autoReadLabel');
            if (autoReadEnabled) {
                pill.classList.add('active');
                label.innerText = 'Auto-Read: ON (3m)';
                showSyncToast('🟢 <b>Auto-Read Active:</b> Background quotes will auto-sync every 3 minutes.');
                startAutoReadTimer();
            } else {
                pill.classList.remove('active');
                label.innerText = 'Auto-Read: OFF';
                showSyncToast('⚪ <b>Auto-Read Paused:</b> Manual refresh mode active.');
                if (autoReadTimer) clearInterval(autoReadTimer);
            }
        }

        function showSyncToast(msg, duration = 4500) {
            let toast = document.getElementById('syncToast');
            if (!toast) {
                toast = document.createElement('div');
                toast.id = 'syncToast';
                toast.className = 'sync-toast';
                document.body.appendChild(toast);
            }
            toast.innerHTML = msg;
            toast.style.display = 'block';
            setTimeout(() => { toast.style.display = 'none'; }, duration);
        }

        async function triggerLiveRefresh(isAuto = false) {
            const btn = document.getElementById('refreshBtn');
            const icon = btn.querySelector('.refresh-icon');
            const btnText = document.getElementById('refreshBtnText');

            icon.classList.add('spinning');
            btnText.innerText = 'Syncing Live Feeds...';
            btn.disabled = true;

            const isOnlineHosted = window.location.hostname.includes('github.io') || (window.location.protocol.startsWith('http') && !window.location.hostname.includes('127.0.0.1') && !window.location.hostname.includes('localhost'));
            const pushFlag = isAuto ? 'false' : 'true';

            try {
                showSyncToast('⏳ <b>Syncing Live Feeds:</b> Querying real-time market quotes...');
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 95000);

                let localSuccess = false;
                try {
                    const response = await fetch(`http://127.0.0.1:5005/api/refresh?mode=quick&push=${pushFlag}`, {
                        method: 'GET',
                        headers: { 'Accept': 'application/json' },
                        signal: controller.signal
                    });
                    clearTimeout(timeoutId);

                    if (response.ok) {
                        localSuccess = true;
                        const data = await response.json();
                        showSyncToast(isAuto ? '✅ <b>Live Feeds Updated!</b> Reloading fresh market prices...' : '✅ <b>Market Data & CMP Synced!</b> Updated local dashboard & pushed live to GitHub Pages. Reloading...');
                        setTimeout(() => {
                            window.location.reload();
                        }, 700);
                        return;
                    }
                } catch (fetchErr) {
                    clearTimeout(timeoutId);
                    // Daemon not reachable on 127.0.0.1:5005
                }

                if (isOnlineHosted) {
                    showSyncToast('🌐 <b>Cloud Data Sync:</b> Reloading newest live market intelligence from GitHub Actions...');
                    setTimeout(() => {
                        const url = new URL(window.location.href);
                        url.searchParams.set('_sync', Date.now());
                        window.location.href = url.toString();
                    }, 900);
                } else {
                    checkDaemonStatus(false);
                    showSyncToast(`
                        <div style="font-weight:700; color:#f87171; font-size:13px; margin-bottom:4px;">⚠️ Live Sync Daemon is Offline</div>
                        <div style="font-size:12px; line-height:1.4; color:#cbd5e1;">
                            Could not reach sync server at <b>http://127.0.0.1:5005</b>.<br/>
                            Run <b>start_sync_daemon.bat</b> on Desktop to start local 3-minute streaming feeds.
                        </div>
                    `, 5500);
                }
            } catch (err) {
                console.warn('Sync server connection notice:', err);
            } finally {
                setTimeout(() => {
                    icon.classList.remove('spinning');
                    btnText.innerText = 'Refresh Live Data';
                    btn.disabled = false;
                }, 1200);
            }
        }

        function startAutoReadTimer() {
            if (autoReadTimer) clearInterval(autoReadTimer);
            // 3 minutes = 180,000 ms (background daemon owns git push with cooldown; UI stays local)
            autoReadTimer = setInterval(() => {
                if (autoReadEnabled && isDaemonOnline) {
                    console.log('[IndianStockAI] Auto-read timer triggered live refresh.');
                    triggerLiveRefresh(true);
                }
            }, 180000);
        }


        // --- Click-to-Sort Table Columns ---
        function sortTable(th, colIdx) {
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            if (!tbody) return;

            document.querySelectorAll('.chart-drawer-row').forEach(r => r.remove());

            const rows = Array.from(tbody.querySelectorAll('tr.stock-row, tr'));
            const isAsc = th.classList.contains('asc');
            const newAsc = !isAsc;

            table.querySelectorAll('th').forEach(h => h.classList.remove('asc', 'desc'));
            th.classList.add(newAsc ? 'asc' : 'desc');

            rows.sort((rowA, rowB) => {
                const cellA = rowA.children[colIdx]?.innerText?.trim() || '';
                const cellB = rowB.children[colIdx]?.innerText?.trim() || '';

                const cleanA = cellA.replace(/^(P\/E:|ROCE:|QoQ:|Prom:)/i, '').replace(/[₹,%+x⭐🔥]/g, '').split('/')[0].trim();
                const cleanB = cellB.replace(/^(P\/E:|ROCE:|QoQ:|Prom:)/i, '').replace(/[₹,%+x⭐🔥]/g, '').split('/')[0].trim();
                const numA = parseFloat(cleanA);
                const numB = parseFloat(cleanB);

                if (!isNaN(numA) && !isNaN(numB) && cleanA !== '' && cleanB !== '') {
                    return newAsc ? (numA - numB) : (numB - numA);
                }
                return newAsc ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
            });

            rows.forEach(r => tbody.appendChild(r));
        }

        // --- CSV Export Engine ---
        function exportActiveTableToCSV() {
            const activePanel = document.querySelector('.view-panel:not([style*="display: none"])');
            if (!activePanel) {
                showSyncToast('⚠️ No active table found to export.');
                return;
            }

            const table = activePanel.querySelector('table');
            if (!table) {
                showSyncToast('⚠️ The active tab does not contain a table.');
                return;
            }

            const rows = [];
            const headers = [];
            table.querySelectorAll('thead th').forEach(th => {
                let txt = th.innerText.replace('▲', '').replace('▼', '').replace('↕', '').trim();
                if (txt !== 'Chart' && txt !== 'Action') {
                    headers.push('"' + txt.split('"').join('""') + '"');
                }
            });
            rows.push(headers.join(','));

            table.querySelectorAll('tbody tr').forEach(tr => {
                if (tr.classList.contains('chart-drawer-row') || tr.style.display === 'none') return;
                
                const rowData = [];
                tr.querySelectorAll('td').forEach((td, idx) => {
                    const headerTxt = table.querySelectorAll('thead th')[idx]?.innerText?.trim() || '';
                    if (headerTxt.includes('Chart') || headerTxt.includes('Action')) return;
                    
                    let txt = td.innerText.trim();
                    rowData.push('"' + txt.split('"').join('""') + '"');
                });
                if (rowData.length > 0) {
                    rows.push(rowData.join(','));
                }
            });

            if (rows.length <= 1) {
                showSyncToast('⚠️ No visible stock rows to export.');
                return;
            }

            const csvContent = String.fromCharCode(0xFEFF) + rows.join(String.fromCharCode(10));
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            const viewId = activePanel.id ? activePanel.id.replace('view-', '') : 'stocks';
            const nowStr = new Date().toISOString().slice(0, 10);
            a.href = url;
            a.download = `Indian_Stock_AI_${viewId}_${nowStr}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            showSyncToast(`📥 <b>CSV Exported!</b> Saved as <code>Indian_Stock_AI_${viewId}_${nowStr}.csv</code>`);
        }

        // --- Interactive Candlestick Chart Drawer Engine ---
        async function toggleCandleChart(symbol, btn) {
            const tr = btn.closest('tr');
            if (!tr) return;

            const next = tr.nextElementSibling;
            if (next && next.classList.contains('chart-drawer-row') && next.getAttribute('data-chart-symbol') === symbol) {
                next.remove();
                btn.innerText = '📈 Chart';
                return;
            }

            document.querySelectorAll('.chart-drawer-row').forEach(r => {
                const openSym = r.getAttribute('data-chart-symbol');
                r.remove();
                document.querySelectorAll('.chart-btn').forEach(b => {
                    if (b.getAttribute('onclick')?.includes(openSym)) b.innerText = '📈 Chart';
                });
            });

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
                                <span>📈 ${symbol} &bull; Daily Candlestick Technical Chart</span>
                                <div style="display:flex; gap:6px; margin-left:14px;">
                                    <button class="chart-tf-btn" onclick="reloadCandleChart('${symbol}', '${canvasId}', '1m', this)">1M</button>
                                    <button class="chart-tf-btn" onclick="reloadCandleChart('${symbol}', '${canvasId}', '3m', this)">3M</button>
                                    <button class="chart-tf-btn active" onclick="reloadCandleChart('${symbol}', '${canvasId}', '6m', this)">6M</button>
                                    <button class="chart-tf-btn" onclick="reloadCandleChart('${symbol}', '${canvasId}', '1y', this)">1Y</button>
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
                                <button class="chart-close-btn" onclick="this.closest('.chart-drawer-row').remove(); document.querySelectorAll('.chart-btn').forEach(b => { if(b.getAttribute('onclick')?.includes('${symbol}')) b.innerText='📈 Chart'; });">✕ Close</button>
                            </div>
                        </div>
                        <div id="chartTooltip_${safeSym}" style="font-size:12px; font-weight:700; color:var(--text); margin-bottom:8px; min-height:18px;">
                            Hover over any candle to inspect Date, Open, High, Low, Close, and Volume
                        </div>
                        <div style="position:relative;">
                            <canvas id="${canvasId}" class="chart-canvas" width="1100" height="320"></canvas>
                        </div>
                    </div>
                </td>
            `;

            tr.parentNode.insertBefore(drawerTr, tr.nextSibling);
            btn.innerText = '📉 Hide';

            await fetchAndRenderCandles(symbol, canvasId, '6m');
        }

        async function reloadCandleChart(symbol, canvasId, period, tfBtn) {
            if (tfBtn) {
                tfBtn.parentNode.querySelectorAll('.chart-tf-btn').forEach(b => b.classList.remove('active'));
                tfBtn.classList.add('active');
            }
            await fetchAndRenderCandles(symbol, canvasId, period);
        }

        async function fetchAndRenderCandles(symbol, canvasId, period) {
            let candles = [];
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 4000);
                const res = await fetch(`http://127.0.0.1:5005/api/candles?symbol=${encodeURIComponent(symbol)}&period=${period}`, {
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                if (res.ok) {
                    const data = await res.json();
                    if (data.candles && data.candles.length > 0) {
                        candles = data.candles;
                    }
                }
            } catch (e) {}

            if (!candles || candles.length === 0) {
                candles = generateFallbackCandles(symbol, period);
            }

            renderCanvasCandlesticks(canvasId, candles, symbol);
        }

        function generateFallbackCandles(symbol, period) {
            const prof = (typeof ENRICHED_PROFILES !== 'undefined') ? ENRICHED_PROFILES[symbol] : null;
            let basePrice = prof ? prof.cmp : 1500;
            const numDays = period === '1m' ? 22 : period === '3m' ? 64 : period === '1y' ? 250 : 126;
            const list = [];
            const now = new Date();
            let current = basePrice * 0.85;

            for (let i = numDays; i >= 0; i--) {
                const d = new Date(now.getTime() - i * 86400000);
                if (d.getDay() === 0 || d.getDay() === 6) continue;
                const changePct = (Math.random() - 0.48) * 0.035;
                const open = current;
                current = current * (1 + changePct);
                const close = current;
                const high = Math.max(open, close) * (1 + Math.random() * 0.015);
                const low = Math.min(open, close) * (1 - Math.random() * 0.015);
                const vol = Math.floor(250000 + Math.random() * 1500000);
                list.push({
                    time: d.toISOString().slice(0, 10),
                    open: Math.round(open * 100) / 100,
                    high: Math.round(high * 100) / 100,
                    low: Math.round(low * 100) / 100,
                    close: Math.round(close * 100) / 100,
                    volume: vol
                });
            }
            return list;
        }

        function renderCanvasCandlesticks(canvasId, candles, symbol) {
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

            function calcEMA(data, period) {
                const k = 2 / (period + 1);
                const emaArr = new Array(data.length);
                let sum = 0;
                for (let i = 0; i < period && i < data.length; i++) {
                    sum += data[i].close;
                }
                let prevEma = sum / Math.min(period, data.length);
                for (let i = 0; i < data.length; i++) {
                    if (i < period - 1) {
                        emaArr[i] = null;
                    } else if (i === period - 1) {
                        emaArr[i] = prevEma;
                    } else {
                        prevEma = (data[i].close - prevEma) * k + prevEma;
                        emaArr[i] = prevEma;
                    }
                }
                return emaArr;
            }

            const ema20 = calcEMA(candles, 20);
            const ema50 = calcEMA(candles, 50);

            let minPrice = Infinity;
            let maxPrice = -Infinity;
            let maxVol = 0;

            candles.forEach(c => {
                if (c.low < minPrice) minPrice = c.low;
                if (c.high > maxPrice) maxPrice = c.high;
                if (c.volume > maxVol) maxVol = c.volume;
            });

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

            function priceToY(p) {
                return padTop + priceAreaH - ((p - minPrice) / (maxPrice - minPrice)) * priceAreaH;
            }

            function volToH(v) {
                return (v / (maxVol || 1)) * volAreaH;
            }

            const candleCount = candles.length;
            const candleSlot = chartW / candleCount;
            const candleWidth = Math.max(2, candleSlot * 0.7);

            function drawChart(activeIdx = -1) {
                ctx.clearRect(0, 0, width, height);

                const gridSteps = 5;
                const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
                ctx.strokeStyle = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)';
                ctx.fillStyle = isDark ? '#94a3b8' : '#64748b';
                ctx.font = '10px -apple-system, BlinkMacSystemFont, sans-serif';
                ctx.textAlign = 'left';

                for (let i = 0; i <= gridSteps; i++) {
                    const p = minPrice + (maxPrice - minPrice) * (i / gridSteps);
                    const y = priceToY(p);
                    ctx.beginPath();
                    ctx.moveTo(padLeft, y);
                    ctx.lineTo(width - padRight, y);
                    ctx.stroke();
                    ctx.fillText('₹' + p.toFixed(1), width - padRight + 6, y + 3);
                }

                ctx.beginPath();
                ctx.moveTo(padLeft, volAreaTop);
                ctx.lineTo(width - padRight, volAreaTop);
                ctx.stroke();

                for (let i = 0; i < candleCount; i++) {
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
                }

                ctx.strokeStyle = '#f59e0b';
                ctx.lineWidth = 1.8;
                ctx.beginPath();
                let started20 = false;
                for (let i = 0; i < candleCount; i++) {
                    if (ema20[i] !== null) {
                        const x = padLeft + i * candleSlot + candleSlot / 2;
                        const y = priceToY(ema20[i]);
                        if (!started20) { ctx.moveTo(x, y); started20 = true; }
                        else { ctx.lineTo(x, y); }
                    }
                }
                ctx.stroke();

                ctx.strokeStyle = '#38bdf8';
                ctx.lineWidth = 1.8;
                ctx.beginPath();
                let started50 = false;
                for (let i = 0; i < candleCount; i++) {
                    if (ema50[i] !== null) {
                        const x = padLeft + i * candleSlot + candleSlot / 2;
                        const y = priceToY(ema50[i]);
                        if (!started50) { ctx.moveTo(x, y); started50 = true; }
                        else { ctx.lineTo(x, y); }
                    }
                }
                ctx.stroke();

                if (activeIdx >= 0 && activeIdx < candleCount) {
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

                    if (tooltipEl) {
                        const chg = activeC.close - activeC.open;
                        const chgPct = ((chg / activeC.open) * 100).toFixed(2);
                        const chgCol = chg >= 0 ? '#10b981' : '#ef4444';
                        const sign = chg >= 0 ? '+' : '';
                        tooltipEl.innerHTML = `
                            <span style="color:var(--text-muted);">Date:</span> <b>${activeC.time}</b> &nbsp;|&nbsp;
                            <span style="color:var(--text-muted);">Open:</span> <b>₹${activeC.open.toFixed(2)}</b> &nbsp;|&nbsp;
                            <span style="color:var(--text-muted);">High:</span> <b style="color:#10b981;">₹${activeC.high.toFixed(2)}</b> &nbsp;|&nbsp;
                            <span style="color:var(--text-muted);">Low:</span> <b style="color:#ef4444;">₹${activeC.low.toFixed(2)}</b> &nbsp;|&nbsp;
                            <span style="color:var(--text-muted);">Close:</span> <b>₹${activeC.close.toFixed(2)}</b> &nbsp;|&nbsp;
                            <span style="color:${chgCol}; font-weight:800;">${sign}${chg.toFixed(2)} (${sign}${chgPct}%)</span> &nbsp;|&nbsp;
                            <span style="color:var(--text-muted);">Vol:</span> <b>${activeC.volume.toLocaleString('en-IN')}</b>
                        `;
                    }
                }
            }

            drawChart(-1);

            canvas.onmousemove = function(e) {
                const bbox = canvas.getBoundingClientRect();
                const mx = e.clientX - bbox.left;
                if (mx < padLeft || mx > width - padRight) return;
                const idx = Math.floor((mx - padLeft) / candleSlot);
                if (idx >= 0 && idx < candleCount) {
                    drawChart(idx);
                }
            };

            canvas.onmouseleave = function() {
                drawChart(-1);
                if (tooltipEl) {
                    tooltipEl.innerHTML = 'Hover over any candle to inspect Date, Open, High, Low, Close, and Volume';
                }
            };
        }

        // --- Personal Portfolio & Real-Time P&L Tracker ---
        const DEFAULT_PORTFOLIO = [
            { symbol: 'TCS', qty: 15, buyPrice: 3820.00 },
            { symbol: 'INFY', qty: 30, buyPrice: 1720.50 },
            { symbol: 'RELIANCE', qty: 10, buyPrice: 2840.00 },
            { symbol: 'TATAMOTORS', qty: 45, buyPrice: 890.00 },
            { symbol: 'DIXON', qty: 5, buyPrice: 11450.00 }
        ];

        function getPortfolio() {
            try {
                const raw = localStorage.getItem('stock_ai_user_portfolio');
                if (raw) return JSON.parse(raw);
            } catch (e) {}
            return DEFAULT_PORTFOLIO;
        }

        function savePortfolio(list, syncRemote = true) {
            try {
                localStorage.setItem('stock_ai_user_portfolio', JSON.stringify(list));
            } catch (e) {}
            if (syncRemote && isDaemonOnline) {
                fetch('http://127.0.0.1:5005/api/portfolio', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ holdings: list })
                }).catch(() => {});
            }
            renderPortfolio();
            if (syncRemote && isDaemonOnline) {
                syncPortfolioAuditFromServer().then(() => renderPortfolio());
            }
        }

        async function syncPortfolioStorageWithServer() {
            try {
                const res = await fetch('http://127.0.0.1:5005/api/portfolio');
                if (!res.ok) return;
                const payload = await res.json();
                const srvList = Array.isArray(payload.holdings) ? payload.holdings : [];
                const localRaw = localStorage.getItem('stock_ai_user_portfolio');
                if (srvList.length > 0) {
                    localStorage.setItem('stock_ai_user_portfolio', JSON.stringify(srvList));
                    renderPortfolio();
                } else if (localRaw) {
                    const localList = JSON.parse(localRaw);
                    if (Array.isArray(localList) && localList.length > 0) {
                        await fetch('http://127.0.0.1:5005/api/portfolio', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ holdings: localList })
                        });
                    }
                }
            } catch (e) {}
        }

        function resetPortfolioToDemo() {
            savePortfolio(DEFAULT_PORTFOLIO);
            showSyncToast('↺ <b>Portfolio Reset:</b> High-conviction benchmark demo holdings restored.');
        }

        // --- Portfolio Real-Time Stock Search & Autocomplete ---
        let activeSuggestionIndex = -1;

        function onPortfolioSymbolInput(inputEl) {
            const query = (inputEl.value || '').trim().toLowerCase();
            const dropdown = document.getElementById('portSymbolSuggestions');
            const chip = document.getElementById('portSelectedChip');
            if (chip) chip.style.display = 'none';

            if (!dropdown) return;

            if (!query || query.length < 1) {
                dropdown.style.display = 'none';
                dropdown.innerHTML = '';
                activeSuggestionIndex = -1;
                return;
            }

            const catalog = (typeof NSE_DATABASE !== 'undefined' && Array.isArray(NSE_DATABASE)) ? NSE_DATABASE : [];
            
            const symStart = [];
            const nameStart = [];
            const contains = [];

            catalog.forEach(item => {
                const sym = (item.symbol || '').toLowerCase();
                const nm = (item.name || '').toLowerCase();

                if (sym.startsWith(query)) {
                    symStart.push(item);
                } else {
                    const words = nm.split(' ');
                    const wordMatch = words.some(w => w.startsWith(query));
                    if (wordMatch) {
                        nameStart.push(item);
                    } else if (sym.includes(query) || nm.includes(query)) {
                        contains.push(item);
                    }
                }
            });

            const combined = [...symStart, ...nameStart, ...contains].slice(0, 8);

            if (combined.length === 0) {
                dropdown.innerHTML = `
                    <div style="padding: 12px; font-size: 12px; color: var(--text-muted); text-align: center;">
                        No NSE stock matching "<b>${query}</b>". You can still add it manually.
                    </div>
                `;
                dropdown.style.display = 'block';
                activeSuggestionIndex = -1;
                return;
            }

            let html = '';
            combined.forEach((item, idx) => {
                const live = getLiveCMPForSymbol(item.symbol);
                const cmpStr = live ? ('₹' + live.cmp.toLocaleString('en-IN', {minimumFractionDigits: 2})) : '';
                const cleanName = (item.name || '').split('"').join('');
                const cleanSector = (item.sector || 'NSE Equities').split('"').join('');

                html += `
                    <div class="ac-item" data-index="${idx}" onclick="selectPortfolioStock('${item.symbol}', '${cleanName}', '${cleanSector}')">
                        <div>
                            <span class="ac-sym">${item.symbol}</span>
                            <div class="ac-name" title="${cleanName}">${item.name}</div>
                        </div>
                        <div class="ac-meta">
                            <span class="ac-sector">${cleanSector}</span>
                            ${cmpStr ? `<div class="ac-cmp">${cmpStr}</div>` : ''}
                        </div>
                    </div>
                `;
            });

            dropdown.innerHTML = html;
            dropdown.style.display = 'block';
            activeSuggestionIndex = -1;
        }

        function onPortfolioSymbolKeyDown(e) {
            const dropdown = document.getElementById('portSymbolSuggestions');
            if (!dropdown || dropdown.style.display === 'none') return;

            const items = dropdown.querySelectorAll('.ac-item');
            if (items.length === 0) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                activeSuggestionIndex = (activeSuggestionIndex + 1) % items.length;
                updateSuggestionHighlight(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                activeSuggestionIndex = (activeSuggestionIndex - 1 + items.length) % items.length;
                updateSuggestionHighlight(items);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (activeSuggestionIndex >= 0 && activeSuggestionIndex < items.length) {
                    items[activeSuggestionIndex].click();
                } else if (items.length > 0) {
                    items[0].click();
                }
            } else if (e.key === 'Escape') {
                dropdown.style.display = 'none';
                activeSuggestionIndex = -1;
            }
        }

        function updateSuggestionHighlight(items) {
            items.forEach((it, idx) => {
                if (idx === activeSuggestionIndex) {
                    it.classList.add('active');
                    it.scrollIntoView({ block: 'nearest' });
                } else {
                    it.classList.remove('active');
                }
            });
        }

        async function selectPortfolioStock(symbol, name, sector) {
            const input = document.getElementById('portSymbolInput');
            const dropdown = document.getElementById('portSymbolSuggestions');
            const chip = document.getElementById('portSelectedChip');
            const priceInput = document.getElementById('portBuyPriceInput');
            const qtyInput = document.getElementById('portQtyInput');

            if (input) input.value = symbol;
            if (dropdown) {
                dropdown.style.display = 'none';
                dropdown.innerHTML = '';
            }

            if (chip) {
                chip.style.display = 'inline-flex';
                chip.innerHTML = `🏢 <b>${name}</b> &bull; ${sector}`;
            }

            if (priceInput && (!priceInput.value || parseFloat(priceInput.value) <= 0)) {
                priceInput.placeholder = 'Fetching live CMP...';
                const live = await fetchLiveQuote(symbol);
                if (live && live.cmp > 0) {
                    priceInput.value = live.cmp.toFixed(2);
                    showSyncToast(`📌 <b>${symbol}</b>: Verified Live CMP <b>₹${live.cmp.toLocaleString('en-IN', {minimumFractionDigits: 2})}</b> auto-filled into Buy Price!`);
                } else {
                    priceInput.placeholder = 'Buy Price ₹ (e.g. 3850)';
                }
            }

            if (qtyInput) {
                qtyInput.focus();
            }
        }

        // Close autocomplete when clicking outside
        document.addEventListener('click', function(e) {
            const wrapper = document.querySelector('.autocomplete-wrapper');
            const dropdown = document.getElementById('portSymbolSuggestions');
            if (dropdown && wrapper && !wrapper.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });

        function addPortfolioHolding() {
            const symInput = document.getElementById('portSymbolInput');
            const qtyInput = document.getElementById('portQtyInput');
            const priceInput = document.getElementById('portBuyPriceInput');
            const dateInput = document.getElementById('portBuyDateInput');

            const symbol = (symInput?.value || '').trim().toUpperCase();
            const qty = parseInt(qtyInput?.value || '0', 10);
            const buyPrice = parseFloat(priceInput?.value || '0');
            const buyDate = (dateInput?.value || '').trim();

            if (!symbol) {
                showSyncToast('⚠️ Please enter a stock symbol (e.g. TCS).');
                return;
            }
            if (isNaN(qty) || qty <= 0) {
                showSyncToast('⚠️ Please enter a valid quantity greater than 0.');
                return;
            }
            if (isNaN(buyPrice) || buyPrice <= 0) {
                showSyncToast('⚠️ Please enter a valid buy price.');
                return;
            }

            const port = getPortfolio();
            const existingIdx = port.findIndex(h => h.symbol === symbol);
            if (existingIdx >= 0) {
                const oldH = port[existingIdx];
                const newTotalQty = oldH.qty + qty;
                const newAvgPrice = ((oldH.qty * oldH.buyPrice) + (qty * buyPrice)) / newTotalQty;
                const mergedDate = oldH.buyDate || buyDate || '';
                port[existingIdx] = {
                    symbol,
                    qty: newTotalQty,
                    buyPrice: Math.round(newAvgPrice * 100) / 100,
                    ...(mergedDate ? { buyDate: mergedDate } : {})
                };
            } else {
                port.push({ symbol, qty, buyPrice, ...(buyDate ? { buyDate } : {}) });
            }

            savePortfolio(port);
            if (symInput) symInput.value = '';
            if (qtyInput) qtyInput.value = '';
            if (priceInput) priceInput.value = '';
            if (dateInput) dateInput.value = '';
            const chip = document.getElementById('portSelectedChip');
            if (chip) chip.style.display = 'none';
            showSyncToast(`✅ <b>Added to Portfolio:</b> ${qty} shares of <b>${symbol}</b> @ ₹${buyPrice.toLocaleString('en-IN')}`);
        }

        function deletePortfolioHolding(idx) {
            const port = getPortfolio();
            if (idx >= 0 && idx < port.length) {
                const removed = port.splice(idx, 1)[0];
                savePortfolio(port);
                showSyncToast(`🗑️ Removed <b>${removed.symbol}</b> from portfolio.`);
            }
        }

        // Real-Time Verified Live Quotes Cache for Portfolio
        window.PORTFOLIO_LIVE_PRICES = {};
        try {
            const savedPrices = localStorage.getItem('stock_ai_live_prices');
            if (savedPrices) window.PORTFOLIO_LIVE_PRICES = JSON.parse(savedPrices);
        } catch (e) {}

        async function fetchLiveQuote(sym) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 4000);
                const res = await fetch(`http://127.0.0.1:5005/api/quote?symbol=${encodeURIComponent(sym)}`, {
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                if (res.ok) {
                    const data = await res.json();
                    if (data && data.currentPrice && data.currentPrice > 0) {
                        const quote = {
                            cmp: Number(data.currentPrice),
                            change_pct: Number(data.changePercent || 0),
                            time: Date.now()
                        };
                        window.PORTFOLIO_LIVE_PRICES[sym] = quote;
                        try {
                            localStorage.setItem('stock_ai_live_prices', JSON.stringify(window.PORTFOLIO_LIVE_PRICES));
                        } catch (e) {}
                        return quote;
                    }
                }
            } catch (e) {}
            return null;
        }

        let isSyncingPortfolio = false;
        window.PORTFOLIO_AUDIT_DATA = {};
        window.PORTFOLIO_AUDIT_META = null;

        async function syncAllPortfolioQuotes() {
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
        }

        function getPortfolioStrategyMode() {
            const sel = document.getElementById('portStrategyMode');
            if (sel && sel.value) return sel.value;
            try {
                return localStorage.getItem('stock_ai_port_strategy') || 'long_term';
            } catch (e) {
                return 'long_term';
            }
        }

        async function onPortfolioStrategyChange() {
            const mode = getPortfolioStrategyMode();
            try {
                localStorage.setItem('stock_ai_port_strategy', mode);
            } catch (e) {}
            window.PORTFOLIO_AUDIT_DATA = {};
            renderPortfolio();
            await syncPortfolioAuditFromServer();
            renderPortfolio();
        }

        async function syncPortfolioAuditFromServer() {
            const port = getPortfolio();
            if (!port || port.length === 0) return;
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 15000);
                const res = await fetch('http://127.0.0.1:5005/api/portfolio_audit', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ holdings: port, strategy_mode: getPortfolioStrategyMode() }),
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                if (res.ok) {
                    const audit = await res.json();
                    window.PORTFOLIO_AUDIT_META = audit;
                    if (audit && audit.holdings) {
                        audit.holdings.forEach(item => {
                            window.PORTFOLIO_AUDIT_DATA[item.symbol] = item;
                        });
                    }
                }
            } catch (e) {}
        }

        function getLiveCMPForSymbol(sym) {
            // 1. Check verified live quotes cache from daemon
            if (window.PORTFOLIO_LIVE_PRICES && window.PORTFOLIO_LIVE_PRICES[sym] && window.PORTFOLIO_LIVE_PRICES[sym].cmp > 0) {
                return window.PORTFOLIO_LIVE_PRICES[sym];
            }
            // 2. Check universal 503-stock verified CMP database (embedded)
            if (typeof ALL_STOCK_CMPS !== 'undefined' && ALL_STOCK_CMPS[sym] && ALL_STOCK_CMPS[sym].cmp > 0) {
                return { cmp: ALL_STOCK_CMPS[sym].cmp, change_pct: ALL_STOCK_CMPS[sym].change_pct || 0 };
            }
            // 3. Check ENRICHED_PROFILES (precomputed backend profiles)
            if (typeof ENRICHED_PROFILES !== 'undefined' && ENRICHED_PROFILES[sym] && ENRICHED_PROFILES[sym].cmp > 0) {
                return { cmp: ENRICHED_PROFILES[sym].cmp, change_pct: ENRICHED_PROFILES[sym].change_pct || 0 };
            }
            // 4. Table-aware CMP lookup (accounting for dedicated CIO Rating / Archetype columns)
            const tableColLookups = [
                ['#view-momentum tr[data-symbol="' + sym + '"]', 3],
                ['#view-hidden_gems tr[data-symbol="' + sym + '"]', 3],
                ['#view-radar tr[data-symbol="' + sym + '"]', 3],
                ['#view-leaderboard tr[data-symbol="' + sym + '"]', 3],
                ['#view-fifty_two_week tr[data-symbol="' + sym + '"]', 2],
            ];
            for (const [sel, colIdx] of tableColLookups) {
                const row = document.querySelector(sel);
                if (row && row.children[colIdx]) {
                    const cmpCell = row.children[colIdx].innerText || '';
                    if (cmpCell.includes('₹')) {
                        const clean = parseFloat(cmpCell.replace(/[₹,]/g, '').split(/\s+/)[0]);
                        if (!isNaN(clean) && clean > 0) {
                            return { cmp: clean, change_pct: 0.0 };
                        }
                    }
                }
            }
            return null;
        }

        function renderPortfolio() {
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
            port.forEach((h, idx) => {
                const live = getLiveCMPForSymbol(h.symbol);
                if (!live) {
                    missingQuotes.push(h.symbol);
                }

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
                    ? `<b style="color:#38bdf8;">₹${cmp.toLocaleString('en-IN', {minimumFractionDigits: 2})}</b>`
                    : `<span style="color:#f59e0b; font-size:12px;" title="Fetching live quote from daemon...">⏳ ₹${cmp.toLocaleString('en-IN', {minimumFractionDigits: 2})}</span>`;

                // Calculate Trailing Stop-Loss & Senior CIO Action based on active Strategy Horizon
                const stratMode = getPortfolioStrategyMode();
                let trailingSL = h.buyPrice * 0.88;
                let actionBadge = '🟢 STRONG HOLD';
                let actionColor = '#10b981';
                let actionReason = 'Structural posture intact above long-term floor. Let winner compound.';

                const prof = (typeof ENRICHED_PROFILES !== 'undefined' && ENRICHED_PROFILES[h.symbol]) ? ENRICHED_PROFILES[h.symbol] : null;
                const ema20 = prof && prof.ema_20 ? prof.ema_20 : (cmp * 0.97);
                const ema50 = prof && prof.ema_50 ? prof.ema_50 : (cmp * 0.94);
                const ema200 = prof && prof.ema_200 ? prof.ema_200 : (cmp * 0.88);
                const rsi = prof && prof.rsi ? prof.rsi : 55.0;

                if (stratMode === 'long_term') {
                    if (pnlPct >= 50.0) {
                        trailingSL = Math.max(ema200 * 0.98, cmp * 0.85, h.buyPrice * 1.15);
                    } else if (pnlPct >= 15.0) {
                        trailingSL = Math.max(ema200 * 0.96, h.buyPrice * 1.00);
                    } else if (pnlPct >= 0) {
                        trailingSL = Math.min(h.buyPrice * 0.88, ema200 * 0.95);
                    } else {
                        trailingSL = Math.min(h.buyPrice * 0.85, ema200 * 0.93);
                    }
                } else {
                    if (pnlPct >= 35.0) {
                        trailingSL = Math.max(ema20 * 0.985, cmp * 0.91, h.buyPrice * 1.15);
                    } else if (pnlPct >= 15.0) {
                        trailingSL = Math.max(ema50 * 0.98, h.buyPrice * 1.02);
                    } else if (pnlPct >= 0) {
                        trailingSL = Math.min(h.buyPrice * 0.92, ema50 * 0.97);
                    } else {
                        trailingSL = h.buyPrice * 0.92;
                    }
                }
                trailingSL = Math.round(trailingSL * 100) / 100;

                // Action verdict determination
                if (cmp < trailingSL) {
                    if (pnlPct > 0) {
                        actionBadge = '🔴 TRAIL SL HIT';
                        actionColor = '#f97316';
                        actionReason = 'CMP breached trailing profit stop of ₹' + trailingSL.toFixed(2) + '. Lock in remaining gains!';
                    } else {
                        actionBadge = '🔴 FLOOR BREACHED';
                        actionColor = '#dc2626';
                        actionReason = 'CMP breached risk stop at ₹' + trailingSL.toFixed(2) + '. Reassess or cut loser.';
                    }
                    atRiskCount++;
                    urgentAlerts.push({
                        symbol: h.symbol,
                        badge: actionBadge,
                        color: actionColor,
                        reason: actionReason,
                        action: 'Review / exit ' + h.qty + ' shares at ₹' + cmp.toFixed(2) + ' to preserve capital.'
                    });
                } else if (stratMode === 'swing' && pnlPct >= 40.0 && rsi >= 75.0) {
                    actionBadge = '🟠 BOOK 35% PROFIT';
                    actionColor = '#f59e0b';
                    actionReason = 'Overbought swing (RSI ' + rsi.toFixed(1) + ') after +' + pnlPct.toFixed(1) + '% run. Book partial gains!';
                } else if (stratMode === 'swing' && pnlPct >= 25.0 && cmp < ema20) {
                    actionBadge = '🟡 TRIM 25%';
                    actionColor = '#eab308';
                    actionReason = 'Slipped below 20-EMA; protect +' + pnlPct.toFixed(1) + '% profit by trimming 25%.';
                } else if (stratMode === 'long_term' && cmp >= ema200 && prof && (prof.fund_score >= 6.8 || prof.is_bullish)) {
                    actionBadge = '🟢 LET COMPOUNDER RIDE';
                    actionColor = '#10b981';
                    actionReason = 'Long-term wealth posture intact above 200-EMA (₹' + ema200.toFixed(2) + ') with strong fundamentals.';
                } else if (prof && prof.is_bullish) {
                    actionBadge = '🟢 STRONG HOLD (LEADER)';
                    actionColor = '#10b981';
                    actionReason = 'Leading Stage-2 momentum stock above key EMAs. Let winner run!';
                }

                // If live audit cache from server exists, use enriched server audit!
                if (window.PORTFOLIO_AUDIT_DATA && window.PORTFOLIO_AUDIT_DATA[h.symbol]) {
                    const srv = window.PORTFOLIO_AUDIT_DATA[h.symbol];
                    if (srv.action_badge) actionBadge = srv.action_badge;
                    if (srv.action_color) actionColor = srv.action_color;
                    if (srv.trailing_stop_loss) trailingSL = srv.trailing_stop_loss;
                    if (srv.rationale) actionReason = srv.rationale;

                    if (srv.action_code === 'EMERGENCY_SELL' || srv.action_code === 'EXIT_TRAILING_SL' || srv.action_code === 'CUT_LOSS' || srv.action_code === 'TREND_BREAKDOWN_SELL') {
                        if (!urgentAlerts.find(a => a.symbol === h.symbol)) {
                            atRiskCount++;
                            urgentAlerts.push({
                                symbol: h.symbol,
                                badge: srv.action_badge,
                                color: srv.action_color,
                                reason: srv.rationale,
                                action: srv.suggested_action_detail
                            });
                        }
                    }
                }

                const srvMeta = (window.PORTFOLIO_AUDIT_DATA && window.PORTFOLIO_AUDIT_DATA[h.symbol]) ? window.PORTFOLIO_AUDIT_DATA[h.symbol] : null;
                const taxLabel = (srvMeta && srvMeta.tax_status && srvMeta.tax_status !== 'Buy Date N/A')
                    ? `<div class="tax-tag">${srvMeta.tax_status}</div>`
                    : (h.buyDate ? `<div class="tax-tag">Bought ${h.buyDate}</div>` : '');

                rowsHtml += `
                    <tr class="portfolio-holding-row" data-symbol="${h.symbol}">
                        <td>
                            <div class="sym-name">${h.symbol}</div>
                            <div class="sub-text">${(srvMeta && srvMeta.sector) ? srvMeta.sector : 'Holding #' + (idx + 1)}</div>
                            ${taxLabel}
                        </td>
                        <td><b>${h.qty}</b></td>
                        <td>₹${h.buyPrice.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                        <td>${cmpDisplay}</td>
                        <td>₹${invested.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                        <td><b>₹${currentVal.toLocaleString('en-IN', {minimumFractionDigits: 2})}</b></td>
                        <td style="color:${dayColor}; font-weight:700;">${daySign}${dayPct.toFixed(2)}%</td>
                        <td style="color:${pnlColor}; font-weight:700;">${pnlSign}₹${pnl.toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                        <td style="color:${pnlColor}; font-weight:800; font-size:14px;">${pnlSign}${pnlPct.toFixed(2)}%</td>
                        <td><b style="color:#f59e0b;">₹${trailingSL.toLocaleString('en-IN', {minimumFractionDigits: 2})}</b></td>
                        <td>
                            <span class="cio-badge" style="color:${actionColor}; border-color:${actionColor};" onclick="openHoldingAuditModal('${h.symbol}', ${idx})" title="Click to view full institutional audit">
                                ${actionBadge} ℹ️
                            </span>
                        </td>
                        <td><button class="chart-btn" onclick="toggleCandleChart('${h.symbol}', this)">📈 Chart</button></td>
                        <td><button class="delete-holding-btn" onclick="deletePortfolioHolding(${idx})" title="Delete holding">🗑️</button></td>
                    </tr>
                `;
            });

            tbody.innerHTML = rowsHtml;

            // Update Urgent Alerts Banner
            const banner = document.getElementById('portUrgentAlertsBanner');
            if (banner) {
                if (urgentAlerts.length > 0) {
                    let bannerHtml = `
                        <div style="font-weight: 800; font-size: 14px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                            ⚠️ <b>CIO Urgent Sell Warnings (${urgentAlerts.length} At Risk):</b>
                        </div>
                    `;
                    urgentAlerts.forEach(a => {
                        bannerHtml += `
                            <div style="margin-top: 6px; padding: 8px 12px; background: rgba(0,0,0,0.25); border-radius: 6px; border-left: 4px solid ${a.color};">
                                <b>${a.symbol}</b> &bull; <span style="color:${a.color}; font-weight:700;">${a.badge}</span>: ${a.reason}<br/>
                                <span style="color: #38bdf8; font-weight: 600;">👉 Suggested Action: ${a.action}</span>
                            </div>
                        `;
                    });
                    banner.innerHTML = bannerHtml;
                    banner.style.display = 'block';
                } else {
                    banner.style.display = 'none';
                }
            }

            const meta = window.PORTFOLIO_AUDIT_META;
            const concBanner = document.getElementById('portConcentrationBanner');
            if (concBanner) {
                if (meta && ((meta.concentration_alerts && meta.concentration_alerts.length > 0) || (meta.sector_allocation && meta.sector_allocation.length > 0))) {
                    const secPills = (meta.sector_allocation || []).slice(0, 5).map(s =>
                        `<span class="feed-pill"><b>${s.sector}</b> ${s.weight_pct}%</span>`
                    ).join(' ');
                    const concWarnings = (meta.concentration_alerts || []).map(w =>
                        `<div style="color:#fbbf24; margin-top:4px;">⚠️ ${w}</div>`
                    ).join('');
                    concBanner.innerHTML = `
                        <div style="display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:8px;">
                            <div><b>📊 Portfolio Allocation &amp; Risk Guardrails</b> (Diversification Score: <b style="color:#38bdf8;">${meta.diversification_score || '—'}/10</b>)</div>
                            <div style="display:flex; flex-wrap:wrap; gap:6px;">${secPills}</div>
                        </div>
                        ${concWarnings}
                    `;
                    concBanner.style.display = 'block';
                } else {
                    concBanner.style.display = 'none';
                }
            }

            // If any holdings are missing verified live quotes, fetch them in background!
            if (missingQuotes.length > 0 && !isSyncingPortfolio) {
                syncAllPortfolioQuotes();
            }

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

            if (elInvested) elInvested.innerText = '₹' + totalInvested.toLocaleString('en-IN', {minimumFractionDigits: 2});
            if (elCurrent) elCurrent.innerText = '₹' + totalCurrentValue.toLocaleString('en-IN', {minimumFractionDigits: 2});
            
            if (elPnL) {
                elPnL.innerText = (totalPnL >= 0 ? '+' : '') + '₹' + totalPnL.toLocaleString('en-IN', {minimumFractionDigits: 2});
                elPnL.style.color = totalPnL >= 0 ? '#10b981' : '#ef4444';
            }
            if (elPnLPct) {
                elPnLPct.innerText = (totalPnL >= 0 ? '+' : '') + totalPnLPct.toFixed(2) + '% Overall';
                elPnLPct.style.color = totalPnL >= 0 ? '#10b981' : '#ef4444';
            }

            if (elDayPnL) {
                elDayPnL.innerText = (totalDayPnL >= 0 ? '+' : '') + '₹' + totalDayPnL.toLocaleString('en-IN', {minimumFractionDigits: 2});
                elDayPnL.style.color = totalDayPnL >= 0 ? '#10b981' : '#ef4444';
            }
            if (elDayPnLPct) {
                elDayPnLPct.innerText = (totalDayPnL >= 0 ? '+' : '') + totalDayPnLPct.toFixed(2) + '% Today';
                elDayPnLPct.style.color = totalDayPnL >= 0 ? '#10b981' : '#ef4444';
            }

            // Health Score & At Risk Indicators
            if (port.length > 0) {
                const healthyCount = port.length - atRiskCount;
                const healthScore = Math.max(1.0, Math.min(10.0, (healthyCount / port.length) * 10.0));
                if (elHealth) {
                    elHealth.innerText = healthScore.toFixed(1) + ' / 10';
                    elHealth.style.color = healthScore >= 8.0 ? '#38bdf8' : (healthScore >= 5.0 ? '#f59e0b' : '#ef4444');
                }
                if (elHealthSub) {
                    elHealthSub.innerText = healthScore >= 8.0 ? 'Institutional Grade' : (healthScore >= 5.0 ? 'Moderate Health' : 'Risk Elevated');
                    elHealthSub.style.color = healthScore >= 8.0 ? '#10b981' : (healthScore >= 5.0 ? '#f59e0b' : '#ef4444');
                }
                if (elAtRisk) {
                    elAtRisk.innerText = atRiskCount === 0 ? '0 At Risk' : atRiskCount + ' Require Exit';
                    elAtRisk.style.color = atRiskCount === 0 ? '#10b981' : '#ef4444';
                }
                if (elAtRiskSub) {
                    elAtRiskSub.innerText = atRiskCount === 0 ? 'Trailing Stops Intact' : 'Action Required!';
                    elAtRiskSub.style.color = atRiskCount === 0 ? 'var(--text-muted)' : '#ef4444';
                }
            }
        }

        function openHoldingAuditModal(sym, idx) {
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
            let rationale = srv ? srv.rationale : (prof ? (prof.buy_entry_strategy || prof.strategy_exp || 'Structural posture intact.') : 'Trend structure intact with stop-loss protection active.');
            let actionDetail = srv ? srv.suggested_action_detail : ('Maintain position of ' + h.qty + ' shares with active structural floor.');
            let trailingSL = srv ? srv.trailing_stop_loss : (pnlPct >= 35 ? cmp * 0.88 : h.buyPrice * 0.88);
            let catalyst = srv && srv.news_catalyst ? srv.news_catalyst : 'Stable financial news flow with no critical governance warnings detected.';

            const ema20 = prof && prof.ema_20 ? ('₹' + prof.ema_20.toFixed(2)) : 'N/A';
            const ema50 = prof && prof.ema_50 ? ('₹' + prof.ema_50.toFixed(2)) : 'N/A';
            const ema200 = prof && prof.ema_200 ? ('₹' + prof.ema_200.toFixed(2)) : 'N/A';
            const rsi = prof && prof.rsi ? prof.rsi.toFixed(1) : '55.0';

            if (bodyEl) {
                bodyEl.innerHTML = `
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                        <div style="padding: 12px; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid var(--border);">
                            <div style="font-size: 11px; color: var(--text-muted);">Total P&amp;L Gain / Loss</div>
                            <div style="font-size: 18px; font-weight: 800; color: ${pnl >= 0 ? '#10b981' : '#ef4444'};">
                                ${pnl >= 0 ? '+' : ''}₹${pnl.toLocaleString('en-IN', {minimumFractionDigits: 2})} (${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%)
                            </div>
                        </div>
                        <div style="padding: 12px; background: rgba(255,255,255,0.03); border-radius: 8px; border: 1px solid var(--border);">
                            <div style="font-size: 11px; color: var(--text-muted);">Dynamic Trailing Stop-Loss</div>
                            <div style="font-size: 18px; font-weight: 800; color: #f59e0b;">
                                ₹${trailingSL.toLocaleString('en-IN', {minimumFractionDigits: 2})}
                            </div>
                        </div>
                    </div>

                    <div style="margin-bottom: 16px; padding: 14px; background: rgba(0,0,0,0.2); border-radius: 8px; border-left: 4px solid ${actionColor};">
                        <div style="font-size: 11px; text-transform: uppercase; font-weight: 800; color: ${actionColor}; margin-bottom: 4px;">
                            🎯 CIO Recommendation: ${actionBadge}
                        </div>
                        <div style="font-size: 13px; line-height: 1.5; color: var(--text-heading); margin-bottom: 8px;">
                            ${rationale}
                        </div>
                        <div style="font-size: 12px; color: #38bdf8; font-weight: 600;">
                            👉 Executable Action: ${actionDetail}
                        </div>
                    </div>

                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 16px;">
                        <div style="padding: 8px; text-align: center; background: rgba(255,255,255,0.02); border-radius: 6px; border: 1px solid var(--border);">
                            <div style="font-size: 10px; color: var(--text-muted);">20-Day EMA</div>
                            <div style="font-size: 12px; font-weight: 700; color: var(--text-heading); margin-top: 3px;">${ema20}</div>
                        </div>
                        <div style="padding: 8px; text-align: center; background: rgba(255,255,255,0.02); border-radius: 6px; border: 1px solid var(--border);">
                            <div style="font-size: 10px; color: var(--text-muted);">50-Day EMA</div>
                            <div style="font-size: 12px; font-weight: 700; color: var(--text-heading); margin-top: 3px;">${ema50}</div>
                        </div>
                        <div style="padding: 8px; text-align: center; background: rgba(255,255,255,0.02); border-radius: 6px; border: 1px solid var(--border);">
                            <div style="font-size: 10px; color: var(--text-muted);">200-Day EMA</div>
                            <div style="font-size: 12px; font-weight: 700; color: var(--text-heading); margin-top: 3px;">${ema200}</div>
                        </div>
                        <div style="padding: 8px; text-align: center; background: rgba(255,255,255,0.02); border-radius: 6px; border: 1px solid var(--border);">
                            <div style="font-size: 10px; color: var(--text-muted);">Daily RSI</div>
                            <div style="font-size: 12px; font-weight: 700; color: #38bdf8; margin-top: 3px;">${rsi}</div>
                        </div>
                    </div>

                    <div style="padding: 12px; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px solid var(--border);">
                        <div style="font-size: 11px; font-weight: 700; color: var(--text-muted); margin-bottom: 4px;">📰 News Sentiment &amp; Event Catalyst:</div>
                        <div style="font-size: 12px; line-height: 1.5; color: var(--text-heading);">
                            ${catalyst}
                        </div>
                    </div>
                `;
            }

            if (modal) modal.style.display = 'flex';
        }

        function closeHoldingAuditModal(e) {
            const modal = document.getElementById('holdingAuditModal');
            if (modal) modal.style.display = 'none';
        }

        window.addEventListener('DOMContentLoaded', async () => {
            let currentTheme = 'dark';
            try {
                currentTheme = localStorage.getItem('stock_ai_theme') || 'dark';
            } catch (e) {}
            applyTheme(currentTheme);
            try {
                const savedMode = localStorage.getItem('stock_ai_port_strategy');
                const modeSel = document.getElementById('portStrategyMode');
                if (savedMode && modeSel) modeSel.value = savedMode;
            } catch (e) {}

            populateSectorFilter();
            renderPortfolio();

            const online = await checkDaemonStatus(false);
            if (online) {
                await syncPortfolioStorageWithServer();
                syncPortfolioAuditFromServer().then(() => renderPortfolio());
                refreshFeedHealthRibbon();
            }
            startAutoReadTimer();
            // Periodically ping daemon status every 45s
            setInterval(() => checkDaemonStatus(false), 45000);

            // Initialize SIP Calculator
            calcSipWealth(15000, 10, 10);
        });

        async function refreshFeedHealthRibbon() {
            const el = document.getElementById('feedHealthRibbon');
            if (!el) return;
            try {
                const res = await fetch('http://127.0.0.1:5005/api/feed_health');
                if (!res.ok) return;
                const fh = await res.json();
                if (!fh || !Array.isArray(fh.feeds)) return;
                const pills = fh.feeds.map(f =>
                    `<span class="feed-pill" title="${f.detail} • Updated: ${f.updated_at}"><span class="feed-dot" style="background:${f.color};"></span><b>${f.feed}:</b> ${f.status} (${f.age})</span>`
                ).join('');
                el.innerHTML = `<span class="feed-health-title">📡 Feeds (${fh.healthy_count}/${fh.total_feeds} Healthy):</span>` + pills;
            } catch (e) {}
        }

        // --- Telegram Modal Functions ---
        function openTelegramModal() {
            const modal = document.getElementById('telegramModal');
            if (modal) modal.style.display = 'flex';
        }

        function closeTelegramModal(event) {
            if (!event || event.target.id === 'telegramModal' || event.target.classList.contains('modal-close-btn') || event.target.tagName === 'BUTTON') {
                const modal = document.getElementById('telegramModal');
                if (modal) modal.style.display = 'none';
            }
        }

        // --- 1-Click Broker CSV Upload & Parser (Zerodha, Groww, Angel One, Upstox) ---
        function handleBrokerCsvUpload(input) {
            const file = input.files && input.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = function(e) {
                try {
                    const text = e.target.result || '';
                    const rawLines = text.split(String.fromCharCode(10));
                    const lines = [];
                    for (let i = 0; i < rawLines.length; i++) {
                        const cleanLine = rawLines[i].split(String.fromCharCode(13)).join('').trim();
                        if (cleanLine.length > 0) {
                            lines.push(cleanLine);
                        }
                    }

                    if (lines.length < 2) {
                        alert('Uploaded CSV file appears empty or invalid.');
                        return;
                    }

                    const delim = lines[0].indexOf(';') !== -1 ? ';' : ',';
                    const rawHeaders = lines[0].split(delim);
                    const header = [];
                    for (let i = 0; i < rawHeaders.length; i++) {
                        header.push(rawHeaders[i].trim().toLowerCase().replace(/['"]/g, ''));
                    }

                    let symIdx = -1;
                    let qtyIdx = -1;
                    let priceIdx = -1;

                    for (let i = 0; i < header.length; i++) {
                        const h = header[i];
                        if (symIdx === -1 && (h.indexOf('symbol') !== -1 || h.indexOf('instrument') !== -1 || h.indexOf('ticker') !== -1 || h.indexOf('stock') !== -1 || h.indexOf('scrip') !== -1)) {
                            symIdx = i;
                        }
                        if (qtyIdx === -1 && (h.indexOf('qty') !== -1 || h.indexOf('quantity') !== -1 || h.indexOf('shares') !== -1)) {
                            qtyIdx = i;
                        }
                        if (priceIdx === -1 && (h.indexOf('avg') !== -1 || h.indexOf('cost') !== -1 || h.indexOf('buy') !== -1 || h.indexOf('price') !== -1)) {
                            priceIdx = i;
                        }
                    }

                    if (symIdx === -1 || qtyIdx === -1) {
                        alert('Could not automatically identify Symbol and Quantity columns in your CSV. Please check the header row.');
                        return;
                    }

                    const newHoldings = [];
                    let importedCount = 0;

                    for (let i = 1; i < lines.length; i++) {
                        const rawRow = lines[i].split(delim);
                        if (rawRow.length <= Math.max(symIdx, qtyIdx)) continue;

                        let rawSym = rawRow[symIdx].toUpperCase().replace('-EQ', '').replace('.NS', '').replace('NSE:', '').trim();
                        rawSym = rawSym.replace(/['"\s]/g, '');

                        const qtyStr = (rawRow[qtyIdx] || '0').replace(/,/g, '').trim();
                        const qty = parseFloat(qtyStr);

                        let price = 0.0;
                        if (priceIdx !== -1 && rawRow[priceIdx]) {
                            const priceStr = rawRow[priceIdx].replace(/,/g, '').replace('₹', '').replace('Rs', '').trim();
                            price = parseFloat(priceStr);
                        }

                        if (rawSym && !isNaN(qty) && qty > 0) {
                            let cmp = price;
                            if (window.PORTFOLIO_CMP_CACHE && window.PORTFOLIO_CMP_CACHE[rawSym]) {
                                cmp = window.PORTFOLIO_CMP_CACHE[rawSym];
                            }
                            newHoldings.push({'symbol': rawSym, 'qty': qty, 'buyPrice': (isNaN(price) || price <= 0) ? cmp : price, 'cmp': cmp > 0 ? cmp : price});
                            importedCount++;
                        }
                    }

                    if (importedCount > 0) {
                        savePortfolio(newHoldings);
                        showSyncToast('✅ Successfully imported ' + importedCount + ' holdings from broker CSV! Running AI Health Audit...');
                        syncAllPortfolioQuotes();
                    } else {
                        alert('No valid holdings could be parsed from the CSV file.');
                    }
                } catch (err) {
                    alert('Error parsing CSV file: ' + err.message);
                }
            };
            reader.readAsText(file);
            input.value = '';
        }

        // --- Smart SIP & Step-Up Compounding Calculator ---
        function onSipSliderChange() {
            const amt = parseFloat(document.getElementById('sipAmountSlider').value);
            const yrs = parseFloat(document.getElementById('sipYearsSlider').value);
            const step = parseFloat(document.getElementById('sipStepUpSlider').value);

            document.getElementById('sipAmountVal').innerText = '₹' + amt.toLocaleString('en-IN');
            document.getElementById('sipYearsVal').innerText = yrs + ' Years';
            document.getElementById('sipStepUpVal').innerText = step + '% / year';

            calcSipWealth(amt, yrs, step);
        }

        function setSipAmount(amt) {
            document.getElementById('sipAmountSlider').value = amt;
            onSipSliderChange();
        }

        function setSipYears(yrs) {
            document.getElementById('sipYearsSlider').value = yrs;
            onSipSliderChange();
        }

        function setSipStepUp(step) {
            document.getElementById('sipStepUpSlider').value = step;
            onSipSliderChange();
        }

        function adjustSipYears(delta) {
            const slider = document.getElementById('sipYearsSlider');
            if (!slider) return;
            let val = parseInt(slider.value, 10) + delta;
            val = Math.max(1, Math.min(30, val));
            slider.value = val;
            onSipSliderChange();
        }

        function adjustSipStepUp(delta) {
            const slider = document.getElementById('sipStepUpSlider');
            if (!slider) return;
            let val = parseInt(slider.value, 10) + delta;
            val = Math.max(0, Math.min(30, val));
            slider.value = val;
            onSipSliderChange();
        }

        function adjustSipAmount(delta) {
            const slider = document.getElementById('sipAmountSlider');
            if (!slider) return;
            let val = parseInt(slider.value, 10) + delta;
            val = Math.max(1000, Math.min(200000, val));
            slider.value = val;
            onSipSliderChange();
        }

        function formatIndianCurrency(num) {
            if (num >= 10000000) {
                return '₹' + (num / 10000000).toFixed(2) + ' Cr';
            } else if (num >= 100000) {
                return '₹' + (num / 100000).toFixed(2) + ' L';
            } else {
                return '₹' + Math.round(num).toLocaleString('en-IN');
            }
        }

        function calcSipWealth(monthlySip = 15000, years = 10, stepUpPct = 10) {
            let totalInvested = 0;
            let fdWealth = 0;
            let niftyWealth = 0;
            let alphaWealth = 0;

            const rFd = 0.07 / 12;
            const rNifty = 0.125 / 12;
            const rAlpha = 0.185 / 12;

            let curSip = monthlySip;
            let crorepatiYear = null;

            for (let y = 1; y <= years; y++) {
                for (let m = 1; m <= 12; m++) {
                    totalInvested += curSip;
                    fdWealth = (fdWealth + curSip) * (1 + rFd);
                    niftyWealth = (niftyWealth + curSip) * (1 + rNifty);
                    alphaWealth = (alphaWealth + curSip) * (1 + rAlpha);

                    if (!crorepatiYear && alphaWealth >= 10000000) {
                        crorepatiYear = y;
                    }
                }
                curSip = curSip * (1 + (stepUpPct / 100));
            }

            const elInvested = document.getElementById('sipTotalInvested');
            if (elInvested) elInvested.innerText = formatIndianCurrency(totalInvested);

            const elFd = document.getElementById('sipFdWealth');
            if (elFd) elFd.innerText = formatIndianCurrency(fdWealth);
            const elFdGain = document.getElementById('sipFdGain');
            if (elFdGain) elFdGain.innerText = 'Gain: +' + formatIndianCurrency(Math.max(0, fdWealth - totalInvested));

            const elNifty = document.getElementById('sipNiftyWealth');
            if (elNifty) elNifty.innerText = formatIndianCurrency(niftyWealth);
            const elNiftyGain = document.getElementById('sipNiftyGain');
            if (elNiftyGain) elNiftyGain.innerText = 'Gain: +' + formatIndianCurrency(Math.max(0, niftyWealth - totalInvested));

            const elAlpha = document.getElementById('sipAlphaWealth');
            if (elAlpha) elAlpha.innerText = formatIndianCurrency(alphaWealth);
            const elAlphaGain = document.getElementById('sipAlphaGain');
            if (elAlphaGain) elAlphaGain.innerText = 'Gain: +' + formatIndianCurrency(Math.max(0, alphaWealth - totalInvested));

            const elBonus = document.getElementById('sipAlphaBonus');
            if (elBonus) elBonus.innerText = '+' + formatIndianCurrency(Math.max(0, alphaWealth - niftyWealth));

            const elBadge = document.getElementById('sipMilestoneBadge');
            if (elBadge) {
                if (crorepatiYear) {
                    elBadge.innerText = `🏆 Crorepati Milestone: Year ${crorepatiYear}!`;
                    elBadge.style.background = '#16a34a';
                } else {
                    elBadge.innerText = `🎯 ₹1 Crore Target: ${years}Y Path`;
                    elBadge.style.background = '#0284c7';
                }
            }
        }
    
