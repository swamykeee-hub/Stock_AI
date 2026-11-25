import json
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import config

IST = timezone(timedelta(hours=5, minutes=30))


def _format_age(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s ago"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{seconds / 3600:.1f}h ago"
    return f"{seconds / 86400:.1f}d ago"


def _inspect_cache_file(
    label: str,
    path: Path,
    fresh_threshold_sec: int,
    stale_threshold_sec: int,
    detail_builder=None,
) -> Dict[str, Any]:
    """Inspects cache file age and structured contents cleanly without network calls."""
    if not path.exists():
        return {
            "feed": label,
            "status": "MISSING",
            "color": "#ef4444",
            "age": "Not built",
            "updated_at": "—",
            "detail": "Cache file missing",
        }

    age_sec = max(0.0, time.time() - path.stat().st_mtime)
    updated_at = datetime.fromtimestamp(path.stat().st_mtime, tz=IST).strftime("%d-%b %H:%M IST")
    data: Any = None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        return {
            "feed": label,
            "status": "ERROR",
            "color": "#ef4444",
            "age": _format_age(age_sec),
            "updated_at": updated_at,
            "detail": f"Unreadable JSON: {exc}",
        }

    detail = detail_builder(data) if detail_builder else "Cache available"
    if age_sec <= fresh_threshold_sec:
        status, color = "FRESH", "#10b981"
    elif age_sec <= stale_threshold_sec:
        status, color = "CACHED", "#38bdf8"
    else:
        status, color = "STALE", "#f59e0b"

    return {
        "feed": label,
        "status": status,
        "color": color,
        "age": _format_age(age_sec),
        "updated_at": updated_at,
        "detail": detail,
    }


def collect_feed_health(scan_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Audits freshness & operational status of all upstream data feeds
    (Yahoo Finance, AMFI NAVs, Groww Option Chain / FII-DII, Moneycontrol Movers, IPOs).
    """
    scan_file = Path(config.SCHEDULE_CONFIG.get("DAILY_SCAN_FILE", config.REPORTS_DIR / "latest_daily_scan.json"))
    cmps_file = config.CACHE_DIR / "all_stock_cmps.json"
    mf_file = config.CACHE_DIR / "mutual_funds_cache.json"
    inst_file = config.CACHE_DIR / "institutional_flow.json"
    movers_file = config.CACHE_DIR / "market_movers.json"
    corp_file = config.CACHE_DIR / "corporate_actions.json"

    feeds: List[Dict[str, Any]] = []

    # 1. Yahoo Finance NSE Quotes & Indices
    feeds.append(
        _inspect_cache_file(
            "Yahoo NSE Quotes",
            scan_file if scan_file.exists() else cmps_file,
            fresh_threshold_sec=900,
            stale_threshold_sec=43200,
            detail_builder=lambda d: (
                f"{len(d.get('indices', {}))} indices, {len(d.get('top_bullish_stocks', []))} picks"
                if isinstance(d, dict)
                else f"{len(d)} quotes"
            ),
        )
    )

    # 2. AMFI Mutual Fund NAVs
    feeds.append(
        _inspect_cache_file(
            "AMFI Live NAVs",
            mf_file,
            fresh_threshold_sec=43200,
            stale_threshold_sec=86400,
            detail_builder=lambda d: (
                f"{sum(1 for x in d if x.get('is_live_nav'))}/{len(d)} Live NAVs"
                if isinstance(d, list)
                else "Available"
            ),
        )
    )

    # 3. Groww Nifty PCR & Moneycontrol FII/DII
    def _inst_detail(d: Any) -> str:
        if not isinstance(d, dict):
            return "Cached"
        deriv = d.get("derivatives", {})
        pcr = deriv.get("pcr", "—")
        st = deriv.get("status", "CACHED")
        return f"PCR {pcr} ({st})"

    feeds.append(
        _inspect_cache_file(
            "FII/DII & Nifty PCR",
            inst_file,
            fresh_threshold_sec=900,
            stale_threshold_sec=43200,
            detail_builder=_inst_detail,
        )
    )

    # 4. Moneycontrol Intraday Top Gainers / Losers
    feeds.append(
        _inspect_cache_file(
            "NSE Movers Feed",
            movers_file,
            fresh_threshold_sec=900,
            stale_threshold_sec=43200,
            detail_builder=lambda d: (
                f"{len(d.get('top_gainers', []))} gainers / {len(d.get('top_losers', []))} losers"
                if isinstance(d, dict)
                else "Cached"
            ),
        )
    )

    # 5. Corporate Actions & Dividends Calendar
    feeds.append(
        _inspect_cache_file(
            "Corporate Actions",
            corp_file,
            fresh_threshold_sec=43200,
            stale_threshold_sec=172800,
            detail_builder=lambda d: (
                f"{d.get('total_events', 0)} events tracked" if isinstance(d, dict) else "Cached"
            ),
        )
    )

    healthy_count = sum(1 for f in feeds if f["status"] in ("FRESH", "CACHED"))
    checked_at = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")

    return {
        "checked_at": checked_at,
        "healthy_count": healthy_count,
        "total_feeds": len(feeds),
        "feeds": feeds,
    }
