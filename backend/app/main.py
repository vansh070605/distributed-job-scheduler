import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from app.core.config import settings
from app.core.logging import logger
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.middleware.logging import RequestLoggingMiddleware
from app.api.v1.api import api_router
from app.monitoring import health

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logger middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(health.router, prefix="/monitoring", tags=["Monitoring"])


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Distributed Job Scheduler API...")
    
    # Database seeding: ensure first superuser exists
    async with AsyncSessionLocal() as session:
        try:
            query = select(User).where(User.email == settings.FIRST_SUPERUSER)
            result = await session.execute(query)
            admin = result.scalar_one_or_none()
            
            if not admin:
                logger.info(f"Creating default superuser {settings.FIRST_SUPERUSER}")
                admin_user = User(
                    email=settings.FIRST_SUPERUSER,
                    hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                    full_name="System Administrator",
                    role="admin",
                    is_active=True
                )
                session.add(admin_user)
                await session.commit()
            else:
                logger.info("Default superuser already exists.")
        except Exception as e:
            logger.error(f"Error seeding default admin user: {str(e)}")
            await session.rollback()
