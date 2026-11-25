import re
import json
import time
from typing import Dict, Any, List, Optional, Tuple
import requests
from bs4 import BeautifulSoup
import config


def clean_numeric_str(val: Any) -> str:
    """Normalizes Screener numeric text strings cleanly without units/newlines."""
    if val is None:
        return ""
    text = str(val).replace("\xa0", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_float_safe(val: Any) -> Optional[float]:
    """Parses numbers from Screener formatted strings (e.g. '₹ 1,28,810 Cr.', '+33%', '96.2')."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    text = clean_numeric_str(val)
    if not text or text in ("N/A", "—", "-", "None", "%"):
        return None
    cleaned = re.sub(r"[₹,%+xX]", "", text)
    cleaned = re.sub(r"(?i)\bcr\.?\b", "", cleaned).strip()
    match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


class FundamentalAnalyst:
    """
    Evaluates consolidated financial health, capital efficiency, quarterly inflection
    (operating leverage & EPS acceleration), cash conversion, capex CWIP pipeline,
    smart-money shareholding accumulation, and GARP valuation with 24-hour disk caching.
    """

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    }
    CACHE_DIR = config.CACHE_DIR / "fundamentals"
    SCHEMA_VERSION = 3

    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _fetch_screener_soup(self, clean_sym: str) -> Tuple[Optional[BeautifulSoup], bool]:
        """Fetches consolidated Screener page first with 429 backoff, falling back to standalone."""
        for suffix, is_consol in [("consolidated/", True), ("", False)]:
            url = f"https://www.screener.in/company/{clean_sym}/{suffix}"
            for attempt in range(2):
                try:
                    r = requests.get(url, headers=self.HEADERS, timeout=10)
                    if r.status_code == 429:
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    if r.status_code == 200 and "top-ratios" in r.text:
                        soup = BeautifulSoup(r.text, "html.parser")
                        if soup.find("ul", id="top-ratios"):
                            return soup, is_consol
                    break
                except Exception:
                    break
        return None, False

    @staticmethod
    def _parse_top_ratios(soup: BeautifulSoup) -> Dict[str, Any]:
        """Extracts cleaned #top-ratios metrics plus numeric values."""
        metrics: Dict[str, Any] = {
            "market_cap_cr": "N/A",
            "current_price": "N/A",
            "stock_pe": "N/A",
            "book_value": "N/A",
            "dividend_yield_pct": "N/A",
            "roce_pct": "N/A",
            "roe_pct": "N/A",
            "debt_to_equity": "N/A",
            "face_value": "N/A",
            "pb_ratio": "N/A",
        }
        ratios_ul = soup.find("ul", id="top-ratios")
        if not ratios_ul:
            return metrics

        for li in ratios_ul.find_all("li"):
            name_el = li.find("span", class_="name")
            val_el = li.find("span", class_="nowrap value")
            if not (name_el and val_el):
                continue
            n = clean_numeric_str(name_el.text).lower()
            raw_v = clean_numeric_str(val_el.text)
            num_v = parse_float_safe(raw_v)

            if "market cap" in n:
                metrics["market_cap_cr"] = f"{int(round(num_v))}" if num_v is not None else raw_v
                metrics["market_cap_num"] = num_v
            elif "current price" in n:
                metrics["current_price"] = f"{num_v:g}" if num_v is not None else raw_v
                metrics["current_price_num"] = num_v
            elif "stock p/e" in n:
                metrics["stock_pe"] = f"{num_v:g}" if num_v is not None else raw_v
                metrics["pe_num"] = num_v
            elif "book value" in n:
                metrics["book_value"] = f"{num_v:g}" if num_v is not None else raw_v
                metrics["book_value_num"] = num_v
            elif "dividend yield" in n:
                metrics["dividend_yield_pct"] = f"{num_v:g}" if num_v is not None else raw_v
            elif "roce" in n:
                metrics["roce_pct"] = f"{num_v:g}" if num_v is not None else raw_v
                metrics["roce_num"] = num_v
            elif "roe" in n:
                metrics["roe_pct"] = f"{num_v:g}" if num_v is not None else raw_v
                metrics["roe_num"] = num_v
            elif "debt" in n and "equity" in n:
                metrics["debt_to_equity"] = f"{num_v:.2f}" if num_v is not None else raw_v
                metrics["debt_to_equity_num"] = num_v
            elif "face value" in n:
                metrics["face_value"] = f"{num_v:g}" if num_v is not None else raw_v

        cmp_n = metrics.get("current_price_num")
        bv_n = metrics.get("book_value_num")
        if cmp_n and bv_n and bv_n > 0:
            pb = round(cmp_n / bv_n, 2)
            metrics["pb_ratio"] = f"{pb:.2f}"
            metrics["pb_num"] = pb

        return metrics

    @staticmethod
    def _parse_ranges_tables(soup: BeautifulSoup) -> Dict[str, Optional[float]]:
        """Extracts 3Y, 5Y, 10Y, and TTM/1Y CAGRs from Screener's .ranges-table blocks."""
        out: Dict[str, Optional[float]] = {
            "sales_cagr_3y": None,
            "sales_cagr_5y": None,
            "sales_growth_ttm": None,
            "profit_cagr_3y": None,
            "profit_cagr_5y": None,
            "profit_growth_ttm": None,
            "roe_3y": None,
            "roe_5y": None,
            "price_cagr_3y": None,
            "price_cagr_5y": None,
        }
        for tbl in soup.select("table.ranges-table"):
            rows = tbl.select("tr")
            if not rows:
                continue
            title = clean_numeric_str(rows[0].text).lower()
            vals: Dict[str, Optional[float]] = {}
            for tr in rows[1:]:
                tds = tr.select("td")
                if len(tds) >= 2:
                    label = clean_numeric_str(tds[0].text).lower().rstrip(":")
                    vals[label] = parse_float_safe(tds[1].text)

            if "sales growth" in title:
                out["sales_cagr_3y"] = vals.get("3 years")
                out["sales_cagr_5y"] = vals.get("5 years")
                out["sales_growth_ttm"] = vals.get("ttm")
            elif "profit growth" in title:
                out["profit_cagr_3y"] = vals.get("3 years")
                out["profit_cagr_5y"] = vals.get("5 years")
                out["profit_growth_ttm"] = vals.get("ttm")
            elif "return on equity" in title:
                out["roe_3y"] = vals.get("3 years")
                out["roe_5y"] = vals.get("5 years")
            elif "stock price cagr" in title:
                out["price_cagr_3y"] = vals.get("3 years")
                out["price_cagr_5y"] = vals.get("5 years")
        return out

    @staticmethod
    def _extract_table_series(soup: BeautifulSoup, container_selector: str) -> Dict[str, List[Optional[float]]]:
        """Extracts row name -> list of floats from the first data-table inside container_selector."""
        series_map: Dict[str, List[Optional[float]]] = {}
        container = soup.select_one(container_selector)
        if not container:
            return series_map
        tbl = container.select_one("table.data-table") or container.select_one("table")
        if not tbl:
            return series_map

        for tr in tbl.select("tbody tr"):
            tds = tr.select("td")
            if len(tds) < 2:
                continue
            raw_label = clean_numeric_str(tds[0].text).replace("+", "").strip().lower()
            # Keep first occurrence to prevent nested/duplicate label overrides
            if raw_label not in series_map:
                series_map[raw_label] = [parse_float_safe(td.text) for td in tds[1:]]
        return series_map

    @staticmethod
    def _find_series(series_map: Dict[str, List[Optional[float]]], keywords: List[str]) -> List[Optional[float]]:
        """Finds first matching row values for any substring keyword in series_map."""
        for kw in keywords:
            for k, v in series_map.items():
                if kw in k:
                    return v
        return []

    @staticmethod
    def _compute_yoy_pct(series: List[Optional[float]], lag: int = 4) -> Optional[float]:
        """Computes YoY % change comparing latest quarter vs `lag` quarters ago."""
        valid = [x for x in series if x is not None]
        if len(valid) <= lag:
            return None
        curr = valid[-1]
        prev = valid[-1 - lag]
        if prev is None or abs(prev) < 1e-6:
            return None
        if prev < 0 and curr > 0:
            return 100.0  # Loss-to-profit turnaround
        return round(((curr - prev) / abs(prev)) * 100.0, 1)

    def _parse_quarterly_inflection(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Detects quarterly operating leverage (OPM expansion) and EPS/PAT acceleration."""
        q_map = self._extract_table_series(soup, "#quarters")
        sales = self._find_series(q_map, ["sales", "revenue"])
        yoy_sales_row = self._find_series(q_map, ["yoy sales growth"])
        opm = self._find_series(q_map, ["opm %", "financing margin %"])
        pat = self._find_series(q_map, ["net profit"])
        eps = self._find_series(q_map, ["eps in rs"])

        # YoY sales growth: prefer Screener's row or compute 4Q lag
        sales_yoy = None
        if yoy_sales_row:
            non_null = [x for x in yoy_sales_row if x is not None]
            if non_null:
                sales_yoy = non_null[-1]
        if sales_yoy is None:
            sales_yoy = self._compute_yoy_pct(sales, lag=4)

        pat_yoy = self._compute_yoy_pct(pat, lag=4)
        pat_qoq = self._compute_yoy_pct(pat, lag=1)
        pat_prev_yoy = None
        valid_pat = [x for x in pat if x is not None]
        if len(valid_pat) >= 6 and valid_pat[-6] and abs(valid_pat[-6]) > 1e-6:
            if valid_pat[-6] < 0 and valid_pat[-2] > 0:
                pat_prev_yoy = 100.0
            else:
                pat_prev_yoy = round(((valid_pat[-2] - valid_pat[-6]) / abs(valid_pat[-6])) * 100.0, 1)

        eps_yoy = self._compute_yoy_pct(eps, lag=4)

        # Operating Margin Expansion (bps): latest quarter vs 4 quarters ago
        opm_latest = None
        opm_year_ago = None
        opm_expansion_bps = None
        valid_opm = [x for x in opm if x is not None]
        if valid_opm:
            opm_latest = valid_opm[-1]
            if len(valid_opm) >= 5:
                opm_year_ago = valid_opm[-5]
                opm_expansion_bps = round((opm_latest - opm_year_ago) * 100.0, 0)
            elif len(valid_opm) >= 3:
                opm_year_ago = valid_opm[-3]
                opm_expansion_bps = round((opm_latest - opm_year_ago) * 100.0, 0)

        # Sequential (QoQ) profit expansion streak check
        is_sequential_accel = False
        if len(valid_pat) >= 3:
            is_sequential_accel = valid_pat[-1] > valid_pat[-2] > valid_pat[-3] and valid_pat[-1] > 0

        return {
            "qtr_sales_yoy_pct": sales_yoy,
            "qtr_pat_qoq_pct": pat_qoq,
            "qtr_pat_yoy_pct": pat_yoy,
            "qtr_pat_prev_yoy_pct": pat_prev_yoy,
            "qtr_eps_yoy_pct": eps_yoy,
            "opm_latest_pct": opm_latest,
            "opm_year_ago_pct": opm_year_ago,
            "opm_expansion_bps": opm_expansion_bps,
            "is_sequential_pat_accel": is_sequential_accel,
            "is_financial_sector": any("financing margin" in k for k in q_map.keys()),
        }

    def _parse_balance_cash_shareholding(self, soup: BeautifulSoup, is_financial: bool) -> Dict[str, Any]:
        """Extracts D/E, CWIP capex, CFO/PAT, #ratios multi-year ROCE delta, and Promoter/FII/DII flows."""
        bs_map = self._extract_table_series(soup, "#balance-sheet")
        cf_map = self._extract_table_series(soup, "#cash-flow")
        pl_map = self._extract_table_series(soup, "#profit-loss")
        rat_map = self._extract_table_series(soup, "#ratios")

        # Shareholding: strictly prefer quarterly-shp tab if present
        sh_sel = "#quarterly-shp" if soup.select_one("#quarterly-shp") else "#shareholding"
        sh_map = self._extract_table_series(soup, sh_sel)

        # Multi-year ROCE % trajectory from #ratios table
        roce_seq = [x for x in self._find_series(rat_map, ["roce %"]) if x is not None]
        roce_latest_tbl = roce_seq[-1] if roce_seq else None
        roce_prev_tbl = roce_seq[-2] if len(roce_seq) >= 2 else None
        roce_delta_tbl = (
            round(roce_latest_tbl - roce_prev_tbl, 1)
            if (roce_latest_tbl is not None and roce_prev_tbl is not None)
            else None
        )

        borrowings = [x for x in self._find_series(bs_map, ["borrowings"]) if x is not None]
        equity = [x for x in self._find_series(bs_map, ["equity capital"]) if x is not None]
        reserves = [x for x in self._find_series(bs_map, ["reserves"]) if x is not None]
        deposits = [x for x in self._find_series(bs_map, ["deposits"]) if x is not None]
        fixed_assets = [x for x in self._find_series(bs_map, ["fixed assets"]) if x is not None]
        cwip = [x for x in self._find_series(bs_map, ["cwip"]) if x is not None]

        if deposits:
            is_financial = True

        debt_to_equity = None
        if borrowings and equity and reserves:
            net_worth = equity[-1] + reserves[-1]
            if net_worth > 0:
                debt_to_equity = round(borrowings[-1] / net_worth, 2)

        # CWIP Capex expansion signal
        cwip_latest = cwip[-1] if cwip else 0.0
        cwip_prev = cwip[-2] if len(cwip) >= 2 else cwip_latest
        cwip_growth_pct = round(((cwip_latest - cwip_prev) / abs(cwip_prev)) * 100.0, 1) if cwip_prev > 1 else 0.0
        cwip_to_fa_pct = round((cwip_latest / fixed_assets[-1]) * 100.0, 1) if (fixed_assets and fixed_assets[-1] > 1) else 0.0

        # Cash Flow Quality (3Y CFO / PAT and latest CFO/EBITDA)
        cfo = [x for x in self._find_series(cf_map, ["cash from operating activity"]) if x is not None]
        fcf = [x for x in self._find_series(cf_map, ["free cash flow"]) if x is not None]
        cfo_ebitda = [x for x in self._find_series(cf_map, ["cfo/ebitda"]) if x is not None]
        annual_pat = [x for x in self._find_series(pl_map, ["net profit"]) if x is not None]

        cfo_to_pat_3y = None
        if len(cfo) >= 3 and len(annual_pat) >= 3:
            sum_cfo = sum(cfo[-3:])
            # Ignore TTM column in P&L if headers include TTM, approximate using matching length heuristic
            sum_pat = sum(annual_pat[-4:-1]) if len(annual_pat) > len(cfo) else sum(annual_pat[-3:])
            if sum_pat > 0:
                cfo_to_pat_3y = round(sum_cfo / sum_pat, 2)

        cfo_ebitda_latest = cfo_ebitda[-1] if cfo_ebitda else None
        fcf_latest = fcf[-1] if fcf else None

        # Shareholding Intelligence (Promoters, FIIs, DIIs)
        promoters = [x for x in self._find_series(sh_map, ["promoters"]) if x is not None]
        fiis = [x for x in self._find_series(sh_map, ["fiis"]) if x is not None]
        diis = [x for x in self._find_series(sh_map, ["diis"]) if x is not None]
        public = [x for x in self._find_series(sh_map, ["public"]) if x is not None]

        prom_latest = promoters[-1] if promoters else None
        prom_qoq_delta = round(promoters[-1] - promoters[-2], 2) if len(promoters) >= 2 else 0.0
        prom_4q_prev = promoters[-5] if len(promoters) >= 5 else (promoters[0] if promoters else None)
        prom_4q_delta = round(promoters[-1] - prom_4q_prev, 2) if (prom_latest is not None and prom_4q_prev is not None) else 0.0

        fii_latest = fiis[-1] if fiis else 0.0
        dii_latest = diis[-1] if diis else 0.0
        inst_latest = round(fii_latest + dii_latest, 2)

        fii_4q_prev = fiis[-5] if len(fiis) >= 5 else (fiis[0] if fiis else fii_latest)
        dii_4q_prev = diis[-5] if len(diis) >= 5 else (diis[0] if diis else dii_latest)
        inst_4q_delta = round(inst_latest - (fii_4q_prev + dii_4q_prev), 2)

        pub_delta = 0.0
        if len(public) >= 2:
            prev_pub = public[-5] if len(public) >= 5 else public[0]
            pub_delta = round(public[-1] - prev_pub, 2)

        # Promoter pledge parse from pros/cons text or shareholding extras if available
        pledge_pct = 0.0
        for row_k, vals in sh_map.items():
            if "pledg" in row_k and vals:
                non_null = [v for v in vals if v is not None]
                if non_null:
                    pledge_pct = non_null[-1]

        return {
            "is_financial_sector": is_financial,
            "debt_to_equity": debt_to_equity,
            "roce_latest_tbl_pct": roce_latest_tbl,
            "roce_prev_pct": roce_prev_tbl,
            "roce_delta_pct": roce_delta_tbl,
            "cwip_cr": cwip_latest,
            "cwip_growth_pct": cwip_growth_pct,
            "cwip_to_fixed_assets_pct": cwip_to_fa_pct,
            "cfo_latest_cr": cfo[-1] if cfo else None,
            "fcf_latest_cr": fcf_latest,
            "cfo_ebitda_pct": cfo_ebitda_latest,
            "cfo_to_pat_3y": cfo_to_pat_3y,
            "promoter_pct": prom_latest,
            "promoter_qoq_delta_pct": prom_qoq_delta,
            "promoter_4q_delta_pct": prom_4q_delta,
            "promoter_pledge_pct": pledge_pct,
            "fii_pct": fii_latest,
            "dii_pct": dii_latest,
            "inst_total_pct": inst_latest,
            "inst_4q_delta_pct": inst_4q_delta,
            "public_4q_delta_pct": pub_delta,
        }

    def analyze(self, symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Performs 360-degree consolidated fundamental & multibagger inflection audit."""
        clean_sym = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
        cache_path = self.CACHE_DIR / f"{clean_sym}.json"

        # Check 24-hour disk cache & verify schema version
        if not force_refresh and cache_path.exists():
            try:
                mtime = cache_path.stat().st_mtime
                if (time.time() - mtime) < 86400:
                    with open(cache_path, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                        if cached.get("schema_version") == self.SCHEMA_VERSION:
                            return cached
            except Exception:
                pass

        soup, is_consolidated = self._fetch_screener_soup(clean_sym)

        metrics: Dict[str, Any] = {
            "market_cap_cr": "N/A",
            "current_price": "N/A",
            "stock_pe": "N/A",
            "book_value": "N/A",
            "dividend_yield_pct": "N/A",
            "roce_pct": "N/A",
            "roe_pct": "N/A",
            "debt_to_equity": "N/A",
            "face_value": "N/A",
            "pb_ratio": "N/A",
        }
        strengths: List[str] = []
        red_flags: List[str] = []
        ranges: Dict[str, Any] = {}
        inflection: Dict[str, Any] = {}
        balance_inst: Dict[str, Any] = {}
        quality_score = 4.5
        inflection_score = 4.5
        valuation_score = 5.0

        if soup is not None:
            metrics = self._parse_top_ratios(soup)
            ranges = self._parse_ranges_tables(soup)
            inflection = self._parse_quarterly_inflection(soup)
            balance_inst = self._parse_balance_cash_shareholding(
                soup, is_financial=inflection.get("is_financial_sector", False)
            )

            # Populate debt_to_equity inside metrics if computed from Balance Sheet
            if balance_inst.get("debt_to_equity") is not None and metrics["debt_to_equity"] == "N/A":
                metrics["debt_to_equity"] = f"{balance_inst['debt_to_equity']:.2f}"

            pros = [clean_numeric_str(li.text) for li in soup.select(".pros ul li") if clean_numeric_str(li.text)]
            cons = [clean_numeric_str(li.text) for li in soup.select(".cons ul li") if clean_numeric_str(li.text)]

            # Check pros/cons for pledge mention if pledge table row wasn't explicit
            for c_item in cons:
                if "pledg" in c_item.lower():
                    p_val = parse_float_safe(c_item)
                    if p_val is not None and balance_inst.get("promoter_pledge_pct", 0.0) == 0.0:
                        balance_inst["promoter_pledge_pct"] = p_val

            # --- 1. Capital Efficiency & Balance Sheet Quality Score (0-10) ---
            roce_num = metrics.get("roce_num")
            roe_num = metrics.get("roe_num")
            de_num = balance_inst.get("debt_to_equity")
            is_fin = balance_inst.get("is_financial_sector", False)
            cfo_pat = balance_inst.get("cfo_to_pat_3y")
            cfo_ebitda = balance_inst.get("cfo_ebitda_pct")

            if roce_num is not None:
                if roce_num >= 25.0:
                    quality_score += 2.5
                    strengths.append(f"Elite Capital Efficiency (ROCE: {roce_num:.1f}%)")
                elif roce_num >= config.FUNDAMENTAL_CONFIG["MIN_ROCE"]:
                    quality_score += 1.6
                    strengths.append(f"Strong Capital Return (ROCE: {roce_num:.1f}%)")
                elif roce_num < 9.0:
                    quality_score -= 1.2
                    red_flags.append(f"Sub-par ROCE ({roce_num:.1f}%)")

            if roe_num is not None:
                if roe_num >= 20.0:
                    quality_score += 1.5
                    strengths.append(f"Superior ROE: {roe_num:.1f}%")
                elif roe_num >= config.FUNDAMENTAL_CONFIG["MIN_ROE"]:
                    quality_score += 0.8
                elif roe_num < 8.0:
                    quality_score -= 0.8

            if not is_fin and de_num is not None:
                if de_num <= 0.25:
                    quality_score += 1.2
                    strengths.append(f"Fortress Balance Sheet (D/E: {de_num:.2f}x)")
                elif de_num <= config.FUNDAMENTAL_CONFIG["MAX_DEBT_TO_EQUITY"]:
                    quality_score += 0.5
                else:
                    quality_score -= 1.5
                    red_flags.append(f"Elevated Leverage (D/E: {de_num:.2f}x)")

            if (cfo_pat is not None and cfo_pat >= config.MULTIBAGGER_CONFIG["MIN_CFO_TO_PAT_3Y"]) or (
                cfo_ebitda is not None and cfo_ebitda >= 75.0
            ):
                quality_score += 1.0
                if cfo_ebitda is not None:
                    strengths.append(f"Cash Generative Profits (CFO/EBITDA: {cfo_ebitda:.0f}%)")
            elif cfo_pat is not None and cfo_pat < 0.4:
                quality_score -= 1.2
                red_flags.append(f"Weak Operating Cash Conversion (3Y CFO/PAT: {cfo_pat:.2f}x)")

            pledge_pct = balance_inst.get("promoter_pledge_pct", 0.0)
            if pledge_pct > config.FUNDAMENTAL_CONFIG["MAX_PROMOTER_PLEDGE"]:
                quality_score -= 1.8
                red_flags.append(f"High Promoter Pledge Risk ({pledge_pct:.1f}%)")

            # --- 2. Earnings Inflection & Reinvestment Pipeline Score (0-10) ---
            opm_exp = inflection.get("opm_expansion_bps")
            q_pat_yoy = inflection.get("qtr_pat_yoy_pct")
            q_sales_yoy = inflection.get("qtr_sales_yoy_pct")
            pat_3y = ranges.get("profit_cagr_3y")
            sales_3y = ranges.get("sales_cagr_3y")
            pat_ttm = ranges.get("profit_growth_ttm")
            inst_delta = balance_inst.get("inst_4q_delta_pct", 0.0)
            cwip_growth = balance_inst.get("cwip_growth_pct", 0.0)
            cwip_ratio = balance_inst.get("cwip_to_fixed_assets_pct", 0.0)

            if opm_exp is not None:
                if opm_exp >= 300:
                    inflection_score += 2.2
                    strengths.append(f"Sharp Margin Inflection (OPM +{int(opm_exp)} bps YoY)")
                elif opm_exp >= config.MULTIBAGGER_CONFIG["MIN_OPM_EXPANSION_BPS"]:
                    inflection_score += 1.3
                    strengths.append(f"Expanding Operating Margins (+{int(opm_exp)} bps)")
                elif opm_exp <= -300:
                    inflection_score -= 1.5
                    red_flags.append(f"Operating Margin Compression ({int(opm_exp)} bps YoY)")

            if q_pat_yoy is not None:
                if q_pat_yoy >= 40.0:
                    inflection_score += 2.0
                    strengths.append(f"Explosive Quarterly PAT Surge (+{q_pat_yoy:.1f}% YoY)")
                elif q_pat_yoy >= config.MULTIBAGGER_CONFIG["MIN_QTR_PAT_YOY_SURGE"]:
                    inflection_score += 1.2
                elif q_pat_yoy < -15.0:
                    inflection_score -= 1.2
                    red_flags.append(f"Quarterly Earnings Contraction ({q_pat_yoy:.1f}% YoY)")

            if inflection.get("is_sequential_pat_accel"):
                inflection_score += 0.8

            if q_sales_yoy is not None and q_sales_yoy >= 18.0:
                inflection_score += 0.8

            if pat_3y is not None and pat_3y >= 20.0:
                inflection_score += 1.0
                strengths.append(f"Multi-Year Profit Compounding (3Y CAGR: +{pat_3y:.0f}%)")
            elif pat_3y is not None and pat_3y < 0 and (q_pat_yoy or 0) < 15.0:
                inflection_score -= 0.8

            if sales_3y is not None and sales_3y >= 15.0:
                inflection_score += 0.6

            if inst_delta >= 1.5:
                inflection_score += 1.0
                strengths.append(f"Smart Money Accumulation (FII+DII {inst_delta:+.1f}% over 4Q)")
            elif inst_delta <= -2.5:
                inflection_score -= 0.8
                red_flags.append(f"Institutional Distribution (FII+DII {inst_delta:+.1f}% over 4Q)")

            prom_qoq = balance_inst.get("promoter_qoq_delta_pct", 0.0)
            prom_4q = balance_inst.get("promoter_4q_delta_pct", 0.0)
            if prom_qoq > 0.05 or prom_4q > 0.1:
                inflection_score += 0.9
                best_p = prom_qoq if prom_qoq > 0.05 else prom_4q
                strengths.append(f"Promoter Stake Increased (+{best_p:.2f}%)")

            roce_delta = balance_inst.get("roce_delta_pct")
            if roce_delta is not None and roce_delta > 0.0:
                inflection_score += 0.8
                strengths.append(f"Expanding ROCE Efficiency (+{roce_delta:.1f}% YoY)")

            q_pat_qoq = inflection.get("qtr_pat_qoq_pct")
            if q_pat_qoq is not None and q_pat_qoq >= 15.0:
                inflection_score += 0.6

            if cwip_ratio >= 15.0 or cwip_growth >= 25.0:
                inflection_score += 0.7
                strengths.append(f"Capex Capacity Runway Active (CWIP: ₹{balance_inst.get('cwip_cr', 0):,.0f} Cr)")

            # --- 3. GARP Valuation Score (PEG & Inflection-Aware) ---
            pe_num = metrics.get("pe_num")
            # Effective growth benchmark: best forward-aligned growth signal
            growth_candidates = [g for g in [pat_3y, pat_ttm, q_pat_yoy] if g is not None and g > 0]
            eff_growth = max(growth_candidates) if growth_candidates else None
            peg_ratio = None

            if pe_num is not None and pe_num > 0:
                if eff_growth and eff_growth >= 5.0:
                    peg_ratio = round(pe_num / eff_growth, 2)
                    metrics["peg_ratio"] = f"{peg_ratio:.2f}"
                    metrics["peg_num"] = peg_ratio

                    if peg_ratio <= 1.0:
                        valuation_score += 3.0
                        strengths.append(f"Deep GARP Value (PEG: {peg_ratio:.2f}x)")
                    elif peg_ratio <= config.MULTIBAGGER_CONFIG["MAX_PEG_RATIO"]:
                        valuation_score += 1.8
                        strengths.append(f"Reasonable GARP Multiple (PEG: {peg_ratio:.2f}x)")
                    elif peg_ratio > 3.0 and (q_pat_yoy or 0) < 20.0:
                        valuation_score -= 1.8
                        red_flags.append(f"Expensive Valuation vs Growth (PEG: {peg_ratio:.2f}x)")
                else:
                    if pe_num <= 22.0:
                        valuation_score += 1.5
                    elif pe_num > 75.0:
                        # Avoid unfair penalty when margin/PAT turnaround inflection is active
                        is_turning = (opm_exp or 0) >= 200 and (q_pat_yoy or 0) >= 30.0
                        if not is_turning:
                            valuation_score -= 1.2
                            red_flags.append(f"High Multiple Without Acceleration (P/E: {pe_num:.1f}x)")

            metrics["peg_ratio"] = metrics.get("peg_ratio", "N/A")

            # Append Screener's top curated pros/cons that aren't redundant
            for p_txt in pros:
                if p_txt not in strengths:
                    strengths.append(p_txt)
            for c_txt in cons:
                if c_txt not in red_flags:
                    red_flags.append(c_txt)
        else:
            strengths.append("Standard market capitalization profile")

        quality_score = max(1.0, min(round(quality_score, 1), 10.0))
        inflection_score = max(1.0, min(round(inflection_score, 1), 10.0))
        valuation_score = max(1.0, min(round(valuation_score, 1), 10.0))

        # Overall fundamental score blends Quality (45%), Inflection/Growth (35%), GARP Valuation (20%)
        final_fund_score = max(
            1.0,
            min(round((quality_score * 0.45) + (inflection_score * 0.35) + (valuation_score * 0.20), 1), 10.0),
        )

        if not strengths:
            strengths.append("Established market presence")
        if not red_flags:
            red_flags.append("Standard market & execution risks apply")

        result = {
            "schema_version": self.SCHEMA_VERSION,
            "is_consolidated": is_consolidated,
            "score": final_fund_score,
            "quality_score": quality_score,
            "inflection_score": inflection_score,
            "valuation_score": valuation_score,
            "metrics": metrics,
            "ranges": ranges,
            "inflection": inflection,
            "balance_inst": balance_inst,
            "strengths": strengths[:5],
            "red_flags": red_flags[:4],
        }

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
        except Exception:
            pass

        return result
