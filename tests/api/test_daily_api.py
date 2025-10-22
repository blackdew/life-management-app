"""
Daily Todo API 테스트
"""
import pytest
from datetime import date, timedelta, datetime
from fastapi.testclient import TestClient
from app.main import app
from app.models.todo import DailyTodo, TodoCategory
from app.models.journey import Journey, JourneyStatus


class TestDailyTodoAPI:
    """Daily Todo API 테스트 클래스"""

    def test_get_today_todos_empty(self, client: TestClient, test_db):
        """오늘의 할일 목록 조회 - 빈 목록 테스트"""
        response = client.get("/api/daily/todos/today")
        assert response.status_code == 200

        data = response.json()
        assert data["todos"] == []

    def test_get_today_todos_with_data(self, client: TestClient, test_db):
        """오늘의 할일 목록 조회 - 데이터가 있는 경우"""
        # 테스트 데이터 생성
        todo1 = DailyTodo(
            title="오늘 할일 1",
            notes="테스트 노트 1",
            category=TodoCategory.WORK,
            created_date=date.today(),
            scheduled_date=date.today(),
            is_completed=True
        )
        todo2 = DailyTodo(
            title="오늘 할일 2",
            notes="테스트 노트 2",
            category=TodoCategory.PERSONAL,
            created_date=date.today(),
            scheduled_date=date.today(),
            is_completed=False
        )
        # 어제 할일 (미완료시 자동 이월되어 오늘 목록에 포함됨)
        todo_yesterday = DailyTodo(
            title="어제 할일",
            created_date=date.today() - timedelta(days=1),
            scheduled_date=date.today() - timedelta(days=1),
            is_completed=False
        )

        test_db.add(todo1)
        test_db.add(todo2)
        test_db.add(todo_yesterday)
        test_db.commit()

        response = client.get("/api/daily/todos/today")
        assert response.status_code == 200

        data = response.json()
        assert len(data["todos"]) == 3  # 자동 이월 시스템으로 어제 미완료 할일도 포함

        # 제목 확인 - 어제 미완료 할일도 자동 이월되어 포함됨
        titles = [todo["title"] for todo in data["todos"]]
        assert "오늘 할일 1" in titles
        assert "오늘 할일 2" in titles
        assert "어제 할일" in titles  # 자동 이월로 포함됨

    def test_create_todo_success(self, client: TestClient, test_db):
        """할일 생성 성공 테스트"""
        todo_data = {
            "title": "새 할일",
            "description": "할일 설명",
            "notes": "할일 노트",
            "category": "업무",
            "estimated_minutes": 60
        }

        response = client.post("/api/daily/todos", data=todo_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "새 할일"
        assert data["category"] == "업무"
        assert data["is_completed"] is False

        # 데이터베이스 확인
        todo = test_db.query(DailyTodo).filter(DailyTodo.title == "새 할일").first()
        assert todo is not None
        assert todo.category == TodoCategory.WORK
        assert todo.estimated_minutes == 60

    def test_create_todo_with_journey(self, client: TestClient, test_db):
        """여정과 연결된 할일 생성 테스트"""
        # 여정 생성
        journey = Journey(
            title="테스트 여정",
            description="테스트용",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status=JourneyStatus.ACTIVE
        )
        test_db.add(journey)
        test_db.commit()
        test_db.refresh(journey)

        todo_data = {
            "title": "여정 할일",
            "description": "여정과 연결",
            "journey_id": journey.id
        }

        response = client.post("/api/daily/todos", data=todo_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "여정 할일"

        # 데이터베이스 확인
        todo = test_db.query(DailyTodo).filter(DailyTodo.title == "여정 할일").first()
        assert todo is not None
        assert todo.journey_id == journey.id

    def test_create_quick_todo_success(self, client: TestClient, test_db):
        """빠른 할일 추가 성공 테스트"""
        todo_data = {"title": "빠른 할일"}

        response = client.post("/api/daily/todos/quick", data=todo_data)
        assert response.status_code == 200

        data = response.json()
        assert data["title"] == "빠른 할일"
        assert data["is_completed"] is False
        assert data["category"] == "기타"  # 기본값

        # 데이터베이스 확인
        todo = test_db.query(DailyTodo).filter(DailyTodo.title == "빠른 할일").first()
        assert todo is not None
        assert todo.category == TodoCategory.OTHER

    def test_create_quick_todo_empty_title(self, client: TestClient, test_db):
        """빈 제목으로 빠른 할일 추가 실패 테스트"""
        todo_data = {"title": ""}

        response = client.post("/api/daily/todos/quick", data=todo_data)
        assert response.status_code == 400

    def test_create_quick_todo_whitespace_title(self, client: TestClient, test_db):
        """공백만 있는 제목으로 빠른 할일 추가 실패 테스트"""
        todo_data = {"title": "   "}

        response = client.post("/api/daily/todos/quick", data=todo_data)
        assert response.status_code == 400

    def test_toggle_todo_completion_success(self, client: TestClient, test_db):
        """할일 완료 토글 성공 테스트"""
        todo = DailyTodo(
            title="토글 테스트",
            scheduled_date=date.today(),
            is_completed=False
        )
        test_db.add(todo)
        test_db.commit()
        test_db.refresh(todo)

        response = client.patch(f"/api/daily/todos/{todo.id}/toggle")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == todo.id
        assert data["is_completed"] is True
        assert data["completed_at"] is not None

        # 데이터베이스 확인
        test_db.refresh(todo)
        assert todo.is_completed is True
        assert todo.completed_at is not None

    def test_toggle_todo_completion_not_found(self, client: TestClient, test_db):
        """존재하지 않는 할일 토글 실패 테스트"""
        response = client.patch("/api/daily/todos/999/toggle")
        assert response.status_code == 404

    def test_complete_todo_with_reflection(self, client: TestClient, test_db):
        """회고와 함께 할일 완료 테스트"""
        todo = DailyTodo(
            title="회고 테스트",
            scheduled_date=date.today(),
            is_completed=False
        )
        test_db.add(todo)
        test_db.commit()
        test_db.refresh(todo)

        reflection_data = {"reflection": "오늘 이 일을 하면서 많이 배웠다."}

        response = client.patch(f"/api/daily/todos/{todo.id}/complete", data=reflection_data)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == todo.id
        assert data["is_completed"] is True
        assert data["completion_reflection"] == "오늘 이 일을 하면서 많이 배웠다."

    def test_update_completion_reflection_success(self, client: TestClient, test_db):
        """완료 회고 수정 성공 테스트"""
        # Given: 완료된 할일 (회고 포함)
        todo = DailyTodo(
            title="완료된 할일",
            scheduled_date=date.today(),
            is_completed=True,
            completed_at=datetime.now(),
            completion_reflection="원래 회고 내용"
        )
        test_db.add(todo)
        test_db.commit()
        test_db.refresh(todo)

        # When: 회고만 수정
        update_data = {"reflection": "수정된 회고 내용입니다!"}
        response = client.patch(f"/api/daily/todos/{todo.id}/reflection", data=update_data)

        # Then: 회고만 업데이트됨
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo.id
        assert data["completion_reflection"] == "수정된 회고 내용입니다!"
        assert data["is_completed"] is True  # 여전히 완료 상태

        # 데이터베이스 확인
        test_db.refresh(todo)
        assert todo.completion_reflection == "수정된 회고 내용입니다!"

    def test_update_completion_reflection_incomplete_todo(self, client: TestClient, test_db):
        """미완료 할일의 회고 수정 실패 테스트"""
        # Given: 미완료 할일
        todo = DailyTodo(
            title="미완료 할일",
            scheduled_date=date.today(),
            is_completed=False
        )
        test_db.add(todo)
        test_db.commit()
        test_db.refresh(todo)

        # When: 회고 수정 시도
        update_data = {"reflection": "미완료 할일 회고 수정 시도"}
        response = client.patch(f"/api/daily/todos/{todo.id}/reflection", data=update_data)

        # Then: 실패 (400 Bad Request)
        assert response.status_code == 400
        assert "완료된 할 일만" in response.json()["detail"]

    def test_update_completion_reflection_not_found(self, client: TestClient, test_db):
        """존재하지 않는 할일의 회고 수정 실패 테스트"""
        update_data = {"reflection": "존재하지 않는 할일"}
        response = client.patch("/api/daily/todos/999/reflection", data=update_data)
        assert response.status_code == 404

    def test_update_completion_reflection_empty(self, client: TestClient, test_db):
        """회고를 빈 값으로 수정 (삭제) 테스트"""
        # Given: 완료된 할일 (회고 포함)
        todo = DailyTodo(
            title="완료된 할일",
            scheduled_date=date.today(),
            is_completed=True,
            completed_at=datetime.now(),
            completion_reflection="삭제할 회고"
        )
        test_db.add(todo)
        test_db.commit()
        test_db.refresh(todo)

        # When: 빈 회고로 수정
        update_data = {"reflection": ""}
        response = client.patch(f"/api/daily/todos/{todo.id}/reflection", data=update_data)

        # Then: 회고가 None으로 설정됨
        assert response.status_code == 200
        data = response.json()
        assert data["completion_reflection"] is None

        # 데이터베이스 확인
        test_db.refresh(todo)
        assert todo.completion_reflection is None

    def test_delete_todo_success(self, client: TestClient, test_db):
        """할일 삭제 성공 테스트"""
        todo = DailyTodo(
            title="삭제 테스트",
            scheduled_date=date.today()
        )
        test_db.add(todo)
        test_db.commit()
        test_db.refresh(todo)

        response = client.delete(f"/api/daily/todos/{todo.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "할 일이 삭제되었습니다"

        # 데이터베이스에서 삭제 확인
        deleted_todo = test_db.query(DailyTodo).filter(DailyTodo.id == todo.id).first()
        assert deleted_todo is None

    def test_delete_todo_not_found(self, client: TestClient, test_db):
        """존재하지 않는 할일 삭제 실패 테스트"""
        response = client.delete("/api/daily/todos/999")
        assert response.status_code == 404

    def test_get_today_summary(self, client: TestClient, test_db):
        """오늘의 요약 정보 조회 테스트"""
        # 테스트 데이터 생성
        todo1 = DailyTodo(
            title="완료된 할일",
            scheduled_date=date.today(),
            is_completed=True,
            category=TodoCategory.WORK
        )
        todo2 = DailyTodo(
            title="미완료 할일",
            scheduled_date=date.today(),
            is_completed=False,
            category=TodoCategory.PERSONAL
        )
        test_db.add(todo1)
        test_db.add(todo2)
        test_db.commit()

        response = client.get("/api/daily/summary/today")
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "completed" in data
        assert "completion_rate" in data

    def test_get_weekly_summary(self, client: TestClient, test_db):
        """주간 요약 정보 조회 테스트"""
        response = client.get("/api/daily/summary/weekly")
        assert response.status_code == 200

        # 기본적으로 JSON 응답이 와야 함
        data = response.json()
        assert isinstance(data, dict)

    def test_get_category_summary(self, client: TestClient, test_db):
        """카테고리별 요약 조회 테스트"""
        # 카테고리별 할일 생성
        todo_work = DailyTodo(
            title="업무 할일",
            category=TodoCategory.WORK,
            scheduled_date=date.today(),
            is_completed=True
        )
        todo_personal = DailyTodo(
            title="개인 할일",
            category=TodoCategory.PERSONAL,
            scheduled_date=date.today(),
            is_completed=False
        )
        test_db.add(todo_work)
        test_db.add(todo_personal)
        test_db.commit()

        response = client.get("/api/daily/summary/categories")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)

    def test_reschedule_todo_success(self, client: TestClient, test_db):
        """할일 일정 재조정 성공 테스트"""
        todo = DailyTodo(
            title="일정 변경 테스트",
            scheduled_date=date.today(),
            is_completed=False
        )
        test_db.add(todo)
        test_db.commit()
        test_db.refresh(todo)

        new_date = (date.today() + timedelta(days=1)).isoformat()
        reschedule_data = {"new_date": new_date}

        response = client.patch(f"/api/daily/todos/{todo.id}/reschedule", data=reschedule_data)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == todo.id
        assert data["scheduled_date"] == new_date

        # 데이터베이스 확인
        test_db.refresh(todo)
        assert todo.scheduled_date == date.today() + timedelta(days=1)

    def test_reschedule_todo_invalid_date(self, client: TestClient, test_db):
        """잘못된 날짜로 일정 재조정 실패 테스트"""
        todo = DailyTodo(
            title="일정 변경 테스트",
            scheduled_date=date.today()
        )
        test_db.add(todo)
        test_db.commit()
        test_db.refresh(todo)

        reschedule_data = {"new_date": "invalid-date"}

        response = client.patch(f"/api/daily/todos/{todo.id}/reschedule", data=reschedule_data)
        assert response.status_code == 400

    def test_reschedule_todo_with_reason_success(self, client: TestClient, test_db):
        """미루기 사유 포함 할 일 재조정 테스트"""
        # Given: 할 일 생성
        todo = DailyTodo(
            title="미루기 테스트 할 일",
            category=TodoCategory.WORK,
            created_date=date.today()
        )
        test_db.add(todo)
        test_db.commit()
        test_db.refresh(todo)

        new_date = (date.today() + timedelta(days=1)).isoformat()
        reschedule_data = {"new_date": new_date, "reason": "회의가 늦게 끝남"}

        response = client.patch(f"/api/daily/todos/{todo.id}/reschedule", data=reschedule_data)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == todo.id
        assert data["scheduled_date"] == new_date
        assert data["postpone_count"] == 1

    def test_get_journeys_for_selection(self, client: TestClient, test_db):
        """할일 추가용 여정 목록 조회 테스트"""
        # 여정 생성
        journey = Journey(
            title="선택용 여정",
            description="테스트용",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status=JourneyStatus.ACTIVE
        )
        test_db.add(journey)
        test_db.commit()

        response = client.get("/api/daily/journeys")
        assert response.status_code == 200

        data = response.json()
        assert "journeys" in data
        assert isinstance(data["journeys"], list)

    def test_get_todo_by_id_success(self, client: TestClient, test_db):
        """특정 할일 상세 조회 성공 테스트"""
        todo = DailyTodo(
            title="상세 조회 테스트",
            description="상세 설명",
            notes="상세 노트",
            category=TodoCategory.LEARNING,
            estimated_minutes=90,
            scheduled_date=date.today()
        )
        test_db.add(todo)
        test_db.commit()
        test_db.refresh(todo)

        response = client.get(f"/api/daily/todos/{todo.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == todo.id
        assert data["title"] == "상세 조회 테스트"
        assert data["description"] == "상세 설명"
        assert data["notes"] == "상세 노트"
        assert data["category"] == "학습"
        assert data["estimated_minutes"] == 90

    def test_get_todo_by_id_not_found(self, client: TestClient, test_db):
        """존재하지 않는 할일 조회 실패 테스트"""
        response = client.get("/api/daily/todos/999")
        assert response.status_code == 404

    def test_update_todo_success(self, client: TestClient, test_db):
        """할일 수정 성공 테스트"""
        todo = DailyTodo(
            title="수정 전 제목",
            description="수정 전 설명",
            category=TodoCategory.OTHER,
            scheduled_date=date.today()
        )
        test_db.add(todo)
        test_db.commit()
        test_db.refresh(todo)

        update_data = {
            "title": "수정 후 제목",
            "description": "수정 후 설명",
            "notes": "새로운 노트",
            "category": "학습",
            "estimated_minutes": 120
        }

        response = client.put(f"/api/daily/todos/{todo.id}", data=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == todo.id
        assert data["title"] == "수정 후 제목"
        assert data["description"] == "수정 후 설명"
        assert data["notes"] == "새로운 노트"
        assert data["category"] == "학습"

        # 데이터베이스 확인
        test_db.refresh(todo)
        assert todo.title == "수정 후 제목"
        assert todo.category == TodoCategory.LEARNING

    def test_update_todo_not_found(self, client: TestClient, test_db):
        """존재하지 않는 할일 수정 실패 테스트"""
        update_data = {
            "title": "존재하지 않는 할일",
            "description": "수정 시도"
        }

        response = client.put("/api/daily/todos/999", data=update_data)
        assert response.status_code == 404

    def test_get_reflection_summary(self, client: TestClient, test_db):
        """회고용 오늘의 활동 요약 조회 테스트"""
        # 테스트 데이터 생성 - 완료된 할일
        completed_todo = DailyTodo(
            title="완료된 업무",
            category=TodoCategory.WORK,
            scheduled_date=date.today(),
            is_completed=True,
            completed_at=datetime.now()
        )
        # 미완료 할일
        pending_todo = DailyTodo(
            title="미완료 학습",
            category=TodoCategory.LEARNING,
            scheduled_date=date.today(),
            is_completed=False,
            estimated_minutes=60
        )
        test_db.add(completed_todo)
        test_db.add(pending_todo)
        test_db.commit()

        response = client.get("/api/daily/reflection-summary")
        assert response.status_code == 200

        data = response.json()
        assert "summary" in data
        assert "completed_todos" in data
        assert "pending_todos" in data
        assert "reflection_template" in data
        assert "today_date" in data

        # 회고 템플릿에 오늘 날짜가 포함되어 있는지 확인
        assert "하루를 마무리하며" in data["reflection_template"]
        assert "오늘의 성과" in data["reflection_template"]

    def test_create_todo_invalid_category(self, client: TestClient, test_db):
        """잘못된 카테고리로 할일 생성 시 기타로 분류되는지 테스트"""
        todo_data = {
            "title": "카테고리 테스트",
            "category": "존재하지않는카테고리"
        }

        response = client.post("/api/daily/todos", data=todo_data)
        assert response.status_code == 200

        data = response.json()
        assert data["category"] == "기타"  # 기본값으로 설정

        # 데이터베이스 확인
        todo = test_db.query(DailyTodo).filter(DailyTodo.title == "카테고리 테스트").first()
        assert todo is not None
        assert todo.category == TodoCategory.OTHER

    # === 경과일 정보 API 테스트 ===

    def test_get_today_todos_includes_overdue_info(self, client: TestClient, test_db):
        """오늘의 할일 목록에 경과일 정보가 포함되는지 테스트"""
        # 오늘 할일 생성
        today_todo = DailyTodo(
            title="오늘 할일",
            created_date=date.today(),
            scheduled_date=date.today(),
            is_completed=False
        )
        test_db.add(today_todo)

        # 어제 할일 생성 (1일 지남)
        yesterday = date.today() - timedelta(days=1)
        overdue_todo = DailyTodo(
            title="어제 할일",
            created_date=yesterday,
            scheduled_date=yesterday,
            is_completed=False
        )
        test_db.add(overdue_todo)

        test_db.commit()

        response = client.get("/api/daily/todos/today")
        assert response.status_code == 200

        data = response.json()
        assert "todos" in data
        assert len(data["todos"]) == 2

        # 경과일 정보 확인
        for todo_data in data["todos"]:
            assert "days_overdue" in todo_data
            assert "overdue_status" in todo_data
            assert "created_date" in todo_data
            assert "scheduled_date" in todo_data

            if todo_data["title"] == "오늘 할일":
                assert todo_data["days_overdue"] == 0
                assert todo_data["overdue_status"] == "today"
            elif todo_data["title"] == "어제 할일":
                assert todo_data["days_overdue"] == 1
                assert todo_data["overdue_status"] == "overdue"

    def test_get_today_todos_scheduled_status(self, client: TestClient, test_db):
        """미래 예정된 할일의 상태 테스트"""
        # 오늘 생성되었지만 내일 예정인 할일
        tomorrow = date.today() + timedelta(days=1)
        scheduled_todo = DailyTodo(
            title="내일 할일",
            created_date=date.today(),
            scheduled_date=tomorrow,
            is_completed=False
        )
        test_db.add(scheduled_todo)
        test_db.commit()

        response = client.get("/api/daily/todos/today")
        assert response.status_code == 200

        data = response.json()
        # scheduled_date가 미래인 할일은 오늘 할일에 포함되지 않아야 함
        assert len(data["todos"]) == 0

    def test_get_today_todos_with_past_incomplete(self, client: TestClient, test_db):
        """과거 미완료 할일이 자동 이월되어 경과일 정보가 올바른지 테스트"""
        # 3일 전 할일
        three_days_ago = date.today() - timedelta(days=3)
        old_todo = DailyTodo(
            title="3일 전 할일",
            created_date=three_days_ago,
            scheduled_date=three_days_ago,
            is_completed=False
        )
        test_db.add(old_todo)
        test_db.commit()

        response = client.get("/api/daily/todos/today")
        assert response.status_code == 200

        data = response.json()
        assert len(data["todos"]) == 1

        todo_data = data["todos"][0]
        assert todo_data["title"] == "3일 전 할일"
        assert todo_data["days_overdue"] == 3
        assert todo_data["overdue_status"] == "overdue"