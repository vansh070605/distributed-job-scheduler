from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api import deps
from app.repositories import OrganizationRepository
from app.schemas.organization import OrganizationCreate, OrganizationResponse
from app.models.organization import Organization
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    org_in: OrganizationCreate,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.RoleChecker(["admin", "manager"]))
):
    org_repo = OrganizationRepository(db)
    existing_org = await org_repo.get_by_slug(org_in.slug)
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization with this slug already exists",
        )
    
    org = Organization(name=org_in.name, slug=org_in.slug)
    return await org_repo.create(org)


@router.get("/", response_model=List[OrganizationResponse])
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    org_repo = OrganizationRepository(db)
    return await org_repo.get_multi(skip=skip, limit=limit)
