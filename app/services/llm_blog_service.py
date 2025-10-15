"""
LLM 기반 블로그 글 생성 서비스

회고 데이터를 바탕으로 OpenAI 또는 Claude API를 사용하여
자동으로 블로그 글을 생성하는 서비스입니다.
"""
import os
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from ..models.daily_reflection import DailyReflection
from ..models.todo import DailyTodo
from ..models.daily_memo import DailyMemo


class LLMProvider(Enum):
    """LLM 제공업체"""
    OPENAI = "openai"
    CLAUDE = "claude"


class LLMBlogService:
    """LLM 기반 블로그 글 생성 서비스"""

    @staticmethod
    def get_api_key(provider: LLMProvider) -> str:
        """환경변수에서 API 키 가져오기"""
        if provider == LLMProvider.OPENAI:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
            return api_key
        elif provider == LLMProvider.CLAUDE:
            api_key = os.getenv("CLAUDE_API_KEY")
            if not api_key:
                raise ValueError("CLAUDE_API_KEY 환경변수가 설정되지 않았습니다.")
            return api_key
        else:
            raise ValueError(f"지원하지 않는 LLM 제공업체: {provider}")

    @staticmethod
    def get_optimal_model(provider: LLMProvider) -> str:
        """블로그 글 생성에 최적화된 모델 반환"""
        if provider == LLMProvider.OPENAI:
            return "gpt-4o"  # 최신 GPT-4o 모델 (블로그 글 품질이 우수)
        elif provider == LLMProvider.CLAUDE:
            return "claude-3-5-sonnet-20241022"  # 최신 Claude 3.5 Sonnet (창작 능력 우수)
        else:
            raise ValueError(f"지원하지 않는 LLM 제공업체: {provider}")

    @staticmethod
    def generate_blog_prompt(
        reflection: DailyReflection,
        completed_todos: List[DailyTodo],
        pending_todos: List[DailyTodo],
        daily_memos: List[DailyMemo] = None,
        include_images: bool = False,
        additional_prompt: str = None
    ) -> str:
        """블로그 글 생성을 위한 프롬프트 생성"""

        # 기본 프롬프트 구조
        prompt = f"""당신은 전문적인 블로거입니다. 아래 일일 회고 데이터를 바탕으로 매력적이고 읽기 좋은 블로그 글을 작성해주세요.

## 회고 정보
- 날짜: {reflection.reflection_date.strftime('%Y년 %m월 %d일')}
- 만족도: {reflection.satisfaction_score}/5
- 에너지: {reflection.energy_level}/5
- 전체 완료율: {reflection.completion_rate:.1f}%

## 전체 회고 내용
{reflection.reflection_text}

"""

        # 완료된 할일 추가
        if completed_todos:
            prompt += "## 완료한 일들\n"
            for todo in completed_todos:
                prompt += f"- **{todo.title}**"
                if todo.description:
                    prompt += f": {todo.description}"
                prompt += f" (카테고리: {todo.category.value})\n"

                if todo.completion_reflection:
                    prompt += f"  회고: {todo.completion_reflection}\n"

                if include_images and todo.completion_image_path:
                    prompt += f"  이미지: {todo.completion_image_path}\n"

                prompt += "\n"

        # 미완료 할일 추가
        if pending_todos:
            prompt += "## 미완료 할일들\n"
            for todo in pending_todos:
                prompt += f"- **{todo.title}**"
                if todo.description:
                    prompt += f": {todo.description}"
                prompt += f" (카테고리: {todo.category.value})\n"
            prompt += "\n"

        # 하루 중 작성한 메모들 추가
        if daily_memos:
            prompt += "## 하루 중 작성한 메모들\n"
            for memo in daily_memos:
                time_str = memo.created_at.strftime('%H:%M') if memo.created_at else ""
                prompt += f"- {memo.content}"
                if time_str:
                    prompt += f" ({time_str})"
                prompt += "\n"
            prompt += "\n"

        # 이미지 관련 지시사항
        if include_images:
            image_todos = [todo for todo in completed_todos if todo.completion_image_path]
            if image_todos:
                prompt += "## 이미지가 포함된 할일들\n"
                for todo in image_todos:
                    prompt += f"- {todo.title}: {todo.completion_image_path}\n"
                prompt += "\n블로그 글에 이미지를 적절한 위치에 배치해주세요.\n\n"

        # 블로그 글 작성 지시사항
        prompt += """## 작성 지침
1. 마크다운 형식으로 작성해주세요
2. 제목은 날짜와 함께 매력적으로 작성
3. 개인적이고 진솔한 톤앤매너 사용
4. 완료한 일들의 성취감과 배운 점 강조
5. 미완료 일들에 대한 앞으로의 계획이나 다짐 포함
6. 전체적으로 긍정적이고 성장 지향적인 메시지
7. 적절한 이모지 사용으로 읽기 쉽게 작성

"""

        # 추가 프롬프트가 있다면 추가
        if additional_prompt:
            prompt += f"## 추가 요청사항\n{additional_prompt}\n\n"

        prompt += "이제 위 정보를 바탕으로 블로그 글을 작성해주세요:"

        return prompt

    @staticmethod
    async def call_llm_api(
        provider: LLMProvider,
        prompt: str
    ) -> str:
        """LLM API 호출 (환경변수에서 API 키 자동 로딩)"""
        # 환경변수에서 API 키 가져오기
        api_key = LLMBlogService.get_api_key(provider)

        # 최적의 모델 자동 선택
        model = LLMBlogService.get_optimal_model(provider)

        if provider == LLMProvider.OPENAI:
            return await LLMBlogService._call_openai_api(prompt, api_key, model)
        elif provider == LLMProvider.CLAUDE:
            return await LLMBlogService._call_claude_api(prompt, api_key, model)
        else:
            raise ValueError(f"지원하지 않는 LLM 제공업체: {provider}")

    @staticmethod
    async def _call_openai_api(prompt: str, api_key: str, model: str) -> str:
        """OpenAI API 호출"""

        client = AsyncOpenAI(api_key=api_key)

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 개인 블로그를 작성하는 전문 작가입니다. 일상적이고 친근한 톤으로 글을 작성하며, 개인의 성장과 경험을 중심으로 이야기를 풀어나갑니다."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=2000
        )

        return response.choices[0].message.content

    @staticmethod
    async def _call_claude_api(prompt: str, api_key: str, model: str) -> str:
        """Claude API 호출"""

        client = AsyncAnthropic(api_key=api_key)

        response = await client.messages.create(
            model=model,
            max_tokens=2000,
            temperature=0.7,
            system="당신은 개인 블로그를 작성하는 전문 작가입니다. 일상적이고 친근한 톤으로 글을 작성하며, 개인의 성장과 경험을 중심으로 이야기를 풀어나갑니다.",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.content[0].text

    @staticmethod
    async def generate_blog_content(
        reflection_id: int,
        db: Session,
        provider: LLMProvider,
        include_images: bool = True,
        force_regenerate: bool = False,
        additional_prompt: str = None
    ) -> Dict[str, Any]:
        """블로그 콘텐츠 생성 메인 함수"""

        # 회고 데이터 조회
        reflection = db.query(DailyReflection).filter(
            DailyReflection.id == reflection_id
        ).first()

        if not reflection:
            raise ValueError(f"회고를 찾을 수 없습니다: ID {reflection_id}")

        # 캐시된 콘텐츠 확인 (재생성 강제가 아닌 경우)
        if not force_regenerate:
            cached_content = LLMBlogService.get_cached_blog_content(reflection_id, db)
            if cached_content:
                return {
                    "content": cached_content["content"],
                    "is_cached": True,
                    "generated_at": cached_content["generated_at"]
                }

        # 관련 할일 데이터 조회
        from sqlalchemy import and_, or_, func

        reflection_date = reflection.reflection_date

        todos = db.query(DailyTodo).filter(
            or_(
                # 완료된 할일: 완료한 날짜가 회고 날짜와 같음
                and_(
                    DailyTodo.is_completed == True,
                    func.date(DailyTodo.completed_at) == reflection_date
                ),
                # 미완료 할일: 예정된 날짜가 회고 날짜와 같음
                and_(
                    DailyTodo.is_completed == False,
                    DailyTodo.scheduled_date == reflection_date
                )
            )
        ).all()

        completed_todos = [todo for todo in todos if todo.is_completed]
        pending_todos = [todo for todo in todos if not todo.is_completed]

        # 해당 날짜의 메모들 조회
        from ..services.daily_memo_service import DailyMemoService
        daily_memos = DailyMemoService.get_memos_by_date(db, reflection_date)

        # 프롬프트 생성
        prompt = LLMBlogService.generate_blog_prompt(
            reflection=reflection,
            completed_todos=completed_todos,
            pending_todos=pending_todos,
            daily_memos=daily_memos,
            include_images=include_images,
            additional_prompt=additional_prompt
        )

        # LLM API 호출
        blog_content = await LLMBlogService.call_llm_api(
            provider=provider,
            prompt=prompt
        )

        # DB에 저장
        LLMBlogService.save_blog_content_to_db(
            reflection_id=reflection_id,
            content=blog_content,
            prompt=prompt,
            db=db
        )

        return {
            "content": blog_content,
            "is_cached": False,
            "generated_at": datetime.now()
        }

    @staticmethod
    def get_cached_blog_content(reflection_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """캐시된 블로그 콘텐츠 조회"""
        reflection = db.query(DailyReflection).filter(
            DailyReflection.id == reflection_id
        ).first()

        if not reflection or not reflection.generated_blog_content:
            return None

        return {
            "content": reflection.generated_blog_content,
            "generated_at": reflection.blog_generated_at,
            "prompt": reflection.blog_generation_prompt
        }

    @staticmethod
    def save_blog_content_to_db(
        reflection_id: int,
        content: str,
        prompt: str,
        db: Session
    ) -> None:
        """블로그 콘텐츠를 데이터베이스에 저장"""
        reflection = db.query(DailyReflection).filter(
            DailyReflection.id == reflection_id
        ).first()

        if not reflection:
            raise ValueError(f"회고를 찾을 수 없습니다: ID {reflection_id}")

        reflection.generated_blog_content = content
        reflection.blog_generation_prompt = prompt
        reflection.blog_generated_at = datetime.now()

        db.commit()
