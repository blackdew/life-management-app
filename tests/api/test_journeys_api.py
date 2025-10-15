"""
여정 API 테스트
"""
import pytest
from datetime import date, timedelta, datetime
from fastapi.testclient import TestClient
from app.main import app
from app.models.journey import Journey, JourneyStatus


class TestJourneysAPI:
    """여정 API 테스트 클래스"""

    def test_create_journey_success(self, client: TestClient, test_db):
        """여정 생성 성공 테스트"""
        journey_data = {
            "title": "테스트 여정",
            "description": "테스트용 여정입니다",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=30)).isoformat(),
        }

        response = client.post("/api/journeys/", data=journey_data)
        if response.status_code != 200:
            print(f"Error response: {response.status_code}")
            print(f"Error content: {response.text}")
        assert response.status_code == 200  # HTMX 요청이므로 200 반환

        # 데이터베이스에 저장되었는지 확인
        journey = test_db.query(Journey).filter(Journey.title == "테스트 여정").first()
        assert journey is not None
        assert journey.title == "테스트 여정"
        assert journey.description == "테스트용 여정입니다"
        assert journey.status == JourneyStatus.PLANNING

    def test_create_journey_duplicate_title(self, client: TestClient, test_db):
        """중복 제목 여정 생성 실패 테스트"""
        # 첫 번째 여정 생성
        journey_data = {
            "title": "중복 테스트",
            "description": "첫 번째 여정",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=30)).isoformat(),
        }
        response = client.post("/api/journeys/", data=journey_data)
        assert response.status_code == 200

        # 동일한 제목으로 두 번째 여정 생성 시도
        duplicate_data = {
            "title": "중복 테스트",  # 동일한 제목
            "description": "두 번째 여정",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=60)).isoformat(),
        }
        response = client.post("/api/journeys/", data=duplicate_data)
        assert response.status_code == 409  # Conflict

    def test_create_journey_duplicate_title_case_insensitive(self, client: TestClient, test_db):
        """대소문자 무시 중복 제목 테스트"""
        # 첫 번째 여정
        journey_data = {
            "title": "Case Test",
            "description": "첫 번째",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=30)).isoformat(),
        }
        response = client.post("/api/journeys/", data=journey_data)
        assert response.status_code == 200

        # 대소문자만 다른 제목으로 시도
        duplicate_data = {
            "title": "case test",  # 소문자
            "description": "두 번째",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=60)).isoformat(),
        }
        response = client.post("/api/journeys/", data=duplicate_data)
        assert response.status_code == 409

    def test_create_journey_duplicate_title_with_spaces(self, client: TestClient, test_db):
        """공백 포함 중복 제목 테스트"""
        # 첫 번째 여정
        journey_data = {
            "title": "  Space Test  ",
            "description": "첫 번째",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=30)).isoformat(),
        }
        response = client.post("/api/journeys/", data=journey_data)
        assert response.status_code == 200

        # 공백만 다른 제목으로 시도
        duplicate_data = {
            "title": "Space Test",  # 공백 제거
            "description": "두 번째",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=60)).isoformat(),
        }
        response = client.post("/api/journeys/", data=duplicate_data)
        assert response.status_code == 409

    def test_create_journey_invalid_dates(self, client: TestClient, test_db):
        """잘못된 날짜로 여정 생성 실패 테스트"""
        journey_data = {
            "title": "날짜 테스트",
            "description": "시작일이 종료일보다 늦음",
            "start_date": (date.today() + timedelta(days=30)).isoformat(),  # 종료일보다 늦음
            "end_date": date.today().isoformat(),
        }

        response = client.post("/api/journeys/", data=journey_data)
        assert response.status_code == 400  # Bad Request

    def test_get_all_journeys_empty(self, client: TestClient, test_db):
        """빈 여정 목록 조회 테스트"""
        response = client.get("/api/journeys/")
        assert response.status_code == 200

        data = response.json()
        assert data["journeys"] == []
        assert data["total"] == 0

    def test_get_all_journeys_with_data(self, client: TestClient, test_db):
        """여정이 있는 경우 목록 조회 테스트"""
        # 테스트 데이터 생성
        journey1 = Journey(
            title="여정 1",
            description="첫 번째 여정",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status=JourneyStatus.ACTIVE,
            progress=25.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        journey2 = Journey(
            title="여정 2",
            description="두 번째 여정",
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=40),
            status=JourneyStatus.PLANNING,
            progress=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        test_db.add(journey1)
        test_db.add(journey2)
        test_db.commit()

        response = client.get("/api/journeys/")
        assert response.status_code == 200

        data = response.json()
        assert len(data["journeys"]) == 2
        assert data["total"] == 2

        # 시작일 순으로 정렬되는지 확인
        assert data["journeys"][0]["title"] == "여정 1"
        assert data["journeys"][1]["title"] == "여정 2"

    def test_get_journey_by_id_success(self, client: TestClient, test_db):
        """ID로 여정 조회 성공 테스트"""
        journey = Journey(
            title="조회 테스트",
            description="ID로 조회할 여정",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status=JourneyStatus.ACTIVE,
            progress=50.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        test_db.add(journey)
        test_db.commit()
        test_db.refresh(journey)

        response = client.get(f"/api/journeys/{journey.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == journey.id
        assert data["title"] == "조회 테스트"
        assert data["progress"] == 50.0

    def test_get_journey_by_id_not_found(self, client: TestClient, test_db):
        """존재하지 않는 여정 조회 실패 테스트"""
        response = client.get("/api/journeys/999")
        assert response.status_code == 404

    def test_update_journey_success(self, client: TestClient, test_db):
        """여정 수정 성공 테스트"""
        journey = Journey(
            title="수정 전",
            description="수정 전 설명",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status=JourneyStatus.PLANNING,
            progress=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        test_db.add(journey)
        test_db.commit()
        test_db.refresh(journey)

        update_data = {
            "title": "수정 후",
            "description": "수정 후 설명",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=60)).isoformat(),
            "status": "진행중",
            "progress": 30.0
        }

        response = client.post(f"/api/journeys/{journey.id}/edit", data=update_data)
        assert response.status_code == 200

        # 데이터베이스에서 확인
        test_db.refresh(journey)
        assert journey.title == "수정 후"
        assert journey.description == "수정 후 설명"
        assert journey.status == JourneyStatus.ACTIVE
        assert journey.progress == 30.0

    def test_update_journey_not_found(self, client: TestClient, test_db):
        """존재하지 않는 여정 수정 실패 테스트"""
        update_data = {
            "title": "존재하지 않음",
            "description": "테스트",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=30)).isoformat(),
            "status": "계획중",
            "progress": 0.0
        }

        response = client.post("/api/journeys/999/edit", data=update_data)
        assert response.status_code == 404

    def test_delete_journey_success(self, client: TestClient, test_db):
        """여정 삭제 성공 테스트"""
        journey = Journey(
            title="삭제할 여정",
            description="삭제 테스트용",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status=JourneyStatus.PLANNING,
            progress=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        test_db.add(journey)
        test_db.commit()
        test_db.refresh(journey)

        response = client.delete(f"/api/journeys/{journey.id}")
        assert response.status_code == 204

        # 데이터베이스에서 삭제되었는지 확인
        deleted_journey = test_db.query(Journey).filter(Journey.id == journey.id).first()
        assert deleted_journey is None

    def test_delete_journey_not_found(self, client: TestClient, test_db):
        """존재하지 않는 여정 삭제 실패 테스트"""
        response = client.delete("/api/journeys/999")
        assert response.status_code == 404

    def test_delete_journey_with_todos(self, client: TestClient, test_db):
        """연결된 TODO가 있는 여정 삭제 실패 테스트"""
        # 여정 생성
        journey = Journey(
            title="TODO가 있는 여정",
            description="삭제 불가능",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status=JourneyStatus.ACTIVE,
            progress=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        test_db.add(journey)
        test_db.commit()
        test_db.refresh(journey)

        # 연결된 TODO 생성
        from app.models.todo import Todo
        todo = Todo(
            title="연결된 할일",
            description="여정과 연결됨",
            journey_id=journey.id,
            is_completed=False
        )

        test_db.add(todo)
        test_db.commit()

        response = client.delete(f"/api/journeys/{journey.id}")
        assert response.status_code == 409  # Conflict

    def test_get_journey_new_form(self, client: TestClient, test_db):
        """새 여정 폼 조회 테스트"""
        response = client.get("/api/journeys/new")
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()

    def test_get_journey_edit_form(self, client: TestClient, test_db):
        """여정 편집 폼 조회 테스트"""
        journey = Journey(
            title="편집 폼 테스트",
            description="편집 폼 조회용",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            status=JourneyStatus.ACTIVE,
            progress=25.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        test_db.add(journey)
        test_db.commit()
        test_db.refresh(journey)

        response = client.get(f"/api/journeys/{journey.id}/edit")
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()

    def test_get_journey_edit_form_not_found(self, client: TestClient, test_db):
        """존재하지 않는 여정 편집 폼 조회 실패 테스트"""
        response = client.get("/api/journeys/999/edit")
        assert response.status_code == 404