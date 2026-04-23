from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==========================================
# EXISTING BUSINESS SCHEMAS (PRESERVED)
# ==========================================

class BusinessBase(BaseModel):
    name: str
    phone: str
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    source: Optional[str] = None


class BusinessCreate(BusinessBase):
    """Create new business - uses existing structure"""
    business_name: Optional[str] = None  # Added for GMB compatibility
    location: Optional[str] = None
    category: Optional[str] = None
    website: Optional[str] = None
    google_place_id: Optional[str] = None


class BusinessOut(BusinessBase):
    id: int
    business_name: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = None
    website: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2+


class BusinessUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    business_name: Optional[str] = None
    location: Optional[str] = None
    category: Optional[str] = None
    website: Optional[str] = None


# ==========================================
# EXISTING API KEY SCHEMAS (PRESERVED)
# ==========================================

class ApiKeyCreate(BaseModel):
    quota: Optional[int] = 10000
    user_id: Optional[int] = None
    key_name: Optional[str] = None


class ApiKeyOut(BaseModel):
    id: int
    key: str
    user_id: Optional[int]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==========================================
# EXISTING USAGE SCHEMAS (PRESERVED)
# ==========================================

class UsageOut(BaseModel):
    key: str
    quota: int
    used: int
    total_requests: Optional[int] = 0
    requests_today: Optional[int] = 0
    requests_this_month: Optional[int] = 0
    rate_limit_remaining: Optional[int] = None


# ==========================================
# NEW: METRICS SCHEMAS
# ==========================================

class MetricOut(BaseModel):
    id: int
    business_id: int
    date: datetime
    searches_direct: int
    searches_discovery: int
    views_search: int
    views_maps: int
    actions_phone: int
    actions_website: int
    actions_directions: int
    actions_booking: int
    review_count: int
    average_rating: float
    photo_views: int
    post_views: int
    
    class Config:
        from_attributes = True


class MetricCreate(BaseModel):
    business_id: int
    searches_direct: int = 0
    searches_discovery: int = 0
    views_search: int = 0
    views_maps: int = 0
    actions_phone: int = 0
    actions_website: int = 0
    actions_directions: int = 0
    actions_booking: int = 0


# ==========================================
# NEW: COMPETITOR ANALYSIS SCHEMAS
# ==========================================

class CompetitorAnalysisRequest(BaseModel):
    business_name: str = Field(..., min_length=1, max_length=255)
    location: str = Field(..., min_length=1, max_length=255)
    keyword: str = Field(..., min_length=1, max_length=100)


class RankingFactor(BaseModel):
    factor_name: str
    score: int
    description: str
    impact_level: str  # high, medium, low


class CompetitorAnalysisResponse(BaseModel):
    status: str
    business_name: str
    ranking_position: int
    total_score: int
    max_score: int
    gmb_data: Dict[str, Any]
    ranking_factors: List[RankingFactor]
    explanation: str
    recommendations: List[str]
    competitive_gaps: Dict[str, Any]
    estimated_time_to_outrank: str
    estimated_investment: str


class CompetitorAnalysisOut(BaseModel):
    id: int
    business_name: str
    location: str
    keyword: str
    ranking_position: int
    ranking_score: int
    rating: float
    review_count: int
    photo_count: int
    categories: List[str]
    primary_category: str
    profile_completeness: float
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==========================================
# NEW: COMPETITOR COMPARISON SCHEMAS
# ==========================================

class CompetitorComparisonRequest(BaseModel):
    your_business_id: int
    competitor_names: List[str] = Field(..., min_items=1, max_items=10)
    location: str
    keyword: str


class CompetitorComparisonOut(BaseModel):
    your_business: Dict[str, Any]
    competitors: List[Dict[str, Any]]
    total_competitors: int
    keyword: str
    location: str


# ==========================================
# NEW: TRACKING SCHEMAS
# ==========================================

class BatchTrackingRequest(BaseModel):
    business_id: int
    competitors: List[str] = Field(..., min_items=1, max_items=20)
    location: str
    keywords: List[str] = Field(..., min_items=1, max_items=10)
    tracking_frequency: str = Field(default="weekly", pattern="^(daily|weekly|monthly)$")


class CompetitorTrackingOut(BaseModel):
    id: int
    business_id: int
    competitor_name: str
    location: str
    keyword: str
    tracking_frequency: str
    is_active: bool
    last_tracked: Optional[datetime]
    next_track_date: Optional[datetime]
    current_position: Optional[int]
    current_score: Optional[int]
    
    class Config:
        from_attributes = True


class TrackingStatusUpdate(BaseModel):
    is_active: bool


# ==========================================
# NEW: GMB INSIGHTS SCHEMAS
# ==========================================

class GMBInsightsRequest(BaseModel):
    business_id: int
    start_date: str  # ISO format: YYYY-MM-DD
    end_date: str    # ISO format: YYYY-MM-DD
    metrics: List[str] = Field(
        default=["searches", "views", "calls", "directions"],
        max_items=10
    )
    
    @validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError('Date must be in ISO format: YYYY-MM-DD')


class GMBInsightsResponse(BaseModel):
    status: str
    business_id: int
    business_name: str
    message: str
    date_range: Optional[Dict[str, str]] = None


# ==========================================
# NEW: REVIEW SCHEMAS
# ==========================================

class ReviewOut(BaseModel):
    id: int
    business_id: int
    reviewer_name: str
    rating: float
    review_text: str
    review_date: datetime
    reply_text: Optional[str]
    reply_date: Optional[datetime]
    sentiment: str
    is_deleted: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReviewResponse(BaseModel):
    review_id: int
    response_text: str = Field(..., min_length=10, max_length=1000)


class ReviewCreate(BaseModel):
    business_id: int
    reviewer_name: str
    rating: float = Field(..., ge=1.0, le=5.0)
    review_text: str
    review_date: datetime
    sentiment: str = Field(default="neutral", pattern="^(positive|negative|neutral)$")


class ReviewStats(BaseModel):
    total_reviews: int
    average_rating: float
    positive_reviews: int
    negative_reviews: int
    neutral_reviews: int
    response_rate: float
    avg_response_time_hours: float


# ==========================================
# NEW: POST SCHEMAS
# ==========================================

class GMBPostCreate(BaseModel):
    business_id: int
    post_type: str = Field(..., pattern="^(offer|event|update)$")
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1, max_length=1500)
    cta_type: str = Field(default="learn_more", pattern="^(call|book|learn_more|order|shop)$")
    media_url: Optional[str] = None
    scheduled_date: Optional[datetime] = None


class GMBPostOut(BaseModel):
    id: int
    business_id: int
    post_type: str
    title: str
    content: str
    cta_type: str
    media_url: Optional[str]
    scheduled_date: Optional[datetime]
    published_date: Optional[datetime]
    status: str
    views: int
    clicks: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ==========================================
# NEW: DASHBOARD SCHEMAS
# ==========================================

class DashboardSummary(BaseModel):
    business_id: int
    business_name: str
    location: str
    total_searches: int
    total_views: int
    total_actions: int
    avg_rating: float
    total_reviews: int
    competitors_tracked: int
    period: str


class PerformanceMetric(BaseModel):
    date: str
    searches: int
    views: int
    phone_calls: int
    website_clicks: int
    directions: int


# ==========================================
# NEW: RANKING INSIGHTS SCHEMAS
# ==========================================

class RankingFactorDetail(BaseModel):
    factor: str
    max_points: int
    importance: str
    description: str
    optimization_tip: str


class RankingFactorsResponse(BaseModel):
    keyword: str
    location: str
    last_updated: str
    ranking_factors: List[RankingFactorDetail]
    total_max_score: int
    recommended_minimum_score: int
    top_3_threshold: int


class CompetitiveBenchmark(BaseModel):
    business_name: str
    keyword: str
    location: str
    benchmarks: Dict[str, Any]
    recommendations: List[str]
    total_competitors_analyzed: int


# ==========================================
# NEW: EXPORT SCHEMAS
# ==========================================

class ExportRequest(BaseModel):
    business_id: int
    keyword: str
    format: str = Field(default="csv", pattern="^(csv|pdf|json)$")
    include_history: bool = False


class ExportResponse(BaseModel):
    status: str
    message: str
    file_path: str
    download_ready_in: str


# ==========================================
# NEW: ERROR SCHEMAS
# ==========================================

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ==========================================
# NEW: PAGINATION SCHEMAS
# ==========================================

class PaginationParams(BaseModel):
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1, le=500)


class PaginatedResponse(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[Any]


# ==========================================
# NEW: AUTHENTICATION SCHEMAS
# ==========================================

class GoogleAuthRequest(BaseModel):
    authorization_code: str


class GoogleAuthResponse(BaseModel):
    status: str
    message: str
    access_token: Optional[str]
    refresh_token: Optional[str]
    expires_in: Optional[int]


# ==========================================
# NEW: WEBHOOK SCHEMAS
# ==========================================

class WebhookEvent(BaseModel):
    event_type: str
    business_id: int
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class WebhookSubscription(BaseModel):
    business_id: int
    webhook_url: str
    events: List[str] = Field(..., min_items=1)
    is_active: bool = True
