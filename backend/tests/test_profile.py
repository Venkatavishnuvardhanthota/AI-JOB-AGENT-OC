import pytest
from httpx import AsyncClient


async def _register_and_login(
    client: AsyncClient, email: str = "profile_test@example.com"
) -> tuple[str, str]:
    password = "testpassword123"
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    data = login_resp.json()
    return data["access_token"], data["refresh_token"]


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_profile_creates_default(client: AsyncClient):
    token, _ = await _register_and_login(client)
    response = await client.get(
        "/api/v1/profile", headers=_auth_header(token)
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] is None
    assert data["headline"] is None
    assert data["bio"] is None


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient):
    token, _ = await _register_and_login(client)
    payload = {
        "phone": "+1234567890",
        "headline": "Software Engineer",
        "bio": "Experienced developer",
        "location": "San Francisco",
        "salary_expectation_min": 100000,
        "salary_expectation_max": 150000,
        "salary_currency": "USD",
        "linkedin_url": "https://linkedin.com/in/test",
        "github_url": "https://github.com/test",
    }
    response = await client.put(
        "/api/v1/profile",
        json=payload,
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "+1234567890"
    assert data["headline"] == "Software Engineer"
    assert data["location"] == "San Francisco"
    assert data["salary_expectation_min"] == 100000


@pytest.mark.asyncio
async def test_profile_unauthorized(client: AsyncClient):
    response = await client.get("/api/v1/profile")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_education(client: AsyncClient):
    token, _ = await _register_and_login(client)
    payload = {
        "institution": "MIT",
        "degree": "B.S. Computer Science",
        "field_of_study": "Computer Science",
        "start_date": "2018-09-01",
        "end_date": "2022-06-01",
        "gpa": 3.8,
    }
    response = await client.post(
        "/api/v1/profile/education",
        json=payload,
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["institution"] == "MIT"
    assert data["degree"] == "B.S. Computer Science"
    assert data["gpa"] == 3.8
    assert "id" in data


@pytest.mark.asyncio
async def test_list_education(client: AsyncClient):
    token, _ = await _register_and_login(client)
    await client.post(
        "/api/v1/profile/education",
        json={
            "institution": "Stanford",
            "degree": "M.S. CS",
        },
        headers=_auth_header(token),
    )
    response = await client.get(
        "/api/v1/profile/education",
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["institution"] == "Stanford"


@pytest.mark.asyncio
async def test_update_education(client: AsyncClient):
    token, _ = await _register_and_login(client)
    create_resp = await client.post(
        "/api/v1/profile/education",
        json={"institution": "Harvard", "degree": "B.A."},
        headers=_auth_header(token),
    )
    edu_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/profile/education/{edu_id}",
        json={"gpa": 3.9},
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    assert response.json()["gpa"] == 3.9


@pytest.mark.asyncio
async def test_delete_education(client: AsyncClient):
    token, _ = await _register_and_login(client)
    create_resp = await client.post(
        "/api/v1/profile/education",
        json={"institution": "Yale", "degree": "B.S."},
        headers=_auth_header(token),
    )
    edu_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/profile/education/{edu_id}",
        headers=_auth_header(token),
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_experience(client: AsyncClient):
    token, _ = await _register_and_login(client)
    payload = {
        "company": "Google",
        "title": "Software Engineer",
        "location": "Mountain View",
        "start_date": "2022-07-01",
        "is_current": True,
    }
    response = await client.post(
        "/api/v1/profile/experience",
        json=payload,
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["company"] == "Google"
    assert data["title"] == "Software Engineer"
    assert data["is_current"] is True


@pytest.mark.asyncio
async def test_create_skill(client: AsyncClient):
    token, _ = await _register_and_login(client)
    response = await client.post(
        "/api/v1/profile/skills",
        json={"name": "Python", "category": "Language", "proficiency": 5},
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Python"


@pytest.mark.asyncio
async def test_list_skills(client: AsyncClient):
    token, _ = await _register_and_login(client)
    await client.post(
        "/api/v1/profile/skills",
        json={"name": "FastAPI", "category": "Framework"},
        headers=_auth_header(token),
    )
    response = await client.get(
        "/api/v1/profile/skills",
        headers=_auth_header(token),
    )
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_create_certification(client: AsyncClient):
    token, _ = await _register_and_login(client)
    response = await client.post(
        "/api/v1/profile/certifications",
        json={
            "name": "AWS Solutions Architect",
            "issuer": "Amazon",
            "issue_date": "2023-01-15",
        },
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    assert response.json()["issuer"] == "Amazon"


@pytest.mark.asyncio
async def test_create_language(client: AsyncClient):
    token, _ = await _register_and_login(client)
    response = await client.post(
        "/api/v1/profile/languages",
        json={"name": "English", "proficiency": "Native"},
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    assert response.json()["name"] == "English"


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    token, _ = await _register_and_login(client)
    response = await client.post(
        "/api/v1/profile/projects",
        json={
            "name": "AI Agent",
            "description": "An AI-powered job application agent",
            "url": "https://github.com/test/ai-agent",
        },
        headers=_auth_header(token),
    )
    assert response.status_code == 201
    assert response.json()["name"] == "AI Agent"


@pytest.mark.asyncio
async def test_blacklist_crud(client: AsyncClient):
    token, _ = await _register_and_login(client)

    create_resp = await client.post(
        "/api/v1/profile/blacklist",
        json={"company_name": "Bad Corp", "reason": "Poor experience"},
        headers=_auth_header(token),
    )
    assert create_resp.status_code == 201
    bl_id = create_resp.json()["id"]

    list_resp = await client.get(
        "/api/v1/profile/blacklist",
        headers=_auth_header(token),
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    delete_resp = await client.delete(
        f"/api/v1/profile/blacklist/{bl_id}",
        headers=_auth_header(token),
    )
    assert delete_resp.status_code == 204


@pytest.mark.asyncio
async def test_cannot_access_others_data(client: AsyncClient):
    token1, _ = await _register_and_login(
        client, "user1_profile@example.com"
    )

    create_resp = await client.post(
        "/api/v1/profile/skills",
        json={"name": "Python", "category": "Language"},
        headers=_auth_header(token1),
    )
    skill_id = create_resp.json()["id"]

    token2, _ = await _register_and_login(
        client, "user2_profile@example.com"
    )

    response = await client.put(
        f"/api/v1/profile/skills/{skill_id}",
        json={"name": "Java"},
        headers=_auth_header(token2),
    )
    assert response.status_code == 404
