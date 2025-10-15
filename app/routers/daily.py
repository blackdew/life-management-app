from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import uuid
from pathlib import Path

from ..core.database import get_db
from ..models.todo import DailyTodo, TodoCategory
from ..models.daily_memo import DailyMemo
from ..services.daily_todo_service import DailyTodoService
from ..services.daily_memo_service import DailyMemoService
from ..core.timezone import get_current_date, format_date_for_display, format_datetime_for_api

router = APIRouter(prefix="/api/daily", tags=["일상 Todo"])


# API 엔드포인트들

@router.get("/todos/today")
async def get_today_todos(db: Session = Depends(get_db)):
    """오늘의 할 일 목록 조회"""
    try:
        from datetime import date

        todos = DailyTodoService.get_today_todos(db)
        today = get_current_date()

        return {
            "todos": [
                {
                    "id": todo.id,
                    "title": todo.title,
                    "notes": todo.notes,
                    "category": todo.category.value,
                    "is_completed": todo.is_completed,
                    "completed_at": format_datetime_for_api(todo.completed_at),
                    "estimated_minutes": todo.estimated_minutes,
                    "actual_minutes": todo.actual_minutes,
                    # 경과일 정보 추가
                    "days_overdue": (today - todo.created_date).days,
                    "overdue_status": _calculate_overdue_status(todo, today),
                    "created_date": todo.created_date.isoformat(),
                    "scheduled_date": todo.scheduled_date.isoformat() if todo.scheduled_date else None,
                    # 미루기 정보 추가
                    "postpone_count": todo.postpone_count or 0,
                }
                for todo in todos
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"할 일 목록 조회 실패: {str(e)}")


def _calculate_overdue_status(todo, today):
    """할일의 지연 상태 계산"""
    days_overdue = (today - todo.created_date).days

    if todo.scheduled_date and todo.scheduled_date > today:
        return "scheduled"  # 미래 예정
    elif days_overdue == 0:
        return "today"  # 오늘
    elif days_overdue > 0:
        return "overdue"  # 지연됨
    else:
        return "today"  # 기본값


@router.post("/todos")
async def create_todo(
    title: str = Form(),
    description: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    estimated_minutes: Optional[int] = Form(None),
    journey_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    """새 할 일 생성"""
    try:
        # 카테고리 변환 (한국어 값으로 enum 찾기)
        todo_category = None
        if category:
            # 한국어 값으로 enum 찾기
            for cat in TodoCategory:
                if cat.value == category:
                    todo_category = cat
                    break
            if todo_category is None:
                todo_category = TodoCategory.OTHER

        todo = DailyTodoService.create_todo(
            db=db,
            title=title,
            description=description,
            notes=notes,
            category=todo_category,
            estimated_minutes=estimated_minutes,
            journey_id=journey_id,
        )

        return {
            "id": todo.id,
            "title": todo.title,
            "notes": todo.notes,
            "category": todo.category.value,
            "is_completed": todo.is_completed,
            "created_at": todo.created_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"할 일 생성 실패: {str(e)}")


@router.post("/todos/quick")
async def create_quick_todo(title: str = Form(), db: Session = Depends(get_db)):
    """빠른 할 일 추가 (제목만)"""
    try:
        if not title or not title.strip():
            raise HTTPException(status_code=400, detail="할 일 제목이 필요합니다")

        todo = DailyTodoService.add_quick_todo(db, title)
        return {
            "id": todo.id,
            "title": todo.title,
            "is_completed": todo.is_completed,
            "category": todo.category.value,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"빠른 할 일 추가 실패: {str(e)}")


@router.patch("/todos/{todo_id}/toggle")
async def toggle_todo_complete(todo_id: int, db: Session = Depends(get_db)):
    """할 일 완료/미완료 토글"""
    try:
        todo = DailyTodoService.toggle_complete(db, todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다")

        return {
            "id": todo.id,
            "title": todo.title,
            "is_completed": todo.is_completed,
            "completed_at": todo.completed_at.isoformat() if todo.completed_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"할 일 상태 변경 실패: {str(e)}")


@router.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """할 일 삭제"""
    try:
        success = DailyTodoService.delete_todo(db, todo_id)
        if not success:
            raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다")

        return {"message": "할 일이 삭제되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"할 일 삭제 실패: {str(e)}")


@router.get("/summary/today")
async def get_today_summary(db: Session = Depends(get_db)):
    """오늘의 요약 정보"""
    try:
        summary = DailyTodoService.get_today_summary(db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 정보 조회 실패: {str(e)}")


@router.get("/summary/weekly")
async def get_weekly_summary(db: Session = Depends(get_db)):
    """주간 요약 정보"""
    try:
        summary = DailyTodoService.get_weekly_summary(db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주간 요약 조회 실패: {str(e)}")


@router.get("/summary/categories")
async def get_category_summary(db: Session = Depends(get_db)):
    """카테고리별 요약"""
    try:
        summary = DailyTodoService.get_category_summary(db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"카테고리 요약 조회 실패: {str(e)}")


@router.patch("/todos/{todo_id}/complete")
async def complete_todo_with_reflection(
    todo_id: int,
    reflection: Optional[str] = Form(None),
    reflection_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """할 일 완료 시 회고 작성 (이미지 포함)"""
    try:
        # 이미지 업로드 처리
        image_path = None
        if reflection_image and reflection_image.filename:
            # 파일 확장자 검증
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
            file_extension = Path(reflection_image.filename).suffix.lower()

            if file_extension not in allowed_extensions:
                raise HTTPException(status_code=400, detail="지원하지 않는 이미지 형식입니다. (jpg, png, gif, webp만 지원)")

            # 고유 파일명 생성
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            upload_dir = Path("app/static/uploads/reflections")
            upload_dir.mkdir(parents=True, exist_ok=True)

            # 파일 저장
            file_path = upload_dir / unique_filename
            with open(file_path, "wb") as buffer:
                content = await reflection_image.read()
                buffer.write(content)

            # 웹에서 접근 가능한 경로로 저장
            image_path = f"/static/uploads/reflections/{unique_filename}"

        # 할 일 완료 처리 (이미지 경로 포함)
        todo = DailyTodoService.toggle_complete(db, todo_id, reflection, image_path)
        if not todo:
            raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다")

        return {
            "id": todo.id,
            "title": todo.title,
            "is_completed": todo.is_completed,
            "completion_reflection": todo.completion_reflection,
            "completion_image_path": todo.completion_image_path,
            "completed_at": todo.completed_at.isoformat() if todo.completed_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"할 일 완료 처리 실패: {str(e)}")


@router.patch("/todos/{todo_id}/reschedule")
async def reschedule_todo(
    todo_id: int,
    new_date: str = Form(),  # YYYY-MM-DD 형식
    reason: Optional[str] = Form(None),    # 미루기 사유 (선택적)
    db: Session = Depends(get_db)
):
    """할 일 일정 재조정 (미루기 사유 선택적)"""
    try:
        from datetime import datetime

        # 날짜 파싱
        try:
            parsed_date = datetime.strptime(new_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="올바른 날짜 형식이 아닙니다 (YYYY-MM-DD)")

        # 사유가 있으면 새로운 메서드 사용, 없으면 기존 메서드 사용
        if reason and reason.strip():
            todo = DailyTodoService.reschedule_todo_with_reason(
                db=db,
                todo_id=todo_id,
                new_date=parsed_date,
                reason=reason
            )
        else:
            # 기존 방식 (하위 호환성)
            todo = DailyTodoService.reschedule_todo(
                db=db,
                todo_id=todo_id,
                new_date=parsed_date
            )
        if not todo:
            raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다")

        return {
            "id": todo.id,
            "title": todo.title,
            "scheduled_date": todo.scheduled_date.isoformat(),
            "created_date": todo.created_date.isoformat(),
            "postpone_count": todo.postpone_count,
            "last_reason": reason
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일정 재조정 실패: {str(e)}")


@router.get("/journeys")
async def get_journeys_for_selection(db: Session = Depends(get_db)):
    """할 일 추가 시 선택할 수 있는 여정 목록"""
    try:
        journeys = DailyTodoService.get_journeys_for_selection(db)
        return {"journeys": journeys}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"여정 목록 조회 실패: {str(e)}")


@router.get("/todos/{todo_id}")
async def get_todo_by_id(todo_id: int, db: Session = Depends(get_db)):
    """특정 할 일 상세 조회"""
    try:
        todo = DailyTodoService.get_todo_by_id(db, todo_id)
        if not todo:
            raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다")

        return {
            "id": todo.id,
            "title": todo.title,
            "description": todo.description,
            "notes": todo.notes,
            "category": todo.category.value,
            "is_completed": todo.is_completed,
            "estimated_minutes": todo.estimated_minutes,
            "actual_minutes": todo.actual_minutes,
            "journey_id": todo.journey_id,
            "created_date": todo.created_date.isoformat(),
            "scheduled_date": todo.scheduled_date.isoformat(),
            "completed_at": todo.completed_at.isoformat() if todo.completed_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"할 일 조회 실패: {str(e)}")


@router.put("/todos/{todo_id}")
async def update_todo(
    todo_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    estimated_minutes: Optional[int] = Form(None),
    journey_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """할 일 수정"""
    try:
        # 카테고리 변환 (한국어 값으로 enum 찾기)
        todo_category = None
        if category:
            # 한국어 값으로 enum 찾기
            for cat in TodoCategory:
                if cat.value == category:
                    todo_category = cat
                    break
            if todo_category is None:
                todo_category = TodoCategory.OTHER

        todo = DailyTodoService.update_todo(
            db=db,
            todo_id=todo_id,
            title=title,
            description=description,
            notes=notes,
            category=todo_category,
            estimated_minutes=estimated_minutes,
            actual_minutes=None,  # 필요시 나중에 추가
            journey_id=journey_id,
        )

        if not todo:
            raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다")

        return {
            "id": todo.id,
            "title": todo.title,
            "description": todo.description,
            "notes": todo.notes,
            "category": todo.category.value,
            "journey_id": todo.journey_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"할 일 수정 실패: {str(e)}")


@router.get("/reflection-summary")
async def get_reflection_summary(db: Session = Depends(get_db)):
    """회고 작성용 오늘의 활동 요약"""
    try:
        from datetime import date as date_cls
        # 오늘의 할 일 목록
        todos = DailyTodoService.get_today_todos(db)
        # 오늘의 요약
        summary = DailyTodoService.get_today_summary(db)
        # 오늘의 메모들
        today_memos = DailyMemoService.get_memos_by_date(db, date_cls.today())

        # 카테고리별 분류
        completed_todos = [todo for todo in todos if todo.is_completed]
        pending_todos = [todo for todo in todos if not todo.is_completed]

        # 카테고리별 그룹화
        from collections import defaultdict
        completed_by_category = defaultdict(list)
        pending_by_category = defaultdict(list)

        for todo in completed_todos:
            completed_by_category[todo.category.value].append({
                "id": todo.id,
                "title": todo.title,
                "completed_at": todo.completed_at.strftime("%H:%M") if todo.completed_at else None
            })

        for todo in pending_todos:
            pending_by_category[todo.category.value].append({
                "id": todo.id,
                "title": todo.title,
                "estimated_minutes": todo.estimated_minutes
            })

        # 자동 회고 텍스트 생성
        today_str = format_date_for_display(get_current_date())

        reflection_template = f"""오늘 {today_str} 하루를 마무리하며...

📊 오늘의 성과:
- 전체 할 일: {summary.get('total', 0)}개
- 완료: {summary.get('completed', 0)}개 ({summary.get('completion_rate', 0):.1f}%)
- 미완료: {summary.get('pending', 0)}개

✅ 완료한 일들:"""

        # 완료된 할 일들 추가
        if completed_todos:
            for category, items in completed_by_category.items():
                if items:
                    category_name = {
                        'WORK': '💼 업무',
                        'PERSONAL': '👤 개인',
                        'HEALTH': '💪 건강',
                        'LEARNING': '📚 학습',
                        'SOCIAL': '👥 사회',
                        'OTHER': '🔹 기타'
                    }.get(category, category)

                    reflection_template += f"\n{category_name}:"
                    for item in items:
                        time_str = f" ({item['completed_at']})" if item['completed_at'] else ""
                        reflection_template += f"\n  • {item['title']}{time_str}"
        else:
            reflection_template += "\n(완료한 일이 없습니다)"

        # 미완료 할 일들 추가
        if pending_todos:
            reflection_template += "\n\n⏳ 미완료 남은 일들:"
            for category, items in pending_by_category.items():
                if items:
                    category_name = {
                        'WORK': '💼 업무',
                        'PERSONAL': '👤 개인',
                        'HEALTH': '💪 건강',
                        'LEARNING': '📚 학습',
                        'SOCIAL': '👥 사회',
                        'OTHER': '🔹 기타'
                    }.get(category, category)

                    reflection_template += f"\n{category_name}:"
                    for item in items:
                        time_str = f" (예상 {item['estimated_minutes']}분)" if item['estimated_minutes'] else ""
                        reflection_template += f"\n  • {item['title']}{time_str}"

        # 오늘의 메모들 추가
        if today_memos:
            reflection_template += "\n\n📝 오늘의 메모들:"
            for memo in today_memos:
                time_str = memo.created_at.strftime("%H:%M") if memo.created_at else ""
                reflection_template += f"\n  • {memo.content}"
                if time_str:
                    reflection_template += f" ({time_str})"

        reflection_template += "\n\n💭 오늘의 생각과 느낌:\n"

        return {
            "summary": summary,
            "completed_todos": completed_by_category,
            "pending_todos": pending_by_category,
            "today_memos": [
                {
                    "id": memo.id,
                    "content": memo.content,
                    "created_at": format_datetime_for_api(memo.created_at),
                }
                for memo in today_memos
            ],
            "reflection_template": reflection_template,
            "today_date": today_str
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"회고 요약 조회 실패: {str(e)}")


@router.get("/todos/{todo_id}/postpone-summary")
async def get_todo_postpone_summary(todo_id: int, db: Session = Depends(get_db)):
    """할 일의 미루기 요약 정보 조회"""
    try:
        summary = DailyTodoService.get_postpone_summary(db, todo_id)
        if not summary:
            raise HTTPException(status_code=404, detail="할 일을 찾을 수 없습니다")

        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"미루기 요약 조회 실패: {str(e)}")


# === 메모 관련 API 엔드포인트 ===

@router.get("/memos/today")
async def get_today_memos(db: Session = Depends(get_db)):
    """오늘의 메모 목록 조회"""
    try:
        from datetime import date
        today = get_current_date()
        memos = DailyMemoService.get_memos_by_date(db, today)

        return {
            "memos": [
                {
                    "id": memo.id,
                    "content": memo.content,
                    "memo_date": memo.memo_date.isoformat(),
                    "created_at": format_datetime_for_api(memo.created_at),
                    "updated_at": format_datetime_for_api(memo.updated_at),
                }
                for memo in memos
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오늘의 메모 조회 실패: {str(e)}")


@router.post("/memos", status_code=201)
async def create_memo(
    memo_date: str = Form(),
    content: str = Form(),
    db: Session = Depends(get_db)
):
    """새로운 메모 생성"""
    try:
        from datetime import datetime

        # 날짜 파싱
        try:
            parsed_date = datetime.strptime(memo_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="올바른 날짜 형식이 아닙니다 (YYYY-MM-DD)")

        # 메모 생성
        memo = DailyMemoService.create_memo(
            db=db,
            memo_date=parsed_date,
            content=content
        )

        return {
            "id": memo.id,
            "content": memo.content,
            "memo_date": memo.memo_date.isoformat(),
            "created_at": format_datetime_for_api(memo.created_at),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메모 생성 실패: {str(e)}")


@router.post("/memos/quick", status_code=201)
async def create_quick_memo(
    content: str = Form(),
    db: Session = Depends(get_db)
):
    """빠른 메모 생성 (오늘 날짜 자동 설정)"""
    try:
        from datetime import date
        today = get_current_date()

        memo = DailyMemoService.create_memo(
            db=db,
            memo_date=today,
            content=content
        )

        return {
            "id": memo.id,
            "content": memo.content,
            "memo_date": memo.memo_date.isoformat(),
            "created_at": format_datetime_for_api(memo.created_at),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"빠른 메모 생성 실패: {str(e)}")



@router.get("/memos/date/{memo_date}")
async def get_memos_by_date(memo_date: str, db: Session = Depends(get_db)):
    """특정 날짜의 메모들 조회"""
    try:
        from datetime import datetime

        # 날짜 파싱
        try:
            parsed_date = datetime.strptime(memo_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="올바른 날짜 형식이 아닙니다 (YYYY-MM-DD)")

        memos = DailyMemoService.get_memos_by_date(db, parsed_date)

        return {
            "memos": [
                {
                    "id": memo.id,
                    "content": memo.content,
                    "memo_date": memo.memo_date.isoformat(),
                    "created_at": format_datetime_for_api(memo.created_at),
                    "updated_at": format_datetime_for_api(memo.updated_at),
                }
                for memo in memos
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"날짜별 메모 조회 실패: {str(e)}")


@router.get("/memos/recent")
async def get_recent_memos(limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_db)):
    """최근 메모들 조회"""
    try:
        memos = DailyMemoService.get_recent_memos(db, limit)

        return {
            "memos": [
                {
                    "id": memo.id,
                    "content": memo.content,
                    "memo_date": memo.memo_date.isoformat(),
                    "created_at": format_datetime_for_api(memo.created_at),
                    "updated_at": format_datetime_for_api(memo.updated_at),
                }
                for memo in memos
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"최근 메모 조회 실패: {str(e)}")


@router.get("/memos/search")
async def search_memos(keyword: str = Query(..., min_length=1), limit: int = Query(default=50, ge=1, le=100), db: Session = Depends(get_db)):
    """키워드로 메모 검색"""
    try:
        if not keyword or not keyword.strip():
            raise HTTPException(status_code=400, detail="검색 키워드가 필요합니다")

        memos = DailyMemoService.search_memos(db, keyword, limit)

        return {
            "memos": [
                {
                    "id": memo.id,
                    "content": memo.content,
                    "memo_date": memo.memo_date.isoformat(),
                    "created_at": format_datetime_for_api(memo.created_at),
                    "updated_at": format_datetime_for_api(memo.updated_at),
                }
                for memo in memos
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메모 검색 실패: {str(e)}")


@router.get("/memos/count/{memo_date}")
async def get_memo_count_by_date(memo_date: str, db: Session = Depends(get_db)):
    """특정 날짜의 메모 개수 조회"""
    try:
        from datetime import datetime

        # 날짜 파싱
        try:
            parsed_date = datetime.strptime(memo_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="올바른 날짜 형식이 아닙니다 (YYYY-MM-DD)")

        count = DailyMemoService.get_memos_count_by_date(db, parsed_date)

        return {
            "count": count,
            "date": memo_date
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메모 개수 조회 실패: {str(e)}")


class BulkDeleteRequest(BaseModel):
    memo_ids: list[int]

@router.delete("/memos/bulk")
async def bulk_delete_memos(
    request: BulkDeleteRequest,
    db: Session = Depends(get_db)
):
    """메모 일괄 삭제"""
    try:
        deleted_count = 0
        for memo_id in request.memo_ids:
            try:
                success = DailyMemoService.delete_memo(db, memo_id)
                if success:
                    deleted_count += 1
            except ValueError:
                # 메모가 없는 경우 무시하고 계속 진행
                continue

        return {"deleted_count": deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"일괄 삭제 실패: {str(e)}")


# 경로 매개변수가 있는 엔드포인트들은 마지막에 정의 (충돌 방지)
@router.get("/memos/{memo_id}")
async def get_memo_by_id(memo_id: int, db: Session = Depends(get_db)):
    """ID로 특정 메모 조회"""
    try:
        memo = DailyMemoService.get_memo_by_id(db, memo_id)
        if not memo:
            raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다")

        return {
            "id": memo.id,
            "content": memo.content,
            "memo_date": memo.memo_date.isoformat(),
            "created_at": format_datetime_for_api(memo.created_at),
            "updated_at": format_datetime_for_api(memo.updated_at),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메모 조회 실패: {str(e)}")


@router.put("/memos/{memo_id}")
async def update_memo(
    memo_id: int,
    content: str = Form(),
    db: Session = Depends(get_db)
):
    """메모 수정"""
    try:
        memo = DailyMemoService.update_memo(
            db=db,
            memo_id=memo_id,
            content=content
        )

        return {
            "id": memo.id,
            "content": memo.content,
            "memo_date": memo.memo_date.isoformat(),
            "updated_at": format_datetime_for_api(memo.updated_at),
        }
    except ValueError as e:
        if "메모를 찾을 수 없습니다" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메모 수정 실패: {str(e)}")


@router.delete("/memos/{memo_id}")
async def delete_memo(memo_id: int, db: Session = Depends(get_db)):
    """메모 삭제"""
    try:
        success = DailyMemoService.delete_memo(db, memo_id)
        if not success:
            raise HTTPException(status_code=404, detail="메모를 찾을 수 없습니다")

        return {"message": "메모가 삭제되었습니다"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"메모 삭제 실패: {str(e)}")