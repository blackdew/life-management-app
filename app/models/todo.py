from datetime import datetime, date
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Date,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base
from ..core.timezone import get_current_utc_datetime, get_current_date


class TodoCategory(Enum):
    WORK = "업무"
    LEARNING = "학습"
    HEALTH = "건강"
    PERSONAL = "개인"
    RELATIONSHIP = "관계"
    OTHER = "기타"


class TodoStatus(Enum):
    TODO = "할일"
    IN_PROGRESS = "진행중"
    COMPLETED = "완료"
    CANCELLED = "취소"


class TodoPriority(Enum):
    LOW = "낮음"
    NORMAL = "보통"
    HIGH = "높음"
    URGENT = "긴급"


class DailyTodo(Base):
    """일상 중심의 Todo 모델"""
    __tablename__ = "daily_todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="할 일 제목")
    description = Column(Text, nullable=True, comment="상세 내용")
    notes = Column(Text, nullable=True, comment="간단한 메모")
    category = Column(
        SQLEnum(TodoCategory), default=TodoCategory.OTHER, comment="카테고리 (선택적)"
    )

    # 완료 관련
    is_completed = Column(Boolean, default=False, comment="완료 여부")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="완료 시각")
    completion_reflection = Column(Text, nullable=True, comment="완료 후 회고")
    completion_image_path = Column(String(500), nullable=True, comment="완료 회고 이미지 경로")

    # 날짜 관련
    created_date = Column(Date, default=func.current_date(), comment="생성 날짜")
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), comment="생성 시각"
    )
    scheduled_date = Column(Date, nullable=True, comment="예정 일자 (미루기용)")

    # 시간 기록 (선택적)
    estimated_minutes = Column(Integer, nullable=True, comment="예상 소요시간 (분)")
    actual_minutes = Column(Integer, nullable=True, comment="실제 소요시간 (분)")

    # 미루기 관련
    postpone_count = Column(Integer, default=0, comment="미루기 횟수")
    postpone_history = Column(Text, nullable=True, comment="미루기 히스토리 (JSON)")

    # 여정 연결
    journey_id = Column(
        Integer, ForeignKey("journeys.id"), nullable=True, comment="연관 여정 ID"
    )

    # Relationships
    journey = relationship("Journey", back_populates="daily_todos")

    # 프로젝트 연결 (선택적) - 일상 관리에서는 사용하지 않음
    # project_id = Column(
    #     Integer, ForeignKey("journeys.id"), nullable=True, comment="연관 프로젝트 ID"
    # )

    def __repr__(self) -> str:
        return f"<DailyTodo(id={self.id}, title='{self.title}', completed={self.is_completed}, date={self.created_date})>"

    @property
    def is_today(self) -> bool:
        """오늘 생성된 할 일인지 확인"""
        return self.created_date == get_current_date()

    def complete(self) -> None:
        """할 일 완료 처리"""
        self.is_completed = True
        self.completed_at = get_current_utc_datetime()

    def uncomplete(self) -> None:
        """할 일 완료 취소"""
        self.is_completed = False
        self.completed_at = None


# 기존 Todo 모델도 유지 (호환성을 위해)
class Todo(Base):
    """기존 Todo 모델 (별도 테이블로 유지)"""
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, comment="할 일 제목")
    description = Column(Text, nullable=True, comment="상세 설명")

    # 상태 및 우선순위
    status = Column(
        SQLEnum(TodoStatus), default=TodoStatus.TODO, comment="할일 상태"
    )
    priority = Column(
        SQLEnum(TodoPriority), default=TodoPriority.NORMAL, comment="우선순위"
    )
    category = Column(
        SQLEnum(TodoCategory), default=TodoCategory.OTHER, comment="카테고리"
    )

    # 완료 관련
    is_completed = Column(Boolean, default=False, comment="완료 여부")
    completed_at = Column(DateTime(timezone=True), nullable=True, comment="완료 시각")

    # 날짜 관련
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), comment="생성 시각"
    )

    # 시간 추정
    estimated_time = Column(Integer, nullable=True, comment="예상 소요시간 (분)")
    actual_time = Column(Integer, nullable=True, comment="실제 소요시간 (분)")

    # 여정 연결
    journey_id = Column(
        Integer, ForeignKey("journeys.id"), nullable=True, comment="여정 ID"
    )

    # Relationships
    journey = relationship("Journey", back_populates="todos")

    def __repr__(self) -> str:
        return f"<Todo(id={self.id}, title='{self.title}', completed={self.is_completed})>"

    def complete(self) -> None:
        """할 일 완료 처리"""
        self.is_completed = True
        self.completed_at = get_current_utc_datetime()

    def uncomplete(self) -> None:
        """할 일 완료 취소"""
        self.is_completed = False
        self.completed_at = None
