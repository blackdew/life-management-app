#!/bin/bash
# 메인(프로덕션) 환경 서버 실행 스크립트
# 사용법: ./scripts/run_main.sh

# 메인 DB 사용 정보 출력
echo "🚀 메인(프로덕션) 환경 서버를 시작합니다..."
echo "📍 환경: MAIN (PRODUCTION)"
echo "🗄️  DB: data/app.db"
echo "🌐 포트: 8001"
echo "⚠️  디버그 모드: OFF"
echo ""

# Uvicorn 서버 실행 (프로덕션 모드 - reload 없음)
# 환경변수를 명령어 앞에 직접 지정
APP_ENV=main DEBUG=false uv run uvicorn app.main:app --host 0.0.0.0 --port 8001
