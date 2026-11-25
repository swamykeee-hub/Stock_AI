from typing import Tuple


def _glow_style(accent_hex: str) -> str:
    return f'<div class="idx-bg-glow" style="background: radial-gradient(circle, {accent_hex}66 0%, transparent 72%);"></div>'


def _svg_wrapper(svg_inner: str, accent_hex: str, anim_cls: str = "") -> str:
    """Wraps SVG scene cleanly inside .idx-bg-art + soft ambient radial glow."""
    return (
        f'{_glow_style(accent_hex)}'
        f'<div class="idx-bg-art {anim_cls}" aria-hidden="true">'
        f'<svg viewBox="0 0 140 96" fill="none" xmlns="http://www.w3.org/2000/svg">{svg_inner}</svg>'
        f'</div>'
    )


def get_index_visual_backdrop(card_title: str) -> Tuple[str, str]:
    """
    Returns (backdrop_html, extra_card_class) for each index, macro, or CIO status card.
    Strictly scoped to the inside right corner of each individual box with GPU animations.
    """
    key = (card_title or "").upper().strip()

    # 1. NIFTY FMCG: Consumer Staples (Atta Flour Sack, Cooking Oil Bottle, Wheat Stalks)
    if "FMCG" in key:
        svg = """
        <defs>
            <linearGradient id="iv-fmcg-sack" x1="48" y1="30" x2="88" y2="86" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stop-color="#fde68a" stop-opacity="0.72"/>
                <stop offset="100%" stop-color="#d97706" stop-opacity="0.30"/>
            </linearGradient>
            <linearGradient id="iv-fmcg-oil" x1="94" y1="18" x2="120" y2="84" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stop-color="#fef08a" stop-opacity="0.85"/>
                <stop offset="55%" stop-color="#f59e0b" stop-opacity="0.55"/>
                <stop offset="100%" stop-color="#b45309" stop-opacity="0.35"/>
            </linearGradient>
        </defs>
        <!-- Left & top Wheat Stalks (gentle sway) -->
        <g class="idx-anim-float-rev" opacity="0.78">
            <path d="M36 78 C32 62, 34 46, 40 30" stroke="#fcd34d" stroke-width="1.6" stroke-linecap="round"/>
            <ellipse cx="35" cy="40" rx="3" ry="5.5" transform="rotate(-24 35 40)" fill="#fbbf24" opacity="0.7"/>
            <ellipse cx="42" cy="46" rx="3" ry="5.5" transform="rotate(24 42 46)" fill="#fbbf24" opacity="0.7"/>
            <ellipse cx="33" cy="54" rx="3" ry="5" transform="rotate(-26 33 54)" fill="#f59e0b" opacity="0.65"/>
            <ellipse cx="40" cy="60" rx="3" ry="5" transform="rotate(20 40 60)" fill="#f59e0b" opacity="0.65"/>
            <path d="M122 76 C126 60, 125 46, 120 34" stroke="#fcd34d" stroke-width="1.5" stroke-linecap="round"/>
            <ellipse cx="120" cy="42" rx="2.6" ry="5" transform="rotate(-22 120 42)" fill="#fbbf24" opacity="0.65"/>
            <ellipse cx="127" cy="48" rx="2.6" ry="5" transform="rotate(24 127 48)" fill="#fbbf24" opacity="0.65"/>
        </g>
        <!-- Main Products: Atta Flour Sack + Cooking Oil Bottle -->
        <g class="idx-anim-float">
            <!-- Atta Sack Folded Top & Flour Mound -->
            <path d="M52 38 Q68 24 84 38 Z" fill="#fef3c7" opacity="0.75"/>
            <path d="M48 39 C44 52, 43 72, 47 82 C52 86, 84 86, 89 82 C93 72, 92 52, 88 39 C81 42, 55 42, 48 39 Z"
                  fill="url(#iv-fmcg-sack)" stroke="#fde68a" stroke-width="1.6"/>
            <circle cx="68" cy="63" r="10" fill="#78350f" fill-opacity="0.38" stroke="#fde68a" stroke-width="1.1"/>
            <path d="M68 57 V69 M64 61 L68 58 L72 61 M64 65 L68 62 L72 65" stroke="#fef08a" stroke-width="1.3" stroke-linecap="round"/>
            <!-- Cooking Oil Bottle -->
            <rect x="103" y="16" width="8" height="5" rx="1.5" fill="#fbbf24" stroke="#fef3c7" stroke-width="1"/>
            <path d="M103 21 L101 29 C96 32, 95 38, 95 45 L95 79 C95 83, 98 85, 107 85 C116 85, 119 83, 119 79 L119 45 C119 38, 118 32, 113 29 L111 21 Z"
                  fill="url(#iv-fmcg-oil)" stroke="#fef08a" stroke-width="1.5"/>
            <rect x="97" y="48" width="20" height="14" rx="2" fill="#fffbeb" fill-opacity="0.22" stroke="#fde68a" stroke-width="0.9"/>
            <circle cx="107" cy="55" r="3" fill="#fef08a" opacity="0.85"/>
        </g>
        """
        return _svg_wrapper(svg, "#f59e0b"), "idx-theme-amber"

    # 2. NIFTY PHARMA: Capsules, Medicine Blister & Continuous EKG Heartbeat Wave
    if "PHARMA" in key:
        svg = """
        <defs>
            <linearGradient id="iv-ph-cap" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#6ee7b7" stop-opacity="0.9"/>
                <stop offset="100%" stop-color="#059669" stop-opacity="0.4"/>
            </linearGradient>
        </defs>
        <!-- Pill Blister Pack Backdrop -->
        <g class="idx-anim-float-rev" transform="rotate(-14 98 48)" opacity="0.75">
            <rect x="74" y="20" width="42" height="56" rx="6" fill="#064e3b" fill-opacity="0.45" stroke="#34d399" stroke-width="1.4"/>
            <ellipse cx="87" cy="33" rx="6" ry="3.8" fill="url(#iv-ph-cap)" stroke="#a7f3d0" stroke-width="1"/>
            <ellipse cx="103" cy="33" rx="6" ry="3.8" fill="url(#iv-ph-cap)" stroke="#a7f3d0" stroke-width="1"/>
            <ellipse cx="87" cy="48" rx="6" ry="3.8" fill="url(#iv-ph-cap)" stroke="#a7f3d0" stroke-width="1"/>
            <ellipse cx="103" cy="48" rx="6" ry="3.8" fill="url(#iv-ph-cap)" stroke="#a7f3d0" stroke-width="1"/>
            <ellipse cx="87" cy="63" rx="6" ry="3.8" fill="url(#iv-ph-cap)" stroke="#a7f3d0" stroke-width="1"/>
            <ellipse cx="103" cy="63" rx="6" ry="3.8" fill="url(#iv-ph-cap)" stroke="#a7f3d0" stroke-width="1"/>
        </g>
        <!-- Floating Glowing Capsules -->
        <g class="idx-anim-float">
            <g transform="translate(54,32) rotate(-32)">
                <rect x="-11" y="-5" width="22" height="10" rx="5" fill="#10b981" fill-opacity="0.65" stroke="#a7f3d0" stroke-width="1.3"/>
                <path d="M0 -5 H6 A5 5 0 0 1 6 5 H0 Z" fill="#ecfdf5" fill-opacity="0.55"/>
            </g>
            <g transform="translate(68,66) rotate(24)">
                <rect x="-10" y="-4.5" width="20" height="9" rx="4.5" fill="#2dd4bf" fill-opacity="0.65" stroke="#99f6e4" stroke-width="1.3"/>
                <path d="M0 -4.5 H5.5 A4.5 4.5 0 0 1 5.5 4.5 H0 Z" fill="#f0fdfa" fill-opacity="0.55"/>
            </g>
        </g>
        <!-- Live EKG Heartbeat Wave -->
        <path d="M22 76 H52 L60 66 L67 84 L76 48 L85 84 L92 68 L100 76 H134"
              stroke="#34d399" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
              class="idx-anim-dash" opacity="0.9"/>
        """
        return _svg_wrapper(svg, "#10b981"), "idx-theme-emerald"

    # 3. NIFTY METAL: Corrugated Metal Roof Sheets + Stacked Steel TMT Rods (Rebar Bundle)
    if "METAL" in key:
        svg = """
        <defs>
            <linearGradient id="iv-met-sheet" x1="50" y1="16" x2="130" y2="56" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stop-color="#e2e8f0" stop-opacity="0.82"/>
                <stop offset="55%" stop-color="#64748b" stop-opacity="0.58"/>
                <stop offset="100%" stop-color="#334155" stop-opacity="0.45"/>
            </linearGradient>
            <linearGradient id="iv-met-rod" x1="40" y1="54" x2="128" y2="86" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stop-color="#cbd5e1" stop-opacity="0.90"/>
                <stop offset="55%" stop-color="#94a3b8" stop-opacity="0.65"/>
                <stop offset="100%" stop-color="#fb923c" stop-opacity="0.62"/>
            </linearGradient>
        </defs>
        <!-- Back Layer: Stacked Corrugated Metal Roof Sheets -->
        <g class="idx-anim-float-rev">
            <!-- Lower Stacked Sheet Edge -->
            <path d="M56 38 L78 21 L132 25 L110 44 Z"
                  fill="#475569" fill-opacity="0.55" stroke="#94a3b8" stroke-width="1.1"/>
            <!-- Top Corrugated Roof Sheet Body -->
            <path d="M52 33 L76 15 L130 19 L106 38 Z"
                  fill="url(#iv-met-sheet)" stroke="#e2e8f0" stroke-width="1.3" stroke-linejoin="round"/>
            <!-- Parallel Corrugation Ridges across Sheet -->
            <g stroke="#f8fafc" stroke-opacity="0.55" stroke-width="1.1" stroke-linecap="round">
                <line x1="60" y1="31" x2="83" y2="16"/>
                <line x1="70" y1="32" x2="93" y2="17"/>
                <line x1="80" y1="33" x2="103" y2="17.5"/>
                <line x1="90" y1="34" x2="113" y2="18"/>
                <line x1="100" y1="35" x2="122" y2="19"/>
            </g>
            <!-- Rhythmic Corrugated Wave Front Lip -->
            <path d="M52 33 Q55 37 58 34 T64 34 T70 35 T76 35 T82 36 T88 36 T94 37 T100 37 T106 38"
                  stroke="#bae6fd" stroke-width="1.6" stroke-linecap="round" class="idx-anim-dash"/>
        </g>
        <!-- Front Layer: Bundled Steel Metal Rods (TMT Rebar Stack) -->
        <g class="idx-anim-float">
            <!-- Bottom Row (3 Steel Rods) -->
            <path d="M40 68 L100 62 L100 71 L40 77 Z" fill="url(#iv-met-rod)" stroke="#cbd5e1" stroke-width="1"/>
            <path d="M46 75 L108 69 L108 78 L46 84 Z" fill="url(#iv-met-rod)" stroke="#e2e8f0" stroke-width="1.1"/>
            <path d="M54 80 L118 74 L118 83 L54 89 Z" fill="url(#iv-met-rod)" stroke="#f8fafc" stroke-width="1.2"/>
            <!-- Top Row (2 Steel Rods resting in pyramid) -->
            <path d="M44 59 L104 53 L104 62 L44 68 Z" fill="url(#iv-met-rod)" stroke="#e2e8f0" stroke-width="1.1"/>
            <path d="M52 65 L114 59 L114 68 L52 74 Z" fill="url(#iv-met-rod)" stroke="#f8fafc" stroke-width="1.2"/>
            <!-- Subtle Rebar Ribs Highlight -->
            <g stroke="#fed7aa" stroke-opacity="0.65" stroke-width="1">
                <line x1="68" y1="57" x2="68" y2="65"/><line x1="78" y1="56" x2="78" y2="64"/><line x1="88" y1="55" x2="88" y2="63"/>
                <line x1="76" y1="63" x2="76" y2="71"/><line x1="86" y1="62" x2="86" y2="70"/><line x1="96" y1="61" x2="96" y2="69"/>
            </g>
            <!-- Clean Circular Rod End-Caps -->
            <circle cx="104" cy="57.5" r="4.6" fill="#1e293b" stroke="#fdba74" stroke-width="1.5"/>
            <circle cx="114" cy="63.5" r="4.6" fill="#1e293b" stroke="#fde68a" stroke-width="1.5"/>
            <circle cx="100" cy="66.5" r="4.4" fill="#1e293b" stroke="#cbd5e1" stroke-width="1.3"/>
            <circle cx="108" cy="73.5" r="4.6" fill="#1e293b" stroke="#fdba74" stroke-width="1.5"/>
            <circle cx="118" cy="78.5" r="4.8" fill="#1e293b" stroke="#fde68a" stroke-width="1.6"/>
            <circle cx="118" cy="78.5" r="1.6" fill="#fb923c"/>
            <circle cx="114" cy="63.5" r="1.6" fill="#fb923c"/>
        </g>
        <!-- Molten Forge Spark Accents -->
        <g class="idx-anim-pulse" fill="#fb923c">
            <circle cx="129" cy="48" r="2"/><circle cx="125" cy="57" r="1.5"/><circle cx="35" cy="58" r="1.6"/>
        </g>
        """
        return _svg_wrapper(svg, "#f97316"), "idx-theme-orange"

    # 4. NIFTY AUTO: Sleek EV Sports Coupe + Spinning Alloy Wheels + Speed Streaks
    if "AUTO" in key:
        svg = """
        <defs>
            <linearGradient id="iv-auto-body" x1="34" y1="36" x2="128" y2="76" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stop-color="#38bdf8" stop-opacity="0.72"/>
                <stop offset="100%" stop-color="#22d3ee" stop-opacity="0.28"/>
            </linearGradient>
        </defs>
        <g class="idx-anim-flow-left" opacity="0.6">
            <line x1="16" y1="54" x2="36" y2="54" stroke="#38bdf8" stroke-width="1.6" stroke-linecap="round"/>
            <line x1="22" y1="62" x2="34" y2="62" stroke="#67e8f9" stroke-width="1.2" stroke-linecap="round"/>
        </g>
        <g class="idx-anim-float">
            <!-- Sleek Sports Coupe Chassis -->
            <path d="M36 68 C36 59, 41 53, 52 51 L67 39 C75 35, 92 35, 102 41 L122 50 C128 53, 130 59, 129 68 H117 A11 11 0 0 0 95 68 H67 A11 11 0 0 0 45 68 Z"
                  fill="url(#iv-auto-body)" stroke="#7dd3fc" stroke-width="1.6" stroke-linejoin="round"/>
            <!-- Cabin Windows -->
            <path d="M58 50 L69 41 C77 38, 89 38, 99 43 L110 50 Z" fill="#0f172a" fill-opacity="0.5" stroke="#bae6fd" stroke-width="1"/>
            <!-- Headlight glow -->
            <ellipse cx="124" cy="56" rx="4" ry="2" fill="#e0f2fe"/>
            <!-- Spinning Alloy Wheels -->
            <g class="idx-anim-spin">
                <circle cx="56" cy="69" r="10.5" fill="#0f172a" stroke="#e0f2fe" stroke-width="2.4"/>
                <circle cx="56" cy="69" r="5.5" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="2.5 2"/>
                <circle cx="56" cy="69" r="2" fill="#bae6fd"/>
            </g>
            <g class="idx-anim-spin">
                <circle cx="106" cy="69" r="10.5" fill="#0f172a" stroke="#e0f2fe" stroke-width="2.4"/>
                <circle cx="106" cy="69" r="5.5" stroke="#38bdf8" stroke-width="1.5" stroke-dasharray="2.5 2"/>
                <circle cx="106" cy="69" r="2" fill="#bae6fd"/>
            </g>
        </g>
        """
        return _svg_wrapper(svg, "#06b6d4"), "idx-theme-cyan"

    # 5. BANK NIFTY: Classical Vault Building Pillars + Floating Glowing Rupee Coins
    if "BANK NIFTY" in key:
        svg = """
        <defs>
            <linearGradient id="iv-bk-col" x1="56" y1="24" x2="124" y2="82" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stop-color="#93c5fd" stop-opacity="0.75"/>
                <stop offset="100%" stop-color="#3b82f6" stop-opacity="0.28"/>
            </linearGradient>
        </defs>
        <g opacity="0.88">
            <polygon points="56,36 90,18 124,36" fill="url(#iv-bk-col)" stroke="#bfdbfe" stroke-width="1.5"/>
            <rect x="61" y="40" width="7" height="34" rx="1" fill="url(#iv-bk-col)" stroke="#93c5fd" stroke-width="1"/>
            <rect x="78" y="40" width="7" height="34" rx="1" fill="url(#iv-bk-col)" stroke="#93c5fd" stroke-width="1"/>
            <rect x="95" y="40" width="7" height="34" rx="1" fill="url(#iv-bk-col)" stroke="#93c5fd" stroke-width="1"/>
            <rect x="112" y="40" width="7" height="34" rx="1" fill="url(#iv-bk-col)" stroke="#93c5fd" stroke-width="1"/>
            <rect x="53" y="75" width="74" height="6" rx="2" fill="#60a5fa" fill-opacity="0.55" stroke="#bfdbfe" stroke-width="1"/>
        </g>
        <!-- Floating Glowing Rupee Coin -->
        <g class="idx-anim-float">
            <circle cx="48" cy="56" r="13" fill="#f59e0b" fill-opacity="0.45" stroke="#fde68a" stroke-width="1.6"/>
            <text x="48" y="61" text-anchor="middle" fill="#fef08a" font-size="14" font-weight="800">₹</text>
        </g>
        """
        return _svg_wrapper(svg, "#3b82f6"), "idx-theme-blue"

    # 6. NIFTY PRIVATE BANK: Contactless Card + Digital Payment Waves
    if "PRIVATE BANK" in key:
        svg = """
        <g class="idx-anim-float">
            <rect x="52" y="32" width="68" height="44" rx="7" fill="#1e3a8a" fill-opacity="0.65" stroke="#60a5fa" stroke-width="1.6"/>
            <rect x="52" y="42" width="68" height="8" fill="#38bdf8" fill-opacity="0.3"/>
            <rect x="60" y="56" width="12" height="9" rx="2" fill="#fde68a" fill-opacity="0.8"/>
            <text x="108" y="66" text-anchor="middle" fill="#bae6fd" font-size="13" font-weight="800">₹</text>
        </g>
        <g class="idx-anim-pulse" opacity="0.75">
            <path d="M123 42 C128 46, 128 54, 123 58" stroke="#38bdf8" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M128 38 C135 45, 135 55, 128 62" stroke="#7dd3fc" stroke-width="1.6" stroke-linecap="round"/>
        </g>
        """
        return _svg_wrapper(svg, "#38bdf8"), "idx-theme-cyan"

    # 7. NIFTY FIN-SERVICES: Ascending Wealth Shield & Compounding Arrow
    if "FIN-SERVICES" in key or "FIN" in key:
        svg = """
        <path d="M88 22 L114 31 V52 C114 68, 102 79, 88 85 C74 79, 62 68, 62 52 V31 Z"
              fill="#4f46e5" fill-opacity="0.32" stroke="#a5b4fc" stroke-width="1.6"/>
        <path d="M44 74 L68 58 L84 64 L118 32" stroke="#34d399" stroke-width="2.4" stroke-linecap="round"
              stroke-linejoin="round" class="idx-anim-dash"/>
        <polygon points="118,32 108,33 116,42" fill="#34d399" class="idx-anim-float"/>
        """
        return _svg_wrapper(svg, "#6366f1"), "idx-theme-indigo"

    # 8. NIFTY IT: Microchip Processor + Traveling Circuit Data Packets
    if "NIFTY IT" in key:
        svg = """
        <g opacity="0.82">
            <rect x="68" y="30" width="40" height="40" rx="6" fill="#0e7490" fill-opacity="0.45" stroke="#22d3ee" stroke-width="1.8"/>
            <rect x="78" y="40" width="20" height="20" rx="3" fill="#06b6d4" fill-opacity="0.4" stroke="#a5f3fc" stroke-width="1.1"/>
            <text x="88" y="54" text-anchor="middle" fill="#ecfeff" font-size="11" font-weight="800">&lt;/&gt;</text>
        </g>
        <!-- Animated Circuit Traces -->
        <g stroke="#38bdf8" stroke-width="1.5" stroke-linecap="round" class="idx-anim-dash">
            <path d="M32 42 H68 M38 58 H68 M108 42 H134 M108 58 H128 M82 14 V30 M96 14 V30 M82 70 V86 M96 70 V86"/>
        </g>
        <g class="idx-anim-pulse" fill="#67e8f9">
            <circle cx="32" cy="42" r="2.5"/><circle cx="38" cy="58" r="2.5"/>
            <circle cx="134" cy="42" r="2.5"/><circle cx="128" cy="58" r="2.5"/>
        </g>
        """
        return _svg_wrapper(svg, "#06b6d4"), "idx-theme-cyan"

    # 9. NIFTY AI CATALYSTS: Neural Network Nodes + Rotating AI Diamond Core
    if "AI" in key:
        svg = """
        <g stroke="#c084fc" stroke-width="1.3" opacity="0.65" class="idx-anim-dash">
            <line x1="56" y1="30" x2="92" y2="50"/><line x1="52" y1="68" x2="92" y2="50"/>
            <line x1="124" y1="28" x2="92" y2="50"/><line x1="126" y1="70" x2="92" y2="50"/>
            <line x1="56" y1="30" x2="124" y2="28"/><line x1="52" y1="68" x2="126" y2="70"/>
        </g>
        <g class="idx-anim-spin-slow">
            <polygon points="92,34 108,50 92,66 76,50" fill="#7c3aed" fill-opacity="0.45" stroke="#e9d5ff" stroke-width="1.8"/>
            <circle cx="92" cy="50" r="5" fill="#38bdf8"/>
        </g>
        <g class="idx-anim-pulse" fill="#38bdf8">
            <circle cx="56" cy="30" r="3.5"/><circle cx="52" cy="68" r="3.5"/>
            <circle cx="124" cy="28" r="3.5"/><circle cx="126" cy="70" r="3.5"/>
        </g>
        """
        return _svg_wrapper(svg, "#8b5cf6"), "idx-theme-purple"

    # 10. INDIA VIX: Volatility Oscilloscope Wave + Alert Rings
    if "VIX" in key:
        svg = """
        <g class="idx-anim-pulse">
            <circle cx="96" cy="48" r="28" stroke="#f59e0b" stroke-opacity="0.35" stroke-width="1.4"/>
            <circle cx="96" cy="48" r="18" stroke="#fbbf24" stroke-opacity="0.55" stroke-width="1.4"/>
        </g>
        <path d="M26 58 Q48 22 66 58 T104 42 T136 52" stroke="#fbbf24" stroke-width="2.2"
              stroke-linecap="round" class="idx-anim-dash"/>
        """
        return _svg_wrapper(svg, "#f59e0b"), "idx-theme-amber"

    # 11. NIFTY 50: Charging Golden/Emerald Market Bull + Rising Candlesticks Skyline
    if "NIFTY 50" in key:
        svg = """
        <!-- Rising Candlesticks Skyline -->
        <g opacity="0.45" class="idx-anim-float-rev">
            <rect x="48" y="54" width="6" height="24" rx="1.5" fill="#10b981"/>
            <rect x="60" y="42" width="6" height="36" rx="1.5" fill="#10b981"/>
            <rect x="72" y="48" width="6" height="30" rx="1.5" fill="#34d399"/>
        </g>
        <!-- Stylized Charging Bull Head & Horns -->
        <g class="idx-anim-float">
            <path d="M72 30 C64 20, 74 16, 84 26 L98 28 C108 18, 120 20, 112 32 C122 40, 126 52, 118 64 C112 72, 102 78, 92 78 C82 78, 72 68, 70 54 C68 42, 74 34, 72 30 Z"
                  fill="#10b981" fill-opacity="0.38" stroke="#6ee7b7" stroke-width="1.8" stroke-linejoin="round"/>
            <circle cx="105" cy="45" r="2.2" fill="#fef08a"/>
            <path d="M84 64 Q95 70 106 64" stroke="#a7f3d0" stroke-width="1.6" stroke-linecap="round"/>
        </g>
        """
        return _svg_wrapper(svg, "#10b981"), "idx-theme-emerald"

    # 12. SENSEX: Exchange Tower Skyline + Glowing Ticker Curve
    if "SENSEX" in key:
        svg = """
        <g opacity="0.65">
            <rect x="78" y="20" width="24" height="58" rx="3" fill="#0284c7" fill-opacity="0.38" stroke="#7dd3fc" stroke-width="1.5"/>
            <line x1="90" y1="10" x2="90" y2="20" stroke="#bae6fd" stroke-width="1.8"/>
            <rect x="58" y="42" width="16" height="36" rx="2" fill="#0369a1" fill-opacity="0.35" stroke="#38bdf8" stroke-width="1.2"/>
            <rect x="106" y="36" width="16" height="42" rx="2" fill="#0369a1" fill-opacity="0.35" stroke="#38bdf8" stroke-width="1.2"/>
        </g>
        <path d="M30 70 L58 56 L78 60 L102 32 L130 22" stroke="#fde047" stroke-width="2"
              stroke-linecap="round" class="idx-anim-dash"/>
        """
        return _svg_wrapper(svg, "#0ea5e9"), "idx-theme-blue"

    # 13. NIFTY 100 / NIFTY 200: Institutional Blue-Chip Skyline / Constellation
    if "100" in key or "200" in key:
        svg = """
        <g class="idx-anim-float-rev" opacity="0.68">
            <rect x="46" y="56" width="12" height="24" rx="2" fill="#38bdf8" fill-opacity="0.35" stroke="#7dd3fc" stroke-width="1.2"/>
            <rect x="64" y="42" width="14" height="38" rx="2" fill="#0ea5e9" fill-opacity="0.4" stroke="#7dd3fc" stroke-width="1.2"/>
            <rect x="84" y="28" width="16" height="52" rx="2" fill="#3b82f6" fill-opacity="0.45" stroke="#bae6fd" stroke-width="1.4"/>
            <rect x="106" y="48" width="14" height="32" rx="2" fill="#6366f1" fill-opacity="0.4" stroke="#a5b4fc" stroke-width="1.2"/>
        </g>
        <path d="M40 62 L68 46 L92 32 L124 22" stroke="#34d399" stroke-width="1.8" stroke-linecap="round" class="idx-anim-dash"/>
        """
        return _svg_wrapper(svg, "#3b82f6"), "idx-theme-blue"

    # 14. BRENT CRUDE ($/BBL): Nodding Oil Pumpjack Derrick + Barrel Drop
    if "CRUDE" in key or "BRENT" in key:
        svg = """
        <g opacity="0.82">
            <!-- Derrick A-Frame -->
            <path d="M58 80 L76 34 L94 80 M66 60 H86" stroke="#fbbf24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <!-- Animated Nodding Pumpjack Arm -->
            <g class="idx-anim-pump">
                <line x1="48" y1="30" x2="108" y2="42" stroke="#fde68a" stroke-width="3" stroke-linecap="round"/>
                <path d="M42 26 C40 32, 42 40, 48 42" stroke="#f59e0b" stroke-width="3" stroke-linecap="round"/>
                <line x1="45" y1="42" x2="45" y2="76" stroke="#d97706" stroke-width="1.5" stroke-dasharray="3 2"/>
            </g>
            <!-- Oil Drop Ripple -->
            <path d="M114 48 C114 48, 124 62, 124 69 A10 10 0 1 1 104 69 C104 62, 114 48, 114 48 Z"
                  fill="#f59e0b" fill-opacity="0.55" stroke="#fef08a" stroke-width="1.4" class="idx-anim-float"/>
        </g>
        """
        return _svg_wrapper(svg, "#d97706"), "idx-theme-amber"

    # 15. US 10-YR YIELD (%): Bond Treasury Pillars + Yield Sine Curve
    if "YIELD" in key or "10-YR" in key:
        svg = """
        <g opacity="0.55">
            <rect x="64" y="34" width="60" height="44" rx="4" fill="#1e3a8a" fill-opacity="0.35" stroke="#60a5fa" stroke-width="1.3"/>
            <line x1="76" y1="34" x2="76" y2="78" stroke="#93c5fd" stroke-width="1.4"/>
            <line x1="94" y1="34" x2="94" y2="78" stroke="#93c5fd" stroke-width="1.4"/>
            <line x1="112" y1="34" x2="112" y2="78" stroke="#93c5fd" stroke-width="1.4"/>
        </g>
        <path d="M30 66 Q58 26 84 54 T132 34" stroke="#38bdf8" stroke-width="2.4" stroke-linecap="round" class="idx-anim-dash"/>
        """
        return _svg_wrapper(svg, "#3b82f6"), "idx-theme-blue"

    # 16. US DOLLAR INDEX (DXY): Orbital Globe Rings + Crisp $ Watermark
    if "DOLLAR" in key or "DXY" in key:
        svg = """
        <g class="idx-anim-spin-slow" opacity="0.65">
            <circle cx="96" cy="48" r="27" stroke="#34d399" stroke-width="1.4" stroke-dasharray="6 4"/>
            <ellipse cx="96" cy="48" rx="14" ry="27" stroke="#6ee7b7" stroke-width="1.2"/>
            <line x1="69" y1="48" x2="123" y2="48" stroke="#6ee7b7" stroke-width="1.1"/>
        </g>
        <g class="idx-anim-float">
            <circle cx="96" cy="48" r="14" fill="#065f46" fill-opacity="0.7" stroke="#a7f3d0" stroke-width="1.5"/>
            <text x="96" y="54" text-anchor="middle" fill="#ecfdf5" font-size="16" font-weight="800">$</text>
        </g>
        """
        return _svg_wrapper(svg, "#10b981"), "idx-theme-emerald"

    # 17. SENIOR CIO MARKET STANCE: Strategic Bull Radar Sweep
    if "CIO" in key or "STANCE" in key:
        svg = """
        <g opacity="0.7">
            <circle cx="100" cy="48" r="28" stroke="#10b981" stroke-opacity="0.45" stroke-width="1.4"/>
            <circle cx="100" cy="48" r="18" stroke="#34d399" stroke-opacity="0.55" stroke-width="1.2"/>
            <circle cx="100" cy="48" r="8" stroke="#6ee7b7" stroke-opacity="0.7" stroke-width="1.2"/>
            <g class="idx-anim-spin">
                <path d="M100 48 L126 38 A28 28 0 0 1 118 68 Z" fill="#10b981" fill-opacity="0.32"/>
                <line x1="100" y1="48" x2="126" y2="38" stroke="#6ee7b7" stroke-width="2" stroke-linecap="round"/>
            </g>
        </g>
        """
        return _svg_wrapper(svg, "#10b981"), "idx-theme-emerald"

    # 18. INSTITUTIONAL FLOW & PCR: Dual Bidirectional Capital Flow Streams
    if "INSTITUTIONAL" in key or "PCR" in key:
        svg = """
        <g class="idx-anim-flow-right" opacity="0.82">
            <path d="M48 34 H114 L106 27 M114 34 L106 41" stroke="#34d399" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M64 49 H126 L118 42 M126 49 L118 56" stroke="#38bdf8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
        </g>
        <g class="idx-anim-flow-left" opacity="0.72">
            <path d="M122 66 H56 L64 59 M56 66 L64 73" stroke="#a78bfa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </g>
        """
        return _svg_wrapper(svg, "#8b5cf6"), "idx-theme-purple"

    # Default clean Market Pulse Wave
    svg = """
    <path d="M28 66 L56 48 L76 56 L104 28 L130 22" stroke="#38bdf8" stroke-width="2.2"
          stroke-linecap="round" class="idx-anim-dash"/>
    """
    return _svg_wrapper(svg, "#38bdf8"), "idx-theme-blue"
