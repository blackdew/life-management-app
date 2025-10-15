from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Form, Query
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.daily_reflection import DailyReflection
from app.services.daily_reflection_service import DailyReflectionService
from app.services.llm_blog_service import LLMBlogService, LLMProvider
from app.schemas.llm_blog import BlogGenerationRequest, BlogGenerationResponse, BlogContentResponse

router = APIRouter(prefix="/api/reflections", tags=["일일 회고"])
templates = Jinja2Templates(directory="app/templates")


@router.post("/", response_model=dict)
async def create_reflection(
    reflection_date: str = Form(),
    reflection_text: str = Form(),
    satisfaction_score: Optional[int] = Form(None),
    energy_level: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """일일 회고 생성"""
    try:
        # 날짜 파싱
        reflection_date_obj = datetime.strptime(reflection_date, "%Y-%m-%d").date()

        # 점수 검증
        if satisfaction_score is not None and not (1 <= satisfaction_score <= 5):
            raise HTTPException(status_code=400, detail="만족도 점수는 1-5 사이여야 합니다")
        if energy_level is not None and not (1 <= energy_level <= 5):
            raise HTTPException(status_code=400, detail="에너지 레벨은 1-5 사이여야 합니다")

        reflection = DailyReflectionService.create_reflection(
            db=db,
            reflection_date=reflection_date_obj,
            reflection_text=reflection_text.strip(),
            satisfaction_score=satisfaction_score,
            energy_level=energy_level
        )

        return {
            "id": reflection.id,
            "reflection_date": reflection.reflection_date.isoformat(),
            "reflection_text": reflection.reflection_text,
            "completion_rate": reflection.completion_rate,
            "total_todos": reflection.total_todos,
            "completed_todos": reflection.completed_todos,
            "satisfaction_score": reflection.satisfaction_score,
            "energy_level": reflection.energy_level
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="올바른 날짜 형식이 아닙니다 (YYYY-MM-DD)")
    except HTTPException:
        raise  # HTTPException은 그대로 re-raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"회고 저장 중 오류가 발생했습니다: {str(e)}")


@router.get("/date/{reflection_date}")
async def get_reflection_by_date(
    reflection_date: str,
    db: Session = Depends(get_db)
):
    """특정 날짜의 회고 조회"""
    try:
        reflection_date_obj = datetime.strptime(reflection_date, "%Y-%m-%d").date()
        reflection = DailyReflectionService.get_reflection_by_date(db, reflection_date_obj)

        if not reflection:
            return {"message": "해당 날짜의 회고가 없습니다"}

        return {
            "id": reflection.id,
            "reflection_date": reflection.reflection_date.isoformat(),
            "reflection_text": reflection.reflection_text,
            "completion_rate": reflection.completion_rate,
            "total_todos": reflection.total_todos,
            "completed_todos": reflection.completed_todos,
            "satisfaction_score": reflection.satisfaction_score,
            "energy_level": reflection.energy_level,
            "created_at": reflection.created_at.isoformat() if reflection.created_at else None,
            "todos_snapshot": reflection.todos_snapshot
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="올바른 날짜 형식이 아닙니다 (YYYY-MM-DD)")


@router.get("/recent")
async def get_recent_reflections(
    limit: int = 30,
    db: Session = Depends(get_db)
):
    """최근 회고 목록 조회"""
    reflections = DailyReflectionService.get_recent_reflections(db, limit)

    return {
        "reflections": [
            {
                "id": r.id,
                "reflection_date": r.reflection_date.isoformat(),
                "reflection_text": r.reflection_text[:100] + "..." if len(r.reflection_text) > 100 else r.reflection_text,
                "completion_rate": r.completion_rate,
                "total_todos": r.total_todos,
                "completed_todos": r.completed_todos,
                "satisfaction_score": r.satisfaction_score,
                "energy_level": r.energy_level
            }
            for r in reflections
        ]
    }


@router.get("/stats")
async def get_reflection_stats(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """회고 통계 조회"""
    stats = DailyReflectionService.get_stats_summary(db, days)
    return stats


@router.delete("/date/{reflection_date}")
async def delete_reflection(
    reflection_date: str,
    db: Session = Depends(get_db)
):
    """회고 삭제"""
    try:
        reflection_date_obj = datetime.strptime(reflection_date, "%Y-%m-%d").date()
        success = DailyReflectionService.delete_reflection(db, reflection_date_obj)

        if success:
            return {"message": "회고가 삭제되었습니다"}
        else:
            raise HTTPException(status_code=404, detail="해당 날짜의 회고를 찾을 수 없습니다")

    except ValueError:
        raise HTTPException(status_code=400, detail="올바른 날짜 형식이 아닙니다 (YYYY-MM-DD)")



# LLM 블로그 글 생성 관련 엔드포인트

@router.post("/{reflection_id}/generate-blog", response_model=BlogGenerationResponse)
async def generate_blog_content(
    reflection_id: int,
    request: BlogGenerationRequest,
    db: Session = Depends(get_db)
):
    """회고를 바탕으로 LLM을 이용해 블로그 글을 생성합니다"""
    try:
        # LLM 제공업체 검증
        provider = LLMProvider(request.provider)

        # 블로그 글 생성
        result = await LLMBlogService.generate_blog_content(
            reflection_id=reflection_id,
            db=db,
            provider=provider,
            include_images=request.include_images,
            additional_prompt=request.additional_prompt
        )

        return BlogGenerationResponse(
            content=result["content"],
            is_cached=result["is_cached"],
            generated_at=result["generated_at"]
        )

    except ValueError as e:
        if "회고를 찾을 수 없습니다" in str(e):
            raise HTTPException(status_code=404, detail="회고를 찾을 수 없습니다")
        else:
            raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # OpenAI/Claude API 오류가 HTTP status code를 포함하고 있는지 확인
        error_msg = str(e)
        if "400:" in error_msg and "API 키가 유효하지 않습니다" in error_msg:
            raise HTTPException(status_code=400, detail="API 키가 유효하지 않습니다")
        else:
            raise HTTPException(status_code=500, detail=f"블로그 글 생성 실패: {str(e)}")


@router.post("/{reflection_id}/regenerate-blog", response_model=BlogGenerationResponse)
async def regenerate_blog_content(
    reflection_id: int,
    request: BlogGenerationRequest,
    db: Session = Depends(get_db)
):
    """기존 블로그 글을 강제로 재생성합니다"""
    try:
        # LLM 제공업체 검증
        provider = LLMProvider(request.provider)

        # 블로그 글 강제 재생성
        result = await LLMBlogService.generate_blog_content(
            reflection_id=reflection_id,
            db=db,
            provider=provider,
            include_images=request.include_images,
            force_regenerate=True,  # 강제 재생성
            additional_prompt=request.additional_prompt
        )

        return BlogGenerationResponse(
            content=result["content"],
            is_cached=result["is_cached"],
            generated_at=result["generated_at"]
        )

    except ValueError as e:
        if "회고를 찾을 수 없습니다" in str(e):
            raise HTTPException(status_code=404, detail="회고를 찾을 수 없습니다")
        else:
            raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        # OpenAI/Claude API 오류가 HTTP status code를 포함하고 있는지 확인
        error_msg = str(e)
        if "400:" in error_msg and "API 키가 유효하지 않습니다" in error_msg:
            raise HTTPException(status_code=400, detail="API 키가 유효하지 않습니다")
        else:
            raise HTTPException(status_code=500, detail=f"블로그 글 생성 실패: {str(e)}")


@router.get("/{reflection_id}/blog-content", response_model=BlogContentResponse)
async def get_blog_content(
    reflection_id: int,
    db: Session = Depends(get_db)
):
    """저장된 블로그 콘텐츠를 조회합니다"""
    try:
        # 회고 존재 여부 확인
        reflection = db.query(DailyReflection).filter(
            DailyReflection.id == reflection_id
        ).first()

        if not reflection:
            raise HTTPException(status_code=404, detail="회고를 찾을 수 없습니다")

        # 캐시된 블로그 콘텐츠 조회
        cached_content = LLMBlogService.get_cached_blog_content(reflection_id, db)
        if not cached_content:
            raise HTTPException(status_code=404, detail="생성된 블로그 글이 없습니다")

        return BlogContentResponse(
            content=cached_content["content"],
            generated_at=cached_content["generated_at"],
            prompt=cached_content["prompt"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"블로그 콘텐츠 조회 실패: {str(e)}")


# 페이지 라우터들 - 레거시 /reflections 페이지 리다이렉트 추가
page_router = APIRouter()

@page_router.get("/reflections", response_class=HTMLResponse)
async def reflections_redirect():
    """레거시 /reflections 페이지를 /reflection-history로 리다이렉트"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/reflection-history", status_code=301)


