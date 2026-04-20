# rule.py
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    app_id: Mapped[int] = mapped_column(ForeignKey("apps.id"), index=True)

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=100)

    http_method: Mapped[str | None] = mapped_column(String(16), nullable=True)
    host_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    path_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)

    action_type: Mapped[str] = mapped_column(String(50))
    action_config: Mapped[dict] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    app = relationship("App", back_populates="rules")