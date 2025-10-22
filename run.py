#!/usr/bin/env python3
"""
크로스 플랫폼 실행 스크립트

모든 운영체제(Windows, Mac, Linux)에서 동일하게 사용 가능한 실행 스크립트입니다.

사용법:
    # 개발 환경 실행
    python run.py dev

    # 메인 환경 실행
    python run.py main

    # 테스트 실행
    python run.py test
"""

import sys
import os
import subprocess
import platform
from pathlib import Path
from typing import Literal


class ColorCode:
    """터미널 색상 코드"""

    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


def print_colored(message: str, color: str = ColorCode.RESET):
    """색상이 적용된 메시지 출력"""
    print(f"{color}{message}{ColorCode.RESET}")


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리 반환"""
    return Path(__file__).parent


def run_dev_server():
    """개발 환경 서버 실행"""
    print_colored("🚀 개발 환경 서버를 시작합니다...", ColorCode.GREEN)
    print_colored("📍 환경: DEV", ColorCode.CYAN)
    print_colored("🗄️  DB: data/app_dev.db", ColorCode.CYAN)
    print_colored("🌐 포트: 8000", ColorCode.CYAN)
    print()

    # 환경변수 설정
    env = os.environ.copy()
    env["APP_ENV"] = "dev"

    # Uvicorn 서버 실행
    cmd = ["uv", "run", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

    try:
        subprocess.run(cmd, env=env, cwd=get_project_root(), check=True)
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ 서버 실행 실패: {e}", ColorCode.RED)
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        print_colored("✋ 서버가 종료되었습니다.", ColorCode.YELLOW)
        sys.exit(0)


def run_main_server():
    """메인 환경 서버 실행"""
    print_colored("🚀 메인(프로덕션) 환경 서버를 시작합니다...", ColorCode.GREEN)
    print_colored("📍 환경: MAIN (PRODUCTION)", ColorCode.YELLOW)
    print_colored("🗄️  DB: data/app.db", ColorCode.CYAN)
    print_colored("🌐 포트: 8001", ColorCode.CYAN)
    print_colored("⚠️  디버그 모드: OFF", ColorCode.YELLOW)
    print()

    # 환경변수 설정
    env = os.environ.copy()
    env["APP_ENV"] = "main"
    env["DEBUG"] = "false"

    # Uvicorn 서버 실행 (reload 없음)
    cmd = ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]

    try:
        subprocess.run(cmd, env=env, cwd=get_project_root(), check=True)
    except subprocess.CalledProcessError as e:
        print_colored(f"❌ 서버 실행 실패: {e}", ColorCode.RED)
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        print_colored("✋ 서버가 종료되었습니다.", ColorCode.YELLOW)
        sys.exit(0)


def run_tests():
    """테스트 실행"""
    print_colored("======================================", ColorCode.CYAN)
    print_colored("🧪 서비스 로직 테스트 (async 지원)", ColorCode.GREEN)
    print_colored("======================================", ColorCode.CYAN)
    print("FastAPI TestClient 없이 실행하여 이벤트 루프 충돌 방지")
    print()

    project_root = get_project_root()

    # 서비스 테스트 실행
    cmd_service = [
        "uv",
        "run",
        "pytest",
        "tests/services/",
        "-v",
        "--tb=short",
        "--cov=app/services",
        "--cov-report=term-missing",
    ]

    try:
        subprocess.run(cmd_service, cwd=project_root, check=True)
    except subprocess.CalledProcessError as e:
        print()
        print_colored("❌ 서비스 테스트 실패!", ColorCode.RED)
        sys.exit(e.returncode)

    print()
    print_colored("======================================", ColorCode.CYAN)
    print_colored("🌐 API 및 통합 테스트", ColorCode.GREEN)
    print_colored("======================================", ColorCode.CYAN)
    print("FastAPI TestClient 사용, async 서비스 테스트는 skip")
    print()

    # API, E2E, 모델 테스트 실행
    cmd_api = [
        "uv",
        "run",
        "pytest",
        "tests/api/",
        "tests/e2e/",
        "tests/models/",
        "-v",
        "--tb=short",
    ]

    try:
        subprocess.run(cmd_api, cwd=project_root, check=True)
    except subprocess.CalledProcessError as e:
        print()
        print_colored("❌ API/통합 테스트 실패!", ColorCode.RED)
        sys.exit(e.returncode)

    print()
    print_colored("======================================", ColorCode.CYAN)
    print_colored("✅ 모든 테스트 완료", ColorCode.GREEN)
    print_colored("======================================", ColorCode.CYAN)
    print("서비스 로직: 실제 async 테스트 포함")
    print("API/E2E: HTTP 인터페이스 및 시나리오 테스트")
    print()


def print_usage():
    """사용법 출력"""
    print_colored("사용법:", ColorCode.CYAN)
    print("  python run.py dev     # 개발 환경 서버 실행")
    print("  python run.py main    # 메인 환경 서버 실행")
    print("  python run.py test    # 테스트 실행")
    print()
    print_colored(f"현재 운영체제: {platform.system()}", ColorCode.YELLOW)


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print_colored("❌ 명령어를 지정해주세요.", ColorCode.RED)
        print()
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "dev":
        run_dev_server()
    elif command == "main":
        run_main_server()
    elif command == "test":
        run_tests()
    else:
        print_colored(f"❌ 알 수 없는 명령어: {command}", ColorCode.RED)
        print()
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
