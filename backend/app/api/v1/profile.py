from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.repositories.certification import CertificationRepository
from app.repositories.education import EducationRepository
from app.repositories.experience import ExperienceRepository
from app.repositories.job_preference import JobPreferenceRepository
from app.repositories.language import LanguageRepository
from app.repositories.project import ProjectRepository
from app.repositories.skill import SkillRepository
from app.schemas.career_profile import CareerProfileResponse, CareerProfileUpdate
from app.schemas.certification import CertificationCreate, CertificationResponse, CertificationUpdate
from app.schemas.education import EducationCreate, EducationResponse, EducationUpdate
from app.schemas.experience import ExperienceCreate, ExperienceResponse, ExperienceUpdate
from app.schemas.job_preference import JobPreferenceResponse, JobPreferenceUpdate
from app.schemas.language import LanguageCreate, LanguageResponse, LanguageUpdate
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.schemas.skill import SkillCreate, SkillResponse, SkillUpdate
from app.services.profile import CareerProfileService

router = APIRouter()


@router.get("/")
async def get_profile(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CareerProfileService(db)
    profile = await service.get_profile(current_user.id)
    return {"success": True, "data": CareerProfileResponse.model_validate(profile).model_dump()}


@router.patch("/")
async def update_profile(
    body: CareerProfileUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = CareerProfileService(db)
    profile = await service.update_profile(current_user.id, body.model_dump(exclude_none=True))
    return {"success": True, "data": CareerProfileResponse.model_validate(profile).model_dump()}


@router.get("/completeness")
async def profile_completeness(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    service = CareerProfileService(db)
    result = await service.calculate_completeness(current_user.id)
    return {"success": True, "data": result}


@router.post("/education")
async def add_education(
    body: EducationCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = CareerProfileService(db)
    profile = await service.get_profile(current_user.id)
    from app.models.education import Education

    edu = Education(profile_id=profile.id, **body.model_dump())
    repo = EducationRepository(db)
    created = await repo.create(edu)
    return {"success": True, "data": EducationResponse.model_validate(created).model_dump()}


@router.patch("/education/{education_id}")
async def update_education(
    education_id: str,
    body: EducationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = EducationRepository(db)
    edu = await repo.get_by_id(education_id)
    if not edu:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Education not found.")
    for key, value in body.model_dump(exclude_none=True).items():
        setattr(edu, key, value)
    await repo.update(edu)
    return {"success": True, "data": EducationResponse.model_validate(edu).model_dump()}


@router.delete("/education/{education_id}", status_code=204)
async def delete_education(
    education_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    repo = EducationRepository(db)
    edu = await repo.get_by_id(education_id)
    if edu:
        await repo.delete(edu)


@router.post("/experience")
async def add_experience(
    body: ExperienceCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = CareerProfileService(db)
    profile = await service.get_profile(current_user.id)
    from app.models.experience import Experience

    exp = Experience(profile_id=profile.id, **body.model_dump())
    repo = ExperienceRepository(db)
    created = await repo.create(exp)
    return {"success": True, "data": ExperienceResponse.model_validate(created).model_dump()}


@router.patch("/experience/{experience_id}")
async def update_experience(
    experience_id: str,
    body: ExperienceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ExperienceRepository(db)
    exp = await repo.get_by_id(experience_id)
    if not exp:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Experience not found.")
    for key, value in body.model_dump(exclude_none=True).items():
        setattr(exp, key, value)
    await repo.update(exp)
    return {"success": True, "data": ExperienceResponse.model_validate(exp).model_dump()}


@router.delete("/experience/{experience_id}", status_code=204)
async def delete_experience(
    experience_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    repo = ExperienceRepository(db)
    exp = await repo.get_by_id(experience_id)
    if exp:
        await repo.delete(exp)


@router.post("/projects")
async def add_project(
    body: ProjectCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = CareerProfileService(db)
    profile = await service.get_profile(current_user.id)
    from app.models.project import Project

    proj = Project(profile_id=profile.id, **body.model_dump())
    repo = ProjectRepository(db)
    created = await repo.create(proj)
    return {"success": True, "data": ProjectResponse.model_validate(created).model_dump()}


@router.patch("/projects/{project_id}")
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ProjectRepository(db)
    proj = await repo.get_by_id(project_id)
    if not proj:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Project not found.")
    for key, value in body.model_dump(exclude_none=True).items():
        setattr(proj, key, value)
    await repo.update(proj)
    return {"success": True, "data": ProjectResponse.model_validate(proj).model_dump()}


@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    repo = ProjectRepository(db)
    proj = await repo.get_by_id(project_id)
    if proj:
        await repo.delete(proj)


@router.post("/skills")
async def add_skill(
    body: SkillCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = CareerProfileService(db)
    profile = await service.get_profile(current_user.id)
    from app.models.skill import Skill

    skill = Skill(profile_id=profile.id, **body.model_dump())
    repo = SkillRepository(db)
    created = await repo.create(skill)
    return {"success": True, "data": SkillResponse.model_validate(created).model_dump()}


@router.patch("/skills/{skill_id}")
async def update_skill(
    skill_id: str, body: SkillUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    repo = SkillRepository(db)
    skill = await repo.get_by_id(skill_id)
    if not skill:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Skill not found.")
    for key, value in body.model_dump(exclude_none=True).items():
        setattr(skill, key, value)
    await repo.update(skill)
    return {"success": True, "data": SkillResponse.model_validate(skill).model_dump()}


@router.delete("/skills/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    repo = SkillRepository(db)
    skill = await repo.get_by_id(skill_id)
    if skill:
        await repo.delete(skill)


@router.post("/certifications")
async def add_certification(
    body: CertificationCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = CareerProfileService(db)
    profile = await service.get_profile(current_user.id)
    from app.models.certification import Certification

    cert = Certification(profile_id=profile.id, **body.model_dump())
    repo = CertificationRepository(db)
    created = await repo.create(cert)
    return {"success": True, "data": CertificationResponse.model_validate(created).model_dump()}


@router.patch("/certifications/{certification_id}")
async def update_certification(
    certification_id: str,
    body: CertificationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = CertificationRepository(db)
    cert = await repo.get_by_id(certification_id)
    if not cert:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Certification not found.")
    for key, value in body.model_dump(exclude_none=True).items():
        setattr(cert, key, value)
    await repo.update(cert)
    return {"success": True, "data": CertificationResponse.model_validate(cert).model_dump()}


@router.delete("/certifications/{certification_id}", status_code=204)
async def delete_certification(
    certification_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    repo = CertificationRepository(db)
    cert = await repo.get_by_id(certification_id)
    if cert:
        await repo.delete(cert)


@router.post("/languages")
async def add_language(
    body: LanguageCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = CareerProfileService(db)
    profile = await service.get_profile(current_user.id)
    from app.models.language import Language

    lang = Language(profile_id=profile.id, **body.model_dump())
    repo = LanguageRepository(db)
    created = await repo.create(lang)
    return {"success": True, "data": LanguageResponse.model_validate(created).model_dump()}


@router.patch("/languages/{language_id}")
async def update_language(
    language_id: str,
    body: LanguageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = LanguageRepository(db)
    lang = await repo.get_by_id(language_id)
    if not lang:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Language not found.")
    for key, value in body.model_dump(exclude_none=True).items():
        setattr(lang, key, value)
    await repo.update(lang)
    return {"success": True, "data": LanguageResponse.model_validate(lang).model_dump()}


@router.delete("/languages/{language_id}", status_code=204)
async def delete_language(
    language_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    repo = LanguageRepository(db)
    lang = await repo.get_by_id(language_id)
    if lang:
        await repo.delete(lang)


@router.patch("/preferences")
async def update_preferences(
    body: JobPreferenceUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    service = CareerProfileService(db)
    profile = await service.get_profile(current_user.id)
    repo = JobPreferenceRepository(db)
    prefs = await repo.get_by_profile(profile.id)
    if not prefs:
        from app.models.job_preference import JobPreference

        prefs = JobPreference(profile_id=profile.id)
        await repo.create(prefs)
    for key, value in body.model_dump(exclude_none=True).items():
        setattr(prefs, key, value)
    await repo.update(prefs)
    return {"success": True, "data": JobPreferenceResponse.model_validate(prefs).model_dump()}
