import pytest

from database.models import (
    AIRequest,
    AIResponse,
    Application,
    ApplicationEvent,
    AuditLog,
    BackgroundJob,
    CareerProfile,
    Company,
    Education,
    Experience,
    Job,
    JobSearch,
    Notification,
    ProviderConfiguration,
    RefreshToken,
    ResumeTemplate,
    ResumeVersion,
    SavedSearch,
    SchedulerJob,
    Skill,
    User,
    UserPreference,
)


class TestUser:
    async def test_create_user(self, session):
        user = User(email="test@example.com", password_hash="hash", first_name="John", last_name="Doe")
        session.add(user)
        await session.flush()
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.is_active is True

    async def test_user_email_unique(self, session):
        user1 = User(email="dup@example.com", password_hash="hash", first_name="A", last_name="B")
        session.add(user1)
        await session.flush()
        user2 = User(email="dup@example.com", password_hash="hash2", first_name="C", last_name="D")
        session.add(user2)
        with pytest.raises(Exception):
            await session.flush()

    async def test_user_soft_delete(self, session):
        user = User(email="del@example.com", password_hash="hash", first_name="Del", last_name="User")
        session.add(user)
        await session.flush()
        user.soft_delete()
        assert user.is_deleted is True
        assert user.deleted_at is not None


class TestCareerProfile:
    async def test_create_profile(self, session):
        user = User(email="profile@test.com", password_hash="hash", first_name="P", last_name="R")
        session.add(user)
        await session.flush()
        profile = CareerProfile(user_id=user.id, professional_summary="A summary")
        session.add(profile)
        await session.flush()
        assert profile.id is not None
        assert profile.user_id == user.id

    async def test_profile_user_unique(self, session):
        user = User(email="unique@test.com", password_hash="hash", first_name="U", last_name="N")
        session.add(user)
        await session.flush()
        p1 = CareerProfile(user_id=user.id)
        session.add(p1)
        await session.flush()
        p2 = CareerProfile(user_id=user.id)
        session.add(p2)
        with pytest.raises(Exception):
            await session.flush()

    async def test_profile_cascade_delete(self, session):
        user = User(email="cascade@test.com", password_hash="hash", first_name="C", last_name="D")
        session.add(user)
        await session.flush()
        profile = CareerProfile(user_id=user.id)
        session.add(profile)
        await session.flush()
        education = Education(profile_id=profile.id, institution="MIT", degree="BS")
        session.add(education)
        await session.flush()
        await session.delete(profile)
        await session.flush()
        edu = await session.get(Education, education.id)
        assert edu is None


class TestEducation:
    async def test_create(self, session):
        user = User(email="edu@test.com", password_hash="h", first_name="E", last_name="D")
        session.add(user)
        await session.flush()
        profile = CareerProfile(user_id=user.id)
        session.add(profile)
        await session.flush()
        edu = Education(profile_id=profile.id, institution="Stanford", degree="MS", field_of_study="CS")
        session.add(edu)
        await session.flush()
        assert edu.id is not None
        assert edu.institution == "Stanford"


class TestExperience:
    async def test_create(self, session):
        user = User(email="exp@test.com", password_hash="h", first_name="E", last_name="X")
        session.add(user)
        await session.flush()
        profile = CareerProfile(user_id=user.id)
        session.add(profile)
        await session.flush()
        exp = Experience(profile_id=profile.id, company="Google", title="Engineer")
        session.add(exp)
        await session.flush()
        assert exp.id is not None
        assert exp.title == "Engineer"


class TestSkill:
    async def test_create(self, session):
        user = User(email="skill@test.com", password_hash="h", first_name="S", last_name="K")
        session.add(user)
        await session.flush()
        profile = CareerProfile(user_id=user.id)
        session.add(profile)
        await session.flush()
        skill = Skill(profile_id=profile.id, name="Python", proficiency="Expert")
        session.add(skill)
        await session.flush()
        assert skill.id is not None
        assert skill.name == "Python"

    async def test_unique_name_per_profile(self, session):
        user = User(email="sk2@test.com", password_hash="h", first_name="S", last_name="K")
        session.add(user)
        await session.flush()
        profile = CareerProfile(user_id=user.id)
        session.add(profile)
        await session.flush()
        s1 = Skill(profile_id=profile.id, name="Python")
        session.add(s1)
        await session.flush()
        s2 = Skill(profile_id=profile.id, name="Python")
        session.add(s2)
        with pytest.raises(Exception):
            await session.flush()


class TestJob:
    async def test_create(self, session):
        job = Job(provider="linkedin", title="Engineer", company="Meta", location="Menlo Park")
        session.add(job)
        await session.flush()
        assert job.id is not None
        assert job.title == "Engineer"

    async def test_unique_provider_job(self, session):
        j1 = Job(provider="linkedin", provider_job_id="123", title="E1", company="C1")
        session.add(j1)
        await session.flush()
        j2 = Job(provider="linkedin", provider_job_id="123", title="E2", company="C2")
        session.add(j2)
        with pytest.raises(Exception):
            await session.flush()


class TestApplication:
    async def test_create(self, session):
        user = User(email="app@test.com", password_hash="h", first_name="A", last_name="P")
        session.add(user)
        await session.flush()
        job = Job(provider="indeed", title="Job", company="ACME")
        session.add(job)
        await session.flush()
        app = Application(user_id=user.id, job_id=job.id, status="Draft")
        session.add(app)
        await session.flush()
        assert app.id is not None
        assert app.status == "Draft"

    async def test_unique_user_job(self, session):
        user = User(email="app2@test.com", password_hash="h", first_name="A", last_name="P")
        session.add(user)
        await session.flush()
        job = Job(provider="indeed", title="Job2", company="ACME")
        session.add(job)
        await session.flush()
        a1 = Application(user_id=user.id, job_id=job.id)
        session.add(a1)
        await session.flush()
        a2 = Application(user_id=user.id, job_id=job.id)
        session.add(a2)
        with pytest.raises(Exception):
            await session.flush()


class TestAuditLog:
    async def test_create(self, session):
        log = AuditLog(event_type="USER_CREATED", outcome="success")
        session.add(log)
        await session.flush()
        assert log.id is not None
        assert log.event_type == "USER_CREATED"


class TestCompany:
    async def test_create(self, session):
        company = Company(name="Test Corp", industry="Technology")
        session.add(company)
        await session.flush()
        assert company.id is not None
        assert company.name == "Test Corp"

    async def test_unique_name(self, session):
        c1 = Company(name="Unique Co")
        session.add(c1)
        await session.flush()
        c2 = Company(name="Unique Co")
        session.add(c2)
        with pytest.raises(Exception):
            await session.flush()


class TestResumeVersion:
    async def test_create(self, session):
        user = User(email="resume@test.com", password_hash="h", first_name="R", last_name="S")
        session.add(user)
        await session.flush()
        rv = ResumeVersion(user_id=user.id, version=1, title="v1")
        session.add(rv)
        await session.flush()
        assert rv.id is not None
        assert rv.version == 1

    async def test_unique_user_version(self, session):
        user = User(email="rv2@test.com", password_hash="h", first_name="R", last_name="V")
        session.add(user)
        await session.flush()
        r1 = ResumeVersion(user_id=user.id, version=1)
        session.add(r1)
        await session.flush()
        r2 = ResumeVersion(user_id=user.id, version=1)
        session.add(r2)
        with pytest.raises(Exception):
            await session.flush()


class TestNotification:
    async def test_create(self, session):
        user = User(email="notif@test.com", password_hash="h", first_name="N", last_name="F")
        session.add(user)
        await session.flush()
        n = Notification(user_id=user.id, title="Test", message="Hello")
        session.add(n)
        await session.flush()
        assert n.id is not None
        assert n.is_read is False


class TestSchedulerJob:
    async def test_create(self, session):
        user = User(email="sched@test.com", password_hash="h", first_name="S", last_name="J")
        session.add(user)
        await session.flush()
        sj = SchedulerJob(user_id=user.id, name="daily")
        session.add(sj)
        await session.flush()
        assert sj.id is not None
        assert sj.enabled is True


class TestApplicationEvent:
    async def test_create(self, session):
        from datetime import datetime, timezone

        user = User(email="evt@test.com", password_hash="h", first_name="E", last_name="V")
        session.add(user)
        await session.flush()
        job = Job(provider="evt", title="Event Job", company="EC")
        session.add(job)
        await session.flush()
        app = Application(user_id=user.id, job_id=job.id)
        session.add(app)
        await session.flush()
        event = ApplicationEvent(
            application_id=app.id,
            event_type="STATUS_CHANGE",
            description="Updated",
            occurred_at=datetime.now(timezone.utc),
        )
        session.add(event)
        await session.flush()
        assert event.id is not None
        assert event.event_type == "STATUS_CHANGE"


class TestAIRequest:
    async def test_create(self, session):
        user = User(email="ai@test.com", password_hash="h", first_name="A", last_name="I")
        session.add(user)
        await session.flush()
        req = AIRequest(user_id=user.id, provider="openrouter", model="gpt-4")
        session.add(req)
        await session.flush()
        assert req.id is not None
        assert req.status == "pending"


class TestAIResponse:
    async def test_create(self, session):
        user = User(email="air@test.com", password_hash="h", first_name="A", last_name="R")
        session.add(user)
        await session.flush()
        req = AIRequest(user_id=user.id, provider="openrouter")
        session.add(req)
        await session.flush()
        resp = AIResponse(request_id=req.id, content="Response text")
        session.add(resp)
        await session.flush()
        assert resp.id is not None


class TestRefreshToken:
    async def test_create(self, session):
        from datetime import datetime, timedelta, timezone

        user = User(email="rt@test.com", password_hash="h", first_name="R", last_name="T")
        session.add(user)
        await session.flush()
        token = RefreshToken(
            user_id=user.id,
            token_hash="abc123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        session.add(token)
        await session.flush()
        assert token.id is not None
        assert token.is_revoked is False


class TestUserPreference:
    async def test_create(self, session):
        user = User(email="pref@test.com", password_hash="h", first_name="P", last_name="R")
        session.add(user)
        await session.flush()
        pref = UserPreference(user_id=user.id, theme="dark")
        session.add(pref)
        await session.flush()
        assert pref.id is not None
        assert pref.theme == "dark"


class TestProviderConfiguration:
    async def test_create(self, session):
        pc = ProviderConfiguration(provider_name="test", provider_type="ai")
        session.add(pc)
        await session.flush()
        assert pc.id is not None
        assert pc.is_enabled is True


class TestBackgroundJob:
    async def test_create(self, session):
        user = User(email="bg@test.com", password_hash="h", first_name="B", last_name="G")
        session.add(user)
        await session.flush()
        bj = BackgroundJob(user_id=user.id, job_type="test")
        session.add(bj)
        await session.flush()
        assert bj.id is not None
        assert bj.status == "pending"


class TestSavedSearch:
    async def test_create(self, session):
        user = User(email="ss@test.com", password_hash="h", first_name="S", last_name="S")
        session.add(user)
        await session.flush()
        ss = SavedSearch(user_id=user.id, name="Python Jobs")
        session.add(ss)
        await session.flush()
        assert ss.id is not None


class TestJobSearch:
    async def test_create(self, session):
        user = User(email="js@test.com", password_hash="h", first_name="J", last_name="S")
        session.add(user)
        await session.flush()
        js = JobSearch(user_id=user.id, query="developer")
        session.add(js)
        await session.flush()
        assert js.id is not None


class TestResumeTemplate:
    async def test_create(self, session):
        user = User(email="rt2@test.com", password_hash="h", first_name="R", last_name="T")
        session.add(user)
        await session.flush()
        rt = ResumeTemplate(user_id=user.id, name="Modern")
        session.add(rt)
        await session.flush()
        assert rt.id is not None
