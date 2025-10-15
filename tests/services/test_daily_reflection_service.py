"""
DailyReflectionService 유닛 테스트
"""
import pytest
from datetime import date, datetime
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