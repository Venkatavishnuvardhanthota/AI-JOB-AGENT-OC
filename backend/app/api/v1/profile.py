import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.deps import get_current_user, get_profile_service
from app.core.config import settings
from app.models.blacklisted_company import BlacklistedCompany
from app.models.certification import Certification
from app.models.education import Education
from app.models.experience import Experience
from app.models.language import Language
from app.models.project import Project
from app.models.skill import Skill
from app.models.user import User
from app.repositories.base import BaseRepository
from app.schemas.blacklist import (
    BlacklistedCompanyCreate,
    BlacklistedCompanyResponse,
)
from app.schemas.certification import (
    CertificationCreate,
    CertificationResponse,
    CertificationUpdate,
)
from app.schemas.education import (
    EducationCreate,
    EducationResponse,
    EducationUpdate,
)
from app.schemas.experience import (
    ExperienceCreate,
    ExperienceResponse,
    ExperienceUpdate,
)
from app.schemas.language import LanguageCreate, LanguageResponse, LanguageUpdate
from app.schemas.profile import UserProfileResponse, UserProfileUpdate
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.skill import SkillCreate, SkillResponse, SkillUpdate
from app.services.profile import ProfileService

router = APIRouter()


async def _save_upload(file: UploadFile, subdir: str) -> str:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is not allowed.",
        )
    upload_dir = os.path.join(settings.UPLOAD_DIR, subdir)
    os.makedirs(upload_dir, exist_ok=True)
    file_id = str(uuid.uuid4())
    dest = os.path.join(upload_dir, f"{file_id}{ext}")
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )
    with open(dest, "wb") as f:
        f.write(content)
    return dest


async def _verify_ownership(
    repo: BaseRepository, item_id: uuid.UUID, user_id: uuid.UUID
):
    item = await repo.get(item_id)
    if not item or str(item.user_id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found.",
        )
    return item


# ── User Profile ──

@router.get("", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> UserProfileResponse:
    profile = await service.get_or_create_profile(current_user.id)
    return UserProfileResponse.model_validate(profile)


@router.put("", response_model=UserProfileResponse)
async def update_profile(
    request: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> UserProfileResponse:
    profile = await service.update_profile(
        current_user.id, **request.model_dump(exclude_unset=True)
    )
    return UserProfileResponse.model_validate(profile)


@router.post("/resume", response_model=UserProfileResponse)
async def upload_resume(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> UserProfileResponse:
    path = await _save_upload(file, "resumes")
    profile = await service.update_profile(
        current_user.id, resume_file=path
    )
    return UserProfileResponse.model_validate(profile)


# ── Education ──

@router.get("/education", response_model=list[EducationResponse])
async def list_education(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> list[EducationResponse]:
    items = await service.get_educations(current_user.id)
    return [EducationResponse.model_validate(e) for e in items]


@router.post("/education", response_model=EducationResponse, status_code=201)
async def create_education(
    request: EducationCreate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> EducationResponse:
    repo = BaseRepository(Education, service.session)
    edu = await repo.create(user_id=current_user.id, **request.model_dump())
    return EducationResponse.model_validate(edu)


@router.put("/education/{item_id}", response_model=EducationResponse)
async def update_education(
    item_id: uuid.UUID,
    request: EducationUpdate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> EducationResponse:
    repo = BaseRepository(Education, service.session)
    item = await _verify_ownership(repo, item_id, current_user.id)
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await service.session.flush()
    await service.session.refresh(item)
    return EducationResponse.model_validate(item)


@router.delete("/education/{item_id}", status_code=204)
async def delete_education(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    repo = BaseRepository(Education, service.session)
    item = await _verify_ownership(repo, item_id, current_user.id)
    await service.session.delete(item)
    await service.session.flush()


# ── Experience ──

@router.get("/experience", response_model=list[ExperienceResponse])
async def list_experience(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> list[ExperienceResponse]:
    items = await service.get_experiences(current_user.id)
    return [ExperienceResponse.model_validate(e) for e in items]


@router.post("/experience", response_model=ExperienceResponse, status_code=201)
async def create_experience(
    request: ExperienceCreate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> ExperienceResponse:
    repo = BaseRepository(Experience, service.session)
    item = await repo.create(user_id=current_user.id, **request.model_dump())
    return ExperienceResponse.model_validate(item)


@router.put("/experience/{item_id}", response_model=ExperienceResponse)
async def update_experience(
    item_id: uuid.UUID,
    request: ExperienceUpdate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> ExperienceResponse:
    repo = BaseRepository(Experience, service.session)
    item = await _verify_ownership(repo, item_id, current_user.id)
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await service.session.flush()
    await service.session.refresh(item)
    return ExperienceResponse.model_validate(item)


@router.delete("/experience/{item_id}", status_code=204)
async def delete_experience(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    repo = BaseRepository(Experience, service.session)
    item = await _verify_ownership(repo, item_id, current_user.id)
    await service.session.delete(item)
    await service.session.flush()


# ── Projects ──

@router.get("/projects", response_model=list[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> list[ProjectResponse]:
    items = await service.get_projects(current_user.id)
    return [ProjectResponse.model_validate(p) for p in items]


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def create_project(
    request: ProjectCreate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> ProjectResponse:
    repo = BaseRepository(Project, service.session)
    item = await repo.create(user_id=current_user.id, **request.model_dump())
    return ProjectResponse.model_validate(item)


@router.put("/projects/{item_id}", response_model=ProjectResponse)
async def update_project(
    item_id: uuid.UUID,
    request: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> ProjectResponse:
    repo = BaseRepository(Project, service.session)
    item = await _verify_ownership(repo, item_id, current_user.id)
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await service.session.flush()
    await service.session.refresh(item)
    return ProjectResponse.model_validate(item)


@router.delete("/projects/{item_id}", status_code=204)
async def delete_project(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    repo = BaseRepository(Project, service.session)
    item = await _verify_ownership(repo, item_id, current_user.id)
    await service.session.delete(item)
    await service.session.flush()


# ── Skills ──

@router.get("/skills", response_model=list[SkillResponse])
async def list_skills(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> list[SkillResponse]:
    items = await service.get_skills(current_user.id)
    return [SkillResponse.model_validate(s) for s in items]


@router.post("/skills", response_model=SkillResponse, status_code=201)
async def create_skill(
    request: SkillCreate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> SkillResponse:
    repo = BaseRepository(Skill, service.session)
    item = await repo.create(user_id=current_user.id, **request.model_dump())
    return SkillResponse.model_validate(item)


@router.put("/skills/{item_id}", response_model=SkillResponse)
async def update_skill(
    item_id: uuid.UUID,
    request: SkillUpdate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> SkillResponse:
    repo = BaseRepository(Skill, service.session)
    item = await _verify_ownership(repo, item_id, current_user.id)
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await service.session.flush()
    await service.session.refresh(item)
    return SkillResponse.model_validate(item)


@router.delete("/skills/{item_id}", status_code=204)
async def delete_skill(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    repo = BaseRepository(Skill, service.session)
    item = await _verify_ownership(repo, item_id, current_user.id)
    await service.session.delete(item)
    await service.session.flush()


# ── Certifications ──

@router.get("/certifications", response_model=list[CertificationResponse])
async def list_certifications(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> list[CertificationResponse]:
    items = await service.get_certifications(current_user.id)
    return [CertificationResponse.model_validate(c) for c in items]


@router.post("/certifications", response_model=CertificationResponse, status_code=201)
async def create_certification(
    request: CertificationCreate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> CertificationResponse:
    repo = BaseRepository(Certification, service.session)
    item = await repo.create(user_id=current_user.id, **request.model_dump())
    return CertificationResponse.model_validate(item)


@router.put("/certifications/{item_id}", response_model=CertificationResponse)
async def update_certification(
    item_id: uuid.UUID,
    request: CertificationUpdate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> CertificationResponse:
    repo = BaseRepository(Certification, service.session)
    item = await _verify_ownership(repo, item_id, current_user.id)
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await service.session.flush()
    await service.session.refresh(item)
    return CertificationResponse.model_validate(item)


@router.delete("/certifications/{item_id}", status_code=204)
async def delete_certification(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    repo = BaseRepository(Certification, service.session)
    item = await _verify_ownership(repo, item_id, current_user.id)
    await service.session.delete(item)
    await service.session.flush()


# ── Languages ──

@router.get("/languages", response_model=list[LanguageResponse])
async def list_languages(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> list[LanguageResponse]:
    items = await service.get_languages(current_user.id)
    return [LanguageResponse.model_validate(lang) for lang in items]


@router.post("/languages", response_model=LanguageResponse, status_code=201)
async def create_language(
    request: LanguageCreate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> LanguageResponse:
    repo = BaseRepository(Language, service.session)
    item = await repo.create(user_id=current_user.id, **request.model_dump())
    return LanguageResponse.model_validate(item)


@router.put("/languages/{item_id}", response_model=LanguageResponse)
async def update_language(
    item_id: uuid.UUID,
    request: LanguageUpdate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> LanguageResponse:
    repo = BaseRepository(Language, service.session)
    item = await _verify_ownership(repo, item_id, current_user.id)
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    await service.session.flush()
    await service.session.refresh(item)
    return LanguageResponse.model_validate(item)


@router.delete("/languages/{item_id}", status_code=204)
async def delete_language(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    repo = BaseRepository(Language, service.session)
    item = await _verify_ownership(repo, item_id, current_user.id)
    await service.session.delete(item)
    await service.session.flush()


# ── Blacklist ──

@router.get("/blacklist", response_model=list[BlacklistedCompanyResponse])
async def list_blacklist(
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> list[BlacklistedCompanyResponse]:
    items = await service.get_blacklisted_companies(current_user.id)
    return [BlacklistedCompanyResponse.model_validate(b) for b in items]


@router.post("/blacklist", response_model=BlacklistedCompanyResponse, status_code=201)
async def add_to_blacklist(
    request: BlacklistedCompanyCreate,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> BlacklistedCompanyResponse:
    repo = BaseRepository(BlacklistedCompany, service.session)
    item = await repo.create(user_id=current_user.id, **request.model_dump())
    return BlacklistedCompanyResponse.model_validate(item)


@router.delete("/blacklist/{item_id}", status_code=204)
async def remove_from_blacklist(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    repo = BaseRepository(BlacklistedCompany, service.session)
    item = await _verify_ownership(repo, item_id, current_user.id)
    await service.session.delete(item)
    await service.session.flush()
