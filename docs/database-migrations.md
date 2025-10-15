# 🗃️ 데이터베이스 마이그레이션 가이드

## 📋 개요

이 프로젝트는 Alembic을 사용하여 데이터베이스 스키마 변경을 체계적으로 관리합니다. 모든 데이터베이스 스키마 변경은 마이그레이션을 통해 버전 관리되며, 롤백과 업그레이드가 가능합니다.

## 🚀 빠른 시작

### 통합 DB 관리 명령어

모든 데이터베이스 관리 작업이 `scripts/db.py`로 통합되었습니다:

### 마이그레이션 상태 확인
```bash
# 현재 마이그레이션 상태 확인
python scripts/db.py migrate-status

# 상세 정보 포함
python scripts/db.py migrate-status --verbose --history
```

### 새로운 마이그레이션 생성
```bash
# 모델 변경 후 자동 마이그레이션 생성
python scripts/db.py migrate-new "Add user profile table"

# 또는 직접 alembic 명령 사용
uv run alembic revision --autogenerate -m "Add user profile table"
```

### 마이그레이션 적용
```bash
# 모든 미적용 마이그레이션 적용
python scripts/db.py migrate-up

# 특정 리비전으로 마이그레이션
python scripts/db.py migrate-up --revision abc123
```

### 마이그레이션 롤백
```bash
# 이전 버전으로 롤백
python scripts/db.py migrate-down

# 2단계 이전으로 롤백
python scripts/db.py migrate-down --steps 2

# 특정 리비전으로 롤백
python scripts/db.py migrate-down --revision abc123

# 롤백 계획만 확인 (실제 실행 안함)
python scripts/db.py migrate-down --dry-run
```

## 📝 상세 가이드

### 1. 새로운 모델 추가 워크플로우

1. **모델 정의**
   ```python
   # app/models/new_model.py
   from sqlalchemy import Column, Integer, String, DateTime
   from app.core.database import Base
   from app.core.timezone import get_current_utc_datetime

   class NewModel(Base):
       __tablename__ = "new_models"

       id = Column(Integer, primary_key=True)
       name = Column(String(100), nullable=False)
       # 타임존 처리: UTC로 저장, 애플리케이션 레벨에서 시간 생성
       created_at = Column(DateTime, nullable=False, comment="생성 시간")

       def __init__(self, **kwargs):
           if 'created_at' not in kwargs:
               kwargs['created_at'] = get_current_utc_datetime()
           super().__init__(**kwargs)
   ```

2. **모델 등록**
   ```python
   # migrations/env.py에 import 추가
   from app.models.new_model import NewModel
   ```

3. **마이그레이션 생성**
   ```bash
   python scripts/db.py migrate-new "Add NewModel table"
   ```

4. **마이그레이션 검토 및 적용**
   ```bash
   # 생성된 마이그레이션 파일 검토 후
   python scripts/db.py migrate-up
   ```

### 2. 기존 모델 수정 워크플로우

1. **모델 수정**
   ```python
   # 예: 새 컬럼 추가
   class ExistingModel(Base):
       # ... 기존 컬럼들
       new_column = Column(String(50), nullable=True)  # 추가된 컬럼
   ```

2. **마이그레이션 생성**
   ```bash
   python scripts/db.py migrate-new "Add new_column to ExistingModel"
   ```

3. **마이그레이션 파일 확인**
   - `migrations/versions/` 디렉토리의 새 파일 확인
   - `upgrade()` 함수와 `downgrade()` 함수 검토
   - 필요시 데이터 변환 로직 추가

4. **마이그레이션 적용**
   ```bash
   python scripts/db.py migrate-up
   ```

### 3. 데이터 마이그레이션

복잡한 데이터 변환이 필요한 경우:

```python
# 마이그레이션 파일에서
def upgrade() -> None:
    # 스키마 변경
    op.add_column('users', sa.Column('full_name', sa.String(200)))

    # 데이터 변환
    connection = op.get_bind()
    connection.execute("""
        UPDATE users
        SET full_name = first_name || ' ' || last_name
        WHERE first_name IS NOT NULL AND last_name IS NOT NULL
    """)

def downgrade() -> None:
    op.drop_column('users', 'full_name')
```

## ⏰ 타임존 처리 가이드라인

### 타임존 설계 원칙

이 프로젝트는 다음과 같은 타임존 처리 원칙을 따릅니다:

1. **데이터베이스 저장**: 모든 datetime은 UTC로 저장 (timezone-naive)
2. **사용자 표시**: 환경변수 `TIMEZONE`에 따라 로컬 시간으로 변환하여 표시
3. **국제화 지원**: 동일한 데이터가 다른 시간대에서도 올바르게 표시

### DateTime 컬럼 정의 가이드라인

```python
from sqlalchemy import Column, DateTime
from app.core.timezone import get_current_utc_datetime

class MyModel(Base):
    # ✅ 올바른 방법: 애플리케이션 레벨에서 UTC 시간 생성
    created_at = Column(DateTime, nullable=False, comment="생성 시간")
    updated_at = Column(DateTime, nullable=True, comment="수정 시간")

    def __init__(self, **kwargs):
        if 'created_at' not in kwargs:
            kwargs['created_at'] = get_current_utc_datetime()
        super().__init__(**kwargs)

# ❌ 피해야 할 방법: 데이터베이스 레벨 기본값 사용
# created_at = Column(DateTime, server_default=func.now())  # SQLite는 UTC 사용
# created_at = Column(DateTime, default=datetime.now)       # 서버 로컬 시간 사용
```

### 기존 모델 타임존 적용 마이그레이션

기존 모델에 타임존 처리를 적용할 때의 마이그레이션 예시:

```python
"""Remove server_default from datetime columns for timezone handling

Revision ID: timezone_migration
Revises: previous_revision
Create Date: 2024-10-14 12:00:00.000000

"""
from alembic import op
from sqlalchemy import Column, DateTime

def upgrade() -> None:
    # 1. server_default 제거
    with op.batch_alter_table('daily_memos') as batch_op:
        batch_op.alter_column('created_at', server_default=None)
        batch_op.alter_column('updated_at', server_default=None)

def downgrade() -> None:
    # 롤백 시 server_default 복원
    with op.batch_alter_table('daily_memos') as batch_op:
        batch_op.alter_column('created_at', server_default='(CURRENT_TIMESTAMP)')
        batch_op.alter_column('updated_at', server_default='(CURRENT_TIMESTAMP)')
```

### 타임존 관련 주의사항

1. **새 모델 생성 시**
   - `server_default=func.now()` 사용 금지
   - `get_current_utc_datetime()` 함수 사용
   - 애플리케이션 레벨에서 시간 생성

2. **기존 데이터 마이그레이션 시**
   - 기존 데이터가 이미 UTC인지 확인
   - 필요시 시간대 변환 로직 추가
   - 데이터 손실 방지를 위한 백업 필수

3. **테스트 시**
   - 타임존 변환 테스트 필수
   - 자정 경계 시간 테스트
   - API 응답 시간 포맷 검증

## 🔧 고급 사용법

### 수동 마이그레이션 생성
```bash
# 빈 마이그레이션 파일 생성
uv run alembic revision -m "Custom data migration"
```

### 브랜치 마이그레이션
```bash
# 여러 브랜치가 있는 경우 병합
uv run alembic merge -m "Merge branches" head1 head2
```

### 마이그레이션 히스토리 확인
```bash
# 전체 히스토리
uv run alembic history --verbose

# 특정 범위
uv run alembic history --rev-range current:head
```

## 🚨 주의사항

### 프로덕션 환경에서의 마이그레이션

1. **백업 필수**
   ```bash
   # 마이그레이션 전 백업
   cp data/app.db data/app_backup_$(date +%Y%m%d_%H%M%S).db
   ```

2. **롤백 계획 확인**
   ```bash
   # 롤백 가능성 미리 테스트
   python scripts/rollback.py --dry-run
   ```

3. **단계별 적용**
   ```bash
   # 한 번에 하나씩 적용
   python scripts/migrate.py --revision +1
   ```

### 마이그레이션 충돌 해결

1. **충돌 발생 시**
   ```bash
   # 현재 상태 확인
   python scripts/migration_status.py

   # 히스토리 확인
   uv run alembic history --verbose
   ```

2. **병합 마이그레이션 생성**
   ```bash
   uv run alembic merge -m "Resolve migration conflict" head1 head2
   ```

## 📁 파일 구조

```
migrations/
├── env.py                 # Alembic 환경 설정
├── script.py.mako        # 마이그레이션 템플릿
├── alembic.ini           # Alembic 설정 파일
└── versions/             # 마이그레이션 파일들
    ├── 20241011_1202_8aaa01a42a55_initial_schema_creation.py
    └── ...

scripts/
└── db.py                # 통합 데이터베이스 관리 스크립트
    ├── migrate-new      # 새 마이그레이션 생성
    ├── migrate-up       # 마이그레이션 적용
    ├── migrate-down     # 마이그레이션 롤백
    ├── migrate-status   # 상태 확인
    ├── backup          # 백업 생성
    ├── restore         # 백업 복원
    └── init            # 데이터베이스 초기화
```

## 🔄 개발 워크플로우 통합

### 개발 환경 설정
```bash
# 프로젝트 초기 설정 시
uv sync
python scripts/db.py init  # 데이터베이스 초기화
```

### 새 기능 개발 시
```bash
# 1. 새 브랜치 생성
git checkout -b feature/new-model

# 2. 모델 변경
# ... 코드 수정 ...

# 3. 마이그레이션 생성
python scripts/db.py migrate-new "Add new feature model"

# 4. 테스트
python scripts/db.py migrate-up
pytest

# 5. 커밋
git add .
git commit -m "✨ Add new feature with migration"
```

### 코드 리뷰 체크리스트
- [ ] 마이그레이션 파일이 포함되어 있는가?
- [ ] `upgrade()` 함수가 올바르게 구현되었는가?
- [ ] `downgrade()` 함수가 올바르게 구현되었는가?
- [ ] 데이터 손실 위험이 없는가?
- [ ] 인덱스와 제약조건이 적절히 설정되었는가?

## 🐛 문제 해결

### 일반적인 오류들

1. **"Target database is not up to date"**
   ```bash
   python scripts/db.py migrate-up
   ```

2. **"Can't locate revision identified by..."**
   ```bash
   # 마이그레이션 히스토리 확인
   python scripts/db.py migrate-status --history
   ```

3. **모델 import 오류**
   - `migrations/env.py`에 새 모델이 import되었는지 확인

4. **데이터베이스 잠금 오류**
   ```bash
   # 실행 중인 서버 종료 후 재시도
   pkill -f uvicorn
   python scripts/db.py migrate-up
   ```

### 긴급 복구 절차

1. **백업에서 복원**
   ```bash
   cp data/app_backup_[timestamp].db data/app.db
   ```

2. **마이그레이션 테이블 재설정**
   ```bash
   # 주의: 데이터 손실 위험
   uv run alembic stamp head
   ```

## 📊 모니터링

### 정기 점검 항목
- [ ] 마이그레이션 상태가 최신인가?
- [ ] 백업이 정기적으로 생성되고 있는가?
- [ ] 롤백 테스트가 가능한가?
- [ ] 마이그레이션 파일이 버전 관리되고 있는가?

### 성능 모니터링
```bash
# 데이터베이스 크기 확인
ls -lh data/app.db

# 마이그레이션 실행 시간 측정
time python scripts/db.py migrate-up
```

---

*이 가이드는 프로젝트와 함께 지속적으로 업데이트됩니다.*
*문제가 발생하면 CLAUDE.md의 디버깅 가이드라인을 참고하세요.*