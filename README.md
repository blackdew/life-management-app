# ⚡ Daily Flow - 일상 흐름 관리

**매일의 작은 성취들을 관리하며 하루를 개선해가는 일상 관리 도구**

> *"개인의 하루에 집중하여 작업을 관리하고 회고하며 하루를 개선해가는 실용적인 웹 애플리케이션*

## 🎯 **주요 특징**

### ✨ **핵심 기능들**
- **🎮 통합 할 일 관리**: 모든 여정의 오늘 할 일을 한눈에
- **📝 데일리 메모**: 하루 종일 떠오르는 생각과 아이디어 기록
- **💭 회고 시스템**: 완료 시 배움과 성과 기록
- **📅 미루기 기능**: 유연한 일정 재조정
- **🎯 여정 연결**: 목표 지향적 할 일 관리
- **📊 실시간 완료 현황**: 개수 기반 피드백과 동기부여
- **🤖 AI 블로그 생성**: LLM을 활용한 자동 블로그 포스트 생성

## 🚀 **빠른 시작**

### **환경 설정**
환경변수를 통해 애플리케이션의 동작을 설정할 수 있습니다.

**Mac / Linux:**
```bash
# .env 파일 생성 및 설정 (선택사항)
echo "APP_ENV=dev" > .env
echo "TIMEZONE=Asia/Seoul" >> .env
echo "DEBUG=True" >> .env
```

**Windows (PowerShell):**
```powershell
# .env 파일 생성 및 설정 (선택사항)
"APP_ENV=dev" | Out-File -FilePath .env -Encoding UTF8
"TIMEZONE=Asia/Seoul" | Out-File -FilePath .env -Append -Encoding UTF8
"DEBUG=True" | Out-File -FilePath .env -Append -Encoding UTF8
```

**Windows (CMD):**
```cmd
REM .env 파일 생성 및 설정 (선택사항)
echo APP_ENV=dev > .env
echo TIMEZONE=Asia/Seoul >> .env
echo DEBUG=True >> .env
```

또는 `.env.example` 파일을 `.env`로 복사하여 사용하세요:
```bash
# 모든 OS 공통
cp .env.example .env   # Mac/Linux
copy .env.example .env  # Windows
```

### **설치**
```bash
# 의존성 설치
uv sync

# 데이터베이스 초기화 (개발 환경)
python scripts/db.py --env dev init
```

### **실행**

#### **크로스 플랫폼 실행 (권장 ⭐)**
모든 OS에서 동일하게 사용 가능한 Python 스크립트:
```bash
# 개발 환경 실행
python run.py dev

# 메인 환경 실행
python run.py main

# 웹 브라우저에서 접속
# 개발: http://localhost:8000
# 메인: http://localhost:8001
```

#### **OS별 실행 스크립트**

**Mac / Linux:**
```bash
# 개발 환경
./scripts/run_dev.sh

# 메인 환경
./scripts/run_main.sh
```

**Windows (PowerShell):**
```powershell
# 개발 환경
.\scripts\run_dev.ps1

# 메인 환경
.\scripts\run_main.ps1
```

**Windows (CMD):**
```cmd
# 개발 환경
scripts\run_dev.bat

# 메인 환경
scripts\run_main.bat
```

#### **수동 실행 (고급)**

**Mac / Linux:**
```bash
# 개발 환경
APP_ENV=dev uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 메인 환경
APP_ENV=main uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**Windows (PowerShell):**
```powershell
# 개발 환경
$env:APP_ENV="dev"; uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 메인 환경
$env:APP_ENV="main"; uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**Windows (CMD):**
```cmd
# 개발 환경
set APP_ENV=dev && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 메인 환경
set APP_ENV=main && uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
```

#### **환경 구분**
프로젝트는 개발(dev)과 메인(main) 환경을 분리하여 관리합니다:

| 환경 | 데이터베이스 | 포트 | 시각적 표시 | 용도 |
|------|-------------|------|------------|------|
| **개발(dev)** | `data/app_dev.db` | 8000 | 노란색 배너 | 실험 및 테스트 |
| **메인(main)** | `data/app.db` | 8001 | 배너 없음 | 실제 운영 데이터 |

### **상태 확인**
```bash
# 서버 헬스 체크
curl http://localhost:8000/health

# 오늘의 할 일 확인
curl http://localhost:8000/api/daily/todos/today

# 여정 목록 확인
curl http://localhost:8000/api/daily/journeys
```

## 📱 **사용법**

### **기본 워크플로우**
1. **할 일 추가**: 빠른 입력 또는 상세 입력 선택
2. **여정 연결**: 드롭다운에서 관련 여정 선택
3. **진행 확인**: 실시간 완료 현황과 할일 개수 확인
4. **완료 & 회고**: 할 일 완료 시 배움과 성과 기록
5. **미루기**: 필요시 다른 날짜로 일정 조정

### **주요 UI 요소**
- **⚙️ 버튼**: 상세 입력 폼 토글
- **🎯 태그**: 연결된 여정 표시
- **🏷️ 태그**: 카테고리 구분
- **⏱️ 태그**: 예상 소요시간
- **✏️ 버튼**: 할 일 편집
- **📅 버튼**: 미루기 (일정 변경)

## 🛠️ **기술 스택**

### **백엔드**
- **FastAPI**: 고성능 Python 웹 프레임워크
- **SQLAlchemy**: ORM 및 데이터베이스 관리
- **SQLite**: 로컬 데이터베이스
- **Pydantic**: 데이터 검증 및 직렬화

### **프론트엔드**
- **Jinja2**: 서버사이드 템플릿 엔진
- **Tailwind CSS**: 유틸리티 기반 CSS 프레임워크
- **Vanilla JavaScript**: 경량 클라이언트 로직
- **모달 기반 UI**: 깔끔한 사용자 경험

## 📂 **프로젝트 구조**

```
life-management-app/
├── app/
│   ├── main.py                    # FastAPI 앱 + 페이지 라우터
│   ├── models/
│   │   ├── todo.py               # DailyTodo 모델
│   │   └── journey.py            # Journey 모델
│   ├── services/
│   │   └── daily_todo_service.py # 비즈니스 로직
│   ├── routers/
│   │   └── daily.py              # API 엔드포인트
│   ├── templates/
│   │   ├── base.html             # 기본 레이아웃
│   │   └── daily_todos.html      # 메인 페이지
│   └── static/                   # CSS, JS 파일
├── scripts/
│   └── db.py                    # 통합 데이터베이스 관리
├── data/
│   └── app.db                   # SQLite 데이터베이스
└── docs/
    └── diagrams/                # 설계 문서
```

## 🔌 **API 엔드포인트**

### **할 일 관리**
```bash
# 빠른 할 일 추가
POST /api/daily/todos/quick
Content-Type: application/x-www-form-urlencoded
Body: title=할일제목

# 상세 할 일 추가
POST /api/daily/todos
Content-Type: application/x-www-form-urlencoded
Body: title=할일제목&description=상세내용&journey_id=1&estimated_minutes=60

# 회고와 함께 완료
PATCH /api/daily/todos/{id}/complete
Body: reflection=오늘배운점과성과

# 미루기 (일정 재조정)
PATCH /api/daily/todos/{id}/reschedule
Body: new_date=2024-09-29

# 할 일 수정
PUT /api/daily/todos/{id}
Body: title=수정된제목&description=수정된내용

# 할 일 삭제
DELETE /api/daily/todos/{id}
```

### **조회 API**
```bash
# 오늘의 할 일 목록
GET /api/daily/todos/today

# 오늘의 요약 정보
GET /api/daily/summary/today

# 여정 목록 (할 일 추가용)
GET /api/daily/journeys
```

### **데일리 메모 관리**
```bash
# 빠른 메모 추가
POST /api/daily/memos/quick
Content-Type: application/x-www-form-urlencoded
Body: content=메모내용

# 오늘의 메모 목록
GET /api/daily/memos/today

# 최근 메모 조회
GET /api/daily/memos/recent?limit=10

# 메모 검색
GET /api/daily/memos/search?keyword=키워드

# 특정 날짜 메모 조회
GET /api/daily/memos/date/2024-09-29

# 메모 수정
PUT /api/daily/memos/{id}
Body: content=수정된메모내용

# 메모 삭제
DELETE /api/daily/memos/{id}

# 메모 일괄 삭제
DELETE /api/daily/memos/bulk
Body: memo_ids=[1,2,3]
```

## 🎨 **디자인 철학**

### **사용자 경험 원칙**
- **직관성**: 설명 없이도 이해할 수 있는 UI
- **반응성**: 즉시 피드백과 시각적 변화
- **일관성**: 전체 인터페이스의 통일감
- **접근성**: 모바일 친화적 터치 인터페이스
- **의미성**: 단순한 TODO가 아닌 성장 도구

### **색상 체계**
- **보라색** (🎯): 여정 연결
- **파란색** (🏷️): 카테고리 구분
- **회색** (⏱️): 시간 정보
- **녹색**: 완료 상태 및 회고
- **노란색**: 미루기 액션

## 🗃️ **데이터베이스 관리**

### **통합 DB 관리 도구**
모든 데이터베이스 작업이 `scripts/db.py`로 통합되었습니다. **환경별로 분리 관리**되므로 `--env` 옵션을 반드시 지정하세요:

```bash
# 개발 DB 초기화
python scripts/db.py --env dev init

# 메인 DB 초기화
python scripts/db.py --env main init

# 개발 DB 마이그레이션 상태 확인
python scripts/db.py --env dev migrate-status

# 메인 DB 마이그레이션 상태 확인
python scripts/db.py --env main migrate-status

# 개발 DB에 새 마이그레이션 생성
python scripts/db.py --env dev migrate-new "Add new feature"

# 개발 DB에 마이그레이션 적용
python scripts/db.py --env dev migrate-up

# 검증 후 메인 DB에 마이그레이션 적용
python scripts/db.py --env main migrate-up

# 마이그레이션 롤백 (환경별)
python scripts/db.py --env dev migrate-down
python scripts/db.py --env main migrate-down

# 백업 생성 (환경별)
python scripts/db.py --env dev backup
python scripts/db.py --env main backup

# 백업 복원 (환경별)
python scripts/db.py --env dev restore <backup_file>
python scripts/db.py --env main restore <backup_file>

# 전체 도움말
python scripts/db.py --help
```

### **권장 워크플로우**
1. **개발 환경에서 먼저 테스트** (`--env dev`)
   - 스키마 변경 시 개발 DB에서 먼저 마이그레이션 생성 및 적용
   - 개발 서버로 충분히 테스트
2. **충분히 검증 후 메인 환경에 적용** (`--env main`)
   - 메인 DB 변경 전 **반드시 백업!**
   - 마이그레이션 적용 후 메인 서버로 동작 확인
3. **롤백 계획 수립**
   - 중요한 변경 전에는 롤백 방법 미리 준비

자세한 내용은 [데이터베이스 마이그레이션 가이드](docs/database-migrations.md)를 참고하세요.

## 🧪 **테스트**

### **크로스 플랫폼 테스트 (권장 ⭐)**
모든 OS에서 동일하게 사용:
```bash
# 통합 테스트 스크립트 실행
python run.py test
```

### **OS별 테스트 스크립트**

**Mac / Linux:**
```bash
# 분리 실행 스크립트
./tests/test-services.sh
```

**Windows (PowerShell):**
```powershell
# 분리 실행 스크립트
.\tests\test-services.ps1
```

**Windows (CMD):**
```cmd
REM 분리 실행 스크립트
tests\test-services.bat
```

### **수동 테스트 실행 (모든 OS 공통)**
FastAPI TestClient와 pytest-asyncio 간 이벤트 루프 충돌을 방지하기 위해 분리 실행을 권장합니다:

```bash
# 일상 개발: 서비스 로직 테스트 (빠른 피드백)
uv run pytest tests/services/ -v

# 통합 검증: API 및 모델 테스트
uv run pytest tests/api/ tests/routers/ tests/models/ -v

# 커버리지 포함 테스트 (분리 실행)
uv run pytest tests/services/ --cov=app --cov-report=html
uv run pytest tests/api/ tests/routers/ tests/models/ --cov=app --cov-append --cov-report=html
```

### **테스트 현황**
- **서비스 테스트**: ✅ 125/125 통과 (91% 커버리지)
- **API 테스트**: ✅ 132/132 통과 (70% 커버리지)
- **E2E 테스트**: ✅ 53/53 통과
- **총 310개 테스트 모두 100% 통과** ✅

### **async 관련 주의사항**
LLM 테스트는 FastAPI TestClient와 pytest-asyncio 간 이벤트 루프 충돌을 피하기 위해 별도 실행이 필요합니다:

```bash
# LLM 테스트 제외하고 실행 (일상적인 테스트)
uv run pytest -v -k "not llm"

# LLM 테스트만 별도 실행 (필요시)
uv run pytest tests/models/test_daily_reflection_llm.py -v
```

## 📈 **로드맵**

### **즉시 가능한 개선사항**
- [ ] 주간/월간 뷰 추가
- [ ] 통계 대시보드 구현
- [ ] 검색 및 필터링 기능
- [ ] 알림 시스템
- [ ] 데이터 내보내기

### **장기 계획**
- [ ] PWA 지원 (오프라인 사용)
- [ ] 다크모드 테마
- [ ] 키보드 단축키
- [ ] 드래그앤드롭 UI
- [ ] 협업 기능

## ⚙️ **환경 설정**

### **지원되는 환경변수**
애플리케이션의 동작을 `.env` 파일이나 시스템 환경변수로 설정할 수 있습니다:

| 환경변수 | 기본값 | 설명 |
|----------|--------|------|
| `APP_ENV` | `dev` | 애플리케이션 환경 (`dev` 또는 `main`) |
| `TIMEZONE` | `Asia/Seoul` | 시간 표시용 타임존 (pytz 형식) |
| `DEBUG` | `True` | 디버그 모드 활성화 |
| `DATABASE_URL` | *(환경별 자동)* | 데이터베이스 연결 URL (명시적 지정 가능) |
| `APP_NAME` | `"Daily Flow"` | 애플리케이션 이름 |

**참고**: `DATABASE_URL`을 명시적으로 지정하지 않으면 `APP_ENV`에 따라 자동 설정됩니다:
- `dev` → `sqlite:///./data/app_dev.db`
- `main` → `sqlite:///./data/app.db`

### **타임존 설정**
애플리케이션은 데이터베이스에 UTC 시간으로 저장하고, 사용자에게는 설정된 타임존으로 표시합니다:

```bash
# 한국 시간 (기본값)
TIMEZONE=Asia/Seoul

# 다른 타임존 예시
TIMEZONE=America/New_York
TIMEZONE=Europe/London
TIMEZONE=Asia/Tokyo
```

이 설계를 통해 같은 데이터가 다른 시간대에서도 올바르게 표시됩니다.

### **.env 파일 예시**
```bash
TIMEZONE=Asia/Seoul
DEBUG=True
DATABASE_URL=sqlite:///./data/app.db
APP_NAME="나의 일상 관리"
```

## 🤝 **기여하기**

### **개발 환경 설정**
```bash
# 저장소 클론
git clone [repository-url]
cd life-management-app

# 개발 의존성 설치
uv sync --dev

# 개발 서버 시작
uv run uvicorn app.main:app --reload
```

### **코딩 스타일**
- **Python**: Black + isort + mypy
- **HTML/CSS**: Prettier
- **JavaScript**: ESLint
- **커밋 메시지**: Conventional Commits

## 📄 **라이선스**

MIT License - 자유롭게 사용, 수정, 배포 가능

---

## 🎯 **시작하기**

### **모든 OS 공통 (권장 ⭐)**
```bash
# 1. 의존성 설치
uv sync

# 2. 데이터베이스 초기화 (개발 환경)
python scripts/db.py --env dev init

# 3. 개발 서버 시작 (크로스 플랫폼)
python run.py dev

# 4. 브라우저에서 http://localhost:8000 접속
```

### **Mac / Linux**
```bash
# 1. 의존성 설치
uv sync

# 2. 데이터베이스 초기화
python scripts/db.py --env dev init

# 3. 개발 서버 시작
./scripts/run_dev.sh

# 4. 브라우저에서 http://localhost:8000 접속
```

### **Windows (PowerShell)**
```powershell
# 1. 의존성 설치
uv sync

# 2. 데이터베이스 초기화
python scripts/db.py --env dev init

# 3. 개발 서버 시작
.\scripts\run_dev.ps1

# 4. 브라우저에서 http://localhost:8000 접속
```

### **Windows (CMD)**
```cmd
REM 1. 의존성 설치
uv sync

REM 2. 데이터베이스 초기화
python scripts/db.py --env dev init

REM 3. 개발 서버 시작
scripts\run_dev.bat

REM 4. 브라우저에서 http://localhost:8000 접속
```

---

*"Daily Flow와 함께 만족하는 일상을 만들어보세요!"* 🚀✨❤️