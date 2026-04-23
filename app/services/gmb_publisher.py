"""
app/services/gmb_publisher.py
Google My Business Post Publisher -- OAuth2 (Production)
Uses the official Google My Business API v4.9

UPDATED: Reuses existing GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET from .env
         -- no separate oauth_client.json file required.
         Falls back to oauth_client.json file if env vars not set.
✅ v2.5: Increased timeout (10s connect, 45s read)
         Retry logic with exponential backoff (3 retries)
         Proper ReadTimeout / ConnectionError handling
         base64 media_url stripped before sending to GMB (must be public URL)
         CALL CTA no longer requires a URL
         Token save uses json.dump pattern
✅ v2.6: Auto-proxy localhost/private URLs via imgbb (free CDN)
         _resolve_media_url() — single function handles all 4 cases
         _is_local_url() — detects localhost / private IPs
         _upload_to_imgbb() — downloads local image, re-uploads to imgbb
         IMGBB_API_KEY env var support (free key: https://api.imgbb.com/)
         Detailed image debug logging at every step
         Backward-compat: _safe_media_url() kept as alias
✅ v2.7: Fixed credential paths — now always relative to THIS file (__file__)
         so uvicorn can be run from any working directory without triggering
         re-auth. No more OAuth prompt when token.json already exists.
✅ v2.8: token.json kept in PROJECT ROOT (E:\LEADMATRIX-API-BACKUP\)
         _THIS_DIR goes up 2 levels from app/services/ to project root.
         _get_oauth_credentials() now tries refresh on ANY invalid token
         (not just expired) — prevents re-auth when token is valid but
         creds.valid=False due to missing expiry field.
         Auto-refresh in get_access_token() always saves updated token back.
"""

__version__ = "2.8.0"

import os
import json
import logging
import base64
from datetime import datetime
from typing import Optional


logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# OPTIONAL IMPORTS -- graceful fallback if libs not installed
# ─────────────────────────────────────────────────────────────
try:
    from google.oauth2.credentials import Credentials
    from google.oauth2 import service_account
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import googleapiclient.discovery
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False
    logger.warning(
        "[WARN] Google API libs not installed. "
        "Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
    )


try:
    import requests as _requests_lib
    from requests.adapters import HTTPAdapter
    from requests.exceptions import ReadTimeout, ConnectionError as RequestsConnectionError
    from urllib3.util.retry import Retry
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# ─────────────────────────────────────────────────────────────
# ✅ ROBUST SESSION WITH RETRY + INCREASED TIMEOUT
# ─────────────────────────────────────────────────────────────
GMB_CONNECT_TIMEOUT = 10
GMB_READ_TIMEOUT    = 45


def _build_session():
    session = _requests_lib.Session()
    retry = Retry(
        total            = 3,
        backoff_factor   = 2,
        status_forcelist = [429, 500, 502, 503, 504],
        allowed_methods  = ["GET", "POST", "PATCH", "DELETE"],
        raise_on_status  = False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://",  adapter)
    return session


_requests = _build_session() if REQUESTS_AVAILABLE else None


# ─────────────────────────────────────────────────────────────
# SCOPES
# ─────────────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/business.manage"]


# ─────────────────────────────────────────────────────────────
# GMB API ENDPOINTS
# ─────────────────────────────────────────────────────────────
GMB_ACCOUNT_BASE = "https://mybusinessaccountmanagement.googleapis.com/v1"
GMB_INFO_BASE    = "https://mybusinessbusinessinformation.googleapis.com/v1"
GMB_POSTS_BASE   = "https://mybusiness.googleapis.com/v4"


# ─────────────────────────────────────────────────────────────
# ✅ v2.8 FIX: CREDENTIAL PATHS — always point to PROJECT ROOT
# app/services/gmb_publisher.py → up 2 levels → project root
# token.json lives at:  E:\LEADMATRIX-API-BACKUP\token.json
# Override via .env vars if needed.
# ─────────────────────────────────────────────────────────────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))   # app/services/
_ROOT_DIR = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))  # project root

def _resolve_path(env_var: str, default_filename: str) -> str:
    """
    Resolve a credential file path.
    If the env var is set but is not absolute, treat it as relative to _ROOT_DIR.
    Falls back to _ROOT_DIR/<default_filename>.
    """
    raw = os.getenv(env_var, "")
    if not raw:
        return os.path.join(_ROOT_DIR, default_filename)
    if os.path.isabs(raw):
        return raw
    return os.path.join(_ROOT_DIR, raw)

OAUTH_CLIENT_FILE    = _resolve_path("GOOGLE_OAUTH_CLIENT_FILE", "oauth_client.json")
OAUTH_TOKEN_FILE     = _resolve_path("GOOGLE_OAUTH_TOKEN_FILE",  "token.json")
SERVICE_ACCOUNT_FILE = _resolve_path("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
AUTH_MODE = os.getenv("GOOGLE_AUTH_MODE", "oauth")

# Use GMB-specific credentials (Desktop app type).
# Do NOT fall back to GOOGLE_CLIENT_ID/SECRET — those are the GSC Web Application
# client and will cause redirect_uri_mismatch when used with InstalledAppFlow.
_GOOGLE_CLIENT_ID     = os.getenv("GMB_CLIENT_ID")
_GOOGLE_CLIENT_SECRET = os.getenv("GMB_CLIENT_SECRET")


# ─────────────────────────────────────────────────────────────
# IMGBB CONFIG
# Free public image hosting for local dev / no-CDN setups.
# Get free API key at: https://api.imgbb.com/
# Set IMGBB_API_KEY in your .env to enable auto-proxy of localhost URLs
# ─────────────────────────────────────────────────────────────
IMGBB_API_KEY    = os.getenv("IMGBB_API_KEY", "")
IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"

MEDIA_BASE_URL = os.getenv("MEDIA_BASE_URL", "http://localhost:8000")

_LOCAL_URL_PATTERNS = (
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "192.168.",
    "10.",
    "172.16.",
    "::1",
)

# Print version + resolved token path on import for easy debugging
print(
    f"[OK] GMB Publisher v{__version__} LOADED | "
    f"imgbb proxy: {'ENABLED' if IMGBB_API_KEY else 'NO KEY SET'}"
)
print(f"[OK] GMB Token path: {OAUTH_TOKEN_FILE}")
print(f"[OK] GMB Token exists: {os.path.exists(OAUTH_TOKEN_FILE)}")


def _build_client_config() -> dict | None:
    if _GOOGLE_CLIENT_ID and _GOOGLE_CLIENT_SECRET:
        return {
            "installed": {
                "client_id":                   _GOOGLE_CLIENT_ID,
                "client_secret":               _GOOGLE_CLIENT_SECRET,
                "redirect_uris":               ["http://localhost", "urn:ietf:wg:oauth:2.0:oob"],
                "auth_uri":                    "https://accounts.google.com/o/oauth2/auth",
                "token_uri":                   "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            }
        }
    return None


# ─────────────────────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────────────────────

def _get_oauth_credentials() -> Optional["Credentials"]:
    if not GOOGLE_LIBS_AVAILABLE:
        raise RuntimeError("Google API libraries not installed.")

    creds = None

    if os.path.exists(OAUTH_TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(OAUTH_TOKEN_FILE, SCOPES)
            logger.info(f"[Auth] Token loaded from: {OAUTH_TOKEN_FILE}")
        except Exception as e:
            logger.warning(f"[Auth] Failed to load token file: {e}")

    # ✅ v2.8: Try refresh on ANY invalid state (expired OR creds.valid=False)
    # This prevents re-auth when token exists but is stale/missing expiry field
    if creds and not creds.valid and creds.refresh_token:
        try:
            logger.info("[Auth] Token not valid — attempting silent refresh...")
            creds.refresh(Request())
            _save_token(creds)
            logger.info("[Auth] OAuth2 token refreshed successfully.")
            return creds
        except Exception as e:
            logger.error(f"[Auth] Token refresh failed: {e}")
            creds = None

    if creds and creds.valid:
        return creds

    # No valid token — trigger OAuth flow
    if not creds:
        client_config = _build_client_config()

        if client_config:
            logger.info("[Auth] Using GOOGLE_CLIENT_ID/SECRET from .env for GMB OAuth.")
            flow  = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
            _save_token(creds)
            logger.info("[Auth] New OAuth2 token obtained from .env credentials and saved.")

        elif os.path.exists(OAUTH_CLIENT_FILE):
            logger.info(f"[Auth] Using oauth_client.json file: {OAUTH_CLIENT_FILE}")
            flow  = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
            _save_token(creds)
            logger.info("[Auth] New OAuth2 token obtained from file and saved.")

        else:
            raise FileNotFoundError(
                "No OAuth2 credentials found for GMB Publisher. Fix one of these:\n"
                "  Option A (easiest): Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env\n"
                f"  Option B: Place oauth_client.json at {OAUTH_CLIENT_FILE}\n"
                "  Download from: Google Cloud Console -> APIs & Services -> Credentials -> OAuth 2.0 Client IDs"
            )

    return creds


def _get_service_account_credentials() -> Optional["service_account.Credentials"]:
    if not GOOGLE_LIBS_AVAILABLE:
        raise RuntimeError("Google API libraries not installed.")
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        raise FileNotFoundError(
            f"Service account file not found: {SERVICE_ACCOUNT_FILE}\n"
            "Download from Google Cloud Console -> IAM -> Service Accounts -> Keys"
        )
    return service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )


def _save_token(creds: "Credentials"):
    token_dir = os.path.dirname(OAUTH_TOKEN_FILE)
    if token_dir:
        os.makedirs(token_dir, exist_ok=True)

    token_data = {
        "token":         creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri":     creds.token_uri,
        "client_id":     creds.client_id,
        "client_secret": creds.client_secret,
        "scopes":        list(creds.scopes) if creds.scopes else [],
    }
    with open(OAUTH_TOKEN_FILE, "w") as f:
        json.dump(token_data, f, indent=2)

    logger.info(f"[Auth] Token saved to: {OAUTH_TOKEN_FILE}")


def get_credentials():
    if AUTH_MODE == "service_account":
        return _get_service_account_credentials()
    return _get_oauth_credentials()


def get_access_token() -> str:
    """Get a valid access token, refreshing silently if needed."""
    creds = get_credentials()
    if not creds.valid or creds.expired:
        try:
            creds.refresh(Request())
            _save_token(creds)
            logger.info("[Auth] Access token refreshed in get_access_token().")
        except Exception as e:
            logger.error(f"[Auth] Failed to refresh in get_access_token(): {e}")
            raise
    return creds.token


# ─────────────────────────────────────────────────────────────
# ACCOUNT / LOCATION HELPERS
# ─────────────────────────────────────────────────────────────

def list_accounts() -> list[dict]:
    token = get_access_token()
    try:
        resp = _requests.get(
            f"{GMB_ACCOUNT_BASE}/accounts",
            headers={"Authorization": f"Bearer {token}"},
            timeout=(GMB_CONNECT_TIMEOUT, GMB_READ_TIMEOUT),
        )
        resp.raise_for_status()
        return resp.json().get("accounts", [])
    except ReadTimeout:
        logger.error("[GMBPublisher] Timeout fetching accounts")
        raise
    except RequestsConnectionError as e:
        logger.error(f"[GMBPublisher] Connection error fetching accounts: {e}")
        raise


def list_locations(account_name: str) -> list[dict]:
    token = get_access_token()
    try:
        resp = _requests.get(
            f"{GMB_INFO_BASE}/{account_name}/locations",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "readMask": "name,title,storefrontAddress,websiteUri",
                "pageSize": 100,
            },
            timeout=(GMB_CONNECT_TIMEOUT, GMB_READ_TIMEOUT),
        )
        resp.raise_for_status()
    except ReadTimeout:
        logger.error("[GMBPublisher] Timeout fetching locations")
        raise
    except RequestsConnectionError as e:
        logger.error(f"[GMBPublisher] Connection error fetching locations: {e}")
        raise

    locs = resp.json().get("locations", [])

    for loc in locs:
        if loc.get("name", "").startswith("locations/"):
            loc["name"] = f"{account_name}/{loc['name']}"

    return locs


def get_first_location() -> Optional[str]:
    try:
        accounts = list_accounts()
        if not accounts:
            return None
        locations = list_locations(accounts[0]["name"])
        if not locations:
            return None
        return locations[0]["name"]
    except Exception as e:
        logger.error(f"[GMB] Failed to fetch first location: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# MEDIA URL HELPERS  (v2.6)
# ─────────────────────────────────────────────────────────────

def _is_local_url(url: str) -> bool:
    """Return True if the URL points to a local/private network address."""
    if not url:
        return False
    for pattern in _LOCAL_URL_PATTERNS:
        if pattern in url:
            return True
    return False


def _upload_to_imgbb(image_url: str) -> Optional[str]:
    """
    Download image from a local URL and re-upload to imgbb (free CDN).
    Returns the public imgbb URL, or None if upload fails.
    Requires IMGBB_API_KEY in .env — free key at https://api.imgbb.com/
    """
    if not IMGBB_API_KEY:
        logger.warning(
            "[GMBPublisher] ⚠️  media_url is a localhost URL — Google cannot reach it.\n"
            "  Fix: Add IMGBB_API_KEY=your_key to .env (free at https://api.imgbb.com/)\n"
            "  Post will publish WITHOUT the image until key is set."
        )
        return None

    try:
        logger.info(f"[GMBPublisher] 🔄 Proxying local image via imgbb: {image_url}")

        img_resp = _requests_lib.get(image_url, timeout=15)
        img_resp.raise_for_status()

        img_b64 = base64.b64encode(img_resp.content).decode("utf-8")

        upload_resp = _requests_lib.post(
            IMGBB_UPLOAD_URL,
            data={
                "key":        IMGBB_API_KEY,
                "image":      img_b64,
                "expiration": 2592000,  # 30 days
            },
            timeout=30,
        )
        upload_resp.raise_for_status()
        result = upload_resp.json()

        public_url = result["data"]["url"]
        logger.info(f"[GMBPublisher] ✅ imgbb upload success → {public_url}")
        return public_url

    except Exception as e:
        logger.error(f"[GMBPublisher] ❌ imgbb upload failed: {e}")
        return None


def _resolve_media_url(media_url: str | None) -> str | None:
    """
    Resolve a media_url to a publicly accessible URL that Google can fetch.

    Rules:
      1. None / empty           → None (no image)
      2. base64 data URI        → None (GMB never supports base64)
      3. localhost / private IP → try imgbb proxy; None if no key
      4. non-http string        → None
      5. public https:// URL    → return as-is ✅
    """
    if not media_url:
        return None

    # Rule 2: base64
    if media_url.startswith("data:image/"):
        logger.warning(
            "[GMBPublisher] ⚠️  media_url is a base64 data URI — not supported by GMB API.\n"
            "  Fix: Call POST /api/media/upload first to get a public URL."
        )
        return None

    # Rule 3: localhost / private
    if _is_local_url(media_url):
        logger.warning(
            f"[GMBPublisher] ⚠️  media_url is local/private: {media_url}\n"
            "  Google's servers cannot reach localhost. Options:\n"
            "  A) IMGBB_API_KEY in .env → auto-proxy (free: https://api.imgbb.com/)\n"
            "  B) Deploy backend → set MEDIA_BASE_URL=https://yourdomain.com in .env\n"
            "  C) Paste a public CDN URL directly in the media field"
        )
        proxied = _upload_to_imgbb(media_url)
        if proxied:
            logger.info(f"[GMBPublisher] 🔀 Rewrote local → public: {proxied}")
            return proxied
        logger.warning("[GMBPublisher] 🚫 Image skipped — post will publish without image")
        return None

    # Rule 4: non-http
    if not media_url.startswith("http"):
        logger.warning(f"[GMBPublisher] ⚠️  Invalid URL, skipping: {media_url[:80]}")
        return None

    # Rule 5: valid public URL
    logger.info(f"[GMBPublisher] 🖼️  Media URL OK (public): {media_url}")
    return media_url


# Backward compat alias
def _safe_media_url(media_url: str | None) -> str | None:
    return _resolve_media_url(media_url)


# ─────────────────────────────────────────────────────────────
# POST BUILDER
# ─────────────────────────────────────────────────────────────

CTA_ACTION_MAP = {
    "BOOK":       "BOOK",
    "ORDER":      "ORDER",
    "SHOP":       "SHOP",
    "LEARN_MORE": "LEARN_MORE",
    "SIGN_UP":    "SIGN_UP",
    "CALL":       "CALL",
    "GET_OFFER":  "GET_OFFER",
}


def _build_post_body(
    summary:        str,
    post_type:      str        = "STANDARD",
    cta_type:       str | None = None,
    cta_url:        str | None = None,
    cta_value:      str | None = None,
    media_url:      str | None = None,
    event_title:    str | None = None,
    event_start:    str | None = None,
    event_end:      str | None = None,
    offer_code:     str | None = None,
    offer_url:      str | None = None,
    offer_terms:    str | None = None,
) -> dict:
    body: dict = {
        "summary":      summary,
        "languageCode": "en",
    }

    # ── Call-To-Action ────────────────────────────────────────
    if cta_type:
        normalized_cta = CTA_ACTION_MAP.get(cta_type.upper(), "LEARN_MORE")
        cta_url_final  = cta_url or cta_value

        if normalized_cta == "CALL":
            body["callToAction"] = {"actionType": "CALL"}
        elif cta_url_final:
            body["callToAction"] = {
                "actionType": normalized_cta,
                "url":        cta_url_final,
            }
        else:
            logger.warning(
                f"[GMBPublisher] cta_type='{cta_type}' dropped — "
                "GMB requires a URL for this CTA type."
            )

    # ── Media ─────────────────────────────────────────────────
    safe_url = _resolve_media_url(media_url)
    if safe_url:
        body["media"] = [{"mediaFormat": "PHOTO", "sourceUrl": safe_url}]
        logger.info(f"[GMBPublisher] 📷 Image attached: {safe_url}")
    elif media_url:
        logger.warning("[GMBPublisher] 🚫 No image attached — see warnings above")

    # ── Topic / Post type ─────────────────────────────────────
    if post_type.upper() == "EVENT" and event_title:
        body["topicType"] = "EVENT"
        body["event"]     = {"title": event_title, "schedule": {}}
        if event_start:
            body["event"]["schedule"]["startDate"] = _date_str_to_gmb(event_start)
            body["event"]["schedule"]["startTime"] = {"hours": 0, "minutes": 0}
        if event_end:
            body["event"]["schedule"]["endDate"] = _date_str_to_gmb(event_end)
            body["event"]["schedule"]["endTime"] = {"hours": 23, "minutes": 59}

    elif post_type.upper() == "OFFER":
        body["topicType"] = "OFFER"
        body["offer"]     = {}
        if offer_code:
            body["offer"]["couponCode"] = offer_code
        if offer_url:
            body["offer"]["redeemOnlineUrl"] = offer_url
        if offer_terms:
            body["offer"]["termsConditions"] = offer_terms

    else:
        body["topicType"] = "STANDARD"

    return body


def _date_str_to_gmb(date_str: str) -> dict:
    try:
        d = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        d = datetime.strptime(date_str[:10], "%Y-%m-%d")
    return {"year": d.year, "month": d.month, "day": d.day}


# ─────────────────────────────────────────────────────────────
# MAIN PUBLISH FUNCTION
# ─────────────────────────────────────────────────────────────

def publish_post(
    location_name:  str,
    summary:        str,
    post_type:      str        = "STANDARD",
    cta_type:       str | None = None,
    cta_url:        str | None = None,
    cta_value:      str | None = None,
    media_url:      str | None = None,
    event_title:    str | None = None,
    event_start:    str | None = None,
    event_end:      str | None = None,
    offer_code:     str | None = None,
    offer_url:      str | None = None,
    offer_terms:    str | None = None,
) -> dict:
    if not GOOGLE_LIBS_AVAILABLE or not REQUESTS_AVAILABLE:
        raise RuntimeError(
            "Required libraries not installed. "
            "Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client requests"
        )

    token     = get_access_token()
    post_body = _build_post_body(
        summary     = summary,
        post_type   = post_type,
        cta_type    = cta_type,
        cta_url     = cta_url,
        cta_value   = cta_value,
        media_url   = media_url,
        event_title = event_title,
        event_start = event_start,
        event_end   = event_end,
        offer_code  = offer_code,
        offer_url   = offer_url,
        offer_terms = offer_terms,
    )

    url = f"{GMB_POSTS_BASE}/{location_name}/localPosts"

    logger.info(f"[GMBPublisher] POST → {url}")
    logger.info(
        f"[GMBPublisher] topicType={post_body.get('topicType')} | "
        f"cta={post_body.get('callToAction')} | "
        f"media={'✅ ' + post_body['media'][0]['sourceUrl'][:60] if post_body.get('media') else '❌ none'}"
    )
    logger.debug(f"[GMBPublisher] Full body: {json.dumps(post_body, indent=2)}")

    try:
        resp = _requests.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            json    = post_body,
            timeout = (GMB_CONNECT_TIMEOUT, GMB_READ_TIMEOUT),
        )
    except ReadTimeout:
        logger.error(
            f"[GMBPublisher] ⏱️  GMB API read timeout after {GMB_READ_TIMEOUT}s "
            "(all 3 retries exhausted). The post was NOT published."
        )
        raise ReadTimeout(
            f"GMB API did not respond within {GMB_READ_TIMEOUT}s after 3 retries. "
            "Retry in a few minutes."
        )
    except RequestsConnectionError as e:
        logger.error(f"[GMBPublisher] 🔌 Connection error to GMB API: {e}")
        raise

    if not resp.ok:
        logger.error(f"[GMBPublisher] API Error {resp.status_code}: {resp.text[:400]}")
        resp.raise_for_status()

    result = resp.json()
    logger.info(f"[GMBPublisher] ✅ Post published: {result.get('name', '?')}")
    return result


# ─────────────────────────────────────────────────────────────
# DELETE / UPDATE
# ─────────────────────────────────────────────────────────────

def delete_post(post_name: str) -> bool:
    if not GOOGLE_LIBS_AVAILABLE or not REQUESTS_AVAILABLE:
        raise RuntimeError("Required libraries not installed.")
    token = get_access_token()
    try:
        resp = _requests.delete(
            f"{GMB_POSTS_BASE}/{post_name}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=(GMB_CONNECT_TIMEOUT, GMB_READ_TIMEOUT),
        )
        resp.raise_for_status()
    except ReadTimeout:
        logger.error("[GMBPublisher] Timeout deleting post")
        raise
    logger.info(f"[GMBPublisher] Post deleted: {post_name}")
    return True


def update_post(post_name: str, summary: str, **kwargs) -> dict:
    if not GOOGLE_LIBS_AVAILABLE or not REQUESTS_AVAILABLE:
        raise RuntimeError("Required libraries not installed.")
    token     = get_access_token()
    post_body = _build_post_body(summary=summary, **kwargs)
    try:
        resp = _requests.patch(
            f"{GMB_POSTS_BASE}/{post_name}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json",
            },
            json   = post_body,
            params = {"updateMask": "summary,callToAction,media,topicType,event,offer"},
            timeout= (GMB_CONNECT_TIMEOUT, GMB_READ_TIMEOUT),
        )
    except ReadTimeout:
        logger.error("[GMBPublisher] Timeout updating post")
        raise
    if not resp.ok:
        logger.error(f"[GMBPublisher] Update error {resp.status_code}: {resp.text[:400]}")
        resp.raise_for_status()
    result = resp.json()
    logger.info(f"[GMBPublisher] Post updated: {result.get('name', '?')}")
    return result


# ─────────────────────────────────────────────────────────────
# ROUTER WRAPPER
# ─────────────────────────────────────────────────────────────

def publish_post_to_gmb(post, profile_id: str | None = None) -> dict:
    """Wrapper called by the router (create_post / trigger_post_now / retry)."""
    try:
        location_name = profile_id or getattr(post, "profile_id", None)

        if not location_name:
            try:
                from app.database import SessionLocal
                from app.models import Business
                db       = SessionLocal()
                business = db.query(Business).filter(Business.id == post.business_id).first()
                db.close()
                if business:
                    location_name = getattr(business, "gmb_url", None)
            except Exception as e:
                logger.warning(f"[GMBPublisher] Could not fetch business for post {post.id}: {e}")

        if not location_name:
            location_name = get_first_location()

        if not location_name:
            return {
                "success":      False,
                "gmb_response": None,
                "error": (
                    "No GMB location_name found. "
                    "Set gmb_url on the business record "
                    "(format: accounts/123/locations/456)."
                ),
            }

        if location_name.startswith("http"):
            logger.warning(
                f"[GMBPublisher] profile_id looks like a URL, not an API path: {location_name}. "
                "Expected format: accounts/ACCOUNT_ID/locations/LOCATION_ID"
            )

        post_type_map = {
            "update": "STANDARD",
            "offer":  "OFFER",
            "event":  "EVENT",
        }
        raw_type = getattr(post, "post_type", "update") or "update"
        gmb_type = post_type_map.get(raw_type.lower(), "STANDARD")

        raw_media = getattr(post, "media_url", None)
        logger.info(
            f"[GMBPublisher] Post #{getattr(post, 'id', '?')} media_url (raw): "
            f"{'None' if not raw_media else raw_media[:80]}"
        )

        result = publish_post(
            location_name = location_name,
            summary       = post.content or "",
            post_type     = gmb_type,
            cta_type      = getattr(post, "cta_type",  None),
            cta_url       = getattr(post, "cta_url",   None),
            cta_value     = getattr(post, "cta_value", None),
            media_url     = raw_media,
            event_title   = getattr(post, "event_title", None),
            event_start   = (str(post.event_start_date) if getattr(post, "event_start_date", None) else None),
            event_end     = (str(post.event_end_date)   if getattr(post, "event_end_date",   None) else None),
            offer_code    = getattr(post, "offer_code",  None),
            offer_url     = getattr(post, "offer_url",   None),
            offer_terms   = getattr(post, "offer_terms", None),
        )

        logger.info(f"[GMBPublisher] Post #{post.id} published → GMB name: {result.get('name', '?')}")
        return {"success": True, "gmb_response": result, "error": None}

    except ReadTimeout:
        err = (
            f"GMB API timed out after {GMB_READ_TIMEOUT}s (3 retries exhausted). "
            "Retry in a few minutes."
        )
        logger.error(f"[GMBPublisher] ⏱️  Post #{getattr(post, 'id', '?')}: {err}")
        return {"success": False, "gmb_response": None, "error": err}

    except RequestsConnectionError as e:
        err = f"Cannot reach mybusiness.googleapis.com: {e}"
        logger.error(f"[GMBPublisher] 🔌 Post #{getattr(post, 'id', '?')}: {err}")
        return {"success": False, "gmb_response": None, "error": err}

    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"[GMBPublisher] Failed post #{getattr(post, 'id', '?')}: {e}\n{tb}")
        return {"success": False, "gmb_response": None, "error": str(e)}


# ─────────────────────────────────────────────────────────────
# SCHEDULER WRAPPER
# ─────────────────────────────────────────────────────────────

def publish_gmb_post(post) -> dict:
    """High-level wrapper called by the scheduler."""
    result = publish_post_to_gmb(post)
    return {
        "success":       result["success"],
        "gmb_post_name": (result.get("gmb_response") or {}).get("name") if result["success"] else None,
        "error":         result.get("error"),
    }
