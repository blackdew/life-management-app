"""
API 응답의 타임존 변환 테스트

실제 타임존 변환 로직을 테스트합니다.
SQLite는 UTC로 저장하고 API 응답에서 한국 시간으로 변환되는지 확인합니다.
"""
import pytest
import re
from datetime import datetime, date
from fastapi.testclient import TestClient

from app.main import app
from app.models.daily_memo import DailyMemo


class TestTimezoneApiResponses:
    """API 응답의 타임존 변환 테스트"""

    def test_daily_memo_api_returns_korea_timezone_format(self, test_db, client):
        """일일 메모 API 응답이 한국 시간 형식으로 변환되는지 테스트"""
        # Given: 테스트 전 기존 메모 정리
        test_db.query(DailyMemo).delete()
        test_db.commit()

        # 메모를 DB에 저장 (UTC 시간으로 저장됨)
        import uuid
        unique_content = f"타임존 테스트 메모-{uuid.uuid4().hex[:8]}"
        memo = DailyMemo(
            memo_date=date.today(),
            content=unique_content
        )
        test_db.add(memo)
        test_db.commit()
        test_db.refresh(memo)

        # When: API로 메모 조회
        response = client.get(f"/api/daily/memos/{memo.id}")

        # Then: 응답이 성공하고 한국 시간 형식으로 변환됨
        assert response.status_code == 200
        data = response.json()

        # 응답에 created_at이 있고, 한국 시간 형식(+09:00)인지 확인
        assert "created_at" in data
        assert data["created_at"].endswith("+09:00")
        assert data["content"] == unique_content

        # 날짜 형식이 올바른지 확인 (ISO 8601 형식)
        datetime_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*\+09:00'
        assert re.match(datetime_pattern, data["created_at"])

    def test_daily_memo_list_api_returns_korea_timezone_format(self, test_db, client):
        """일일 메모 목록 API 응답이 한국 시간 형식으로 변환되는지 테스트"""
        # Given: 오늘 날짜의 메모들 생성
        import uuid
        unique_suffix = uuid.uuid4().hex[:8]
        memo1 = DailyMemo(
            memo_date=date.today(),
            content=f"첫 번째 메모-{unique_suffix}"
        )
        memo2 = DailyMemo(
            memo_date=date.today(),
            content=f"두 번째 메모-{unique_suffix}"
        )
        test_db.add_all([memo1, memo2])
        test_db.commit()

        # When: 메모 목록 API 호출
        response = client.get("/api/daily/memos/today")

        # Then: 모든 메모의 타임스탬프가 한국 시간 형식임
        assert response.status_code == 200
        data = response.json()

        assert "memos" in data
        assert len(data["memos"]) >= 2

        # 모든 메모가 한국 시간 형식을 가지는지 확인
        for memo in data["memos"]:
            assert "created_at" in memo
            assert memo["created_at"].endswith("+09:00")

    def test_daily_memo_create_api_returns_korea_timezone_format(self, test_db, client):
        """메모 생성 API가 한국 시간 형식으로 응답하는지 테스트"""
        # Given: 테스트 전 기존 메모 정리
        test_db.query(DailyMemo).delete()
        test_db.commit()

        # 메모 생성 요청 데이터
        import uuid
        unique_content = f"새로운 메모 내용-{uuid.uuid4().hex[:8]}"
        memo_data = {
            "memo_date": date.today().isoformat(),
            "content": unique_content
        }

        # When: 메모 생성 API 호출
        response = client.post("/api/daily/memos", data=memo_data)

        # Then: 성공 응답과 한국 시간 형식 반환
        assert response.status_code == 201
        data = response.json()

        # API 응답은 한국 시간 형식으로 반환됨
        assert "created_at" in data
        assert data["created_at"].endswith("+09:00")
        assert data["content"] == unique_content

        # DB에 실제로 저장되었는지 확인
        saved_memo = test_db.query(DailyMemo).filter_by(content=unique_content).first()
        assert saved_memo is not None

    def test_daily_memo_update_api_returns_korea_timezone_format(self, test_db, client):
        """메모 수정 API의 타임존 형식 테스트"""
        # Given: 기존 메모
        memo = DailyMemo(
            memo_date=date.today(),
            content="원본 내용"
        )
        test_db.add(memo)
        test_db.commit()
        test_db.refresh(memo)

        # When: 메모 수정
        update_data = {"content": "수정된 내용"}
        response = client.put(f"/api/daily/memos/{memo.id}", data=update_data)

        # Then: 응답 성공 및 타임존 형식 확인
        assert response.status_code == 200
        data = response.json()

        assert data["content"] == "수정된 내용"
        # 응답에 타임스탬프 필드가 있다면 한국 시간 형식인지 확인
        if "created_at" in data:
            assert data["created_at"].endswith("+09:00")
        if "updated_at" in data:
            assert data["updated_at"].endswith("+09:00")

    def test_timezone_consistency_across_endpoints(self, test_db, client):
        """모든 엔드포인트에서 일관된 타임존 형식 사용 테스트"""
        # Given: 메모 생성
        memo_data = {
            "memo_date": date.today().isoformat(),
            "content": "일관성 테스트 메모"
        }
        create_response = client.post("/api/daily/memos", data=memo_data)
        assert create_response.status_code == 201
        memo_id = create_response.json()["id"]

        # When: 다양한 엔드포인트로 동일한 메모 조회
        endpoints_to_test = [
            f"/api/daily/memos/{memo_id}",
            "/api/daily/memos/today",
            "/api/daily/memos/recent"
        ]

        # Then: 모든 엔드포인트에서 일관된 타임존 형식 사용
        for endpoint in endpoints_to_test:
            response = client.get(endpoint)
            assert response.status_code == 200
            data = response.json()

            # 단일 메모 응답인지 목록 응답인지 확인
            if "memos" in data:
                # 목록 응답
                for memo in data["memos"]:
                    if memo.get("content") == "일관성 테스트 메모":
                        assert memo["created_at"].endswith("+09:00")
            else:
                # 단일 메모 응답
                if data.get("content") == "일관성 테스트 메모":
                    assert data["created_at"].endswith("+09:00")