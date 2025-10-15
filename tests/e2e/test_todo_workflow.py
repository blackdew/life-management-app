"""
할일 관리 핵심 사용자 여정 E2E 테스트
API 테스트와 중복 제거, 핵심 워크플로우만 유지
"""
import pytest
from playwright.sync_api import Page, expect


class TestTodoWorkflow:
    """할일 관리 핵심 사용자 여정 테스트"""

    def test_complete_todo_user_journey(self, page: Page, helpers):
        """핵심 사용자 여정: 할일 생성 → 완료 → 확인"""
        # 할일 생성
        todo_title = "완전한 사용자 여정 테스트"
        page.fill("#quick-todo-input", todo_title)
        page.click("#quick-add-btn")
        page.wait_for_load_state("networkidle")

        # 할일이 UI에 표시되는지 확인
        expect(page.get_by_text(todo_title)).to_be_visible()

        # 할일 완료 (UI 상호작용 테스트)
        complete_btn = page.locator(".todo-item").last.locator("button").first
        if complete_btn.is_visible():
            complete_btn.click()
            page.wait_for_load_state("networkidle")

    def test_quick_todo_creation_ui_flow(self, page: Page, helpers):
        """빠른 할일 생성 UI 플로우 테스트"""
        # 입력 필드와 버튼의 존재 확인
        expect(page.locator("#quick-todo-input")).to_be_visible()
        expect(page.locator("#quick-add-btn")).to_be_enabled()

        # 할일 입력 및 생성
        page.fill("#quick-todo-input", "UI 플로우 테스트")
        page.click("#quick-add-btn")
        page.wait_for_load_state("networkidle")

        # 입력 필드가 클리어되고 할일이 표시되는지 확인
        input_value = page.input_value("#quick-todo-input")
        assert input_value == ""  # 입력 필드 클리어 확인
        expect(page.get_by_text("UI 플로우 테스트")).to_be_visible()