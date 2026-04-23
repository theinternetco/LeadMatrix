"""
APScheduler for GMB Posts — Auto-Publisher
Runs every 60 seconds, picks up due scheduled posts for ALL businesses,
publishes via GMB API.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import GMBPost, Business

logger = logging.getLogger("gmb_scheduler")


async def _process_due_posts():
    """
    Core job: fetch ALL posts where status='scheduled' AND scheduled_date <= NOW
    across ALL businesses, then publish each one via GMB API.
    """
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        due_posts = (
            db.query(GMBPost)
            .filter(
                GMBPost.status == "scheduled",
                GMBPost.scheduled_date <= now,
            )
            .order_by(GMBPost.scheduled_date.asc())  # oldest due first
            .all()
        )

        if not due_posts:
            return  # nothing to do — silent exit

        logger.info("🕐 Scheduler: %d post(s) due across all businesses", len(due_posts))

        # Group by business for cleaner logging
        business_cache: dict[int, Business] = {}

        published_count = 0
        failed_count = 0

        for post in due_posts:
            try:
                # --- Resolve Business (cached) ---
                if post.business_id not in business_cache:
                    biz = db.query(Business).filter(Business.id == post.business_id).first()
                    business_cache[post.business_id] = biz
                else:
                    biz = business_cache[post.business_id]

                # --- Resolve profile_id ---
                profile_id = post.profile_id or (biz.gmb_url if biz else None)

                if not profile_id:
                    post.status    = "failed"
                    post.error_log = (
                        f"Business id={post.business_id}: "
                        "no profile_id or gmb_url configured"
                    )
                    post.retry_count = (post.retry_count or 0) + 1
                    db.commit()
                    failed_count += 1
                    logger.error(
                        "Post id=%s (biz=%s) failed: no profile_id",
                        post.id, post.business_id,
                    )
                    continue

                # Skip if business is inactive
                if biz and getattr(biz, "status", "active") != "active":
                    post.status    = "failed"
                    post.error_log = f"Business id={post.business_id} is not active"
                    db.commit()
                    failed_count += 1
                    logger.warning(
                        "Post id=%s skipped: business id=%s is inactive",
                        post.id, post.business_id,
                    )
                    continue

                # --- Lazy import to avoid circular imports ---
                from app.services.gmb_publisher import publish_post_to_gmb

                result = publish_post_to_gmb(post, profile_id=profile_id)

                if result["success"]:
                    post.status         = "published"
                    post.published_date = datetime.now(timezone.utc)
                    post.error_log      = None
                    gmb_resp            = result.get("gmb_response") or {}
                    post.google_post_id = gmb_resp.get("name") or gmb_resp.get("id")
                    published_count += 1
                    logger.info(
                        "✅ Post id=%s (biz=%s) → published (profile=%s)",
                        post.id, post.business_id, profile_id,
                    )
                else:
                    post.status      = "failed"
                    post.error_log   = result.get("error", "Unknown error from GMB API")
                    post.retry_count = (post.retry_count or 0) + 1
                    failed_count += 1
                    logger.error(
                        "❌ Post id=%s (biz=%s) → failed: %s",
                        post.id, post.business_id, post.error_log,
                    )

                db.commit()

            except Exception as e:
                logger.exception("Exception processing post id=%s (biz=%s)", post.id, post.business_id)
                post.status      = "failed"
                post.error_log   = str(e)
                post.retry_count = (post.retry_count or 0) + 1
                failed_count += 1
                try:
                    db.commit()
                except Exception:
                    db.rollback()

        logger.info(
            "📊 Scheduler run complete — published: %d, failed: %d, total: %d",
            published_count, failed_count, len(due_posts),
        )

    except Exception:
        logger.exception("Scheduler job _process_due_posts crashed")
        db.rollback()
    finally:
        db.close()


class GMBScheduler:
    def __init__(self):
        self.scheduler  = AsyncIOScheduler()
        self.is_running = False

    def start(self):
        """Start scheduler and register the GMB auto-publish job."""
        if not self.scheduler.running:
            self.scheduler.add_job(
                _process_due_posts,
                trigger="interval",
                seconds=60,
                id="gmb_auto_publisher",
                replace_existing=True,
                max_instances=1,        # never overlap — one run at a time
                misfire_grace_time=30,  # if missed by <30s, still execute
            )
            self.scheduler.start()
            self.is_running = True
            print("✅ GMB Scheduler started — checking every 60 seconds (all businesses)")
        else:
            print("⚠️  Scheduler already running")

    def stop(self):
        """Gracefully stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            print("🛑 GMB Scheduler stopped")

    def trigger_now(self):
        """Manually fire the job immediately (for testing/admin)."""
        job = self.scheduler.get_job("gmb_auto_publisher")
        if job:
            job.modify(next_run_time=datetime.now(timezone.utc))
            print("⚡ Scheduler manually triggered")
        else:
            print("⚠️  Job not found — is scheduler running?")

    def get_status(self) -> dict:
        """Return scheduler status for health check endpoint."""
        job = self.scheduler.get_job("gmb_auto_publisher")
        return {
            "running":  self.is_running,
            "next_run": str(job.next_run_time) if job else None,
            "job_id":   "gmb_auto_publisher",
        }


# ── Singleton instance ────────────────────────────────────────────────────────
scheduler = GMBScheduler()