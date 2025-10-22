# 개발 환경 서버 실행 스크립트 (Windows PowerShell)
# 사용법: .\scripts\run_dev.ps1

# 개발 DB 사용 정보 출력
Write-Host "🚀 개발 환경 서버를 시작합니다..." -ForegroundColor Green
Write-Host "📍 환경: DEV" -ForegroundColor Cyan
Write-Host "🗄️  DB: data\app_dev.db" -ForegroundColor Cyan
Write-Host "🌐 포트: 8000" -ForegroundColor Cyan
Write-Host ""

# Uvicorn 서버 실행 (개발 모드)
# 환경변수 설정 후 실행
$env:APP_ENV = "dev"
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
