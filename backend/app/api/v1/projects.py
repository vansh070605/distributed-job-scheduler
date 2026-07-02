from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.repositories import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectResponse
from app.models.project import Project
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_in: ProjectCreate,
    org_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["admin", "manager"]))
):
    project_repo = ProjectRepository(db)
    existing_project = await project_repo.get_by_slug(org_id, project_in.slug)
    if existing_project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project with this slug already exists in this organization",
        )
    
    project = Project(
        name=project_in.name,
        slug=project_in.slug,
        org_id=org_id
    )
    return await project_repo.create(project)


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    org_id: str,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    project_repo = ProjectRepository(db)
    return await project_repo.get_by_org(org_id)
