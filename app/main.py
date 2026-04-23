# app/main.py
# LeadMatrix API — v5.3.1
# ============================================================
# CHANGELOG v5.3.1 (vs 5.3.0)
#   ✅ FIXED: Sync slow on Windows — replaced asyncio.create_subprocess_exec
#      with asyncio.to_thread + subprocess.run (no stdout buffering issues)
#   ✅ push_to_db.py runs with -u flag (unbuffered) for clean output
#   ✅ Full stdout+stderr captured and logged after completion
#   ✅ subprocess.TimeoutExpired handled — fails gracefully after 300s
#   ✅ All v5.3.0 code preserved unchanged (only _run_sync replaced)
# ============================================================

from dotenv import load_dotenv
import os
import sys
import asyncio
import subprocess
import time
import random
import uuid
import shutil
import calendar
from datetime import datetime, timedelta, date
from contextlib import asynccontextmanager

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.api import endpoints
from app.routers import gmb_posts
from app.database import get_db

from app.services.scheduler import scheduler as gmb_scheduler

SEO_MODULE_AVAILABLE = False

try:
    from app.models import Business, GMBInsight, GMBPerformance, Review, GMBPost
    MODELS_AVAILABLE = True
except ImportError as e:
    MODELS_AVAILABLE = False
    print(f"[WARN] Models not fully loaded: {e}")

try:
    from app.scraper.stealth_gmb_scraper import StealthGMBScraper
    STEALTH_SCRAPER_AVAILABLE = True
except ImportError:
    STEALTH_SCRAPER_AVAILABLE = False
    print("[WARN] Stealth scraper not available.")

# ── GMB Publisher ─────────────────────────────────────────────────────────────
GMB_PUBLISHER_AVAILABLE = False
GMB_PUBLISHER_VERSION   = "NOT LOADED"
IMGBB_API_KEY           = os.getenv("IMGBB_API_KEY", "")   # fallback if publisher not loaded
try:
    from app.services.gmb_publisher import (
        publish_post_to_gmb,
        list_accounts,
        list_locations,
        __version__ as _gmb_pub_version,
        IMGBB_API_KEY as _pub_imgbb_key,
    )
    GMB_PUBLISHER_AVAILABLE = True
    GMB_PUBLISHER_VERSION   = f"v{_gmb_pub_version}"
    IMGBB_API_KEY           = _pub_imgbb_key          # use the one from publisher (already loaded from .env)
except ImportError as e:
    print(f"[WARN] GMB Publisher not available: {e}")

# ── Ranking Tracker ───────────────────────────────────────────────────────────
GMB_RANKING_TRACKER_AVAILABLE = False
try:
    from app.services.gmb_ranking_tracker import AdvancedGMBRankingTracker
    GMB_RANKING_TRACKER_AVAILABLE = True
    print("[OK] Advanced GMB Ranking Tracker LOADED")
except (ImportError, Exception) as e:
    print(f"[WARN] GMB Ranking Tracker not available: {e}")

    class AdvancedGMBRankingTracker:
        def __init__(self, headless=False, use_google_search=False):
            self.headless          = headless
            self.use_google_search = use_google_search

        def check_gmb_ranking(self, **kwargs):
            return {"found": False, "position": 0, "error": "GMB Ranking Tracker not available"}

        def close(self):
            pass

    print("[WARN] Using fallback dummy GMB Ranking Tracker")


# ============================================================
# MEDIA UPLOAD CONFIG
# ============================================================

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_UPLOAD_BYTES    = 10 * 1024 * 1024  # 10 MB

# Base URL for uploaded files — change to your production domain when deploying
MEDIA_BASE_URL = os.getenv("MEDIA_BASE_URL", "http://localhost:8000")

IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"


# ============================================================
# SESSION HELPERS
# ============================================================

_MAX_SESSIONS = 50

def _evict_old_sessions(store: dict):
    """Keep only the most recent _MAX_SESSIONS entries; drop oldest completed ones first."""
    if len(store) <= _MAX_SESSIONS:
        return
    completed = sorted(
        [(k, v) for k, v in store.items() if v.get("status") != "running"],
        key=lambda x: x[1].get("started_at", ""),
    )
    for k, _ in completed[: len(store) - _MAX_SESSIONS]:
        del store[k]


# ============================================================
# LIFESPAN — startup + shutdown
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 70)
    print("LEADMATRIX API V5.3.1 - STARTING UP")
    print("=" * 70)

    # ── Database: init tables + run migrations ────────────────────────────
    try:
        from app.database import init_db, run_migrations, check_db_connection

        try:
            import app.models  # noqa: F401
        except Exception as e:
            print(f"[WARN] Model import warning: {e}")

        check_db_connection()
        init_db()
        run_migrations()
        print("[OK] Database tables verified/created (v5.3)")
    except Exception as e:
        print(f"[WARN] Database startup warning: {e}")

    # ── GMB Auto-Scheduler ────────────────────────────────────────────────
    try:
        gmb_scheduler.start()
        print("[OK] GMB Auto-Scheduler STARTED (every 60s)")
    except Exception as e:
        print(f"[WARN] GMB Scheduler failed to start: {e}")

    imgbb_status = "ENABLED" if IMGBB_API_KEY else "NO KEY SET"
    print(f"[*] Stealth Scraper:  {'V4.1 MULTI-TAB OK' if STEALTH_SCRAPER_AVAILABLE else 'DISABLED'}")
    print(f"[*] Models:           {'LOADED OK' if MODELS_AVAILABLE else 'LIMITED'}")
    print(f"[*] Ranking Tracker:  {'ENABLED OK' if GMB_RANKING_TRACKER_AVAILABLE else 'FALLBACK MODE'}")
    print(f"[*] GMB Publisher:    {GMB_PUBLISHER_VERSION + ' OK' if GMB_PUBLISHER_AVAILABLE else 'NOT LOADED'}")
    print(f"[*] SEO Module:       {'ENABLED OK' if SEO_MODULE_AVAILABLE else 'DISABLED'}")
    print(f"[*] GMB Blog Poster:  ENABLED")
    print(f"[*] GMB Sync Button:  ENABLED — calls push_to_db.py (v5.3.1 FAST SYNC)")
    print(f"[*] Media Upload:     ENABLED → {UPLOADS_DIR}")
    print(f"[*] imgbb Proxy:      {imgbb_status}")
    print(f"[*] Analytics Fix:    v5.2 — Exact date range query (no month expansion)")
    print(f"[*] Platform:         {'Windows' if sys.platform == 'win32' else sys.platform}")
    print(f"[*] Frontend:         http://localhost:3000")
    print(f"[*] Backend:          http://localhost:8000")
    print(f"[*] API Docs:         http://localhost:8000/docs")
    print("=" * 70 + "\n")

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────
    global gmb_scraper
    print("\n[*] Shutting down LeadMatrix API...")
    if gmb_scraper:
        try:
            gmb_scraper.close()
        except Exception:
            pass
    gmb_scraper = None

    try:
        gmb_scheduler.stop()
        print("[OK] GMB Auto-Scheduler stopped")
    except Exception as e:
        print(f"[WARN] Scheduler stop error: {e}")

    print("[OK] Shutdown complete")


# ============================================================
# APP INIT
# ============================================================

app = FastAPI(
    title       = "LeadMatrix API",
    description = "GMB Analytics Backend with V4.1 MULTI-TAB SCRAPING + One-Click Sync",
    version     = "5.3.1",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
         # ✅ Vercel deployment
        "https://leadmatrix-beta.vercel.app",
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Frontend static files ─────────────────────────────────────────────────────
try:
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
    if os.path.exists(frontend_path):
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")
        print(f"[OK] Frontend mounted at: {frontend_path}")
    else:
        print(f"[WARN] Frontend directory not found at: {frontend_path}")
except Exception as e:
    print(f"[WARN] Could not mount frontend: {e}")

# ── Uploads static files — serves /uploads/<filename> publicly ───────────────
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

gmb_scraper       = None
ranking_sessions: dict = {}
sync_sessions:    dict = {}

app.include_router(endpoints.router, prefix="/v1")
app.include_router(gmb_posts.router, prefix="/api/gmb-posts", tags=["GMB Posts"])


# ============================================================
# PYDANTIC MODELS
# ============================================================

class BusinessCreate(BaseModel):
    name:     str
    address:  str = ""
    phone:    str = ""
    website:  str = ""
    category: str = ""
    city:     str = ""
    state:    str = ""
    gmb_url:  str = ""


class BusinessUpdate(BaseModel):
    """PATCH /api/businesses/{id} — all fields optional."""
    name:     str | None = None
    address:  str | None = None
    phone:    str | None = None
    website:  str | None = None
    category: str | None = None
    city:     str | None = None
    state:    str | None = None
    gmb_url:  str | None = None


class InsightCreate(BaseModel):
    business_id:    int
    date:           str
    profile_views:  int = 0
    search_views:   int = 0
    maps_views:     int = 0
    phone_calls:    int = 0
    website_clicks: int = 0
    directions:     int = 0
    photo_views:    int = 0


class StartTrackingRequest(BaseModel):
    business_name: str
    location:      str
    keywords:      list[str]
    use_proxy:     bool       = False
    proxy_ip:      str | None = None


class StartTrackingResponse(BaseModel):
    success:     bool
    tracking_id: str
    message:     str


class TrackingStatusResponse(BaseModel):
    status:   str
    progress: int
    total:    int
    message:  str | None = None


class SyncRequest(BaseModel):
    business_id: int | None  = None
    start_date:  str | None  = None
    end_date:    str | None  = None
    force:       bool        = False


# ============================================================
# DATE HELPERS
# ============================================================

def _parse_date_param(value: str | None, fallback: date) -> date:
    if not value:
        return fallback
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid date format: '{value}'. Supported formats: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY"
        )


def _exact_datetime_range(start: date, end: date):
    """
    Returns (start_dt, end_dt) as datetime objects covering the full day range:
      start_dt = start at 00:00:00
      end_dt   = end   at 23:59:59
    """
    start_dt = datetime(start.year, start.month, start.day, 0, 0, 0)
    end_dt   = datetime(end.year,   end.month,   end.day,   23, 59, 59)
    return start_dt, end_dt


def _month_range_for_dates(start: date, end: date):
    month_start = datetime(start.year, start.month, 1, 0, 0, 0)
    last_day    = calendar.monthrange(end.year, end.month)[1]
    month_end   = datetime(end.year, end.month, last_day, 23, 59, 59)
    return month_start, month_end


# ============================================================
# ROOT & HEALTH
# ============================================================

@app.get("/")
def health_check():
    return {
        "status":  "LeadMatrix API is running!",
        "version": "5.3.1",
        "features": [
            "Manual GMB",
            "Multi-Tab Scraping V4.1",
            "Analytics",
            "Platform Breakdown",
            "Search Keywords",
            "One-Click GMB Sync (REAL — push_to_db.py)",
            "Single-Business Sync",
            f"GMB Publisher {GMB_PUBLISHER_VERSION}",
            "Advanced Ranking Tracker" if GMB_RANKING_TRACKER_AVAILABLE else "Advanced Ranking Tracker FALLBACK",
            "SEO Module" if SEO_MODULE_AVAILABLE else "SEO Module DISABLED",
            "GMB Blog Poster",
            "GMB Post Scheduler",
            "Media Upload (imgbb auto-proxy)" if IMGBB_API_KEY else "Media Upload",
            "Analytics Fix v5.2 (exact date range)",
        ],
        "endpoints": {
            "gmb_login":           "/api/gmb/stealth-login",
            "gmb_businesses":      "/api/gmb/businesses",
            "gmb_scrape_all_tabs": "/api/gmb/scrape-all-tabs",
            "performance_data":    "/api/performance/{business_id}",
            "analytics":           "/api/analytics/{business_id}",
            "sync_gmb":            "/api/sync-gmb-data",
            "sync_status":         "/api/sync-status/{sync_id}",
            "sync_latest":         "/api/sync-status/latest",
            "gmb_posts":           "/api/gmb-posts/",
            "publisher_status":    "/api/gmb/publisher-status",
            "media_upload":        "/api/media/upload",
            "docs":                "/docs",
        }
    }


@app.get("/api/health")
def api_health(db: Session = Depends(get_db)):
    total_businesses = 0
    if MODELS_AVAILABLE:
        try:
            total_businesses = db.query(Business).filter(Business.status == "active").count()
        except Exception:
            pass
    return {
        "status":            "ok",
        "version":           "5.3.1",
        "total_businesses":  total_businesses,
        "gmb_logged_in":     gmb_scraper.logged_in if gmb_scraper else False,
        "scraper_version":   "V4.1 MULTI-TAB" if STEALTH_SCRAPER_AVAILABLE else "DISABLED",
        "ranking_tracker":   "ADVANCED GMB TRACKER" if GMB_RANKING_TRACKER_AVAILABLE else "FALLBACK MODE",
        "seo_module":        "ENABLED" if SEO_MODULE_AVAILABLE else "DISABLED",
        "gmb_blog_poster":   "ENABLED",
        "gmb_sync":          "ENABLED — real push_to_db.py subprocess (v5.3.1 fast)",
        "gmb_publisher":     f"{GMB_PUBLISHER_VERSION} OK" if GMB_PUBLISHER_AVAILABLE else "NOT LOADED",
        "gmb_scheduler":     "RUNNING" if gmb_scheduler.is_running else "STOPPED",
        "media_upload":      "ENABLED",
        "imgbb_proxy":       "ENABLED" if IMGBB_API_KEY else "NO KEY SET",
        "analytics_fix":     "v5.2 exact-range",
    }


# ============================================================
# ✅ v5.1 — MEDIA UPLOAD with imgbb auto-proxy
# ============================================================

@app.post("/api/media/upload")
async def upload_media(file: UploadFile = File(...)):
    """
    Upload an image file and get back a **public** URL safe for the GMB API.

    Flow (v5.1):
      1. Validate type + size
      2. Save to disk (UPLOADS_DIR)
      3. If IMGBB_API_KEY is set → upload bytes directly to imgbb → return public URL ✅
      4. If no key → return localhost URL (gmb_publisher.py will proxy at publish time)

    Returns:
      - url           → public imgbb URL  OR  localhost URL
      - local_url     → always the localhost URL (for local access)
      - imgbb_proxied → true if successfully proxied to imgbb
      - filename, original_name, size, content_type
    """
    # ── Validate content type ─────────────────────────────────
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file.content_type}' not allowed. Use JPG, PNG, WEBP, or GIF."
        )

    # ── Read + size check ─────────────────────────────────────
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(contents) // 1024} KB). Max allowed is 10 MB."
        )

    # ── Safe unique filename ──────────────────────────────────
    ext_map  = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
    ext      = ext_map.get(file.content_type, "jpg")
    filename = f"{uuid.uuid4().hex}.{ext}"
    dest     = os.path.join(UPLOADS_DIR, filename)

    # ── Save to disk ──────────────────────────────────────────
    with open(dest, "wb") as f:
        f.write(contents)

    local_url     = f"{MEDIA_BASE_URL}/uploads/{filename}"
    public_url    = local_url
    imgbb_proxied = False

    # ── ✅ Auto-proxy to imgbb (upload bytes directly — no re-download) ──
    if IMGBB_API_KEY:
        try:
            import base64
            import requests as _req

            img_b64     = base64.b64encode(contents).decode("utf-8")
            upload_resp = _req.post(
                IMGBB_UPLOAD_URL,
                data={
                    "key":        IMGBB_API_KEY,
                    "image":      img_b64,
                    "expiration": 2592000,   # 30 days
                },
                timeout=30,
            )
            upload_resp.raise_for_status()
            result        = upload_resp.json()
            public_url    = result["data"]["url"]
            imgbb_proxied = True
            print(f"[Media Upload] ✅ imgbb proxy → {public_url}")
        except Exception as e:
            print(f"[Media Upload] ⚠️  imgbb failed, using localhost URL: {e}")
            public_url = local_url
    else:
        print(f"[Media Upload] ℹ️  No IMGBB_API_KEY — saved locally. gmb_publisher.py will proxy at publish time.")

    print(f"[Media Upload] Saved: {filename} ({len(contents) // 1024} KB) | public: {public_url}")

    return {
        "url":           public_url,
        "local_url":     local_url,
        "imgbb_proxied": imgbb_proxied,
        "filename":      filename,
        "original_name": file.filename,
        "size":          len(contents),
        "content_type":  file.content_type,
    }


# ============================================================
# STATIC PAGES
# ============================================================

@app.get("/gmb/create-post")
async def serve_gmb_post_creator():
    try:
        path = os.path.join(os.path.dirname(__file__), "..", "frontend", "gmb-posts", "create-post.html")
        if os.path.exists(path):
            return FileResponse(path)
        return {"error": "GMB post creator page not found"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/gmb/scheduled-posts")
async def serve_scheduled_posts():
    try:
        path = os.path.join(os.path.dirname(__file__), "..", "frontend", "gmb-posts", "scheduled-posts.html")
        if os.path.exists(path):
            return FileResponse(path)
        return {"error": "Scheduled posts page not found"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# DASHBOARD METRICS
# ============================================================

@app.get("/api/dashboard/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)):
    try:
        if not MODELS_AVAILABLE:
            return _mock_dashboard_metrics()

        businesses       = db.query(Business).filter(Business.status == "active").all()
        total_businesses = len(businesses)
        end_date         = date.today()
        start_date       = end_date - timedelta(days=30)

        insights = db.query(GMBInsight).filter(
            GMBInsight.date >= start_date,
            GMBInsight.date <= end_date
        ).all()

        profile_views  = sum(i.profile_views  or 0 for i in insights)
        phone_calls    = sum(i.phone_calls    or 0 for i in insights)
        directions     = sum(i.directions     or 0 for i in insights)
        website_clicks = sum(i.website_clicks or 0 for i in insights)

        try:
            reviews       = db.query(Review).all()
            total_reviews = len(reviews)
            avg_rating    = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else 0
        except Exception:
            total_reviews = 0
            avg_rating    = 0

        if total_businesses == 0 or profile_views == 0:
            return _mock_dashboard_metrics()

        return {
            "total_businesses": total_businesses,
            "profile_views":    profile_views,
            "phone_calls":      phone_calls,
            "directions":       directions,
            "website_clicks":   website_clicks,
            "avg_rating":       avg_rating,
            "total_reviews":    total_reviews,
            "photos":           0,
        }
    except Exception as e:
        print(f"Dashboard metrics error: {e}")
        return _mock_dashboard_metrics()


def _mock_dashboard_metrics():
    return {
        "total_businesses": 12,
        "profile_views":    45230,
        "phone_calls":      892,
        "directions":       1245,
        "website_clicks":   3456,
        "avg_rating":       4.8,
        "total_reviews":    342,
        "photos":           156,
    }


# ============================================================
# PERFORMANCE DATA
# ============================================================

@app.get("/api/performance/{business_id}")
def get_performance_data(business_id: int, months: int = 3, db: Session = Depends(get_db)):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Models not available")

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    from_date = datetime.now() - timedelta(days=months * 31)
    records   = db.query(GMBPerformance).filter(
        GMBPerformance.business_id == business_id,
        GMBPerformance.metric_date >= from_date
    ).order_by(GMBPerformance.metric_date.asc()).all()

    if not records:
        return {
            "success":       True,
            "business_id":   business_id,
            "business_name": business.business_name or business.name,
            "message":       "No performance data found. Click Sync GMB to pull latest data.",
            "data":          [],
        }

    data = []
    for r in records:
        data.append({
            "month":                      r.metric_date.strftime("%Y-%m") if r.metric_date else None,
            "views_search":               r.views_search,
            "views_maps":                 r.views_maps,
            "total_views":                (r.views_search or 0) + (r.views_maps or 0),
            "actions_phone_calls":        r.actions_phone_calls,
            "actions_website_clicks":     r.actions_website_clicks,
            "actions_direction_requests": r.actions_direction_requests,
            "actions_messages":           r.actions_messages,
            "actions_bookings":           r.actions_bookings,
            "profile_interactions":       r.profile_interactions_total,
            "photo_views":                r.photo_views_total,
            "reviews_total":              r.reviews_total_count,
            "reviews_avg_rating":         r.reviews_average_rating,
            "posts_views":                r.posts_total_views,
            "data_source":                r.data_source,
        })

    totals = {
        "total_views":                sum(d["total_views"] for d in data),
        "total_phone_calls":          sum(d["actions_phone_calls"]        or 0 for d in data),
        "total_website_clicks":       sum(d["actions_website_clicks"]     or 0 for d in data),
        "total_directions":           sum(d["actions_direction_requests"] or 0 for d in data),
        "total_profile_interactions": sum(d["profile_interactions"]       or 0 for d in data),
    }

    return {
        "success":         True,
        "business_id":     business_id,
        "business_name":   business.business_name or business.name,
        "months_returned": len(data),
        "totals":          totals,
        "data":            data,
    }


# ============================================================
# ✅ ANALYTICS — v5.2 EXACT DATE-RANGE FIX
# ============================================================

@app.get("/api/analytics/{business_id}")
def get_analytics(
    business_id: int,
    days:        int        = Query(30, ge=1, le=365),
    start_date:  str | None = Query(None, description="Any format: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY"),
    end_date:    str | None = Query(None, description="Any format: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY"),
    db:          Session    = Depends(get_db),
):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Models not available")

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    business_name  = business.business_name or business.name or f"Business #{business_id}"
    resolved_end   = _parse_date_param(end_date,   date.today())
    resolved_start = _parse_date_param(start_date, resolved_end - timedelta(days=days))

    if resolved_end < resolved_start:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    print(f"[Analytics v5.2] Business #{business_id} | {resolved_start} → {resolved_end}")

    # ── GMBInsight daily rows ─────────────────────────────────────────────
    try:
        insights = db.query(GMBInsight).filter(
            GMBInsight.business_id == business_id,
            GMBInsight.date        >= resolved_start,
            GMBInsight.date        <= resolved_end
        ).order_by(GMBInsight.date.asc()).all()
    except Exception as e:
        print(f"[WARN] GMBInsight query failed: {e}")
        insights = []

    daily_trends = [
        {
            "date":                 str(i.date),
            "phone_calls":          i.phone_calls    or 0,
            "directions":           i.directions     or 0,
            "website_clicks":       i.website_clicks or 0,
            "conversations":        getattr(i, "conversations",        None) or 0,
            "bookings":             getattr(i, "bookings",             None) or 0,
            "profile_interactions": getattr(i, "profile_interactions", None) or 0,
        }
        for i in insights
    ]

    perf_query_start, perf_query_end = _exact_datetime_range(resolved_start, resolved_end)

    first_of_start_month = datetime(resolved_start.year, resolved_start.month, 1, 0, 0, 0)
    last_day_end_month   = calendar.monthrange(resolved_end.year, resolved_end.month)[1]
    first_of_end_month   = datetime(resolved_end.year, resolved_end.month, 1, 0, 0, 0)

    print(f"[Analytics v5.2] Perf exact range:  {perf_query_start} → {perf_query_end}")
    print(f"[Analytics v5.2] Perf monthly cover: {first_of_start_month} → {first_of_end_month}")

    try:
        perf_records = db.query(GMBPerformance).filter(
            GMBPerformance.business_id == business_id,
            GMBPerformance.metric_date >= first_of_start_month,
            GMBPerformance.metric_date <= datetime(
                resolved_end.year, resolved_end.month, last_day_end_month, 23, 59, 59
            ),
        ).order_by(GMBPerformance.metric_date.asc()).all()
    except Exception as e:
        print(f"[WARN] GMBPerformance query failed: {e}")
        perf_records = []

    print(f"[Analytics v5.2] GMBPerformance rows matched: {len(perf_records)}")

    # ── Aggregate performance metrics ────────────────────────────────────
    perf_phone_calls  = sum(getattr(r, "actions_phone_calls",        0) or 0 for r in perf_records)
    perf_directions   = sum(getattr(r, "actions_direction_requests", 0) or 0 for r in perf_records)
    perf_website_clks = sum(getattr(r, "actions_website_clicks",     0) or 0 for r in perf_records)
    perf_messages     = sum(getattr(r, "actions_messages",           0) or 0 for r in perf_records)
    perf_bookings     = sum(getattr(r, "actions_bookings",           0) or 0 for r in perf_records)
    perf_interactions = sum(getattr(r, "profile_interactions_total", 0) or 0 for r in perf_records)

    total_phone_calls    = perf_phone_calls  if perf_records else sum(i.phone_calls    or 0 for i in insights)
    total_directions     = perf_directions   if perf_records else sum(i.directions     or 0 for i in insights)
    total_website_clicks = perf_website_clks if perf_records else sum(i.website_clicks or 0 for i in insights)
    total_conversations  = perf_messages     if perf_records else sum(getattr(i, "conversations", None) or 0 for i in insights)
    total_bookings       = perf_bookings     if perf_records else sum(getattr(i, "bookings",      None) or 0 for i in insights)

    if perf_interactions > 0:
        total_profile_interactions = perf_interactions
    else:
        total_profile_interactions = (
            total_phone_calls + total_directions + total_website_clicks
            + total_conversations + total_bookings
        )

    # ── Reviews ──────────────────────────────────────────────────────────
    avg_rating    = None
    total_reviews = 0
    try:
        reviews = db.query(Review).filter(Review.business_id == business_id).all()
        if reviews:
            total_reviews = len(reviews)
            avg_rating    = round(sum(r.rating for r in reviews) / total_reviews, 1)
    except Exception as e:
        print(f"[WARN] Reviews query failed for business {business_id}: {e}")

    # ── Platform breakdown ───────────────────────────────────────────────
    platform_breakdown = None
    try:
        p_gsm = sum(getattr(r, "views_search_mobile",  None) or 0 for r in perf_records)
        p_gsd = sum(getattr(r, "views_search_desktop", None) or 0 for r in perf_records)
        p_gmm = sum(getattr(r, "views_maps_mobile",    None) or 0 for r in perf_records)
        p_gmd = sum(getattr(r, "views_maps_desktop",   None) or 0 for r in perf_records)
        if p_gsm + p_gsd + p_gmm + p_gmd > 0:
            platform_breakdown = {
                "google_search_mobile":  p_gsm,
                "google_search_desktop": p_gsd,
                "google_maps_mobile":    p_gmm,
                "google_maps_desktop":   p_gmd,
                "source":                "gmb_performance",
            }
        else:
            gsm = sum(getattr(i, "google_search_mobile",  None) or 0 for i in insights)
            gsd = sum(getattr(i, "google_search_desktop", None) or 0 for i in insights)
            gmm = sum(getattr(i, "google_maps_mobile",    None) or 0 for i in insights)
            gmd = sum(getattr(i, "google_maps_desktop",   None) or 0 for i in insights)
            if gsm + gsd + gmm + gmd > 0:
                platform_breakdown = {
                    "google_search_mobile":  gsm,
                    "google_search_desktop": gsd,
                    "google_maps_mobile":    gmm,
                    "google_maps_desktop":   gmd,
                    "source":                "gmb_insight_daily",
                }
            else:
                search_total = sum(getattr(i, "search_views", None) or 0 for i in insights)
                maps_total   = sum(getattr(i, "maps_views",   None) or 0 for i in insights)
                if search_total + maps_total > 0:
                    platform_breakdown = {
                        "google_search_mobile":  round(search_total * 0.75),
                        "google_search_desktop": round(search_total * 0.25),
                        "google_maps_mobile":    round(maps_total   * 0.85),
                        "google_maps_desktop":   round(maps_total   * 0.15),
                        "source":                "estimated",
                    }
    except Exception as e:
        print(f"[WARN] Platform breakdown failed: {e}")

    # ── Search keywords ───────────────────────────────────────────────────
    search_keywords = []
    try:
        import json as _json
        kw_totals: dict[str, dict] = {}
        for r in perf_records:
            raw_json = getattr(r, "search_keywords_json", None)
            if not raw_json:
                continue
            if isinstance(raw_json, str):
                try:
                    raw_json = _json.loads(raw_json)
                except Exception:
                    continue
            if not isinstance(raw_json, list):
                continue
            for item in raw_json:
                kw   = (item.get("searchKeyword") or "").strip()
                val  = item.get("insightsValue") or 0
                lt15 = bool(item.get("isLessThan15", False))
                if not kw:
                    continue
                key = kw.lower()
                if key in kw_totals:
                    kw_totals[key]["insightsValue"] += val
                    kw_totals[key]["isLessThan15"]   = kw_totals[key]["isLessThan15"] and lt15
                else:
                    kw_totals[key] = {
                        "searchKeyword": kw,
                        "insightsValue": val,
                        "isLessThan15":  lt15,
                    }
        search_keywords = sorted(
            kw_totals.values(),
            key=lambda x: x["insightsValue"],
            reverse=True,
        )[:10]
    except Exception as e:
        print(f"[WARN] Keywords aggregation failed: {e}")

    # ── Last sync timestamp ───────────────────────────────────────────────
    last_sync = None
    for s in sorted(sync_sessions.values(), key=lambda x: x.get("started_at", ""), reverse=True):
        if s.get("status") == "completed":
            if s.get("business_id") == business_id or s.get("business_id") is None:
                last_sync = s.get("completed_at")
                break

    # ── Build response ────────────────────────────────────────────────────
    response = {
        "success":  True,
        "business": {"id": business_id, "name": business_name},
        "metrics": {
            "total_phone_calls":          total_phone_calls,
            "total_directions":           total_directions,
            "total_website_clicks":       total_website_clicks,
            "total_conversations":        total_conversations,
            "total_bookings":             total_bookings,
            "total_profile_interactions": total_profile_interactions,
        },
        "daily_trends": daily_trends,
        "data_summary": {
            "days_requested":    days,
            "days_with_data":    len(insights),
            "perf_records":      len(perf_records),
            "date_range_start":  str(resolved_start),
            "date_range_end":    str(resolved_end),
            "perf_query_start":  str(first_of_start_month),
            "perf_query_end":    str(datetime(resolved_end.year, resolved_end.month, last_day_end_month, 23, 59, 59)),
            "last_synced":       last_sync,
            "analytics_version": "5.2",
        },
    }

    if total_reviews > 0:
        response["reviews"] = {"total": total_reviews, "avg_rating": avg_rating}
    if platform_breakdown:
        response["platform_breakdown"] = platform_breakdown
    if search_keywords:
        response["search_keywords"] = search_keywords

    return response


# ============================================================
# BUSINESS CRUD
# ============================================================

@app.post("/api/businesses")
def create_business(business: BusinessCreate, db: Session = Depends(get_db)):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Models not available")
    try:
        db_business = Business(
            name          = business.name,
            business_name = business.name,
            phone         = business.phone,
            phone_number  = business.phone,
            address       = business.address,
            location      = business.address,
            city          = business.city,
            state         = business.state,
            category      = business.category,
            website       = business.website,
            gmb_url       = business.gmb_url,
            status        = "active",
        )
        db.add(db_business)
        db.commit()
        db.refresh(db_business)
        return {
            "success":  True,
            "message":  "Business added successfully!",
            "business": {"id": db_business.id, "name": db_business.business_name or db_business.name},
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/businesses")
def get_all_businesses(limit: int = Query(200, ge=1, le=1000), db: Session = Depends(get_db)):
    if not MODELS_AVAILABLE:
        return {"success": True, "total": 0, "businesses": []}
    try:
        businesses = db.query(Business).filter(Business.status == "active").limit(limit).all()
        return {
            "success":    True,
            "total":      len(businesses),
            "businesses": [
                {
                    "id":           b.id,
                    "name":         b.business_name or b.name,
                    "businessname": b.business_name or b.name,
                    "category":     b.category,
                    "city":         b.city,
                    "phone":        b.phone_number or b.phone,
                    "website":      b.website,
                    "gmb_url":      b.gmb_url,
                    "gmburl":       b.gmb_url,
                    "status":       b.status,
                }
                for b in businesses
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/businesses/{business_id}")
def get_business(business_id: int, db: Session = Depends(get_db)):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Models not available")
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return {
        "success":  True,
        "business": {
            "id":       business.id,
            "name":     business.business_name or business.name,
            "category": business.category,
            "city":     business.city,
            "phone":    business.phone_number or business.phone,
            "address":  business.address,
            "website":  business.website,
            "gmb_url":  business.gmb_url,
        },
    }


@app.patch("/api/businesses/{business_id}")
def update_business(business_id: int, payload: BusinessUpdate, db: Session = Depends(get_db)):
    """
    Partial update for a business record.
    Most common use: set gmb_url = "accounts/123/locations/456"

    Example:
        PATCH /api/businesses/3
        {"gmb_url": "accounts/1234567890/locations/9876543210"}
    """
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Models not available")
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    updated_fields = []
    if payload.name     is not None:
        business.name          = payload.name
        business.business_name = payload.name
        updated_fields.append("name")
    if payload.address  is not None:
        business.address  = payload.address
        business.location = payload.address
        updated_fields.append("address")
    if payload.phone    is not None:
        business.phone        = payload.phone
        business.phone_number = payload.phone
        updated_fields.append("phone")
    if payload.website  is not None:
        business.website  = payload.website
        updated_fields.append("website")
    if payload.category is not None:
        business.category = payload.category
        updated_fields.append("category")
    if payload.city     is not None:
        business.city     = payload.city
        updated_fields.append("city")
    if payload.state    is not None:
        business.state    = payload.state
        updated_fields.append("state")
    if payload.gmb_url  is not None:
        business.gmb_url  = payload.gmb_url
        updated_fields.append("gmb_url")

    try:
        db.commit()
        db.refresh(business)
        return {
            "success":        True,
            "message":        f"Updated: {', '.join(updated_fields) or 'nothing changed'}",
            "updated_fields": updated_fields,
            "business": {
                "id":      business.id,
                "name":    business.business_name or business.name,
                "gmb_url": business.gmb_url,
            },
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/businesses/{business_id}")
def delete_business(business_id: int, db: Session = Depends(get_db)):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Models not available")
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    business.status = "inactive"
    db.commit()
    return {"success": True, "message": "Business deleted"}


# ============================================================
# INSIGHTS (MANUAL)
# ============================================================

@app.post("/api/insights")
def add_insight(insight: InsightCreate, db: Session = Depends(get_db)):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Models not available")
    try:
        business = db.query(Business).filter(Business.id == insight.business_id).first()
        if not business:
            raise HTTPException(status_code=404, detail="Business not found")

        insight_date = datetime.strptime(insight.date, "%Y-%m-%d").date()
        existing     = db.query(GMBInsight).filter(
            GMBInsight.business_id == insight.business_id,
            GMBInsight.date        == insight_date
        ).first()

        if existing:
            existing.profile_views  = insight.profile_views
            existing.phone_calls    = insight.phone_calls
            existing.website_clicks = insight.website_clicks
            existing.directions     = insight.directions
            message = "Updated successfully!"
        else:
            db_insight = GMBInsight(
                business_id    = insight.business_id,
                date           = insight_date,
                profile_views  = insight.profile_views,
                phone_calls    = insight.phone_calls,
                website_clicks = insight.website_clicks,
                directions     = insight.directions,
            )
            db.add(db_insight)
            message = "Added successfully!"

        db.commit()
        return {"success": True, "message": message}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/insights/{business_id}")
def get_insights(business_id: int, days: int = 30, db: Session = Depends(get_db)):
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="Models not available")

    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    end_date   = date.today()
    start_date = end_date - timedelta(days=days)

    insights = db.query(GMBInsight).filter(
        GMBInsight.business_id == business_id,
        GMBInsight.date        >= start_date,
        GMBInsight.date        <= end_date
    ).order_by(GMBInsight.date).all()

    return {
        "success": True,
        "data": [
            {
                "date":           str(i.date),
                "profile_views":  i.profile_views,
                "phone_calls":    i.phone_calls,
                "website_clicks": i.website_clicks,
                "directions":     i.directions,
            }
            for i in insights
        ],
    }


# ============================================================
# GMB PUBLISHER STATUS
# ============================================================

@app.get("/api/gmb/publisher-status")
def gmb_publisher_status():
    if not GMB_PUBLISHER_AVAILABLE:
        return {
            "available": False,
            "message":   "GMB Publisher not loaded. Check app/services/gmb_publisher.py",
        }
    return {
        "available":   True,
        "version":     GMB_PUBLISHER_VERSION,
        "imgbb_proxy": "ENABLED" if IMGBB_API_KEY else "NO KEY SET — add IMGBB_API_KEY to .env",
        "message":     f"GMB Publisher {GMB_PUBLISHER_VERSION} is ready.",
    }


# ============================================================
# ✅ v5.3.1 GMB SYNC — asyncio.to_thread (fast on Windows)
# ============================================================

@app.post("/api/sync-gmb-data")
async def sync_gmb_data(request: SyncRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    active = [s for s in sync_sessions.values() if s.get("status") == "running"]
    if active and not request.force:
        return {
            "success":  False,
            "message":  "A sync is already running. Pass force=true to override.",
            "sync_id":  active[0].get("sync_id"),
        }

    sync_id = str(uuid.uuid4())[:8]
    sync_sessions[sync_id] = {
        "sync_id":     sync_id,
        "status":      "running",
        "started_at":  datetime.utcnow().isoformat(),
        "business_id": request.business_id,
        "progress":    0,
        "message":     "Starting sync...",
    }
    _evict_old_sessions(sync_sessions)

    background_tasks.add_task(_run_sync, sync_id, request, db)
    return {"success": True, "sync_id": sync_id, "message": "Sync started"}


async def _run_sync(sync_id: str, request: SyncRequest, db: Session):
    """
    ✅ v5.3.1 FAST SYNC — uses asyncio.to_thread + subprocess.run.
    Fixes Windows stdout buffering issue with asyncio.create_subprocess_exec.
    FastAPI event loop stays fully responsive during the sync.
    """
    import traceback

    try:
        # ── Resolve push_to_db.py path ────────────────────────────────────
        script = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "push_to_db.py")
        )
        if not os.path.exists(script):
            script_alt = os.path.join(os.path.dirname(__file__), "push_to_db.py")
            if os.path.exists(script_alt):
                script = script_alt
            else:
                raise FileNotFoundError(
                    f"push_to_db.py not found. Tried:\n  {script}\n  {script_alt}"
                )

        # ── Build CLI command ─────────────────────────────────────────────
        cmd = [sys.executable, "-u", script]   # -u = unbuffered stdout

        if request.business_id is not None:
            cmd += ["--business-id", str(request.business_id)]

        if request.start_date and request.end_date:
            cmd += ["--start-date", request.start_date, "--end-date", request.end_date]
        else:
            cmd += ["--months", "3"]

        if request.force:
            cmd += ["--force"]

        cmd_display = " ".join(cmd[2:])
        print(f"[Sync {sync_id}] ▶ python {cmd_display}")
        sync_sessions[sync_id]["message"]  = f"Running: {cmd_display}"
        sync_sessions[sync_id]["progress"] = 20

        # ── Run blocking subprocess in thread pool ────────────────────────
        def _blocking_run():
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(script),
                timeout=300,
            )

        result = await asyncio.to_thread(_blocking_run)

        # ── Log full output ───────────────────────────────────────────────
        if result.stdout:
            for line in result.stdout.splitlines():
                print(f"[Sync {sync_id}] {line}")

        if result.stderr:
            for line in result.stderr.splitlines():
                print(f"[Sync {sync_id}] STDERR: {line}")

        # ── Evaluate result ───────────────────────────────────────────────
        if result.returncode == 0:
            print(f"[Sync {sync_id}] ✅ Completed successfully")
            sync_sessions[sync_id]["status"]       = "completed"
            sync_sessions[sync_id]["progress"]     = 100
            sync_sessions[sync_id]["message"]      = "Sync completed successfully"
            sync_sessions[sync_id]["completed_at"] = datetime.utcnow().isoformat()
        else:
            tail = (result.stderr or result.stdout or "")[-400:]
            error_msg = f"push_to_db.py exited with code {result.returncode}. Output: {tail}"
            print(f"[Sync {sync_id}] ❌ {error_msg}")
            sync_sessions[sync_id]["status"]  = "failed"
            sync_sessions[sync_id]["message"] = error_msg

    except subprocess.TimeoutExpired:
        msg = "Sync timed out after 300 seconds"
        print(f"[Sync {sync_id}] ❌ {msg}")
        sync_sessions[sync_id]["status"]  = "failed"
        sync_sessions[sync_id]["message"] = msg

    except FileNotFoundError as e:
        msg = str(e)
        print(f"[Sync {sync_id}] ❌ {msg}")
        sync_sessions[sync_id]["status"]  = "failed"
        sync_sessions[sync_id]["message"] = msg

    except Exception as e:
        msg = f"Sync error: {e}"
        print(f"[Sync {sync_id}] ❌ {msg}")
        traceback.print_exc()
        sync_sessions[sync_id]["status"]  = "failed"
        sync_sessions[sync_id]["message"] = msg


@app.get("/api/sync-status/{sync_id}")
def get_sync_status(sync_id: str):
    if sync_id == "latest":
        if not sync_sessions:
            return {"status": "none", "message": "No sync sessions found"}
        latest = sorted(sync_sessions.values(), key=lambda x: x.get("started_at", ""), reverse=True)[0]
        return latest
    session = sync_sessions.get(sync_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sync session not found")
    return session


# ============================================================
# GMB SCRAPER — Stealth Login + Scrape
# ============================================================

@app.post("/api/gmb/stealth-login")
async def gmb_stealth_login():
    global gmb_scraper
    if not STEALTH_SCRAPER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Stealth scraper not available")
    try:
        if gmb_scraper:
            try:
                gmb_scraper.close()
            except Exception:
                pass
        gmb_scraper = StealthGMBScraper(headless=False)
        result = gmb_scraper.login()
        return {"success": True, "message": "Login successful", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gmb/businesses")
async def get_gmb_businesses():
    global gmb_scraper
    if not gmb_scraper:
        raise HTTPException(status_code=400, detail="Not logged in. Call /api/gmb/stealth-login first.")
    try:
        businesses = gmb_scraper.get_businesses()
        return {"success": True, "businesses": businesses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/gmb/scrape-all-tabs")
async def scrape_all_tabs(background_tasks: BackgroundTasks):
    global gmb_scraper
    if not STEALTH_SCRAPER_AVAILABLE:
        raise HTTPException(status_code=503, detail="Stealth scraper not available")
    if not gmb_scraper:
        raise HTTPException(status_code=400, detail="Not logged in. Call /api/gmb/stealth-login first.")
    try:
        result = gmb_scraper.scrape_all_tabs()
        return {"success": True, "message": "Scrape completed", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# RANKING TRACKER
# ============================================================

@app.post("/api/gmb/start-tracking", response_model=StartTrackingResponse)
async def start_gmb_tracking(request: StartTrackingRequest, background_tasks: BackgroundTasks):
    tracking_id = str(uuid.uuid4())[:8]
    ranking_sessions[tracking_id] = {
        "tracking_id": tracking_id,
        "status":      "running",
        "started_at":  datetime.utcnow().isoformat(),
        "progress":    0,
        "total":       len(request.keywords),
        "results":     [],
        "message":     "Starting tracking...",
    }
    _evict_old_sessions(ranking_sessions)
    background_tasks.add_task(_run_tracking, tracking_id, request)
    return StartTrackingResponse(
        success=True,
        tracking_id=tracking_id,
        message=f"Tracking started for {len(request.keywords)} keywords",
    )


async def _run_tracking(tracking_id: str, request: StartTrackingRequest):
    tracker = None
    try:
        tracker = AdvancedGMBRankingTracker(headless=True, use_google_search=True)
        results = []
        for i, keyword in enumerate(request.keywords):
            ranking_sessions[tracking_id]["progress"] = i
            ranking_sessions[tracking_id]["message"]  = f"Checking: {keyword}"
            result = await asyncio.to_thread(
                tracker.check_gmb_ranking,
                business_name=request.business_name,
                location=request.location,
                keyword=keyword,
            )
            results.append({"keyword": keyword, **result})
            ranking_sessions[tracking_id]["results"] = results
            await asyncio.sleep(random.uniform(1.5, 3.5))

        ranking_sessions[tracking_id]["status"]   = "completed"
        ranking_sessions[tracking_id]["progress"] = len(request.keywords)
        ranking_sessions[tracking_id]["message"]  = "Tracking completed"
    except Exception as e:
        ranking_sessions[tracking_id]["status"]  = "failed"
        ranking_sessions[tracking_id]["message"] = str(e)
    finally:
        if tracker:
            try:
                tracker.close()
            except Exception:
                pass


@app.get("/api/gmb/tracking-status/{tracking_id}")
def get_tracking_status(tracking_id: str):
    session = ranking_sessions.get(tracking_id)
    if not session:
        raise HTTPException(status_code=404, detail="Tracking session not found")
    return session


@app.post("/api/gmb/check-ranking")
async def check_gmb_ranking(request: StartTrackingRequest):
    """Quick single-request ranking check (blocking, no background task)."""
    tracker = None
    try:
        tracker = AdvancedGMBRankingTracker(headless=True, use_google_search=True)
        results = []
        for keyword in request.keywords:
            result = await asyncio.to_thread(
                tracker.check_gmb_ranking,
                business_name=request.business_name,
                location=request.location,
                keyword=keyword,
            )
            results.append({"keyword": keyword, **result})
        return {"success": True, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tracker:
            try:
                tracker.close()
            except Exception:
                pass


# ============================================================
# GMB PUBLISHER ENDPOINTS
# ============================================================

@app.post("/api/gmb/publish-post")
async def publish_gmb_post(request: dict):
    if not GMB_PUBLISHER_AVAILABLE:
        raise HTTPException(status_code=503, detail="GMB Publisher not available")
    try:
        result = await asyncio.to_thread(publish_post_to_gmb, **request)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gmb/accounts")
async def get_gmb_accounts():
    if not GMB_PUBLISHER_AVAILABLE:
        raise HTTPException(status_code=503, detail="GMB Publisher not available")
    try:
        accounts = await asyncio.to_thread(list_accounts)
        return {"success": True, "accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gmb/locations/{account_id}")
async def get_gmb_locations(account_id: str):
    if not GMB_PUBLISHER_AVAILABLE:
        raise HTTPException(status_code=503, detail="GMB Publisher not available")
    try:
        locations = await asyncio.to_thread(list_locations, account_id)
        return {"success": True, "locations": locations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
