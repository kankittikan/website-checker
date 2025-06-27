from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import async_sessionmaker
from datetime import datetime, UTC
from sqlalchemy import ForeignKey
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

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
Base = declarative_base()

# Website model
class Website(Base):
    __tablename__ = "websites"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(unique=True, index=True)
    status: Mapped[bool] = mapped_column(default=True)
    notify_on_down: Mapped[bool] = mapped_column(default=False)  # Changed default to False
    last_checked: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    last_notification_sent: Mapped[datetime] = mapped_column(nullable=True)
    server_info_id: Mapped[int] = mapped_column(ForeignKey("server_info.id"), nullable=True)
    server_info: Mapped["ServerInfo"] = relationship("ServerInfo", back_populates="website")

# Server Info model
class ServerInfo(Base):
    __tablename__ = "server_info"

    id: Mapped[int] = mapped_column(primary_key=True)
    host: Mapped[str] = mapped_column(index=True)
    username: Mapped[str]
    ssh_key_path: Mapped[str] = mapped_column(nullable=True)
    password: Mapped[str] = mapped_column(nullable=True)
    cpu_usage: Mapped[float] = mapped_column(nullable=True)
    ram_usage: Mapped[float] = mapped_column(nullable=True)
    disk_usage: Mapped[float] = mapped_column(nullable=True)
    last_checked: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    last_cpu_alert: Mapped[datetime] = mapped_column(nullable=True)
    last_ram_alert: Mapped[datetime] = mapped_column(nullable=True)
    last_disk_alert: Mapped[datetime] = mapped_column(nullable=True)
    website: Mapped["Website"] = relationship("Website", back_populates="server_info")

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
    await engine.dispose()

# Create tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all) 