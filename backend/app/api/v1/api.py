from fastapi import APIRouter
from app.api.v1 import auth, orgs, projects, queues, jobs, workers, metrics

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(orgs.router, prefix="/orgs", tags=["Organizations"])
api_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_router.include_router(queues.router, tags=["Queues"])
api_router.include_router(jobs.router, tags=["Jobs"])
api_router.include_router(workers.router, prefix="/workers", tags=["Workers"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["Metrics"])
