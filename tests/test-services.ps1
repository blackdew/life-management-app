# 서비스 로직 테스트 분리 실행 스크립트 (Windows PowerShell)
# async 이벤트 루프 충돌을 피하기 위해 서비스 테스트와 API 테스트를 분리 실행

# 에러 발생 시 중단
$ErrorActionPreference = "Stop"

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "🧪 서비스 로직 테스트 (async 지원)" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "FastAPI TestClient 없이 실행하여 이벤트 루프 충돌 방지"
Write-Host ""

# 서비스 테스트만 실행 (async 테스트 포함)
uv run pytest tests\services\ -v --tb=short --cov=app\services --cov-report=term-missing
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ 서비스 테스트 실패!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "🌐 API 및 통합 테스트" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "FastAPI TestClient 사용, async 서비스 테스트는 skip"
Write-Host ""

# API, E2E, 모델 테스트 실행
uv run pytest tests\api\ tests\e2e\ tests\models\ -v --tb=short
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ API/통합 테스트 실패!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "✅ 모든 테스트 완료" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "서비스 로직: 실제 async 테스트 포함"
Write-Host "API/E2E: HTTP 인터페이스 및 시나리오 테스트"
Write-Host ""
