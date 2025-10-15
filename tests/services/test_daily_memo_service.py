"""
DailyMemoService 테스트
"""
import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.models.daily_memo import DailyMemo
from app.services.daily_memo_service import DailyMemoService


class TestDailyMemoService:
    """DailyMemoService 테스트"""

    def test_create_memo_success(self, test_db: Session):
        """메모 생성 성공 테스트"""
        # Given: 유효한 메모 데이터
        memo_date = date.today()
        content = "새로운 메모 내용"

        # When: 메모 생성
        memo = DailyMemoService.create_memo(
            db=test_db,
            memo_date=memo_date,
            content=content
        )

        # Then: 메모가 정상적으로 생성됨
        assert memo.id is not None
        assert memo.memo_date == memo_date
        assert memo.content == content
        assert isinstance(memo.created_at, datetime)

    def test_create_memo_empty_content_fails(self, test_db: Session):
        """빈 내용으로 메모 생성 실패 테스트"""
        # Given: 빈 내용
        memo_date = date.today()
        content = ""

        # When & Then: 메모 생성 시 실패
        with pytest.raises(ValueError, match="메모 내용은 비어있을 수 없습니다"):
            DailyMemoService.create_memo(
                db=test_db,
                memo_date=memo_date,
                content=content
            )

    def test_get_memos_by_date_success(self, test_db: Session):
        """날짜별 메모 조회 성공 테스트"""
        # Given: 여러 날짜의 메모들
        today = date.today()
        yesterday = date(today.year, today.month, today.day - 1)

        memo1 = DailyMemo(memo_date=today, content="오늘 메모 1")
        memo2 = DailyMemo(memo_date=today, content="오늘 메모 2")
        memo3 = DailyMemo(memo_date=yesterday, content="어제 메모")

        test_db.add_all([memo1, memo2, memo3])
        test_db.commit()

        # When: 오늘 날짜의 메모 조회
        today_memos = DailyMemoService.get_memos_by_date(test_db, today)

        # Then: 오늘 메모만 반환됨 (시간순 정렬)
        assert len(today_memos) == 2
        assert all(memo.memo_date == today for memo in today_memos)
        # 생성 시간 순으로 정렬됨
        assert today_memos[0].created_at <= today_memos[1].created_at

    def test_get_memos_by_date_empty_result(self, test_db: Session):
        """메모가 없는 날짜 조회 테스트"""
        # Given: 메모가 없는 날짜
        memo_date = date.today()

        # When: 메모 조회
        memos = DailyMemoService.get_memos_by_date(test_db, memo_date)

        # Then: 빈 리스트 반환
        assert memos == []

    def test_update_memo_success(self, test_db: Session):
        """메모 수정 성공 테스트"""
        # Given: 기존 메모
        memo = DailyMemo(
            memo_date=date.today(),
            content="원본 내용"
        )
        test_db.add(memo)
        test_db.commit()
        test_db.refresh(memo)

        # When: 메모 수정
        updated_memo = DailyMemoService.update_memo(
            db=test_db,
            memo_id=memo.id,
            content="수정된 내용"
        )

        # Then: 내용이 수정됨
        assert updated_memo.content == "수정된 내용"
        assert updated_memo.id == memo.id
        assert updated_memo.memo_date == memo.memo_date

    def test_update_memo_not_found_fails(self, test_db: Session):
        """존재하지 않는 메모 수정 실패 테스트"""
        # Given: 존재하지 않는 메모 ID
        non_existent_id = 999

        # When & Then: 메모 수정 시 실패
        with pytest.raises(ValueError, match="메모를 찾을 수 없습니다"):
            DailyMemoService.update_memo(
                db=test_db,
                memo_id=non_existent_id,
                content="수정 내용"
            )

    def test_update_memo_empty_content_fails(self, test_db: Session):
        """빈 내용으로 메모 수정 실패 테스트"""
        # Given: 기존 메모
        memo = DailyMemo(
            memo_date=date.today(),
            content="원본 내용"
        )
        test_db.add(memo)
        test_db.commit()
        test_db.refresh(memo)

        # When & Then: 빈 내용으로 수정 시 실패
        with pytest.raises(ValueError, match="메모 내용은 비어있을 수 없습니다"):
            DailyMemoService.update_memo(
                db=test_db,
                memo_id=memo.id,
                content=""
            )

    def test_delete_memo_success(self, test_db: Session):
        """메모 삭제 성공 테스트"""
        # Given: 기존 메모
        memo = DailyMemo(
            memo_date=date.today(),
            content="삭제할 메모"
        )
        test_db.add(memo)
        test_db.commit()
        test_db.refresh(memo)

        # When: 메모 삭제
        result = DailyMemoService.delete_memo(test_db, memo.id)

        # Then: 삭제 성공
        assert result is True

        # 실제로 삭제되었는지 확인
        deleted_memo = test_db.query(DailyMemo).filter(DailyMemo.id == memo.id).first()
        assert deleted_memo is None

    def test_delete_memo_not_found_fails(self, test_db: Session):
        """존재하지 않는 메모 삭제 실패 테스트"""
        # Given: 존재하지 않는 메모 ID
        non_existent_id = 999

        # When & Then: 메모 삭제 시 실패
        with pytest.raises(ValueError, match="메모를 찾을 수 없습니다"):
            DailyMemoService.delete_memo(test_db, non_existent_id)

    def test_get_memo_by_id_success(self, test_db: Session):
        """ID로 메모 조회 성공 테스트"""
        # Given: 기존 메모
        memo = DailyMemo(
            memo_date=date.today(),
            content="조회할 메모"
        )
        test_db.add(memo)
        test_db.commit()
        test_db.refresh(memo)

        # When: 메모 조회
        found_memo = DailyMemoService.get_memo_by_id(test_db, memo.id)

        # Then: 메모가 조회됨
        assert found_memo is not None
        assert found_memo.id == memo.id
        assert found_memo.content == memo.content

    def test_get_memo_by_id_not_found(self, test_db: Session):
        """존재하지 않는 ID로 메모 조회 테스트"""
        # Given: 존재하지 않는 메모 ID
        non_existent_id = 999

        # When: 메모 조회
        found_memo = DailyMemoService.get_memo_by_id(test_db, non_existent_id)

        # Then: None 반환
        assert found_memo is None

    def test_get_recent_memos_success(self, test_db: Session):
        """최근 메모 조회 테스트"""
        # Given: 여러 메모들 생성
        today = date.today()
        yesterday = date(today.year, today.month, today.day - 1)

        memo1 = DailyMemo(memo_date=yesterday, content="메모 1")
        memo2 = DailyMemo(memo_date=yesterday, content="메모 2")
        memo3 = DailyMemo(memo_date=today, content="메모 3")

        test_db.add_all([memo1, memo2, memo3])
        test_db.commit()

        # When: 최근 메모 2개 조회
        recent_memos = DailyMemoService.get_recent_memos(test_db, limit=2)

        # Then: 정확히 2개가 반환되고, 모두 유효한 메모임
        assert len(recent_memos) == 2
        memo_contents = [memo.content for memo in recent_memos]
        assert all(content in ["메모 1", "메모 2", "메모 3"] for content in memo_contents)

        # 전체 조회 시 3개 모두 반환됨
        all_recent_memos = DailyMemoService.get_recent_memos(test_db, limit=10)
        assert len(all_recent_memos) == 3

    def test_get_memos_count_by_date(self, test_db: Session):
        """날짜별 메모 개수 조회 테스트"""
        # Given: 오늘 날짜의 메모들
        today = date.today()
        memo1 = DailyMemo(memo_date=today, content="메모 1")
        memo2 = DailyMemo(memo_date=today, content="메모 2")
        memo3 = DailyMemo(memo_date=today, content="메모 3")

        test_db.add_all([memo1, memo2, memo3])
        test_db.commit()

        # When: 메모 개수 조회
        count = DailyMemoService.get_memos_count_by_date(test_db, today)

        # Then: 정확한 개수 반환
        assert count == 3

    def test_get_memos_count_by_date_zero(self, test_db: Session):
        """메모가 없는 날짜의 개수 조회 테스트"""
        # Given: 메모가 없는 날짜
        empty_date = date.today()

        # When: 메모 개수 조회
        count = DailyMemoService.get_memos_count_by_date(test_db, empty_date)

        # Then: 0 반환
        assert count == 0