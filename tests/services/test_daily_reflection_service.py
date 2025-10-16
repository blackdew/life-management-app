"""
DailyReflectionService 유닛 테스트
"""
import pytest
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session

from app.services.daily_reflection_service import DailyReflectionService
from app.models.daily_reflection import DailyReflection
from app.models.todo import DailyTodo, TodoCategory


class TestDailyReflectionService:
    """DailyReflectionService 테스트 클래스"""

    def test_get_reflection_by_date_exists(self, test_db: Session, sample_reflection: DailyReflection):
        """특정 날짜의 회고 조회 - 존재하는 경우"""
        reflection = DailyReflectionService.get_reflection_by_date(test_db, date.today())
        assert reflection is not None
        assert reflection.id == sample_reflection.id

    def test_get_reflection_by_date_not_exists(self, test_db: Session):
        """특정 날짜의 회고 조회 - 존재하지 않는 경우"""
        reflection = DailyReflectionService.get_reflection_by_date(test_db, date(2024, 1, 1))
        assert reflection is None

    def test_create_reflection_basic(self, test_db: Session):
        """기본 회고 생성 테스트"""
        reflection = DailyReflectionService.create_reflection(
            db=test_db,
            reflection_date=date(2024, 10, 1),
            reflection_text="새로운 회고 내용",
            satisfaction_score=4,
            energy_level=3
        )

        assert reflection.id is not None
        assert reflection.reflection_date == date(2024, 10, 1)
        assert reflection.reflection_text == "새로운 회고 내용"
        assert reflection.satisfaction_score == 4
        assert reflection.energy_level == 3

    def test_create_reflection_with_todos_snapshot(self, test_db: Session):
        """할일 스냅샷을 포함한 회고 생성"""
        # 테스트용 할일들 생성
        todo1 = DailyTodo(
            title="완료된 할일",
            description="완료된 할일 설명",
            category=TodoCategory.WORK,
            is_completed=True,
            completed_at=datetime.now(),
            created_date=date.today(),
            scheduled_date=date.today()
        )
        todo2 = DailyTodo(
            title="미완료 할일",
            description="미완료 할일 설명",
            category=TodoCategory.PERSONAL,
            is_completed=False,
            created_date=date.today(),
            scheduled_date=date.today()
        )
        test_db.add_all([todo1, todo2])
        test_db.commit()

        reflection = DailyReflectionService.create_reflection(
            db=test_db,
            reflection_date=date.today(),
            reflection_text="할일과 함께하는 회고",
            satisfaction_score=5,
            energy_level=4
        )

        assert reflection.total_todos == 2
        assert reflection.completed_todos == 1
        assert reflection.completion_rate == 50.0
        assert reflection.todos_snapshot is not None
        assert "completed" in reflection.todos_snapshot
        assert "incomplete" in reflection.todos_snapshot

    def test_update_existing_reflection(self, test_db: Session):
        """기존 회고 업데이트 테스트"""
        # 먼저 회고 생성
        original_reflection = DailyReflectionService.create_reflection(
            test_db,
            reflection_date=date(2024, 10, 1),
            reflection_text="원래 회고",
            satisfaction_score=3,
            energy_level=2
        )

        # 같은 날짜로 다시 생성하면 업데이트되어야 함
        updated_reflection = DailyReflectionService.create_reflection(
            test_db,
            reflection_date=date(2024, 10, 1),
            reflection_text="수정된 회고",
            satisfaction_score=5,
            energy_level=4
        )

        assert updated_reflection.id == original_reflection.id
        assert updated_reflection.reflection_text == "수정된 회고"
        assert updated_reflection.satisfaction_score == 5
        assert updated_reflection.energy_level == 4

    def test_delete_reflection_success(self, test_db: Session):
        """회고 삭제 성공"""
        # 회고 생성
        reflection = DailyReflectionService.create_reflection(
            test_db,
            reflection_date=date(2024, 10, 1),
            reflection_text="삭제될 회고",
            satisfaction_score=3,
            energy_level=3
        )

        # 삭제
        result = DailyReflectionService.delete_reflection(test_db, date(2024, 10, 1))
        assert result is True

        # 삭제 확인
        deleted_reflection = DailyReflectionService.get_reflection_by_date(test_db, date(2024, 10, 1))
        assert deleted_reflection is None

    def test_delete_reflection_not_exists(self, test_db: Session):
        """존재하지 않는 회고 삭제"""
        result = DailyReflectionService.delete_reflection(test_db, date(2024, 1, 1))
        assert result is False

    def test_get_recent_reflections(self, test_db: Session):
        """최근 회고 조회"""
        # 여러 날짜의 회고 생성
        for i in range(5):
            DailyReflectionService.create_reflection(
                test_db,
                reflection_date=date(2024, 10, i + 1),
                reflection_text=f"회고 {i + 1}",
                satisfaction_score=3,
                energy_level=3
            )

        recent_reflections = DailyReflectionService.get_recent_reflections(test_db, limit=3)
        assert len(recent_reflections) == 3
        # 최신 순으로 정렬되어야 함
        assert recent_reflections[0].reflection_date > recent_reflections[1].reflection_date

    def test_get_reflections_by_month(self, test_db: Session):
        """월별 회고 조회"""
        # 2024년 10월의 회고들 생성
        for i in range(10):
            DailyReflectionService.create_reflection(
                test_db,
                reflection_date=date(2024, 10, i + 1),
                reflection_text=f"회고 {i + 1}",
                satisfaction_score=4 if i % 2 == 0 else 3,
                energy_level=3 if i % 2 == 0 else 4
            )

        # 2024년 9월 회고도 하나 생성
        DailyReflectionService.create_reflection(
            test_db,
            reflection_date=date(2024, 9, 15),
            reflection_text="9월 회고",
            satisfaction_score=4,
            energy_level=3
        )

        # 10월 회고만 조회
        reflections = DailyReflectionService.get_reflections_by_month(test_db, 2024, 10)
        assert len(reflections) == 10
        assert all(r.reflection_date.month == 10 for r in reflections)

    def test_get_stats_summary(self, test_db: Session):
        """회고 통계 요약"""
        # 여러 회고 생성
        for i in range(5):
            DailyReflectionService.create_reflection(
                test_db,
                reflection_date=date.today(),
                reflection_text=f"회고 {i + 1}",
                satisfaction_score=4 if i % 2 == 0 else 3,
                energy_level=3 if i % 2 == 0 else 4
            )

        stats = DailyReflectionService.get_stats_summary(test_db, days=30)

        assert stats["total_days"] == 1  # 같은 날짜로 여러번 생성하면 하나만 남음
        assert stats["avg_completion_rate"] >= 0.0
        assert stats["avg_satisfaction"] > 0.0
        assert stats["avg_energy"] > 0.0

    def test_reflection_with_no_todos(self, test_db: Session):
        """할일이 없는 날의 회고 생성"""
        reflection = DailyReflectionService.create_reflection(
            test_db,
            reflection_date=date(2024, 10, 1),
            reflection_text="할일이 없는 날의 회고",
            satisfaction_score=3,
            energy_level=3
        )

        assert reflection.total_todos == 0
        assert reflection.completed_todos == 0
        assert reflection.completion_rate == 0.0
        assert reflection.todos_snapshot is not None
        assert len(reflection.todos_snapshot["completed"]) == 0
        assert len(reflection.todos_snapshot["incomplete"]) == 0

    def test_get_stats_summary_empty(self, test_db: Session):
        """회고가 없을 때 통계 요약 테스트"""
        # 빈 DB 상태에서 통계 요약 호출
        stats = DailyReflectionService.get_stats_summary(test_db, days=30)

        # 빈 경우의 기본값들 확인
        assert stats["total_days"] == 0
        assert stats["avg_completion_rate"] == 0.0

    def test_reflection_includes_automatically_carried_over_todos(self, test_db: Session):
        """자동 이월된 할일(과거 미완료)이 오늘 회고에 포함되어야 함"""
        today = date.today()
        yesterday = today - timedelta(days=1)

        # 어제 생성되었지만 완료하지 못한 할일 (자동 이월)
        overdue_todo = DailyTodo(
            title="어제 미완료 할일",
            category=TodoCategory.WORK,
            created_date=yesterday,
            scheduled_date=yesterday,  # 어제 예정이었음
            is_completed=False
        )

        # 오늘 생성된 할일
        today_todo = DailyTodo(
            title="오늘 할일",
            category=TodoCategory.PERSONAL,
            created_date=today,
            scheduled_date=today,
            is_completed=False
        )

        test_db.add_all([overdue_todo, today_todo])
        test_db.commit()

        # When: 오늘 회고 생성
        reflection = DailyReflectionService.create_reflection(
            test_db,
            reflection_date=today,
            reflection_text="자동 이월 테스트",
            satisfaction_score=3,
            energy_level=3
        )

        # Then: 자동 이월된 할일도 포함되어야 함
        assert reflection.total_todos == 2  # 어제 미완료 + 오늘 할일
        assert reflection.completed_todos == 0
        assert len(reflection.todos_snapshot["incomplete"]) == 2

    def test_reflection_excludes_explicitly_postponed_todos_to_future(self, test_db: Session):
        """명시적으로 미래로 미룬 할일은 오늘 회고에서 제외되어야 함"""
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # 오늘 생성했지만 내일로 미룬 할일
        postponed_todo = DailyTodo(
            title="내일로 미룬 할일",
            category=TodoCategory.WORK,
            created_date=today,
            scheduled_date=tomorrow,  # 내일로 미룸
            postpone_count=1,
            is_completed=False
        )

        # 오늘 예정된 일반 할일
        today_todo = DailyTodo(
            title="오늘 할일",
            category=TodoCategory.PERSONAL,
            created_date=today,
            scheduled_date=today,
            is_completed=False
        )

        test_db.add_all([postponed_todo, today_todo])
        test_db.commit()

        # When: 오늘 회고 생성
        reflection = DailyReflectionService.create_reflection(
            test_db,
            reflection_date=today,
            reflection_text="명시적 미룸 제외 테스트",
            satisfaction_score=4,
            energy_level=3
        )

        # Then: 내일로 미룬 할일은 제외되어야 함
        assert reflection.total_todos == 1  # 오늘 할일만
        assert len(reflection.todos_snapshot["incomplete"]) == 1
        assert reflection.todos_snapshot["incomplete"][0]["title"] == "오늘 할일"

    def test_reflection_includes_todos_postponed_from_past_to_today(self, test_db: Session):
        """과거에서 오늘로 명시적으로 미룬 할일은 오늘 회고에 포함되어야 함"""
        today = date.today()
        yesterday = today - timedelta(days=1)

        # 어제 생성되었고 오늘로 미룬 할일
        postponed_to_today = DailyTodo(
            title="어제에서 오늘로 미룬 할일",
            category=TodoCategory.WORK,
            created_date=yesterday,
            scheduled_date=today,  # 오늘로 미룸
            postpone_count=1,
            is_completed=False
        )

        # 오늘 생성된 일반 할일
        today_todo = DailyTodo(
            title="오늘 생성한 할일",
            category=TodoCategory.LEARNING,
            created_date=today,
            scheduled_date=today,
            is_completed=True,
            completed_at=datetime.now()
        )

        test_db.add_all([postponed_to_today, today_todo])
        test_db.commit()

        # When: 오늘 회고 생성
        reflection = DailyReflectionService.create_reflection(
            test_db,
            reflection_date=today,
            reflection_text="과거→오늘 미룸 포함 테스트",
            satisfaction_score=4,
            energy_level=4
        )

        # Then: 오늘로 미룬 할일도 포함되어야 함
        assert reflection.total_todos == 2  # 오늘로 미룬 것 + 오늘 할일
        assert reflection.completed_todos == 1
        assert len(reflection.todos_snapshot["incomplete"]) == 1
        assert len(reflection.todos_snapshot["completed"]) == 1

    def test_reflection_count_matches_today_todos_display(self, test_db: Session):
        """회고의 할일 카운트가 실제 오늘의 할일 화면과 일치해야 함"""
        from app.services.daily_todo_service import DailyTodoService

        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        # 시나리오: 복잡한 실제 상황
        todos = [
            # 1. 오늘 생성, 오늘 예정 (표시 O, 회고 O)
            DailyTodo(
                title="오늘 할일",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=today,
                is_completed=False
            ),
            # 2. 오늘 생성, 오늘 완료 (표시 O, 회고 O)
            DailyTodo(
                title="오늘 완료한 할일",
                category=TodoCategory.LEARNING,
                created_date=today,
                scheduled_date=today,
                is_completed=True,
                completed_at=datetime.now()
            ),
            # 3. 어제 생성, 어제 예정, 미완료 → 자동 이월 (표시 O, 회고 O)
            DailyTodo(
                title="어제 미완료 자동 이월",
                category=TodoCategory.HEALTH,
                created_date=yesterday,
                scheduled_date=yesterday,
                is_completed=False
            ),
            # 4. 어제 생성, 오늘로 미룸 (표시 O, 회고 O)
            DailyTodo(
                title="어제에서 오늘로 미룬 할일",
                category=TodoCategory.PERSONAL,
                created_date=yesterday,
                scheduled_date=today,
                postpone_count=1,
                is_completed=False
            ),
            # 5. 오늘 생성, 내일로 미룸 (표시 X, 회고 X)
            DailyTodo(
                title="내일로 미룬 할일",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=tomorrow,
                postpone_count=1,
                is_completed=False
            ),
            # 6. 어제 생성, 어제 완료 (표시 X, 회고 X)
            DailyTodo(
                title="어제 완료한 할일",
                category=TodoCategory.OTHER,
                created_date=yesterday,
                scheduled_date=yesterday,
                is_completed=True,
                completed_at=datetime.now() - timedelta(days=1)
            ),
        ]

        test_db.add_all(todos)
        test_db.commit()

        # When: 오늘의 할일 화면 조회 & 회고 생성
        today_todos_display = DailyTodoService.get_today_todos(test_db)
        reflection = DailyReflectionService.create_reflection(
            test_db,
            reflection_date=today,
            reflection_text="통합 테스트",
            satisfaction_score=4,
            energy_level=3
        )

        # Then: 화면에 표시되는 할일 수 = 회고의 할일 수
        expected_count = 4  # 1, 2, 3, 4번만 포함
        assert len(today_todos_display) == expected_count
        assert reflection.total_todos == expected_count

        # 완료/미완료 개수도 일치해야 함
        display_completed = len([t for t in today_todos_display if t.is_completed])
        display_incomplete = len([t for t in today_todos_display if not t.is_completed])

        assert reflection.completed_todos == display_completed
        assert (reflection.total_todos - reflection.completed_todos) == display_incomplete