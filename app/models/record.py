from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, Date, DateTime, Integer, String, Text, Enum as SQLEnum
from sqlalchemy.sql import func

from ..core.database import Base


class EnergyLevel(Enum):
    VERY_LOW = 1
    LOW = 2
    NORMAL = 3
    HIGH = 4
    VERY_HIGH = 5


class DailyRecord(Base):
    __tablename__ = "daily_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, comment="기록 날짜")
    reflection = Column(Text, nullable=True, comment="하루 성찰 내용")
    gratitude = Column(Text, nullable=True, comment="감사한 일들")
    energy_level: Column[EnergyLevel] = Column(
        SQLEnum(EnergyLevel), default=EnergyLevel.NORMAL, comment="에너지 레벨"
    )
    meta_cognitive_notes = Column(
        Text, nullable=True, comment="메타인지 노트 (자기 관찰, 도파민 패턴 등)"
    )

    # 추가 필드들 (확장 가능)
    mood_note = Column(String(500), nullable=True, comment="기분 메모")
    key_learnings = Column(Text, nullable=True, comment="주요 배운 점들")
    tomorrow_focus = Column(Text, nullable=True, comment="내일 집중할 것들")

    created_at = Column(
        DateTime(timezone=True), nullable=False, comment="생성일시"
    )

    def __repr__(self) -> str:
        return f"<DailyRecord(id={self.id}, date='{self.date}', energy_level={self.energy_level})>"
