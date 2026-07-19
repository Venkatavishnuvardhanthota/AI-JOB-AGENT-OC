import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.browser_automation import (
    AutomationLogListItem,
    AutomationRunRequest,
    AutomationRunResponse,
    BrowserAutomationResult,
    SiteConfigResponse,
)
from app.services.browser.automation_service import BrowserAutomationService
from app.services.browser.site_configs import list_permitted_sites

router = APIRouter()


def get_automation_service(
    db: AsyncSession = Depends(get_db),
) -> BrowserAutomationService:
    return BrowserAutomationService(db)


@router.get("/automation/sites", response_model=list[SiteConfigResponse])
async def list_automation_sites(
    current_user: User = Depends(get_current_user),
) -> list[SiteConfigResponse]:
    sites = list_permitted_sites()
    return [SiteConfigResponse(**s) for s in sites]


@router.post("/automation/run", response_model=AutomationRunResponse, status_code=202)
async def run_automation(
    request: AutomationRunRequest,
    current_user: User = Depends(get_current_user),
    service: BrowserAutomationService = Depends(get_automation_service),
) -> AutomationRunResponse:
    result = await service.run_automation(
        user_id=current_user.id,
        url=request.url,
        fields=[f.model_dump() for f in request.fields],
        resume_file_path=request.resume_file_path,
        cover_letter_file_path=request.cover_letter_file_path,
        certificate_file_paths=request.certificate_file_paths,
        job_posting_id=request.job_posting_id,
    )
    return AutomationRunResponse(
        id=uuid.uuid4(),
        status=result.status,
        message=result.error or f"Automation completed with status: {result.status}",
    )


@router.get("/automation/logs", response_model=list[AutomationLogListItem])
async def list_automation_logs(
    current_user: User = Depends(get_current_user),
    service: BrowserAutomationService = Depends(get_automation_service),
) -> list[AutomationLogListItem]:
    logs = await service.list_logs(current_user.id)
    return [AutomationLogListItem.model_validate(log) for log in logs]


@router.get("/automation/logs/{log_id}", response_model=BrowserAutomationResult)
async def get_automation_log(
    log_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: BrowserAutomationService = Depends(get_automation_service),
) -> BrowserAutomationResult:
    log = await service.get_log(log_id, current_user.id)
    if not log:
        raise HTTPException(status_code=404, detail="Automation log not found.")
    return BrowserAutomationResult.model_validate(log)
