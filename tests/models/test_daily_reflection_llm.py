"""
DailyReflection 모델의 LLM 관련 필드 테스트
"""
import pytest
from datetime import date, datetime
from sqlalchemy.orm import Session

from app.models.daily_reflection import DailyReflection


class TestDailyReflectionLLMFields:
    """DailyReflection 모델의 LLM 관련 필드 테스트"""

    def test_create_reflection_with_llm_fields(self, test_db: Session):
        """LLM 관련 필드가 포함된 회고 생성 테스트"""
        reflection = DailyReflection(
            reflection_date=date.today(),
            reflection_text="오늘의 회고 내용",
            total_todos=5,
            completed_todos=3,
            completion_rate=60.0,
            generated_blog_content="# 오늘의 블로그 글\n\n정말 보람찬 하루였습니다.",
            blog_generation_prompt="회고를 바탕으로 블로그 글을 작성해주세요.",
            blog_generated_at=datetime.now()
        )

        test_db.add(reflection)
        test_db.commit()
        test_db.refresh(reflection)

        assert reflection.id is not None
        assert reflection.generated_blog_content == "# 오늘의 블로그 글\n\n정말 보람찬 하루였습니다."
        assert reflection.blog_generation_prompt == "회고를 바탕으로 블로그 글을 작성해주세요."
        assert reflection.blog_generated_at is not None

    def test_create_reflection_without_llm_fields(self, test_db: Session):
        """LLM 필드 없이 회고 생성 테스트 (기본값 확인)"""
        reflection = DailyReflection(
            reflection_date=date.today(),
            reflection_text="일반 회고 내용",
            total_todos=3,
            completed_todos=2,
            completion_rate=66.7
        )

        test_db.add(reflection)
        test_db.commit()
        test_db.refresh(reflection)

        assert reflection.id is not None
        assert reflection.generated_blog_content is None
        assert reflection.blog_generation_prompt is None
        assert reflection.blog_generated_at is None

    def test_update_existing_reflection_with_llm_content(self, test_db: Session):
        """기존 회고에 LLM 콘텐츠 업데이트 테스트"""
        # 기본 회고 생성
        reflection = DailyReflection(
            reflection_date=date.today(),
            reflection_text="기본 회고",
            total_todos=1,
            completed_todos=1,
            completion_rate=100.0
        )
        test_db.add(reflection)
        test_db.commit()
        test_db.refresh(reflection)

        # LLM 콘텐츠 추가
        reflection.generated_blog_content = "# AI가 생성한 블로그 글"
        reflection.blog_generation_prompt = "블로그 글을 생성해주세요"
        reflection.blog_generated_at = datetime.now()

        test_db.commit()
        test_db.refresh(reflection)

        assert reflection.generated_blog_content == "# AI가 생성한 블로그 글"
        assert reflection.blog_generation_prompt == "블로그 글을 생성해주세요"
        assert reflection.blog_generated_at is not None

    def test_llm_content_can_be_large_text(self, test_db: Session):
        """LLM으로 생성된 긴 블로그 글 저장 테스트"""
        large_blog_content = "# 오늘의 회고\n\n" + "이것은 긴 내용입니다. " * 1000
        large_prompt = "상세한 프롬프트입니다. " * 100

        reflection = DailyReflection(
            reflection_date=date.today(),
            reflection_text="회고 내용",
            total_todos=1,
            completed_todos=1,
            completion_rate=100.0,
            generated_blog_content=large_blog_content,
            blog_generation_prompt=large_prompt
        )

        test_db.add(reflection)
        test_db.commit()
        test_db.refresh(reflection)

        assert len(reflection.generated_blog_content) > 5000
        assert len(reflection.blog_generation_prompt) > 1000
        assert reflection.generated_blog_content == large_blog_content
        assert reflection.blog_generation_prompt == large_prompt

    def test_blog_generated_at_is_optional(self, test_db: Session):
        """blog_generated_at 필드가 선택적인지 테스트"""
        reflection = DailyReflection(
            reflection_date=date.today(),
            reflection_text="회고 내용",
            total_todos=1,
            completed_todos=1,
            completion_rate=100.0,
            generated_blog_content="블로그 글",
            blog_generation_prompt="프롬프트"
            # blog_generated_at는 의도적으로 설정하지 않음
        )

        test_db.add(reflection)
        test_db.commit()
        test_db.refresh(reflection)

        assert reflection.generated_blog_content == "블로그 글"
        assert reflection.blog_generation_prompt == "프롬프트"
        assert reflection.blog_generated_at is None

    def test_multiple_blog_generations_update(self, test_db: Session):
        """여러 번 블로그 글을 생성하는 경우 업데이트 테스트"""
        reflection = DailyReflection(
            reflection_date=date.today(),
            reflection_text="회고 내용",
            total_todos=1,
            completed_todos=1,
            completion_rate=100.0
        )
        test_db.add(reflection)
        test_db.commit()
        test_db.refresh(reflection)

        # 첫 번째 생성
        first_generation_time = datetime.now()
        reflection.generated_blog_content = "첫 번째 블로그 글"
        reflection.blog_generation_prompt = "첫 번째 프롬프트"
        reflection.blog_generated_at = first_generation_time
        test_db.commit()

        # 두 번째 생성 (재생성)
        import time
        time.sleep(0.1)  # 시간 차이를 위해
        second_generation_time = datetime.now()
        reflection.generated_blog_content = "두 번째 블로그 글"
        reflection.blog_generation_prompt = "두 번째 프롬프트 (추가 요청 포함)"
        reflection.blog_generated_at = second_generation_time
        test_db.commit()
        test_db.refresh(reflection)

        assert reflection.generated_blog_content == "두 번째 블로그 글"
        assert reflection.blog_generation_prompt == "두 번째 프롬프트 (추가 요청 포함)"
        assert reflection.blog_generated_at == second_generation_time
        assert reflection.blog_generated_at > first_generation_time