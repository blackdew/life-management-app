"""
여정 Pydantic 스키마 정의

API 요청/응답에 사용되는 데이터 모델들을 정의합니다.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from ..models.journey import JourneyStatus


class JourneyBase(BaseModel):
    """여정 기본 스키마"""

    title: str = Field(..., min_length=1, max_length=100, description="여정 제목")
    description: Optional[str] = Field(
        None, max_length=500, description="여정 설명"
    )
    start_date: date = Field(..., description="시작일")
    end_date: date = Field(..., description="종료일")
    status: JourneyStatus = Field(
        default=JourneyStatus.PLANNING, description="상태"
    )


class JourneyCreate(JourneyBase):
    """여정 생성 스키마"""

    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="진행률 (0-100)")


class JourneyUpdate(BaseModel):
    """여정 수정 스키마"""

    title: Optional[str] = Field(
        None, min_length=1, max_length=100, description="여정 제목"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="여정 설명"
    )
    start_date: Optional[date] = Field(None, description="시작일")
    end_date: Optional[date] = Field(None, description="종료일")
    status: Optional[JourneyStatus] = Field(None, description="상태")
    progress: Optional[float] = Field(
        None, ge=0.0, le=100.0, description="진행률 (0-100)"
    )


class JourneyResponse(JourneyBase):
    """여정 응답 스키마"""

    id: int = Field(..., description="여정 ID")
    progress: float = Field(..., ge=0.0, le=100.0, description="진행률 (0-100)")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    model_config = ConfigDict(from_attributes=True)


class JourneyListResponse(BaseModel):
    """여정 목록 응답 스키마"""

    journeys: list[JourneyResponse]
    total: int = Field(..., description="전체 여정 수")

    model_config = ConfigDict(from_attributes=True)