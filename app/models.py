from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


# ==========================================
# EXISTING MODELS (PRESERVED & ENHANCED)
# ==========================================


class Business(Base):
    __tablename__ = "businesses"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String, index=True, nullable=False)
    phone           = Column(String, nullable=False)
    address         = Column(String)
    lat             = Column(Float)
    lng             = Column(Float)
    source          = Column(String)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())

    business_name   = Column(String, index=True)
    location        = Column(String)
    category        = Column(String)
    website         = Column(String)
    google_place_id = Column(String, unique=True)

    phone_number    = Column(String)
    city            = Column(String)
    state           = Column(String)
    gmb_url         = Column(String)
    status          = Column(String, default="active")

    metrics          = relationship("BusinessMetric",     back_populates="business", cascade="all, delete-orphan")
    competitors      = relationship("CompetitorTracking", back_populates="business", cascade="all, delete-orphan")
    reviews          = relationship("Review",             back_populates="business", cascade="all, delete-orphan")
    posts            = relationship("GMBPost",            back_populates="business", cascade="all, delete-orphan")
    performance_data = relationship("GMBPerformance",     back_populates="business", cascade="all, delete-orphan")
    insights         = relationship("GMBInsight",         back_populates="business", cascade="all, delete-orphan")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id         = Column(Integer, primary_key=True, index=True)
    key        = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    quota      = Column(Integer, default=10000)
    used       = Column(Integer, default=0)
    user_id    = Column(Integer, index=True)
    is_active  = Column(Boolean, default=True)
    last_used  = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))


# ==========================================
# BUSINESS METRICS
# ==========================================


class BusinessMetric(Base):
    __tablename__ = "business_metrics"

    id          = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    date        = Column(DateTime(timezone=True), default=func.now(), index=True)

    searches_direct    = Column(Integer, default=0)
    searches_discovery = Column(Integer, default=0)
    views_search       = Column(Integer, default=0)
    views_maps         = Column(Integer, default=0)
    actions_phone      = Column(Integer, default=0)
    actions_website    = Column(Integer, default=0)
    actions_directions = Column(Integer, default=0)
    actions_booking    = Column(Integer, default=0)
    review_count       = Column(Integer, default=0)
    average_rating     = Column(Float,   default=0.0)
    photo_views        = Column(Integer, default=0)
    post_views         = Column(Integer, default=0)
    created_at         = Column(DateTime(timezone=True), server_default=func.now())

    business = relationship("Business", back_populates="metrics")


# ==========================================
# GMB INSIGHT
# ==========================================


class GMBInsight(Base):
    __tablename__ = "gmb_insights"

    id          = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    date        = Column(Date, nullable=False, index=True)

    profile_views = Column(Integer, default=0)
    search_views  = Column(Integer, default=0)
    maps_views    = Column(Integer, default=0)

    google_search_mobile  = Column(Integer, default=0)
    google_search_desktop = Column(Integer, default=0)
    google_maps_mobile    = Column(Integer, default=0)
    google_maps_desktop   = Column(Integer, default=0)

    phone_calls    = Column(Integer, default=0)
    website_clicks = Column(Integer, default=0)
    directions     = Column(Integer, default=0)
    conversations  = Column(Integer, default=0)
    bookings       = Column(Integer, default=0)

    profile_interactions = Column(Integer, default=0)
    photo_views          = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    business = relationship("Business", back_populates="insights")


# ==========================================
# GMB PERFORMANCE
# ==========================================


class GMBPerformance(Base):
    __tablename__ = "gmb_performance"

    id          = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    metric_date = Column(DateTime(timezone=True), nullable=False, index=True)

    profile_interactions_total = Column(Integer, default=0)

    discovery_searches = Column(Integer, default=0)
    direct_searches    = Column(Integer, default=0)
    branded_searches   = Column(Integer, default=0)

    views_search = Column(Integer, default=0)
    views_maps   = Column(Integer, default=0)

    views_search_mobile  = Column(Integer, default=0)
    views_search_desktop = Column(Integer, default=0)
    views_maps_mobile    = Column(Integer, default=0)
    views_maps_desktop   = Column(Integer, default=0)

    actions_website_clicks     = Column(Integer, default=0)
    actions_phone_calls        = Column(Integer, default=0)
    actions_direction_requests = Column(Integer, default=0)
    actions_bookings           = Column(Integer, default=0)
    actions_messages           = Column(Integer, default=0)
    actions_food_orders        = Column(Integer, default=0)

    photo_views_total    = Column(Integer, default=0)
    photo_views_owner    = Column(Integer, default=0)
    photo_views_customer = Column(Integer, default=0)
    photo_count_total    = Column(Integer, default=0)
    photo_count_new      = Column(Integer, default=0)

    reviews_total_count    = Column(Integer, default=0)
    reviews_new_count      = Column(Integer, default=0)
    reviews_average_rating = Column(Float,   default=0.0)
    reviews_replied_count  = Column(Integer, default=0)
    reviews_pending_count  = Column(Integer, default=0)

    posts_total_views  = Column(Integer, default=0)
    posts_total_clicks = Column(Integer, default=0)
    posts_published    = Column(Integer, default=0)

    change_interactions = Column(Float, default=0.0)
    change_searches     = Column(Float, default=0.0)
    change_actions      = Column(Float, default=0.0)

    competitor_comparison = Column(JSON)
    market_position_score = Column(Integer, default=0)

    search_keywords_json = Column(Text, nullable=True)
    raw_data             = Column(JSON)

    data_source  = Column(String,  default="api")
    is_estimated = Column(Boolean, default=False)
    notes        = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    business = relationship("Business", back_populates="performance_data")


# ==========================================
# COMPETITOR ANALYSIS
# ==========================================


class CompetitorAnalysis(Base):
    __tablename__ = "competitor_analysis"

    id            = Column(Integer, primary_key=True, index=True)
    business_name = Column(String,  index=True, nullable=False)
    location      = Column(String,  nullable=False)
    keyword       = Column(String,  index=True, nullable=False)

    ranking_position = Column(Integer)
    ranking_score    = Column(Integer)
    rating           = Column(Float,   default=0.0)
    review_count     = Column(Integer, default=0)
    photo_count      = Column(Integer, default=0)
    categories       = Column(JSON)
    primary_category = Column(String)

    has_website          = Column(Boolean, default=False)
    has_phone            = Column(Boolean, default=False)
    has_hours            = Column(Boolean, default=False)
    has_photos           = Column(Boolean, default=False)
    profile_completeness = Column(Float,   default=0.0)

    domain_authority  = Column(Integer, default=0)
    has_schema        = Column(Boolean, default=False)
    has_service_pages = Column(Boolean, default=False)
    internal_links    = Column(Integer, default=0)

    total_citations  = Column(Integer, default=0)
    citation_sources = Column(JSON)

    report_data     = Column(JSON)
    explanation     = Column(Text)
    ranking_factors = Column(JSON)
    recommendations = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ==========================================
# COMPETITOR TRACKING
# ==========================================


class CompetitorTracking(Base):
    __tablename__ = "competitor_tracking"

    id                  = Column(Integer, primary_key=True, index=True)
    business_id         = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)
    competitor_name     = Column(String,  nullable=False)
    competitor_place_id = Column(String)
    location            = Column(String,  nullable=False)
    keyword             = Column(String,  nullable=False, index=True)

    tracking_frequency = Column(String,  default="weekly")
    is_active          = Column(Boolean, default=True, index=True)
    last_tracked       = Column(DateTime(timezone=True))
    next_track_date    = Column(DateTime(timezone=True))

    current_position = Column(Integer)
    current_score    = Column(Integer)
    current_rating   = Column(Float)
    current_reviews  = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    business = relationship("Business", back_populates="competitors")


# ==========================================
# REVIEW
# ==========================================


class Review(Base):
    __tablename__ = "reviews"

    id          = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)

    reviewer_name = Column(String,  nullable=False)
    rating        = Column(Float,   nullable=False)
    review_text   = Column(Text)
    review_date   = Column(DateTime(timezone=True), nullable=False, index=True)

    reply_text = Column(Text)
    reply_date = Column(DateTime(timezone=True))

    sentiment        = Column(String,  default="neutral")
    is_deleted       = Column(Boolean, default=False)
    google_review_id = Column(String,  unique=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    business = relationship("Business", back_populates="reviews")


# ==========================================
# GMB POST
# ✅ status: plain String(50) — no SAEnum needed
#    Valid values: "draft" | "scheduled" | "published" | "failed" | "pending"
# ✅ v5.1: Added ai_generated, ai_topic, content_angle for AI auto-post feature
# ==========================================


class GMBPost(Base):
    __tablename__ = "gmb_posts"

    id          = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)

    # Core post fields
    post_type = Column(String(50),   nullable=False, default="update")
    title     = Column(String(500),  nullable=True)
    content   = Column(Text,         nullable=False)
    media_url = Column(String(1000), nullable=True)

    # CTA
    cta_type  = Column(String(50),  nullable=True)
    cta_value = Column(String(512), nullable=True)

    # GMB location resource: accounts/{id}/locations/{id}
    profile_id = Column(String(512), nullable=True, index=True)

    # Scheduling
    scheduled_date = Column(DateTime(timezone=True), nullable=True)
    published_date = Column(DateTime(timezone=True), nullable=True)

    # Status — supports: draft | scheduled | published | failed | pending
    status = Column(String(50), nullable=False, default="draft", index=True)

    # Error tracking
    error_log   = Column(Text,    nullable=True)
    retry_count = Column(Integer, default=0)

    # GMB API response
    google_post_id = Column(String(512), nullable=True)

    # Engagement metrics
    views  = Column(Integer, default=0)
    clicks = Column(Integer, default=0)

    # ── AI Auto-Post fields (v5.1) ──────────────────────────────────────────
    # True when the post was created via /auto-generate endpoint
    ai_generated  = Column(Boolean,     nullable=False, default=False, index=True)
    # The topic/headline chosen by AI (e.g. "May Special Offer — Bright Smiles")
    ai_topic      = Column(String(300),  nullable=True)
    # Content angle used (seasonal_offer | service_highlight | before_after |
    #                     tips_faq | client_result | why_choose_us)
    content_angle = Column(String(100),  nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    business = relationship("Business", back_populates="posts")


# ==========================================
# USER
# ==========================================


class User(Base):
    __tablename__ = "users"

    id           = Column(Integer, primary_key=True, index=True)
    email        = Column(String, unique=True, index=True, nullable=False)
    full_name    = Column(String)
    company_name = Column(String)

    hashed_password = Column(String)
    is_active       = Column(Boolean, default=True)
    is_verified     = Column(Boolean, default=False)

    google_access_token  = Column(String)
    google_refresh_token = Column(String)
    google_token_expiry  = Column(DateTime(timezone=True))

    subscription_tier    = Column(String, default="free")
    subscription_expires = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))


# ==========================================
# NOTIFICATION
# ==========================================


class Notification(Base):
    __tablename__ = "notifications"

    id          = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), index=True)

    notification_type = Column(String, nullable=False)
    title             = Column(String, nullable=False)
    message           = Column(Text,   nullable=False)
    severity          = Column(String, default="info")

    is_read    = Column(Boolean, default=False)
    is_sent    = Column(Boolean, default=False)
    extra_data = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ==========================================
# AUDIT LOG
# ==========================================


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, index=True)
    business_id = Column(Integer, index=True)

    action        = Column(String, nullable=False, index=True)
    resource_type = Column(String)
    resource_id   = Column(Integer)

    ip_address = Column(String)
    user_agent = Column(String)

    status        = Column(String)
    error_message = Column(Text)
    changes       = Column(JSON)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ==========================================
# WEBHOOK
# ==========================================


class Webhook(Base):
    __tablename__ = "webhooks"

    id          = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False, index=True)

    webhook_url = Column(String,  nullable=False)
    events      = Column(JSON)
    secret_key  = Column(String)

    is_active      = Column(Boolean, default=True)
    last_triggered = Column(DateTime(timezone=True))
    total_calls    = Column(Integer, default=0)
    failed_calls   = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ==========================================
# SCHEDULED TASK
# ==========================================


class ScheduledTask(Base):
    __tablename__ = "scheduled_tasks"

    id          = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), index=True)

    task_type = Column(String, nullable=False, index=True)
    task_data = Column(JSON)

    schedule_type  = Column(String)
    scheduled_time = Column(DateTime(timezone=True), nullable=False, index=True)
    next_run       = Column(DateTime(timezone=True), index=True)

    is_active   = Column(Boolean, default=True)
    last_run    = Column(DateTime(timezone=True))
    last_status = Column(String)
    run_count   = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())