from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ApiKey

async def get_api_key(request: Request, db: Session = None):
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required")

    if db is None:
        # In FastAPI Depends will handle db session injection
        async for _db in get_db():
            db = _db

    api_key_obj = db.query(ApiKey).filter(ApiKey.key == api_key).first()
    if not api_key_obj:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    return api_key_obj
