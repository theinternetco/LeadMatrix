from dotenv import load_dotenv
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# ─── Load .env ────────────────────────────────────────────────────────────────
for _candidate in [
    os.path.join(os.path.dirname(__file__), ".env"),
    os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
]:
    if os.path.exists(_candidate):
        load_dotenv(_candidate)
        break

# ─── Database URL ─────────────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./gmb_dashboard.db"
    logger.warning("⚠️ DATABASE_URL not set — falling back to SQLite: %s", DATABASE_URL)
    print(f"⚠️ DATABASE_URL not found in .env, using SQLite: {DATABASE_URL}")
else:
    _safe = DATABASE_URL.split("@")[-1]
    logger.info("✅ Database: %s", _safe)
    print(f"✅ Connected to database: ...@{_safe}")

# ─── Engine ───────────────────────────────────────────────────────────────────
_IS_SQLITE = DATABASE_URL.startswith("sqlite")
_IS_POSTGRES = DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres")

if _IS_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
elif _IS_POSTGRES:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=1800,
        connect_args={
            "connect_timeout": 10,
            "application_name": "leadmatrix",
            "options": "-c statement_timeout=30000",
        },
        echo=False,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False,
    )

# ─── Session factory ──────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()

# ─── FastAPI dependency ───────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# ─── Safe sub-query helper ────────────────────────────────────────────────────
def safe_query(db, fn, label: str = "query"):
    try:
        return fn()
    except Exception as exc:
        db.rollback()
        logger.warning("⚠️ %s query failed: %s", label, exc)
        return None

# ─── Init helpers ─────────────────────────────────────────────────────────────
def init_db():
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables verified/created")
    print("✅ Database tables verified/created")

def check_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful!")
        print("✅ Database connection successful!")
        return True
    except Exception as exc:
        logger.error("❌ Database connection failed: %s", exc)
        print(f"❌ Database connection failed: {exc}")
        return False

def run_migrations():
    """
    Apply any missing columns added to models after initial table creation.
    Safe to run on every startup — uses IF NOT EXISTS, ignores already-exists errors.

    ✅ v5.1: Added gmb_posts ai_generated / ai_topic / content_angle
             Added support for new 'pending' status in gmb_posts
    ✅ v5.0: Added reviews.updated_at
             Added gmb_performance platform breakdown columns
             Added gmb_performance profile_interactions_total column
             Added gmb_performance search_keywords_json column
             Added gmb_performance views_search / views_maps columns
    ✅ v4.6: gmb_posts status column type fix + views/clicks/cta_type columns
    ✅ v4.5: Fixed gmb_insights table name
    ✅ v4.4: Full gmb_posts column sync
    ✅ v4.3: Added gmb_insights.conversations + gmb_insights.bookings
    """
    if not _IS_POSTGRES:
        return  # SQLite uses CREATE TABLE IF NOT EXISTS — no ALTER needed

    migrations = [
        # ── businesses ───────────────────────────────────────────────────────
        "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS business_name VARCHAR(255)",
        "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50)",
        "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS city VARCHAR(100)",
        "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS state VARCHAR(100)",
        "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS gmb_url TEXT",
        "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS google_place_id VARCHAR(255)",
        "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS category VARCHAR(255)",
        "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS website TEXT",
        "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS location TEXT",
        "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active'",

        # ── reviews ──────────────────────────────────────────────────────────
        "ALTER TABLE reviews ADD COLUMN IF NOT EXISTS google_review_id VARCHAR(255)",
        "ALTER TABLE reviews ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()",

        # ── gmb_posts — full sync + AI fields ────────────────────────────────
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS post_type VARCHAR(50) DEFAULT 'update'",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS title VARCHAR(500)",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS content TEXT",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS media_url TEXT",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS cta_type VARCHAR(50)",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS cta_value TEXT",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS cta_url TEXT",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS profile_id TEXT",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS description TEXT",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS scheduled_date TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS published_date TIMESTAMP WITH TIME ZONE",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS error_log TEXT",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS google_post_id TEXT",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS views INTEGER DEFAULT 0",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS clicks INTEGER DEFAULT 0",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS ai_generated BOOLEAN DEFAULT FALSE",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS ai_topic VARCHAR(300)",
        "ALTER TABLE gmb_posts ADD COLUMN IF NOT EXISTS content_angle VARCHAR(100)",
        "ALTER TABLE gmb_posts ALTER COLUMN status TYPE VARCHAR(50)",

        # ── gmb_insights ──────────────────────────────────────────────────────
        "ALTER TABLE gmb_insights ADD COLUMN IF NOT EXISTS conversations INTEGER DEFAULT 0",
        "ALTER TABLE gmb_insights ADD COLUMN IF NOT EXISTS bookings INTEGER DEFAULT 0",
        "ALTER TABLE gmb_insights ADD COLUMN IF NOT EXISTS profile_interactions INTEGER DEFAULT 0",
        "ALTER TABLE gmb_insights ADD COLUMN IF NOT EXISTS google_search_mobile INTEGER DEFAULT 0",
        "ALTER TABLE gmb_insights ADD COLUMN IF NOT EXISTS google_search_desktop INTEGER DEFAULT 0",
        "ALTER TABLE gmb_insights ADD COLUMN IF NOT EXISTS google_maps_mobile INTEGER DEFAULT 0",
        "ALTER TABLE gmb_insights ADD COLUMN IF NOT EXISTS google_maps_desktop INTEGER DEFAULT 0",
        "ALTER TABLE gmb_insights ADD COLUMN IF NOT EXISTS search_views INTEGER DEFAULT 0",
        "ALTER TABLE gmb_insights ADD COLUMN IF NOT EXISTS maps_views INTEGER DEFAULT 0",
        "ALTER TABLE gmb_insights ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",

        # ── gmb_performance ───────────────────────────────────────────────────
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS actions_bookings INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS actions_messages INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS actions_food_orders INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS photo_views_owner INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS photo_views_customer INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS photo_count_new INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS reviews_replied_count INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS reviews_pending_count INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS posts_total_views INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS posts_total_clicks INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS posts_published INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS change_interactions FLOAT",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS change_searches FLOAT",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS change_actions FLOAT",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS competitor_comparison JSONB",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS market_position_score FLOAT",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS is_estimated BOOLEAN DEFAULT FALSE",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS notes TEXT",

        # ── gmb_performance accurate analytics ────────────────────────────────
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS profile_interactions_total INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS views_search INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS views_maps INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS views_search_mobile INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS views_search_desktop INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS views_maps_mobile INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS views_maps_desktop INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS photo_views_total INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS reviews_total_count INTEGER DEFAULT 0",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS reviews_average_rating FLOAT",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS search_keywords_json JSONB",
        "ALTER TABLE gmb_performance ADD COLUMN IF NOT EXISTS data_source VARCHAR(50) DEFAULT 'gmb_api'",
    ]

    backfill = [
        "UPDATE reviews SET updated_at = created_at WHERE updated_at IS NULL",
        "UPDATE gmb_posts SET ai_generated = FALSE WHERE ai_generated IS NULL",
    ]

    ok = err = 0
    with engine.connect() as conn:
        # If gmb_posts.status is a PostgreSQL ENUM, add pending safely
        try:
            conn.execute(text("ALTER TYPE post_status ADD VALUE IF NOT EXISTS 'pending'"))
            conn.commit()
            logger.info("✅ Added 'pending' to post_status enum (if enum exists)")
        except Exception as exc:
            conn.rollback()
            logger.info("Skipping enum status migration (likely VARCHAR status): %s", exc)

        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
                ok += 1
            except Exception as exc:
                conn.rollback()
                msg = str(exc).lower()
                if "already exists" not in msg:
                    logger.warning("Migration warning: %s | SQL: %s", exc, sql)
                err += 1

        for sql in backfill:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception as exc:
                conn.rollback()
                logger.warning("Backfill warning: %s | SQL: %s", exc, sql)

    print(f"✅ Migrations v5.1: {ok} applied, {err} skipped/already-exists")
    logger.info("Migrations: %d applied, %d skipped", ok, err)