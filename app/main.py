from fastapi import FastAPI, Request, HTTPException, Depends, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Union, Optional
from dotenv import load_dotenv
import logging

# .env 파일 로드 (환경변수 설정)
load_dotenv()

from .routers import daily  # 일상 Todo만 사용, 기존 복잡한 구조는 임시로 비활성화
from .routers import reflections  # 일일 회고 시스템
from .routers import journeys
from .core.database import get_db
from .core.config import settings
from .models.journey import Journey
from .models.todo import Todo, DailyTodo
from .services.daily_todo_service import DailyTodoService
from .core.timezone import get_current_date, format_date_for_display

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Daily Flow - 일상 흐름 관리", version="1.0.0")

# 앱 시작 시 환경 정보 출력
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info(f"🚀 서버 시작")
    logger.info(f"📍 환경: {settings.app_env.upper()}")
    logger.info(f"🗄️  데이터베이스: {settings.database_url}")
    logger.info(f"🐛 디버그 모드: {settings.debug}")
    logger.info("=" * 60)

# API 라우터 등록
app.include_router(daily.router)  # 일상 Todo API (메인)
app.include_router(reflections.router)  # 일일 회고 API
app.include_router(reflections.page_router)  # 일일 회고 페이지
app.include_router(journeys.router, prefix="/api")  # 여정 API
# TODO API는 daily.router로 대체됨

# 정적 파일 및 템플릿 설정
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# 템플릿 전역 변수 설정 - 모든 템플릿에서 환경 정보 사용 가능
templates.env.globals.update({
    "app_env": settings.app_env,
    "is_dev": settings.app_env == "dev",
    "database_url": settings.database_url
})

# 모든 템플릿에 공통 컨텍스트 추가하는 헬퍼 함수
def add_common_context(context: dict) -> dict:
    """모든 템플릿에 공통으로 필요한 컨텍스트 변수들을 추가합니다."""
    common = {
        "app_env": settings.app_env,
        "is_dev": settings.app_env == "dev",
        "database_url": settings.database_url
    }
    return {**common, **context}


# 에러 핸들러 - API와 페이지 구분
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> Union[JSONResponse, HTMLResponse]:
    # API 요청인 경우 JSON 응답
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"detail": exc.detail or "API 리소스를 찾을 수 없습니다."},
        )

    # 페이지 요청인 경우 HTML 응답
    return templates.TemplateResponse(
        request=request,
        name="errors/404.html",
        context=add_common_context({"detail": "페이지를 찾을 수 없습니다."}),
        status_code=404,
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> Union[JSONResponse, HTMLResponse]:
    # API 요청인 경우 JSON 응답
    if request.url.path.startswith("/api/"):
        detail = getattr(exc, "detail", None) or "서버 내부 오류가 발생했습니다."
        return JSONResponse(status_code=500, content={"detail": detail})

    # 페이지 요청인 경우 HTML 응답
    return templates.TemplateResponse(
        request=request,
        name="errors/500.html",
        context=add_common_context({"detail": "서버 내부 오류가 발생했습니다."}),
        status_code=500,
    )


# 페이지 라우터들
@app.get("/", response_class=HTMLResponse)
async def daily_todo_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """메인 페이지 - 오늘의 할 일"""
    try:
        # 오늘의 할 일 조회
        today_todos = DailyTodoService.get_today_todos(db)

        # 오늘의 요약 정보
        summary = DailyTodoService.get_today_summary(db)

        # 템플릿 데이터 구성
        from datetime import date
        today = get_current_date()
        today_str = format_date_for_display(today)

        # 각 할일에 경과일 정보 추가
        enhanced_todos = []
        for todo in today_todos:
            days_overdue = (today - todo.created_date).days

            # 지연 상태 계산
            if todo.scheduled_date and todo.scheduled_date > today:
                overdue_status = "scheduled"
            elif days_overdue == 0:
                overdue_status = "today"
            elif days_overdue > 0:
                overdue_status = "overdue"
            else:
                overdue_status = "today"

            # 경과일 텍스트 생성
            if days_overdue == 0:
                overdue_text = ""
            elif days_overdue == 1:
                overdue_text = "1일 지남"
            else:
                overdue_text = f"{days_overdue}일 지남"

            # 할일 객체에 추가 정보 설정
            todo.days_overdue = days_overdue
            todo.overdue_status = overdue_status
            todo.overdue_text = overdue_text
            enhanced_todos.append(todo)

        context = {
            "request": request,
            "today_todos": enhanced_todos,
            "summary": summary,
            "today_date": today_str,
            "page_title": "오늘의 할 일",
        }

        return templates.TemplateResponse(
            request=request, name="daily_todos.html", context=add_common_context(context)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오늘의 할 일 페이지 로딩 중 오류: {str(e)}")


@app.get("/journeys", response_class=HTMLResponse)
async def journey_management_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """통합 여정 관리 페이지"""
    try:
        # 여정 조회 (진행률순 정렬)
        journeys = db.query(Journey).order_by(Journey.status, Journey.start_date).all()

        # 각 여정의 실시간 진행률 및 할일 개수 계산
        journey_data = []
        for journey in journeys:
            # 여정별 할일 개수 계산 (Todo와 DailyTodo 모두 포함)
            journey_todos = db.query(Todo).filter(Todo.journey_id == journey.id).all()
            journey_daily_todos = db.query(DailyTodo).filter(DailyTodo.journey_id == journey.id).all()
            total_todos = len(journey_todos) + len(journey_daily_todos)
            completed_todos = len([t for t in journey_todos if t.is_completed]) + len([t for t in journey_daily_todos if t.is_completed])

            actual_progress = journey.calculate_actual_progress()
            journey_data.append({
                'journey': journey,
                'actual_progress': actual_progress,
                'total_todos': total_todos,
                'completed_todos': completed_todos
            })

        # 통계 계산
        from .models.journey import JourneyStatus
        active_journeys_count = (
            db.query(Journey)
            .filter(Journey.status.in_([JourneyStatus.ACTIVE, JourneyStatus.PLANNING]))
            .count()
        )

        # 전체 할일 개수 계산 (미완료)
        pending_todos_count = db.query(Todo).filter(Todo.is_completed == False).count()
        pending_daily_todos_count = db.query(DailyTodo).filter(DailyTodo.is_completed == False).count()
        total_pending_todos = pending_todos_count + pending_daily_todos_count

        # 전체 할일 개수 계산 (전체)
        total_todos = db.query(Todo).count() + db.query(DailyTodo).count()
        total_completed_todos = db.query(Todo).filter(Todo.is_completed == True).count() + db.query(DailyTodo).filter(DailyTodo.is_completed == True).count()

        context = {
            "request": request,
            "journey_data": journey_data,
            "active_journeys_count": active_journeys_count,
            "pending_todos_count": total_pending_todos,
            "total_todos": total_todos,
            "total_completed_todos": total_completed_todos,
        }
        return templates.TemplateResponse(
            request=request, name="project_management.html", context=add_common_context(context)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"여정 관리 페이지 로딩 중 오류: {str(e)}")


# 기존 대시보드 페이지 - 여정 관리로 리다이렉트
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_redirect():
    """대시보드 페이지를 여정 관리로 리다이렉트"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/journeys", status_code=301)


# 기존 projects 페이지 - 여정으로 리다이렉트
@app.get("/projects", response_class=HTMLResponse)
async def projects_redirect():
    """프로젝트 페이지를 여정으로 리다이렉트"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/journeys", status_code=301)


@app.get("/journeys/{journey_id}", response_class=HTMLResponse)
async def journey_detail_page(
    request: Request, journey_id: int, db: Session = Depends(get_db)
) -> HTMLResponse:
    """여정 상세 페이지"""
    try:
        # 실제 데이터베이스에서 여정 조회
        journey = db.query(Journey).filter(Journey.id == journey_id).first()
        if not journey:
            raise HTTPException(status_code=404, detail="여정을 찾을 수 없습니다")

        # 해당 여정의 TODO 목록 조회 (Todo와 DailyTodo 모두)
        legacy_todos = db.query(Todo).filter(Todo.journey_id == journey_id).all()
        daily_todos = db.query(DailyTodo).filter(DailyTodo.journey_id == journey_id).all()

        # 두 테이블의 데이터를 합쳐서 통합된 목록 생성
        todos = []

        # 기존 Todo 데이터 추가
        for todo in legacy_todos:
            todos.append({
                'id': todo.id,
                'title': todo.title,
                'description': todo.description,
                'is_completed': todo.is_completed,
                'completed_at': todo.completed_at,
                'created_at': todo.created_at,
                'category': 'legacy',  # 구분용
                'estimated_time': None,
                'actual_time': None,
                'priority': 'medium',  # 기본값
                'source': 'todo'
            })

        # DailyTodo 데이터 추가
        for todo in daily_todos:
            todos.append({
                'id': todo.id,
                'title': todo.title,
                'description': todo.description,
                'is_completed': todo.is_completed,
                'completed_at': todo.completed_at,
                'created_at': todo.created_at,
                'category': todo.category.value if todo.category else '기타',
                'estimated_time': todo.estimated_minutes,
                'actual_time': todo.actual_minutes,
                'priority': 'medium',  # 기본값 (DailyTodo에는 priority 없음)
                'source': 'daily_todo'
            })

        completed_todos_count = len([t for t in todos if t['is_completed']])
        total_todos_count = len(todos)

        # 할일 기준 진행률 계산 (실제 완료도 반영)
        calculated_progress = (completed_todos_count / total_todos_count * 100) if total_todos_count > 0 else 0.0

        context = {
            "request": request,
            "journey": journey,
            "todos": todos,
            "completed_todos_count": completed_todos_count,
            "total_todos_count": total_todos_count,
            "calculated_progress": round(calculated_progress, 1),
        }
        return templates.TemplateResponse(
            request=request, name="journey_detail.html", context=add_common_context(context)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"여정 상세 페이지 로딩 중 오류: {str(e)}"
        )


# 기존 TODO 페이지 - 여정 관리로 리다이렉트
@app.get("/todos", response_class=HTMLResponse)
async def todos_redirect():
    """TODO 페이지를 여정 관리로 리다이렉트"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/journeys", status_code=301)


# T1-15: 실시간 검색 엔드포인트
@app.get("/api/search", response_class=HTMLResponse)
async def search(
    request: Request,
    q: Optional[str] = Query(None, description="검색 쿼리"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """실시간 검색 결과를 반환합니다 (HTMX용)."""
    try:
        search_results = {"journeys": [], "todos": []}

        # 검색어가 있는 경우에만 검색 수행
        if q and len(q.strip()) > 0:
            search_query = f"%{q.strip()}%"

            # 여정 검색 (제목, 설명에서)
            journeys = (
                db.query(Journey)
                .filter(
                    or_(
                        Journey.title.ilike(search_query),
                        Journey.description.ilike(search_query),
                    )
                )
                .limit(5)
                .all()
            )

            # TODO 검색 (제목, 설명에서)
            todos = (
                db.query(Todo)
                .filter(
                    or_(
                        Todo.title.ilike(search_query),
                        Todo.description.ilike(search_query),
                    )
                )
                .limit(5)
                .all()
            )

            # 검색 결과 구성 (할일 개수 기반)
            journey_search_results = []
            for m in journeys:
                # 여정별 할일 개수 계산
                m_todos = db.query(Todo).filter(Todo.journey_id == m.id).all()
                m_daily_todos = db.query(DailyTodo).filter(DailyTodo.journey_id == m.id).all()
                total_todos = len(m_todos) + len(m_daily_todos)
                completed_todos = len([t for t in m_todos if t.is_completed]) + len([t for t in m_daily_todos if t.is_completed])

                journey_search_results.append({
                    "id": m.id,
                    "title": m.title,
                    "description": m.description,
                    "total_todos": total_todos,
                    "completed_todos": completed_todos,
                })

            search_results["journeys"] = journey_search_results

            search_results["todos"] = [
                {
                    "id": t.id,
                    "title": t.title,
                    "description": t.description,
                    "is_completed": t.is_completed,
                    "journey_title": t.journey.title if t.journey else "없음",
                }
                for t in todos
            ]

        return templates.TemplateResponse(
            "partials/search_results.html",
            add_common_context({"request": request, "search_results": search_results, "query": q or ""})
        )

    except Exception as e:
        # 검색 오류 시 빈 결과 반환
        return templates.TemplateResponse(
            "partials/search_results.html",
            add_common_context({
                "request": request,
                "search_results": {"journeys": [], "todos": []},
                "query": q or "",
                "error": f"검색 중 오류가 발생했습니다: {str(e)}",
            })
        )


@app.get("/reflection-history", response_class=HTMLResponse)
async def reflection_history_page(
    request: Request,
    week_start: Optional[str] = Query(None, description="주간 시작일 (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
) -> HTMLResponse:
    """회고 히스토리 통합 페이지"""
    try:
        # 주간 통계 계산
        from datetime import date, timedelta
        today = get_current_date()

        # 특정 주가 지정되었으면 해당 주, 아니면 이번 주
        if week_start:
            try:
                target_date = date.fromisoformat(week_start)
                monday = target_date - timedelta(days=target_date.weekday())
            except ValueError:
                monday = today - timedelta(days=today.weekday())
        else:
            monday = today - timedelta(days=today.weekday())

        week_dates = [monday + timedelta(days=i) for i in range(7)]

        # 이번 주의 일별 할일 통계 및 회고 데이터 (회고 기반 완료율 우선 사용)
        from .models.daily_reflection import DailyReflection
        weekly_stats = []
        total_satisfaction = 0
        total_energy = 0
        reflection_count = 0

        for day in week_dates:
            # 해당 날짜의 회고 데이터 확인
            reflection = db.query(DailyReflection).filter(DailyReflection.reflection_date == day).first()

            # 해당 날짜의 할일 목록 (아코디언에서 표시용)
            day_todos = db.query(DailyTodo).filter(DailyTodo.created_date == day).all()

            if reflection:
                # 회고가 있으면 회고 시점의 정확한 데이터 사용 (소급 적용 방지)
                total = reflection.total_todos
                completed = reflection.completed_todos
                completion_rate = reflection.completion_rate

                # 만족도, 에너지 통계용
                if reflection.satisfaction_score:
                    total_satisfaction += reflection.satisfaction_score
                    reflection_count += 1
                if reflection.energy_level:
                    total_energy += reflection.energy_level
            else:
                # 회고가 없으면 실시간 계산 (오늘이거나 회고 작성 전)
                completed = len([t for t in day_todos if t.is_completed])
                total = len(day_todos)
                completion_rate = (completed / total * 100) if total > 0 else 0

            weekly_stats.append({
                "date": day,
                "day_name": day.strftime("%a"),
                "day_korean": ["월", "화", "수", "목", "금", "토", "일"][day.weekday()],
                "total_todos": total,
                "completed_todos": completed,
                "completion_rate": completion_rate,
                "is_today": day == today,
                "has_reflection": reflection is not None,
                "reflection": reflection,
                "todos": day_todos,
                "satisfaction_score": reflection.satisfaction_score if reflection else None,
                "energy_level": reflection.energy_level if reflection else None,
                "reflection_text": reflection.reflection_text if reflection else None
            })

        # 주간 여정 진행률 (실시간 계산)
        from .models.journey import JourneyStatus
        journeys = db.query(Journey).filter(Journey.status.in_([JourneyStatus.ACTIVE, JourneyStatus.PLANNING])).all()

        # 각 여정의 실시간 진행률 및 할일 개수 계산
        journey_data = []
        for journey in journeys:
            # 여정별 할일 개수 계산 (Todo와 DailyTodo 모두 포함)
            journey_todos = db.query(Todo).filter(Todo.journey_id == journey.id).all()
            journey_daily_todos = db.query(DailyTodo).filter(DailyTodo.journey_id == journey.id).all()
            total_todos = len(journey_todos) + len(journey_daily_todos)
            completed_todos = len([t for t in journey_todos if t.is_completed]) + len([t for t in journey_daily_todos if t.is_completed])

            actual_progress = journey.calculate_actual_progress()
            journey_data.append({
                'journey': journey,
                'actual_progress': actual_progress,
                'total_todos': total_todos,
                'completed_todos': completed_todos
            })

        # 네비게이션 정보
        prev_monday = monday - timedelta(days=7)
        next_monday = monday + timedelta(days=7)

        # 주간 평균 계산
        avg_satisfaction = (total_satisfaction / reflection_count) if reflection_count > 0 else 0
        avg_energy = (total_energy / reflection_count) if reflection_count > 0 else 0

        context = {
            "request": request,
            "weekly_stats": weekly_stats,
            "journey_data": journey_data,
            "current_week": f"{monday.strftime('%Y년 %m월 %d일')} - {week_dates[-1].strftime('%m월 %d일')}",
            "today": today,
            "monday": monday,
            "prev_monday": prev_monday,
            "next_monday": next_monday,
            "is_current_week": monday <= today <= week_dates[-1],
            "week_averages": {
                "avg_satisfaction": avg_satisfaction,
                "avg_energy": avg_energy,
                "reflection_count": reflection_count
            }
        }

        return templates.TemplateResponse(
            request=request, name="reflection_history.html", context=add_common_context(context)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"회고 히스토리 페이지 로딩 중 오류: {str(e)}")


@app.get("/api/reflection-day/{date_str}")
async def get_day_reflection_detail(
    date_str: str,
    db: Session = Depends(get_db)
):
    """특정 날짜의 회고 및 할일 상세 정보 조회 (아코디언용)"""
    try:
        from datetime import date
        from .models.daily_reflection import DailyReflection

        # 날짜 파싱
        target_date = date.fromisoformat(date_str)

        # 회고 데이터 조회
        reflection = db.query(DailyReflection).filter(
            DailyReflection.reflection_date == target_date
        ).first()

        # 할일 목록 조회
        day_todos = db.query(DailyTodo).filter(
            DailyTodo.created_date == target_date
        ).all()

        # 할일을 완료/미완료로 분류하고 소급 완료 여부 확인
        completed_todos = [todo for todo in day_todos if todo.is_completed]
        pending_todos = [todo for todo in day_todos if not todo.is_completed]

        # 회고가 있는 경우 소급 완료된 할일 구분
        retroactively_completed = []
        completed_on_time = []

        if reflection:
            # 회고 시점 기준 완료된 할일 수와 현재 완료된 할일 수 비교
            reflection_completed_count = reflection.completed_todos
            current_completed_count = len(completed_todos)

            if current_completed_count > reflection_completed_count:
                # 소급 완료된 할일이 있음
                # 완료 시점으로 구분 (회고 생성일 이후 완료된 것들)
                reflection_created_date = reflection.created_at.date() if reflection.created_at else target_date

                for todo in completed_todos:
                    if todo.completed_at:
                        todo_completed_date = todo.completed_at.date()
                        if todo_completed_date > reflection_created_date:
                            retroactively_completed.append(todo)
                        else:
                            completed_on_time.append(todo)
                    else:
                        # completed_at이 없는 경우 회고 시점 완료로 간주
                        completed_on_time.append(todo)
            else:
                completed_on_time = completed_todos
        else:
            completed_on_time = completed_todos

        return {
            "date": date_str,
            "has_reflection": reflection is not None,
            "reflection": {
                "id": reflection.id if reflection else None,
                "reflection_text": reflection.reflection_text if reflection else None,
                "satisfaction_score": reflection.satisfaction_score if reflection else None,
                "energy_level": reflection.energy_level if reflection else None,
                "completion_rate": reflection.completion_rate if reflection else None,
                "total_todos": reflection.total_todos if reflection else len(day_todos),
                "completed_todos": reflection.completed_todos if reflection else len(completed_todos),
                "created_at": reflection.created_at.isoformat() if reflection and reflection.created_at else None,
            },
            "todos": {
                "completed_on_time": [
                    {
                        "id": todo.id,
                        "title": todo.title,
                        "category": todo.category.value,
                        "completion_reflection": todo.completion_reflection,
                        "completion_image_path": todo.completion_image_path,
                        "journey_id": todo.journey_id,
                        "completed_at": todo.completed_at.isoformat() if todo.completed_at else None,
                    }
                    for todo in completed_on_time
                ],
                "retroactively_completed": [
                    {
                        "id": todo.id,
                        "title": todo.title,
                        "category": todo.category.value,
                        "completion_reflection": todo.completion_reflection,
                        "completion_image_path": todo.completion_image_path,
                        "journey_id": todo.journey_id,
                        "completed_at": todo.completed_at.isoformat() if todo.completed_at else None,
                    }
                    for todo in retroactively_completed
                ],
                "pending": [
                    {
                        "id": todo.id,
                        "title": todo.title,
                        "category": todo.category.value,
                        "journey_id": todo.journey_id
                    }
                    for todo in pending_todos
                ]
            }
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 날짜 형식입니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 조회 중 오류: {str(e)}")


@app.get("/weekly", response_class=HTMLResponse)
async def redirect_to_reflection_history(
    request: Request,
    week_start: Optional[str] = Query(None, description="주간 시작일 (YYYY-MM-DD)")
):
    """기존 주간 계획 페이지를 회고 히스토리로 리다이렉트"""
    from fastapi.responses import RedirectResponse

    # 주간 시작일이 있으면 파라미터로 전달
    if week_start:
        return RedirectResponse(url=f"/reflection-history?week_start={week_start}", status_code=301)
    else:
        return RedirectResponse(url="/reflection-history", status_code=301)


@app.get("/health")
async def health_check() -> dict:
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "message": "서버가 정상적으로 작동 중입니다."}
