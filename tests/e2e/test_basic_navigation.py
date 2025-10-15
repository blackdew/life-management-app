"""
기본 네비게이션 및 페이지 로딩 E2E 테스트
"""
import pytest
import re
from playwright.sync_api import Page, expect


class TestBasicNavigation:
    """기본 페이지 네비게이션 테스트"""

    def test_homepage_loads_successfully(self, page: Page):
        """홈페이지가 정상적으로 로딩되는지 테스트"""
        # 페이지 제목 확인
        expect(page).to_have_title("Daily Flow")

        # 주요 요소들이 표시되는지 확인
        expect(page.locator("h1")).to_contain_text("Daily Flow")
        expect(page.locator("main")).to_be_visible()

    def test_navigation_menu_works(self, page: Page):
        """네비게이션 메뉴가 정상 작동하는지 테스트"""
        # 데스크톱에서 테스트하도록 화면 크기 설정
        page.set_viewport_size({"width": 1280, "height": 720})

        # 마일스톤 관리 페이지로 이동 (데스크톱 사이드바 사용)
        page.click("aside a[href='/journeys']")
        expect(page).to_have_url(re.compile(".*/journeys"))

        # 회고 히스토리 페이지로 이동
        page.click("aside a[href='/reflection-history']")
        expect(page).to_have_url(re.compile(".*/reflection-history"))

        # 홈으로 돌아가기
        page.click("aside a[href='/']")
        expect(page).to_have_url(re.compile(".*/$"))

    def test_responsive_design(self, page: Page):
        """반응형 디자인이 작동하는지 테스트"""
        # 데스크톱 사이즈
        page.set_viewport_size({"width": 1280, "height": 720})
        expect(page.locator("aside").first).to_be_visible()  # 데스크톱 사이드바

        # 모바일 사이즈
        page.set_viewport_size({"width": 375, "height": 667})
        # 모바일에서는 하단 네비게이션이 표시되어야 함
        expect(page.locator("nav.lg\\:hidden").first).to_be_visible()  # 모바일 하단 nav

    def test_page_load_performance(self, page: Page):
        """페이지 로딩 성능 테스트"""
        # 페이지 로딩 시간 측정
        import time
        start_time = time.time()

        page.reload()
        page.wait_for_load_state("networkidle")

        load_time = time.time() - start_time

        # 3초 이내에 로딩되어야 함
        assert load_time < 3.0, f"페이지 로딩이 너무 느림: {load_time:.2f}초"

    def test_error_pages(self, page: Page):
        """에러 페이지 처리 테스트"""
        # 존재하지 않는 페이지로 이동
        page.goto(page.url + "/nonexistent-page")

        # 404 에러 페이지가 표시되는지 확인
        expect(page.locator("body")).to_contain_text("페이지를 찾을 수 없습니다")

    def test_search_functionality(self, page: Page):
        """검색 기능 테스트"""
        # 검색 입력 필드가 있는지 확인
        search_input = page.locator("input[name='q']")
        if search_input.is_visible():
            # 검색어 입력
            search_input.fill("테스트")

            # 검색 결과가 표시되는지 확인
            page.wait_for_selector("[data-search-results]", timeout=3000)
            expect(page.locator("[data-search-results]")).to_be_visible()