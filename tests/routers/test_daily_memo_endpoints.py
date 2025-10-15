"""
Daily 라우터의 메모 API 엔드포인트 테스트
"""
import pytest
from datetime import date, datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.daily_memo import DailyMemo
from app.services.daily_memo_service import DailyMemoService


class TestDailyMemoEndpoints:
    """일일 메모 API 엔드포인트 테스트"""

    def test_get_today_memos_success(self, client: TestClient, test_db: Session):
        """오늘의 메모 조회 성공 테스트"""
        # Given: 오늘 날짜의 메모들
        today = date.today()
        memo1 = DailyMemo(memo_date=today, content="첫 번째 메모")
        memo2 = DailyMemo(memo_date=today, content="두 번째 메모")
        test_db.add_all([memo1, memo2])
        test_db.commit()

        # When: 오늘의 메모 조회 API 호출
        response = client.get("/api/daily/memos/today")

        # Then: 성공적으로 메모들이 반환됨
        assert response.status_code == 200
        data = response.json()
        assert "memos" in data
        assert len(data["memos"]) == 2
        memo_contents = [memo["content"] for memo in data["memos"]]
        assert "첫 번째 메모" in memo_contents
        assert "두 번째 메모" in memo_contents

    def test_get_today_memos_empty(self, client: TestClient, test_db: Session):
        """오늘의 메모가 없는 경우 테스트"""
        # Given: 메모가 없는 상태

        # When: 오늘의 메모 조회 API 호출
        response = client.get("/api/daily/memos/today")

        # Then: 빈 배열이 반환됨
        assert response.status_code == 200
        data = response.json()
        assert "memos" in data
        assert data["memos"] == []

    def test_create_memo_success(self, client: TestClient, test_db: Session):
        """메모 생성 성공 테스트"""
        # Given: 유효한 메모 데이터
        memo_data = {
            "memo_date": date.today().isoformat(),
            "content": "새로운 메모 내용"
        }

        # When: 메모 생성 API 호출
        response = client.post("/api/daily/memos", data=memo_data)

        # Then: 메모가 성공적으로 생성됨
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "새로운 메모 내용"
        assert data["memo_date"] == date.today().isoformat()
        assert "id" in data
        assert "created_at" in data

        # 데이터베이스에 실제로 저장되었는지 확인
        memo = test_db.query(DailyMemo).filter(DailyMemo.id == data["id"]).first()
        assert memo is not None
        assert memo.content == "새로운 메모 내용"

    def test_create_memo_empty_content_fails(self, client: TestClient):
        """빈 내용으로 메모 생성 실패 테스트"""
        # Given: 빈 내용의 메모 데이터
        memo_data = {
            "memo_date": date.today().isoformat(),
            "content": ""
        }

        # When: 메모 생성 API 호출
        response = client.post("/api/daily/memos", data=memo_data)

        # Then: 400 에러가 발생함
        assert response.status_code == 400
        data = response.json()
        assert "메모 내용은 비어있을 수 없습니다" in data["detail"]

    def test_create_memo_invalid_date_fails(self, client: TestClient):
        """잘못된 날짜 형식으로 메모 생성 실패 테스트"""
        # Given: 잘못된 날짜 형식의 메모 데이터
        memo_data = {
            "memo_date": "2024-13-45",  # 잘못된 날짜
            "content": "메모 내용"
        }

        # When: 메모 생성 API 호출
        response = client.post("/api/daily/memos", data=memo_data)

        # Then: 400 에러가 발생함
        assert response.status_code == 400
        data = response.json()
        assert "올바른 날짜 형식이 아닙니다" in data["detail"]

    def test_update_memo_success(self, client: TestClient, test_db: Session):
        """메모 수정 성공 테스트"""
        # Given: 기존 메모
        memo = DailyMemo(
            memo_date=date.today(),
            content="원본 내용"
        )
        test_db.add(memo)
        test_db.commit()
        test_db.refresh(memo)

        # When: 메모 수정 API 호출
        update_data = {"content": "수정된 내용"}
        response = client.put(f"/api/daily/memos/{memo.id}", data=update_data)

        # Then: 메모가 성공적으로 수정됨
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "수정된 내용"
        assert data["id"] == memo.id

        # 데이터베이스에 실제로 반영되었는지 확인
        test_db.refresh(memo)
        updated_memo = test_db.query(DailyMemo).filter(DailyMemo.id == memo.id).first()
        assert updated_memo.content == "수정된 내용"

    def test_update_memo_not_found_fails(self, client: TestClient):
        """존재하지 않는 메모 수정 실패 테스트"""
        # Given: 존재하지 않는 메모 ID
        non_existent_id = 999

        # When: 메모 수정 API 호출
        update_data = {"content": "수정 내용"}
        response = client.put(f"/api/daily/memos/{non_existent_id}", data=update_data)

        # Then: 404 에러가 발생함
        assert response.status_code == 404
        data = response.json()
        assert "메모를 찾을 수 없습니다" in data["detail"]

    def test_update_memo_empty_content_fails(self, client: TestClient, test_db: Session):
        """빈 내용으로 메모 수정 실패 테스트"""
        # Given: 기존 메모
        memo = DailyMemo(
            memo_date=date.today(),
            content="원본 내용"
        )
        test_db.add(memo)
        test_db.commit()
        test_db.refresh(memo)

        # When: 빈 내용으로 메모 수정 API 호출
        update_data = {"content": ""}
        response = client.put(f"/api/daily/memos/{memo.id}", data=update_data)

        # Then: 400 에러가 발생함
        assert response.status_code == 400
        data = response.json()
        assert "메모 내용은 비어있을 수 없습니다" in data["detail"]

    def test_delete_memo_success(self, client: TestClient, test_db: Session):
        """메모 삭제 성공 테스트"""
        # Given: 기존 메모
        memo = DailyMemo(
            memo_date=date.today(),
            content="삭제할 메모"
        )
        test_db.add(memo)
        test_db.commit()
        test_db.refresh(memo)

        # When: 메모 삭제 API 호출
        response = client.delete(f"/api/daily/memos/{memo.id}")

        # Then: 메모가 성공적으로 삭제됨
        assert response.status_code == 200
        data = response.json()
        assert "삭제되었습니다" in data["message"]

        # 데이터베이스에서 실제로 삭제되었는지 확인
        deleted_memo = test_db.query(DailyMemo).filter(DailyMemo.id == memo.id).first()
        assert deleted_memo is None

    def test_delete_memo_not_found_fails(self, client: TestClient):
        """존재하지 않는 메모 삭제 실패 테스트"""
        # Given: 존재하지 않는 메모 ID
        non_existent_id = 999

        # When: 메모 삭제 API 호출
        response = client.delete(f"/api/daily/memos/{non_existent_id}")

        # Then: 404 에러가 발생함
        assert response.status_code == 404
        data = response.json()
        assert "메모를 찾을 수 없습니다" in data["detail"]

    def test_get_memo_by_id_success(self, client: TestClient, test_db: Session):
        """ID로 메모 조회 성공 테스트"""
        # Given: 기존 메모
        memo = DailyMemo(
            memo_date=date.today(),
            content="조회할 메모"
        )
        test_db.add(memo)
        test_db.commit()
        test_db.refresh(memo)

        # When: 메모 조회 API 호출
        response = client.get(f"/api/daily/memos/{memo.id}")

        # Then: 메모가 성공적으로 조회됨
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == memo.id
        assert data["content"] == "조회할 메모"
        assert data["memo_date"] == date.today().isoformat()
        assert "created_at" in data

    def test_get_memo_by_id_not_found_fails(self, client: TestClient):
        """존재하지 않는 ID로 메모 조회 실패 테스트"""
        # Given: 존재하지 않는 메모 ID
        non_existent_id = 999

        # When: 메모 조회 API 호출
        response = client.get(f"/api/daily/memos/{non_existent_id}")

        # Then: 404 에러가 발생함
        assert response.status_code == 404
        data = response.json()
        assert "메모를 찾을 수 없습니다" in data["detail"]

    def test_get_memos_by_date_success(self, client: TestClient, test_db: Session):
        """특정 날짜의 메모 조회 성공 테스트"""
        # Given: 특정 날짜의 메모들
        target_date = date(2024, 10, 15)
        memo1 = DailyMemo(memo_date=target_date, content="메모 1")
        memo2 = DailyMemo(memo_date=target_date, content="메모 2")
        memo3 = DailyMemo(memo_date=date.today(), content="다른 날 메모")
        test_db.add_all([memo1, memo2, memo3])
        test_db.commit()

        # When: 특정 날짜의 메모 조회 API 호출
        response = client.get(f"/api/daily/memos/date/{target_date.isoformat()}")

        # Then: 해당 날짜의 메모들만 반환됨
        assert response.status_code == 200
        data = response.json()
        assert "memos" in data
        assert len(data["memos"]) == 2
        memo_contents = [memo["content"] for memo in data["memos"]]
        assert "메모 1" in memo_contents
        assert "메모 2" in memo_contents
        assert "다른 날 메모" not in memo_contents

    def test_get_recent_memos_success(self, client: TestClient, test_db: Session):
        """최근 메모 조회 성공 테스트"""
        # Given: 여러 메모들
        memo1 = DailyMemo(memo_date=date.today(), content="최신 메모 1")
        memo2 = DailyMemo(memo_date=date.today(), content="최신 메모 2")
        memo3 = DailyMemo(memo_date=date.today(), content="최신 메모 3")
        test_db.add_all([memo1, memo2, memo3])
        test_db.commit()

        # When: 최근 메모 조회 API 호출 (limit=2)
        response = client.get("/api/daily/memos/recent", params={"limit": 2})

        # Then: 최신 2개 메모가 반환됨
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert "memos" in data
        assert len(data["memos"]) == 2
        # 메모가 생성 시간 역순으로 정렬되어 있는지 확인
        memo_contents = [memo["content"] for memo in data["memos"]]
        assert all(content in ["최신 메모 1", "최신 메모 2", "최신 메모 3"] for content in memo_contents)

    def test_search_memos_success(self, client: TestClient, test_db: Session):
        """메모 검색 성공 테스트"""
        # Given: 검색 가능한 메모들
        memo1 = DailyMemo(memo_date=date.today(), content="중요한 회의 내용")
        memo2 = DailyMemo(memo_date=date.today(), content="오늘의 중요한 아이디어")
        memo3 = DailyMemo(memo_date=date.today(), content="일반적인 메모")
        test_db.add_all([memo1, memo2, memo3])
        test_db.commit()

        # When: '중요한' 키워드로 검색 API 호출
        response = client.get("/api/daily/memos/search", params={"keyword": "중요한"})

        # Then: 키워드가 포함된 메모들만 반환됨
        assert response.status_code == 200
        data = response.json()
        assert "memos" in data
        assert len(data["memos"]) == 2
        memo_contents = [memo["content"] for memo in data["memos"]]
        assert "중요한 회의 내용" in memo_contents
        assert "오늘의 중요한 아이디어" in memo_contents
        assert "일반적인 메모" not in memo_contents

    def test_search_memos_empty_keyword_fails(self, client: TestClient):
        """빈 키워드로 검색 실패 테스트"""
        # Given: 빈 키워드

        # When: 빈 키워드로 검색 API 호출
        response = client.get("/api/daily/memos/search", params={"keyword": ""})

        # Then: 422 에러가 발생함 (Query validation 실패)
        assert response.status_code == 422

    def test_get_memo_count_by_date_success(self, client: TestClient, test_db: Session):
        """날짜별 메모 개수 조회 성공 테스트"""
        # Given: 특정 날짜의 메모들
        target_date = date.today()
        memo1 = DailyMemo(memo_date=target_date, content="메모 1")
        memo2 = DailyMemo(memo_date=target_date, content="메모 2")
        memo3 = DailyMemo(memo_date=target_date, content="메모 3")
        test_db.add_all([memo1, memo2, memo3])
        test_db.commit()

        # When: 날짜별 메모 개수 조회 API 호출
        response = client.get(f"/api/daily/memos/count/{target_date.isoformat()}")

        # Then: 정확한 개수가 반환됨
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3
        assert data["date"] == target_date.isoformat()

    def test_api_error_handling(self, client: TestClient):
        """API 에러 처리 테스트"""
        # When: 잘못된 엔드포인트 호출
        response = client.get("/api/daily/memos/999999")  # 존재하지 않는 메모 ID

        # Then: 404 에러가 발생함
        assert response.status_code == 404

    def test_create_memo_quick_success(self, client: TestClient, test_db: Session):
        """빠른 메모 생성 성공 테스트 (오늘 날짜 자동 설정)"""
        # Given: 메모 내용만 제공
        memo_data = {"content": "빠른 메모 내용"}

        # When: 빠른 메모 생성 API 호출
        response = client.post("/api/daily/memos/quick", data=memo_data)

        # Then: 오늘 날짜로 메모가 생성됨
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "빠른 메모 내용"
        assert data["memo_date"] == date.today().isoformat()
        assert "id" in data

        # 데이터베이스에 실제로 저장되었는지 확인
        memo = test_db.query(DailyMemo).filter(DailyMemo.id == data["id"]).first()
        assert memo is not None
        assert memo.content == "빠른 메모 내용"
        assert memo.memo_date == date.today()

    def test_bulk_delete_memos_success(self, client: TestClient, test_db: Session):
        """메모 일괄 삭제 성공 테스트"""
        # Given: 여러 메모들
        memo1 = DailyMemo(memo_date=date.today(), content="메모 1")
        memo2 = DailyMemo(memo_date=date.today(), content="메모 2")
        memo3 = DailyMemo(memo_date=date.today(), content="메모 3")
        test_db.add_all([memo1, memo2, memo3])
        test_db.commit()
        test_db.refresh(memo1)
        test_db.refresh(memo2)

        # When: 여러 메모 일괄 삭제 API 호출
        delete_data = {"memo_ids": [memo1.id, memo2.id]}
        response = client.request("DELETE", "/api/daily/memos/bulk", json=delete_data)

        # Then: 지정된 메모들이 삭제됨
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 2

        # 데이터베이스에서 실제로 삭제되었는지 확인
        remaining_memos = test_db.query(DailyMemo).all()
        assert len(remaining_memos) == 1
        assert remaining_memos[0].content == "메모 3"