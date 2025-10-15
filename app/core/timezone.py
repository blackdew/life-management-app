"""
타임존 관리 유틸리티

올바른 국제화 지원을 위한 타임존 설계:
1. 데이터베이스 저장: 항상 UTC (timezone-naive)
2. 사용자 표시: 환경변수 TIMEZONE에 따라 변환해서 표시

이 설계를 통해 같은 데이터가 다른 시간대에서도 올바르게 표시됩니다.
"""

from datetime import datetime, date
from typing import Optional
import pytz
from sqlalchemy import func

from app.core.config import settings


def get_timezone() -> pytz.BaseTzInfo:
    """설정된 타임존을 반환합니다."""
    return pytz.timezone(settings.timezone)


def get_utc_timezone() -> pytz.BaseTzInfo:
    """UTC 타임존 객체를 반환합니다."""
    return pytz.UTC


def get_current_utc_datetime() -> datetime:
    """현재 UTC 시간을 반환합니다 (DB 저장용).

    Returns:
        timezone-naive UTC datetime (DB 저장용)
    """
    return datetime.utcnow()


def get_current_local_datetime() -> datetime:
    """현재 로컬 시간을 반환합니다 (표시용).

    Returns:
        timezone-aware local datetime
    """
    return datetime.now(get_timezone())


def get_current_date() -> date:
    """현재 날짜를 설정된 타임존으로 반환합니다."""
    return get_current_local_datetime().date()


def utc_to_local(utc_dt: Optional[datetime]) -> Optional[datetime]:
    """UTC datetime을 로컬 타임존으로 변환합니다.

    Args:
        utc_dt: UTC 시간 (timezone-naive, UTC로 가정)

    Returns:
        로컬 타임존으로 변환된 시간 (timezone-aware)
    """
    if utc_dt is None:
        return None

    # naive datetime을 UTC timezone-aware로 변환
    if utc_dt.tzinfo is None:
        utc_dt = get_utc_timezone().localize(utc_dt)

    # 로컬 타임존으로 변환
    return utc_dt.astimezone(get_timezone())


def local_to_utc(local_dt: Optional[datetime]) -> Optional[datetime]:
    """로컬 타임존 datetime을 UTC로 변환합니다.

    Args:
        local_dt: 로컬 시간 (timezone-aware 또는 naive)

    Returns:
        UTC 시간 (timezone-naive, DB 저장용)
    """
    if local_dt is None:
        return None

    # naive datetime인 경우 로컬 타임존으로 가정
    if local_dt.tzinfo is None:
        local_dt = get_timezone().localize(local_dt)

    # UTC로 변환 후 timezone-naive로 변경 (DB 저장용)
    return local_dt.astimezone(get_utc_timezone()).replace(tzinfo=None)


def format_datetime_for_display(dt: Optional[datetime], format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """UTC datetime을 로컬 타임존으로 변환해서 표시용 포맷팅합니다.

    Args:
        dt: UTC datetime (timezone-naive, DB에서 조회된 값)
        format_string: 포맷 문자열

    Returns:
        로컬 타임존으로 변환된 포맷팅 문자열
    """
    if dt is None:
        return ""

    # UTC를 로컬 타임존으로 변환 후 포맷팅
    local_dt = utc_to_local(dt)
    return local_dt.strftime(format_string) if local_dt else ""


def format_date_for_display(d: Optional[date]) -> str:
    """date를 화면 표시용 한국어 포맷으로 변환합니다."""
    if d is None:
        return ""
    return d.strftime("%Y년 %m월 %d일")


def format_time_for_display(dt: Optional[datetime]) -> str:
    """UTC datetime을 로컬 시간으로 변환해서 시간만 표시합니다.

    Args:
        dt: UTC datetime (timezone-naive, DB에서 조회된 값)

    Returns:
        "HH:MM" 형식의 로컬 시간 문자열
    """
    if dt is None:
        return ""

    local_dt = utc_to_local(dt)
    return local_dt.strftime("%H:%M") if local_dt else ""


def format_datetime_for_api(dt: Optional[datetime]) -> Optional[str]:
    """API 응답용 datetime 포맷팅 (ISO 형식, 로컬 타임존).

    Args:
        dt: UTC datetime (timezone-naive, DB에서 조회된 값)

    Returns:
        ISO 형식의 로컬 시간 문자열 또는 None
    """
    if dt is None:
        return None

    local_dt = utc_to_local(dt)
    return local_dt.isoformat() if local_dt else None


# 유틸리티 함수들
def localize_datetime(dt: datetime) -> datetime:
    """하위 호환성: UTC datetime을 로컬 타임존으로 변환"""
    return utc_to_local(dt)


def is_same_date(dt1: datetime, dt2: datetime) -> bool:
    """두 datetime이 같은 날짜인지 확인 (타임존 고려)"""
    local_dt1 = utc_to_local(dt1) if dt1 else None
    local_dt2 = utc_to_local(dt2) if dt2 else None

    if not local_dt1 or not local_dt2:
        return False

    return local_dt1.date() == local_dt2.date()


def is_today(dt: datetime) -> bool:
    """주어진 UTC datetime이 로컬 타임존 기준 오늘인지 확인"""
    return is_same_date(dt, get_current_utc_datetime())


def get_today_start() -> datetime:
    """오늘 00:00:00을 UTC로 반환합니다 (DB 저장용)."""
    today = get_current_date()
    local_start = get_timezone().localize(datetime.combine(today, datetime.min.time()))
    return local_to_utc(local_start)


def get_today_end() -> datetime:
    """오늘 23:59:59를 UTC로 반환합니다 (DB 저장용)."""
    today = get_current_date()
    local_end = get_timezone().localize(datetime.combine(today, datetime.max.time()))
    return local_to_utc(local_end)