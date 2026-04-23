# UTF-8 stdout fix — MUST be first (Windows cp1252 emoji fix)
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


import json
import os
import calendar
import argparse
import time
import requests
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from app.database import SessionLocal, engine
from app.models import Base, Business, GMBPerformance, GMBInsight
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request


Base.metadata.create_all(bind=engine)


# ============================================================
# CONFIG
# ============================================================

TOKEN_FILE    = os.path.join(os.path.dirname(__file__), "token.json")
ACCOUNT_ID    = "114295392753759292048"
REVISION_DAYS = 7

DEFAULT_SYNC_MONTHS = 3
MAX_HISTORY_MONTHS  = 18

SYNC_VERSION = "5.3"

# Retry config for transient Google API errors
MAX_RETRIES  = 3
RETRY_BACKOFF = 2.0  # seconds — doubles on each retry


def get_months_list(n: int) -> list[tuple[int, int, str]]:
    n     = min(n, MAX_HISTORY_MONTHS)
    today = date.today()
    months = []
    for i in range(n - 1, -1, -1):
        month = today.month - i
        year  = today.year
        while month <= 0:
            month += 12
            year  -= 1
        label = date(year, month, 1).strftime("%b").upper()
        months.append((year, month, label))
    return months


def get_months_from_range(start_date: str, end_date: str) -> list[tuple[int, int, str]]:
    from_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    to_date   = datetime.strptime(end_date,   "%Y-%m-%d").date()

    months = []
    y, m = from_date.year, from_date.month
    while (y, m) <= (to_date.year, to_date.month):
        label = date(y, m, 1).strftime("%b").upper()
        months.append((y, m, label))
        m += 1
        if m > 12:
            m = 1
            y += 1

    if len(months) > MAX_HISTORY_MONTHS:
        print(f"[WARN] Date range covers {len(months)} months — capping at {MAX_HISTORY_MONTHS}")
        months = months[:MAX_HISTORY_MONTHS]

    return months


def _is_revision_window(year: int, month: int) -> bool:
    """True if this month falls within the last REVISION_DAYS days."""
    today    = date.today()
    cutoff   = today - timedelta(days=REVISION_DAYS)
    last_day = calendar.monthrange(year, month)[1]
    month_end = date(year, month, last_day)
    return month_end >= cutoff


# ============================================================
# METRIC DEFINITIONS
# ============================================================

GMB_METRICS = [
    "BUSINESS_IMPRESSIONS_DESKTOP_SEARCH",
    "BUSINESS_IMPRESSIONS_MOBILE_SEARCH",
    "BUSINESS_IMPRESSIONS_DESKTOP_MAPS",
    "BUSINESS_IMPRESSIONS_MOBILE_MAPS",
    "CALL_CLICKS",
    "WEBSITE_CLICKS",
    "BUSINESS_DIRECTION_REQUESTS",
    "BUSINESS_CONVERSATIONS",
    "BUSINESS_BOOKINGS",
    "BUSINESS_PROFILE_CLICKS",
]

VIEW_METRICS = [
    "BUSINESS_IMPRESSIONS_DESKTOP_SEARCH",
    "BUSINESS_IMPRESSIONS_MOBILE_SEARCH",
    "BUSINESS_IMPRESSIONS_DESKTOP_MAPS",
    "BUSINESS_IMPRESSIONS_MOBILE_MAPS",
]

INTERACTION_METRICS = [
    "CALL_CLICKS",
    "WEBSITE_CLICKS",
    "BUSINESS_DIRECTION_REQUESTS",
    "BUSINESS_CONVERSATIONS",
    "BUSINESS_BOOKINGS",
]


# ============================================================
# AUTH
# ============================================================

def load_credentials() -> Credentials | None:
    if not os.path.exists(TOKEN_FILE):
        print(f"[WARN] token.json not found at {TOKEN_FILE} — skipping live API fetch")
        return None
    creds = Credentials.from_authorized_user_file(TOKEN_FILE)
    if creds.expired and creds.refresh_token:
        print("[INFO] Refreshing access token...")
        creds.refresh(Request())
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "token":         creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri":     creds.token_uri,
                "client_id":     creds.client_id,
                "client_secret": creds.client_secret,
                "scopes":        list(creds.scopes),
            }, f, indent=2)
        print("[OK] Token refreshed")
    return creds


# ============================================================
# GMB API — FETCH ALL LOCATIONS
# ============================================================

def fetch_gmb_locations(headers: dict) -> list[dict]:
    url    = f"https://mybusinessbusinessinformation.googleapis.com/v1/accounts/{ACCOUNT_ID}/locations"
    params = {
        "readMask": "name,title,storefrontAddress,websiteUri,phoneNumbers",
        "pageSize": 100,
    }
    try:
        r    = requests.get(url, params=params, headers=headers, timeout=15)
        data = r.json()
        if "error" in data:
            print(f"[WARN] Locations API error: {data['error']['message']}")
            return []
        locations = data.get("locations", [])
        print(f"[OK] Fetched {len(locations)} locations from GMB API")
        return locations
    except Exception as e:
        print(f"[WARN] Failed to fetch locations: {e}")
        return []


# ============================================================
# GMB API — DAILY FETCH (with retry)
# ============================================================

def _get_with_retry(url: str, params: dict, headers: dict) -> dict:
    """GET with exponential backoff retry on 429/503."""
    delay = RETRY_BACKOFF
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r    = requests.get(url, params=params, headers=headers, timeout=15)
            data = r.json()
            if "error" in data:
                code = data["error"].get("code", 0)
                if code in (429, 503) and attempt < MAX_RETRIES:
                    print(f"      [RETRY {attempt}/{MAX_RETRIES}] Rate limited — waiting {delay:.0f}s...")
                    time.sleep(delay)
                    delay *= 2
                    continue
            return data
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES:
                print(f"      [RETRY {attempt}/{MAX_RETRIES}] Timeout — waiting {delay:.0f}s...")
                time.sleep(delay)
                delay *= 2
            else:
                raise
    return {}


def get_daily_metric(
    location_name: str,
    metric: str,
    year: int,
    month: int,
    headers: dict
) -> dict[str, int]:
    last_day = calendar.monthrange(year, month)[1]
    today    = date.today()
    cap_day  = min(last_day, today.day if (year == today.year and month == today.month) else last_day)

    url = (
        f"https://businessprofileperformance.googleapis.com/v1/"
        f"{location_name}:getDailyMetricsTimeSeries"
    )
    params = {
        "dailyMetric":                metric,
        "dailyRange.startDate.year":  year,
        "dailyRange.startDate.month": month,
        "dailyRange.startDate.day":   1,
        "dailyRange.endDate.year":    year,
        "dailyRange.endDate.month":   month,
        "dailyRange.endDate.day":     cap_day,
    }
    try:
        data = _get_with_retry(url, params, headers)
        if "error" in data:
            code = data["error"].get("code", 0)
            msg  = data["error"].get("message", "")
            if code == 400 and "BUSINESS_PROFILE_CLICKS" in metric:
                print(f"      [INFO] BUSINESS_PROFILE_CLICKS not supported — will use sub-metric sum as fallback")
            else:
                print(f"      [WARN] API error for {metric}: {msg}")
            return {}
        daily: dict[str, int] = {}
        for v in data.get("timeSeries", {}).get("datedValues", []):
            d = v.get("date", {})
            if not d:
                continue
            key        = (
                f"{d.get('year', year)}-"
                f"{str(d.get('month', month)).zfill(2)}-"
                f"{str(d.get('day', 1)).zfill(2)}"
            )
            daily[key] = int(v.get("value") or 0)
        return daily
    except Exception as e:
        print(f"      [WARN] Request failed for {metric}: {e}")
        return {}


def fetch_daily_data_for_month(
    location_name: str,
    year: int,
    month: int,
    headers: dict
) -> dict[str, dict[str, int]]:
    result = {}
    for metric in GMB_METRICS:
        daily          = get_daily_metric(location_name, metric, year, month, headers)
        result[metric] = daily
        total          = sum(daily.values())
        print(f"      [OK] {metric}: {total}")
    return result


# ============================================================
# UTIL — insightsValue parser
# ============================================================

def _parse_insights_value(raw) -> tuple[int, bool]:
    if raw is None:
        return 0, True
    if isinstance(raw, dict):
        if raw.get("threshold") == "LESS_THAN_FIFTEEN":
            return 0, True
        inner = raw.get("value")
        if inner is None:
            return 0, True
        raw = inner
    try:
        val = int(raw)
        return val, False
    except (ValueError, TypeError):
        return 0, True


# ============================================================
# GMB API — SEARCH KEYWORDS
# ============================================================

def fetch_search_keywords(
    location_name: str,
    year: int,
    month: int,
    headers: dict
) -> list[dict]:
    url = (
        f"https://businessprofileperformance.googleapis.com/v1/"
        f"{location_name}/searchkeywords/impressions/monthly"
    )
    params = {
        "monthlyRange.startMonth.year":  year,
        "monthlyRange.startMonth.month": month,
        "monthlyRange.endMonth.year":    year,
        "monthlyRange.endMonth.month":   month,
    }
    try:
        data = _get_with_retry(url, params, headers)
        if "error" in data:
            print(f"      [WARN] Keywords API: {data['error']['message']}")
            return []
        raw      = data.get("searchKeywordsCounts", [])
        keywords = []
        for item in raw:
            kw    = item.get("searchKeyword", "").strip()
            value = item.get("insightsValue")
            if kw:
                parsed, lt15 = _parse_insights_value(value)
                keywords.append({
                    "searchKeyword": kw,
                    "insightsValue": parsed,
                    "isLessThan15":  lt15,
                })
        print(f"      [OK] Keywords: {len(keywords)} queries found")
        return keywords
    except Exception as e:
        print(f"      [WARN] Keywords fetch failed: {e}")
        return []


# ============================================================
# SMART SKIP
# ============================================================

def _month_already_synced(db: Session, business_id: int, year: int, month: int) -> bool:
    """
    Returns True if month is already synced and NOT in the revision window.
    REVISION_DAYS (7) months are always re-synced to pick up late Google data.
    """
    # Always re-sync current month and revision window
    if _is_revision_window(year, month):
        return False

    metric_date = datetime(year, month, 1)
    existing    = db.query(GMBPerformance).filter(
        GMBPerformance.business_id == business_id,
        GMBPerformance.metric_date == metric_date,
    ).first()

    if not existing:
        return False

    has_data = (
        (getattr(existing, "views_search", 0) or 0) +
        (getattr(existing, "views_maps",   0) or 0) +
        (getattr(existing, "actions_phone_calls", 0) or 0)
    ) > 0

    return has_data


# ============================================================
# BUSINESS MATCHING
# ============================================================

def get_or_create_business(db: Session, business_name: str, location_id: str) -> Business:
    business = db.query(Business).filter(
        Business.google_place_id == location_id
    ).first()

    if not business:
        business = db.query(Business).filter(
            (Business.name == business_name) |
            (Business.business_name == business_name)
        ).first()

    if not business:
        business = Business(
            name            = business_name,
            business_name   = business_name,
            google_place_id = location_id,
            phone           = "N/A",
            status          = "active",
        )
        db.add(business)
        db.flush()
        print(f"   [NEW] Created: {business_name} (ID: {business.id})")
    else:
        if not business.google_place_id:
            business.google_place_id = location_id
        print(f"   [MATCH] {business.business_name or business.name} (ID: {business.id})")

    return business


# ============================================================
# HELPER — resolve total_profile_interactions
# ============================================================

def _resolve_total_interactions(monthly_totals: dict[str, int]) -> tuple[int, bool]:
    """
    v5.2: Use BUSINESS_PROFILE_CLICKS as authoritative total_interactions.
    Falls back to sub-metric sum only if BUSINESS_PROFILE_CLICKS returned 0
    or was not supported by the API.
    """
    google_native = monthly_totals.get("BUSINESS_PROFILE_CLICKS", 0)
    if google_native > 0:
        return google_native, True

    fallback = (
        monthly_totals.get("CALL_CLICKS",                 0) +
        monthly_totals.get("WEBSITE_CLICKS",              0) +
        monthly_totals.get("BUSINESS_DIRECTION_REQUESTS", 0) +
        monthly_totals.get("BUSINESS_CONVERSATIONS",      0) +
        monthly_totals.get("BUSINESS_BOOKINGS",           0)
    )
    return fallback, False


# ============================================================
# DB UPSERT — GMBPerformance
# ============================================================

def upsert_performance(
    db: Session,
    business_id: int,
    year: int,
    month: int,
    monthly_totals: dict[str, int],
    keywords: list[dict] = [],
    dry_run: bool = False,
):
    metric_date = datetime(year, month, 1)

    existing = db.query(GMBPerformance).filter(
        GMBPerformance.business_id == business_id,
        GMBPerformance.metric_date == metric_date
    ).first()

    calls = monthly_totals.get("CALL_CLICKS",                 0)
    clks  = monthly_totals.get("WEBSITE_CLICKS",              0)
    dirs  = monthly_totals.get("BUSINESS_DIRECTION_REQUESTS", 0)
    convs = monthly_totals.get("BUSINESS_CONVERSATIONS",      0)
    bkgs  = monthly_totals.get("BUSINESS_BOOKINGS",           0)

    gsm = monthly_totals.get("BUSINESS_IMPRESSIONS_MOBILE_SEARCH",  0)
    gsd = monthly_totals.get("BUSINESS_IMPRESSIONS_DESKTOP_SEARCH", 0)
    gmm = monthly_totals.get("BUSINESS_IMPRESSIONS_MOBILE_MAPS",    0)
    gmd = monthly_totals.get("BUSINESS_IMPRESSIONS_DESKTOP_MAPS",   0)

    total_interactions, used_google_native = _resolve_total_interactions(monthly_totals)
    sub_sum = calls + clks + dirs + convs + bkgs

    print(f"\n   [VERIFY] Writing to gmb_performance:")
    print(f"     calls={calls}  dirs={dirs}  clks={clks}  convs={convs}  bkgs={bkgs}")
    print(f"     sub_metrics_sum={sub_sum}")
    if used_google_native:
        diff = total_interactions - sub_sum
        print(f"     BUSINESS_PROFILE_CLICKS={total_interactions}  (Google native ✅, diff vs sum: {diff:+d})")
    else:
        print(f"     BUSINESS_PROFILE_CLICKS=0 or unsupported — using sub-metric sum={total_interactions} as fallback ⚠️")
    print(f"     profile_interactions_total={total_interactions}")
    print(f"     views_search={gsd + gsm}  views_maps={gmd + gmm}")

    if dry_run:
        action = "UPDATE" if existing else "INSERT"
        print(f"   [DRY-RUN] Would {action} GMBPerformance {year}-{month:02d}")
        return

    fields = {
        "business_id":                business_id,
        "metric_date":                metric_date,
        "views_search":               gsd + gsm,
        "views_maps":                 gmd + gmm,
        "views_search_mobile":        gsm,
        "views_search_desktop":       gsd,
        "views_maps_mobile":          gmm,
        "views_maps_desktop":         gmd,
        "actions_phone_calls":        calls,
        "actions_website_clicks":     clks,
        "actions_direction_requests": dirs,
        "actions_messages":           convs,
        "actions_bookings":           bkgs,
        "profile_interactions_total": total_interactions,
        "search_keywords_json":       json.dumps(keywords, ensure_ascii=False) if keywords else None,
        "data_source":                "google_api",
        "is_estimated":               False,
        "updated_at":                 datetime.now(),
    }

    today            = date.today()
    is_current_month = (year == today.year and month == today.month)

    if existing:
        for k, v in fields.items():
            _safe_set(existing, k, v)
        status = "PARTIAL (month in progress)" if is_current_month else "FINAL"
        print(f"   [UPDATE] GMBPerformance {year}-{month:02d} [{status}]")
    else:
        row = GMBPerformance()
        for k, v in fields.items():
            _safe_set(row, k, v)
        db.add(row)
        print(f"   [INSERT] GMBPerformance {year}-{month:02d}")


# ============================================================
# DB UPSERT — GMBInsight (daily rows)
# ============================================================

def upsert_daily_insights(
    db: Session,
    business_id: int,
    year: int,
    month: int,
    daily_by_metric: dict[str, dict[str, int]],
    dry_run: bool = False,
) -> tuple[int, int]:
    last_day = calendar.monthrange(year, month)[1]
    today    = date.today()
    cap_day  = min(last_day, today.day if (year == today.year and month == today.month) else last_day)

    inserted = 0
    updated  = 0

    for day in range(1, cap_day + 1):
        day_key  = f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"
        row_date = date(year, month, day)

        gsm   = daily_by_metric.get("BUSINESS_IMPRESSIONS_MOBILE_SEARCH",  {}).get(day_key, 0)
        gsd   = daily_by_metric.get("BUSINESS_IMPRESSIONS_DESKTOP_SEARCH", {}).get(day_key, 0)
        gmm   = daily_by_metric.get("BUSINESS_IMPRESSIONS_MOBILE_MAPS",    {}).get(day_key, 0)
        gmd   = daily_by_metric.get("BUSINESS_IMPRESSIONS_DESKTOP_MAPS",   {}).get(day_key, 0)
        calls = daily_by_metric.get("CALL_CLICKS",                         {}).get(day_key, 0)
        clks  = daily_by_metric.get("WEBSITE_CLICKS",                      {}).get(day_key, 0)
        dirs  = daily_by_metric.get("BUSINESS_DIRECTION_REQUESTS",         {}).get(day_key, 0)
        convs = daily_by_metric.get("BUSINESS_CONVERSATIONS",              {}).get(day_key, 0)
        bkgs  = daily_by_metric.get("BUSINESS_BOOKINGS",                   {}).get(day_key, 0)

        profile_views = gsm + gsd + gmm + gmd
        search_views  = gsm + gsd
        maps_views    = gmm + gmd

        bpc_daily = daily_by_metric.get("BUSINESS_PROFILE_CLICKS", {}).get(day_key, 0)
        profile_interactions = bpc_daily if bpc_daily > 0 else (calls + clks + dirs + convs + bkgs)

        all_fields = {
            "business_id":           business_id,
            "date":                  row_date,
            "profile_views":         profile_views,
            "search_views":          search_views,
            "maps_views":            maps_views,
            "google_search_mobile":  gsm,
            "google_search_desktop": gsd,
            "google_maps_mobile":    gmm,
            "google_maps_desktop":   gmd,
            "phone_calls":           calls,
            "website_clicks":        clks,
            "directions":            dirs,
            "conversations":         convs,
            "bookings":              bkgs,
            "profile_interactions":  profile_interactions,
            "updated_at":            datetime.now(),
        }

        if dry_run:
            updated += 1
            continue

        existing = db.query(GMBInsight).filter(
            GMBInsight.business_id == business_id,
            GMBInsight.date        == row_date
        ).first()

        if existing:
            for k, v in all_fields.items():
                _safe_set(existing, k, v)
            updated += 1
        else:
            row = GMBInsight()
            for k, v in all_fields.items():
                _safe_set(row, k, v)
            db.add(row)
            inserted += 1

    return inserted, updated


# ============================================================
# FALLBACK — Push from JSON monthly totals
# ============================================================

def upsert_insight_from_json(
    db: Session,
    business_id: int,
    data: dict,
    year: int,
    month: int,
    label: str,
    dry_run: bool = False,
):
    insight_date = date(year, month, 1)

    gsm   = data.get(f"BUSINESS_IMPRESSIONS_MOBILE_SEARCH_{label}",  0)
    gsd   = data.get(f"BUSINESS_IMPRESSIONS_DESKTOP_SEARCH_{label}", 0)
    gmm   = data.get(f"BUSINESS_IMPRESSIONS_MOBILE_MAPS_{label}",    0)
    gmd   = data.get(f"BUSINESS_IMPRESSIONS_DESKTOP_MAPS_{label}",   0)
    calls = data.get(f"CALL_CLICKS_{label}",                         0)
    clks  = data.get(f"WEBSITE_CLICKS_{label}",                      0)
    dirs  = data.get(f"BUSINESS_DIRECTION_REQUESTS_{label}",         0)
    convs = data.get(f"BUSINESS_CONVERSATIONS_{label}",              0)
    bkgs  = data.get(f"BUSINESS_BOOKINGS_{label}",                   0)
    bpc   = data.get(f"BUSINESS_PROFILE_CLICKS_{label}", 0)
    profile_interactions = bpc if bpc > 0 else (calls + clks + dirs + convs + bkgs)

    all_fields = {
        "business_id":           business_id,
        "date":                  insight_date,
        "profile_views":         gsm + gsd + gmm + gmd,
        "search_views":          gsm + gsd,
        "maps_views":            gmm + gmd,
        "google_search_mobile":  gsm,
        "google_search_desktop": gsd,
        "google_maps_mobile":    gmm,
        "google_maps_desktop":   gmd,
        "phone_calls":           calls,
        "website_clicks":        clks,
        "directions":            dirs,
        "conversations":         convs,
        "bookings":              bkgs,
        "profile_interactions":  profile_interactions,
        "updated_at":            datetime.now(),
    }

    if dry_run:
        print(f"   [DRY-RUN] Would upsert {label} insight (JSON fallback)")
        return

    existing = db.query(GMBInsight).filter(
        GMBInsight.business_id == business_id,
        GMBInsight.date        == insight_date
    ).first()

    if existing:
        for k, v in all_fields.items():
            _safe_set(existing, k, v)
        print(f"   [UPDATE] {label} insight (JSON fallback)")
    else:
        row = GMBInsight()
        for k, v in all_fields.items():
            _safe_set(row, k, v)
        db.add(row)
        print(f"   [INSERT] {label} insight (JSON fallback)")


def upsert_performance_from_json(
    db: Session,
    business_id: int,
    data: dict,
    year: int,
    month: int,
    label: str,
    dry_run: bool = False,
):
    metric_date = datetime(year, month, 1)

    existing = db.query(GMBPerformance).filter(
        GMBPerformance.business_id == business_id,
        GMBPerformance.metric_date == metric_date
    ).first()

    gsm   = data.get(f"BUSINESS_IMPRESSIONS_MOBILE_SEARCH_{label}",  0)
    gsd   = data.get(f"BUSINESS_IMPRESSIONS_DESKTOP_SEARCH_{label}", 0)
    gmm   = data.get(f"BUSINESS_IMPRESSIONS_MOBILE_MAPS_{label}",    0)
    gmd   = data.get(f"BUSINESS_IMPRESSIONS_DESKTOP_MAPS_{label}",   0)
    calls = data.get(f"CALL_CLICKS_{label}",                         0)
    clks  = data.get(f"WEBSITE_CLICKS_{label}",                      0)
    dirs  = data.get(f"BUSINESS_DIRECTION_REQUESTS_{label}",         0)
    convs = data.get(f"BUSINESS_CONVERSATIONS_{label}",              0)
    bkgs  = data.get(f"BUSINESS_BOOKINGS_{label}",                   0)
    bpc   = data.get(f"BUSINESS_PROFILE_CLICKS_{label}", 0)
    total = bpc if bpc > 0 else (calls + clks + dirs + convs + bkgs)

    fields = {
        "business_id":                business_id,
        "metric_date":                metric_date,
        "views_search":               gsd + gsm,
        "views_maps":                 gmd + gmm,
        "views_search_mobile":        gsm,
        "views_search_desktop":       gsd,
        "views_maps_mobile":          gmm,
        "views_maps_desktop":         gmd,
        "actions_phone_calls":        calls,
        "actions_website_clicks":     clks,
        "actions_direction_requests": dirs,
        "actions_messages":           convs,
        "actions_bookings":           bkgs,
        "profile_interactions_total": total,
        "data_source":                "api_json",
        "is_estimated":               False,
        "updated_at":                 datetime.now(),
    }

    if dry_run:
        action = "UPDATE" if existing else "INSERT"
        print(f"   [DRY-RUN] Would {action} {label} performance (JSON fallback)")
        return

    if existing:
        for k, v in fields.items():
            _safe_set(existing, k, v)
        print(f"   [UPDATE] {label} performance (JSON fallback, keywords preserved)")
    else:
        row = GMBPerformance()
        for k, v in fields.items():
            _safe_set(row, k, v)
        if hasattr(row, "search_keywords_json"):
            row.search_keywords_json = None
        db.add(row)
        print(f"   [INSERT] {label} performance (JSON fallback, no keywords)")


# ============================================================
# UTIL
# ============================================================

def _safe_set(obj, attr: str, value):
    if hasattr(obj, attr):
        setattr(obj, attr, value)


def _print_summary(
    success: int,
    failed: int,
    skipped: int,
    json_file,
    used_api: bool,
    target_id,
    months_list,
    dry_run: bool = False,
):
    print("\n" + "=" * 70)
    label = f"SYNC {'DRY-RUN' if dry_run else 'COMPLETE'}  [push_to_db v{SYNC_VERSION}]"
    print(label)
    print(f"   Success : {success} businesses")
    if failed:
        print(f"   Failed  : {failed} businesses")
    if skipped:
        print(f"   Skipped : {skipped} months (already in DB + outside revision window)")
    if dry_run:
        print(f"   Dry-run : NO data was written to the database")
    if json_file:
        print(f"   JSON    : {json_file}")
    mode = "Live Google API  —  DAILY rows + Keywords (UPSERT)" if used_api else "JSON fallback  —  MONTHLY rows (keywords preserved)"
    print(f"   Mode    : {mode}")
    print(f"   Months  : {[f'{y}-{m:02d}' for y, m, _ in months_list]}")
    if target_id:
        print(f"   Synced  : Business #{target_id} only")
    print("=" * 70 + "\n")


# ============================================================
# PARALLEL MONTH FETCH
# ============================================================

def _fetch_month_data(
    loc_name: str,
    year: int,
    month: int,
    label: str,
    headers: dict,
) -> tuple[int, int, str, dict, list]:
    """Worker for ThreadPoolExecutor — fetches one month's data from Google API."""
    print(f"\n   [{label} {year}] Starting parallel fetch...")
    daily_by_metric = fetch_daily_data_for_month(loc_name, year, month, headers)
    keywords        = fetch_search_keywords(loc_name, year, month, headers)
    return year, month, label, daily_by_metric, keywords


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="GMB -> DB Sync")
    parser.add_argument("--business-id",   type=int,   default=None)
    parser.add_argument("--months",        type=int,   default=DEFAULT_SYNC_MONTHS)
    parser.add_argument("--skip-existing", action="store_true", default=False)
    parser.add_argument("--force",         action="store_true", default=False)
    parser.add_argument("--start-date",    type=str,   default=None)
    parser.add_argument("--end-date",      type=str,   default=None)
    parser.add_argument("--dry-run",       action="store_true", default=False,
                        help="Preview what would be synced without writing to DB")
    parser.add_argument("--workers",       type=int,   default=1,
                        help="Parallel month fetch workers (default=1, max=4)")

    args          = parser.parse_args()
    target_id     = args.business_id
    skip_existing = args.skip_existing and not args.force
    dry_run       = args.dry_run
    workers       = min(max(args.workers, 1), 4)

    if args.start_date:
        end_date_str    = args.end_date or date.today().strftime("%Y-%m-%d")
        MONTHS          = get_months_from_range(args.start_date, end_date_str)
        date_range_mode = f"{args.start_date} -> {end_date_str}"
    else:
        sync_months     = min(max(args.months, 1), MAX_HISTORY_MONTHS)
        MONTHS          = get_months_list(sync_months)
        date_range_mode = f"last {len(MONTHS)} months"

    print("\n" + "=" * 70)
    print(f"GMB -> DATABASE SYNC  (push_to_db v{SYNC_VERSION})")
    print(f"   Date range    : {date_range_mode}")
    print(f"   Months        : {[f'{y}-{m:02d}' for y, m, _ in MONTHS]}")
    print(f"   Total months  : {len(MONTHS)}")
    print(f"   Revision days : Last {REVISION_DAYS} days always re-synced")
    print(f"   Skip existing : {'YES — missing months only (+ revision window)' if skip_existing else 'NO — full upsert'}")
    if args.force:
        print(f"   Force mode    : YES — re-syncing all months")
    if dry_run:
        print(f"   DRY-RUN       : YES — no data will be written")
    if workers > 1:
        print(f"   Workers       : {workers} parallel month fetches")
    if target_id:
        print(f"   Mode          : Single business — DB ID #{target_id}")
    else:
        print("   Mode          : All businesses")
    print("=" * 70 + "\n")

    creds   = load_credentials()
    headers = {"Authorization": f"Bearer {creds.token}"} if creds else None
    use_api = headers is not None

    if use_api:
        print("[INFO] Live GMB API available — fetching DAILY granularity + Keywords\n")
    else:
        print("[INFO] No token — using JSON monthly totals only\n")

    db      = SessionLocal()
    success = 0
    failed  = 0
    total_skipped_months = 0

    try:
        if use_api:
            print("Fetching locations from GMB API...")
            gmb_locations = fetch_gmb_locations(headers)

            if not gmb_locations:
                print("[WARN] No locations returned — falling back to JSON")
                use_api = False
            else:
                if target_id is not None:
                    db_lookup = SessionLocal()
                    try:
                        biz = db_lookup.query(Business).filter(Business.id == target_id).first()
                        if not biz:
                            print(f"[ERROR] Business #{target_id} not found in database")
                            sys.exit(1)
                        biz_name   = (biz.business_name or biz.name or "").strip()
                        biz_gplace = biz.google_place_id or ""

                        matched = [
                            loc for loc in gmb_locations
                            if loc.get("name", "") == biz_gplace
                            or loc.get("name", "").split("/")[-1] == biz_gplace
                        ]
                        if not matched:
                            matched = [
                                loc for loc in gmb_locations
                                if loc.get("title", "").strip().lower() == biz_name.lower()
                            ]
                        if not matched:
                            print(f"[ERROR] No GMB location found for: '{biz_name}'")
                            print("   Available locations:")
                            for loc in gmb_locations[:8]:
                                print(f"   - {loc.get('title', '?')}: {loc.get('name', '?')}")
                            sys.exit(1)

                        gmb_locations = matched
                        print(f"   Matched: {matched[0].get('title')}\n")
                    finally:
                        db_lookup.close()

                for loc in gmb_locations:
                    loc_name  = loc.get("name", "")
                    biz_title = loc.get("title", "Unknown")

                    print(f"\n{'-' * 60}")
                    print(f"  {biz_title}")
                    print(f"  Location: {loc_name}")

                    try:
                        business = get_or_create_business(db, biz_title, loc_name)
                        bid      = target_id if target_id is not None else business.id

                        # Separate months into skip vs fetch
                        months_to_fetch = []
                        for year, month, label in MONTHS:
                            if skip_existing and _month_already_synced(db, bid, year, month):
                                print(f"\n   [{label} {year}]  SKIP (already in DB + outside revision window)")
                                total_skipped_months += 1
                            else:
                                months_to_fetch.append((year, month, label))

                        if not months_to_fetch:
                            print(f"\n   All months already synced for {biz_title}")
                            success += 1
                            continue

                        # Fetch all months (parallel if workers > 1)
                        fetched_results = []
                        if workers > 1 and len(months_to_fetch) > 1:
                            print(f"\n   Fetching {len(months_to_fetch)} months with {workers} parallel workers...")
                            with ThreadPoolExecutor(max_workers=workers) as executor:
                                futures = {
                                    executor.submit(
                                        _fetch_month_data, loc_name, y, m, lbl, headers
                                    ): (y, m, lbl)
                                    for y, m, lbl in months_to_fetch
                                }
                                for future in as_completed(futures):
                                    try:
                                        fetched_results.append(future.result())
                                    except Exception as e:
                                        y, m, lbl = futures[future]
                                        print(f"   [ERROR] Fetch failed for {lbl} {y}: {e}")
                            # Sort by date to write in order
                            fetched_results.sort(key=lambda x: (x[0], x[1]))
                        else:
                            for year, month, label in months_to_fetch:
                                today            = date.today()
                                is_current_month = (year == today.year and month == today.month)
                                in_revision      = _is_revision_window(year, month)
                                suffix = " <-- current month (partial)" if is_current_month else (" <-- revision window" if in_revision else " <-- complete month")
                                print(f"\n   [{label} {year}]{suffix}")
                                print("   Fetching daily metrics + search keywords from Google API...")
                                daily_by_metric = fetch_daily_data_for_month(loc_name, year, month, headers)
                                keywords        = fetch_search_keywords(loc_name, year, month, headers)
                                fetched_results.append((year, month, label, daily_by_metric, keywords))

                        # Write all fetched months to DB
                        for year, month, label, daily_by_metric, keywords in fetched_results:
                            monthly_totals = {
                                metric: sum(daily_by_metric.get(metric, {}).values())
                                for metric in GMB_METRICS
                            }

                            total_views  = sum(monthly_totals.get(m, 0) for m in VIEW_METRICS)
                            sub_sum      = sum(monthly_totals.get(m, 0) for m in INTERACTION_METRICS)
                            bpc_total    = monthly_totals.get("BUSINESS_PROFILE_CLICKS", 0)

                            print(f"\n   Monthly totals [{label} {year}]:")
                            print(f"     Views            : {total_views}")
                            print(f"       Search Mobile  : {monthly_totals.get('BUSINESS_IMPRESSIONS_MOBILE_SEARCH', 0)}")
                            print(f"       Search Desktop : {monthly_totals.get('BUSINESS_IMPRESSIONS_DESKTOP_SEARCH', 0)}")
                            print(f"       Maps Mobile    : {monthly_totals.get('BUSINESS_IMPRESSIONS_MOBILE_MAPS', 0)}")
                            print(f"       Maps Desktop   : {monthly_totals.get('BUSINESS_IMPRESSIONS_DESKTOP_MAPS', 0)}")
                            print(f"     Calls            : {monthly_totals.get('CALL_CLICKS', 0)}")
                            print(f"     Website Clicks   : {monthly_totals.get('WEBSITE_CLICKS', 0)}")
                            print(f"     Directions       : {monthly_totals.get('BUSINESS_DIRECTION_REQUESTS', 0)}")
                            print(f"     Messages         : {monthly_totals.get('BUSINESS_CONVERSATIONS', 0)}")
                            print(f"     Bookings         : {monthly_totals.get('BUSINESS_BOOKINGS', 0)}")
                            print(f"     Sub-metrics sum  : {sub_sum}")
                            if bpc_total > 0:
                                diff = bpc_total - sub_sum
                                print(f"     BUSINESS_PROFILE_CLICKS: {bpc_total}  ← stored as total_interactions  (diff vs sum: {diff:+d})")
                            else:
                                print(f"     BUSINESS_PROFILE_CLICKS: 0 / not supported — using sub-metrics sum ({sub_sum}) as fallback")
                            if keywords:
                                top = keywords[0]
                                val = top["insightsValue"] if not top["isLessThan15"] else "< 15"
                                print(f"     Top keyword      : '{top['searchKeyword']}' ({val})")
                                print(f"     Keywords         : {len(keywords)} total")
                            else:
                                print(f"     Keywords         : 0 (none returned by Google API)")

                            upsert_performance(db, bid, year, month, monthly_totals, keywords, dry_run=dry_run)
                            inserted, updated = upsert_daily_insights(db, bid, year, month, daily_by_metric, dry_run=dry_run)
                            print(f"   GMBInsight : {inserted} inserted, {updated} updated (UPSERT)")
                            print(f"   Keywords   : {len(keywords)} saved to GMBPerformance")

                        if not dry_run:
                            db.commit()
                        success += 1
                        print(f"\n   [{'DRY-RUN' if dry_run else 'DONE'}] {biz_title} {'(no write)' if dry_run else 'committed to DB'}")

                    except Exception as e:
                        db.rollback()
                        print(f"   [ERROR] {biz_title}: {e}")
                        import traceback
                        traceback.print_exc()
                        failed += 1

                db.close()
                _print_summary(success, failed, total_skipped_months, None, True, target_id, MONTHS, dry_run)
                return

        # ── JSON fallback ────────────────────────────────────────────────────
        json_file = os.path.join(os.path.dirname(__file__), "gmb_performance_results.json")
        if not os.path.exists(json_file):
            print(f"[ERROR] JSON not found: {json_file}")
            sys.exit(1)

        with open(json_file, encoding="utf-8") as f:
            all_results = json.load(f)
        print(f"[INFO] Loaded {len(all_results)} businesses from JSON")

        if target_id is not None:
            db_lookup = SessionLocal()
            try:
                biz      = db_lookup.query(Business).filter(Business.id == target_id).first()
                if not biz:
                    print(f"[ERROR] Business #{target_id} not found in database")
                    sys.exit(1)
                biz_name = (biz.business_name or biz.name or "").strip()
                results  = [
                    r for r in all_results
                    if r.get("business", "").strip().lower() == biz_name.lower()
                ]
                if not results:
                    print(f"[ERROR] No JSON entry for: '{biz_name}'")
                    sys.exit(1)
                print(f"   Matched JSON: {biz_name}\n")
            finally:
                db_lookup.close()
        else:
            results = all_results
            print(f"   Syncing all {len(results)} businesses from JSON\n")

        for data in results:
            bname = data.get("business", "Unknown")
            lid   = data.get("location", "")
            print(f"\n{'-' * 60}")
            print(f"  {bname}")
            try:
                business = get_or_create_business(db, bname, lid)
                bid      = target_id if target_id is not None else business.id
                for year, month, label in MONTHS:
                    if skip_existing and _month_already_synced(db, bid, year, month):
                        print(f"\n   [{label} {year}]  SKIP (already in DB + outside revision window)")
                        total_skipped_months += 1
                        continue
                    print(f"\n   [{label} {year}]")
                    upsert_performance_from_json(db, bid, data, year, month, label, dry_run=dry_run)
                    upsert_insight_from_json(db, bid, data, year, month, label, dry_run=dry_run)
                if not dry_run:
                    db.commit()
                success += 1
                print(f"\n   [{'DRY-RUN' if dry_run else 'DONE'}] {bname} {'(no write)' if dry_run else 'committed to DB'}")
            except Exception as e:
                db.rollback()
                print(f"   [ERROR] {bname}: {e}")
                import traceback
                traceback.print_exc()
                failed += 1

        _print_summary(success, failed, total_skipped_months, json_file, False, target_id, MONTHS, dry_run)

    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()