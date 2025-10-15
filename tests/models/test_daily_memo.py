"""
DailyMemo 모델 테스트
"""
import pytest
from datetime import date, datetime
from sqlalchemy.exc import IntegrityError

from app.models.daily_memo import DailyMemo
from app.core.timezone import get_current_date, get_current_utc_datetime


class TestDailyMemo:
    """DailyMemo 모델 테스트"""

    def test_create_daily_memo_success(self, test_db):
        """일일 메모 생성 성공 테스트"""
        # Given: 유효한 메모 데이터
        memo_date = get_current_date()
        content = "오늘 아침에 새로운 아이디어가 떠올랐다."

        # When: 메모 생성
        memo = DailyMemo(
            memo_date=memo_date,
            content=content,
            created_at=get_current_utc_datetime()
        )
        test_db.add(memo)
        test_db.commit()

        # Then: 메모가 정상적으로 생성됨
        assert memo.id is not None
        assert memo.memo_date == memo_date
        assert memo.content == content
        assert isinstance(memo.created_at, datetime)
        assert memo.updated_at is None  # 아직 수정하지 않았으므로

    def test_create_daily_memo_without_date_fails(self, test_db):
        """날짜 없이 메모 생성 실패 테스트"""
        # Given: 날짜가 없는 메모 데이터
        content = "날짜 없는 메모"

        # When & Then: 메모 생성 시 실패
        with pytest.raises(IntegrityError):
            memo = DailyMemo(content=content)
            test_db.add(memo)
            test_db.commit()

    def test_create_daily_memo_without_content_fails(self, test_db):
        """내용 없이 메모 생성 실패 테스트"""
        # Given: 내용이 없는 메모 데이터
        memo_date = get_current_date()

        # When & Then: 메모 생성 시 실패
        with pytest.raises(IntegrityError):
            memo = DailyMemo(memo_date=memo_date)
            test_db.add(memo)
            test_db.commit()

    def test_update_daily_memo_updates_timestamp(self, test_db):
        """메모 수정 시 updated_at 업데이트 테스트"""
        import time

        # Given: 기존 메모
        memo = DailyMemo(
            memo_date=date.today(),
            content="원본 내용"
        )
        test_db.add(memo)
        test_db.commit()

        original_created_at = memo.created_at

        # 충분한 시간 간격 보장
        time.sleep(0.1)

        # When: 메모 내용 수정
        memo.content = "수정된 내용"
        test_db.commit()
        test_db.refresh(memo)

        # Then: updated_at이 설정됨
        assert memo.content == "수정된 내용"
        assert memo.created_at == original_created_at  # 생성시간은 변경되지 않음
        assert memo.updated_at is not None
        assert memo.updated_at >= memo.created_at  # updated_at은 created_at과 같거나 이후

    def test_multiple_memos_same_date_allowed(self, test_db):
        """같은 날짜에 여러 메모 허용 테스트"""
        # Given: 같은 날짜의 여러 메모
        memo_date = get_current_date()
        memo1 = DailyMemo(memo_date=memo_date, content="첫 번째 메모")
        memo2 = DailyMemo(memo_date=memo_date, content="두 번째 메모")

        # When: 메모들 저장
        test_db.add_all([memo1, memo2])
        test_db.commit()

        # Then: 모두 정상적으로 저장됨
        assert memo1.id != memo2.id
        assert memo1.memo_date == memo2.memo_date
        assert memo1.content != memo2.content

    def test_memo_string_representation(self, test_db):
        """메모 문자열 표현 테스트"""
        # Given: 메모 생성
        memo_date = date(2024, 10, 11)
        content = "테스트 메모"
        memo = DailyMemo(memo_date=memo_date, content=content)
        test_db.add(memo)
        test_db.commit()

        # When: 문자열 표현 확인
        repr_str = repr(memo)

        # Then: 날짜와 내용이 포함됨
        assert "2024-10-11" in repr_str
        assert "테스트 메모" in repr_str

    def test_get_memos_by_date(self, test_db):
        """날짜별 메모 조회 테스트"""
        # Given: 여러 날짜의 메모들
        today = get_current_date()
        from datetime import timedelta
        yesterday = today - timedelta(days=1)

        memo_today = DailyMemo(memo_date=today, content="오늘 메모")
        memo_yesterday = DailyMemo(memo_date=yesterday, content="어제 메모")

        test_db.add_all([memo_today, memo_yesterday])
        test_db.commit()

        # When: 오늘 날짜의 메모만 조회
        today_memos = test_db.query(DailyMemo).filter(
            DailyMemo.memo_date == today
        ).all()

        # Then: 오늘 메모만 반환됨
        assert len(today_memos) == 1
        assert today_memos[0].content == "오늘 메모"

    def test_memo_content_max_length(self, test_db):
        """메모 내용 최대 길이 테스트"""
        # Given: 매우 긴 메모 내용
        long_content = "A" * 2000  # 2000자 메모
        memo = DailyMemo(
            memo_date=date.today(),
            content=long_content
        )

        # When: 메모 저장
        test_db.add(memo)
        test_db.commit()

        # Then: 정상적으로 저장됨 (Text 타입이므로 긴 텍스트 허용)
        assert memo.content == long_content
        assert len(memo.content) == 2000

    def test_memo_ordering_by_created_at(self, test_db):
        """메모 생성시간 순서 테스트"""
        # Given: 여러 메모를 시간차를 두고 생성
        from datetime import datetime, timezone
        import time

        # 첫 번째 메모 생성
        memo1 = DailyMemo(memo_date=date.today(), content="첫 번째")
        test_db.add(memo1)
        test_db.commit()
        test_db.refresh(memo1)  # 생성 시간 정보 새로고침

        # 충분한 시간 대기 (1초)
        time.sleep(1.0)

        # 두 번째 메모 생성
        memo2 = DailyMemo(memo_date=date.today(), content="두 번째")
        test_db.add(memo2)
        test_db.commit()
        test_db.refresh(memo2)  # 생성 시간 정보 새로고침

        # When: 생성시간 순으로 조회
        memos = test_db.query(DailyMemo).order_by(
            DailyMemo.created_at
        ).all()

        # Then: 생성 순서대로 정렬됨
        assert len(memos) >= 2
        assert memos[0].content == "첫 번째"
        assert memos[1].content == "두 번째"

        # 시간 비교 (같은 경우도 허용하되, 순서는 보장)
        assert memos[0].created_at <= memos[1].created_at

        # ID 기준으로 순서 확인 (생성 순서 보장)
        assert memos[0].id < memos[1].id