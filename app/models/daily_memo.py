"""
일일 메모 모델

날짜별로 사용자가 기록하는 간단한 메모들을 저장하는 모델입니다.
할일이나 마일스톤과는 독립적으로 운영되며, 순수하게 날짜 기반으로만 관리됩니다.
"""

from datetime import date
from sqlalchemy import Column, Integer, Text, Date, DateTime
from sqlalchemy.sql import func

from app.core.database import Base
from app.core.timezone import get_current_date


class DailyMemo(Base):
    """일일 메모 모델"""
    __tablename__ = "daily_memos"

    id = Column(Integer, primary_key=True, index=True)
    memo_date = Column(Date, nullable=False, comment="메모 날짜")
    content = Column(Text, nullable=False, comment="메모 내용")

    # 메타데이터
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="생성 시간"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
        comment="수정 시간"
    )

    def __repr__(self) -> str:
        """메모 문자열 표현"""
        content_preview = self.content[:30] + "..." if len(self.content) > 30 else self.content
        return f"<DailyMemo(date={self.memo_date}, content='{content_preview}')>"

    def __str__(self) -> str:
        """사용자 친화적 문자열 표현"""
        return f"{self.memo_date}: {self.content}"

    @property
    def is_today(self) -> bool:
        """오늘 날짜의 메모인지 확인"""
        return self.memo_date == get_current_date()

    @property
    def content_length(self) -> int:
        """메모 내용 길이"""
        return len(self.content) if self.content else 0