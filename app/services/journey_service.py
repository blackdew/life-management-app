"""
여정 서비스 레이어

여정 관련 비즈니스 로직을 처리합니다.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func

from ..models.journey import Journey, JourneyStatus
from ..models.todo import Todo
from ..schemas.journey import JourneyCreate, JourneyUpdate
from ..core.timezone import get_current_utc_datetime


class JourneyService:
    """여정 비즈니스 로직 서비스"""

    @staticmethod
    def get_all_journeys(db: Session) -> List[Journey]:
        """모든 여정 조회

        Args:
            db: 데이터베이스 세션

        Returns:
            여정 목록 (생성일 내림차순)
        """
        try:
            return db.query(Journey).order_by(Journey.created_at.desc()).all()
        except Exception as e:
            raise ValueError(f"여정 목록 조회 중 오류가 발생했습니다: {str(e)}")

    @staticmethod
    def get_journey_by_id(db: Session, journey_id: int) -> Optional[Journey]:
        """ID로 여정 조회

        Args:
            db: 데이터베이스 세션
            journey_id: 여정 ID

        Returns:
            여정 객체 또는 None
        """
        try:
            return db.query(Journey).filter(Journey.id == journey_id).first()
        except Exception as e:
            raise ValueError(f"여정 조회 중 오류가 발생했습니다: {str(e)}")

    @staticmethod
    def create_journey(db: Session, journey_data: JourneyCreate) -> Journey:
        """새 여정 생성

        Args:
            db: 데이터베이스 세션
            journey_data: 여정 생성 데이터

        Returns:
            생성된 여정 객체

        Raises:
            ValueError: 여정 생성 실패 시
        """
        try:
            current_utc_time = get_current_utc_datetime()
            db_journey = Journey(**journey_data.model_dump(), created_at=current_utc_time)
            db.add(db_journey)
            db.commit()
            db.refresh(db_journey)
            return db_journey
        except Exception as e:
            db.rollback()
            raise ValueError(f"여정 생성 중 오류가 발생했습니다: {str(e)}")

    @staticmethod
    def update_journey(
        db: Session, journey_id: int, journey_data: JourneyUpdate
    ) -> Optional[Journey]:
        """여정 수정"""
        db_journey = JourneyService.get_journey_by_id(db, journey_id)
        if not db_journey:
            return None

        update_data = journey_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_journey, field, value)

        db.commit()
        db.refresh(db_journey)
        return db_journey

    @staticmethod
    def delete_journey(db: Session, journey_id: int) -> bool:
        """여정 삭제"""
        db_journey = JourneyService.get_journey_by_id(db, journey_id)
        if not db_journey:
            return False

        db.delete(db_journey)
        db.commit()
        return True

    @staticmethod
    def calculate_journey_progress(db: Session, journey_id: int) -> float:
        """여정 진행률 계산 (0-100)

        Args:
            db: 데이터베이스 세션
            journey_id: 여정 ID

        Returns:
            진행률 (0.0~100.0)

        Raises:
            ValueError: 여정이 존재하지 않는 경우
        """
        try:
            # 여정 존재 확인
            journey = db.query(Journey).filter(Journey.id == journey_id).first()
            if not journey:
                raise ValueError(f"ID {journey_id}인 여정을 찾을 수 없습니다")

            # 해당 여정의 전체 TODO 수와 완료된 TODO 수 조회
            total_todos = (
                db.query(func.count(Todo.id))
                .filter(Todo.journey_id == journey_id)
                .scalar()
                or 0
            )

            if total_todos == 0:
                return 0.0

            completed_todos = (
                db.query(func.count(Todo.id))
                .filter(
                    and_(Todo.journey_id == journey_id, Todo.is_completed == True)
                )
                .scalar()
                or 0
            )

            return (completed_todos / total_todos) * 100.0

        except Exception as e:
            raise ValueError(f"진행률 계산 중 오류가 발생했습니다: {str(e)}")

    @staticmethod
    def update_journey_progress(
        db: Session, journey_id: int
    ) -> Optional[Journey]:
        """여정 진행률 업데이트"""
        db_journey = JourneyService.get_journey_by_id(db, journey_id)
        if not db_journey:
            return None

        # 진행률 계산 및 업데이트
        progress = JourneyService.calculate_journey_progress(db, journey_id)
        db_journey.progress = progress  # type: ignore

        # 진행률에 따른 상태 자동 업데이트
        if progress == 100.0:
            db_journey.status = JourneyStatus.COMPLETED  # type: ignore
        elif progress > 0:
            db_journey.status = JourneyStatus.ACTIVE  # type: ignore
        else:
            db_journey.status = JourneyStatus.PLANNING  # type: ignore

        db.commit()
        db.refresh(db_journey)
        return db_journey

    @staticmethod
    def get_journeys_with_todos(db: Session) -> List[Journey]:
        """TODO를 포함한 여정 조회"""
        return (
            db.query(Journey)
            .options(joinedload(Journey.todos))
            .order_by(Journey.created_at.desc())
            .all()
        )

    @staticmethod
    def get_active_journeys(db: Session) -> List[Journey]:
        """진행 중인 여정 조회"""
        return (
            db.query(Journey)
            .filter(Journey.status == JourneyStatus.ACTIVE)
            .order_by(Journey.created_at.desc())
            .all()
        )

    @staticmethod
    def get_journey_statistics(db: Session, journey_id: int) -> dict:
        """여정 통계 정보"""
        journey = JourneyService.get_journey_by_id(db, journey_id)
        if not journey:
            return {}

        # TODO 통계 계산
        todos_query = db.query(Todo).filter(Todo.journey_id == journey_id)

        total_todos = todos_query.count()
        completed_todos = todos_query.filter(Todo.is_completed == True).count()
        pending_todos = total_todos - completed_todos

        # 예상 시간 vs 실제 시간
        estimated_time = (
            db.query(func.coalesce(func.sum(Todo.estimated_time), 0))
            .filter(Todo.journey_id == journey_id)
            .scalar()
        )

        actual_time = (
            db.query(func.coalesce(func.sum(Todo.actual_time), 0))
            .filter(
                and_(
                    Todo.journey_id == journey_id,
                    Todo.is_completed == True,
                    Todo.actual_time.isnot(None),
                )
            )
            .scalar()
        )

        return {
            "journey_id": journey_id,
            "total_todos": total_todos,
            "completed_todos": completed_todos,
            "pending_todos": pending_todos,
            "progress_percentage": JourneyService.calculate_journey_progress(
                db, journey_id
            ),
            "estimated_total_time": estimated_time,
            "actual_total_time": actual_time,
            "status": journey.status.value if journey.status else None,
        }