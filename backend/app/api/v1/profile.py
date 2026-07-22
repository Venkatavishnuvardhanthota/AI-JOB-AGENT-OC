import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import User
from app.schemas.career_profile import CareerProfileResponse, CareerProfileUpdate
from app.schemas.certification import CertificationCreate, CertificationResponse, CertificationUpdate
from app.schemas.education import EducationCreate, EducationResponse, EducationUpdate
from app.schemas.experience import ExperienceCreate, ExperienceResponse, ExperienceUpdate
from app.schemas.job_preference import JobPreferenceResponse, JobPreferenceUpdate
from app.schemas.language import LanguageCreate, LanguageResponse, LanguageUpdate
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.skill import SkillCreate, SkillResponse, SkillUpdate
from app.schemas.social_link import SocialLinkCreate, SocialLinkResponse, SocialLinkUpdate
from app.services.profile import CareerProfileService

router = APIRouter()


@router.get("/")
async def get_profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CareerProfileService(db)
    profile = await service.get_profile(current_user.id)
    return {"success": True, "data": CareerProfileResponse.model_validate(profile).model_dump()}


@router.patch("/")
async def update_profile(
    body: CareerProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    profile = await service.update_profile(current_user.id, body.model_dump(exclude_none=True))
    return {"success": True, "data": CareerProfileResponse.model_validate(profile).model_dump()}


@router.get("/completeness")
async def profile_completeness(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CareerProfileService(db)
    result = await service.calculate_completeness(current_user.id)
    return {"success": True, "data": result}


# ── Education ──


@router.post("/education", status_code=201)
async def add_education(
    body: EducationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    edu = await service.add_education(current_user.id, body.model_dump())
    return {"success": True, "data": EducationResponse.model_validate(edu).model_dump()}


@router.patch("/education/{education_id}")
async def update_education(
    education_id: uuid.UUID,
    body: EducationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    edu = await service.update_education(current_user.id, education_id, body.model_dump(exclude_none=True))
    return {"success": True, "data": EducationResponse.model_validate(edu).model_dump()}


@router.delete("/education/{education_id}", status_code=204)
async def delete_education(
    education_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    await service.delete_education(current_user.id, education_id)


# ── Experience ──


@router.post("/experience", status_code=201)
async def add_experience(
    body: ExperienceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    exp = await service.add_experience(current_user.id, body.model_dump())
    return {"success": True, "data": ExperienceResponse.model_validate(exp).model_dump()}


@router.patch("/experience/{experience_id}")
async def update_experience(
    experience_id: uuid.UUID,
    body: ExperienceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    exp = await service.update_experience(current_user.id, experience_id, body.model_dump(exclude_none=True))
    return {"success": True, "data": ExperienceResponse.model_validate(exp).model_dump()}


@router.delete("/experience/{experience_id}", status_code=204)
async def delete_experience(
    experience_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    await service.delete_experience(current_user.id, experience_id)


# ── Skills ──


@router.post("/skills", status_code=201)
async def add_skill(
    body: SkillCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    skill = await service.add_skill(current_user.id, body.model_dump())
    return {"success": True, "data": SkillResponse.model_validate(skill).model_dump()}


@router.patch("/skills/{skill_id}")
async def update_skill(
    skill_id: uuid.UUID,
    body: SkillUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    skill = await service.update_skill(current_user.id, skill_id, body.model_dump(exclude_none=True))
    return {"success": True, "data": SkillResponse.model_validate(skill).model_dump()}


@router.delete("/skills/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    await service.delete_skill(current_user.id, skill_id)


# ── Projects ──


@router.post("/projects", status_code=201)
async def add_project(
    body: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    proj = await service.add_project(current_user.id, body.model_dump())
    return {"success": True, "data": ProjectResponse.model_validate(proj).model_dump()}


@router.patch("/projects/{project_id}")
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    proj = await service.update_project(current_user.id, project_id, body.model_dump(exclude_none=True))
    return {"success": True, "data": ProjectResponse.model_validate(proj).model_dump()}


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    await service.delete_project(current_user.id, project_id)


# ── Certifications ──


@router.post("/certifications", status_code=201)
async def add_certification(
    body: CertificationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    cert = await service.add_certification(current_user.id, body.model_dump())
    return {"success": True, "data": CertificationResponse.model_validate(cert).model_dump()}


@router.patch("/certifications/{certification_id}")
async def update_certification(
    certification_id: uuid.UUID,
    body: CertificationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    cert = await service.update_certification(
        current_user.id, certification_id, body.model_dump(exclude_none=True)
    )
    return {"success": True, "data": CertificationResponse.model_validate(cert).model_dump()}


@router.delete("/certifications/{certification_id}", status_code=204)
async def delete_certification(
    certification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    await service.delete_certification(current_user.id, certification_id)


# ── Languages ──


@router.post("/languages", status_code=201)
async def add_language(
    body: LanguageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    lang = await service.add_language(current_user.id, body.model_dump())
    return {"success": True, "data": LanguageResponse.model_validate(lang).model_dump()}


@router.patch("/languages/{language_id}")
async def update_language(
    language_id: uuid.UUID,
    body: LanguageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    lang = await service.update_language(current_user.id, language_id, body.model_dump(exclude_none=True))
    return {"success": True, "data": LanguageResponse.model_validate(lang).model_dump()}


@router.delete("/languages/{language_id}", status_code=204)
async def delete_language(
    language_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    await service.delete_language(current_user.id, language_id)


# ── Social Links ──


@router.post("/social-links", status_code=201)
async def add_social_link(
    body: SocialLinkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    link = await service.add_social_link(current_user.id, body.model_dump())
    return {"success": True, "data": SocialLinkResponse.model_validate(link).model_dump()}


@router.patch("/social-links/{link_id}")
async def update_social_link(
    link_id: uuid.UUID,
    body: SocialLinkUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    link = await service.update_social_link(current_user.id, link_id, body.model_dump(exclude_none=True))
    return {"success": True, "data": SocialLinkResponse.model_validate(link).model_dump()}


@router.delete("/social-links/{link_id}", status_code=204)
async def delete_social_link(
    link_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    await service.delete_social_link(current_user.id, link_id)


# ── Preferences ──


@router.patch("/preferences")
async def update_preferences(
    body: JobPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CareerProfileService(db)
    profile = await service.get_profile(current_user.id)
    from app.models import JobPreference
    from app.repositories import JobPreferenceRepository

    repo = JobPreferenceRepository(db)
    prefs = await repo.get_by_profile(profile.id)
    if not prefs:
        prefs = JobPreference(profile_id=profile.id)
        await repo.create(prefs)
    for key, value in body.model_dump(exclude_none=True).items():
        setattr(prefs, key, value)
    await repo.update(prefs)
    return {"success": True, "data": JobPreferenceResponse.model_validate(prefs).model_dump()}
