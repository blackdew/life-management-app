from datetime import date, datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.daily_reflection import DailyReflection
from app.models.todo import DailyTodo
from app.core.timezone import get_current_date, get_current_utc_datetime


class DailyReflectionService:
    """일일 회고 서비스"""

    @staticmethod
    def create_reflection(
        db: Session,
        reflection_date: date,
        reflection_text: str,
        satisfaction_score: Optional[int] = None,
        energy_level: Optional[int] = None
    ) -> DailyReflection:
        """일일 회고 생성"""

        # 해당 날짜의 할 일 통계 계산
        # - 완료된 할일: 완료한 날짜 기준
        # - 미완료 할일: 자동 이월 포함, 명시적 미래 미룸 제외
        from sqlalchemy import and_, or_, func

        todos = db.query(DailyTodo).filter(
            or_(
                # 1. 완료된 할일: 완료한 날짜가 회고 날짜와 같음
                and_(
                    DailyTodo.is_completed == True,
                    func.date(DailyTodo.completed_at) == reflection_date
                ),
                # 2. 미완료 할일: 생성 날짜가 회고 날짜 이전이고,
                #    scheduled_date가 회고 날짜 이전 또는 같음 (또는 None)
                #    -> 자동 이월 포함, 명시적 미래 미룸 제외
                and_(
                    DailyTodo.is_completed == False,
                    DailyTodo.created_date <= reflection_date,
                    or_(
                        DailyTodo.scheduled_date == None,
                        DailyTodo.scheduled_date <= reflection_date
                    )
                )
            )
        ).all()

        total_todos = len(todos)
        completed_todos = len([t for t in todos if t.is_completed])
        completion_rate = (completed_todos / total_todos * 100) if total_todos > 0 else 0.0

        # 할일 목록 스냅샷 생성
        todos_snapshot = {
            "completed": [
                {
                    "id": t.id,
                    "title": t.title,
                    "category": t.category.value,
                    "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                    "estimated_minutes": t.estimated_minutes,
                    "actual_minutes": t.actual_minutes
                }
                for t in todos if t.is_completed
            ],
            "incomplete": [
                {
                    "id": t.id,
                    "title": t.title,
                    "category": t.category.value,
                    "estimated_minutes": t.estimated_minutes
                }
                for t in todos if not t.is_completed
            ]
        }

        # 기존 회고가 있으면 업데이트, 없으면 생성
        existing_reflection = db.query(DailyReflection).filter(
            DailyReflection.reflection_date == reflection_date
        ).first()

        if existing_reflection:
            # 업데이트
            existing_reflection.reflection_text = reflection_text
            existing_reflection.total_todos = total_todos
            existing_reflection.completed_todos = completed_todos
            existing_reflection.completion_rate = completion_rate
            existing_reflection.todos_snapshot = todos_snapshot
            existing_reflection.satisfaction_score = satisfaction_score
            existing_reflection.energy_level = energy_level
            existing_reflection.updated_at = get_current_utc_datetime()

            db.commit()
            db.refresh(existing_reflection)
            return existing_reflection
        else:
            # 새로 생성 (UTC 시간으로 저장)
            current_utc_time = get_current_utc_datetime()
            reflection = DailyReflection(
                reflection_date=reflection_date,
                reflection_text=reflection_text,
                total_todos=total_todos,
                completed_todos=completed_todos,
                completion_rate=completion_rate,
                todos_snapshot=todos_snapshot,
                satisfaction_score=satisfaction_score,
                energy_level=energy_level,
                created_at=current_utc_time
            )

            db.add(reflection)
            db.commit()
            db.refresh(reflection)
            return reflection

    @staticmethod
    def get_reflection_by_date(db: Session, reflection_date: date) -> Optional[DailyReflection]:
        """특정 날짜의 회고 조회"""
        return db.query(DailyReflection).filter(
            DailyReflection.reflection_date == reflection_date
        ).first()

    @staticmethod
    def get_recent_reflections(db: Session, limit: int = 30) -> List[DailyReflection]:
        """최근 회고 목록 조회"""
        return db.query(DailyReflection).order_by(
            desc(DailyReflection.reflection_date)
        ).limit(limit).all()

    @staticmethod
    def get_reflections_by_month(db: Session, year: int, month: int) -> List[DailyReflection]:
        """특정 월의 회고 목록 조회"""
        from calendar import monthrange
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)

        return db.query(DailyReflection).filter(
            DailyReflection.reflection_date >= start_date,
            DailyReflection.reflection_date <= end_date
        ).order_by(desc(DailyReflection.reflection_date)).all()

    @staticmethod
    def delete_reflection(db: Session, reflection_date: date) -> bool:
        """회고 삭제"""
        reflection = db.query(DailyReflection).filter(
            DailyReflection.reflection_date == reflection_date
        ).first()

        if reflection:
            db.delete(reflection)
            db.commit()
            return True
        return False

    @staticmethod
    def get_stats_summary(db: Session, days: int = 30) -> dict:
        """회고 통계 요약"""
        from datetime import timedelta

        end_date = get_current_date()
        start_date = end_date - timedelta(days=days)

        reflections = db.query(DailyReflection).filter(
            DailyReflection.reflection_date >= start_date,
            DailyReflection.reflection_date <= end_date
        ).all()

        if not reflections:
            return {
                "total_days": 0,
                "avg_completion_rate": 0.0,
                "avg_satisfaction": 0.0,
                "avg_energy": 0.0,
                "total_todos": 0,
                "total_completed": 0
            }

        total_completion_rate = sum(r.completion_rate for r in reflections)
        satisfactions = [r.satisfaction_score for r in reflections if r.satisfaction_score]
        energies = [r.energy_level for r in reflections if r.energy_level]

        return {
            "total_days": len(reflections),
            "avg_completion_rate": total_completion_rate / len(reflections),
            "avg_satisfaction": sum(satisfactions) / len(satisfactions) if satisfactions else 0.0,
            "avg_energy": sum(energies) / len(energies) if energies else 0.0,
            "total_todos": sum(r.total_todos for r in reflections),
            "total_completed": sum(r.completed_todos for r in reflections)
        }