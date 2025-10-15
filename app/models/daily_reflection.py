from sqlalchemy import Column, Integer, Text, Date, DateTime, Float, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class DailyReflection(Base):
    """일일 회고 모델"""
    __tablename__ = "daily_reflections"

    id = Column(Integer, primary_key=True, index=True)
    reflection_date = Column(Date, nullable=False, unique=True, comment="회고 날짜")
    reflection_text = Column(Text, nullable=False, comment="회고 내용")

    # 오늘의 성과 데이터
    total_todos = Column(Integer, default=0, comment="총 할 일 개수")
    completed_todos = Column(Integer, default=0, comment="완료한 할 일 개수")
    completion_rate = Column(Float, default=0.0, comment="완료율 (%)")

    # 할일 목록 상세 정보 (JSON 형태로 저장)
    todos_snapshot = Column(JSON, nullable=True, comment="회고 시점의 할일 목록 스냅샷")

    # 감정/만족도 점수 (1-5)
    satisfaction_score = Column(Integer, nullable=True, comment="만족도 점수 (1-5)")
    energy_level = Column(Integer, nullable=True, comment="에너지 레벨 (1-5)")

    # LLM 생성 블로그 글 관련 필드
    generated_blog_content = Column(Text, nullable=True, comment="LLM이 생성한 블로그 글 내용")
    blog_generation_prompt = Column(Text, nullable=True, comment="블로그 글 생성에 사용된 프롬프트")
    blog_generated_at = Column(DateTime(timezone=True), nullable=True, comment="블로그 글 생성 시간")

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), comment="생성 시간")
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now(), comment="수정 시간")

    def __repr__(self):
        return f"<DailyReflection(date={self.reflection_date}, completion_rate={self.completion_rate}%)>"