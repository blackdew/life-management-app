# Daily Flow - 프로젝트 현재 상태 문서

> **최종 업데이트:** 2025년 10월 22일
> **버전:** 1.0.0
> **상태:** 운영 중 (개발/메인 환경 분리)

---

## 📊 프로젝트 개요

**Daily Flow**는 일상 중심의 할일 관리 및 회고 시스템입니다. 단순한 TODO 앱을 넘어 일상의 작은 성취들을 기록하고 회고하며, 삶의 여정을 관리하는 실용적인 웹 애플리케이션입니다.

### 핵심 가치
- **일상 중심**: 매일의 작은 성취에 집중
- **회고 기반**: 완료 시 배움과 성과 기록
- **여정 연결**: 목표 지향적 할일 관리
- **실시간 피드백**: 개수 기반 완료 현황

---

## 🏗️ 기술 스택

### 백엔드
- **FastAPI** 0.115.5 - 고성능 Python 웹 프레임워크
- **SQLAlchemy** 2.0.36 - ORM 및 데이터베이스 관리
- **Alembic** 1.14.0 - 데이터베이스 마이그레이션
- **SQLite** - 로컬 데이터베이스 (dev/main 분리)
- **Pydantic** 2.9.2 - 데이터 검증 및 직렬화
- **Python** 3.11+ - 프로그래밍 언어

### 프론트엔드
- **Jinja2** - 서버사이드 템플릿 엔진
- **Tailwind CSS** - 유틸리티 기반 CSS 프레임워크
- **Vanilla JavaScript** - 경량 클라이언트 로직
- **모달 기반 UI** - 깔끔한 사용자 경험

### 개발 도구
- **uv** - 빠른 Python 패키지 관리자
- **pytest** 8.3.3 - 테스트 프레임워크
- **pytest-asyncio** - 비동기 테스트 지원
- **httpx** - 비동기 HTTP 클라이언트 (테스트용)

---

## 📁 프로젝트 구조

```
life-management-app/
├── app/
│   ├── core/                      # 핵심 설정 및 공통 모듈
│   │   ├── config.py             # 환경 설정 (dev/main 분리)
│   │   ├── database.py           # 데이터베이스 연결 및 세션 관리
│   │   └── timezone.py           # 타임존 처리 (UTC ↔ KST)
│   │
│   ├── models/                    # 데이터베이스 모델
│   │   ├── todo.py               # DailyTodo (메인), Todo (레거시)
│   │   ├── journey.py            # Journey (여정 관리)
│   │   ├── daily_reflection.py   # DailyReflection (일일 회고)
│   │   ├── daily_memo.py         # DailyMemo (일일 메모)
│   │   └── record.py             # ⚠️ DailyRecord (사용하지 않음 - 제거 대상)
│   │
│   ├── routers/                   # API 라우터
│   │   ├── daily.py              # 할일 & 메모 API (메인)
│   │   ├── journeys.py           # 여정 관리 API
│   │   └── reflections.py        # 회고 & LLM 블로그 생성 API
│   │
│   ├── services/                  # 비즈니스 로직 계층
│   │   ├── daily_todo_service.py # 할일 비즈니스 로직
│   │   ├── daily_memo_service.py # 메모 비즈니스 로직
│   │   ├── daily_reflection_service.py # 회고 비즈니스 로직
│   │   ├── journey_service.py    # 여정 비즈니스 로직
│   │   └── llm_blog_service.py   # LLM 블로그 생성 로직
│   │
│   ├── schemas/                   # Pydantic 스키마
│   │   ├── journey.py            # 여정 관련 스키마
│   │   └── llm_blog.py           # LLM 블로그 관련 스키마
│   │
│   ├── templates/                 # Jinja2 템플릿
│   │   ├── base.html             # 기본 레이아웃
│   │   ├── daily_todos.html      # 메인 페이지 (할일 관리)
│   │   ├── journey_detail.html   # 여정 상세 페이지
│   │   ├── project_management.html # 여정 관리 페이지
│   │   ├── reflection_history.html # 회고 히스토리 페이지
│   │   ├── weekly_planning.html  # ⚠️ 사용하지 않음 (제거 대상)
│   │   ├── forms/                # 폼 컴포넌트
│   │   ├── partials/             # 재사용 가능한 부분 템플릿
│   │   └── errors/               # 에러 페이지 (404, 500)
│   │
│   ├── static/                    # 정적 파일
│   │   ├── css/                  # CSS 파일
│   │   ├── js/                   # JavaScript 파일
│   │   └── uploads/              # 업로드된 파일 (회고 이미지 등)
│   │
│   └── main.py                    # FastAPI 앱 + 페이지 라우터
│
├── migrations/                    # Alembic 마이그레이션
│   ├── env.py                    # Alembic 환경 설정
│   └── versions/                 # 마이그레이션 버전 파일
│       ├── 20251011_1202_...py   # 초기 스키마 생성
│       ├── 20251011_1637_...py   # DailyMemo 모델 추가
│       ├── 20251013_1602_...py   # Milestone → Journey 리팩토링
│       └── 20251014_1754_...py   # DailyReflection created_at 업데이트
│
├── tests/                         # 테스트 코드
│   ├── api/                      # API 테스트 (132개)
│   ├── services/                 # 서비스 테스트 (125개)
│   ├── models/                   # 모델 테스트
│   ├── e2e/                      # E2E 테스트 (53개)
│   └── conftest.py               # pytest 설정
│
├── scripts/                       # 유틸리티 스크립트
│   ├── db.py                     # 통합 DB 관리 도구
│   ├── run_dev.sh                # 개발 환경 실행 스크립트
│   └── run_main.sh               # 메인 환경 실행 스크립트
│
├── data/                          # 데이터베이스 파일
│   ├── app_dev.db                # 개발 환경 DB
│   ├── app.db                    # 메인 환경 DB
│   └── backups/                  # 백업 파일들
│
├── docs/                          # 문서
│   ├── PROJECT_STATUS.md         # 현재 상태 문서 (이 파일)
│   ├── API.md                    # API 문서
│   ├── database-migrations.md    # 마이그레이션 가이드
│   ├── retrospectives/           # 회고 문서들
│   └── archive/                  # 아카이브된 문서들
│
├── pyproject.toml                 # 프로젝트 메타데이터 및 의존성
├── uv.lock                        # uv 잠금 파일
├── alembic.ini                    # Alembic 설정
├── .env                           # 환경 변수 (로컬)
├── .env.example                   # 환경 변수 예시
└── README.md                      # 프로젝트 설명서
```

---

## 💾 데이터베이스 설계

### 현재 사용 중인 모델

#### 1. **DailyTodo** (메인 할일 모델)
```python
class DailyTodo(Base):
    """일상 중심의 Todo 모델"""
    __tablename__ = "daily_todos"

    # 기본 정보
    id: int
    title: str
    description: str | None
    notes: str | None
    category: TodoCategory  # 업무, 학습, 건강, 개인, 관계, 기타

    # 완료 관련
    is_completed: bool
    completed_at: datetime | None
    completion_reflection: str | None
    completion_image_path: str | None

    # 날짜 관련
    created_date: date
    created_at: datetime
    scheduled_date: date | None

    # 시간 기록
    estimated_minutes: int | None
    actual_minutes: int | None

    # 미루기 관련
    postpone_count: int
    postpone_history: str | None  # JSON

    # 여정 연결
    journey_id: int | None
```

#### 2. **Journey** (여정 관리)
```python
class Journey(Base):
    """프로젝트 여정 모델 (이전 Milestone에서 리팩토링)"""
    __tablename__ = "journeys"

    id: int
    title: str
    description: str | None
    start_date: date
    end_date: date
    status: JourneyStatus  # 계획중, 진행중, 완료, 일시중지
    progress: float  # DEPRECATED - calculate_actual_progress() 사용 권장
    created_at: datetime
    updated_at: datetime | None

    # 관계
    todos: List[Todo]
    daily_todos: List[DailyTodo]
```

#### 3. **DailyReflection** (일일 회고)
```python
class DailyReflection(Base):
    """일일 회고 모델"""
    __tablename__ = "daily_reflections"

    id: int
    reflection_date: date  # UNIQUE
    reflection_text: str

    # 성과 데이터
    total_todos: int
    completed_todos: int
    completion_rate: float
    todos_snapshot: dict | None  # JSON

    # 감정/만족도
    satisfaction_score: int | None  # 1-5
    energy_level: int | None  # 1-5

    # LLM 블로그 생성
    generated_blog_content: str | None
    blog_generation_prompt: str | None
    blog_generated_at: datetime | None

    created_at: datetime
    updated_at: datetime | None
```

#### 4. **DailyMemo** (일일 메모)
```python
class DailyMemo(Base):
    """일일 메모 모델"""
    __tablename__ = "daily_memos"

    id: int
    memo_date: date
    content: str
    created_at: datetime
    updated_at: datetime | None
```

#### 5. **Todo** (레거시 모델)
```python
class Todo(Base):
    """기존 Todo 모델 (호환성을 위해 유지)"""
    __tablename__ = "todos"

    id: int
    title: str
    description: str | None
    status: TodoStatus  # 할일, 진행중, 완료, 취소
    priority: TodoPriority  # 낮음, 보통, 높음, 긴급
    category: TodoCategory
    is_completed: bool
    completed_at: datetime | None
    created_at: datetime
    estimated_time: int | None
    actual_time: int | None
    journey_id: int | None
```

### ⚠️ 사용하지 않는 모델 (제거 대상)

#### **DailyRecord** (사용하지 않음)
- **파일**: `app/models/record.py`
- **상태**: 정의만 되어있고 실제로 사용되지 않음
- **권장 조치**: 삭제 또는 DailyReflection과 통합 검토

---

## 🌐 API 엔드포인트 구조

### 1. **일상 할일 & 메모 API** (`/api/daily`)

#### 할일 관련
- `GET /api/daily/todos/today` - 오늘의 할일 목록
- `POST /api/daily/todos` - 상세 할일 생성
- `POST /api/daily/todos/quick` - 빠른 할일 생성
- `GET /api/daily/todos/{id}` - 할일 상세 조회
- `PUT /api/daily/todos/{id}` - 할일 수정
- `DELETE /api/daily/todos/{id}` - 할일 삭제
- `PATCH /api/daily/todos/{id}/toggle` - 완료/미완료 토글
- `PATCH /api/daily/todos/{id}/complete` - 회고와 함께 완료
- `PATCH /api/daily/todos/{id}/reflection` - 완료 회고 수정 (이미지 포함)
- `PATCH /api/daily/todos/{id}/reschedule` - 미루기 (일정 재조정)
- `GET /api/daily/todos/{id}/postpone-summary` - 미루기 요약 정보

#### 요약 정보
- `GET /api/daily/summary/today` - 오늘의 요약
- `GET /api/daily/summary/weekly` - 주간 요약
- `GET /api/daily/summary/categories` - 카테고리별 요약
- `GET /api/daily/reflection-summary` - 회고 작성용 요약

#### 여정 연결
- `GET /api/daily/journeys` - 할일 추가 시 선택 가능한 여정 목록

#### 메모 관련
- `GET /api/daily/memos/today` - 오늘의 메모 목록
- `GET /api/daily/memos/date/{date}` - 특정 날짜 메모 목록
- `GET /api/daily/memos/recent` - 최근 메모 목록
- `GET /api/daily/memos/search` - 키워드 검색
- `GET /api/daily/memos/{id}` - 메모 상세 조회
- `GET /api/daily/memos/count/{date}` - 특정 날짜 메모 개수
- `POST /api/daily/memos` - 메모 생성
- `POST /api/daily/memos/quick` - 빠른 메모 생성 (오늘 날짜)
- `PUT /api/daily/memos/{id}` - 메모 수정
- `DELETE /api/daily/memos/{id}` - 메모 삭제
- `DELETE /api/daily/memos/bulk` - 메모 일괄 삭제

### 2. **여정 관리 API** (`/api/journeys`)

- `GET /api/journeys/` - 모든 여정 목록
- `GET /api/journeys/new` - 새 여정 생성 폼 (HTMX)
- `GET /api/journeys/{id}` - 여정 상세 조회
- `GET /api/journeys/{id}/edit` - 여정 편집 폼 (HTMX)
- `POST /api/journeys/` - 여정 생성
- `POST /api/journeys/{id}/edit` - 여정 수정 (HTMX Form)
- `PUT /api/journeys/{id}` - 여정 수정 (JSON)
- `PUT /api/journeys/{id}/complete` - 여정 완료 처리
- `DELETE /api/journeys/{id}` - 여정 삭제

### 3. **회고 시스템 API** (`/api/reflections`)

#### 회고 기본
- `POST /api/reflections/` - 회고 생성
- `GET /api/reflections/date/{date}` - 특정 날짜 회고 조회
- `GET /api/reflections/recent` - 최근 회고 목록
- `GET /api/reflections/stats` - 회고 통계
- `DELETE /api/reflections/date/{date}` - 회고 삭제

#### LLM 블로그 생성
- `POST /api/reflections/{id}/generate-blog` - 블로그 글 생성
- `POST /api/reflections/{id}/regenerate-blog` - 블로그 글 재생성
- `GET /api/reflections/{id}/blog-content` - 저장된 블로그 콘텐츠 조회

### 4. **페이지 라우터** (메인)

- `GET /` - 메인 페이지 (오늘의 할일)
- `GET /journeys` - 여정 관리 페이지
- `GET /journeys/{id}` - 여정 상세 페이지
- `GET /reflection-history` - 회고 히스토리 페이지
- `GET /api/reflection-day/{date}` - 특정 날짜 회고 상세 (아코디언)
- `GET /api/search` - 실시간 검색 (HTMX)
- `GET /health` - 헬스 체크

#### 리다이렉트 (레거시 URL 호환성)
- `GET /dashboard` → `/journeys` (301)
- `GET /projects` → `/journeys` (301)
- `GET /todos` → `/journeys` (301)
- `GET /weekly` → `/reflection-history` (301)
- `GET /reflections` → `/reflection-history` (301)

---

## 🎨 프론트엔드 구조

### 템플릿 구성

#### 현재 사용 중
- **base.html** - 기본 레이아웃, 네비게이션, 공통 스타일
- **daily_todos.html** - 메인 페이지 (할일 관리, 메모, 빠른 입력)
- **journey_detail.html** - 여정 상세 (할일 목록, 진행률)
- **project_management.html** - 여정 관리 (전체 여정 목록, 통계)
- **reflection_history.html** - 회고 히스토리 (주간 통계, 아코디언 UI)
- **forms/** - 폼 컴포넌트 (여정 생성/편집)
- **partials/** - 재사용 가능한 부분 템플릿 (네비게이션, 검색 결과)
- **errors/** - 에러 페이지 (404, 500)

#### ⚠️ 사용하지 않는 템플릿 (제거 대상)
- **weekly_planning.html** - 코드에서 사용되지 않음

### 주요 UI 기능

1. **환경 구분 표시**
   - 개발 환경: 노란색-주황색 배너 표시
   - 포트 번호 및 DB 파일명 표시
   - 브라우저 탭에 `[DEV]` 접두사

2. **모달 기반 인터랙션**
   - 할일 추가/수정 모달
   - 여정 생성/편집 모달
   - 회고 작성 모달

3. **실시간 업데이트**
   - 완료 개수 실시간 반영
   - 진행률 자동 계산
   - 검색 결과 실시간 표시

4. **반응형 디자인**
   - 모바일 친화적 UI
   - 터치 최적화
   - Tailwind CSS 유틸리티 클래스

---

## 🧪 테스트 현황

### 테스트 커버리지
- **총 테스트 개수**: 310개
- **통과율**: 100% ✅
- **서비스 테스트**: 125개 (91% 커버리지)
- **API 테스트**: 132개 (70% 커버리지)
- **E2E 테스트**: 53개

### 테스트 구조
```
tests/
├── api/                          # API 엔드포인트 테스트
│   ├── test_daily_api.py
│   ├── test_daily_progress_api.py
│   ├── test_journeys_api.py
│   ├── test_llm_blog_api.py
│   ├── test_reflections_api.py
│   └── test_timezone_api_responses.py
│
├── services/                     # 비즈니스 로직 테스트
│   ├── test_daily_todo_service.py
│   ├── test_daily_memo_service.py
│   ├── test_daily_reflection_service.py
│   ├── test_journey_service.py
│   ├── test_auto_rollover_system.py
│   ├── test_daily_todo_postpone.py
│   └── test_today_progress_accuracy.py
│
├── models/                       # 모델 테스트
│   ├── test_todo.py
│   ├── test_journey.py
│   ├── test_daily_memo.py
│   └── test_daily_reflection_llm.py
│
├── e2e/                          # E2E 워크플로우 테스트
│   ├── test_basic_navigation.py
│   ├── test_journey_workflow.py
│   ├── test_reflection_system.py
│   └── test_todo_workflow.py
│
└── conftest.py                   # pytest 설정 및 fixture
```

### 테스트 실행 방법
```bash
# 서비스 로직 테스트 (빠른 피드백)
uv run pytest tests/services/ -v

# API 및 모델 테스트
uv run pytest tests/api/ tests/models/ -v

# E2E 테스트
uv run pytest tests/e2e/ -v

# 전체 테스트
uv run pytest -v

# 커버리지 포함
uv run pytest tests/services/ --cov=app --cov-report=html
```

### 주의사항
- LLM 테스트는 이벤트 루프 충돌 방지를 위해 별도 실행 권장
- FastAPI TestClient와 pytest-asyncio 간 충돌 가능성 있음

---

## 🔧 환경 설정

### 환경 변수
```bash
# .env 파일 예시
APP_ENV=dev                      # dev 또는 main
TIMEZONE=Asia/Seoul              # pytz 형식
DEBUG=True                       # 디버그 모드
DATABASE_URL=                    # (선택) 명시적 DB URL 지정

# APP_ENV에 따른 자동 DB 설정:
# - dev   → sqlite:///./data/app_dev.db
# - main  → sqlite:///./data/app.db
```

### 환경별 실행 방법

#### 개발 환경 (포트 8000)
```bash
# 스크립트 사용
./scripts/run_dev.sh

# 또는 직접 실행
APP_ENV=dev uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 메인 환경 (포트 8001)
```bash
# 스크립트 사용
./scripts/run_main.sh

# 또는 직접 실행
APP_ENV=main uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
```

---

## 💿 데이터베이스 관리

### 통합 DB 관리 도구 (`scripts/db.py`)

```bash
# 환경별 초기화
python scripts/db.py --env dev init
python scripts/db.py --env main init

# 마이그레이션 상태 확인
python scripts/db.py --env dev migrate-status
python scripts/db.py --env main migrate-status

# 새 마이그레이션 생성 (개발 환경)
python scripts/db.py --env dev migrate-new "Add new feature"

# 마이그레이션 적용
python scripts/db.py --env dev migrate-up
python scripts/db.py --env main migrate-up

# 마이그레이션 롤백
python scripts/db.py --env dev migrate-down
python scripts/db.py --env main migrate-down

# 백업
python scripts/db.py --env dev backup
python scripts/db.py --env main backup

# 복원
python scripts/db.py --env dev restore <backup_file>
python scripts/db.py --env main restore <backup_file>
```

### 권장 워크플로우
1. **개발 환경에서 먼저 테스트** (`--env dev`)
   - 스키마 변경 시 개발 DB에서 마이그레이션 생성 및 적용
   - 개발 서버로 충분히 테스트
2. **검증 후 메인 환경에 적용** (`--env main`)
   - 메인 DB 변경 전 **반드시 백업!**
   - 마이그레이션 적용 후 메인 서버로 동작 확인
3. **롤백 계획 수립**
   - 중요한 변경 전에는 롤백 방법 미리 준비

---

## ⚠️ 정리가 필요한 항목

### 1. 사용하지 않는 모델
- **파일**: `app/models/record.py`
- **모델**: `DailyRecord`, `EnergyLevel`
- **문제**: 정의만 되어있고 실제로 사용되지 않음
- **권장 조치**:
  - 삭제 (사용 계획 없는 경우)
  - 또는 `DailyReflection`과 통합 검토

### 2. 사용하지 않는 템플릿
- **파일**: `app/templates/weekly_planning.html`
- **문제**: 코드에서 참조되지 않음
- **권장 조치**: 삭제 또는 아카이브

### 3. Deprecated 필드
- **위치**: `Journey.progress`
- **문제**: `DEPRECATED` 주석 있음, `calculate_actual_progress()` 메서드 사용 권장
- **권장 조치**:
  - 향후 버전에서 제거 계획
  - 현재는 하위 호환성을 위해 유지

### 4. 레거시 모델
- **모델**: `Todo` 테이블
- **상태**: `DailyTodo`로 대체되었지만 호환성을 위해 유지
- **권장 조치**:
  - 장기적으로 `DailyTodo`로 완전 마이그레이션 고려
  - 현재는 기존 데이터 유지를 위해 보존

---

## 📊 주요 기능 현황

### ✅ 구현 완료
- [x] 일상 할일 관리 (DailyTodo)
- [x] 빠른 할일 추가
- [x] 할일 완료 시 회고 작성 (이미지 포함)
- [x] **작업완료 회고 수정 기능** (NEW - Issue #1)
- [x] **하루 마감 회고 수정 기능** (NEW - Issue #2)
- [x] 미루기 기능 (사유 포함)
- [x] 여정 연결 및 관리
- [x] 일일 메모 시스템
- [x] 일일 회고 시스템
- [x] 과거 날짜 회고 작성 기능
- [x] LLM 블로그 글 생성 (OpenAI, Claude)
- [x] 주간 회고 히스토리
- [x] 실시간 검색
- [x] 환경 분리 (dev/main)
- [x] 데이터베이스 마이그레이션 시스템
- [x] 타임존 처리 (UTC ↔ KST)
- [x] 개수 기반 진행률 표시
- [x] 자동 이월 시스템

### 🔄 개선 중
- [ ] UI/UX 최적화
- [ ] 성능 개선
- [ ] 테스트 커버리지 향상

### 📋 향후 계획
- [ ] 주간/월간 뷰 추가
- [ ] 통계 대시보드 구현
- [ ] 알림 시스템
- [ ] 데이터 내보내기
- [ ] PWA 지원 (오프라인 사용)
- [ ] 다크모드 테마
- [ ] 키보드 단축키
- [ ] 드래그앤드롭 UI

---

## 🐛 알려진 이슈

### 1. 이벤트 루프 충돌
- **문제**: FastAPI TestClient와 pytest-asyncio 간 이벤트 루프 충돌
- **영향**: LLM 테스트 실행 시
- **해결방법**: 테스트 분리 실행 (`pytest -k "not llm"`)

### 2. 정적 파일 경로
- **문제**: 업로드된 이미지 경로 처리
- **상태**: 현재 `/static/uploads/` 사용 중, 별도 스토리지 고려 필요

---

## 📈 프로젝트 통계

### 코드 규모
- **Python 파일**: ~40개
- **총 코드 라인**: ~15,000 라인
- **템플릿 파일**: 12개
- **API 엔드포인트**: 50+ 개

### 의존성
- **프로덕션 의존성**: 15개
- **개발 의존성**: 10개

### 데이터베이스
- **테이블**: 5개 (실사용 4개)
- **마이그레이션**: 4개 버전

---

## 📝 최근 주요 변경사항

### 2025-10-22: 하루 마감 회고 수정 기능 구현 (Issue #2)
- 오늘의 할 일 페이지에서 "하루 마감" 모달 열 때 기존 회고 자동 로드
- 회고 텍스트, 만족도, 에너지 레벨 자동 채우기
- 수정 모드와 신규 작성 모드 UI 구분
- 백엔드 변경 없이 프론트엔드만 개선 (JavaScript 40줄 추가)

### 2025-10-22: 작업완료 회고 수정 기능 구현 (Issue #1)
- 완료된 할 일의 회고 내용 수정 기능 추가
- 회고 이미지 추가/변경/삭제 지원
- API 엔드포인트 추가: `PATCH /api/daily/todos/{id}/reflection`
- E2E 테스트 수정 (Playwright strict mode violation 해결)

### 2025-10-17: 과거 날짜 회고 작성 기능 추가
- 회고 히스토리 페이지에서 과거 날짜 회고 작성 가능
- 회고 작성 모달 UI 추가 (날짜, 내용, 만족도, 에너지 레벨)
- 회고가 없는 날짜의 아코디언에 "📝 회고 작성하기" 버튼 추가
- 백엔드 변경 없이 기존 API 재사용

### 2025-10-15: 듀얼 데이터베이스 환경 시스템
- 개발(dev)과 메인(main) 환경 분리
- 환경별 데이터베이스 자동 설정
- 시각적 환경 구분 배너 추가

### 2025-10-14: 진행률 표시 방식 변경
- 프로그레스바에서 개수 기반 표시로 변경
- "완료 3/10" 형식으로 명확한 피드백

### 2025-10-13: Milestone → Journey 리팩토링
- 용어 통일 (마일스톤 → 여정)
- 모든 문서 및 코드 업데이트

### 2025-10-11: 데이터베이스 마이그레이션 시스템 구축
- Alembic 기반 마이그레이션 시스템
- 통합 DB 관리 스크립트 (`scripts/db.py`)

---

## 🔗 관련 문서

- [README.md](../README.md) - 프로젝트 설명 및 빠른 시작 가이드
- [API.md](./API.md) - API 상세 문서
- [database-migrations.md](./database-migrations.md) - 마이그레이션 가이드
- [CLAUDE.md](../../CLAUDE.md) - 개발 가이드라인

---

## 📞 문의 및 지원

프로젝트 관련 문의사항이나 이슈는 다음을 통해 연락주세요:

- **GitHub Issues**: (저장소 설정 시)
- **문서 업데이트**: 이 파일을 직접 수정하여 PR 제출

---

*이 문서는 프로젝트 진행에 따라 지속적으로 업데이트됩니다.*
