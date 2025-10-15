#!/bin/bash
# 서비스 로직 테스트 분리 실행 스크립트
# async 이벤트 루프 충돌을 피하기 위해 서비스 테스트와 API 테스트를 분리 실행

set -e  # 오류 발생 시 스크립트 중단

echo "======================================"
echo "🧪 서비스 로직 테스트 (async 지원)"
echo "======================================"
echo "FastAPI TestClient 없이 실행하여 이벤트 루프 충돌 방지"
echo ""

# 서비스 테스트만 실행 (async 테스트 포함)
uv run pytest tests/services/ -v --tb=short --cov=app/services --cov-report=term-missing

echo ""
echo "======================================"
echo "🌐 API 및 통합 테스트"
echo "======================================"
echo "FastAPI TestClient 사용, async 서비스 테스트는 skip"
echo ""

# API, E2E, 모델 테스트 실행
uv run pytest tests/api/ tests/e2e/ tests/models/ -v --tb=short

echo ""
echo "======================================"
echo "✅ 모든 테스트 완료"
echo "======================================"
echo "서비스 로직: 실제 async 테스트 포함"
echo "API/E2E: HTTP 인터페이스 및 시나리오 테스트"
echo ""