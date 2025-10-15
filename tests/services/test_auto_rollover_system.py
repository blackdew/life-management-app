"""
할일 자동 이월 시스템 테스트
"""
import pytest
from datetime import date, timedelta, datetime
from sqlalchemy.orm import Session

from app.models.todo import DailyTodo, TodoCategory
from app.services.daily_todo_service import DailyTodoService


class TestAutoRolloverSystem:
    """할일 자동 이월 시스템 테스트"""

    def test_today_todos_include_past_incomplete(self, test_db: Session):
        """오늘 할일 목록에 과거 미완료 할일이 포함되는지 테스트"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        three_days_ago = today - timedelta(days=3)

        # 어제 미완료 할일
        todo_yesterday = DailyTodo(
            title="어제 미완료 할일",
            category=TodoCategory.WORK,
            created_date=yesterday,
            is_completed=False
        )

        # 3일 전 미완료 할일
        todo_three_days_ago = DailyTodo(
            title="3일 전 미완료 할일",
            category=TodoCategory.PERSONAL,
            created_date=three_days_ago,
            is_completed=False
        )

        # 오늘 할일
        todo_today = DailyTodo(
            title="오늘 할일",
            category=TodoCategory.LEARNING,
            created_date=today,
            is_completed=False
        )

        test_db.add_all([todo_yesterday, todo_three_days_ago, todo_today])
        test_db.commit()

        # 오늘 할일 목록 조회
        todos = DailyTodoService.get_today_todos(test_db)

        assert len(todos) == 3
        titles = [todo.title for todo in todos]
        assert "어제 미완료 할일" in titles
        assert "3일 전 미완료 할일" in titles
        assert "오늘 할일" in titles

    def test_completed_past_todos_excluded_from_today(self, test_db: Session):
        """과거 완료된 할일은 오늘 목록에서 제외되는지 테스트"""
        today = date.today()
        yesterday = today - timedelta(days=1)

        # 어제 완료된 할일
        todo_completed_yesterday = DailyTodo(
            title="어제 완료된 할일",
            category=TodoCategory.WORK,
            created_date=yesterday,
            is_completed=True,
            completion_reflection="어제 완료했습니다."
        )

        # 어제 미완료 할일
        todo_incomplete_yesterday = DailyTodo(
            title="어제 미완료 할일",
            category=TodoCategory.PERSONAL,
            created_date=yesterday,
            is_completed=False
        )

        # 오늘 할일
        todo_today = DailyTodo(
            title="오늘 할일",
            category=TodoCategory.LEARNING,
            created_date=today,
            is_completed=False
        )

        test_db.add_all([todo_completed_yesterday, todo_incomplete_yesterday, todo_today])
        test_db.commit()

        # 오늘 할일 목록 조회
        todos = DailyTodoService.get_today_todos(test_db)

        assert len(todos) == 2
        titles = [todo.title for todo in todos]
        assert "어제 완료된 할일" not in titles
        assert "어제 미완료 할일" in titles
        assert "오늘 할일" in titles

    def test_future_scheduled_todos_excluded(self, test_db: Session):
        """미래 예정 할일은 해당 날짜까지 숨겨지는지 테스트"""
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # 내일 예정 할일
        todo_scheduled_tomorrow = DailyTodo(
            title="내일 예정 할일",
            category=TodoCategory.WORK,
            created_date=today,
            scheduled_date=tomorrow,
            is_completed=False
        )

        # 오늘 할일
        todo_today = DailyTodo(
            title="오늘 할일",
            category=TodoCategory.PERSONAL,
            created_date=today,
            is_completed=False
        )

        test_db.add_all([todo_scheduled_tomorrow, todo_today])
        test_db.commit()

        # 오늘 할일 목록 조회
        todos = DailyTodoService.get_today_todos(test_db)

        assert len(todos) == 1
        assert todos[0].title == "오늘 할일"

    def test_days_overdue_calculation(self, test_db: Session):
        """경과일 계산이 정확한지 테스트"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        three_days_ago = today - timedelta(days=3)

        # 어제 생성된 할일
        todo_yesterday = DailyTodo(
            title="어제 할일",
            category=TodoCategory.WORK,
            created_date=yesterday,
            is_completed=False
        )

        # 3일 전 생성된 할일
        todo_three_days_ago = DailyTodo(
            title="3일 전 할일",
            category=TodoCategory.PERSONAL,
            created_date=three_days_ago,
            is_completed=False
        )

        # 오늘 생성된 할일
        todo_today = DailyTodo(
            title="오늘 할일",
            category=TodoCategory.LEARNING,
            created_date=today,
            is_completed=False
        )

        test_db.add_all([todo_yesterday, todo_three_days_ago, todo_today])
        test_db.commit()

        # 오늘 할일 목록 조회
        todos = DailyTodoService.get_today_todos(test_db)

        # 할일이 포함되는지 확인 (days_overdue는 API 응답에서만 계산됨)
        assert len(todos) == 3
        titles = [todo.title for todo in todos]
        assert "어제 할일" in titles
        assert "3일 전 할일" in titles
        assert "오늘 할일" in titles

    def test_scheduled_todo_overdue_status(self, test_db: Session):
        """예정된 할일의 지연 상태 테스트"""
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # 내일 예정인데 오늘까지 안한 할일 (실제로는 오늘 목록에 안 나타남)
        todo_scheduled = DailyTodo(
            title="예정된 할일",
            category=TodoCategory.WORK,
            created_date=today - timedelta(days=2),
            scheduled_date=tomorrow,
            is_completed=False
        )

        test_db.add(todo_scheduled)
        test_db.commit()

        # 오늘 할일 목록에는 나타나지 않아야 함
        todos = DailyTodoService.get_today_todos(test_db)
        assert len(todos) == 0

    def test_completed_today_included_in_today_list(self, test_db: Session):
        """오늘 완료한 할일은 오늘 목록에 포함되는지 테스트"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        now = datetime.now()

        # 어제 생성해서 오늘 완료한 할일
        todo_completed_today = DailyTodo(
            title="어제 만들어 오늘 완료한 할일",
            category=TodoCategory.WORK,
            created_date=yesterday,
            is_completed=True,
            completed_at=now,
            completion_reflection="오늘 완료했습니다."
        )

        # 오늘 생성해서 완료한 할일
        todo_created_completed_today = DailyTodo(
            title="오늘 만들어 완료한 할일",
            category=TodoCategory.PERSONAL,
            created_date=today,
            is_completed=True,
            completed_at=now,
            completion_reflection="오늘 완료했습니다."
        )

        test_db.add_all([todo_completed_today, todo_created_completed_today])
        test_db.commit()

        # 오늘 할일 목록 조회
        todos = DailyTodoService.get_today_todos(test_db)

        # 오늘 생성한 완료 할일과 과거 생성해서 오늘 완료한 할일 포함
        assert len(todos) == 2
        titles = [todo.title for todo in todos]
        assert "어제 만들어 오늘 완료한 할일" in titles
        assert "오늘 만들어 완료한 할일" in titles

    def test_mixed_scenario_comprehensive(self, test_db: Session):
        """복합 시나리오 종합 테스트"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        tomorrow = today + timedelta(days=1)
        now = datetime.now()

        todos = [
            # 어제 생성, 미완료 (포함됨)
            DailyTodo(title="어제 미완료", category=TodoCategory.WORK,
                     created_date=yesterday, is_completed=False),

            # 어제 생성, 어제 완료 (제외됨)
            DailyTodo(title="어제 완료", category=TodoCategory.WORK,
                     created_date=yesterday, is_completed=True,
                     completed_at=datetime.combine(yesterday, datetime.now().time()),
                     completion_reflection="어제 완료"),

            # 2일 전 생성, 오늘 완료 (포함됨)
            DailyTodo(title="2일 전 생성 오늘 완료", category=TodoCategory.PERSONAL,
                     created_date=two_days_ago, is_completed=True,
                     completed_at=now,
                     completion_reflection="오늘 완료"),

            # 오늘 생성, 미완료 (포함됨)
            DailyTodo(title="오늘 미완료", category=TodoCategory.LEARNING,
                     created_date=today, is_completed=False),

            # 오늘 생성, 내일 예정 (제외됨)
            DailyTodo(title="내일 예정", category=TodoCategory.HEALTH,
                     created_date=today, scheduled_date=tomorrow, is_completed=False),
        ]

        test_db.add_all(todos)
        test_db.commit()

        # 오늘 할일 목록 조회
        result_todos = DailyTodoService.get_today_todos(test_db)

        # 미완료 할일 2개 + 오늘 완료한 할일 1개 = 3개 포함
        assert len(result_todos) == 3
        titles = [todo.title for todo in result_todos]

        # 포함되어야 할 할일들
        assert "어제 미완료" in titles
        assert "오늘 미완료" in titles
        assert "2일 전 생성 오늘 완료" in titles  # 오늘 완료한 할일이므로 포함

        # 제외되어야 할 할일들
        assert "어제 완료" not in titles  # 어제 완료한 할일이므로 제외
        assert "내일 예정" not in titles