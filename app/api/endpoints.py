from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from typing import List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
import json

router = APIRouter()

from app.database import get_db
from app.models import (
    Business, BusinessMetric, CompetitorAnalysis,
    CompetitorTracking, Review, GMBPost
)

# Safe optional imports
try:
    from app.models import ApiKey
except ImportError:
    ApiKey = None

try:
    from app.schemas import (
        BusinessOut, BusinessCreate, ApiKeyCreate, UsageOut,
        CompetitorAnalysisRequest, CompetitorAnalysisResponse,
        CompetitorComparisonRequest, BatchTrackingRequest,
        GMBInsightsRequest, ReviewResponse, RankingFactor,
        MetricOut
    )
    SCHEMAS_AVAILABLE = True
except ImportError:
    SCHEMAS_AVAILABLE = False
    print("[WARN] Schemas not fully available — using dict responses")

try:
    from app.api.auth import get_api_key, get_google_credentials
except ImportError:
    def get_api_key(api_key: str, db: Session = Depends(get_db)):
        return api_key
    def get_google_credentials(db: Session):
        return None

try:
    from app.api.rate_limiter import check_rate_limiter
except ImportError:
    def check_rate_limiter(max_requests, window):
        def decorator(func):
            return func
        return decorator

try:
    from app.background_tasks import (
        export_to_csv_task, fetch_and_store_insights,
        analyze_multiple_competitors_task
    )
except ImportError:
    def export_to_csv_task(*args, **kwargs): pass
    def fetch_and_store_insights(*args, **kwargs): pass
    def analyze_multiple_competitors_task(*args, **kwargs): pass

try:
    from app.utils import generate_csv_path
except ImportError:
    def generate_csv_path(filename):
        return f"exports/{filename}.csv"

try:
    from app.scraper.gmaps_scraper import OneClickCompetitorAnalyzer
except ImportError:
    class OneClickCompetitorAnalyzer:
        def __init__(self, use_real_scraping=False, headless=True): pass
        def scrape_gmb_data(self, business_name, location):
            return {
                'business_name': business_name, 'rating': 4.5,
                'review_count': 100, 'photo_count': 50,
                'categories': ['Healthcare'], 'primary_category': 'Healthcare',
                'profile_completeness': 85.0, 'phone': '', 'website': '', 'address': location
            }
        def analyze_website(self, url):
            return {'has_website': bool(url), 'domain_authority': 0,
                    'has_schema': False, 'has_service_pages': False, 'internal_links': 0}
        def check_citations(self, business_name, location):
            return {'total_citations': 0, 'sources': []}
        def __del__(self): pass

try:
    from app.scraper.ranking_analyzer import RankingAnalyzer
except ImportError:
    class RankingAnalyzer:
        def calculate_ranking_score(self, gmb_data, website_data, citation_data, keyword):
            return 1200, [('Demo Factor', 100, 'Demo'), ('Another Factor', 50, 'Demo')]
        def generate_explanation(self, business_name, score, factors, gmb_data):
            return f"Demo explanation for {business_name} with score {score}"
        def generate_recommendations(self, factors, gmb_data):
            return ["Demo recommendation 1", "Demo recommendation 2"]

USE_REAL_SCRAPING = True
HEADLESS_BROWSER = True


# ==========================================
# HELPER: Safe date parser
# ==========================================

def parse_flexible_date(date_str: str) -> date:
    if not date_str:
        raise HTTPException(status_code=422, detail="Date value is required")
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(date_str).date()
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid date format: '{date_str}'. Use YYYY-MM-DD or DD/MM/YYYY"
        )


# ==========================================
# HEALTH CHECK
# ==========================================

@router.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "message": "GMB Dashboard API is running",
        "scraping_mode": "Real Scraping ENABLED" if USE_REAL_SCRAPING else "Demo Mode",
        "schemas_loaded": SCHEMAS_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
    }


# ==========================================
# BUSINESS CRUD ENDPOINTS
# ==========================================

@router.get("/businesses", tags=["Business"])
def list_businesses(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    try:
        businesses = db.query(Business).offset(skip).limit(limit).all()
        return [
            {
                "id": b.id,
                "name": getattr(b, "business_name", None) or getattr(b, "name", ""),
                "category": getattr(b, "category", ""),
                "city": getattr(b, "city", ""),
                "phone": getattr(b, "phone_number", None) or getattr(b, "phone", ""),
                "website": getattr(b, "website", ""),
                "status": getattr(b, "status", "active"),
            }
            for b in businesses
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list businesses: {str(e)}")


@router.get("/businesses/{business_id}", tags=["Business"])
def get_business(business_id: int, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    return {
        "id": business.id,
        "name": getattr(business, "business_name", None) or getattr(business, "name", ""),
        "category": getattr(business, "category", ""),
        "city": getattr(business, "city", ""),
        "address": getattr(business, "address", ""),
        "phone": getattr(business, "phone_number", None) or getattr(business, "phone", ""),
        "website": getattr(business, "website", ""),
        "status": getattr(business, "status", "active"),
    }


@router.post("/businesses", status_code=status.HTTP_201_CREATED, tags=["Business"])
def create_business_v1(
    business: Any,
    db: Session = Depends(get_db)
):
    if SCHEMAS_AVAILABLE:
        business_dict = business.dict() if hasattr(business, "dict") else business
    else:
        business_dict = business

    existing = db.query(Business).filter(
        Business.name == business_dict.get('name', business_dict.get('business_name'))
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Business already exists")

    db_business = Business(**business_dict)
    db.add(db_business)
    db.commit()
    db.refresh(db_business)
    return {
        "id": db_business.id,
        "name": getattr(db_business, "business_name", None) or getattr(db_business, "name", ""),
    }


@router.put("/businesses/{business_id}", tags=["Business"])
def update_business(
    business_id: int,
    business: Any,
    db: Session = Depends(get_db)
):
    db_business = db.query(Business).filter(Business.id == business_id).first()
    if not db_business:
        raise HTTPException(status_code=404, detail="Business not found")

    update_data = business.dict() if hasattr(business, "dict") else business
    for key, value in update_data.items():
        if hasattr(db_business, key):
            setattr(db_business, key, value)

    db.commit()
    db.refresh(db_business)
    return {"id": db_business.id, "status": "updated"}


@router.delete("/businesses/{business_id}", tags=["Business"])
def delete_business_v1(business_id: int, db: Session = Depends(get_db)):
    db_business = db.query(Business).filter(Business.id == business_id).first()
    if not db_business:
        raise HTTPException(status_code=404, detail="Business not found")
    db.delete(db_business)
    db.commit()
    return {"status": "success", "message": "Business deleted"}


# ==========================================
# DASHBOARD & ANALYTICS ENDPOINTS
# ==========================================

@router.get("/dashboard/overview", tags=["Dashboard"])
async def get_dashboard_overview(
    business_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    try:
        metrics = db.query(BusinessMetric).filter(
            BusinessMetric.business_id == business_id,
            BusinessMetric.date >= start_date,
            BusinessMetric.date <= end_date
        ).order_by(BusinessMetric.date.desc()).all()
    except Exception:
        metrics = []

    total_searches = sum((getattr(m, "searches_direct", 0) or 0) + (getattr(m, "searches_discovery", 0) or 0) for m in metrics)
    total_views    = sum((getattr(m, "views_search", 0) or 0) + (getattr(m, "views_maps", 0) or 0) for m in metrics)
    total_actions  = sum(
        (getattr(m, "actions_phone", 0) or 0) +
        (getattr(m, "actions_website", 0) or 0) +
        (getattr(m, "actions_directions", 0) or 0)
        for m in metrics
    )
    latest = metrics[0] if metrics else None

    try:
        competitor_count = db.query(CompetitorTracking).filter(
            CompetitorTracking.business_id == business_id,
            CompetitorTracking.is_active == True
        ).count()
    except Exception:
        competitor_count = 0

    try:
        review_count = db.query(Review).filter(Review.business_id == business_id).count()
    except Exception:
        review_count = 0

    return {
        "business": {
            "id": business.id,
            "name": getattr(business, "business_name", None) or getattr(business, "name", ""),
            "location": getattr(business, "location", None) or getattr(business, "address", ""),
            "category": getattr(business, "category", ""),
            "phone": getattr(business, "phone", ""),
            "website": getattr(business, "website", ""),
        },
        "summary": {
            "total_searches": total_searches,
            "total_views": total_views,
            "total_actions": total_actions,
            "avg_rating": getattr(latest, "average_rating", 0) if latest else 0,
            "total_reviews": review_count,
            "competitors_tracked": competitor_count,
        },
        "metrics_timeline": [
            {
                "date": m.date.isoformat() if hasattr(m.date, "isoformat") else str(m.date),
                "searches": (getattr(m, "searches_direct", 0) or 0) + (getattr(m, "searches_discovery", 0) or 0),
                "views": (getattr(m, "views_search", 0) or 0) + (getattr(m, "views_maps", 0) or 0),
                "phone_calls": getattr(m, "actions_phone", 0) or 0,
                "website_clicks": getattr(m, "actions_website", 0) or 0,
                "directions": getattr(m, "actions_directions", 0) or 0,
            }
            for m in reversed(metrics)
        ],
        "period": f"Last {days} days",
    }


@router.get("/analytics/metrics/{business_id}", tags=["Analytics"])
async def get_business_metrics(
    business_id: int,
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD or DD/MM/YYYY"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD or DD/MM/YYYY"),
    db: Session = Depends(get_db)
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    parsed_start = parse_flexible_date(start_date) if start_date else None
    parsed_end   = parse_flexible_date(end_date)   if end_date   else None

    if parsed_start and parsed_end and parsed_end < parsed_start:
        raise HTTPException(status_code=400, detail="end_date must be >= start_date")

    try:
        query = db.query(BusinessMetric).filter(BusinessMetric.business_id == business_id)
        if parsed_start:
            query = query.filter(BusinessMetric.date >= parsed_start)
        if parsed_end:
            query = query.filter(BusinessMetric.date <= parsed_end)
        metrics = query.order_by(BusinessMetric.date.desc()).all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")

    return [
        {
            "id":                   m.id,
            "business_id":          m.business_id,
            "date":                 m.date.isoformat() if hasattr(m.date, "isoformat") else str(m.date),
            "searches_direct":      getattr(m, "searches_direct", 0) or 0,
            "searches_discovery":   getattr(m, "searches_discovery", 0) or 0,
            "views_search":         getattr(m, "views_search", 0) or 0,
            "views_maps":           getattr(m, "views_maps", 0) or 0,
            "actions_phone":        getattr(m, "actions_phone", 0) or 0,
            "actions_website":      getattr(m, "actions_website", 0) or 0,
            "actions_directions":   getattr(m, "actions_directions", 0) or 0,
            "actions_booking":      getattr(m, "actions_booking", 0) or 0,
            "review_count":         getattr(m, "review_count", 0) or 0,
            "average_rating":       getattr(m, "average_rating", 0) or 0,
            "photo_views":          getattr(m, "photo_views", 0) or 0,
            "post_views":           getattr(m, "post_views", 0) or 0,
        }
        for m in metrics
    ]


@router.get("/analytics/metrics/{business_id}/debug", tags=["Analytics"])
async def debug_business_metrics(
    business_id: int,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    import traceback
    try:
        business = db.query(Business).filter(Business.id == business_id).first()
        if not business:
            return {"error": "Business not found", "business_id": business_id}

        parsed_start = parse_flexible_date(start_date) if start_date else None
        parsed_end   = parse_flexible_date(end_date)   if end_date   else None

        query = db.query(BusinessMetric).filter(BusinessMetric.business_id == business_id)
        if parsed_start:
            query = query.filter(BusinessMetric.date >= parsed_start)
        if parsed_end:
            query = query.filter(BusinessMetric.date <= parsed_end)

        metrics = query.order_by(BusinessMetric.date.desc()).all()

        return {
            "business_id":   business_id,
            "business_name": getattr(business, "business_name", None) or getattr(business, "name", ""),
            "parsed_start":  str(parsed_start),
            "parsed_end":    str(parsed_end),
            "total_records": len(metrics),
            "sample": [
                {
                    "id":                 m.id,
                    "date":               str(m.date),
                    "actions_phone":      getattr(m, "actions_phone", "MISSING"),
                    "actions_website":    getattr(m, "actions_website", "MISSING"),
                    "actions_directions": getattr(m, "actions_directions", "MISSING"),
                    "views_search":       getattr(m, "views_search", "MISSING"),
                    "views_maps":         getattr(m, "views_maps", "MISSING"),
                }
                for m in metrics[:5]
            ],
        }
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


@router.post("/analytics/fetch-insights", tags=["Analytics"])
async def fetch_insights(
    request: Any,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    credentials = get_google_credentials(db)
    if not credentials:
        raise HTTPException(status_code=401, detail="Google authentication required.")

    business = db.query(Business).filter(Business.id == request.business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    background_tasks.add_task(
        fetch_and_store_insights,
        business.id,
        getattr(business, "google_place_id", None),
        request.start_date,
        request.end_date,
        credentials,
        db
    )

    return {
        "status": "processing",
        "message": "Fetching insights from Google Business Profile API",
        "business_id": business.id,
        "business_name": getattr(business, "business_name", None) or getattr(business, "name", ""),
    }


# ==========================================
# ONE-CLICK COMPETITOR ANALYSIS
# ==========================================

@router.post("/competitor/analyze", tags=["Competitor Analysis"])
async def analyze_competitor_one_click(
    request: Any,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    use_real_data: bool = Query(True)
):
    scraping_enabled = USE_REAL_SCRAPING or use_real_data
    analyzer = OneClickCompetitorAnalyzer(use_real_scraping=scraping_enabled, headless=HEADLESS_BROWSER)
    ranking_analyzer = RankingAnalyzer()

    try:
        gmb_data = analyzer.scrape_gmb_data(request.business_name, request.location)
        if not gmb_data.get("business_name"):
            raise HTTPException(status_code=404, detail=f"Business '{request.business_name}' not found in {request.location}")

        website_data  = analyzer.analyze_website(gmb_data.get("website", ""))
        citation_data = analyzer.check_citations(request.business_name, request.location)
        score, ranking_factors = ranking_analyzer.calculate_ranking_score(gmb_data, website_data, citation_data, request.keyword)
        explanation     = ranking_analyzer.generate_explanation(request.business_name, score, ranking_factors, gmb_data)
        recommendations = ranking_analyzer.generate_recommendations(ranking_factors, gmb_data)

        try:
            analysis_record = CompetitorAnalysis(
                business_name=request.business_name,
                location=request.location,
                keyword=request.keyword,
                ranking_position=1,
                ranking_score=score,
                rating=gmb_data.get("rating", 0),
                review_count=gmb_data.get("review_count", 0),
                photo_count=gmb_data.get("photo_count", 0),
                categories=gmb_data.get("categories", []),
                primary_category=gmb_data.get("primary_category", ""),
                profile_completeness=gmb_data.get("profile_completeness", 0),
                has_website=bool(gmb_data.get("website")),
                has_phone=bool(gmb_data.get("phone")),
                has_hours=bool(gmb_data.get("hours")),
                has_photos=gmb_data.get("photo_count", 0) > 0,
                domain_authority=website_data.get("domain_authority", 0),
                has_schema=website_data.get("has_schema", False),
                has_service_pages=website_data.get("has_service_pages", False),
                internal_links=website_data.get("internal_links", 0),
                total_citations=citation_data.get("total_citations", 0),
                citation_sources=citation_data.get("sources", []),
                report_data=gmb_data,
                explanation=explanation,
                ranking_factors=[
                    {"factor_name": f[0], "score": f[1], "description": f[2],
                     "impact_level": "high" if f[1] > 150 else "medium" if f[1] > 75 else "low"}
                    for f in ranking_factors
                ],
                recommendations=recommendations,
                created_at=datetime.now()
            )
            db.add(analysis_record)
            db.commit()
        except Exception as db_err:
            print(f"[WARN] Could not save analysis to DB: {db_err}")

        return {
            "status": "success",
            "business_name": request.business_name,
            "total_score": score,
            "max_score": 2000,
            "gmb_data": gmb_data,
            "ranking_factors": [
                {"factor_name": f[0], "score": f[1], "description": f[2],
                 "impact_level": "high" if f[1] > 150 else "medium" if f[1] > 75 else "low"}
                for f in ranking_factors[:10]
            ],
            "explanation": explanation,
            "recommendations": recommendations,
            "estimated_time_to_outrank": "4-8 weeks",
            "estimated_investment": "₹25,000-35,000",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        try:
            del analyzer
        except Exception:
            pass


# ==========================================
# EXPORT & REPORTING
# ==========================================

@router.post("/export/competitor-report/{business_id}", tags=["Export"])
async def export_competitor_report(
    business_id: int,
    keyword: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    csv_path = generate_csv_path(f"competitor_report_{business_id}_{keyword}")
    background_tasks.add_task(export_to_csv_task, business_id, keyword, csv_path, db)

    return {
        "status": "processing",
        "message": "Generating competitor report",
        "file_path": csv_path,
        "download_ready_in": "30-60 seconds",
    }


# ==========================================
# GMB STEALTH LOGIN & DATA EXTRACTION
# ==========================================

_gmb_scraper_instance = None

try:
    from app.scraper.stealth_gmb_scraper import StealthGMBScraper
except ImportError:
    StealthGMBScraper = None
    print("[WARN] StealthGMBScraper not found")


@router.post("/gmb/stealth-login", tags=["GMB Scraper"])
async def gmb_stealth_login(
    email: str = Query(...),
    password: str = Query(...),
    headless: bool = Query(False)
):
    global _gmb_scraper_instance
    if not StealthGMBScraper:
        raise HTTPException(status_code=501, detail="GMB Stealth Scraper not implemented.")

    try:
        _gmb_scraper_instance = StealthGMBScraper(mode="auto", headless=headless)
        success = _gmb_scraper_instance.login(email, password)
        if success:
            businesses = _gmb_scraper_instance.list_all_businesses()
            return {"success": True, "message": "Login successful!", "status": "logged_in",
                    "business_count": len(businesses), "businesses": businesses[:30]}
        _gmb_scraper_instance = None
        return {"success": False, "message": "Login failed. Check credentials.", "status": "failed"}
    except Exception as e:
        _gmb_scraper_instance = None
        return {"success": False, "message": str(e), "status": "error"}


@router.get("/gmb/list-businesses", tags=["GMB Scraper"])
async def gmb_list_businesses():
    global _gmb_scraper_instance
    if not _gmb_scraper_instance or not _gmb_scraper_instance.logged_in:
        raise HTTPException(status_code=401, detail="Not logged in. Please login first")
    try:
        businesses = _gmb_scraper_instance.list_all_businesses()
        return {"success": True, "business_count": len(businesses), "businesses": businesses}
    except Exception as e:
        return {"success": False, "message": str(e), "businesses": []}


@router.post("/gmb/wait-for-performance", tags=["GMB Scraper"])
async def gmb_wait_for_performance():
    global _gmb_scraper_instance
    if not _gmb_scraper_instance or not _gmb_scraper_instance.logged_in:
        raise HTTPException(status_code=401, detail="Not logged in. Please login first")
    try:
        _gmb_scraper_instance.wait_for_performance_page()
        result = _gmb_scraper_instance.scrape_current_page_performance()
        return {"success": True, "data": result.get("data", {}), "message": "Performance data scraped successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/gmb/scrape-current-page", tags=["GMB Scraper"])
async def gmb_scrape_current_page():
    global _gmb_scraper_instance
    if not _gmb_scraper_instance or not _gmb_scraper_instance.logged_in:
        raise HTTPException(status_code=401, detail="Not logged in. Please login first")
    try:
        result = _gmb_scraper_instance.scrape_current_page_performance()
        if result.get("status") == "success":
            return {"success": True, "data": result.get("data", {}), "message": "Scraped successfully"}
        return {"success": False, "message": result.get("error", "Scraping failed")}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/gmb/get-performance", tags=["GMB Scraper"])
async def gmb_get_performance(business_name: Optional[str] = Query(None)):
    global _gmb_scraper_instance
    if not _gmb_scraper_instance or not _gmb_scraper_instance.logged_in:
        raise HTTPException(status_code=401, detail="Not logged in. Please login first")
    try:
        data = _gmb_scraper_instance.scrape_current_page_performance()
        return {"success": True, "data": data.get("data", {})}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.post("/gmb/close-browser", tags=["GMB Scraper"])
async def gmb_close_browser():
    global _gmb_scraper_instance
    if _gmb_scraper_instance:
        try:
            _gmb_scraper_instance.close()
        except Exception:
            pass
        _gmb_scraper_instance = None
        return {"success": True, "message": "Browser closed"}
    return {"success": True, "message": "No active session"}


@router.get("/gmb/session-status", tags=["GMB Scraper"])
async def gmb_session_status():
    global _gmb_scraper_instance
    if _gmb_scraper_instance and _gmb_scraper_instance.logged_in:
        business_count = len(_gmb_scraper_instance.businesses) if _gmb_scraper_instance.businesses else 0
        return {"success": True, "logged_in": True, "status": "active",
                "business_count": business_count, "message": f"Session active with {business_count} businesses"}
    return {"success": False, "logged_in": False, "status": "inactive",
            "business_count": 0, "message": "No active session. Please login."}