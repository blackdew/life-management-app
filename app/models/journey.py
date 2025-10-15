from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    Date,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class JourneyStatus(Enum):
    PLANNING = "계획중"
    ACTIVE = "진행중"
    COMPLETED = "완료"
    PAUSED = "일시중지"


class Journey(Base):
    __tablename__ = "journeys"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, comment="여정 제목")
    description = Column(Text, nullable=True, comment="여정 상세 설명")
    start_date = Column(Date, nullable=False, comment="시작 예정일")
    end_date = Column(Date, nullable=False, comment="종료 예정일")
    status: Column[JourneyStatus] = Column(
        SQLEnum(JourneyStatus), default=JourneyStatus.PLANNING, comment="진행 상태"
    )
    # DEPRECATED: 이 필드는 더 이상 사용되지 않습니다. calculate_actual_progress() 메서드를 사용하세요.
    # TODO: 향후 버전에서 제거 예정
    progress = Column(Float, default=0.0, comment="진행률 (0-100) - DEPRECATED: 실시간 계산 대신 calculate_actual_progress() 사용")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), comment="생성일시"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
        comment="수정일시",
    )

    # Relationships
    todos = relationship(
        "Todo", back_populates="journey", cascade="all, delete-orphan"
    )
    daily_todos = relationship(
        "DailyTodo", back_populates="journey", cascade="all, delete-orphan"
    )

    def calculate_actual_progress(self) -> float:
        """실제 할일 완료도를 기반으로 진행률을 계산합니다."""
        total_todos = 0
        completed_todos = 0

        # Todo 테이블에서 완료도 계산
        for todo in self.todos:
            total_todos += 1
            if todo.is_completed:
                completed_todos += 1

        # DailyTodo 테이블에서 완료도 계산
        for daily_todo in self.daily_todos:
            total_todos += 1
            if daily_todo.is_completed:
                completed_todos += 1

        if total_todos == 0:
            return 0.0

        return round((completed_todos / total_todos) * 100, 1)


    def __repr__(self) -> str:
        return f"<Journey(id={self.id}, title='{self.title}', status='{self.status.value}', progress={self.progress})>"