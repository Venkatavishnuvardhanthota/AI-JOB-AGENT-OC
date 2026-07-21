from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def create_engine(db_url: str | None = None, echo: bool = False) -> AsyncEngine:
    from app.core.config import settings

    url = db_url or settings.DATABASE_URL
    return create_async_engine(
        url,
        echo=echo or settings.APP_DEBUG,
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )


_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine
