"""
APScheduler for GMB Posts — Auto-Publisher
Runs every 60 seconds, picks up due scheduled posts for ALL businesses,
publishes via GMB API.
"""

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import GMBPost, Business, PostHistory
from app.services.post_history import update_post_status

logger = logging.getLogger("gmb_scheduler")


async def _cleanup_old_posts():
    """Delete published posts older than 7 days."""
    db: Session = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        deleted = (
            db.query(GMBPost)
            .filter(GMBPost.status == "published", GMBPost.published_date <= cutoff)
            .delete(synchronize_session=False)
        )
        db.commit()
        if deleted:
            logger.info("🗑️  Cleanup: deleted %d published post(s) older than 7 days", deleted)
    except Exception:
        logger.exception("Cleanup job _cleanup_old_posts crashed")
        db.rollback()
    finally:
        db.close()


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
                # Prefer gmb_location_id (GMB API resource path set via Set GMB Location UI),
                # fall back to gmb_url for backwards compat, then post.profile_id
                profile_id = (
                    post.profile_id
                    or (getattr(biz, "gmb_location_id", None) if biz else None)
                    or (getattr(biz, "gmb_url", None) if biz else None)
                )

                if not profile_id:
                    post.status    = "failed"
                    post.error_log = (
                        f"Business id={post.business_id}: "
                        "no GMB location set — go to Businesses and use Set GMB Location"
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
                update_post_status(db, post.id, post.status, post.published_date)

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


async def _sync_businesses_from_gmb():
    """
    Daily job: fetch all locations from Google Business Profile and upsert
    into the businesses table. Creates new businesses automatically when
    locations are added to Google Business Manager.
    """
    db: Session = SessionLocal()
    try:
        from app.services.gmb_publisher import get_access_token, list_accounts
        import requests as _gmb_req

        token    = get_access_token()
        headers  = {"Authorization": f"Bearer {token}"}
        accounts = list_accounts()

        created = updated = 0

        for account in accounts:
            account_name = account.get("name", "")
            page_token   = None

            while True:
                params: dict = {
                    "readMask": "name,title,phoneNumbers,websiteUri,categories,storefrontAddress",
                    "pageSize": 100,
                }
                if page_token:
                    params["pageToken"] = page_token

                resp = _gmb_req.get(
                    f"https://mybusinessbusinessinformation.googleapis.com/v1/{account_name}/locations",
                    headers=headers,
                    params=params,
                    timeout=15,
                )
                resp.raise_for_status()
                data       = resp.json()
                locations  = data.get("locations", [])
                page_token = data.get("nextPageToken")

                for loc in locations:
                    raw_name = loc.get("name", "")
                    loc_name = raw_name if "/" in raw_name and "accounts/" in raw_name else f"{account_name}/{raw_name}"
                    title    = loc.get("title", "Unknown")
                    phone    = (loc.get("phoneNumbers") or {}).get("primaryPhone", "") or ""
                    website  = loc.get("websiteUri", "") or ""
                    addr     = loc.get("storefrontAddress") or {}
                    city     = addr.get("locality", "") or ""
                    state    = addr.get("administrativeArea", "") or ""
                    cats     = loc.get("categories") or {}
                    category = (cats.get("primaryCategory") or {}).get("displayName", "") or ""

                    from app.models import Business
                    existing = (
                        db.query(Business).filter(Business.gmb_location_id == loc_name).first()
                        or db.query(Business).filter(Business.google_place_id == loc_name).first()
                        or db.query(Business).filter(
                            (Business.business_name == title) | (Business.name == title)
                        ).first()
                    )

                    if existing:
                        changed = False
                        if not getattr(existing, "gmb_location_id", None):
                            existing.gmb_location_id = loc_name
                            changed = True
                        if not existing.google_place_id:
                            existing.google_place_id = loc_name
                            changed = True
                        if changed:
                            updated += 1
                    else:
                        new_biz = Business(
                            name            = title,
                            business_name   = title,
                            phone           = phone or "N/A",
                            phone_number    = phone or "N/A",
                            website         = website,
                            city            = city,
                            state           = state,
                            category        = category,
                            gmb_location_id = loc_name,
                            google_place_id = loc_name,
                            status          = "active",
                        )
                        db.add(new_biz)
                        created += 1

                if not page_token:
                    break

        db.commit()
        if created or updated:
            logger.info("🏢 GMB business sync: %d created, %d updated", created, updated)
        else:
            logger.debug("GMB business sync: no changes")
    except Exception:
        logger.exception("GMB business sync job crashed")
        db.rollback()
    finally:
        db.close()


async def _cleanup_post_history():
    """On or after the 10th of each month, delete previous month's post history entries."""
    now = datetime.now(timezone.utc)
    if now.day < 10:
        return  # wait until the 10th grace period has passed

    # Compute previous month/year
    if now.month == 1:
        prev_month, prev_year = 12, now.year - 1
    else:
        prev_month, prev_year = now.month - 1, now.year

    db: Session = SessionLocal()
    try:
        deleted = (
            db.query(PostHistory)
            .filter(PostHistory.year == prev_year, PostHistory.month == prev_month)
            .delete(synchronize_session=False)
        )
        db.commit()
        if deleted:
            logger.info("📋 History cleanup: deleted %d entries for %d/%d", deleted, prev_month, prev_year)
    except Exception:
        logger.exception("History cleanup job crashed")
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
            self.scheduler.add_job(
                _cleanup_old_posts,
                trigger="interval",
                hours=24,
                id="gmb_post_cleanup",
                replace_existing=True,
                max_instances=1,
            )
            self.scheduler.add_job(
                _cleanup_post_history,
                trigger="interval",
                hours=24,
                id="gmb_history_cleanup",
                replace_existing=True,
                max_instances=1,
            )
            self.scheduler.add_job(
                _sync_businesses_from_gmb,
                trigger="interval",
                hours=24,
                id="gmb_business_sync",
                replace_existing=True,
                max_instances=1,
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