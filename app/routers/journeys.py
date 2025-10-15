"""
여정 API 라우터

여정 관련 CRUD API 엔드포인트를 제공합니다.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import date

from ..core.database import get_db
from ..models.journey import Journey
from ..schemas.journey import (
    JourneyCreate,
    JourneyUpdate,
    JourneyResponse,
    JourneyListResponse,
)

router = APIRouter(prefix="/journeys", tags=["여정"])
templates = Jinja2Templates(directory="app/templates")


# T1-15: 웹 UI 인터랙션을 위한 HTMX 엔드포인트들 (경로 충돌 방지를 위해 앞에 배치)

@router.get("/new", response_class=HTMLResponse)
async def get_journey_new_form(request: Request) -> HTMLResponse:
    """새 여정 생성 폼을 반환합니다 (HTMX용)."""
    return templates.TemplateResponse(request, "forms/journey_new_form.html")


@router.get("/", response_model=JourneyListResponse)
async def get_all_journeys(db: Session = Depends(get_db)) -> JourneyListResponse:
    """모든 여정 목록을 조회합니다."""
    try:
        journeys = db.query(Journey).order_by(Journey.start_date).all()
        return JourneyListResponse(journeys=[JourneyResponse.model_validate(j) for j in journeys], total=len(journeys))  # type: ignore
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"여정 조회 중 오류가 발생했습니다: {str(e)}",
        )


@router.get("/{journey_id}/edit", response_class=HTMLResponse)
async def get_journey_edit_form(
    request: Request, journey_id: int, db: Session = Depends(get_db)
) -> HTMLResponse:
    """여정 편집 폼을 반환합니다 (HTMX용)."""
    try:
        journey = db.query(Journey).filter(Journey.id == journey_id).first()
        if not journey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {journey_id}인 여정을 찾을 수 없습니다",
            )

        return templates.TemplateResponse(
            request,
            "forms/journey_edit_form.html",
            {"journey": journey}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"여정 편집 폼 로딩 중 오류가 발생했습니다: {str(e)}",
        )


@router.get("/{journey_id}", response_model=JourneyResponse)
async def get_journey(journey_id: int, db: Session = Depends(get_db)) -> JourneyResponse:
    """특정 여정을 조회합니다."""
    try:
        journey = db.query(Journey).filter(Journey.id == journey_id).first()
        if not journey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {journey_id}인 여정을 찾을 수 없습니다",
            )
        return journey
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"여정 조회 중 오류가 발생했습니다: {str(e)}",
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_journey(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    start_date: date = Form(...),
    end_date: date = Form(...),
    db: Session = Depends(get_db)
):
    """새로운 여정을 생성합니다 (HTMX Form 데이터 처리)."""
    try:
        # 시작일이 종료일보다 늦으면 안됨
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="시작일이 종료일보다 늦을 수 없습니다",
            )

        # 동일한 제목의 여정이 이미 있는지 확인 (대소문자 및 공백 무시)
        title_cleaned = title.strip().lower()
        existing_journey = (
            db.query(Journey)
            .filter(func.lower(func.trim(Journey.title)) == title_cleaned)
            .first()
        )

        if existing_journey:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"동일한 제목의 여정이 이미 존재합니다: '{existing_journey.title}'",
            )

        # 새 여정 생성
        from ..models.journey import JourneyStatus
        db_journey = Journey(
            title=title,
            description=description,
            start_date=start_date,
            end_date=end_date,
            progress=0.0,
            status=JourneyStatus.PLANNING
        )
        db.add(db_journey)
        db.commit()
        db.refresh(db_journey)

        # HTMX 요청인 경우 빈 응답 반환 (모달 닫기)
        return HTMLResponse(content="", status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"여정 생성 중 오류가 발생했습니다: {str(e)}",
        )


@router.post("/{journey_id}/edit", status_code=status.HTTP_200_OK)
async def update_journey_form(
    request: Request,
    journey_id: int,
    title: str = Form(...),
    description: str = Form(""),
    start_date: date = Form(...),
    end_date: date = Form(...),
    journey_status: str = Form(..., alias="status"),
    progress: float = Form(...),
    db: Session = Depends(get_db)
):
    """여정을 수정합니다 (HTMX Form 데이터 처리)."""
    try:
        # 기존 여정 조회
        db_journey = db.query(Journey).filter(Journey.id == journey_id).first()

        if not db_journey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {journey_id}인 여정을 찾을 수 없습니다",
            )

        # 시작일/종료일 유효성 검증
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="시작일이 종료일보다 늦을 수 없습니다",
            )

        # 제목 중복 확인 (다른 여정과)
        existing_journey = (
            db.query(Journey)
            .filter(
                Journey.title == title,
                Journey.id != journey_id,
            )
            .first()
        )

        if existing_journey:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="동일한 제목의 여정이 이미 존재합니다",
            )

        # 업데이트 실행
        from ..models.journey import JourneyStatus
        db_journey.title = title
        db_journey.description = description
        db_journey.start_date = start_date
        db_journey.end_date = end_date
        db_journey.progress = progress

        # 문자열을 Enum으로 변환
        if journey_status == "계획중":
            db_journey.status = JourneyStatus.PLANNING
        elif journey_status == "진행중":
            db_journey.status = JourneyStatus.ACTIVE
        elif journey_status == "완료":
            db_journey.status = JourneyStatus.COMPLETED
        elif journey_status == "일시중지":
            db_journey.status = JourneyStatus.PAUSED

        db.commit()
        db.refresh(db_journey)

        # HTMX 요청인 경우 빈 응답 반환 (모달 닫기)
        return HTMLResponse(content="", status_code=200)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"여정 수정 중 오류가 발생했습니다: {str(e)}",
        )


@router.put("/{journey_id}", response_model=JourneyResponse)
async def update_journey(
    journey_id: int, journey_data: JourneyUpdate, db: Session = Depends(get_db)
) -> JourneyResponse:
    """여정을 수정합니다."""
    try:
        # 기존 여정 조회
        db_journey = db.query(Journey).filter(Journey.id == journey_id).first()

        if not db_journey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {journey_id}인 여정을 찾을 수 없습니다",
            )

        # 수정할 데이터만 업데이트
        update_data = journey_data.model_dump(exclude_unset=True)

        # 시작일/종료일 유효성 검증
        start_date = update_data.get("start_date", db_journey.start_date)
        end_date = update_data.get("end_date", db_journey.end_date)

        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="시작일이 종료일보다 늦을 수 없습니다",
            )

        # 제목 중복 확인 (다른 여정과)
        if "title" in update_data:
            existing_journey = (
                db.query(Journey)
                .filter(
                    Journey.title == update_data["title"],
                    Journey.id != journey_id,
                )
                .first()
            )

            if existing_journey:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="동일한 제목의 여정이 이미 존재합니다",
                )

        # 업데이트 실행
        for field, value in update_data.items():
            setattr(db_journey, field, value)

        db.commit()
        db.refresh(db_journey)

        return db_journey

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"여정 수정 중 오류가 발생했습니다: {str(e)}",
        )


@router.put("/{journey_id}/complete", response_class=HTMLResponse)
async def complete_journey(journey_id: int, request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """여정을 완료로 표시합니다."""
    try:
        db_journey = db.query(Journey).filter(Journey.id == journey_id).first()

        if not db_journey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {journey_id}인 여정을 찾을 수 없습니다",
            )

        from ..models.journey import JourneyStatus

        db_journey.status = JourneyStatus.COMPLETED  # type: ignore
        db_journey.progress = 100.0  # type: ignore

        db.commit()
        db.refresh(db_journey)

        # 업데이트된 여정 카드 HTML 반환
        return templates.TemplateResponse(
            request,
            "components/journey_card.html",
            {"journey": db_journey}
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"여정 완료 처리 중 오류가 발생했습니다: {str(e)}",
        )


@router.delete("/{journey_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_journey(journey_id: int, db: Session = Depends(get_db)) -> None:
    """여정을 삭제합니다."""
    try:
        # 기존 여정 조회
        db_journey = db.query(Journey).filter(Journey.id == journey_id).first()

        if not db_journey:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ID {journey_id}인 여정을 찾을 수 없습니다",
            )

        # 연결된 TODO가 있는지 확인
        from ..models.todo import Todo

        related_todos = db.query(Todo).filter(Todo.journey_id == journey_id).count()

        if related_todos > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"연결된 TODO가 {related_todos}개 있어 여정을 삭제할 수 없습니다. 먼저 TODO를 삭제하거나 다른 여정으로 이동하세요.",
            )

        # 여정 삭제
        db.delete(db_journey)
        db.commit()

        # 204 No Content는 응답 본문이 없음
        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"여정 삭제 중 오류가 발생했습니다: {str(e)}",
        )