"""
오늘의 진행상황 완료/남은일 개수 정확성 검증 테스트
- 다양한 시나리오에서 완료 개수와 남은일 개수가 정확하게 계산되는지 검증
"""
import pytest
from datetime import date, datetime, timedelta
from app.services.daily_todo_service import DailyTodoService
from app.models.todo import DailyTodo, TodoCategory


class TestTodayProgressAccuracy:
    """오늘의 진행상황 정확성 테스트"""

    def test_empty_todos_shows_zero_progress(self, test_db):
        """할일이 없을 때 모든 개수가 0으로 표시되는지 확인"""
        # When: 할일이 없는 상태에서 요약 조회
        summary = DailyTodoService.get_today_summary(test_db)

        # Then: 모든 개수가 0이어야 함
        assert summary["total"] == 0
        assert summary["completed"] == 0
        assert summary["pending"] == 0
        assert summary["completion_rate"] == 0

    def test_only_completed_todos_shows_100_percent(self, test_db):
        """모든 할일이 완료되었을 때 100% 완료율 표시"""
        # Given: 완료된 할일들만 있음
        today = date.today()

        todos = [
            DailyTodo(
                title=f"완료된 할일 {i}",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=today,
                is_completed=True,
                completed_at=datetime.now()
            )
            for i in range(3)
        ]

        test_db.add_all(todos)
        test_db.commit()

        # When: 요약 조회
        summary = DailyTodoService.get_today_summary(test_db)

        # Then: 모든 할일이 완료되어 100% 완료율
        assert summary["total"] == 3
        assert summary["completed"] == 3
        assert summary["pending"] == 0
        assert summary["completion_rate"] == 100.0

    def test_only_pending_todos_shows_zero_percent(self, test_db):
        """모든 할일이 미완료일 때 0% 완료율 표시"""
        # Given: 미완료 할일들만 있음
        today = date.today()

        todos = [
            DailyTodo(
                title=f"미완료 할일 {i}",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=today,
                is_completed=False
            )
            for i in range(5)
        ]

        test_db.add_all(todos)
        test_db.commit()

        # When: 요약 조회
        summary = DailyTodoService.get_today_summary(test_db)

        # Then: 모든 할일이 미완료로 0% 완료율
        assert summary["total"] == 5
        assert summary["completed"] == 0
        assert summary["pending"] == 5
        assert summary["completion_rate"] == 0.0

    def test_mixed_completion_status_calculates_correctly(self, test_db):
        """완료/미완료 할일이 섞여있을 때 정확한 계산"""
        # Given: 완료 2개, 미완료 3개 할일
        today = date.today()

        # 완료된 할일 2개
        completed_todos = [
            DailyTodo(
                title=f"완료된 할일 {i}",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=today,
                is_completed=True,
                completed_at=datetime.now()
            )
            for i in range(2)
        ]

        # 미완료 할일 3개
        pending_todos = [
            DailyTodo(
                title=f"미완료 할일 {i}",
                category=TodoCategory.PERSONAL,
                created_date=today,
                scheduled_date=today,
                is_completed=False
            )
            for i in range(3)
        ]

        test_db.add_all(completed_todos + pending_todos)
        test_db.commit()

        # When: 요약 조회
        summary = DailyTodoService.get_today_summary(test_db)

        # Then: 정확한 개수와 완료율 계산
        assert summary["total"] == 5
        assert summary["completed"] == 2
        assert summary["pending"] == 3
        assert summary["completion_rate"] == 40.0  # 2/5 * 100

    def test_overdue_todos_included_in_progress(self, test_db):
        """과거 미완료 할일이 오늘 진행상황에 포함되는지 확인"""
        # Given: 어제 미완료 할일과 오늘 할일
        today = date.today()
        yesterday = today - timedelta(days=1)

        # 어제 미완료 할일 (오늘 표시되어야 함)
        overdue_todo = DailyTodo(
            title="어제 미완료 할일",
            category=TodoCategory.WORK,
            created_date=yesterday,
            scheduled_date=yesterday,
            is_completed=False
        )

        # 오늘 완료한 할일
        today_completed = DailyTodo(
            title="오늘 완료한 할일",
            category=TodoCategory.WORK,
            created_date=today,
            scheduled_date=today,
            is_completed=True,
            completed_at=datetime.now()
        )

        # 오늘 미완료 할일
        today_pending = DailyTodo(
            title="오늘 미완료 할일",
            category=TodoCategory.WORK,
            created_date=today,
            scheduled_date=today,
            is_completed=False
        )

        test_db.add_all([overdue_todo, today_completed, today_pending])
        test_db.commit()

        # When: 요약 조회
        summary = DailyTodoService.get_today_summary(test_db)

        # Then: 어제 미완료 할일도 오늘 진행상황에 포함
        assert summary["total"] == 3  # 어제 미완료 + 오늘 완료 + 오늘 미완료
        assert summary["completed"] == 1  # 오늘 완료한 것만
        assert summary["pending"] == 2  # 어제 미완료 + 오늘 미완료
        assert summary["completion_rate"] == 33.3  # 1/3 * 100, 소수점 1자리

    def test_postponed_todos_excluded_from_today_progress(self, test_db):
        """미룬 할일이 오늘 진행상황에서 제외되는지 확인"""
        # Given: 오늘 생성했지만 내일로 미룬 할일과 일반 할일
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # 내일로 미룬 할일 (오늘 표시되면 안됨)
        postponed_todo = DailyTodo(
            title="내일로 미룬 할일",
            category=TodoCategory.WORK,
            created_date=today,
            scheduled_date=tomorrow,
            postpone_count=1,
            is_completed=False
        )

        # 오늘 할 예정인 할일들
        today_todos = [
            DailyTodo(
                title="오늘 완료한 할일",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=today,
                is_completed=True,
                completed_at=datetime.now()
            ),
            DailyTodo(
                title="오늘 미완료 할일",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=today,
                is_completed=False
            )
        ]

        test_db.add_all([postponed_todo] + today_todos)
        test_db.commit()

        # When: 요약 조회
        summary = DailyTodoService.get_today_summary(test_db)

        # Then: 미룬 할일은 제외하고 계산
        assert summary["total"] == 2  # 미룬 할일 제외
        assert summary["completed"] == 1
        assert summary["pending"] == 1
        assert summary["completion_rate"] == 50.0

    def test_postponed_to_today_included_in_progress(self, test_db):
        """다른 날에서 오늘로 미룬 할일이 포함되는지 확인"""
        # Given: 어제 생성되어 오늘로 미룬 할일
        today = date.today()
        yesterday = today - timedelta(days=1)

        # 어제에서 오늘로 미룬 할일
        postponed_to_today = DailyTodo(
            title="어제에서 오늘로 미룬 할일",
            category=TodoCategory.WORK,
            created_date=yesterday,
            scheduled_date=today,
            postpone_count=1,
            is_completed=False
        )

        # 오늘 일반 할일
        today_todo = DailyTodo(
            title="오늘 할일",
            category=TodoCategory.WORK,
            created_date=today,
            scheduled_date=today,
            is_completed=True,
            completed_at=datetime.now()
        )

        test_db.add_all([postponed_to_today, today_todo])
        test_db.commit()

        # When: 요약 조회
        summary = DailyTodoService.get_today_summary(test_db)

        # Then: 오늘로 미룬 할일도 포함
        assert summary["total"] == 2
        assert summary["completed"] == 1
        assert summary["pending"] == 1
        assert summary["completion_rate"] == 50.0

    def test_past_completed_today_included_correctly(self, test_db):
        """과거 할일을 오늘 완료한 경우 정확히 반영되는지 확인"""
        # Given: 어제 생성된 할일을 오늘 완료함
        today = date.today()
        yesterday = today - timedelta(days=1)

        # 어제 생성된 할일을 오늘 완료
        past_todo_completed_today = DailyTodo(
            title="어제 할일을 오늘 완료",
            category=TodoCategory.WORK,
            created_date=yesterday,
            scheduled_date=yesterday,
            is_completed=True,
            completed_at=datetime.now()  # 오늘 완료
        )

        # 오늘 생성된 미완료 할일
        today_pending = DailyTodo(
            title="오늘 미완료 할일",
            category=TodoCategory.WORK,
            created_date=today,
            scheduled_date=today,
            is_completed=False
        )

        test_db.add_all([past_todo_completed_today, today_pending])
        test_db.commit()

        # When: 요약 조회
        summary = DailyTodoService.get_today_summary(test_db)

        # Then: 과거 할일도 오늘 완료된 것으로 포함
        assert summary["total"] == 2
        assert summary["completed"] == 1  # 어제 할일을 오늘 완료
        assert summary["pending"] == 1
        assert summary["completion_rate"] == 50.0

    def test_complex_scenario_accurate_calculation(self, test_db):
        """복잡한 시나리오에서 정확한 계산"""
        # Given: 다양한 상황의 할일들
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        todos = [
            # 1. 오늘 생성 + 오늘 완료
            DailyTodo(
                title="오늘 생성 오늘 완료",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=today,
                is_completed=True,
                completed_at=datetime.now()
            ),
            # 2. 오늘 생성 + 미완료
            DailyTodo(
                title="오늘 생성 미완료",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=today,
                is_completed=False
            ),
            # 3. 어제 생성 + 오늘 완료
            DailyTodo(
                title="어제 생성 오늘 완료",
                category=TodoCategory.WORK,
                created_date=yesterday,
                scheduled_date=yesterday,
                is_completed=True,
                completed_at=datetime.now()
            ),
            # 4. 어제 생성 + 미완료 (자동 이월)
            DailyTodo(
                title="어제 생성 미완료",
                category=TodoCategory.WORK,
                created_date=yesterday,
                scheduled_date=yesterday,
                is_completed=False
            ),
            # 5. 어제 생성 + 오늘로 미룸 + 미완료
            DailyTodo(
                title="어제 생성 오늘로 미룸",
                category=TodoCategory.WORK,
                created_date=yesterday,
                scheduled_date=today,
                postpone_count=1,
                is_completed=False
            ),
            # 6. 오늘 생성 + 내일로 미룸 (오늘 표시 안됨)
            DailyTodo(
                title="오늘 생성 내일로 미룸",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=tomorrow,
                postpone_count=1,
                is_completed=False
            ),
        ]

        test_db.add_all(todos)
        test_db.commit()

        # When: 오늘 표시되는 할일들과 요약 조회
        displayed_todos = DailyTodoService.get_today_todos(test_db)
        summary = DailyTodoService.get_today_summary(test_db)

        # Then: 표시되는 할일들 (1,2,3,4,5번 - 6번은 내일로 미뤄서 제외)
        expected_displayed = 5
        expected_completed = 2  # 1번, 3번
        expected_pending = 3    # 2번, 4번, 5번

        assert len(displayed_todos) == expected_displayed
        assert summary["total"] == expected_displayed
        assert summary["completed"] == expected_completed
        assert summary["pending"] == expected_pending
        assert summary["completion_rate"] == 40.0  # 2/5 * 100

    def test_summary_matches_displayed_todos_always(self, test_db):
        """요약 정보가 항상 표시되는 할일들과 일치하는지 확인"""
        # Given: 임의의 복잡한 할일 데이터
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        todos = [
            # 다양한 상태의 할일들을 생성
            DailyTodo(title="A", created_date=today, scheduled_date=today, is_completed=True, completed_at=datetime.now()),
            DailyTodo(title="B", created_date=today, scheduled_date=today, is_completed=False),
            DailyTodo(title="C", created_date=yesterday, scheduled_date=yesterday, is_completed=False),
            DailyTodo(title="D", created_date=yesterday, scheduled_date=today, is_completed=True, completed_at=datetime.now()),
            DailyTodo(title="E", created_date=today, scheduled_date=tomorrow, is_completed=False),
        ]

        for todo in todos:
            todo.category = TodoCategory.OTHER

        test_db.add_all(todos)
        test_db.commit()

        # When: 표시되는 할일들과 요약 조회
        displayed_todos = DailyTodoService.get_today_todos(test_db)
        summary = DailyTodoService.get_today_summary(test_db)

        # Then: 요약 정보가 표시되는 할일들과 정확히 일치
        displayed_completed = len([t for t in displayed_todos if t.is_completed])
        displayed_pending = len([t for t in displayed_todos if not t.is_completed])
        displayed_total = len(displayed_todos)

        assert summary["total"] == displayed_total
        assert summary["completed"] == displayed_completed
        assert summary["pending"] == displayed_pending

        # 완료율도 정확히 계산되는지 확인
        expected_rate = round(displayed_completed / displayed_total * 100, 1) if displayed_total > 0 else 0
        assert summary["completion_rate"] == expected_rate

    def test_completion_rate_rounding(self, test_db):
        """완료율 반올림이 정확하게 되는지 확인"""
        # Given: 완료율이 소수점을 가지는 경우
        today = date.today()

        # 3개 중 1개 완료 = 33.333...%
        todos = [
            DailyTodo(title="완료", created_date=today, scheduled_date=today,
                     is_completed=True, completed_at=datetime.now(), category=TodoCategory.WORK),
            DailyTodo(title="미완료1", created_date=today, scheduled_date=today,
                     is_completed=False, category=TodoCategory.WORK),
            DailyTodo(title="미완료2", created_date=today, scheduled_date=today,
                     is_completed=False, category=TodoCategory.WORK),
        ]

        test_db.add_all(todos)
        test_db.commit()

        # When: 요약 조회
        summary = DailyTodoService.get_today_summary(test_db)

        # Then: 소수점 1자리로 반올림
        assert summary["total"] == 3
        assert summary["completed"] == 1
        assert summary["pending"] == 2
        assert summary["completion_rate"] == 33.3  # 1/3 * 100 = 33.333... → 33.3