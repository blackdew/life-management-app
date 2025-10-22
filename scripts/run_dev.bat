@echo off
REM 개발 환경 서버 실행 스크립트 (Windows CMD)
REM 사용법: scripts\run_dev.bat

REM 개발 DB 사용 정보 출력
echo 🚀 개발 환경 서버를 시작합니다...
echo 📍 환경: DEV
echo 🗄️  DB: data\app_dev.db
echo 🌐 포트: 8000
echo.

REM Uvicorn 서버 실행 (개발 모드)
REM 환경변수 설정 후 실행
set APP_ENV=dev
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
