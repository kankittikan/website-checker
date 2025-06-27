from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import async_sessionmaker
from datetime import datetime

# Database URL
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./websites.db"

# Create async engine
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Website model
class Website(Base):
    __tablename__ = "websites"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(unique=True, index=True)
    status: Mapped[bool] = mapped_column(default=False)
    last_checked: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    notify_on_down: Mapped[bool] = mapped_column(default=False)
    last_notification_sent: Mapped[datetime] = mapped_column(nullable=True)

# Async context manager for database sessions
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Create tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 