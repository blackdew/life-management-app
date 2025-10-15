"""
테스트 설정 및 공통 픽스쳐
"""
import pytest
from datetime import date, datetime
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import Base, get_db
from app.models.todo import DailyTodo, TodoCategory, Todo
from app.models.journey import Journey, JourneyStatus
from app.models.daily_reflection import DailyReflection
from app.models.record import DailyRecord
from app.models.daily_memo import DailyMemo

# 모든 모델을 import 해야 Base.metadata.create_all()에서 테이블이 생성됨

# 테스트용 임시 파일 데이터베이스 (인메모리 대신)
import tempfile
import os
TEST_DATABASE_URL = "sqlite:///./test_temp.db"


# 전역 테스트 엔진과 세션
test_engine = None
test_session_local = None

@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """테스트용 데이터베이스 세션 픽스쳐"""
    global test_engine, test_session_local

    # 새로운 테스트 엔진 생성
    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )

    # 모든 모델이 등록되었는지 확인 후 테이블 생성
    print(f"Registered tables: {list(Base.metadata.tables.keys())}")
    print(f"Creating tables with engine: {test_engine}")
    Base.metadata.create_all(bind=test_engine)
    print("Tables created successfully")

    # 실제로 테이블이 생성되었는지 확인
    with test_engine.connect() as conn:
        inspector = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
        print(f"Actually created tables: {[row[0] for row in inspector]}")

    test_session_local = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # 테스트용 데이터베이스 세션 생성
    db = test_session_local()
    try:
        yield db
    finally:
        db.close()
        # 테스트 완료 후 임시 파일 정리
        if os.path.exists("./test_temp.db"):
            os.remove("./test_temp.db")


@pytest.fixture(scope="function")
def client(test_db: Session) -> Generator[TestClient, None, None]:
    """FastAPI 테스트 클라이언트 픽스쳐"""
    global test_session_local

    def override_get_db():
        """테스트용 데이터베이스 세션을 반환하는 override 함수"""
        if test_session_local is None:
            raise RuntimeError("test_session_local이 초기화되지 않았습니다")

        db = test_session_local()
        try:
            yield db
        finally:
            db.close()

    # dependency override 설정
    original_get_db = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    print(f"Dependency override 설정됨: {get_db} -> {override_get_db}")

    try:
        yield TestClient(app)
    finally:
        # 오버라이드 완전 제거하여 원본 데이터베이스 복원
        if original_get_db is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = original_get_db
        print("Dependency override 제거됨")


# === 샘플 데이터 픽스쳐 ===

@pytest.fixture
def sample_journey(test_db: Session) -> Journey:
    """샘플 여정 생성"""
    journey = Journey(
        title="테스트 여정",
        description="테스트용 여정입니다",
        start_date=date.today(),
        end_date=date(2024, 12, 31),
        status=JourneyStatus.ACTIVE,
        progress=0.0,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    test_db.add(journey)
    test_db.commit()
    test_db.refresh(journey)
    return journey


@pytest.fixture
def sample_daily_todo(test_db: Session, sample_journey: Journey) -> DailyTodo:
    """샘플 일상 할일 생성"""
    todo = DailyTodo(
        title="테스트 할일",
        description="테스트용 할일입니다",
        notes="테스트 메모",
        category=TodoCategory.WORK,
        estimated_minutes=30,
        journey_id=sample_journey.id,
        created_date=date.today(),
        scheduled_date=date.today()
    )
    test_db.add(todo)
    test_db.commit()
    test_db.refresh(todo)
    return todo


@pytest.fixture
def completed_daily_todo(test_db: Session) -> DailyTodo:
    """완료된 일상 할일 생성"""
    todo = DailyTodo(
        title="완료된 할일",
        description="완료된 테스트 할일",
        category=TodoCategory.PERSONAL,
        is_completed=True,
        completed_at=datetime.now(),
        completion_reflection="테스트 회고 내용",
        created_date=date.today(),
        scheduled_date=date.today()
    )
    test_db.add(todo)
    test_db.commit()
    test_db.refresh(todo)
    return todo


@pytest.fixture
def sample_reflection(test_db: Session) -> DailyReflection:
    """샘플 일일 회고 생성"""
    reflection = DailyReflection(
        reflection_date=date.today(),
        reflection_text="오늘의 테스트 회고입니다.",
        total_todos=5,
        completed_todos=3,
        completion_rate=60.0,
        satisfaction_score=4,
        energy_level=3,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        todos_snapshot={
            "completed": [
                {"title": "할일 1", "category": "업무"},
                {"title": "할일 2", "category": "개인"},
            ],
            "pending": [
                {"title": "할일 3", "category": "학습"},
            ]
        }
    )
    test_db.add(reflection)
    test_db.commit()
    test_db.refresh(reflection)
    return reflection


# === 테스트 데이터 생성기 ===

@pytest.fixture
def todo_data():
    """할일 생성용 기본 데이터"""
    return {
        "title": "새로운 할일",
        "description": "새로운 할일 설명",
        "notes": "메모",
        "category": "업무",
        "estimated_minutes": 60
    }


@pytest.fixture
def journey_data():
    """여정 생성용 기본 데이터"""
    return {
        "title": "새로운 여정",
        "description": "새로운 여정 설명",
        "start_date": "2024-10-01",
        "target_date": "2024-12-31"
    }


@pytest.fixture
def reflection_data():
    """회고 생성용 기본 데이터"""
    return {
        "reflection_date": "2024-10-01",
        "reflection_text": "오늘의 회고 내용입니다.",
        "satisfaction_score": 4,
        "energy_level": 3
    }


# === 유틸리티 함수 ===

def create_test_todos(db: Session, count: int = 3) -> list[DailyTodo]:
    """테스트용 여러 할일 생성"""
    todos = []
    for i in range(count):
        todo = DailyTodo(
            title=f"할일 {i+1}",
            description=f"테스트 할일 {i+1}",
            category=TodoCategory.WORK if i % 2 == 0 else TodoCategory.PERSONAL,
            created_date=date.today(),
            scheduled_date=date.today()
        )
        db.add(todo)
        todos.append(todo)

    db.commit()
    for todo in todos:
        db.refresh(todo)

    return todos


def create_completed_todos(db: Session, count: int = 2) -> list[DailyTodo]:
    """테스트용 완료된 할일들 생성"""
    todos = []
    for i in range(count):
        todo = DailyTodo(
            title=f"완료된 할일 {i+1}",
            description=f"완료된 테스트 할일 {i+1}",
            category=TodoCategory.WORK,
            is_completed=True,
            completed_at=datetime.now(),
            completion_reflection=f"회고 {i+1}",
            created_date=date.today(),
            scheduled_date=date.today()
        )
        db.add(todo)
        todos.append(todo)

    db.commit()
    for todo in todos:
        db.refresh(todo)

    return todos


# === 미완료 작업 자동 이월 테스트용 픽스쳐 ===

@pytest.fixture
def past_incomplete_todo(test_db: Session) -> DailyTodo:
    """어제 생성된 미완료 할일"""
    from datetime import timedelta
    yesterday = date.today() - timedelta(days=1)

    todo = DailyTodo(
        title="어제 할일",
        description="어제 생성된 미완료 할일",
        category=TodoCategory.WORK,
        is_completed=False,
        created_date=yesterday,
        scheduled_date=yesterday
    )
    test_db.add(todo)
    test_db.commit()
    test_db.refresh(todo)
    return todo


@pytest.fixture
def old_incomplete_todo(test_db: Session) -> DailyTodo:
    """일주일 전 생성된 미완료 할일"""
    from datetime import timedelta
    week_ago = date.today() - timedelta(days=7)

    todo = DailyTodo(
        title="일주일 전 할일",
        description="일주일 전 생성된 미완료 할일",
        category=TodoCategory.PERSONAL,
        is_completed=False,
        created_date=week_ago,
        scheduled_date=week_ago
    )
    test_db.add(todo)
    test_db.commit()
    test_db.refresh(todo)
    return todo


@pytest.fixture
def past_completed_todo(test_db: Session) -> DailyTodo:
    """어제 생성되어 어제 완료된 할일"""
    from datetime import timedelta
    yesterday = date.today() - timedelta(days=1)
    yesterday_datetime = datetime.combine(yesterday, datetime.min.time())

    todo = DailyTodo(
        title="어제 완료한 할일",
        description="어제 생성되어 완료된 할일",
        category=TodoCategory.HEALTH,
        is_completed=True,
        completed_at=yesterday_datetime,  # 어제 완료로 설정
        completion_reflection="어제 완료 회고",
        created_date=yesterday,
        scheduled_date=yesterday
    )
    test_db.add(todo)
    test_db.commit()
    test_db.refresh(todo)
    return todo


@pytest.fixture
def future_scheduled_todo(test_db: Session) -> DailyTodo:
    """내일 예정된 할일"""
    from datetime import timedelta
    tomorrow = date.today() + timedelta(days=1)

    todo = DailyTodo(
        title="내일 할일",
        description="내일 예정된 할일",
        category=TodoCategory.LEARNING,
        is_completed=False,
        created_date=date.today(),
        scheduled_date=tomorrow
    )
    test_db.add(todo)
    test_db.commit()
    test_db.refresh(todo)
    return todo


@pytest.fixture
def three_days_ago_todo(test_db: Session) -> DailyTodo:
    """3일 전 생성된 미완료 할일"""
    from datetime import timedelta
    three_days_ago = date.today() - timedelta(days=3)

    todo = DailyTodo(
        title="3일 전 할일",
        description="3일 전 생성된 미완료 할일",
        category=TodoCategory.RELATIONSHIP,
        is_completed=False,
        created_date=three_days_ago,
        scheduled_date=three_days_ago
    )
    test_db.add(todo)
    test_db.commit()
    test_db.refresh(todo)
    return todo