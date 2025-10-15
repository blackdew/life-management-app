#!/bin/bash
# 개발 환경 서버 실행 스크립트
# 사용법: ./scripts/run_dev.sh

# 개발 DB 사용 정보 출력
echo "🚀 개발 환경 서버를 시작합니다..."
echo "📍 환경: DEV"
echo "🗄️  DB: data/app_dev.db"
echo "🌐 포트: 8000"
echo ""

# Uvicorn 서버 실행 (개발 모드)
# 환경변수를 명령어 앞에 직접 지정
APP_ENV=dev uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
