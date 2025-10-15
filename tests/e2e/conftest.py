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
TEST_SERVER_URL = "http://localhost:8001"
TEST_DB_PATH = "data/test_e2e.db"


@pytest.fixture(scope="session")
def test_server():
    """E2E 테스트용 서버 시작"""
    import sys
    import os

    # 테스트용 데이터베이스 생성
    original_db = "data/app.db"
    if Path(original_db).exists():
        shutil.copy2(original_db, TEST_DB_PATH)

    # 환경 변수 설정으로 테스트 DB 사용
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///./{TEST_DB_PATH}"
    env["TESTING"] = "true"

    # 테스트 서버 시작 (Python을 직접 사용)
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"],
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
        process.kill()
        raise RuntimeError("테스트 서버 시작 실패")

    yield TEST_SERVER_URL

    # 정리
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