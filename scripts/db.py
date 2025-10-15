#!/usr/bin/env python3
"""
통합 데이터베이스 관리 스크립트

모든 데이터베이스 관련 작업을 하나의 스크립트로 통합하여 관리합니다:
- 초기화 및 마이그레이션
- 백업 및 복원
- 상태 확인 및 관리

사용법:
    python scripts/db.py <command> [options]

명령어:
    init                    데이터베이스 초기화 (마이그레이션 실행)
    migrate-status          마이그레이션 상태 확인
    migrate-new "description" 새 마이그레이션 생성
    migrate-up              마이그레이션 적용
    migrate-down            마이그레이션 롤백
    backup                  백업 생성
    restore <file>          백업 복원
    list-backups           백업 목록 표시
    reset                   백업 + 초기화 + 최신 마이그레이션
    fresh                   완전 초기화 (데이터 삭제)

예시:
    python scripts/db.py init
    python scripts/db.py status --verbose
    python scripts/db.py migrate-new "Add user profile table"
    python scripts/db.py backup
    python scripts/db.py restore data/backups/app_backup_20241011_120000.db
"""

import sys
import os
import shutil
import sqlite3
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, List


class DatabaseManager:
    """통합 데이터베이스 관리 클래스"""

    def __init__(self, env: str = "dev"):
        self.project_root = Path(__file__).parent.parent
        self.env = env

        # 환경에 따른 데이터베이스 파일 경로 설정
        if env == "main":
            self.db_path = self.project_root / "data" / "app.db"
        else:  # dev
            self.db_path = self.project_root / "data" / "app_dev.db"

        self.backup_dir = self.project_root / "data" / "backups" / env

        # Python 경로에 프로젝트 루트 추가
        sys.path.insert(0, str(self.project_root))

    def _run_alembic_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Alembic 명령어 실행"""
        cmd = ["uv", "run", "alembic"] + args
        # 환경변수로 APP_ENV 전달하여 migrations/env.py가 올바른 DB 사용
        env_vars = os.environ.copy()
        env_vars["APP_ENV"] = self.env
        return subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True,
            env=env_vars
        )

    def _ensure_data_dir(self):
        """data 디렉토리 확보"""
        self.db_path.parent.mkdir(exist_ok=True)

    def _ensure_backup_dir(self):
        """백업 디렉토리 확보"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _print_success(self, message: str):
        """성공 메시지 출력"""
        print(f"✅ {message}")

    def _print_error(self, message: str):
        """에러 메시지 출력"""
        print(f"❌ {message}")

    def _print_info(self, message: str):
        """정보 메시지 출력"""
        print(f"📍 {message}")

    def _print_working(self, message: str):
        """작업 중 메시지 출력"""
        print(f"🔄 {message}")

    # === 초기화 기능 ===
    def init(self) -> bool:
        """데이터베이스 초기화"""
        print("🚀 Alembic 마이그레이션을 사용한 데이터베이스 초기화를 시작합니다...")

        # 1. data 디렉토리 생성
        self._ensure_data_dir()
        self._print_success(f"데이터 디렉토리 확인: {self.db_path.parent}")

        # 2. 마이그레이션 실행
        if not self.up():
            return False

        # 3. 상태 확인
        self.status(show_migration_info=False)

        # 4. 데이터베이스 확인
        if self._verify_database():
            self._print_success("데이터베이스 초기화가 완료되었습니다!")
            print("\n📋 사용 가능한 명령어:")
            print("   • python scripts/db.py migrate-status    # 상태 확인")
            print("   • python scripts/db.py migrate-new 'desc'  # 새 마이그레이션")
            print("   • python scripts/db.py backup           # 백업 생성")
            print("\n다음 단계:")
            print("   1. scripts/seed_data.py를 실행하여 테스트 데이터를 추가하세요")
            print("   2. uv run uvicorn app.main:app --reload로 서버를 시작하세요")
            return True
        else:
            self._print_error("데이터베이스 초기화에 실패했습니다.")
            return False

    def _verify_database(self) -> bool:
        """데이터베이스 생성 확인"""
        try:
            if not self.db_path.exists():
                self._print_error("데이터베이스 파일이 생성되지 않았습니다.")
                return False

            # SQLAlchemy inspect 사용
            from sqlalchemy import inspect, create_engine
            from app.core.config import settings

            engine = create_engine(str(settings.database_url))
            inspector = inspect(engine)
            tables = inspector.get_table_names()

            expected_tables = ["milestones", "todos", "daily_todos", "daily_records", "daily_reflections"]
            missing_tables = set(expected_tables) - set(tables)

            if missing_tables:
                self._print_error(f"누락된 테이블: {missing_tables}")
                return False

            self._print_success("모든 테이블이 정상적으로 생성되었습니다!")

            # 각 테이블의 컬럼 정보 출력
            print("\n📊 테이블 구조:")
            for table_name in expected_tables:
                if table_name in tables:
                    columns = inspector.get_columns(table_name)
                    print(f"\n   {table_name}:")
                    for column in columns:
                        print(f"     - {column['name']}: {column['type']}")

            return True

        except Exception as e:
            self._print_error(f"데이터베이스 확인 중 오류 발생: {e}")
            return False

    # === 마이그레이션 상태 ===
    def status(self, verbose: bool = False, history: bool = False, show_migration_info: bool = True) -> bool:
        """마이그레이션 상태 확인"""
        if show_migration_info:
            print("🔍 데이터베이스 마이그레이션 상태 확인")
            print("=" * 50)

        if verbose:
            self._show_database_info()
            print()

        # 현재 리비전
        current_result = self._run_alembic_command(["current"])
        if current_result.returncode == 0:
            current_revision = current_result.stdout.strip()
            self._print_info(f"현재 리비전: {current_revision}")
        else:
            self._print_error("현재 리비전 확인 중 오류 발생")
            return False

        # 최신 리비전
        heads_result = self._run_alembic_command(["heads"])
        if heads_result.returncode == 0:
            head_revision = heads_result.stdout.strip()
            self._print_info(f"최신 리비전: {head_revision}")
        else:
            self._print_error("최신 리비전 확인 중 오류 발생")
            return False

        # 동기화 상태 확인
        if current_revision == head_revision:
            self._print_success("데이터베이스가 최신 상태입니다!")
        else:
            print("⚠️  데이터베이스가 최신 상태가 아닙니다.")

            # 미적용 마이그레이션 표시
            pending = self._get_pending_migrations()
            if pending and pending[0] != "❌ 오류 발생":
                print("\n📋 적용되지 않은 마이그레이션:")
                for migration in pending:
                    if migration.strip():
                        print(f"  • {migration}")
                print("\n💡 마이그레이션 적용: python scripts/db.py migrate-up")

        # 히스토리 표시
        if history:
            print("\n📚 마이그레이션 히스토리:")
            print("-" * 30)
            history_result = self._run_alembic_command(["history"] + (["--verbose"] if verbose else []))
            if history_result.returncode == 0:
                for line in history_result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"  {line}")

        if show_migration_info:
            print("\n🛠️  유용한 명령어:")
            print("  • 마이그레이션 적용:     python scripts/db.py migrate-up")
            print("  • 새 마이그레이션 생성:  python scripts/db.py migrate-new 'description'")
            print("  • 롤백:                python scripts/db.py migrate-down")
            print("  • 백업:                python scripts/db.py backup")

        return True

    def _show_database_info(self):
        """데이터베이스 정보 표시"""
        from app.core.config import settings

        print(f"🗄️  데이터베이스: {settings.database_url}")

        # 데이터베이스 파일 존재 여부 확인
        if "sqlite" in str(settings.database_url):
            if self.db_path.exists():
                stat = self.db_path.stat()
                size = stat.st_size
                modified = datetime.fromtimestamp(stat.st_mtime)
                print(f"📁 파일 크기: {size:,} bytes")
                print(f"📅 마지막 수정: {modified.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                self._print_error("데이터베이스 파일이 존재하지 않습니다")

    def _get_pending_migrations(self) -> List[str]:
        """적용되지 않은 마이그레이션 목록"""
        try:
            # current에서 head까지의 마이그레이션 확인
            result = self._run_alembic_command(["history", "--rev-range", "current:head"])

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # 현재 리비전을 제외한 라인들만 반환
                return [line for line in lines if line.strip() and not line.startswith('current')]
            else:
                return ["❌ 오류 발생"]

        except Exception as e:
            return [f"❌ 오류: {e}"]

    # === 마이그레이션 생성 ===
    def create(self, description: str) -> bool:
        """새로운 마이그레이션 생성"""
        if not description:
            self._print_error("마이그레이션 설명을 입력해주세요.")
            print("사용법: python scripts/db.py create 'migration_description'")
            return False

        self._print_working(f"새로운 마이그레이션 생성 중: {description}")

        # Alembic revision 명령 실행
        result = self._run_alembic_command(["revision", "--autogenerate", "-m", description])

        if result.returncode == 0:
            self._print_success("마이그레이션이 성공적으로 생성되었습니다!")
            print(f"📝 출력: {result.stdout}")

            # 생성된 파일 경로 추출
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Generating' in line and '.py' in line:
                    file_path = line.split('Generating ')[1].split(' ...')[0]
                    print(f"📄 생성된 파일: {file_path}")
            return True
        else:
            self._print_error("마이그레이션 생성 중 오류가 발생했습니다:")
            print(f"오류: {result.stderr}")
            return False

    # === 마이그레이션 적용 ===
    def up(self, revision: str = "head") -> bool:
        """마이그레이션 적용"""
        self._print_working(f"데이터베이스 마이그레이션 실행 중... (목표: {revision})")

        # Alembic upgrade 명령 실행
        result = self._run_alembic_command(["upgrade", revision])

        if result.returncode == 0:
            self._print_success("데이터베이스 마이그레이션이 성공적으로 완료되었습니다!")
            if result.stdout.strip():
                print(f"📝 출력: {result.stdout}")
            return True
        else:
            self._print_error("마이그레이션 실행 중 오류가 발생했습니다:")
            print(f"오류: {result.stderr}")
            return False

    # === 마이그레이션 롤백 ===
    def down(self, steps: int = 1, revision: Optional[str] = None, dry_run: bool = False) -> bool:
        """마이그레이션 롤백"""
        if revision:
            target = revision
        else:
            target = f"-{steps}"

        if dry_run:
            self._print_info(f"드라이 런 모드: {target}로 롤백 계획 확인 중...")
            # SQL만 출력
            result = self._run_alembic_command(["downgrade", target, "--sql"])
            if result.returncode == 0:
                print("📋 실행될 SQL:")
                print(result.stdout)
                return True
            else:
                self._print_error(f"드라이 런 실행 중 오류: {result.stderr}")
                return False

        print(f"⚠️  주의: 데이터베이스를 {target}로 롤백합니다.")
        confirmation = input("계속하시겠습니까? (y/N): ")

        if confirmation.lower() != 'y':
            self._print_error("롤백이 취소되었습니다.")
            return False

        self._print_working(f"데이터베이스 롤백 실행 중... (목표: {target})")

        result = self._run_alembic_command(["downgrade", target])

        if result.returncode == 0:
            self._print_success("데이터베이스 롤백이 성공적으로 완료되었습니다!")
            if result.stdout.strip():
                print(f"📝 출력: {result.stdout}")
            return True
        else:
            self._print_error("롤백 실행 중 오류가 발생했습니다:")
            print(f"오류: {result.stderr}")
            return False

    # === 백업 기능 ===
    def backup(self) -> Optional[str]:
        """데이터베이스 백업 생성"""
        if not self.db_path.exists():
            self._print_error(f"데이터베이스 파일이 존재하지 않습니다: {self.db_path}")
            return None

        self._ensure_backup_dir()

        # 백업 파일명 생성 (타임스탬프 포함)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"app_backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_filename

        try:
            # SQLite의 VACUUM INTO를 사용한 안전한 백업
            conn = sqlite3.connect(str(self.db_path))
            conn.execute(f"VACUUM INTO '{backup_path}'")
            conn.close()

            # 파일 크기 확인
            size = backup_path.stat().st_size
            self._print_success(f"백업 완료: {backup_path} ({size:,} bytes)")

            # 오래된 백업 정리
            self._cleanup_old_backups()

            return str(backup_path)

        except Exception as e:
            self._print_error(f"백업 실패: {e}")
            return None

    def restore(self, backup_path: str) -> bool:
        """백업에서 데이터베이스 복원"""
        backup_file = Path(backup_path)
        if not backup_file.exists():
            self._print_error(f"백업 파일이 존재하지 않습니다: {backup_path}")
            return False

        try:
            # 현재 데이터베이스를 임시 백업
            temp_backup = None
            if self.db_path.exists():
                temp_backup = self.db_path.with_suffix('.temp_backup')
                shutil.copy2(self.db_path, temp_backup)
                self._print_info(f"현재 데이터베이스를 임시 백업: {temp_backup}")

            # 백업에서 복원
            shutil.copy2(backup_file, self.db_path)

            # 복원된 데이터베이스 검증
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            conn.close()

            self._print_success(f"복원 완료: {backup_path} → {self.db_path}")
            print(f"📊 테이블 수: {table_count}")

            # 마이그레이션 상태를 최신으로 설정 (복원된 DB가 최신이라고 가정)
            stamp_result = self._run_alembic_command(["stamp", "head"])
            if stamp_result.returncode == 0:
                self._print_success("마이그레이션 상태가 최신으로 설정되었습니다.")

            # 임시 백업 제거
            if temp_backup and temp_backup.exists():
                temp_backup.unlink()

            return True

        except Exception as e:
            self._print_error(f"복원 실패: {e}")

            # 롤백: 임시 백업에서 복원
            if temp_backup and temp_backup.exists():
                shutil.copy2(temp_backup, self.db_path)
                temp_backup.unlink()
                print("🔄 원본 데이터베이스로 롤백됨")

            return False

    def list_backups(self):
        """사용 가능한 백업 목록 표시"""
        self._ensure_backup_dir()

        backup_files = list(self.backup_dir.glob("app_backup_*.db"))
        if not backup_files:
            print("📂 사용 가능한 백업이 없습니다.")
            return

        print("📂 사용 가능한 백업:")
        for backup_file in sorted(backup_files, reverse=True):
            size = backup_file.stat().st_size
            mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            print(f"  - {backup_file.name} ({size:,} bytes, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")

    def _cleanup_old_backups(self, keep_count: int = 10):
        """오래된 백업 정리 (최신 keep_count개만 유지)"""
        backup_files = sorted(self.backup_dir.glob("app_backup_*.db"), reverse=True)

        if len(backup_files) <= keep_count:
            return

        old_backups = backup_files[keep_count:]
        for backup_file in old_backups:
            backup_file.unlink()
            print(f"🗑️ 오래된 백업 삭제: {backup_file.name}")

        print(f"🧹 {len(old_backups)}개의 오래된 백업 정리 완료")

    # === 복합 기능 ===
    def reset(self) -> bool:
        """백업 + 초기화 + 최신 마이그레이션"""
        print("🔄 데이터베이스 리셋을 시작합니다...")

        # 1. 백업 생성
        backup_path = self.backup()
        if not backup_path:
            self._print_error("백업 생성에 실패했습니다. 리셋을 중단합니다.")
            return False

        # 2. 최신 마이그레이션 적용
        if not self.up():
            self._print_error("마이그레이션 적용에 실패했습니다.")
            return False

        # 3. 상태 확인
        self.status(show_migration_info=False)

        self._print_success("데이터베이스 리셋이 완료되었습니다!")
        print(f"💾 백업 파일: {backup_path}")
        return True

    def fresh(self) -> bool:
        """완전 초기화 (데이터 삭제)"""
        print("⚠️  경고: 이 작업은 모든 데이터를 삭제합니다!")
        confirmation = input("정말로 모든 데이터를 삭제하고 초기화하시겠습니까? (y/N): ")

        if confirmation.lower() != 'y':
            self._print_error("초기화가 취소되었습니다.")
            return False

        # 1. 기존 데이터베이스 삭제
        if self.db_path.exists():
            self.db_path.unlink()
            self._print_success("기존 데이터베이스 파일 삭제 완료")

        # 2. 새로운 데이터베이스 초기화
        return self.init()


def main():
    """메인 함수 - CLI 인터페이스"""
    parser = argparse.ArgumentParser(
        description="통합 데이터베이스 관리 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python scripts/db.py --env dev init              # 개발 DB 초기화
  python scripts/db.py --env main migrate-status   # 메인 DB 상태 확인
  python scripts/db.py --env dev migrate-new "Add user table" # 개발 DB에 마이그레이션 생성
  python scripts/db.py --env dev migrate-up        # 개발 DB에 마이그레이션 적용
  python scripts/db.py --env main migrate-up       # 메인 DB에 마이그레이션 적용
  python scripts/db.py --env dev backup            # 개발 DB 백업
  python scripts/db.py --env main backup           # 메인 DB 백업
        """
    )

    # 전역 옵션: 환경 선택
    parser.add_argument(
        '--env',
        choices=['dev', 'main'],
        default='dev',
        help='데이터베이스 환경 선택 (기본값: dev)'
    )

    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')

    # init 명령어
    subparsers.add_parser('init', help='데이터베이스 초기화')


    # migrate-new 명령어
    create_parser = subparsers.add_parser('migrate-new', help='새 마이그레이션 생성')
    create_parser.add_argument('description', help='마이그레이션 설명')

    # migrate-up 명령어
    up_parser = subparsers.add_parser('migrate-up', help='마이그레이션 적용')
    up_parser.add_argument('--revision', default='head', help='적용할 리비전 (기본값: head)')

    # migrate-down 명령어
    down_parser = subparsers.add_parser('migrate-down', help='마이그레이션 롤백')
    down_parser.add_argument('--steps', type=int, default=1, help='롤백할 단계 수 (기본값: 1)')
    down_parser.add_argument('--revision', help='롤백할 대상 리비전')
    down_parser.add_argument('--dry-run', action='store_true', help='실제 실행 없이 계획만 확인')

    # migrate-status 명령어
    migrate_status_parser = subparsers.add_parser('migrate-status', help='마이그레이션 상태 확인')
    migrate_status_parser.add_argument('--verbose', action='store_true', help='상세 정보 표시')
    migrate_status_parser.add_argument('--history', action='store_true', help='마이그레이션 히스토리 표시')

    # backup 명령어
    subparsers.add_parser('backup', help='백업 생성')

    # restore 명령어
    restore_parser = subparsers.add_parser('restore', help='백업 복원')
    restore_parser.add_argument('backup_file', help='복원할 백업 파일 경로')

    # list-backups 명령어
    subparsers.add_parser('list-backups', help='백업 목록 표시')

    # reset 명령어
    subparsers.add_parser('reset', help='백업 + 초기화 + 최신 마이그레이션')

    # fresh 명령어
    subparsers.add_parser('fresh', help='완전 초기화 (데이터 삭제)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # DatabaseManager 인스턴스 생성 (환경 전달)
    db_manager = DatabaseManager(env=args.env)
    print(f"📍 환경: {args.env.upper()} (DB: {db_manager.db_path})\n")

    try:
        # 명령어별 실행
        if args.command == 'init':
            success = db_manager.init()
        elif args.command == 'migrate-status':
            success = db_manager.status(verbose=args.verbose, history=args.history)
        elif args.command == 'migrate-new':
            success = db_manager.create(args.description)
        elif args.command == 'migrate-up':
            success = db_manager.up(args.revision)
        elif args.command == 'migrate-down':
            success = db_manager.down(
                steps=args.steps,
                revision=args.revision,
                dry_run=args.dry_run
            )
        elif args.command == 'backup':
            success = db_manager.backup() is not None
        elif args.command == 'restore':
            success = db_manager.restore(args.backup_file)
        elif args.command == 'list-backups':
            db_manager.list_backups()
            success = True
        elif args.command == 'reset':
            success = db_manager.reset()
        elif args.command == 'fresh':
            success = db_manager.fresh()
        else:
            parser.print_help()
            return

        # 실행 결과에 따른 종료 코드
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n❌ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()