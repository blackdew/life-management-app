"""
일일 메모 서비스

날짜별 메모 관리를 위한 비즈니스 로직을 담당합니다.
CRUD 기본 기능과 날짜별 조회, 최근 메모 조회 등의 기능을 제공합니다.
"""

from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.daily_memo import DailyMemo
from app.core.timezone import get_current_utc_datetime


class DailyMemoService:
    """일일 메모 서비스"""

    @staticmethod
    def create_memo(db: Session, memo_date: date, content: str) -> DailyMemo:
        """새로운 메모 생성

        Args:
            db: 데이터베이스 세션
            memo_date: 메모 날짜
            content: 메모 내용

        Returns:
            생성된 메모 객체

        Raises:
            ValueError: 메모 내용이 비어있는 경우
        """
        # 유효성 검사
        if not content or content.strip() == "":
            raise ValueError("메모 내용은 비어있을 수 없습니다")

        # 메모 생성 (UTC 시간으로 저장)
        current_utc_time = get_current_utc_datetime()
        memo = DailyMemo(
            memo_date=memo_date,
            content=content.strip(),
            created_at=current_utc_time
        )

        db.add(memo)
        db.commit()
        db.refresh(memo)

        return memo

    @staticmethod
    def get_memos_by_date(db: Session, memo_date: date) -> List[DailyMemo]:
        """특정 날짜의 메모들 조회 (시간순 정렬)

        Args:
            db: 데이터베이스 세션
            memo_date: 조회할 날짜

        Returns:
            해당 날짜의 메모 리스트 (생성시간 순)
        """
        return (
            db.query(DailyMemo)
            .filter(DailyMemo.memo_date == memo_date)
            .order_by(DailyMemo.created_at.asc())
            .all()
        )

    @staticmethod
    def get_memo_by_id(db: Session, memo_id: int) -> Optional[DailyMemo]:
        """ID로 특정 메모 조회

        Args:
            db: 데이터베이스 세션
            memo_id: 메모 ID

        Returns:
            메모 객체 또는 None
        """
        return db.query(DailyMemo).filter(DailyMemo.id == memo_id).first()

    @staticmethod
    def update_memo(db: Session, memo_id: int, content: str) -> DailyMemo:
        """메모 내용 수정

        Args:
            db: 데이터베이스 세션
            memo_id: 수정할 메모 ID
            content: 새로운 메모 내용

        Returns:
            수정된 메모 객체

        Raises:
            ValueError: 메모를 찾을 수 없거나 내용이 비어있는 경우
        """
        # 유효성 검사
        if not content or content.strip() == "":
            raise ValueError("메모 내용은 비어있을 수 없습니다")

        # 메모 조회
        memo = db.query(DailyMemo).filter(DailyMemo.id == memo_id).first()
        if not memo:
            raise ValueError("메모를 찾을 수 없습니다")

        # 내용 수정 (updated_at도 UTC로 저장)
        memo.content = content.strip()
        memo.updated_at = get_current_utc_datetime()
        db.commit()
        db.refresh(memo)

        return memo

    @staticmethod
    def delete_memo(db: Session, memo_id: int) -> bool:
        """메모 삭제

        Args:
            db: 데이터베이스 세션
            memo_id: 삭제할 메모 ID

        Returns:
            삭제 성공 여부

        Raises:
            ValueError: 메모를 찾을 수 없는 경우
        """
        # 메모 조회
        memo = db.query(DailyMemo).filter(DailyMemo.id == memo_id).first()
        if not memo:
            raise ValueError("메모를 찾을 수 없습니다")

        # 메모 삭제
        db.delete(memo)
        db.commit()

        return True

    @staticmethod
    def get_recent_memos(db: Session, limit: int = 10) -> List[DailyMemo]:
        """최근 메모들 조회 (최신순)

        Args:
            db: 데이터베이스 세션
            limit: 조회할 메모 개수 (기본 10개)

        Returns:
            최근 메모 리스트 (최신순)
        """
        return (
            db.query(DailyMemo)
            .order_by(DailyMemo.created_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_memos_count_by_date(db: Session, memo_date: date) -> int:
        """특정 날짜의 메모 개수 조회

        Args:
            db: 데이터베이스 세션
            memo_date: 조회할 날짜

        Returns:
            해당 날짜의 메모 개수
        """
        return (
            db.query(DailyMemo)
            .filter(DailyMemo.memo_date == memo_date)
            .count()
        )

    @staticmethod
    def get_memos_by_date_range(
        db: Session,
        start_date: date,
        end_date: date
    ) -> List[DailyMemo]:
        """날짜 범위의 메모들 조회

        Args:
            db: 데이터베이스 세션
            start_date: 시작 날짜
            end_date: 종료 날짜

        Returns:
            날짜 범위 내의 메모 리스트 (날짜별, 시간순)
        """
        return (
            db.query(DailyMemo)
            .filter(
                DailyMemo.memo_date >= start_date,
                DailyMemo.memo_date <= end_date
            )
            .order_by(
                DailyMemo.memo_date.asc(),
                DailyMemo.created_at.asc()
            )
            .all()
        )

    @staticmethod
    def search_memos(db: Session, keyword: str, limit: int = 50) -> List[DailyMemo]:
        """키워드로 메모 검색

        Args:
            db: 데이터베이스 세션
            keyword: 검색 키워드
            limit: 조회할 메모 개수 (기본 50개)

        Returns:
            키워드가 포함된 메모 리스트 (최신순)
        """
        if not keyword or keyword.strip() == "":
            return []

        search_pattern = f"%{keyword.strip()}%"
        return (
            db.query(DailyMemo)
            .filter(DailyMemo.content.ilike(search_pattern))
            .order_by(DailyMemo.created_at.desc())
            .limit(limit)
            .all()
        )