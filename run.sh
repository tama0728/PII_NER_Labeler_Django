#!/bin/bash

# Django 서버 시작 스크립트
# 기본 포트: 8080 (사용 중이면 자동으로 다음 포트 찾기)
# 사용법: ./run.sh [포트번호]

PORT=${1:-8080}

# 포트 사용 가능 여부 확인 함수
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 1  # 포트가 사용 중
    else
        return 0  # 포트가 사용 가능
    fi
}

# 사용 가능한 포트 찾기
ORIGINAL_PORT=$PORT
while ! check_port $PORT; do
    echo "⚠️  포트 $PORT는 이미 사용 중입니다. 다음 포트를 확인합니다..."
    PORT=$((PORT + 1))
    if [ $PORT -gt $((ORIGINAL_PORT + 20)) ]; then
        echo "❌ 사용 가능한 포트를 찾을 수 없습니다 (${ORIGINAL_PORT}-$((ORIGINAL_PORT + 20)) 범위)"
        exit 1
    fi
done

if [ $PORT -ne $ORIGINAL_PORT ]; then
    echo "✅ 포트 $PORT를 사용합니다 (원래 요청: $ORIGINAL_PORT)"
fi

echo "🚀 Django KDPII NER Labeler 서버 시작"
echo "📍 포트: $PORT"
echo "📋 관리자: http://localhost:$PORT/admin/"
echo "🏠 대시보드: http://localhost:$PORT/"
echo "⏹️  중지: Ctrl+C"
echo "=================================="

python3 manage.py runserver 0.0.0.0:$PORT