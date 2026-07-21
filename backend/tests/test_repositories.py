import uuid
from datetime import datetime, timezone

import pytest

from database.models import (
    Application,
    CareerProfile,
    Certification,
    Education,
    Experience,
    Job,
    Language,
    Notification,
    Project,
    RefreshToken,
    ResumeVersion,
    SchedulerJob,
    Skill,
    User,
)
from database.repositories import (
    ApplicationRepository,
    AuditRepository,
    CareerProfileRepository,
    CertificationRepository,
    CompanyRepository,
    EducationRepository,
    ExperienceRepository,
    JobRepository,
    LanguageRepository,
    NotificationRepository,
    ProjectRepository,
    RefreshTokenRepository,
    ResumeVersionRepository,
    SchedulerRepository,
    SkillRepository,
    UserRepository,
)


@pytest.mark.usefixtures("session")
class TestUserRepository:
    async def test_create_and_get(self, session):
        repo = UserRepository(session)
        user = await repo.create(User(email="repo@test.com", password_hash="hash", first_name="Repo", last_name="Test"))
        assert user.id is not None
        fetched = await repo.get_by_id(user.id)
        assert fetched is not None
        assert fetched.email == "repo@test.com"

    async def test_get_by_email(self, session):
        repo = UserRepository(session)
        await repo.create(User(email="find@test.com", password_hash="h", first_name="F", last_name="U"))
        found = await repo.get_by_email("find@test.com")
        assert found is not None
        assert found.first_name == "F"

    async def test_exists_by_email(self, session):
        repo = UserRepository(session)
        await repo.create(User(email="exists@test.com", password_hash="h", first_name="E", last_name="X"))
        assert await repo.exists_by_email("exists@test.com") is True
        assert await repo.exists_by_email("nope@test.com") is False

    async def test_update(self, session):
        repo = UserRepository(session)
        user = await repo.create(User(email="upd@test.com", password_hash="hash", first_name="Old", last_name="Name"))
        user.first_name = "New"
        updated = await repo.update(user)
        assert updated.first_name == "New"

    async def test_delete(self, session):
        repo = UserRepository(session)
        user = await repo.create(User(email="del@test.com", password_hash="hash", first_name="Del", last_name="Ete"))
        await repo.delete(user)
        assert await repo.get_by_id(user.id) is None

    async def test_soft_delete(self, session):
        repo = UserRepository(session)
        user = await repo.create(
            User(email="softdel@test.com", password_hash="hash", first_name="Soft", last_name="Del")
        )
        deleted = await repo.soft_delete(user.id)
        assert deleted is not None
        assert deleted.is_deleted is True
        assert deleted.deleted_at is not None

    async def test_count(self, session):
        repo = UserRepository(session)
        for i in range(3):
            await repo.create(User(email=f"count{i}@test.com", password_hash="h", first_name="C", last_name=str(i)))
        assert await repo.count() == 3

    async def test_paginate(self, session):
        repo = UserRepository(session)
        for i in range(10):
            await repo.create(User(email=f"pg{i}@test.com", password_hash="h", first_name="P", last_name=str(i)))
        result = await repo.paginate(page=1, page_size=3)
        assert len(result["items"]) == 3
        assert result["total"] == 10
        assert result["total_pages"] == 4


@pytest.mark.usefixtures("session")
class TestJobRepository:
    async def test_search(self, session):
        repo = JobRepository(session)
        await repo.create(Job(provider="linkedin", title="Python Engineer", company="Meta"))
        await repo.create(Job(provider="indeed", title="Java Developer", company="Google"))
        results, total = await repo.search(search="Python")
        assert total == 1
        assert results[0].title == "Python Engineer"

    async def test_find_duplicates(self, session):
        repo = JobRepository(session)
        await repo.create(Job(provider="linkedin", provider_job_id="abc123", title="Engineer", company="C1"))
        dup = await repo.find_duplicates("linkedin", "abc123")
        assert dup is not None
        assert await repo.find_duplicates("linkedin", "nonexistent") is None

    async def test_bulk_create(self, session):
        repo = JobRepository(session)
        jobs = [Job(provider="linkedin", title=f"Job {i}", company="C") for i in range(5)]
        created = await repo.bulk_create(jobs)
        assert len(created) == 5
        assert created[0].id is not None

    async def test_list(self, session):
        repo = JobRepository(session)
        for i in range(10):
            await repo.create(Job(provider="linkedin", title=f"Job {i}", company="C"))
        items = await repo.list(limit=5)
        assert len(items) == 5

    async def test_search_by_location(self, session):
        repo = JobRepository(session)
        await repo.create(Job(provider="l", title="Engineer", company="C1", location="New York"))
        await repo.create(Job(provider="l", title="Engineer", company="C2", location="San Francisco"))
        results, total = await repo.search(location="New York")
        assert total == 1


@pytest.mark.usefixtures("session")
class TestApplicationRepository:
    async def test_list_by_user(self, session):
        user = await UserRepository(session).create(
            User(email="applist@test.com", password_hash="h", first_name="A", last_name="L")
        )
        job1 = await JobRepository(session).create(Job(provider="linkedin", title="Engineer", company="C"))
        job2 = await JobRepository(session).create(Job(provider="linkedin", title="Manager", company="C"))
        repo = ApplicationRepository(session)
        await repo.create(Application(user_id=user.id, job_id=job1.id, status="Draft"))
        await repo.create(Application(user_id=user.id, job_id=job2.id, status="Submitted"))
        apps, total = await repo.list_by_user(user.id)
        assert total == 2

    async def test_list_by_user_filter_status(self, session):
        user = await UserRepository(session).create(
            User(email="appfilter@test.com", password_hash="h", first_name="A", last_name="F")
        )
        job1 = await JobRepository(session).create(Job(provider="l", title="Engineer", company="C"))
        job2 = await JobRepository(session).create(Job(provider="l", title="Manager", company="C"))
        repo = ApplicationRepository(session)
        await repo.create(Application(user_id=user.id, job_id=job1.id, status="Draft"))
        await repo.create(Application(user_id=user.id, job_id=job2.id, status="Submitted"))
        apps, total = await repo.list_by_user(user.id, status="Submitted")
        assert total == 1

    async def test_exists(self, session):
        user = await UserRepository(session).create(
            User(email="appexists@test.com", password_hash="h", first_name="A", last_name="E")
        )
        job = await JobRepository(session).create(Job(provider="l", title="Engineer", company="C"))
        repo = ApplicationRepository(session)
        await repo.create(Application(user_id=user.id, job_id=job.id))
        assert await repo.exists(user.id, job.id) is True
        assert await repo.exists(user.id, uuid.uuid4()) is False


@pytest.mark.usefixtures("session")
class TestCareerProfileRepository:
    async def test_get_by_user(self, session):
        user = await UserRepository(session).create(
            User(email="cprepo@test.com", password_hash="h", first_name="C", last_name="P")
        )
        repo = CareerProfileRepository(session)
        profile = await repo.create(CareerProfile(user_id=user.id))
        found = await repo.get_by_user(user.id)
        assert found is not None
        assert found.id == profile.id


@pytest.mark.usefixtures("session")
class TestEducationRepository:
    async def test_list_by_profile(self, session):
        user = await UserRepository(session).create(
            User(email="edurepo@test.com", password_hash="h", first_name="E", last_name="D")
        )
        profile = await CareerProfileRepository(session).create(CareerProfile(user_id=user.id))
        repo = EducationRepository(session)
        await repo.create(Education(profile_id=profile.id, institution="MIT", degree="BS"))
        items = await repo.list_by_profile(profile.id)
        assert len(items) == 1
        assert items[0].institution == "MIT"


@pytest.mark.usefixtures("session")
class TestSkillRepository:
    async def test_list_by_profile(self, session):
        user = await UserRepository(session).create(
            User(email="skrepo@test.com", password_hash="h", first_name="S", last_name="K")
        )
        profile = await CareerProfileRepository(session).create(CareerProfile(user_id=user.id))
        repo = SkillRepository(session)
        await repo.create(Skill(profile_id=profile.id, name="Python"))
        items = await repo.list_by_profile(profile.id)
        assert len(items) == 1

    async def test_exists(self, session):
        user = await UserRepository(session).create(
            User(email="skex@test.com", password_hash="h", first_name="S", last_name="X")
        )
        profile = await CareerProfileRepository(session).create(CareerProfile(user_id=user.id))
        repo = SkillRepository(session)
        await repo.create(Skill(profile_id=profile.id, name="Python"))
        assert await repo.exists(profile.id, "Python") is True
        assert await repo.exists(profile.id, "Java") is False


@pytest.mark.usefixtures("session")
class TestResumeVersionRepository:
    async def test_latest_version(self, session):
        user = await UserRepository(session).create(
            User(email="rvrepo@test.com", password_hash="h", first_name="R", last_name="V")
        )
        repo = ResumeVersionRepository(session)
        await repo.create(ResumeVersion(user_id=user.id, version=1))
        await repo.create(ResumeVersion(user_id=user.id, version=2))
        latest = await repo.latest_version(user.id)
        assert latest == 2

    async def test_archive_and_restore(self, session):
        user = await UserRepository(session).create(
            User(email="rvarc@test.com", password_hash="h", first_name="R", last_name="A")
        )
        repo = ResumeVersionRepository(session)
        rv = await repo.create(ResumeVersion(user_id=user.id, version=1))
        archived = await repo.archive(rv.id)
        assert archived is not None
        assert archived.archived is True
        restored = await repo.restore(rv.id)
        assert restored.archived is False


@pytest.mark.usefixtures("session")
class TestNotificationRepository:
    async def test_mark_read(self, session):
        user = await UserRepository(session).create(
            User(email="notrepo@test.com", password_hash="h", first_name="N", last_name="R")
        )
        repo = NotificationRepository(session)
        n = await repo.create(Notification(user_id=user.id, title="Test"))
        marked = await repo.mark_read(n.id)
        assert marked is not None
        assert marked.is_read is True

    async def test_list_by_user_unread_only(self, session):
        user = await UserRepository(session).create(
            User(email="notun@test.com", password_hash="h", first_name="N", last_name="U")
        )
        repo = NotificationRepository(session)
        await repo.create(Notification(user_id=user.id, title="Unread"))
        n2 = await repo.create(Notification(user_id=user.id, title="Read"))
        await repo.mark_read(n2.id)
        items = await repo.list_by_user(user.id, unread_only=True)
        assert len(items) == 1
        assert items[0].title == "Unread"


@pytest.mark.usefixtures("session")
class TestSchedulerRepository:
    async def test_next_jobs(self, session):
        from datetime import timedelta

        user = await UserRepository(session).create(
            User(email="screpo@test.com", password_hash="h", first_name="S", last_name="C")
        )
        repo = SchedulerRepository(session)
        await repo.create(
            SchedulerJob(
                user_id=user.id,
                name="DueJob",
                enabled=True,
                next_run=datetime.now(timezone.utc) - timedelta(hours=1),
            )
        )
        await repo.create(
            SchedulerJob(
                user_id=user.id,
                name="FutureJob",
                enabled=True,
                next_run=datetime.now(timezone.utc) + timedelta(hours=1),
            )
        )
        next_jobs = await repo.next_jobs()
        assert len(next_jobs) == 1
        assert next_jobs[0].name == "DueJob"


@pytest.mark.usefixtures("session")
class TestRefreshTokenRepository:
    async def test_get_by_token_hash(self, session):
        from datetime import timedelta

        user = await UserRepository(session).create(
            User(email="rtrepo@test.com", password_hash="h", first_name="R", last_name="T")
        )
        repo = RefreshTokenRepository(session)
        token = await repo.create(
            RefreshToken(
                user_id=user.id,
                token_hash="hash123",
                expires_at=datetime.now(timezone.utc) + timedelta(days=1),
            )
        )
        found = await repo.get_by_token_hash("hash123")
        assert found is not None
        assert found.id == token.id

    async def test_revoke_all_for_user(self, session):
        from datetime import timedelta

        user = await UserRepository(session).create(
            User(email="rtrev@test.com", password_hash="h", first_name="R", last_name="V")
        )
        repo = RefreshTokenRepository(session)
        for i in range(3):
            await repo.create(
                RefreshToken(
                    user_id=user.id,
                    token_hash=f"hash{i}",
                    expires_at=datetime.now(timezone.utc) + timedelta(days=1),
                )
            )
        await repo.revoke_all_for_user(user.id)
        for i in range(3):
            found = await repo.get_by_token_hash(f"hash{i}")
            assert found is None


@pytest.mark.usefixtures("session")
class TestCompanyRepository:
    async def test_get_by_name(self, session):
        from database.models import Company

        repo = CompanyRepository(session)
        await repo.create(Company(name="Test Inc"))
        found = await repo.get_by_name("Test Inc")
        assert found is not None

    async def test_search_by_name(self, session):
        from database.models import Company

        repo = CompanyRepository(session)
        await repo.create(Company(name="Alpha Corp"))
        await repo.create(Company(name="Alpha LLC"))
        await repo.create(Company(name="Beta Corp"))
        results = await repo.search_by_name("Alpha")
        assert len(results) == 2


@pytest.mark.usefixtures("session")
class TestAuditRepository:
    async def test_log(self, session):
        repo = AuditRepository(session)
        log = await repo.log("TEST_EVENT", outcome="success")
        assert log.id is not None
        assert log.event_type == "TEST_EVENT"

    async def test_search(self, session):
        repo = AuditRepository(session)
        await repo.log("EVENT_A", outcome="success")
        await repo.log("EVENT_B", outcome="fail")
        results = await repo.search(event_type="EVENT_A")
        assert len(results) == 1


@pytest.mark.usefixtures("session")
class TestExperienceRepository:
    async def test_list_by_profile_ordered(self, session):
        from datetime import date

        user = await UserRepository(session).create(
            User(email="exrepo@test.com", password_hash="h", first_name="E", last_name="X")
        )
        profile = await CareerProfileRepository(session).create(CareerProfile(user_id=user.id))
        repo = ExperienceRepository(session)
        await repo.create(
            Experience(profile_id=profile.id, company="Google", title="Junior", start_date=date(2020, 1, 1))
        )
        await repo.create(
            Experience(profile_id=profile.id, company="Meta", title="Senior", start_date=date(2022, 1, 1))
        )
        items = await repo.list_by_profile(profile.id)
        assert len(items) == 2
        assert items[0].title == "Senior"


@pytest.mark.usefixtures("session")
class TestProjectRepository:
    async def test_exists_by_name(self, session):
        user = await UserRepository(session).create(
            User(email="projrepo@test.com", password_hash="h", first_name="P", last_name="J")
        )
        profile = await CareerProfileRepository(session).create(CareerProfile(user_id=user.id))
        repo = ProjectRepository(session)
        await repo.create(Project(profile_id=profile.id, name="My Project"))
        assert await repo.exists_by_name(profile.id, "My Project") is True
        assert await repo.exists_by_name(profile.id, "Other") is False


@pytest.mark.usefixtures("session")
class TestLanguageRepository:
    async def test_list_by_profile(self, session):
        user = await UserRepository(session).create(
            User(email="langrepo@test.com", password_hash="h", first_name="L", last_name="G")
        )
        profile = await CareerProfileRepository(session).create(CareerProfile(user_id=user.id))
        repo = LanguageRepository(session)
        await repo.create(Language(profile_id=profile.id, language="English"))
        items = await repo.list_by_profile(profile.id)
        assert len(items) == 1


@pytest.mark.usefixtures("session")
class TestCertificationRepository:
    async def test_list_by_profile(self, session):
        user = await UserRepository(session).create(
            User(email="certrepo@test.com", password_hash="h", first_name="C", last_name="R")
        )
        profile = await CareerProfileRepository(session).create(CareerProfile(user_id=user.id))
        repo = CertificationRepository(session)
        await repo.create(Certification(profile_id=profile.id, name="AWS Certified"))
        items = await repo.list_by_profile(profile.id)
        assert len(items) == 1
