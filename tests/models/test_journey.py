"""
Journey 모델 테스트

여정 모델의 메서드들을 테스트합니다.
"""
import pytest
from datetime import date
from sqlalchemy.orm import Session

from app.models.journey import Journey, JourneyStatus
from app.models.todo import Todo, DailyTodo, TodoCategory


class TestJourneyModel:
    """Journey 모델 테스트"""

    def test_calculate_actual_progress_empty(self, test_db: Session):
        """할일이 없는 여정의 진행률 계산 테스트"""
        journey = Journey(
            title="빈 여정",
            start_date=date.today(),
            end_date=date.today(),
            status=JourneyStatus.ACTIVE
        )
        test_db.add(journey)
        test_db.commit()
        test_db.refresh(journey)

        progress = journey.calculate_actual_progress()
        assert progress == 0.0

    def test_calculate_actual_progress_with_todos(self, test_db: Session):
        """Todo와 DailyTodo가 있는 여정의 진행률 계산 테스트"""
        journey = Journey(
            title="할일 있는 여정",
            start_date=date.today(),
            end_date=date.today(),
            status=JourneyStatus.ACTIVE
        )
        test_db.add(journey)
        test_db.commit()
        test_db.refresh(journey)

        # Todo 추가 (완료된 것)
        todo1 = Todo(
            title="완료된 할일",
            description="완료된 할일입니다",
            journey_id=journey.id,
            is_completed=True
        )

        # Todo 추가 (미완료)
        todo2 = Todo(
            title="미완료 할일",
            description="미완료 할일입니다",
            journey_id=journey.id,
            is_completed=False
        )

        # DailyTodo 추가 (완료된 것)
        daily_todo1 = DailyTodo(
            title="완료된 일일 할일",
            category=TodoCategory.WORK,
            scheduled_date=date.today(),
            journey_id=journey.id,
            is_completed=True
        )

        # DailyTodo 추가 (미완료)
        daily_todo2 = DailyTodo(
            title="미완료 일일 할일",
            category=TodoCategory.PERSONAL,
            scheduled_date=date.today(),
            journey_id=journey.id,
            is_completed=False
        )

        test_db.add_all([todo1, todo2, daily_todo1, daily_todo2])
        test_db.commit()

        # 진행률 계산: 4개 중 2개 완료 = 50%
        progress = journey.calculate_actual_progress()
        assert progress == 50.0

    def test_calculate_actual_progress_all_completed(self, test_db: Session):
        """모든 할일이 완료된 여정의 진행률 계산 테스트"""
        journey = Journey(
            title="모두 완료된 여정",
            start_date=date.today(),
            end_date=date.today(),
            status=JourneyStatus.ACTIVE
        )
        test_db.add(journey)
        test_db.commit()
        test_db.refresh(journey)

        # 모든 할일 완료
        todo = Todo(
            title="완료된 할일",
            description="완료",
            journey_id=journey.id,
            is_completed=True
        )

        daily_todo = DailyTodo(
            title="완료된 일일 할일",
            category=TodoCategory.HEALTH,
            scheduled_date=date.today(),
            journey_id=journey.id,
            is_completed=True
        )

        test_db.add_all([todo, daily_todo])
        test_db.commit()

        # 진행률 계산: 2개 중 2개 완료 = 100%
        progress = journey.calculate_actual_progress()
        assert progress == 100.0

    def test_calculate_actual_progress_partial_completion(self, test_db: Session):
        """부분 완료된 여정의 진행률 계산 테스트 (소수점 테스트)"""
        journey = Journey(
            title="부분 완료 여정",
            start_date=date.today(),
            end_date=date.today(),
            status=JourneyStatus.ACTIVE
        )
        test_db.add(journey)
        test_db.commit()
        test_db.refresh(journey)

        # 3개 중 1개만 완료 (33.3%)
        todo1 = Todo(title="완료1", journey_id=journey.id, is_completed=True)
        todo2 = Todo(title="미완료1", journey_id=journey.id, is_completed=False)
        todo3 = Todo(title="미완료2", journey_id=journey.id, is_completed=False)

        test_db.add_all([todo1, todo2, todo3])
        test_db.commit()

        # 진행률 계산: 3개 중 1개 완료 = 33.3% (반올림)
        progress = journey.calculate_actual_progress()
        assert progress == 33.3

    def test_journey_repr(self, test_db: Session):
        """여정 __repr__ 메서드 테스트"""
        journey = Journey(
            title="테스트 여정",
            start_date=date.today(),
            end_date=date.today(),
            status=JourneyStatus.ACTIVE,
            progress=75.5
        )
        test_db.add(journey)
        test_db.commit()
        test_db.refresh(journey)

        repr_str = repr(journey)
        assert "Journey" in repr_str
        assert str(journey.id) in repr_str
        assert "테스트 여정" in repr_str
        assert "진행중" in repr_str  # JourneyStatus.ACTIVE.value
        assert "75.5" in repr_str

    def test_journey_repr_with_different_status(self, test_db: Session):
        """다른 상태의 여정 __repr__ 메서드 테스트"""
        journey = Journey(
            title="완료된 여정",
            start_date=date.today(),
            end_date=date.today(),
            status=JourneyStatus.COMPLETED,
            progress=100.0
        )
        test_db.add(journey)
        test_db.commit()
        test_db.refresh(journey)

        repr_str = repr(journey)
        assert "완료된 여정" in repr_str
        assert "완료" in repr_str  # JourneyStatus.COMPLETED.value
        assert "100.0" in repr_str

    def test_calculate_actual_progress_only_todos(self, test_db: Session):
        """Todo만 있는 여정의 진행률 계산 테스트"""
        journey = Journey(
            title="Todo만 있는 여정",
            start_date=date.today(),
            end_date=date.today(),
            status=JourneyStatus.ACTIVE
        )
        test_db.add(journey)
        test_db.commit()
        test_db.refresh(journey)

        # Todo만 추가
        todo1 = Todo(title="완료 Todo", journey_id=journey.id, is_completed=True)
        todo2 = Todo(title="미완료 Todo", journey_id=journey.id, is_completed=False)

        test_db.add_all([todo1, todo2])
        test_db.commit()

        progress = journey.calculate_actual_progress()
        assert progress == 50.0

    def test_calculate_actual_progress_only_daily_todos(self, test_db: Session):
        """DailyTodo만 있는 여정의 진행률 계산 테스트"""
        journey = Journey(
            title="DailyTodo만 있는 여정",
            start_date=date.today(),
            end_date=date.today(),
            status=JourneyStatus.ACTIVE
        )
        test_db.add(journey)
        test_db.commit()
        test_db.refresh(journey)

        # DailyTodo만 추가
        daily_todo1 = DailyTodo(
            title="완료 DailyTodo",
            category=TodoCategory.LEARNING,
            scheduled_date=date.today(),
            journey_id=journey.id,
            is_completed=True
        )
        daily_todo2 = DailyTodo(
            title="미완료 DailyTodo",
            category=TodoCategory.OTHER,
            scheduled_date=date.today(),
            journey_id=journey.id,
            is_completed=False
        )

        test_db.add_all([daily_todo1, daily_todo2])
        test_db.commit()

        progress = journey.calculate_actual_progress()
        assert progress == 50.0