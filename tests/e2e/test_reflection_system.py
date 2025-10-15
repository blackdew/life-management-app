"""
회고 시스템 핵심 사용자 여정 E2E 테스트
API 테스트와 중복 제거, 핵심 UI 플로우만 유지
"""
import pytest
import re
from playwright.sync_api import Page, expect


class TestReflectionSystem:
    """회고 시스템 핵심 UI 테스트"""

    def test_reflection_navigation_and_page_load(self, page: Page):
        """회고 히스토리 페이지 네비게이션 및 로딩 테스트"""
        # 회고 히스토리 페이지로 이동
        page.click("aside a[href='/reflection-history']")
        page.wait_for_load_state("networkidle")

        # 페이지가 올바르게 로딩되었는지 확인
        expect(page.locator("h1")).to_contain_text("회고")
        expect(page).to_have_url(re.compile(r".*/reflection-history$"))

    def test_todo_completion_stays_on_current_page(self, page: Page):
        """할일 완료 후 현재 페이지에 머물러야 함 (리다이렉트 안됨)"""
        # 메인 페이지에서 시작 (이미 conftest.py에서 base URL로 이동됨)
        # page.goto("/")  # 상대 경로 사용 시 문제 발생
        initial_url = page.url

        # 할일이 있는지 확인, 없으면 빠른 할일 추가
        todo_items = page.locator(".todo-item")
        if todo_items.count() == 0:
            page.fill("#quick-todo-title", "테스트 할일")
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")

        # 첫 번째 미완료 할일 찾기
        incomplete_todo = page.locator(".todo-item:not(.completed) .complete-todo").first
        if incomplete_todo.is_visible():
            incomplete_todo.click()

            # 회고 모달이 나타나면 간단한 회고 작성
            if page.locator("#reflection-modal").is_visible():
                page.fill("#reflection-text", "테스트 회고")
                page.click("#submit-reflection")
                page.wait_for_load_state("networkidle")

            # 여전히 같은 페이지에 있어야 함 (리다이렉트 안됨)
            expect(page).to_have_url(initial_url)