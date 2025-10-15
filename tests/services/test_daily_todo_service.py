"""
DailyTodoService 유닛 테스트
"""
import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.services.daily_todo_service import DailyTodoService
from app.models.todo import DailyTodo, TodoCategory
from app.models.journey import Journey, JourneyStatus


class TestDailyTodoService:
    """DailyTodoService 테스트 클래스"""

    def test_get_today_todos_empty(self, test_db: Session):
        """오늘의 할일이 없을 때 빈 리스트 반환"""
        todos = DailyTodoService.get_today_todos(test_db)
        assert todos == []

    def test_get_today_todos_with_data(self, test_db: Session, sample_daily_todo: DailyTodo):
        """오늘의 할일이 있을 때 정상 반환"""
        todos = DailyTodoService.get_today_todos(test_db)
        assert len(todos) == 1
        assert todos[0].id == sample_daily_todo.id
        assert todos[0].title == "테스트 할일"

    def test_create_todo_basic(self, test_db: Session):
        """기본 할일 생성 테스트"""
        todo = DailyTodoService.create_todo(
            db=test_db,
            title="새로운 할일",
            description="새로운 할일 설명"
        )

        assert todo.id is not None
        assert todo.title == "새로운 할일"
        assert todo.description == "새로운 할일 설명"
        assert todo.category == TodoCategory.OTHER  # 기본값
        assert todo.is_completed is False
        assert todo.created_date == date.today()

    def test_create_todo_with_all_fields(self, test_db: Session, sample_journey: Journey):
        """모든 필드를 포함한 할일 생성 테스트"""
        todo = DailyTodoService.create_todo(
            db=test_db,
            title="완전한 할일",
            description="상세 설명",
            notes="메모",
            category=TodoCategory.WORK,
            estimated_minutes=60,
            journey_id=sample_journey.id,
            scheduled_date=date(2024, 12, 25)
        )

        assert todo.title == "완전한 할일"
        assert todo.description == "상세 설명"
        assert todo.notes == "메모"
        assert todo.category == TodoCategory.WORK
        assert todo.estimated_minutes == 60
        assert todo.journey_id == sample_journey.id
        assert todo.scheduled_date == date(2024, 12, 25)

    def test_get_todo_by_id_exists(self, test_db: Session, sample_daily_todo: DailyTodo):
        """존재하는 할일 ID로 조회"""
        todo = DailyTodoService.get_todo_by_id(test_db, sample_daily_todo.id)
        assert todo is not None
        assert todo.id == sample_daily_todo.id

    def test_get_todo_by_id_not_exists(self, test_db: Session):
        """존재하지 않는 할일 ID로 조회"""
        todo = DailyTodoService.get_todo_by_id(test_db, 999)
        assert todo is None

    def test_toggle_complete_to_completed(self, test_db: Session, sample_daily_todo: DailyTodo):
        """할일을 완료 상태로 토글"""
        assert sample_daily_todo.is_completed is False

        todo = DailyTodoService.toggle_complete(test_db, sample_daily_todo.id)

        assert todo is not None
        assert todo.is_completed is True
        assert todo.completed_at is not None

    def test_toggle_complete_to_uncompleted(self, test_db: Session, completed_daily_todo: DailyTodo):
        """완료된 할일을 미완료 상태로 토글"""
        assert completed_daily_todo.is_completed is True

        todo = DailyTodoService.toggle_complete(test_db, completed_daily_todo.id)

        assert todo is not None
        assert todo.is_completed is False
        assert todo.completed_at is None
        assert todo.completion_reflection is None

    def test_toggle_complete_with_reflection(self, test_db: Session, sample_daily_todo: DailyTodo):
        """회고와 함께 할일 완료"""
        reflection_text = "오늘 정말 잘했다!"

        todo = DailyTodoService.toggle_complete(
            test_db,
            sample_daily_todo.id,
            reflection=reflection_text
        )

        assert todo.is_completed is True
        assert todo.completion_reflection == reflection_text

    def test_toggle_complete_with_image(self, test_db: Session, sample_daily_todo: DailyTodo):
        """이미지와 함께 할일 완료"""
        image_path = "/static/uploads/test.jpg"

        todo = DailyTodoService.toggle_complete(
            test_db,
            sample_daily_todo.id,
            image_path=image_path
        )

        assert todo.is_completed is True
        assert todo.completion_image_path == image_path

    def test_delete_todo_success(self, test_db: Session, sample_daily_todo: DailyTodo):
        """할일 삭제 성공"""
        todo_id = sample_daily_todo.id

        result = DailyTodoService.delete_todo(test_db, todo_id)
        assert result is True

        # 삭제 확인
        deleted_todo = DailyTodoService.get_todo_by_id(test_db, todo_id)
        assert deleted_todo is None

    def test_delete_todo_not_exists(self, test_db: Session):
        """존재하지 않는 할일 삭제"""
        result = DailyTodoService.delete_todo(test_db, 999)
        assert result is False

    def test_update_todo_success(self, test_db: Session, sample_daily_todo: DailyTodo):
        """할일 수정 성공"""
        updated_todo = DailyTodoService.update_todo(
            db=test_db,
            todo_id=sample_daily_todo.id,
            title="수정된 제목",
            description="수정된 설명",
            category=TodoCategory.LEARNING,
            estimated_minutes=90
        )

        assert updated_todo is not None
        assert updated_todo.title == "수정된 제목"
        assert updated_todo.description == "수정된 설명"
        assert updated_todo.category == TodoCategory.LEARNING
        assert updated_todo.estimated_minutes == 90

    def test_update_todo_not_exists(self, test_db: Session):
        """존재하지 않는 할일 수정"""
        result = DailyTodoService.update_todo(
            db=test_db,
            todo_id=999,
            title="수정된 제목"
        )
        assert result is None

    def test_update_todo_with_all_fields(self, test_db: Session, sample_daily_todo: DailyTodo):
        """모든 필드를 포함한 할일 수정 테스트"""
        # 새로운 마일스톤 생성
        from app.models.journey import Journey, JourneyStatus
        new_milestone = Journey(
            title="새 마일스톤",
            start_date=date.today(),
            end_date=date.today(),
            status=JourneyStatus.ACTIVE
        )
        test_db.add(new_milestone)
        test_db.commit()

        updated_todo = DailyTodoService.update_todo(
            db=test_db,
            todo_id=sample_daily_todo.id,
            title="새 제목",
            description="새 설명",
            notes="새 메모",
            category=TodoCategory.HEALTH,
            estimated_minutes=120,
            actual_minutes=90,
            journey_id=new_milestone.id
        )

        assert updated_todo is not None
        assert updated_todo.title == "새 제목"
        assert updated_todo.description == "새 설명"
        assert updated_todo.notes == "새 메모"
        assert updated_todo.category == TodoCategory.HEALTH
        assert updated_todo.estimated_minutes == 120
        assert updated_todo.actual_minutes == 90
        assert updated_todo.journey_id == new_milestone.id

    def test_update_todo_empty_strings(self, test_db: Session, sample_daily_todo: DailyTodo):
        """빈 문자열로 할일 수정 테스트"""
        updated_todo = DailyTodoService.update_todo(
            db=test_db,
            todo_id=sample_daily_todo.id,
            description="",
            notes=""
        )

        assert updated_todo is not None
        assert updated_todo.description is None
        assert updated_todo.notes is None

    def test_toggle_complete_not_exists(self, test_db: Session):
        """존재하지 않는 할일 완료 토글"""
        result = DailyTodoService.toggle_complete(test_db, 999)
        assert result is None

    def test_reschedule_todo_success(self, test_db: Session, sample_daily_todo: DailyTodo):
        """할일 일정 재조정 성공"""
        new_date = date(2024, 12, 25)

        updated_todo = DailyTodoService.reschedule_todo(
            test_db,
            sample_daily_todo.id,
            new_date
        )

        assert updated_todo is not None
        assert updated_todo.scheduled_date == new_date
        assert updated_todo.created_date == new_date

    def test_reschedule_todo_not_exists(self, test_db: Session):
        """존재하지 않는 할일 일정 재조정"""
        new_date = date(2024, 12, 25)

        result = DailyTodoService.reschedule_todo(test_db, 999, new_date)
        assert result is None

    def test_add_quick_todo(self, test_db: Session):
        """빠른 할일 추가"""
        todo = DailyTodoService.add_quick_todo(test_db, "빠른 할일")

        assert todo.title == "빠른 할일"
        assert todo.category == TodoCategory.OTHER
        assert todo.created_date == date.today()

    def test_get_today_summary_empty(self, test_db: Session):
        """할일이 없을 때 오늘의 요약"""
        summary = DailyTodoService.get_today_summary(test_db)

        assert summary["total"] == 0
        assert summary["completed"] == 0
        assert summary["pending"] == 0
        assert summary["completion_rate"] == 0

    def test_get_today_summary_with_data(self, test_db: Session):
        """할일이 있을 때 오늘의 요약"""
        # 3개의 할일 생성 (2개 완료, 1개 미완료)
        from tests.conftest import create_test_todos, create_completed_todos

        create_test_todos(test_db, 1)  # 미완료 1개
        create_completed_todos(test_db, 2)  # 완료 2개

        summary = DailyTodoService.get_today_summary(test_db)

        assert summary["total"] == 3
        assert summary["completed"] == 2
        assert summary["pending"] == 1
        assert summary["completion_rate"] == 66.7

    def test_get_category_summary(self, test_db: Session):
        """카테고리별 요약"""
        # 다양한 카테고리의 할일 생성
        DailyTodoService.create_todo(test_db, "업무 할일", category=TodoCategory.WORK)
        DailyTodoService.create_todo(test_db, "개인 할일", category=TodoCategory.PERSONAL)

        summary = DailyTodoService.get_category_summary(test_db)

        assert "업무" in summary
        assert "개인" in summary
        assert summary["업무"]["total"] == 1
        assert summary["개인"]["total"] == 1

    def test_get_journeys_for_selection(self, test_db: Session, sample_journey: Journey):
        """할일 추가용 마일스톤 목록 조회"""
        milestones = DailyTodoService.get_journeys_for_selection(test_db)

        assert len(milestones) == 1
        assert milestones[0]["id"] == sample_journey.id
        assert milestones[0]["title"] == sample_journey.title
        assert milestones[0]["status"] == sample_journey.status.value

    def test_get_weekly_summary(self, test_db: Session):
        """주간 요약 조회 테스트"""
        # 테스트 할일 생성
        todo1 = DailyTodo(
            title="주간 할일 1",
            category=TodoCategory.WORK,
            scheduled_date=date.today(),
            is_completed=True
        )
        todo2 = DailyTodo(
            title="주간 할일 2",
            category=TodoCategory.PERSONAL,
            scheduled_date=date.today(),
            is_completed=False
        )
        test_db.add_all([todo1, todo2])
        test_db.commit()

        # 주간 요약 조회
        summary = DailyTodoService.get_weekly_summary(test_db)

        assert "total_todos" in summary
        assert "total_completed" in summary
        assert "daily_counts" in summary
        assert "week_start" in summary

    # === 미완료 작업 자동 이월 테스트 ===

    def test_get_today_todos_includes_past_incomplete(
        self,
        test_db: Session,
        past_incomplete_todo: DailyTodo,
        old_incomplete_todo: DailyTodo
    ):
        """과거 미완료 할일이 오늘 할일에 포함되는지 테스트"""
        # 오늘 할일도 하나 생성
        today_todo = DailyTodoService.create_todo(test_db, "오늘 할일")

        todos = DailyTodoService.get_today_todos(test_db)

        # 총 3개의 할일이 조회되어야 함 (오늘 + 어제 + 일주일 전)
        assert len(todos) == 3

        # 모든 할일이 포함되어 있는지 확인
        todo_titles = [todo.title for todo in todos]
        assert "오늘 할일" in todo_titles
        assert "어제 할일" in todo_titles
        assert "일주일 전 할일" in todo_titles

    def test_get_today_todos_excludes_past_completed(
        self,
        test_db: Session,
        past_completed_todo: DailyTodo
    ):
        """과거 완료된 할일은 오늘 할일에 포함되지 않는지 테스트"""
        # 오늘 할일 하나 생성
        today_todo = DailyTodoService.create_todo(test_db, "오늘 할일")

        todos = DailyTodoService.get_today_todos(test_db)

        # 오늘 할일만 조회되어야 함 (과거 완료된 할일은 제외)
        assert len(todos) == 1
        assert todos[0].title == "오늘 할일"

    def test_get_today_todos_with_scheduled_dates(
        self,
        test_db: Session,
        future_scheduled_todo: DailyTodo
    ):
        """scheduled_date 기준 필터링 테스트"""
        # 오늘로 미룬 과거 할일 생성
        from datetime import timedelta
        yesterday = date.today() - timedelta(days=1)

        rescheduled_todo = DailyTodo(
            title="미룬 할일",
            description="어제 생성했지만 오늘로 미룬 할일",
            category=TodoCategory.WORK,
            is_completed=False,
            created_date=yesterday,
            scheduled_date=date.today()  # 오늘로 미룸
        )
        test_db.add(rescheduled_todo)
        test_db.commit()

        todos = DailyTodoService.get_today_todos(test_db)

        # 미룬 할일은 포함되어야 하고, 미래 예정 할일은 제외되어야 함
        todo_titles = [todo.title for todo in todos]
        assert "미룬 할일" in todo_titles
        assert "내일 할일" not in todo_titles

    def test_get_today_todos_includes_overdue_todos(
        self,
        test_db: Session,
        three_days_ago_todo: DailyTodo
    ):
        """오래된 미완료 할일도 포함되는지 테스트"""
        todos = DailyTodoService.get_today_todos(test_db)

        assert len(todos) == 1
        assert todos[0].title == "3일 전 할일"

        # 3일 지난 할일임을 확인
        from datetime import timedelta
        expected_date = date.today() - timedelta(days=3)
        assert todos[0].created_date == expected_date

    def test_get_today_todos_mixed_scenarios(
        self,
        test_db: Session,
        past_incomplete_todo: DailyTodo,
        past_completed_todo: DailyTodo,
        future_scheduled_todo: DailyTodo
    ):
        """다양한 시나리오가 섞인 경우 테스트"""
        # 오늘 할일들 추가
        today_incomplete = DailyTodoService.create_todo(test_db, "오늘 미완료")
        today_complete = DailyTodoService.create_todo(test_db, "오늘 완료")
        DailyTodoService.toggle_complete(test_db, today_complete.id)

        todos = DailyTodoService.get_today_todos(test_db)

        # 포함되어야 할 할일: 오늘 미완료 + 오늘 완료 + 어제 미완료
        # 제외되어야 할 할일: 어제 완료 + 내일 예정
        todo_titles = [todo.title for todo in todos]

        assert "오늘 미완료" in todo_titles
        assert "오늘 완료" in todo_titles
        assert "어제 할일" in todo_titles  # 미완료
        assert "어제 완료한 할일" not in todo_titles  # 완료됨
        assert "내일 할일" not in todo_titles  # 미래 예정

    # === 경과일 계산 테스트 ===

    def test_calculate_days_overdue_today(self, test_db: Session):
        """오늘 생성된 할일의 경과일 계산 테스트"""
        todo = DailyTodoService.create_todo(test_db, "오늘 할일")

        # 경과일 계산 로직을 서비스에 추가 예정
        # 지금은 계산 로직 자체를 테스트
        from datetime import timedelta
        days_overdue = (date.today() - todo.created_date).days

        assert days_overdue == 0

    def test_calculate_days_overdue_past(
        self,
        test_db: Session,
        past_incomplete_todo: DailyTodo,
        three_days_ago_todo: DailyTodo
    ):
        """과거 할일의 경과일 계산 테스트"""
        from datetime import timedelta

        # 어제 할일 - 1일 지남
        yesterday_days_overdue = (date.today() - past_incomplete_todo.created_date).days
        assert yesterday_days_overdue == 1

        # 3일 전 할일 - 3일 지남
        three_days_overdue = (date.today() - three_days_ago_todo.created_date).days
        assert three_days_overdue == 3

    def test_overdue_status_calculation(self, test_db: Session):
        """지연 상태 계산 테스트"""
        from datetime import timedelta

        # 오늘 할일
        today_todo = DailyTodoService.create_todo(test_db, "오늘 할일")
        today_days = (date.today() - today_todo.created_date).days

        # 어제 할일
        yesterday = date.today() - timedelta(days=1)
        yesterday_todo = DailyTodo(
            title="어제 할일",
            category=TodoCategory.WORK,
            is_completed=False,
            created_date=yesterday,
            scheduled_date=yesterday
        )
        test_db.add(yesterday_todo)
        test_db.commit()

        yesterday_days = (date.today() - yesterday_todo.created_date).days

        # 미래 예정 할일
        tomorrow = date.today() + timedelta(days=1)
        future_todo = DailyTodo(
            title="미래 할일",
            category=TodoCategory.WORK,
            is_completed=False,
            created_date=date.today(),
            scheduled_date=tomorrow
        )
        test_db.add(future_todo)
        test_db.commit()

        # 상태 분류 로직 테스트
        assert today_days == 0  # 'today'
        assert yesterday_days == 1  # 'overdue'

        # scheduled_date가 미래인 경우는 'scheduled'로 분류될 예정

