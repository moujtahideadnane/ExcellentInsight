import uuid

from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import (
    get_current_org_id,
    get_current_user_id,
    get_rls_db,
    get_storage,
)
from app.schemas.errors import RESPONSES_400, RESPONSES_401, RESPONSES_413
from app.schemas.upload import UploadResponse
from app.services.job_service import JobService
from app.storage.base import StorageBackend

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={**RESPONSES_400, **RESPONSES_401, **RESPONSES_413},
)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user_id: uuid.UUID = Depends(get_current_user_id),
    current_org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_rls_db),
    storage: StorageBackend = Depends(get_storage),
):
    arq_pool = getattr(request.app.state, "arq_pool", None)
    return await JobService.create_and_enqueue(
        db=db,
        user_id=current_user_id,
        org_id=current_org_id,
        file=file,
        storage=storage,
        arq_pool=arq_pool,
    )
