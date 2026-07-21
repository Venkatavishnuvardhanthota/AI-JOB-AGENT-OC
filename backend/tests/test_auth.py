import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.api.v1.auth import router as auth_router
from app.core.database import get_db
from app.core.exceptions import AuthenticationError, ConflictError, NotFoundError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)
from app.schemas.auth import RegisterRequest
from app.services.auth import AuthService
from database.models.user import User
from database.repositories import UserRepository


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "TestPass123!"
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPass123!", hashed) is False

    def test_hash_is_different_each_time(self):
        password = "TestPass123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2


class TestPasswordStrengthValidation:
    def test_valid_password(self):
        request = RegisterRequest(
            email="test@example.com",
            password="StrongPass1!",
            first_name="John",
            last_name="Doe",
        )
        assert request.password == "StrongPass1!"

    def test_missing_uppercase(self):
        with pytest.raises(ValueError, match="uppercase"):
            RegisterRequest(
                email="test@example.com",
                password="weakpass1!",
                first_name="John",
                last_name="Doe",
            )

    def test_missing_lowercase(self):
        with pytest.raises(ValueError, match="lowercase"):
            RegisterRequest(
                email="test@example.com",
                password="WEAKPASS1!",
                first_name="John",
                last_name="Doe",
            )

    def test_missing_digit(self):
        with pytest.raises(ValueError, match="digit"):
            RegisterRequest(
                email="test@example.com",
                password="WeakPass!",
                first_name="John",
                last_name="Doe",
            )

    def test_missing_special_char(self):
        with pytest.raises(ValueError, match="special"):
            RegisterRequest(
                email="test@example.com",
                password="WeakPass1",
                first_name="John",
                last_name="Doe",
            )

    def test_too_short(self):
        with pytest.raises(ValueError, match="at least 8"):
            RegisterRequest(
                email="test@example.com",
                password="Ab1!",
                first_name="John",
                last_name="Doe",
            )


class TestUserRepository:
    async def test_create_user(self, session: AsyncSession):
        repo = UserRepository(session)
        user = User(email="test@example.com", password_hash="hash", first_name="John", last_name="Doe")
        created = await repo.create(user)
        assert created.id is not None
        assert created.email == "test@example.com"
        assert created.is_verified is False
        assert created.is_admin is False
        assert created.last_login_at is None

    async def test_get_by_email(self, session: AsyncSession):
        repo = UserRepository(session)
        user = User(
            email="findme@example.com",
            password_hash="hash",
            first_name="Find",
            last_name="Me",
        )
        await repo.create(user)
        found = await repo.get_by_email("findme@example.com")
        assert found is not None
        assert found.first_name == "Find"
        assert await repo.get_by_email("nonexistent@example.com") is None

    async def test_exists_by_email(self, session: AsyncSession):
        repo = UserRepository(session)
        user = User(email="exists@example.com", password_hash="hash", first_name="Ex", last_name="Ist")
        await repo.create(user)
        assert await repo.exists_by_email("exists@example.com") is True
        assert await repo.exists_by_email("nope@example.com") is False


class TestAuthService:
    async def test_register_success(self, db_session: AsyncSession):
        service = AuthService(db_session)
        result = await service.register("newuser@example.com", "StrongPass1!", "Jane", "Doe")
        assert "user_id" in result
        assert result["email"] == "newuser@example.com"

    async def test_register_duplicate_email(self, db_session: AsyncSession):
        service = AuthService(db_session)
        await service.register("dupe@example.com", "StrongPass1!", "John", "Doe")
        with pytest.raises(ConflictError, match="Email already exists"):
            await service.register("dupe@example.com", "StrongPass2!", "Jane", "Doe")

    async def test_login_success(self, db_session: AsyncSession):
        service = AuthService(db_session)
        await service.register("loginuser@example.com", "StrongPass1!", "Login", "User")
        result = await service.login("loginuser@example.com", "StrongPass1!")
        assert "access_token" in result
        assert "refresh_token" in result
        assert "expires_in" in result
        assert result["token_type"] == "Bearer"
        user = await UserRepository(db_session).get_by_email("loginuser@example.com")
        assert user is not None
        assert user.last_login_at is not None

    async def test_login_invalid_password(self, db_session: AsyncSession):
        service = AuthService(db_session)
        await service.register("badpass@example.com", "StrongPass1!", "Bad", "Pass")
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await service.login("badpass@example.com", "WrongPass1!")

    async def test_login_invalid_email(self, db_session: AsyncSession):
        service = AuthService(db_session)
        with pytest.raises(AuthenticationError, match="Invalid email or password"):
            await service.login("nobody@example.com", "StrongPass1!")

    async def test_login_inactive_user(self, db_session: AsyncSession):
        service = AuthService(db_session)
        await service.register("inactive@example.com", "StrongPass1!", "In", "Active")
        user = await UserRepository(db_session).get_by_email("inactive@example.com")
        user.is_active = False
        await UserRepository(db_session).update(user)
        with pytest.raises(AuthenticationError, match="Account is inactive"):
            await service.login("inactive@example.com", "StrongPass1!")

    async def test_refresh_token_success(self, db_session: AsyncSession):
        service = AuthService(db_session)
        await service.register("refresh@example.com", "StrongPass1!", "Refresh", "Test")
        login_result = await service.login("refresh@example.com", "StrongPass1!")
        refresh_result = await service.refresh_token(login_result["refresh_token"])
        assert "access_token" in refresh_result
        assert "expires_in" in refresh_result

    async def test_refresh_token_invalid(self, db_session: AsyncSession):
        service = AuthService(db_session)
        with pytest.raises(AuthenticationError, match="Invalid or expired refresh token"):
            await service.refresh_token("invalid-token")

    async def test_logout_revokes_tokens(self, db_session: AsyncSession):
        service = AuthService(db_session)
        await service.register("logout@example.com", "StrongPass1!", "Log", "Out")
        login_result = await service.login("logout@example.com", "StrongPass1!")
        user = await UserRepository(db_session).get_by_email("logout@example.com")
        await service.logout(user.id)
        with pytest.raises(AuthenticationError, match="Invalid or expired refresh token"):
            await service.refresh_token(login_result["refresh_token"])

    async def test_change_password_success(self, db_session: AsyncSession):
        service = AuthService(db_session)
        await service.register("changepass@example.com", "StrongPass1!", "Change", "Pass")
        user = await UserRepository(db_session).get_by_email("changepass@example.com")
        await service.change_password(user.id, "StrongPass1!", "NewPass123!")
        result = await service.login("changepass@example.com", "NewPass123!")
        assert "access_token" in result

    async def test_change_password_wrong_current(self, db_session: AsyncSession):
        service = AuthService(db_session)
        await service.register("wrongcurrent@example.com", "StrongPass1!", "Wrong", "Current")
        user = await UserRepository(db_session).get_by_email("wrongcurrent@example.com")
        with pytest.raises(ValidationError, match="Current password is incorrect"):
            await service.change_password(user.id, "WrongPass1!", "NewPass123!")

    async def test_update_profile(self, db_session: AsyncSession):
        service = AuthService(db_session)
        await service.register("update@example.com", "StrongPass1!", "Old", "Name")
        user = await UserRepository(db_session).get_by_email("update@example.com")
        updated = await service.update_profile(user.id, first_name="Updated", last_name="User")
        assert updated.first_name == "Updated"
        assert updated.last_name == "User"

    async def test_update_profile_partial(self, db_session: AsyncSession):
        service = AuthService(db_session)
        await service.register("partial@example.com", "StrongPass1!", "Original", "Name")
        user = await UserRepository(db_session).get_by_email("partial@example.com")
        updated = await service.update_profile(user.id, first_name="OnlyFirst")
        assert updated.first_name == "OnlyFirst"
        assert updated.last_name == "Name"

    async def test_get_current_user(self, db_session: AsyncSession):
        service = AuthService(db_session)
        await service.register("getme@example.com", "StrongPass1!", "Get", "Me")
        user = await UserRepository(db_session).get_by_email("getme@example.com")
        found = await service.get_current_user(user.id)
        assert found.email == "getme@example.com"

    async def test_get_current_user_not_found(self, db_session: AsyncSession):
        service = AuthService(db_session)
        with pytest.raises(NotFoundError, match="User not found"):
            await service.get_current_user(uuid.uuid4())

    async def test_delete_account(self, db_session: AsyncSession):
        service = AuthService(db_session)
        await service.register("delete@example.com", "StrongPass1!", "Delete", "Account")
        user = await UserRepository(db_session).get_by_email("delete@example.com")
        await service.delete_account(user.id)
        user = await UserRepository(db_session).get_by_email("delete@example.com")
        assert user.is_active is False
        assert user.deleted_at is not None


class TestJWTToken:
    def test_create_and_decode_access_token(self):
        subject = str(uuid.uuid4())
        token = create_access_token(subject=subject)
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == subject
        assert "exp" in payload

    def test_expired_token(self):
        from jose import jwt

        from app.core.config import settings

        expired = jwt.encode(
            {
                "sub": str(uuid.uuid4()),
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            },
            settings.APP_SECRET_KEY,
            algorithm="HS256",
        )
        payload = decode_access_token(expired)
        assert payload is None

    def test_invalid_signature(self):
        from jose import jwt

        token = jwt.encode(
            {"sub": str(uuid.uuid4()), "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
            "wrong-secret",
            algorithm="HS256",
        )
        payload = decode_access_token(token)
        assert payload is None

    def test_create_refresh_token_is_urlsafe(self):
        token = create_refresh_token()
        assert len(token) > 0
        assert all(c.isalnum() or c in "-_" for c in token)


class TestAuthAPI:
    @pytest_asyncio.fixture
    async def api_client(self, db_session: AsyncSession):
        app = FastAPI()
        app.include_router(auth_router, prefix="/auth")

        async def _override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = _override_get_db

        @app.exception_handler(AuthenticationError)
        async def auth_error_handler(request, exc):
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": str(exc)})

        @app.exception_handler(ConflictError)
        async def conflict_error_handler(request, exc):
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})

        @app.exception_handler(NotFoundError)
        async def not_found_handler(request, exc):
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})

        @app.exception_handler(ValidationError)
        async def validation_handler(request, exc):
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    async def _register(self, api_client: AsyncClient, email: str, password: str = "StrongPass1!"):
        return await api_client.post(
            "/auth/register",
            json={"email": email, "password": password, "first_name": "T", "last_name": "U"},
        )

    async def _login(self, api_client: AsyncClient, email: str, password: str = "StrongPass1!"):
        return await api_client.post("/auth/login", json={"email": email, "password": password})

    async def test_register_endpoint(self, api_client: AsyncClient):
        resp = await self._register(api_client, "api_test@example.com")
        assert resp.status_code == 201
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["email"] == "api_test@example.com"

    async def test_register_duplicate(self, api_client: AsyncClient):
        await self._register(api_client, "apidupe@example.com")
        resp = await self._register(api_client, "apidupe@example.com", "StrongPass2!")
        assert resp.status_code == 409

    async def test_register_weak_password(self, api_client: AsyncClient):
        resp = await api_client.post(
            "/auth/register",
            json={"email": "weak@example.com", "password": "weak", "first_name": "A", "last_name": "B"},
        )
        assert resp.status_code == 422

    async def test_login_endpoint(self, api_client: AsyncClient):
        await self._register(api_client, "login_api@example.com")
        resp = await self._login(api_client, "login_api@example.com")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    async def test_login_invalid_password(self, api_client: AsyncClient):
        await self._register(api_client, "badpw_api@example.com")
        resp = await api_client.post("/auth/login", json={"email": "badpw_api@example.com", "password": "WrongPass1!"})
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, api_client: AsyncClient):
        resp = await api_client.post("/auth/login", json={"email": "noone@example.com", "password": "StrongPass1!"})
        assert resp.status_code == 401

    async def test_me_authenticated(self, api_client: AsyncClient):
        await self._register(api_client, "me_api@example.com")
        login_resp = await self._login(api_client, "me_api@example.com")
        token = login_resp.json()["data"]["access_token"]
        resp = await api_client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["email"] == "me_api@example.com"

    async def test_me_unauthenticated(self, api_client: AsyncClient):
        resp = await api_client.get("/auth/me")
        assert resp.status_code == 401

    async def test_me_invalid_token(self, api_client: AsyncClient):
        resp = await api_client.get("/auth/me", headers={"Authorization": "Bearer invalid-token"})
        assert resp.status_code == 401

    async def test_refresh_endpoint(self, api_client: AsyncClient):
        await self._register(api_client, "refresh_api@example.com")
        login_resp = await self._login(api_client, "refresh_api@example.com")
        refresh_token = login_resp.json()["data"]["refresh_token"]
        resp = await api_client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "access_token" in data["data"]

    async def test_refresh_invalid_token(self, api_client: AsyncClient):
        resp = await api_client.post("/auth/refresh", json={"refresh_token": "invalid-token-value"})
        assert resp.status_code == 401

    async def test_protected_endpoint_with_expired_token(self, api_client: AsyncClient):
        expired_token = create_access_token(subject=str(uuid.uuid4()), expires_delta=timedelta(seconds=-1))
        resp = await api_client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert resp.status_code == 401

    async def test_logout_revokes_tokens(self, api_client: AsyncClient):
        await self._register(api_client, "logout_api@example.com")
        login_resp = await self._login(api_client, "logout_api@example.com")
        token = login_resp.json()["data"]["access_token"]
        refresh_token = login_resp.json()["data"]["refresh_token"]
        await api_client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
        refresh_resp = await api_client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert refresh_resp.status_code == 401
