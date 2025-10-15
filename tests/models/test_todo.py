"""
Todo 모델 테스트

DailyTodo 모델의 메서드들을 테스트합니다.
"""
import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.models.todo import DailyTodo, Todo, TodoCategory
from app.models.journey import Journey, JourneyStatus


class TestDailyTodoModel:
    """DailyTodo 모델 테스트"""

    def test_is_today_property_true(self, test_db: Session):
        """오늘 생성된 할일의 is_today 속성 테스트"""
        todo = DailyTodo(
            title="오늘 할일",
            category=TodoCategory.WORK,
            created_date=date.today()
        )
        test_db.add(todo)
        test_db.commit()

        assert todo.is_today is True

    def test_is_today_property_false(self, test_db: Session):
        """어제 생성된 할일의 is_today 속성 테스트"""
        from datetime import timedelta
        yesterday = date.today() - timedelta(days=1)

        todo = DailyTodo(
            title="어제 할일",
            category=TodoCategory.PERSONAL,
            created_date=yesterday
        )
        test_db.add(todo)
        test_db.commit()

        assert todo.is_today is False

    def test_complete_method(self, test_db: Session):
        """할일 완료 메서드 테스트"""
        todo = DailyTodo(
            title="완료할 할일",
            category=TodoCategory.HEALTH,
            is_completed=False
        )
        test_db.add(todo)
        test_db.commit()

        # 완료 처리
        todo.complete()
        test_db.commit()

        assert todo.is_completed is True
        assert todo.completed_at is not None
        assert isinstance(todo.completed_at, datetime)

    def test_uncomplete_method(self, test_db: Session):
        """할일 완료 취소 메서드 테스트"""
        todo = DailyTodo(
            title="완료 취소할 할일",
            category=TodoCategory.LEARNING,
            is_completed=True,
            completed_at=datetime.now()
        )
        test_db.add(todo)
        test_db.commit()

        # 완료 취소
        todo.uncomplete()
        test_db.commit()

        assert todo.is_completed is False
        assert todo.completed_at is None

    def test_complete_uncomplete_cycle(self, test_db: Session):
        """완료-취소-완료 사이클 테스트"""
        todo = DailyTodo(
            title="사이클 테스트",
            category=TodoCategory.OTHER
        )
        test_db.add(todo)
        test_db.commit()

        # 초기 상태 확인
        assert todo.is_completed is False
        assert todo.completed_at is None

        # 완료 처리
        todo.complete()
        test_db.commit()
        assert todo.is_completed is True
        assert todo.completed_at is not None

        # 완료 취소
        todo.uncomplete()
        test_db.commit()
        assert todo.is_completed is False
        assert todo.completed_at is None

        # 다시 완료
        todo.complete()
        test_db.commit()
        assert todo.is_completed is True
        assert todo.completed_at is not None


class TestTodoModel:
    """Todo 모델 테스트"""

    def test_todo_complete_method(self, test_db: Session):
        """Todo 완료 메서드 테스트"""
        from app.models.journey import Journey, JourneyStatus

        milestone = Journey(
            title="테스트 마일스톤",
            start_date=date.today(),
            end_date=date.today(),
            status=JourneyStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        test_db.add(milestone)
        test_db.commit()

        todo = Todo(
            title="완료할 Todo",
            description="설명",
            journey_id=milestone.id,
            is_completed=False
        )
        test_db.add(todo)
        test_db.commit()

        # 완료 처리
        todo.complete()
        test_db.commit()

        assert todo.is_completed is True
        assert todo.completed_at is not None
        assert isinstance(todo.completed_at, datetime)

    def test_todo_uncomplete_method(self, test_db: Session):
        """Todo 완료 취소 메서드 테스트"""
        from app.models.journey import Journey, JourneyStatus

        milestone = Journey(
            title="테스트 마일스톤",
            start_date=date.today(),
            end_date=date.today(),
            status=JourneyStatus.ACTIVE,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        test_db.add(milestone)
        test_db.commit()

        todo = Todo(
            title="완료 취소할 Todo",
            description="설명",
            journey_id=milestone.id,
            is_completed=True,
            completed_at=datetime.now()
        )
        test_db.add(todo)
        test_db.commit()

        # 완료 취소
        todo.uncomplete()
        test_db.commit()

        assert todo.is_completed is False
        assert todo.completed_at is None