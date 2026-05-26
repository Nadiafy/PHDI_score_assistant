import uuid
from sqlalchemy import Column, String, Float, Date, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    daily_logs = relationship("DailyLog", back_populates="user", cascade="all, delete-orphan")

class DailyLog(Base):
    __tablename__ = "daily_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    raw_text_log = Column(String, nullable=True)
    total_phdi_score = Column(Float, nullable=False, default=0.0)
    component_scores = Column(JSONB, nullable=False, default={})
    source = Column(String, nullable=False) # 'web' or 'telegram'
    
    user = relationship("User", back_populates="daily_logs")
