# ✅ 시각화 대시보드 구현 작업 목록 (TODO)

## 📋 진행 상황 요약
- **전체 진행률**: 0% (0/40)
- **현재 단계**: Phase 0 - 준비
- **예상 완료일**: TBD
- **마지막 업데이트**: 2025-10-16

---

## 🎯 Phase 0: 준비 및 설계 (0/3)

### 문서화
- [x] PRD.md 작성
- [x] TODO.md 작성 (현재 문서)
- [ ] API 명세서 상세화

---

## 🔧 Phase 1: 백엔드 구현 (0/15)

### 1.1 데이터 모델 및 서비스 레이어
- [ ] **InsightsService 생성** (`app/services/insights_service.py`)
  - [ ] `get_completion_trend(db, days)` - 완료율 트렌드 데이터 반환
  - [ ] `get_satisfaction_energy_trend(db, days)` - 만족도/에너지 트렌드 반환
  - [ ] `get_weekday_pattern(db, weeks)` - 요일별 완료율 패턴 반환
  - [ ] `get_category_distribution(db, days)` - 카테고리별 분포 반환
  - [ ] `get_journey_progress_summary(db)` - 진행 중인 여정 통계 반환
  - [ ] `get_weekly_comparison(db)` - 이번 주 vs 지난 주 비교 반환

### 1.2 API 엔드포인트
- [ ] **InsightsRouter 생성** (`app/routers/insights.py`)
  - [ ] `GET /api/insights/completion-trend` - 완료율 트렌드 API
  - [ ] `GET /api/insights/satisfaction-energy-trend` - 만족도/에너지 API
  - [ ] `GET /api/insights/weekday-pattern` - 요일별 패턴 API
  - [ ] `GET /api/insights/category-distribution` - 카테고리 분포 API
  - [ ] `GET /api/insights/journey-progress` - 여정 진행 API
  - [ ] `GET /api/insights/weekly-comparison` - 주간 비교 API

### 1.3 라우터 등록
- [ ] `app/main.py`에 InsightsRouter 등록
- [ ] API 문서 자동 생성 확인 (`/docs` 페이지)

---

## 🎨 Phase 2: 프론트엔드 구현 (0/12)

### 2.1 대시보드 페이지 생성
- [ ] **템플릿 파일 생성** (`app/templates/insights.html`)
  - [ ] 기본 레이아웃 (헤더, 네비게이션)
  - [ ] 날짜 범위 선택 드롭다운 (7일/30일/90일)
  - [ ] 반응형 그리드 레이아웃 (Tailwind CSS)

### 2.2 Chart.js 통합
- [ ] Chart.js CDN 추가 (v4.x)
- [ ] **완료율 트렌드 차트**
  - [ ] 라인 차트 컨테이너 (`<canvas id="completion-trend-chart">`)
  - [ ] API 호출 및 데이터 바인딩
  - [ ] 평균선 표시
  - [ ] 툴팁 커스터마이징
- [ ] **만족도/에너지 트렌드 차트**
  - [ ] 듀얼 라인 차트 컨테이너
  - [ ] 두 개의 데이터셋 설정 (만족도: 노란색, 에너지: 파란색)
- [ ] **여정 진행 카드**
  - [ ] 프로그레스 바 컴포넌트
  - [ ] 여정 목록 렌더링
- [ ] **요일별 히트맵**
  - [ ] Chart.js Matrix 차트 또는 커스텀 히트맵
- [ ] **카테고리 도넛 차트**
  - [ ] 도넛 차트 컨테이너
  - [ ] 카테고리별 색상 매핑
- [ ] **주간 비교 카드**
  - [ ] 이번 주/지난 주 통계 표시
  - [ ] 변화량 아이콘 (↑/↓)

### 2.3 인터랙션 구현
- [ ] 날짜 범위 변경 시 차트 업데이트
- [ ] 차트 호버 시 툴팁 표시
- [ ] 차트 클릭 시 상세보기 (회고 페이지 이동)
- [ ] 로딩 상태 스켈레톤 UI

---

## 🔗 Phase 3: 통합 및 라우팅 (0/4)

### 3.1 페이지 라우팅
- [ ] `app/main.py`에 `/insights` 페이지 라우트 추가
  ```python
  @app.get("/insights", response_class=HTMLResponse)
  async def insights_page(request: Request):
      return templates.TemplateResponse(request, "insights.html")
  ```
- [ ] 네비게이션 메뉴에 "📊 인사이트" 링크 추가
  - [ ] `app/templates/partials/navigation.html` 수정
  - [ ] 데스크탑 사이드바
  - [ ] 모바일 하단 네비게이션

### 3.2 환경 설정
- [ ] 개발 환경 배너 표시 (`app_env` 변수 전달)
- [ ] 템플릿 컨텍스트 헬퍼 적용

---

## 🧪 Phase 4: 테스트 (0/6)

### 4.1 백엔드 테스트
- [ ] **InsightsService 단위 테스트** (`tests/services/test_insights_service.py`)
  - [ ] `test_get_completion_trend()` - 트렌드 데이터 검증
  - [ ] `test_get_weekday_pattern()` - 요일별 패턴 검증
  - [ ] `test_get_weekly_comparison()` - 주간 비교 검증

### 4.2 API 테스트
- [ ] **API 엔드포인트 테스트** (`tests/routers/test_insights_endpoints.py`)
  - [ ] `test_completion_trend_api()` - 완료율 API 응답 검증
  - [ ] `test_journey_progress_api()` - 여정 진행 API 응답 검증

### 4.3 프론트엔드 테스트
- [ ] 브라우저 호환성 테스트 (Chrome, Safari, Firefox)
- [ ] 반응형 테스트 (모바일, 태블릿, 데스크탑)

---

## 🚀 Phase 5: 최적화 및 배포 (0/5)

### 5.1 성능 최적화
- [ ] DB 쿼리 인덱스 추가 (`DailyReflection.reflection_date`)
- [ ] API 응답 시간 측정 및 개선 (목표: 300ms 이내)
- [ ] 차트 렌더링 애니메이션 최적화

### 5.2 UX 개선
- [ ] 인사이트 메시지 자동 생성 로직
  - [ ] "완료율이 지난 주보다 12% 향상되었어요!"
  - [ ] "수요일이 가장 생산적이에요!"
- [ ] 빈 데이터 상태 처리 (Empty State UI)

### 5.3 문서 업데이트
- [ ] API.md에 새 엔드포인트 추가
- [ ] PROJECT_STATUS.md 업데이트

---

## 📝 세부 구현 가이드

### 백엔드 구현 예시

#### InsightsService 메서드 구조
```python
class InsightsService:
    @staticmethod
    def get_completion_trend(db: Session, days: int = 30) -> dict:
        """완료율 트렌드 데이터"""
        end_date = get_current_date()
        start_date = end_date - timedelta(days=days)

        reflections = db.query(DailyReflection).filter(
            DailyReflection.reflection_date >= start_date,
            DailyReflection.reflection_date <= end_date
        ).order_by(DailyReflection.reflection_date.asc()).all()

        dates = [r.reflection_date.isoformat() for r in reflections]
        rates = [r.completion_rate for r in reflections]
        avg = sum(rates) / len(rates) if rates else 0

        return {
            "dates": dates,
            "rates": rates,
            "average": round(avg, 1)
        }
```

### 프론트엔드 구현 예시

#### Chart.js 라인 차트
```javascript
async function loadCompletionTrendChart(days = 30) {
    const response = await fetch(`/api/insights/completion-trend?days=${days}`);
    const data = await response.json();

    const ctx = document.getElementById('completion-trend-chart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.dates,
            datasets: [{
                label: '완료율 (%)',
                data: data.rates,
                borderColor: '#10B981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: '완료율 트렌드' },
                tooltip: { mode: 'index', intersect: false }
            }
        }
    });
}
```

---

## 🔄 작업 진행 상황 업데이트 규칙

### 체크 표시
- `[ ]` - 미완료
- `[x]` - 완료
- `[~]` - 진행 중 (선택적)

### 커밋 메시지 규칙
```bash
# 예시
git commit -m "✨ feat: InsightsService 완료율 트렌드 메서드 구현"
git commit -m "🎨 ui: 대시보드 페이지 기본 레이아웃 추가"
git commit -m "🧪 test: InsightsService 단위 테스트 추가"
```

---

## 📊 마일스톤

| Phase | 예상 소요 시간 | 목표 완료일 | 상태 |
|-------|-------------|----------|-----|
| Phase 0 | 1시간 | 2025-10-16 | ✅ 완료 |
| Phase 1 | 4시간 | TBD | ⏳ 대기 |
| Phase 2 | 5시간 | TBD | ⏳ 대기 |
| Phase 3 | 1시간 | TBD | ⏳ 대기 |
| Phase 4 | 3시간 | TBD | ⏳ 대기 |
| Phase 5 | 2시간 | TBD | ⏳ 대기 |
| **총계** | **16시간** | TBD | **진행 중** |

---

## 🐛 알려진 이슈 및 제약사항
- 없음 (새 기능 개발)

---

## 💡 추후 개선 아이디어
- [ ] 목표 설정 기능 (예: 이번 달 완료율 80% 목표)
- [ ] 주간/월간 리포트 PDF 내보내기
- [ ] 여정별 타임라인 상세 차트
- [ ] AI 기반 개인화 인사이트 메시지
- [ ] 데이터 필터링 (특정 카테고리만 보기)

---

## 📚 참고 자료
- [Chart.js 공식 문서](https://www.chartjs.org/docs/latest/)
- [Tailwind CSS Grid 가이드](https://tailwindcss.com/docs/grid-template-columns)
- [FastAPI 응답 모델](https://fastapi.tiangolo.com/tutorial/response-model/)
- [PRD.md](./PRD.md) - 제품 요구사항 문서

---

**다음 작업**: Phase 1 시작 - InsightsService 구현
**담당자**: TBD
**질문/이슈**: GitHub Issues 또는 팀 채널에 작성
