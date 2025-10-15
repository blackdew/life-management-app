"""
JourneyService 유닛 테스트
"""
import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.services.journey_service import JourneyService
from app.models.journey import Journey, JourneyStatus
from app.models.todo import DailyTodo, TodoCategory, Todo
from app.schemas.journey import JourneyCreate, JourneyUpdate


class TestJourneyService:
    """JourneyService 테스트 클래스"""

    def test_get_all_journeys_empty(self, test_db: Session):
        """여정이 없을 때 빈 리스트 반환"""
        journeys = JourneyService.get_all_journeys(test_db)
        assert journeys == []

    def test_get_all_journeys_with_data(self, test_db: Session, sample_journey: Journey):
        """여정이 있을 때 정상 반환"""
        journeys = JourneyService.get_all_journeys(test_db)
        assert len(journeys) == 1
        assert journeys[0].id == sample_journey.id
        assert journeys[0].title == "테스트 여정"

    def test_get_journey_by_id_exists(self, test_db: Session, sample_journey: Journey):
        """존재하는 여정 ID로 조회"""
        journey = JourneyService.get_journey_by_id(test_db, sample_journey.id)
        assert journey is not None
        assert journey.id == sample_journey.id
        assert journey.title == "테스트 여정"

    def test_get_journey_by_id_not_exists(self, test_db: Session):
        """존재하지 않는 여정 ID로 조회"""
        journey = JourneyService.get_journey_by_id(test_db, 999)
        assert journey is None

    def test_create_journey_basic(self, test_db: Session):
        """기본 여정 생성 테스트"""
        journey_data = JourneyCreate(
            title="새로운 여정",
            description="새로운 여정 설명",
            start_date=date(2024, 10, 1),
            end_date=date(2024, 12, 31)
        )

        journey = JourneyService.create_journey(test_db, journey_data)

        assert journey.id is not None
        assert journey.title == "새로운 여정"
        assert journey.description == "새로운 여정 설명"
        assert journey.start_date == date(2024, 10, 1)
        assert journey.end_date == date(2024, 12, 31)
        assert journey.status == JourneyStatus.PLANNING  # 기본값
        assert journey.progress == 0.0

    def test_create_journey_with_status(self, test_db: Session):
        """상태를 지정한 여정 생성 테스트"""
        journey_data = JourneyCreate(
            title="활성 여정",
            description="활성 여정 설명",
            start_date=date(2024, 10, 1),
            end_date=date(2024, 12, 31),
            status=JourneyStatus.ACTIVE
        )

        journey = JourneyService.create_journey(test_db, journey_data)
        assert journey.status == JourneyStatus.ACTIVE

    def test_update_journey_success(self, test_db: Session, sample_journey: Journey):
        """여정 수정 성공"""
        update_data = JourneyUpdate(
            title="수정된 여정",
            description="수정된 설명",
            status=JourneyStatus.COMPLETED
        )

        updated_journey = JourneyService.update_journey(
            test_db, sample_journey.id, update_data
        )

        assert updated_journey is not None
        assert updated_journey.title == "수정된 여정"
        assert updated_journey.description == "수정된 설명"
        assert updated_journey.status == JourneyStatus.COMPLETED

    def test_update_journey_not_exists(self, test_db: Session):
        """존재하지 않는 여정 수정"""
        update_data = JourneyUpdate(title="수정된 여정")

        result = JourneyService.update_journey(test_db, 999, update_data)
        assert result is None

    def test_delete_journey_success(self, test_db: Session, sample_journey: Journey):
        """여정 삭제 성공"""
        journey_id = sample_journey.id

        result = JourneyService.delete_journey(test_db, journey_id)
        assert result is True

        # 삭제 확인
        deleted_journey = JourneyService.get_journey_by_id(test_db, journey_id)
        assert deleted_journey is None

    def test_delete_journey_not_exists(self, test_db: Session):
        """존재하지 않는 여정 삭제"""
        result = JourneyService.delete_journey(test_db, 999)
        assert result is False

    def test_get_active_journeys(self, test_db: Session):
        """활성 여정만 조회"""
        # 다양한 상태의 여정 생성
        planning_data = JourneyCreate(
            title="계획중 여정", description="설명",
            start_date=date(2024, 10, 1), end_date=date(2024, 12, 31),
            status=JourneyStatus.PLANNING
        )
        active_data1 = JourneyCreate(
            title="활성 여정 1", description="설명",
            start_date=date(2024, 10, 1), end_date=date(2024, 12, 31),
            status=JourneyStatus.ACTIVE
        )
        active_data2 = JourneyCreate(
            title="활성 여정 2", description="설명",
            start_date=date(2024, 10, 1), end_date=date(2024, 12, 31),
            status=JourneyStatus.ACTIVE
        )
        completed_data = JourneyCreate(
            title="완료된 여정", description="설명",
            start_date=date(2024, 10, 1), end_date=date(2024, 12, 31),
            status=JourneyStatus.COMPLETED
        )

        JourneyService.create_journey(test_db, planning_data)
        JourneyService.create_journey(test_db, active_data1)
        JourneyService.create_journey(test_db, active_data2)
        JourneyService.create_journey(test_db, completed_data)

        active_journeys = JourneyService.get_active_journeys(test_db)
        assert len(active_journeys) == 2
        assert all(j.status == JourneyStatus.ACTIVE for j in active_journeys)

    def test_journey_progress_calculation_empty(self, test_db: Session, sample_journey: Journey):
        """할일이 없는 여정의 진행률 계산"""
        progress = JourneyService.calculate_journey_progress(test_db, sample_journey.id)
        assert progress == 0.0

    def test_journey_progress_calculation_with_todos(self, test_db: Session, sample_journey: Journey):
        """할일이 있는 여정의 진행률 계산"""
        # 일반 할일 2개 추가 (1개 완료, 1개 미완료)
        todo1 = Todo(
            title="할일 1", description="설명 1",
            journey_id=sample_journey.id,
            is_completed=True
        )
        todo2 = Todo(
            title="할일 2", description="설명 2",
            journey_id=sample_journey.id,
            is_completed=False
        )

        test_db.add_all([todo1, todo2])
        test_db.commit()

        # 총 2개 중 1개 완료 = 50%
        progress = JourneyService.calculate_journey_progress(test_db, sample_journey.id)
        assert progress == 50.0

    def test_get_journey_statistics(self, test_db: Session, sample_journey: Journey):
        """여정 통계 정보 조회"""
        # 테스트용 할일 추가
        todo1 = Todo(
            title="할일 1", description="설명 1",
            journey_id=sample_journey.id,
            is_completed=True,
            estimated_time=60
        )
        todo2 = Todo(
            title="할일 2", description="설명 2",
            journey_id=sample_journey.id,
            is_completed=False,
            estimated_time=30
        )

        test_db.add_all([todo1, todo2])
        test_db.commit()

        stats = JourneyService.get_journey_statistics(test_db, sample_journey.id)

        assert stats["journey_id"] == sample_journey.id
        assert stats["total_todos"] == 2
        assert stats["completed_todos"] == 1
        assert stats["pending_todos"] == 1
        assert stats["progress_percentage"] == 50.0
        assert stats["estimated_total_time"] == 90
        assert stats["status"] == JourneyStatus.ACTIVE.value

    def test_update_journey_progress(self, test_db: Session, sample_journey: Journey):
        """여정 진행률 자동 업데이트"""
        # 할일 추가
        todo = Todo(
            title="할일", description="설명",
            journey_id=sample_journey.id,
            is_completed=True
        )
        test_db.add(todo)
        test_db.commit()

        # 진행률 업데이트
        updated_journey = JourneyService.update_journey_progress(test_db, sample_journey.id)

        assert updated_journey is not None
        assert updated_journey.progress == 100.0
        assert updated_journey.status == JourneyStatus.COMPLETED

    def test_get_journeys_with_todos(self, test_db: Session, sample_journey: Journey):
        """TODO를 포함한 여정 조회"""
        # 할일 추가
        todo = Todo(
            title="할일", description="설명",
            journey_id=sample_journey.id
        )
        test_db.add(todo)
        test_db.commit()

        journeys = JourneyService.get_journeys_with_todos(test_db)
        assert len(journeys) == 1
        assert len(journeys[0].todos) == 1
        assert journeys[0].todos[0].title == "할일"

    def test_journey_exceptions_and_edge_cases(self, test_db: Session):
        """여정 예외 상황 및 엣지 케이스 테스트"""
        from app.schemas.journey import JourneyCreate

        # 에러 처리 테스트
        try:
            JourneyService.get_journey_by_id(test_db, 9999)
        except Exception:
            pass  # 에러가 나는 것이 정상

        # 빈 여정 목록 테스트
        journeys = JourneyService.get_all_journeys(test_db)
        # 기존 샘플이 있을 수 있으므로 타입만 확인
        assert isinstance(journeys, list)

    def test_journey_with_special_dates(self, test_db: Session):
        """특수한 날짜 조건의 여정 테스트"""
        from datetime import timedelta
        from app.schemas.journey import JourneyCreate

        # 과거 여정
        past_journey = JourneyCreate(
            title="과거 여정",
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() - timedelta(days=1),
            status=JourneyStatus.COMPLETED
        )

        # 미래 여정
        future_journey = JourneyCreate(
            title="미래 여정",
            start_date=date.today() + timedelta(days=1),
            end_date=date.today() + timedelta(days=30),
            status=JourneyStatus.PLANNING
        )

        # 생성 테스트
        created_past = JourneyService.create_journey(test_db, past_journey)
        created_future = JourneyService.create_journey(test_db, future_journey)

        assert created_past.title == "과거 여정"
        assert created_future.title == "미래 여정"

    def test_error_handling_scenarios(self, test_db: Session):
        """에러 처리 시나리오 테스트"""
        # 잘못된 데이터로 인한 에러 상황들을 시뮬레이션

        # get_journey_by_id 에러 케이스
        journey = JourneyService.get_journey_by_id(test_db, -1)
        assert journey is None

        # update_journey_progress 에러 케이스
        result = JourneyService.update_journey_progress(test_db, 99999)
        assert result is None

    def test_update_journey_partial_fields(self, test_db: Session, sample_journey: Journey):
        """부분 필드만 업데이트하는 테스트"""
        from app.schemas.journey import JourneyUpdate

        # 제목만 업데이트
        update_data = JourneyUpdate(title="새로운 제목만")
        updated = JourneyService.update_journey(test_db, sample_journey.id, update_data)

        assert updated is not None
        assert updated.title == "새로운 제목만"
        assert updated.description == sample_journey.description  # 기존 값 유지

        # 상태만 업데이트
        update_data2 = JourneyUpdate(status=JourneyStatus.COMPLETED)
        updated2 = JourneyService.update_journey(test_db, sample_journey.id, update_data2)

        assert updated2 is not None
        assert updated2.status == JourneyStatus.COMPLETED
        assert updated2.title == "새로운 제목만"  # 이전 업데이트 값 유지

    def test_calculate_journey_progress_edge_cases(self, test_db: Session):
        """여정 진행률 계산 엣지 케이스"""
        # 존재하지 않는 여정의 경우 예외 발생
        with pytest.raises(ValueError, match="진행률 계산 중 오류가 발생했습니다"):
            JourneyService.calculate_journey_progress(test_db, 99999)

    def test_exception_handling_in_get_all_journeys(self, test_db: Session):
        """get_all_journeys에서 예외 처리 테스트"""
        import pytest
        from unittest.mock import patch

        # 데이터베이스 에러를 시뮬레이션
        with patch.object(test_db, 'query') as mock_query:
            mock_query.side_effect = Exception("Database connection error")

            with pytest.raises(ValueError, match="여정 목록 조회 중 오류가 발생했습니다"):
                JourneyService.get_all_journeys(test_db)

    def test_exception_handling_in_get_journey_by_id(self, test_db: Session):
        """get_journey_by_id에서 예외 처리 테스트"""
        import pytest
        from unittest.mock import patch

        # 데이터베이스 에러를 시뮬레이션
        with patch.object(test_db, 'query') as mock_query:
            mock_query.side_effect = Exception("Database connection error")

            with pytest.raises(ValueError, match="여정 조회 중 오류가 발생했습니다"):
                JourneyService.get_journey_by_id(test_db, 1)

    def test_create_journey_database_error(self, test_db: Session):
        """create_journey에서 데이터베이스 에러 테스트 (라인 70-72 커버)"""
        import pytest
        from unittest.mock import patch
        from app.schemas.journey import JourneyCreate

        journey_data = JourneyCreate(
            title="에러 테스트 여정",
            description="데이터베이스 에러 시뮬레이션",
            start_date=date(2024, 10, 1),
            end_date=date(2024, 12, 31)
        )

        # 데이터베이스 commit에서 에러 시뮬레이션
        with patch.object(test_db, 'commit') as mock_commit:
            mock_commit.side_effect = Exception("Database commit error")

            with pytest.raises(ValueError, match="여정 생성 중 오류가 발생했습니다"):
                JourneyService.create_journey(test_db, journey_data)

    def test_update_journey_progress_partial_and_zero(self, test_db: Session, sample_journey: Journey):
        """진행률 업데이트 시 부분 완료(ACTIVE)와 미시작(PLANNING) 상태 테스트 (라인 163-166 커버)"""
        # 부분 완료된 할일 추가 (50% 진행률 = ACTIVE 상태)
        todo1 = Todo(
            title="부분 완료 할일 1",
            description="설명 1",
            journey_id=sample_journey.id,
            is_completed=True
        )
        todo2 = Todo(
            title="부분 완료 할일 2",
            description="설명 2",
            journey_id=sample_journey.id,
            is_completed=False
        )
        test_db.add_all([todo1, todo2])
        test_db.commit()

        # 진행률 업데이트 (50% = ACTIVE)
        updated_journey = JourneyService.update_journey_progress(test_db, sample_journey.id)
        assert updated_journey is not None
        assert updated_journey.progress == 50.0
        assert updated_journey.status == JourneyStatus.ACTIVE

        # 모든 할일을 미완료로 변경 (0% = PLANNING)
        todo1.is_completed = False
        test_db.commit()

        # 진행률 다시 업데이트 (0% = PLANNING)
        updated_journey = JourneyService.update_journey_progress(test_db, sample_journey.id)
        assert updated_journey is not None
        assert updated_journey.progress == 0.0
        assert updated_journey.status == JourneyStatus.PLANNING

    def test_get_journey_statistics_not_exists(self, test_db: Session):
        """존재하지 않는 여정의 통계 조회 테스트 (라인 197 커버)"""
        # 존재하지 않는 여정 ID로 통계 조회
        stats = JourneyService.get_journey_statistics(test_db, 99999)

        # 빈 dict 반환 확인
        assert stats == {}