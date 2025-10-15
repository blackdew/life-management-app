"""
오늘의 할일 남은 개수 계산 오류 테스트
- 다음으로 미룬 작업들이 잘못 카운팅되는 문제를 방지하는 테스트
"""
import pytest
from datetime import date, timedelta
from app.services.daily_todo_service import DailyTodoService
from app.models.todo import DailyTodo, TodoCategory


def test_today_summary_excludes_overdue_todos_from_past(test_db):
    """현재 get_today_summary가 과거 미완료 할일을 카운트하지 않는 문제를 보여주는 테스트"""
    # Given: 어제 미완료 할일과 오늘 할일이 있음
    today = date.today()
    yesterday = today - timedelta(days=1)

    # 어제 생성된 미완료 할일 (오늘 표시되어야 함)
    overdue_todo = DailyTodo(
        title="어제 미완료 할일",
        category=TodoCategory.WORK,
        created_date=yesterday,
        scheduled_date=yesterday,
        is_completed=False
    )

    # 오늘 생성된 할일
    today_todo = DailyTodo(
        title="오늘 할일",
        category=TodoCategory.WORK,
        created_date=today,
        scheduled_date=today,
        is_completed=False
    )

    test_db.add_all([overdue_todo, today_todo])
    test_db.commit()

    # When: 오늘 표시되는 할일들과 요약 계산
    displayed_todos = DailyTodoService.get_today_todos(test_db)
    summary = DailyTodoService.get_today_summary(test_db)

    # Then: 수정 후 표시되는 할일 수와 요약의 수가 일치해야 함
    assert len(displayed_todos) == 2  # 어제 + 오늘 할일 모두 표시
    assert summary["total"] == 2  # 수정 후: 표시되는 할일들과 일치
    assert summary["pending"] == 2  # 수정 후: 표시되는 할일들과 일치


def test_today_summary_should_include_postponed_todos_to_today(test_db):
    """다른 날에서 오늘로 미룬 작업들은 오늘 카운트에 포함되어야 함"""
    # Given: 어제 생성되었지만 오늘로 미룬 할일
    today = date.today()
    yesterday = today - timedelta(days=1)

    # 어제 생성되었지만 오늘로 미룬 할일
    postponed_todo = DailyTodo(
        title="어제에서 오늘로 미룬 할일",
        category=TodoCategory.WORK,
        created_date=yesterday,
        scheduled_date=today,  # 오늘로 미룸
        postpone_count=1
    )

    # 오늘 생성된 일반 할일
    normal_todo = DailyTodo(
        title="오늘 할일",
        category=TodoCategory.WORK,
        created_date=today,
        scheduled_date=today
    )

    test_db.add_all([postponed_todo, normal_todo])
    test_db.commit()

    # When: 오늘의 할일 목록 조회
    today_todos = DailyTodoService.get_today_todos(test_db)

    # Then: 두 할일 모두 포함되어야 함
    assert len(today_todos) == 2
    todo_titles = [todo.title for todo in today_todos]
    assert "어제에서 오늘로 미룬 할일" in todo_titles
    assert "오늘 할일" in todo_titles



def test_fixed_today_summary_matches_displayed_todos(test_db):
    """수정된 요약 계산이 실제 표시되는 할일들과 일치해야 함 (통과해야 할 테스트)"""
    # Given: 복잡한 시나리오 (위와 동일)
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    today_todo1 = DailyTodo(
        title="오늘 할일 1",
        category=TodoCategory.WORK,
        created_date=today,
        scheduled_date=today,
        is_completed=False
    )

    today_todo2 = DailyTodo(
        title="오늘 완료한 할일",
        category=TodoCategory.WORK,
        created_date=today,
        scheduled_date=today,
        is_completed=True
    )

    postponed_away = DailyTodo(
        title="내일로 미룬 할일",
        category=TodoCategory.WORK,
        created_date=today,
        scheduled_date=tomorrow,
        postpone_count=1,
        is_completed=False
    )

    postponed_to_today = DailyTodo(
        title="어제에서 오늘로 미룬 할일",
        category=TodoCategory.WORK,
        created_date=yesterday,
        scheduled_date=today,
        postpone_count=1,
        is_completed=False
    )

    overdue_todo = DailyTodo(
        title="어제 미완료 할일",
        category=TodoCategory.WORK,
        created_date=yesterday,
        scheduled_date=yesterday,
        is_completed=False
    )

    test_db.add_all([
        today_todo1, today_todo2, postponed_away,
        postponed_to_today, overdue_todo
    ])
    test_db.commit()

    # When: 수정된 요약 계산 함수 사용
    displayed_todos = DailyTodoService.get_today_todos(test_db)
    fixed_summary = DailyTodoService.get_today_summary(test_db)

    # Then: 표시되는 할일과 요약이 정확히 일치해야 함
    displayed_completed = len([t for t in displayed_todos if t.is_completed])
    displayed_pending = len([t for t in displayed_todos if not t.is_completed])
    displayed_total = len(displayed_todos)

    assert fixed_summary["total"] == displayed_total
    assert fixed_summary["pending"] == displayed_pending
    assert fixed_summary["completed"] == displayed_completed
    assert fixed_summary["completion_rate"] == round(displayed_completed / displayed_total * 100, 1) if displayed_total > 0 else 0