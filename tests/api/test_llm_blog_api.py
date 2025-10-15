"""
LLM 블로그 생성 API 테스트
"""
import pytest
from unittest.mock import patch, AsyncMock
from datetime import date, datetime
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.daily_reflection import DailyReflection
from app.models.todo import DailyTodo, TodoCategory
from app.services.llm_blog_service import LLMProvider


class TestLLMBlogAPI:
    """LLM 블로그 생성 API 테스트"""

    @pytest.fixture
    def reflection_with_content(self, test_db: Session):
        """테스트용 회고 데이터 (이미 블로그 글이 생성된 상태)"""
        reflection = DailyReflection(
            reflection_date=date.today(),
            reflection_text="오늘은 정말 보람찬 하루였다.",
            total_todos=2,
            completed_todos=2,
            completion_rate=100.0,
            satisfaction_score=5,
            energy_level=4,
            generated_blog_content="# 오늘의 회고\n\n정말 멋진 하루였습니다!",
            blog_generation_prompt="회고를 바탕으로 블로그 글을 작성해주세요.",
            blog_generated_at=datetime.now(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        test_db.add(reflection)
        test_db.commit()
        test_db.refresh(reflection)
        return reflection

    @pytest.fixture
    def reflection_without_content(self, test_db: Session):
        """테스트용 회고 데이터 (블로그 글이 생성되지 않은 상태)"""
        reflection = DailyReflection(
            reflection_date=date.today(),
            reflection_text="새로운 회고 내용",
            total_todos=1,
            completed_todos=1,
            completion_rate=100.0,
            satisfaction_score=4,
            energy_level=3,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        test_db.add(reflection)
        test_db.commit()
        test_db.refresh(reflection)
        return reflection

    def test_generate_blog_first_time_success(self, client: TestClient, test_db: Session, reflection_without_content):
        """첫 번째 블로그 글 생성 성공 테스트"""
        with patch('app.services.llm_blog_service.LLMBlogService.generate_blog_content') as mock_generate:
            # Mock 설정
            mock_generate.return_value = {
                "content": "# AI가 생성한 블로그 글\n\n정말 멋진 하루였네요!",
                "is_cached": False,
                "generated_at": datetime.now()
            }

            response = client.post(
                f"/api/reflections/{reflection_without_content.id}/generate-blog",
                json={
                    "provider": "openai",
                    "include_images": True
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "# AI가 생성한 블로그 글\n\n정말 멋진 하루였네요!"
            assert data["is_cached"] == False
            assert "generated_at" in data

            # Mock이 올바른 매개변수로 호출되었는지 확인
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            assert call_args[1]["reflection_id"] == reflection_without_content.id
            assert call_args[1]["provider"] == LLMProvider.OPENAI
            assert call_args[1]["include_images"] == True

    def test_generate_blog_cached_content(self, client: TestClient, test_db: Session, reflection_with_content):
        """캐시된 블로그 글 조회 테스트"""
        with patch('app.services.llm_blog_service.LLMBlogService.generate_blog_content') as mock_generate:
            # Mock 설정 - 캐시된 콘텐츠 반환
            mock_generate.return_value = {
                "content": reflection_with_content.generated_blog_content,
                "is_cached": True,
                "generated_at": reflection_with_content.blog_generated_at
            }

            response = client.post(
                f"/api/reflections/{reflection_with_content.id}/generate-blog",
                json={
                    "provider": "openai"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "# 오늘의 회고\n\n정말 멋진 하루였습니다!"
            assert data["is_cached"] == True

    def test_regenerate_blog_content(self, client: TestClient, test_db: Session, reflection_with_content):
        """블로그 글 재생성 테스트"""
        with patch('app.services.llm_blog_service.LLMBlogService.generate_blog_content') as mock_generate:
            # Mock 설정 - 새로 생성된 콘텐츠 반환
            mock_generate.return_value = {
                "content": "# 재생성된 블로그 글\n\n더 재미있게 작성된 글입니다!",
                "is_cached": False,
                "generated_at": datetime.now()
            }

            response = client.post(
                f"/api/reflections/{reflection_with_content.id}/regenerate-blog",
                json={
                    "provider": "claude",
                    "include_images": False,
                    "additional_prompt": "더 재미있고 생생하게 써주세요"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "# 재생성된 블로그 글\n\n더 재미있게 작성된 글입니다!"
            assert data["is_cached"] == False

            # Mock이 강제 재생성 옵션과 함께 호출되었는지 확인
            call_args = mock_generate.call_args
            assert call_args[1]["force_regenerate"] == True
            assert call_args[1]["provider"] == LLMProvider.CLAUDE
            assert call_args[1]["additional_prompt"] == "더 재미있고 생생하게 써주세요"

    def test_get_blog_content_success(self, client: TestClient, test_db: Session, reflection_with_content):
        """저장된 블로그 콘텐츠 조회 성공 테스트"""
        response = client.get(f"/api/reflections/{reflection_with_content.id}/blog-content")

        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "# 오늘의 회고\n\n정말 멋진 하루였습니다!"
        assert data["generated_at"] is not None
        assert data["prompt"] == "회고를 바탕으로 블로그 글을 작성해주세요."

    def test_get_blog_content_not_generated(self, client: TestClient, test_db: Session, reflection_without_content):
        """블로그 글이 생성되지 않은 경우 조회 테스트"""
        response = client.get(f"/api/reflections/{reflection_without_content.id}/blog-content")

        assert response.status_code == 404
        data = response.json()
        assert "생성된 블로그 글이 없습니다" in data["detail"]

    def test_generate_blog_invalid_provider(self, client: TestClient, test_db: Session, reflection_without_content):
        """잘못된 LLM 제공업체로 블로그 생성 실패 테스트"""
        response = client.post(
            f"/api/reflections/{reflection_without_content.id}/generate-blog",
            json={
                "provider": "invalid_provider"
            }
        )

        assert response.status_code == 422  # Validation error

    def test_generate_blog_missing_environment_variable(self, client: TestClient, test_db: Session, reflection_without_content):
        """환경변수 미설정 시 블로그 생성 실패 테스트"""
        with patch('app.services.llm_blog_service.LLMBlogService.generate_blog_content') as mock_generate:
            # Mock이 환경변수 오류를 발생시키도록 설정
            mock_generate.side_effect = ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")

            response = client.post(
                f"/api/reflections/{reflection_without_content.id}/generate-blog",
                json={
                    "provider": "openai"
                }
            )

            assert response.status_code == 422
            data = response.json()
            assert "환경변수가 설정되지 않았습니다" in data["detail"]

    def test_generate_blog_reflection_not_found(self, client: TestClient, test_db: Session):
        """존재하지 않는 회고에 대한 블로그 생성 실패 테스트"""
        response = client.post(
            "/api/reflections/999999/generate-blog",
            json={
                "provider": "openai"
            }
        )

        assert response.status_code == 404
        data = response.json()
        assert "회고를 찾을 수 없습니다" in data["detail"]

    def test_generate_blog_llm_api_error(self, client: TestClient, test_db: Session, reflection_without_content):
        """LLM API 오류 발생 시 테스트"""
        with patch('app.services.llm_blog_service.LLMBlogService.generate_blog_content') as mock_generate:
            # Mock이 예외를 발생시키도록 설정
            mock_generate.side_effect = Exception("LLM API 호출 실패")

            response = client.post(
                f"/api/reflections/{reflection_without_content.id}/generate-blog",
                json={
                    "provider": "openai"
                }
            )

            assert response.status_code == 500
            data = response.json()
            assert "블로그 글 생성 실패" in data["detail"]

    def test_generate_blog_with_claude_provider(self, client: TestClient, test_db: Session, reflection_without_content):
        """Claude 제공업체로 블로그 생성 테스트"""
        with patch('app.services.llm_blog_service.LLMBlogService.generate_blog_content') as mock_generate:
            mock_generate.return_value = {
                "content": "# Claude가 작성한 블로그 글\n\n멋진 하루의 기록입니다.",
                "is_cached": False,
                "generated_at": datetime.now()
            }

            response = client.post(
                f"/api/reflections/{reflection_without_content.id}/generate-blog",
                json={
                    "provider": "claude",
                    "include_images": False
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "# Claude가 작성한 블로그 글\n\n멋진 하루의 기록입니다."

            # Claude 관련 매개변수 확인
            call_args = mock_generate.call_args
            assert call_args[1]["provider"] == LLMProvider.CLAUDE

    def test_generate_blog_with_additional_prompt(self, client: TestClient, test_db: Session, reflection_without_content):
        """추가 프롬프트와 함께 블로그 생성 테스트"""
        with patch('app.services.llm_blog_service.LLMBlogService.generate_blog_content') as mock_generate:
            mock_generate.return_value = {
                "content": "# 재미있게 작성된 블로그 글\n\n오늘 하루를 유머러스하게 담았습니다!",
                "is_cached": False,
                "generated_at": datetime.now()
            }

            response = client.post(
                f"/api/reflections/{reflection_without_content.id}/generate-blog",
                json={
                    "provider": "openai",
                    "additional_prompt": "유머러스하고 재미있게 작성해주세요. 이모지도 많이 사용해주세요."
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "재미있게 작성된" in data["content"]

            # 추가 프롬프트가 전달되었는지 확인
            call_args = mock_generate.call_args
            assert call_args[1]["additional_prompt"] == "유머러스하고 재미있게 작성해주세요. 이모지도 많이 사용해주세요."

    def test_blog_content_with_complex_reflection(self, client: TestClient, test_db: Session):
        """복잡한 회고 데이터로 블로그 생성 테스트"""
        # 복잡한 회고와 할일 데이터 생성
        reflection = DailyReflection(
            reflection_date=date.today(),
            reflection_text="오늘은 여러 가지 일을 처리했다. 프로젝트 발표도 하고, 운동도 했으며, 새로운 기술도 학습했다.",
            total_todos=4,
            completed_todos=3,
            completion_rate=75.0,
            satisfaction_score=4,
            energy_level=3
        )
        test_db.add(reflection)
        test_db.commit()
        test_db.refresh(reflection)

        # 관련 할일들 생성
        todos = [
            DailyTodo(
                title="프로젝트 발표",
                category=TodoCategory.WORK,
                is_completed=True,
                completed_at=datetime.now(),
                completion_reflection="발표가 성공적이었다",
                completion_image_path="/static/uploads/presentation.jpg",
                created_date=date.today(),
                scheduled_date=date.today()
            ),
            DailyTodo(
                title="운동하기",
                category=TodoCategory.HEALTH,
                is_completed=True,
                completed_at=datetime.now(),
                created_date=date.today(),
                scheduled_date=date.today()
            ),
            DailyTodo(
                title="새 기술 학습",
                category=TodoCategory.LEARNING,
                is_completed=True,
                completed_at=datetime.now(),
                created_date=date.today(),
                scheduled_date=date.today()
            ),
            DailyTodo(
                title="독서",
                category=TodoCategory.PERSONAL,
                is_completed=False,
                created_date=date.today(),
                scheduled_date=date.today()
            )
        ]
        test_db.add_all(todos)
        test_db.commit()

        with patch('app.services.llm_blog_service.LLMBlogService.generate_blog_content') as mock_generate:
            mock_generate.return_value = {
                "content": "# 다채로운 하루의 기록\n\n프로젝트 발표, 운동, 학습까지 알찬 하루였습니다!",
                "is_cached": False,
                "generated_at": datetime.now()
            }

            response = client.post(
                f"/api/reflections/{reflection.id}/generate-blog",
                json={
                    "provider": "openai",
                    "include_images": True
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "다채로운 하루" in data["content"]

            # 이미지 포함 옵션이 제대로 전달되었는지 확인
            call_args = mock_generate.call_args
            assert call_args[1]["include_images"] == True

    def test_get_blog_content_reflection_not_found(self, client: TestClient, test_db: Session):
        """존재하지 않는 회고의 블로그 콘텐츠 조회 테스트"""
        response = client.get("/api/reflections/999999/blog-content")

        assert response.status_code == 404
        data = response.json()
        assert "회고를 찾을 수 없습니다" in data["detail"]