"""
Helpers for recording and updating PostHistory entries.
Called from gmb_posts router (on schedule/publish) and scheduler (on auto-publish).
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import PostHistory, GMBPost, Business

logger = logging.getLogger("post_history")


def _business_name(db: Session, business_id: int) -> str:
    biz = db.query(Business).filter(Business.id == business_id).first()
    if not biz:
        return f"Business #{business_id}"
    return getattr(biz, "business_name", None) or getattr(biz, "name", None) or f"Business #{business_id}"


def record_post(db: Session, post: GMBPost, business_name: str | None = None) -> None:
    """Insert or update a PostHistory row for the given post."""
    try:
        ref_date = post.scheduled_date or post.published_date or datetime.now(timezone.utc)
        if ref_date.tzinfo is None:
            ref_date = ref_date.replace(tzinfo=timezone.utc)

        biz_name = business_name or _business_name(db, post.business_id)
        status   = post.status.value if hasattr(post.status, "value") else (post.status or "scheduled")

        existing = db.query(PostHistory).filter(PostHistory.post_id == post.id).first()
        if existing:
            existing.status         = status
            existing.published_date = post.published_date
            existing.title          = post.title
            existing.content        = post.content
            existing.media_url      = post.media_url
        else:
            db.add(PostHistory(
                post_id        = post.id,
                business_id    = post.business_id,
                business_name  = biz_name,
                title          = post.title,
                content        = post.content,
                media_url      = post.media_url,
                post_type      = post.post_type,
                status         = status,
                scheduled_date = post.scheduled_date,
                published_date = post.published_date,
                month          = ref_date.month,
                year           = ref_date.year,
            ))
        db.commit()
    except Exception:
        logger.exception("Failed to record post history for post id=%s", post.id)
        db.rollback()


def update_post_status(db: Session, post_id: int, status: str, published_date: datetime | None = None) -> None:
    """Update status (and optionally published_date) on an existing history row."""
    try:
        row = db.query(PostHistory).filter(PostHistory.post_id == post_id).first()
        if row:
            row.status = status
            if published_date:
                row.published_date = published_date
            db.commit()
    except Exception:
        logger.exception("Failed to update post history status for post id=%s", post_id)
        db.rollback()
