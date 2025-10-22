"""
E2E 테스트 설정 및 픽스쳐
"""
import pytest
import subprocess
import time
import requests
from playwright.sync_api import Playwright, Page, Browser
import tempfile
import shutil
from pathlib import Path

# 테스트용 서버 설정
# 개발 환경(8000)에서 테스트 실행
# 8000: dev (개발 + E2E 테스트)
# 8001: main (운영)
TEST_SERVER_URL = "http://localhost:8000"
TEST_DB_PATH = "data/test_e2e.db"
TEST_PORT = 8000


@pytest.fixture(scope="session")
def test_server():
    """E2E 테스트용 서버 확인 또는 시작

    개발 서버(8000)가 이미 실행 중이면 기존 서버 사용
    실행 중이 아니면 테스트용 서버 시작
    """
    import sys
    import os

    # 개발 서버(8000)가 이미 실행 중인지 확인
    server_already_running = False
    try:
        response = requests.get(f"{TEST_SERVER_URL}/", timeout=2)
        if response.status_code == 200:
            server_already_running = True
            print(f"✅ 기존 개발 서버(포트 {TEST_PORT}) 사용")
    except requests.exceptions.RequestException:
        print(f"🚀 테스트용 서버를 포트 {TEST_PORT}에서 시작합니다...")

    process = None
    if not server_already_running:
        # 테스트용 데이터베이스 생성
        original_db = "data/app_dev.db"  # 개발 DB 사용
        if Path(original_db).exists():
            shutil.copy2(original_db, TEST_DB_PATH)

        # 환경 변수 설정으로 테스트 DB 사용
        env = os.environ.copy()
        env["APP_ENV"] = "dev"  # 개발 환경 사용
        env["DATABASE_URL"] = f"sqlite:///./{TEST_DB_PATH}"
        env["TESTING"] = "true"

        # 테스트 서버 시작 (Python을 직접 사용)
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(TEST_PORT)],
            env=env
        )

        # 서버가 시작될 때까지 대기
        max_attempts = 30
        for _ in range(max_attempts):
            try:
                response = requests.get(f"{TEST_SERVER_URL}/", timeout=1)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                time.sleep(1)
        else:
            if process:
                process.kill()
            raise RuntimeError("테스트 서버 시작 실패")

    yield TEST_SERVER_URL

    # 정리 (자체 시작한 서버만 종료)
    if process is not None:
        process.kill()
        if Path(TEST_DB_PATH).exists():
            Path(TEST_DB_PATH).unlink()


@pytest.fixture(scope="session")
def browser_context_args():
    """브라우저 컨텍스트 설정"""
    return {
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
        "locale": "ko-KR",
        "timezone_id": "Asia/Seoul"
    }


@pytest.fixture
def page(playwright: Playwright, browser_context_args, test_server) -> Page:
    """E2E 테스트용 페이지 픽스쳐"""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(**browser_context_args)
    page = context.new_page()

    # 기본 페이지로 이동
    page.goto(test_server)

    yield page

    context.close()
    browser.close()


@pytest.fixture
def page_with_data(page: Page):
    """테스트 데이터가 있는 페이지"""
    # 기본 마일스톤과 할일이 있는 상태로 설정
    # 실제 데이터베이스에 테스트 데이터가 있다고 가정
    page.reload()
    return page


# 공통 헬퍼 함수들
class E2EHelpers:
    @staticmethod
    def wait_for_htmx(page: Page, timeout: int = 5000):
        """HTMX 요청 완료 대기"""
        page.wait_for_function("() => window.htmx && !window.htmx.processing", timeout=timeout)

    @staticmethod
    def fill_and_submit_form(page: Page, form_selector: str, fields: dict, submit_selector: str = None):
        """폼 필드 채우고 제출"""
        for field_name, value in fields.items():
            page.fill(f"{form_selector} [name='{field_name}']", value)

        if submit_selector:
            page.click(submit_selector)
        else:
            page.click(f"{form_selector} [type='submit']")

    @staticmethod
    def wait_for_modal(page: Page, modal_selector: str = "[data-modal]"):
        """모달 표시 대기"""
        page.wait_for_selector(modal_selector, state="visible")

    @staticmethod
    def close_modal(page: Page, close_selector: str = "[data-modal-close]"):
        """모달 닫기"""
        page.click(close_selector)


@pytest.fixture
def helpers():
    """E2E 테스트 헬퍼 함수들"""
    return E2EHelpers