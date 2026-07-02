from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.api import deps
import redis.asyncio as aioredis
from app.core.config import settings

router = APIRouter()


@router.get("/liveness", status_code=status.HTTP_200_OK)
async def liveness():
    """Liveness check to verify the app container is up."""
    return {"status": "ok"}


@router.get("/readiness", status_code=status.HTTP_200_OK)
async def readiness(db: AsyncSession = Depends(deps.get_db)):
    """Readiness check to verify DB and Redis are fully reachable."""
    # Check DB
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not ready: {str(e)}"
        )

    # Check Redis
    try:
        client = aioredis.from_url(settings.REDIS_URL)
        await client.ping()
        await client.close()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis not ready: {str(e)}"
        )

    return {"status": "ready"}


@router.get("/health", status_code=status.HTTP_200_OK)
async def health(db: AsyncSession = Depends(deps.get_db)):
    """Detailed health check for all components."""
    db_ok = True
    db_error = None
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_ok = False
        db_error = str(e)

    redis_ok = True
    redis_error = None
    try:
        client = aioredis.from_url(settings.REDIS_URL)
        await client.ping()
        await client.close()
    except Exception as e:
        redis_ok = False
        redis_error = str(e)

    if not db_ok or not redis_ok:
        return {
            "status": "unhealthy",
            "database": "ok" if db_ok else f"failed: {db_error}",
            "redis": "ok" if redis_ok else f"failed: {redis_error}"
        }

    return {
        "status": "healthy",
        "database": "ok",
        "redis": "ok"
    }
