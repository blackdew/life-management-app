# 메인(프로덕션) 환경 서버 실행 스크립트 (Windows PowerShell)
# 사용법: .\scripts\run_main.ps1

# 메인 DB 사용 정보 출력
Write-Host "🚀 메인(프로덕션) 환경 서버를 시작합니다..." -ForegroundColor Green
Write-Host "📍 환경: MAIN (PRODUCTION)" -ForegroundColor Yellow
Write-Host "🗄️  DB: data\app.db" -ForegroundColor Cyan
Write-Host "🌐 포트: 8001" -ForegroundColor Cyan
Write-Host "⚠️  디버그 모드: OFF" -ForegroundColor Yellow
Write-Host ""

# Uvicorn 서버 실행 (프로덕션 모드 - reload 없음)
# 환경변수 설정 후 실행
$env:APP_ENV = "main"
$env:DEBUG = "false"
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
