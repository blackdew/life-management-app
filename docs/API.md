# 🔌 Daily Flow API 문서

## 🎯 **개요**

Daily Flow의 RESTful API 엔드포인트들을 설명합니다.
모든 API는 Form Data(`application/x-www-form-urlencoded`) 형식을 사용합니다.

**Base URL**: `http://localhost:8000`

---

## 📋 **할 일 관리 API**

### **1. 빠른 할 일 추가**
```http
POST /api/daily/todos/quick
Content-Type: application/x-www-form-urlencoded

title=할일제목
```

**응답 예시:**
```json
{
  "id": 8,
  "title": "저녁 회고 및 내일 계획",
  "is_completed": false,
  "category": "기타"
}
```

### **2. 상세 할 일 추가**
```http
POST /api/daily/todos
Content-Type: application/x-www-form-urlencoded

title=캐글 Hull Tactical 대회 EDA 시작
description=데이터 탐색적 분석 및 초기 베이스라인 모델 구상
category=업무
journey_id=4
estimated_minutes=180
```

**응답 예시:**
```json
{
  "id": 5,
  "title": "캐글 Hull Tactical 대회 EDA 시작",
  "notes": null,
  "category": "업무",
  "is_completed": false,
  "created_at": "2025-09-28T05:29:40"
}
```

### **3. 할 일 완료/미완료 토글 (기본)**
```http
PATCH /api/daily/todos/{todo_id}/toggle
```

### **4. 회고와 함께 할 일 완료**
```http
PATCH /api/daily/todos/{todo_id}/complete
Content-Type: application/x-www-form-urlencoded

reflection=오늘은 더 의식적으로 선택하려고 노력했고, 특히 도파민 유혹을 이겨내는 데 집중했습니다.
```

**응답 예시:**
```json
{
  "id": 6,
  "title": "아침 메타인지 체크 및 오늘 목표 설정",
  "is_completed": true,
  "completion_reflection": "오늘은 더 의식적으로 선택하려고 노력했고, 특히 도파민 유혹을 이겨내는 데 집중했습니다.",
  "completed_at": "2025-09-28T14:36:07.970666"
}
```

### **5. 할 일 미루기 (일정 재조정)**
```http
PATCH /api/daily/todos/{todo_id}/reschedule
Content-Type: application/x-www-form-urlencoded

new_date=2024-09-29
```

**응답 예시:**
```json
{
  "id": 4,
  "title": "문서 작성하기",
  "scheduled_date": "2024-09-29",
  "created_date": "2024-09-29"
}
```

### **6. 할 일 수정**
```http
PUT /api/daily/todos/{todo_id}
Content-Type: application/x-www-form-urlencoded

title=수정된 할 일 제목
description=수정된 상세 내용
category=학습
estimated_minutes=90
```

**응답 예시:**
```json
{
  "id": 7,
  "title": "수정된 할 일 제목",
  "description": "수정된 상세 내용",
  "notes": null,
  "category": "학습",
  "journey_id": null
}
```

### **7. 할 일 삭제**
```http
DELETE /api/daily/todos/{todo_id}
```

**응답 예시:**
```json
{
  "message": "할 일이 삭제되었습니다"
}
```

---

## 📊 **조회 API**

### **1. 오늘의 할 일 목록**
```http
GET /api/daily/todos/today
```

**📈 새로운 기능**: 미완료 작업 자동 이월 및 경과일 표시

**응답 예시:**
```json
{
  "todos": [
    {
      "id": 5,
      "title": "캐글 Hull Tactical 대회 EDA 시작",
      "notes": null,
      "category": "업무",
      "is_completed": false,
      "completed_at": null,
      "estimated_minutes": 180,
      "actual_minutes": null,
      "days_overdue": 3,
      "overdue_status": "overdue",
      "created_date": "2025-10-06",
      "scheduled_date": "2025-10-06"
    },
    {
      "id": 6,
      "title": "아침 메타인지 체크 및 오늘 목표 설정",
      "notes": null,
      "category": "개인",
      "is_completed": true,
      "completed_at": "2025-09-28T14:36:07.970666",
      "estimated_minutes": 15,
      "actual_minutes": null,
      "days_overdue": 0,
      "overdue_status": "today",
      "created_date": "2025-10-09",
      "scheduled_date": null
    }
  ]
}
```

**새로운 응답 필드:**
- `days_overdue`: 생성일로부터 경과일 수 (0 = 오늘, 1+ = 지연됨)
- `overdue_status`: 지연 상태 (`"today"`, `"overdue"`, `"scheduled"`)
- `created_date`: 할일 생성일 (ISO 날짜 형식)
- `scheduled_date`: 예정일 (ISO 날짜 형식, null 가능)

**자동 이월 동작:**
- 과거 미완료 할일이 오늘 할일에 자동 포함됩니다
- 과거 완료된 할일은 제외됩니다
- 미래 예정 할일은 해당 날짜까지 표시되지 않습니다

### **2. 오늘의 요약 정보**
```http
GET /api/daily/summary/today
```

**응답 예시:**
```json
{
  "total": 4,
  "completed": 1,
  "pending": 3,
  "completion_rate": 25.0
}
```

### **3. 주간 요약 정보**
```http
GET /api/daily/summary/weekly
```

### **4. 카테고리별 요약**
```http
GET /api/daily/summary/categories
```

### **5. 여정 목록 (할 일 추가용)**
```http
GET /api/daily/journeys
```

**응답 예시:**
```json
{
  "journeys": [
    {
      "id": 1,
      "title": "M1: 시동 및 루틴 고정",
      "status": "진행중",
      "total_todos": 10,
      "completed_todos": 8
    },
    {
      "id": 4,
      "title": "💰 주식 영역: Hull Tactical + 투자봇",
      "status": "진행중",
      "total_todos": 12,
      "completed_todos": 3
    },
    {
      "id": 7,
      "title": "🧠 내면 관리: 메타인지 + 통제 + 성장",
      "status": "진행중",
      "total_todos": 5,
      "completed_todos": 2
    }
  ]
}
```

---

## 🔧 **시스템 API**

### **헬스 체크**
```http
GET /health
```

**응답 예시:**
```json
{
  "status": "healthy",
  "message": "서버가 정상적으로 작동 중입니다."
}
```

---

## 🌐 **페이지 라우터**

### **메인 페이지**
```http
GET /
```
오늘의 할 일 관리 메인 페이지

### **대시보드**
```http
GET /dashboard
```
전체 현황 대시보드

### **여정 목록**
```http
GET /journeys
```
여정 관리 페이지

### **TODO 목록**
```http
GET /todos
```
전체 할 일 관리 페이지

---

## 📝 **데이터 형식**

### **할 일 (DailyTodo) 필드**
- `id`: 고유 식별자
- `title`: 할 일 제목 (필수)
- `description`: 상세 내용 (선택)
- `notes`: 추가 메모 (선택)
- `category`: 카테고리 (`기타`, `업무`, `개인`, `학습`, `건강`, `취미`)
- `is_completed`: 완료 여부
- `completion_reflection`: 완료 후 회고 (선택)
- `estimated_minutes`: 예상 소요시간 (분)
- `actual_minutes`: 실제 소요시간 (분)
- `scheduled_date`: 예정 일자 (미루기용)
- `created_date`: 생성 일자
- `created_at`: 생성 시간
- `completed_at`: 완료 시간
- `journey_id`: 연결된 여정 ID (선택)

### **여정 (Journey) 필드**
- `id`: 고유 식별자
- `title`: 여정 제목
- `description`: 상세 설명
- `status`: 상태 (`계획중`, `진행중`, `완료`, `일시중지`)
- `total_todos`: 전체 할일 개수
- `completed_todos`: 완료된 할일 개수
- `start_date`: 시작 예정일
- `end_date`: 종료 예정일

---

## ⚠️ **에러 응답**

모든 API는 표준 HTTP 상태 코드를 사용합니다:

- `200`: 성공
- `400`: 잘못된 요청 (필수 필드 누락 등)
- `404`: 리소스를 찾을 수 없음
- `500`: 서버 내부 오류

**에러 응답 예시:**
```json
{
  "detail": "할 일을 찾을 수 없습니다"
}
```

---

## 🧪 **테스트 예시**

### **cURL로 테스트**
```bash
# 빠른 할 일 추가
curl -X POST http://localhost:8000/api/daily/todos/quick \
  -d 'title=테스트 할 일'

# 상세 할 일 추가
curl -X POST http://localhost:8000/api/daily/todos \
  -d 'title=상세 할 일' \
  -d 'description=상세 설명' \
  -d 'category=업무' \
  -d 'journey_id=1' \
  -d 'estimated_minutes=60'

# 회고와 함께 완료
curl -X PATCH http://localhost:8000/api/daily/todos/1/complete \
  -d 'reflection=오늘 배운 점과 성과'

# 오늘의 할 일 조회
curl http://localhost:8000/api/daily/todos/today
```

### **JavaScript/Fetch로 테스트**
```javascript
// 할 일 추가
const formData = new FormData();
formData.append('title', '새로운 할 일');
formData.append('description', '상세한 설명');
formData.append('journey_id', '1');

const response = await fetch('/api/daily/todos', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result);
```

---

## 🎯 **사용 팁**

1. **Form Data 형식**: 모든 POST/PATCH/PUT 요청은 `application/x-www-form-urlencoded` 형식 사용
2. **날짜 형식**: `YYYY-MM-DD` 형식 사용 (예: `2024-09-28`)
3. **여정 연결**: `journey_id`는 선택사항이며, 비어두면 여정 없이 생성
4. **회고 기능**: 완료 시 `reflection` 필드로 의미있는 회고 기록 권장
5. **에러 처리**: API 응답의 `detail` 필드에서 에러 메시지 확인

---

*Daily Flow API로 더 나은 일상 관리를 경험해보세요!* 🚀✨