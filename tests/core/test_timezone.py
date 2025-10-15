"""
타임존 유틸리티 함수 테스트
"""
import pytest
from datetime import datetime, date
import pytz
from unittest.mock import patch

from app.core.timezone import (
    get_timezone,
    get_utc_timezone,
    get_current_utc_datetime,
    get_current_local_datetime,
    get_current_date,
    utc_to_local,
    local_to_utc,
    format_datetime_for_display,
    format_date_for_display,
    format_time_for_display,
    format_datetime_for_api,
    is_same_date,
    is_today,
    get_today_start,
    get_today_end,
)


class TestTimezoneUtilities:
    """타임존 유틸리티 함수 테스트"""

    def test_get_timezone_returns_korea_timezone(self):
        """get_timezone이 한국 시간대를 반환하는지 테스트"""
        # When
        tz = get_timezone()

        # Then
        assert isinstance(tz, pytz.BaseTzInfo)
        assert str(tz) == "Asia/Seoul"

    def test_get_utc_timezone_returns_utc(self):
        """get_utc_timezone이 UTC 시간대를 반환하는지 테스트"""
        # When
        tz = get_utc_timezone()

        # Then
        assert tz == pytz.UTC

    def test_get_current_utc_datetime_returns_utc_time(self):
        """get_current_utc_datetime이 UTC 시간을 반환하는지 테스트"""
        # When
        utc_dt = get_current_utc_datetime()

        # Then
        assert isinstance(utc_dt, datetime)
        assert utc_dt.tzinfo is None  # timezone-naive여야 함

    def test_get_current_local_datetime_returns_korea_time(self):
        """get_current_local_datetime이 한국 시간을 반환하는지 테스트"""
        # When
        local_dt = get_current_local_datetime()

        # Then
        assert isinstance(local_dt, datetime)
        assert local_dt.tzinfo is not None  # timezone-aware여야 함
        assert str(local_dt.tzinfo) == "Asia/Seoul"

    def test_get_current_date_returns_korea_date(self):
        """get_current_date가 한국 기준 날짜를 반환하는지 테스트"""
        # When
        current_date = get_current_date()

        # Then
        assert isinstance(current_date, date)

    def test_utc_to_local_conversion(self):
        """UTC에서 로컬 타임존으로 변환 테스트"""
        # Given: UTC 시간 (2024-10-14 15:30:00 UTC)
        utc_dt = datetime(2024, 10, 14, 15, 30, 0)  # timezone-naive UTC

        # When: 로컬 시간으로 변환
        local_dt = utc_to_local(utc_dt)

        # Then: 한국 시간 (UTC+9)으로 변환됨
        assert local_dt is not None
        assert local_dt.hour == 0  # 15 + 9 = 24 -> 0 (다음날)
        assert local_dt.minute == 30
        assert local_dt.day == 15  # 다음날
        assert str(local_dt.tzinfo) == "Asia/Seoul"

    def test_utc_to_local_with_none_input(self):
        """utc_to_local에 None 입력 시 None 반환 테스트"""
        # When
        result = utc_to_local(None)

        # Then
        assert result is None

    def test_local_to_utc_conversion(self):
        """로컬 타임존에서 UTC로 변환 테스트"""
        # Given: 한국 시간 (2024-10-14 00:30:00 KST)
        korea_tz = pytz.timezone("Asia/Seoul")
        local_dt = korea_tz.localize(datetime(2024, 10, 14, 0, 30, 0))

        # When: UTC로 변환
        utc_dt = local_to_utc(local_dt)

        # Then: UTC 시간 (KST-9)으로 변환됨
        assert utc_dt is not None
        assert utc_dt.hour == 15  # 0 - 9 = -9 -> 15 (전날)
        assert utc_dt.minute == 30
        assert utc_dt.day == 13  # 전날
        assert utc_dt.tzinfo is None  # timezone-naive여야 함

    def test_local_to_utc_with_none_input(self):
        """local_to_utc에 None 입력 시 None 반환 테스트"""
        # When
        result = local_to_utc(None)

        # Then
        assert result is None

    def test_format_datetime_for_display(self):
        """datetime 표시용 포맷팅 테스트"""
        # Given: UTC 시간 (2024-10-14 15:30:00 UTC)
        utc_dt = datetime(2024, 10, 14, 15, 30, 0)

        # When: 표시용 포맷으로 변환
        formatted = format_datetime_for_display(utc_dt)

        # Then: 한국 시간으로 변환되어 포맷됨
        assert "2024-10-15 00:30:00" == formatted

    def test_format_datetime_for_display_with_custom_format(self):
        """datetime 표시용 커스텀 포맷팅 테스트"""
        # Given: UTC 시간
        utc_dt = datetime(2024, 10, 14, 15, 30, 0)

        # When: 커스텀 포맷으로 변환
        formatted = format_datetime_for_display(utc_dt, "%Y년 %m월 %d일 %H시 %M분")

        # Then
        assert "2024년 10월 15일 00시 30분" == formatted

    def test_format_datetime_for_display_with_none(self):
        """format_datetime_for_display에 None 입력 시 빈 문자열 반환"""
        # When
        result = format_datetime_for_display(None)

        # Then
        assert result == ""

    def test_format_date_for_display(self):
        """date 표시용 포맷팅 테스트"""
        # Given
        test_date = date(2024, 10, 14)

        # When
        formatted = format_date_for_display(test_date)

        # Then
        assert formatted == "2024년 10월 14일"

    def test_format_date_for_display_with_none(self):
        """format_date_for_display에 None 입력 시 빈 문자열 반환"""
        # When
        result = format_date_for_display(None)

        # Then
        assert result == ""

    def test_format_time_for_display(self):
        """시간만 표시용 포맷팅 테스트"""
        # Given: UTC 시간 (2024-10-14 15:30:00 UTC)
        utc_dt = datetime(2024, 10, 14, 15, 30, 0)

        # When: 시간만 포맷
        formatted = format_time_for_display(utc_dt)

        # Then: 한국 시간으로 변환된 시간만 표시
        assert formatted == "00:30"

    def test_format_time_for_display_with_none(self):
        """format_time_for_display에 None 입력 시 빈 문자열 반환"""
        # When
        result = format_time_for_display(None)

        # Then
        assert result == ""

    def test_format_datetime_for_api(self):
        """API 응답용 datetime 포맷팅 테스트"""
        # Given: UTC 시간 (2024-10-14 15:30:00 UTC)
        utc_dt = datetime(2024, 10, 14, 15, 30, 0)

        # When: API 응답용 포맷으로 변환
        formatted = format_datetime_for_api(utc_dt)

        # Then: ISO 형식으로 한국 시간이 반환됨
        assert formatted is not None
        assert "2024-10-15T00:30:00+09:00" == formatted

    def test_format_datetime_for_api_with_none(self):
        """format_datetime_for_api에 None 입력 시 None 반환"""
        # When
        result = format_datetime_for_api(None)

        # Then
        assert result is None

    def test_is_same_date_with_same_local_date(self):
        """같은 로컬 날짜인 UTC 시간들이 같은 날짜로 인식되는지 테스트"""
        # Given: 같은 한국 날짜의 서로 다른 UTC 시간들
        utc_dt1 = datetime(2024, 10, 13, 15, 0, 0)  # 한국시간 2024-10-14 00:00
        utc_dt2 = datetime(2024, 10, 13, 23, 59, 0)  # 한국시간 2024-10-14 08:59

        # When
        result = is_same_date(utc_dt1, utc_dt2)

        # Then
        assert result is True

    def test_is_same_date_with_different_local_date(self):
        """다른 로컬 날짜인 UTC 시간들이 다른 날짜로 인식되는지 테스트"""
        # Given: 다른 한국 날짜의 UTC 시간들
        utc_dt1 = datetime(2024, 10, 13, 14, 59, 0)  # 한국시간 2024-10-13 23:59
        utc_dt2 = datetime(2024, 10, 13, 15, 0, 0)   # 한국시간 2024-10-14 00:00

        # When
        result = is_same_date(utc_dt1, utc_dt2)

        # Then
        assert result is False

    def test_is_same_date_with_none_inputs(self):
        """is_same_date에 None 입력들이 있을 때 False 반환"""
        # Given
        utc_dt = datetime(2024, 10, 14, 15, 30, 0)

        # When & Then
        assert is_same_date(None, utc_dt) is False
        assert is_same_date(utc_dt, None) is False
        assert is_same_date(None, None) is False

    @patch('app.core.timezone.get_current_utc_datetime')
    def test_is_today_true(self, mock_get_current_utc):
        """오늘 날짜인 UTC 시간이 오늘로 인식되는지 테스트"""
        # Given: 현재 UTC 시간을 고정
        mock_current_utc = datetime(2024, 10, 14, 12, 0, 0)  # UTC
        mock_get_current_utc.return_value = mock_current_utc

        # 같은 한국 날짜의 다른 UTC 시간
        test_utc_dt = datetime(2024, 10, 13, 16, 0, 0)  # 한국시간 2024-10-14 01:00

        # When
        result = is_today(test_utc_dt)

        # Then
        assert result is True

    @patch('app.core.timezone.get_current_utc_datetime')
    def test_is_today_false(self, mock_get_current_utc):
        """오늘이 아닌 날짜인 UTC 시간이 오늘이 아닌 것으로 인식되는지 테스트"""
        # Given: 현재 UTC 시간을 고정
        mock_current_utc = datetime(2024, 10, 14, 12, 0, 0)  # UTC
        mock_get_current_utc.return_value = mock_current_utc

        # 다른 한국 날짜의 UTC 시간
        test_utc_dt = datetime(2024, 10, 12, 16, 0, 0)  # 한국시간 2024-10-13 01:00

        # When
        result = is_today(test_utc_dt)

        # Then
        assert result is False

    @patch('app.core.timezone.get_current_date')
    def test_get_today_start(self, mock_get_current_date):
        """오늘 시작 시간 (00:00:00) UTC 변환 테스트"""
        # Given: 현재 날짜를 고정
        mock_get_current_date.return_value = date(2024, 10, 14)

        # When: 오늘 시작 시간을 UTC로 가져옴
        start_utc = get_today_start()

        # Then: 한국시간 2024-10-14 00:00:00 -> UTC 2024-10-13 15:00:00
        assert start_utc.year == 2024
        assert start_utc.month == 10
        assert start_utc.day == 13
        assert start_utc.hour == 15
        assert start_utc.minute == 0
        assert start_utc.second == 0
        assert start_utc.tzinfo is None  # timezone-naive

    @patch('app.core.timezone.get_current_date')
    def test_get_today_end(self, mock_get_current_date):
        """오늘 끝 시간 (23:59:59) UTC 변환 테스트"""
        # Given: 현재 날짜를 고정
        mock_get_current_date.return_value = date(2024, 10, 14)

        # When: 오늘 끝 시간을 UTC로 가져옴
        end_utc = get_today_end()

        # Then: 한국시간 2024-10-14 23:59:59 -> UTC 2024-10-14 14:59:59
        assert end_utc.year == 2024
        assert end_utc.month == 10
        assert end_utc.day == 14
        assert end_utc.hour == 14
        assert end_utc.minute == 59
        assert end_utc.second == 59
        assert end_utc.tzinfo is None  # timezone-naive