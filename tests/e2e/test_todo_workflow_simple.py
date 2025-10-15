"""
간단한 할일 관리 E2E 테스트
"""
import pytest
from playwright.sync_api import Page, expect


class TestTodoWorkflowSimple:
    """할일 관리 간단한 테스트"""

    def test_todo_page_loads(self, page: Page):
        """할일 페이지가 로딩되는지 테스트"""
        # 이미 test_server로 이동되어 있음
        expect(page.locator("h1")).to_contain_text("Daily Flow")
        expect(page.locator("#quick-todo-input")).to_be_visible()
        expect(page.locator("#quick-add-btn")).to_be_visible()

    def test_todo_input_works(self, page: Page):
        """할일 입력이 작동하는지 테스트"""
        # 할일 입력 필드에 텍스트 입력
        page.fill("#quick-todo-input", "간단한 E2E 테스트")

        # 입력된 값 확인
        input_value = page.input_value("#quick-todo-input")
        assert input_value == "간단한 E2E 테스트"

    def test_add_button_clickable(self, page: Page):
        """추가 버튼이 클릭 가능한지 테스트"""
        # 버튼이 활성화되어 있는지 확인
        expect(page.locator("#quick-add-btn")).to_be_enabled()

        # 버튼이 보이는지 확인
        expect(page.locator("#quick-add-btn")).to_be_visible()