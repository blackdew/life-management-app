"""
LLM 블로그 생성 관련 Pydantic 스키마
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class BlogGenerationRequest(BaseModel):
    """블로그 글 생성 요청 스키마"""
    provider: str = Field(..., description="LLM 제공업체 (openai, claude)")
    include_images: bool = Field(default=True, description="이미지 포함 여부")
    additional_prompt: Optional[str] = Field(None, description="추가 프롬프트")


class BlogGenerationResponse(BaseModel):
    """블로그 글 생성 응답 스키마"""
    content: str = Field(..., description="생성된 블로그 글 내용")
    is_cached: bool = Field(..., description="캐시된 콘텐츠 여부")
    generated_at: datetime = Field(..., description="생성 시간")


class BlogContentResponse(BaseModel):
    """저장된 블로그 콘텐츠 조회 응답 스키마"""
    content: str = Field(..., description="저장된 블로그 글 내용")
    generated_at: Optional[datetime] = Field(None, description="생성 시간")
    prompt: Optional[str] = Field(None, description="사용된 프롬프트")