import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_create_user(session: AsyncSession):
    user = User(
        email="db_test@example.com",
        hashed_password="hashed_pw_placeholder",
        full_name="DB Test User",
    )
    session.add(user)
    await session.flush()
    await session.refresh(user)

    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)
    assert user.email == "db_test@example.com"
    assert user.is_active is True
    assert user.is_superuser is False
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.asyncio
async def test_user_unique_email(session: AsyncSession):
    user1 = User(
        email="unique@example.com",
        hashed_password="hash1",
    )
    session.add(user1)
    await session.flush()

    user2 = User(
        email="unique@example.com",
        hashed_password="hash2",
    )
    session.add(user2)
    with pytest.raises(Exception):
        await session.flush()


@pytest.mark.asyncio
async def test_user_repr(session: AsyncSession):
    user = User(
        email="repr@example.com",
        hashed_password="hash",
    )
    session.add(user)
    await session.flush()

    assert "repr@example.com" in repr(user)
