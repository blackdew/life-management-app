"""
Reflections API 테스트
"""
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.models.daily_reflection import DailyReflection
from app.models.todo import DailyTodo, TodoCategory


class TestReflectionsAPI:
    """Reflections API 테스트 클래스"""

    def test_create_reflection_success(self, client: TestClient, test_db):
        """회고 생성 성공 테스트"""
        # 테스트용 할일 생성 (회고 생성 시 참조됨)
        from datetime import datetime
        todo = DailyTodo(
            title="테스트 할일",
            category=TodoCategory.WORK,
            created_date=date.today(),
            scheduled_date=date.today(),
            is_completed=True,
            completed_at=datetime.now()  # completed_at 설정 필요
        )
        test_db.add(todo)
        test_db.commit()

        reflection_data = {
            "reflection_date": date.today().isoformat(),
            "reflection_text": "오늘은 정말 보람찬 하루였다. 많은 것을 배웠고 성취감이 크다.",
            "satisfaction_score": 4,
            "energy_level": 3
        }

        response = client.post("/api/reflections/", data=reflection_data)
        assert response.status_code == 200

        data = response.json()
        assert data["reflection_date"] == date.today().isoformat()
        assert data["reflection_text"] == "오늘은 정말 보람찬 하루였다. 많은 것을 배웠고 성취감이 크다."
        assert data["satisfaction_score"] == 4
        assert data["energy_level"] == 3
        assert data["total_todos"] == 1
        assert data["completed_todos"] == 1
        assert data["completion_rate"] == 100.0

        # 데이터베이스 확인
        reflection = test_db.query(DailyReflection).filter(
            DailyReflection.reflection_date == date.today()
        ).first()
        assert reflection is not None
        assert reflection.satisfaction_score == 4
        assert reflection.energy_level == 3

    def test_create_reflection_invalid_satisfaction_score(self, client: TestClient, test_db):
        """잘못된 만족도 점수로 회고 생성 실패 테스트"""
        reflection_data = {
            "reflection_date": date.today().isoformat(),
            "reflection_text": "테스트 회고",
            "satisfaction_score": 6,  # 1-5 범위를 벗어남
            "energy_level": 3
        }

        response = client.post("/api/reflections/", data=reflection_data)
        assert response.status_code == 400

    def test_create_reflection_invalid_energy_level(self, client: TestClient, test_db):
        """잘못된 에너지 레벨로 회고 생성 실패 테스트"""
        reflection_data = {
            "reflection_date": date.today().isoformat(),
            "reflection_text": "테스트 회고",
            "satisfaction_score": 4,
            "energy_level": 0  # 1-5 범위를 벗어남
        }

        response = client.post("/api/reflections/", data=reflection_data)
        assert response.status_code == 400

    def test_create_reflection_invalid_date_format(self, client: TestClient, test_db):
        """잘못된 날짜 형식으로 회고 생성 실패 테스트"""
        reflection_data = {
            "reflection_date": "invalid-date",
            "reflection_text": "테스트 회고",
            "satisfaction_score": 4,
            "energy_level": 3
        }

        response = client.post("/api/reflections/", data=reflection_data)
        assert response.status_code == 400

    def test_create_reflection_without_optional_scores(self, client: TestClient, test_db):
        """만족도와 에너지 레벨 없이 회고 생성 테스트"""
        reflection_data = {
            "reflection_date": date.today().isoformat(),
            "reflection_text": "점수 없는 회고"
        }

        response = client.post("/api/reflections/", data=reflection_data)
        assert response.status_code == 200

        data = response.json()
        assert data["satisfaction_score"] is None
        assert data["energy_level"] is None

    def test_get_reflection_by_date_success(self, client: TestClient, test_db):
        """날짜별 회고 조회 성공 테스트"""
        # 테스트 회고 생성
        reflection = DailyReflection(
            reflection_date=date.today(),
            reflection_text="테스트 회고 내용",
            total_todos=5,
            completed_todos=3,
            completion_rate=60.0,
            satisfaction_score=4,
            energy_level=3,
            todos_snapshot={"completed": [], "incomplete": []}
        )
        test_db.add(reflection)
        test_db.commit()
        test_db.refresh(reflection)

        response = client.get(f"/api/reflections/date/{date.today().isoformat()}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == reflection.id
        assert data["reflection_date"] == date.today().isoformat()
        assert data["reflection_text"] == "테스트 회고 내용"
        assert data["completion_rate"] == 60.0
        assert data["satisfaction_score"] == 4
        assert data["energy_level"] == 3

    def test_get_reflection_by_date_not_found(self, client: TestClient, test_db):
        """존재하지 않는 날짜의 회고 조회 테스트"""
        future_date = (date.today() + timedelta(days=10)).isoformat()
        response = client.get(f"/api/reflections/date/{future_date}")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "해당 날짜의 회고가 없습니다"

    def test_get_reflection_by_date_invalid_format(self, client: TestClient, test_db):
        """잘못된 날짜 형식으로 회고 조회 실패 테스트"""
        response = client.get("/api/reflections/date/invalid-date")
        assert response.status_code == 400

    def test_get_recent_reflections_empty(self, client: TestClient, test_db):
        """최근 회고 목록 조회 - 빈 목록 테스트"""
        response = client.get("/api/reflections/recent")
        assert response.status_code == 200

        data = response.json()
        assert data["reflections"] == []

    def test_get_recent_reflections_with_data(self, client: TestClient, test_db):
        """최근 회고 목록 조회 - 데이터가 있는 경우"""
        # 여러 회고 생성
        for i in range(3):
            reflection = DailyReflection(
                reflection_date=date.today() - timedelta(days=i),
                reflection_text=f"회고 {i+1}번째 내용입니다.",
                total_todos=5,
                completed_todos=3,
                completion_rate=60.0,
                satisfaction_score=4,
                energy_level=3,
                todos_snapshot={"completed": [], "incomplete": []}
            )
            test_db.add(reflection)
        test_db.commit()

        response = client.get("/api/reflections/recent?limit=5")
        assert response.status_code == 200

        data = response.json()
        assert len(data["reflections"]) == 3

        # 최신 날짜가 첫 번째로 와야 함
        assert data["reflections"][0]["reflection_date"] == date.today().isoformat()

    def test_get_recent_reflections_with_limit(self, client: TestClient, test_db):
        """제한된 개수로 최근 회고 목록 조회"""
        # 5개 회고 생성
        for i in range(5):
            reflection = DailyReflection(
                reflection_date=date.today() - timedelta(days=i),
                reflection_text=f"회고 {i+1}",
                total_todos=1,
                completed_todos=1,
                completion_rate=100.0,
                todos_snapshot={"completed": [], "incomplete": []}
            )
            test_db.add(reflection)
        test_db.commit()

        response = client.get("/api/reflections/recent?limit=3")
        assert response.status_code == 200

        data = response.json()
        assert len(data["reflections"]) == 3

    def test_get_reflection_stats_empty(self, client: TestClient, test_db):
        """회고 통계 조회 - 데이터가 없는 경우"""
        response = client.get("/api/reflections/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["total_days"] == 0
        assert data["avg_completion_rate"] == 0.0
        assert data["avg_satisfaction"] == 0.0
        assert data["avg_energy"] == 0.0

    def test_get_reflection_stats_with_data(self, client: TestClient, test_db):
        """회고 통계 조회 - 데이터가 있는 경우"""
        # 통계용 회고 데이터 생성
        reflections_data = [
            (80.0, 4, 3),  # 완료율, 만족도, 에너지
            (60.0, 3, 4),
            (100.0, 5, 5),
        ]

        for i, (completion_rate, satisfaction, energy) in enumerate(reflections_data):
            reflection = DailyReflection(
                reflection_date=date.today() - timedelta(days=i),
                reflection_text=f"통계 테스트 회고 {i+1}",
                total_todos=5,
                completed_todos=int(5 * completion_rate / 100),
                completion_rate=completion_rate,
                satisfaction_score=satisfaction,
                energy_level=energy,
                todos_snapshot={"completed": [], "incomplete": []}
            )
            test_db.add(reflection)
        test_db.commit()

        response = client.get("/api/reflections/stats?days=30")
        assert response.status_code == 200

        data = response.json()
        assert data["total_days"] == 3
        assert data["avg_completion_rate"] == 80.0  # (80+60+100)/3
        assert data["avg_satisfaction"] == 4.0  # (4+3+5)/3
        assert data["avg_energy"] == 4.0  # (3+4+5)/3

    def test_delete_reflection_success(self, client: TestClient, test_db):
        """회고 삭제 성공 테스트"""
        # 삭제할 회고 생성
        reflection = DailyReflection(
            reflection_date=date.today(),
            reflection_text="삭제할 회고",
            total_todos=1,
            completed_todos=1,
            completion_rate=100.0,
            todos_snapshot={"completed": [], "incomplete": []}
        )
        test_db.add(reflection)
        test_db.commit()

        response = client.delete(f"/api/reflections/date/{date.today().isoformat()}")
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "회고가 삭제되었습니다"

        # 데이터베이스에서 삭제 확인
        deleted_reflection = test_db.query(DailyReflection).filter(
            DailyReflection.reflection_date == date.today()
        ).first()
        assert deleted_reflection is None

    def test_delete_reflection_not_found(self, client: TestClient, test_db):
        """존재하지 않는 회고 삭제 실패 테스트"""
        future_date = (date.today() + timedelta(days=10)).isoformat()
        response = client.delete(f"/api/reflections/date/{future_date}")
        assert response.status_code == 404

    def test_delete_reflection_invalid_date(self, client: TestClient, test_db):
        """잘못된 날짜 형식으로 회고 삭제 실패 테스트"""
        response = client.delete("/api/reflections/date/invalid-date")
        assert response.status_code == 400


    def test_update_existing_reflection(self, client: TestClient, test_db):
        """기존 회고 업데이트 테스트 (동일 날짜 재생성)"""
        # 기존 회고 생성
        existing_reflection = DailyReflection(
            reflection_date=date.today(),
            reflection_text="기존 회고 내용",
            total_todos=1,
            completed_todos=1,
            completion_rate=100.0,
            satisfaction_score=3,
            energy_level=3,
            todos_snapshot={"completed": [], "incomplete": []}
        )
        test_db.add(existing_reflection)
        test_db.commit()

        # 동일 날짜로 새 회고 생성 (업데이트됨)
        reflection_data = {
            "reflection_date": date.today().isoformat(),
            "reflection_text": "업데이트된 회고 내용",
            "satisfaction_score": 5,
            "energy_level": 4
        }

        response = client.post("/api/reflections/", data=reflection_data)
        assert response.status_code == 200

        data = response.json()
        assert data["reflection_text"] == "업데이트된 회고 내용"
        assert data["satisfaction_score"] == 5
        assert data["energy_level"] == 4

        # 데이터베이스에서 하나만 존재하는지 확인
        reflections = test_db.query(DailyReflection).filter(
            DailyReflection.reflection_date == date.today()
        ).all()
        assert len(reflections) == 1
        assert reflections[0].reflection_text == "업데이트된 회고 내용"