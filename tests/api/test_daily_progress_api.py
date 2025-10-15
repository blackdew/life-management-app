"""
오늘의 진행상황 API 응답 정확성 테스트
- 실제 API 엔드포인트에서 올바른 진행상황 데이터를 반환하는지 검증
"""
import pytest
from datetime import date, datetime, timedelta
from app.models.todo import DailyTodo, TodoCategory


class TestDailyProgressAPI:
    """오늘의 진행상황 API 테스트"""

    def test_daily_todos_api_returns_correct_summary(self, client, test_db):
        """일일 할일 API가 정확한 요약 정보를 반환하는지 확인"""
        # Given: 다양한 상태의 할일들
        today = date.today()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        todos = [
            # 오늘 표시될 할일들
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
            ),
            DailyTodo(
                title="어제 미완료 할일",
                category=TodoCategory.WORK,
                created_date=yesterday,
                scheduled_date=yesterday,
                is_completed=False
            ),
            # 오늘 표시되지 않을 할일
            DailyTodo(
                title="내일로 미룬 할일",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=tomorrow,
                postpone_count=1,
                is_completed=False
            ),
        ]

        test_db.add_all(todos)
        test_db.commit()

        # When: API 호출
        response = client.get("/")

        # Then: 정확한 요약 정보 반환
        assert response.status_code == 200

        # HTML 응답에서 요약 정보 확인
        html_content = response.text

        # 총 할일 수 확인 (3개: 오늘 완료 + 오늘 미완료 + 어제 미완료)
        assert "1/3" in html_content  # 완료/전체 표시

        # 남은 일 개수 확인 (2개: 오늘 미완료 + 어제 미완료)
        assert "남은 일: 2개" in html_content

    def test_empty_todos_api_shows_zero_progress(self, client, test_db):
        """할일이 없을 때 API가 올바른 빈 상태를 표시하는지 확인"""
        # When: 할일이 없는 상태에서 API 호출
        response = client.get("/")

        # Then: 빈 상태 메시지와 0 진행률
        assert response.status_code == 200
        html_content = response.text

        # 할일이 없을 때 메시지 확인
        assert "아직 할 일이 없네요" in html_content

    def test_api_reflects_todo_completion_changes(self, client, test_db):
        """할일 완료 상태 변경이 API 응답에 즉시 반영되는지 확인"""
        # Given: 미완료 할일 생성
        todo = DailyTodo(
            title="테스트 할일",
            category=TodoCategory.WORK,
            created_date=date.today(),
            scheduled_date=date.today(),
            is_completed=False
        )
        test_db.add(todo)
        test_db.commit()
        todo_id = todo.id

        # When: 할일 완료 처리
        response = client.patch(f"/api/daily/todos/{todo_id}/complete")
        assert response.status_code == 200

        # Then: 페이지에서 완료 상태 반영 확인
        response = client.get("/")
        assert response.status_code == 200
        html_content = response.text

        # 100% 완료율 표시 확인
        assert "1/1" in html_content  # 1개 완료/전체 1개
        assert "남은 일: 0개" in html_content

    def test_api_handles_postponed_todos_correctly(self, client, test_db):
        """미룬 할일이 API 응답에서 올바르게 처리되는지 확인"""
        # Given: 오늘 할일과 내일로 미룬 할일
        today = date.today()
        tomorrow = today + timedelta(days=1)

        todos = [
            DailyTodo(
                title="오늘 할일",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=today,
                is_completed=False
            ),
            DailyTodo(
                title="내일로 미룬 할일",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=tomorrow,
                postpone_count=1,
                is_completed=False
            ),
        ]

        test_db.add_all(todos)
        test_db.commit()

        # When: API 호출
        response = client.get("/")

        # Then: 미룬 할일은 제외하고 계산
        assert response.status_code == 200
        html_content = response.text

        # 오늘 할일만 카운트 (1개)
        assert "0/1" in html_content  # 0개 완료/전체 1개
        assert "남은 일: 1개" in html_content

    def test_api_includes_overdue_todos_in_progress(self, client, test_db):
        """과거 미완료 할일이 API 응답에 포함되는지 확인"""
        # Given: 어제 미완료 할일과 오늘 할일
        today = date.today()
        yesterday = today - timedelta(days=1)

        todos = [
            DailyTodo(
                title="어제 미완료 할일",
                category=TodoCategory.WORK,
                created_date=yesterday,
                scheduled_date=yesterday,
                is_completed=False
            ),
            DailyTodo(
                title="오늘 완료한 할일",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=today,
                is_completed=True,
                completed_at=datetime.now()
            ),
        ]

        test_db.add_all(todos)
        test_db.commit()

        # When: API 호출
        response = client.get("/")

        # Then: 과거 미완료 할일도 포함하여 계산
        assert response.status_code == 200
        html_content = response.text

        # 총 2개 할일 중 1개 완료
        assert "1/2" in html_content
        assert "남은 일: 1개" in html_content

    def test_real_time_progress_updates(self, client, test_db):
        """실시간 진행상황 업데이트가 정확한지 확인"""
        # Given: 3개의 미완료 할일
        today = date.today()
        todos = [
            DailyTodo(
                title=f"할일 {i}",
                category=TodoCategory.WORK,
                created_date=today,
                scheduled_date=today,
                is_completed=False
            )
            for i in range(1, 4)
        ]

        test_db.add_all(todos)
        test_db.commit()
        todo_ids = [todo.id for todo in todos]

        # When & Then: 순차적으로 완료하며 진행상황 확인

        # 1단계: 모든 할일 미완료
        response = client.get("/")
        assert "0/3" in response.text
        assert "남은 일: 3개" in response.text

        # 2단계: 첫 번째 할일 완료
        client.patch(f"/api/daily/todos/{todo_ids[0]}/complete")
        response = client.get("/")
        assert "1/3" in response.text
        assert "남은 일: 2개" in response.text

        # 3단계: 두 번째 할일 완료
        client.patch(f"/api/daily/todos/{todo_ids[1]}/complete")
        response = client.get("/")
        assert "2/3" in response.text
        assert "남은 일: 1개" in response.text

        # 4단계: 마지막 할일 완료
        client.patch(f"/api/daily/todos/{todo_ids[2]}/complete")
        response = client.get("/")
        assert "3/3" in response.text
        assert "남은 일: 0개" in response.text

    def test_progress_calculation_edge_cases(self, client, test_db):
        """진행상황 계산의 엣지 케이스들을 확인"""
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Case 1: 과거 할일을 오늘 완료한 경우
        past_todo = DailyTodo(
            title="어제 할일을 오늘 완료",
            category=TodoCategory.WORK,
            created_date=yesterday,
            scheduled_date=yesterday,
            is_completed=True,
            completed_at=datetime.now()  # 오늘 완료
        )

        test_db.add(past_todo)
        test_db.commit()

        response = client.get("/")
        assert response.status_code == 200
        html_content = response.text

        # 과거 할일도 오늘 완료된 것으로 카운트
        assert "1/1" in html_content
        assert "남은 일: 0개" in html_content

        # Case 2: 할일 완료 취소
        test_db.delete(past_todo)
        test_db.commit()

        # 미완료 할일 추가 후 완료
        new_todo = DailyTodo(
            title="완료 후 취소할 할일",
            category=TodoCategory.WORK,
            created_date=today,
            scheduled_date=today,
            is_completed=False
        )
        test_db.add(new_todo)
        test_db.commit()

        # 완료 처리
        client.patch(f"/api/daily/todos/{new_todo.id}/complete")
        response = client.get("/")
        assert "1/1" in response.text

        # 완료 취소
        client.patch(f"/api/daily/todos/{new_todo.id}/complete")
        response = client.get("/")
        assert "0/1" in response.text
        assert "남은 일: 1개" in response.text