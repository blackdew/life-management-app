import pytest
from datetime import date, datetime, timedelta
import json
from sqlalchemy.orm import Session

from app.models.todo import DailyTodo, TodoCategory
from app.services.daily_todo_service import DailyTodoService


class TestDailyTodoPostpone:
    """미루기 사유 및 히스토리 기능 테스트"""

    def test_postpone_todo_with_reason_records_history(self, test_db: Session):
        """미루기 시 사유와 함께 히스토리가 기록되는지 테스트"""
        # Given: 할 일 생성
        todo = DailyTodoService.create_todo(
            db=test_db,
            title="테스트 할 일",
            scheduled_date=date.today()
        )

        # When: 미루기 사유와 함께 미루기
        tomorrow = date.today() + timedelta(days=1)
        reason = "회의가 늦게 끝남"

        updated_todo = DailyTodoService.reschedule_todo_with_reason(
            db=test_db,
            todo_id=todo.id,
            new_date=tomorrow,
            reason=reason
        )

        # Then: 미루기 히스토리가 기록됨
        assert updated_todo is not None
        assert updated_todo.postpone_count == 1
        assert updated_todo.postpone_history is not None

        history = json.loads(updated_todo.postpone_history)
        assert len(history) == 1
        assert history[0]["from_date"] == date.today().isoformat()
        assert history[0]["to_date"] == tomorrow.isoformat()
        assert history[0]["reason"] == reason
        assert "postponed_at" in history[0]

    def test_postpone_count_increments_correctly(self, test_db: Session):
        """미루기 횟수가 올바르게 증가하는지 테스트"""
        # Given: 할 일 생성
        todo = DailyTodoService.create_todo(
            db=test_db,
            title="테스트 할 일",
            scheduled_date=date.today()
        )

        # When: 여러 번 미루기
        reasons = ["첫 번째 미루기", "두 번째 미루기", "세 번째 미루기"]
        current_date = date.today()

        for i, reason in enumerate(reasons, 1):
            next_date = current_date + timedelta(days=i)
            todo = DailyTodoService.reschedule_todo_with_reason(
                db=test_db,
                todo_id=todo.id,
                new_date=next_date,
                reason=reason
            )

        # Then: 미루기 횟수가 올바르게 증가
        assert todo.postpone_count == 3

        history = json.loads(todo.postpone_history)
        assert len(history) == 3

        # 각 미루기 기록 확인
        for i, reason in enumerate(reasons):
            assert history[i]["reason"] == reason

    def test_postpone_history_tracks_date_changes(self, test_db: Session):
        """미루기 히스토리에서 날짜 변경이 올바르게 추적되는지 테스트"""
        # Given: 할 일 생성
        today = date.today()
        todo = DailyTodoService.create_todo(
            db=test_db,
            title="테스트 할 일",
            scheduled_date=today
        )

        # When: 날짜를 순차적으로 미루기
        dates_and_reasons = [
            (today + timedelta(days=1), "내일로 미루기"),
            (today + timedelta(days=3), "3일 후로 미루기"),
            (today + timedelta(days=7), "일주일 후로 미루기")
        ]

        expected_from_dates = [today]  # 첫 번째는 오늘부터

        for target_date, reason in dates_and_reasons:
            todo = DailyTodoService.reschedule_todo_with_reason(
                db=test_db,
                todo_id=todo.id,
                new_date=target_date,
                reason=reason
            )
            expected_from_dates.append(target_date)  # 다음 미루기의 시작점

        # Then: 날짜 변경이 올바르게 기록됨
        history = json.loads(todo.postpone_history)

        for i, (target_date, reason) in enumerate(dates_and_reasons):
            assert history[i]["from_date"] == expected_from_dates[i].isoformat()
            assert history[i]["to_date"] == target_date.isoformat()
            assert history[i]["reason"] == reason

    def test_postpone_without_reason_fails(self, test_db: Session):
        """미루기 사유 없이 미루기 시 실패하는지 테스트"""
        # Given: 할 일 생성
        todo = DailyTodoService.create_todo(
            db=test_db,
            title="테스트 할 일",
            scheduled_date=date.today()
        )

        # When & Then: 사유 없이 미루기 시 예외 발생
        tomorrow = date.today() + timedelta(days=1)

        with pytest.raises(ValueError, match="미루기 사유는 필수입니다"):
            DailyTodoService.reschedule_todo_with_reason(
                db=test_db,
                todo_id=todo.id,
                new_date=tomorrow,
                reason=""  # 빈 사유
            )

        with pytest.raises(ValueError, match="미루기 사유는 필수입니다"):
            DailyTodoService.reschedule_todo_with_reason(
                db=test_db,
                todo_id=todo.id,
                new_date=tomorrow,
                reason=None  # None 사유
            )

    def test_multiple_postpones_maintain_history(self, test_db: Session):
        """여러 번 미루기 시 히스토리가 누적되는지 테스트"""
        # Given: 할 일 생성
        todo = DailyTodoService.create_todo(
            db=test_db,
            title="자주 미루는 할 일",
            scheduled_date=date.today()
        )

        # When: 5번 미루기
        postpone_data = [
            ("급한 일이 생김", 1),
            ("컨디션이 안 좋음", 2),
            ("자료가 부족함", 1),
            ("다른 업무 우선", 3),
            ("시간이 부족함", 1)
        ]

        current_date = date.today()

        for reason, days_later in postpone_data:
            current_date = current_date + timedelta(days=days_later)
            todo = DailyTodoService.reschedule_todo_with_reason(
                db=test_db,
                todo_id=todo.id,
                new_date=current_date,
                reason=reason
            )

        # Then: 전체 히스토리가 보존됨
        assert todo.postpone_count == 5

        history = json.loads(todo.postpone_history)
        assert len(history) == 5

        # 각 미루기가 시간순으로 기록됨
        for i, (reason, _) in enumerate(postpone_data):
            assert history[i]["reason"] == reason

        # 첫 번째 미루기는 오늘부터 시작
        assert history[0]["from_date"] == date.today().isoformat()

    def test_get_postpone_summary(self, test_db: Session):
        """미루기 요약 정보 조회 테스트"""
        # Given: 여러 번 미뤄진 할 일 생성
        todo = DailyTodoService.create_todo(
            db=test_db,
            title="자주 미루는 할 일",
            scheduled_date=date.today()
        )

        # 3번 미루기
        reasons = ["사유1", "사유2", "사유3"]
        for i, reason in enumerate(reasons, 1):
            next_date = date.today() + timedelta(days=i)
            todo = DailyTodoService.reschedule_todo_with_reason(
                db=test_db,
                todo_id=todo.id,
                new_date=next_date,
                reason=reason
            )

        # When: 미루기 요약 조회
        summary = DailyTodoService.get_postpone_summary(test_db, todo.id)

        # Then: 요약 정보가 올바름
        assert summary["postpone_count"] == 3
        assert summary["original_date"] == date.today().isoformat()
        assert summary["current_date"] == (date.today() + timedelta(days=3)).isoformat()
        assert summary["total_days_postponed"] == 3
        assert len(summary["recent_reasons"]) == 3
        assert summary["recent_reasons"][0] == "사유3"  # 최신 순

    def test_postpone_reason_length_validation(self, test_db: Session):
        """미루기 사유 길이 검증 테스트"""
        # Given: 할 일 생성
        todo = DailyTodoService.create_todo(
            db=test_db,
            title="테스트 할 일",
            scheduled_date=date.today()
        )

        # When & Then: 너무 긴 사유는 실패
        tomorrow = date.today() + timedelta(days=1)
        long_reason = "a" * 101  # 100자 초과

        with pytest.raises(ValueError, match="미루기 사유는 100자 이하여야 합니다"):
            DailyTodoService.reschedule_todo_with_reason(
                db=test_db,
                todo_id=todo.id,
                new_date=tomorrow,
                reason=long_reason
            )

        # 정확히 100자는 성공
        valid_reason = "a" * 100
        result = DailyTodoService.reschedule_todo_with_reason(
            db=test_db,
            todo_id=todo.id,
            new_date=tomorrow,
            reason=valid_reason
        )
        assert result is not None

    def test_cannot_postpone_completed_todo(self, test_db: Session):
        """완료된 할 일은 미룰 수 없는지 테스트"""
        # Given: 완료된 할 일
        todo = DailyTodoService.create_todo(
            db=test_db,
            title="완료된 할 일",
            scheduled_date=date.today()
        )

        # 할 일 완료
        DailyTodoService.toggle_complete(test_db, todo.id)

        # When & Then: 완료된 할 일 미루기 시 실패
        tomorrow = date.today() + timedelta(days=1)

        with pytest.raises(ValueError, match="완료된 할 일은 미룰 수 없습니다"):
            DailyTodoService.reschedule_todo_with_reason(
                db=test_db,
                todo_id=todo.id,
                new_date=tomorrow,
                reason="완료된 할 일 미루기"
            )