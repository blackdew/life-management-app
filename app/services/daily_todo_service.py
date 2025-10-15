from datetime import date, datetime, timedelta
from typing import List, Optional
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from ..models.todo import DailyTodo, TodoCategory
from ..core.timezone import get_current_date, get_current_utc_datetime


class DailyTodoService:
    """일상 Todo 관리 서비스"""

    @staticmethod
    def get_today_todos(db: Session) -> List[DailyTodo]:
        """오늘의 할 일 목록 조회 (오늘 할일 + 과거 미완료 할일 자동 이월)"""
        today = get_current_date()

        query = (
            db.query(DailyTodo)
            .filter(
                or_(
                    # 1. 오늘 생성된 할일 (단, scheduled_date가 미래가 아닌 경우만)
                    and_(
                        DailyTodo.created_date == today,
                        or_(
                            DailyTodo.scheduled_date == None,  # scheduled_date가 없는 경우
                            DailyTodo.scheduled_date <= today  # scheduled_date가 오늘 이전 또는 오늘인 경우
                        )
                    ),

                    # 2. 오늘 완료한 할일 (과거 생성된 것, 생성일이 오늘이 아닌 경우만)
                    and_(
                        DailyTodo.is_completed == True,
                        DailyTodo.created_date < today,
                        func.date(DailyTodo.completed_at) == today
                    ),

                    # 3. 과거 미완료 할일 (자동 이월)
                    and_(
                        DailyTodo.is_completed == False,
                        DailyTodo.created_date < today,
                        or_(
                            DailyTodo.scheduled_date == None,  # scheduled_date가 없는 경우
                            DailyTodo.scheduled_date <= today  # scheduled_date가 오늘 이전인 경우
                        )
                    ),

                    # 4. 오늘로 미룬 할일 (created_date는 과거지만 scheduled_date가 오늘인 경우)
                    and_(
                        DailyTodo.is_completed == False,
                        DailyTodo.scheduled_date == today
                    )
                )
            )
            .order_by(
                # 지연된 할일을 우선 표시 (created_date 오래된 순)
                DailyTodo.created_date.asc(),
                DailyTodo.created_at.asc()
            )
        )

        return query.all()

    @staticmethod
    def get_todo_by_id(db: Session, todo_id: int) -> Optional[DailyTodo]:
        """ID로 특정 할 일 조회"""
        return db.query(DailyTodo).filter(DailyTodo.id == todo_id).first()

    @staticmethod
    def create_todo(
        db: Session,
        title: str,
        description: Optional[str] = None,
        notes: Optional[str] = None,
        category: Optional[TodoCategory] = None,
        estimated_minutes: Optional[int] = None,
        journey_id: Optional[int] = None,
        scheduled_date: Optional[date] = None,
    ) -> DailyTodo:
        """새 할 일 생성"""
        current_utc_time = get_current_utc_datetime()  # UTC로 저장
        todo = DailyTodo(
            title=title.strip(),
            description=description.strip() if description else None,
            notes=notes.strip() if notes else None,
            category=category or TodoCategory.OTHER,
            estimated_minutes=estimated_minutes,
            journey_id=journey_id,
            created_date=get_current_date(),  # 로컬 날짜 (표시용)
            created_at=current_utc_time,  # UTC 시간으로 DB 저장
            scheduled_date=scheduled_date or get_current_date(),
        )
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return todo

    @staticmethod
    def toggle_complete(db: Session, todo_id: int, reflection: Optional[str] = None, image_path: Optional[str] = None) -> Optional[DailyTodo]:
        """할 일 완료/미완료 토글"""
        todo = db.query(DailyTodo).filter(DailyTodo.id == todo_id).first()
        if not todo:
            return None

        if todo.is_completed:
            todo.uncomplete()
            # 완료 해제 시 회고와 이미지 초기화
            todo.completion_reflection = None
            todo.completion_image_path = None
        else:
            todo.complete()
            if reflection:
                todo.completion_reflection = reflection.strip()
            if image_path:
                todo.completion_image_path = image_path

        db.commit()
        db.refresh(todo)
        return todo

    @staticmethod
    def delete_todo(db: Session, todo_id: int) -> bool:
        """할 일 삭제"""
        todo = db.query(DailyTodo).filter(DailyTodo.id == todo_id).first()
        if not todo:
            return False

        db.delete(todo)
        db.commit()
        return True

    @staticmethod
    def get_today_summary(db: Session) -> dict:
        """오늘의 요약 정보 - 실제로 오늘 표시되는 할일들을 기준으로 계산"""
        # get_today_todos와 동일한 로직으로 오늘 표시되는 할일들을 가져옴
        today_todos = DailyTodoService.get_today_todos(db)

        completed_count = len([t for t in today_todos if t.is_completed])
        total_count = len(today_todos)
        pending_count = total_count - completed_count

        return {
            "total": total_count,
            "completed": completed_count,
            "pending": pending_count,
            "completion_rate": round(completed_count / total_count * 100, 1) if total_count > 0 else 0,
        }

    @staticmethod
    def get_weekly_summary(db: Session) -> dict:
        """주간 요약 정보"""
        # 이번 주 시작일 (월요일) 계산
        today = get_current_date()
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)

        # 이번 주 할 일들 조회
        weekly_todos = (
            db.query(DailyTodo)
            .filter(DailyTodo.created_date >= week_start)
            .all()
        )

        # 날짜별 완료 개수 계산
        daily_counts = {}
        for i in range(7):  # 월~일
            day = week_start + timedelta(days=i)
            day_todos = [t for t in weekly_todos if t.created_date == day]
            completed = len([t for t in day_todos if t.is_completed])
            total = len(day_todos)

            daily_counts[day.strftime("%Y-%m-%d")] = {
                "total": total,
                "completed": completed,
                "weekday": day.strftime("%A"),
                "date": day.strftime("%m/%d"),
            }

        return {
            "week_start": week_start.strftime("%Y-%m-%d"),
            "daily_counts": daily_counts,
            "total_completed": len([t for t in weekly_todos if t.is_completed]),
            "total_todos": len(weekly_todos),
        }

    @staticmethod
    def update_todo(
        db: Session,
        todo_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None,
        category: Optional[TodoCategory] = None,
        estimated_minutes: Optional[int] = None,
        actual_minutes: Optional[int] = None,
        journey_id: Optional[int] = None,
    ) -> Optional[DailyTodo]:
        """할 일 수정"""
        todo = db.query(DailyTodo).filter(DailyTodo.id == todo_id).first()
        if not todo:
            return None

        if title is not None:
            todo.title = title.strip()
        if description is not None:
            todo.description = description.strip() if description else None
        if notes is not None:
            todo.notes = notes.strip() if notes else None
        if category is not None:
            todo.category = category
        if estimated_minutes is not None:
            todo.estimated_minutes = estimated_minutes
        if actual_minutes is not None:
            todo.actual_minutes = actual_minutes
        if journey_id is not None:
            todo.journey_id = journey_id

        db.commit()
        db.refresh(todo)
        return todo

    @staticmethod
    def add_quick_todo(db: Session, title: str) -> DailyTodo:
        """빠른 할 일 추가 (최소 정보만)"""
        return DailyTodoService.create_todo(db, title)

    @staticmethod
    def get_category_summary(db: Session) -> dict:
        """카테고리별 요약"""
        today = get_current_date()
        todos = (
            db.query(DailyTodo)
            .filter(DailyTodo.created_date == today)
            .all()
        )

        category_counts = {}
        for category in TodoCategory:
            category_todos = [t for t in todos if t.category == category]
            if category_todos:  # 해당 카테고리에 할 일이 있는 경우만
                completed = len([t for t in category_todos if t.is_completed])
                total = len(category_todos)
                category_counts[category.value] = {
                    "total": total,
                    "completed": completed,
                    "percentage": round(total / len(todos) * 100, 1) if todos else 0,
                }

        return category_counts

    @staticmethod
    def reschedule_todo(db: Session, todo_id: int, new_date: date) -> Optional[DailyTodo]:
        """할 일 일정 재조정 (미루기)"""
        todo = db.query(DailyTodo).filter(DailyTodo.id == todo_id).first()
        if not todo:
            return None

        todo.scheduled_date = new_date
        todo.created_date = new_date  # 새로운 날짜로 이동

        db.commit()
        db.refresh(todo)
        return todo

    @staticmethod
    def get_journeys_for_selection(db: Session) -> list:
        """할 일 추가 시 선택할 수 있는 여정 목록"""
        from ..models.journey import Journey, JourneyStatus

        journeys = (
            db.query(Journey)
            .order_by(Journey.created_at.desc())
            .all()
        )

        return [
            {
                "id": j.id,
                "title": j.title,
                "status": j.status.value
            }
            for j in journeys
        ]

    @staticmethod
    def reschedule_todo_with_reason(
        db: Session,
        todo_id: int,
        new_date: date,
        reason: str
    ) -> Optional[DailyTodo]:
        """할 일 미루기 (사유 포함)"""
        todo = db.query(DailyTodo).filter(DailyTodo.id == todo_id).first()
        if not todo:
            return None

        # 완료된 할 일은 미룰 수 없음
        if todo.is_completed:
            raise ValueError("완료된 할 일은 미룰 수 없습니다")

        # 사유 검증
        if not reason or not reason.strip():
            raise ValueError("미루기 사유는 필수입니다")

        reason = reason.strip()
        if len(reason) > 100:
            raise ValueError("미루기 사유는 100자 이하여야 합니다")

        # 현재 날짜 (미루기 이전 날짜)
        current_date = todo.scheduled_date or todo.created_date

        # 미루기 히스토리 생성
        postpone_record = {
            "from_date": current_date.isoformat(),
            "to_date": new_date.isoformat(),
            "reason": reason,
            "postponed_at": get_current_utc_datetime().isoformat()
        }

        # 기존 히스토리 로드
        existing_history = []
        if todo.postpone_history:
            try:
                existing_history = json.loads(todo.postpone_history)
            except (json.JSONDecodeError, TypeError):
                existing_history = []

        # 새 히스토리 추가
        existing_history.append(postpone_record)

        # 업데이트
        todo.scheduled_date = new_date
        todo.postpone_count = (todo.postpone_count or 0) + 1
        todo.postpone_history = json.dumps(existing_history, ensure_ascii=False)

        db.commit()
        db.refresh(todo)
        return todo

    @staticmethod
    def get_postpone_summary(db: Session, todo_id: int) -> Optional[dict]:
        """미루기 요약 정보 조회"""
        todo = db.query(DailyTodo).filter(DailyTodo.id == todo_id).first()
        if not todo:
            return None

        # 히스토리 파싱
        history = []
        if todo.postpone_history:
            try:
                history = json.loads(todo.postpone_history)
            except (json.JSONDecodeError, TypeError):
                history = []

        # 원본 날짜 (첫 번째 생성 날짜)
        original_date = todo.created_date
        current_date = todo.scheduled_date or todo.created_date

        # 총 미룬 일수 계산
        total_days_postponed = (current_date - original_date).days

        # 최신 사유들 (최대 3개)
        recent_reasons = []
        if history:
            recent_reasons = [h["reason"] for h in reversed(history[-3:])]

        return {
            "postpone_count": todo.postpone_count or 0,
            "original_date": original_date.isoformat(),
            "current_date": current_date.isoformat(),
            "total_days_postponed": total_days_postponed,
            "recent_reasons": recent_reasons,
            "full_history": history
        }