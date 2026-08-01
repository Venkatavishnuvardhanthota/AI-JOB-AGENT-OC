"""Seed script: populates the database with demo data for development.

Usage:
    python -m scripts.seed
    python -m scripts.seed --drop-first   # Drops existing data before seeding
"""

import argparse
import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from database.base import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ENGINE = create_async_engine(settings.DATABASE_URL, echo=False)
SESSION_FACTORY = async_sessionmaker(ENGINE, class_=AsyncSession, expire_on_commit=False)

NOW = datetime.now(timezone.utc)


async def drop_all():
    async with ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    print("Dropped all tables.")


async def create_tables():
    async with ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Created all tables.")


async def seed():
    async with SESSION_FACTORY() as session:
        user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

        existing = await session.execute(text("SELECT id FROM users WHERE id = :id"), {"id": user_id})
        if existing.scalar():
            print("Demo user already exists. Skipping seed.")
            return

        # ── User ──
        await session.execute(
            text("""
                INSERT INTO users (id, email, password_hash, first_name, last_name, is_active, is_verified, is_admin, created_at, updated_at)
                VALUES (:id, :email, :pwd, :first, :last, true, true, false, :now, :now)
            """),
            {
                "id": user_id,
                "email": "demo@example.com",
                "pwd": pwd_context.hash("demo1234"),
                "first": "Demo",
                "last": "User",
                "now": NOW,
            },
        )
        print("  Created demo user: demo@example.com / demo1234")

        # ── Career Profile ──
        profile_id = uuid.uuid4()
        await session.execute(
            text("""
                INSERT INTO career_profiles (id, user_id, headline, summary, created_at, updated_at)
                VALUES (:id, :uid, :headline, :summary, :now, :now)
            """),
            {
                "id": profile_id,
                "uid": user_id,
                "headline": "Senior Full-Stack Engineer",
                "summary": "Experienced full-stack engineer with 8+ years building scalable web applications.",
                "now": NOW,
            },
        )
        print("  Created career profile")

        # ── Skills ──
        skills = ["Python", "TypeScript", "FastAPI", "React", "PostgreSQL", "Docker", "AWS", "GraphQL"]
        for skill in skills:
            await session.execute(
                text("""
                    INSERT INTO skills (id, profile_id, name, category, proficiency, created_at, updated_at)
                    VALUES (:id, :pid, :name, :cat, :prof, :now, :now)
                """),
                {
                    "id": uuid.uuid4(),
                    "pid": profile_id,
                    "name": skill,
                    "cat": "Technical",
                    "prof": 4,
                    "now": NOW,
                },
            )
        print(f"  Added {len(skills)} skills")

        # ── Experience ──
        await session.execute(
            text("""
                INSERT INTO experiences (id, profile_id, job_title, company, start_date, end_date, description, created_at, updated_at)
                VALUES (:id, :pid, :title, :company, :start, :end, :desc, :now, :now)
            """),
            {
                "id": uuid.uuid4(),
                "pid": profile_id,
                "title": "Senior Software Engineer",
                "company": "TechCo Inc.",
                "start": NOW - timedelta(days=365 * 2),
                "end": NOW,
                "desc": "Led backend team, designed microservices architecture, improved API response times by 40%.",
                "now": NOW,
            },
        )
        print("  Added experience entry")

        # ── Sample Jobs ──
        jobs = [
            {
                "id": uuid.uuid4(),
                "title": "Senior Backend Engineer",
                "company": "Acme Corp",
                "description": "Build and maintain distributed systems powering our SaaS platform.",
                "url": "https://example.com/jobs/1",
            },
            {
                "id": uuid.uuid4(),
                "title": "Full-Stack Developer",
                "company": "StartupXYZ",
                "description": "Join a fast-moving team building the next-gen analytics dashboard.",
                "url": "https://example.com/jobs/2",
            },
        ]
        for job in jobs:
            await session.execute(
                text("""
                    INSERT INTO jobs (id, title, company, description, url, source, is_active, created_at, updated_at)
                    VALUES (:id, :title, :company, :desc, :url, 'seed', true, :now, :now)
                """),
                {**job, "now": NOW},
            )
        print(f"  Added {len(jobs)} sample jobs")

        # ── AI Config ──
        await session.execute(
            text("""
                INSERT INTO user_preferences (id, user_id, preferences, created_at, updated_at)
                VALUES (:id, :uid, :prefs, :now, :now)
            """),
            {
                "id": uuid.uuid4(),
                "uid": user_id,
                "prefs": '{"ai_default_provider": "openrouter", "ai_default_model": "gpt-4o"}',
                "now": NOW,
            },
        )
        print("  Created AI configuration preference")

        await session.commit()
        print("\nSeed complete! Login with: demo@example.com / demo1234")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--drop-first", action="store_true", help="Drop all tables before seeding")
    args = parser.parse_args()

    if args.drop_first:
        await drop_all()
    await create_tables()
    await seed()
    await ENGINE.dispose()


if __name__ == "__main__":
    asyncio.run(main())
