#!/bin/bash

# KDPII Labeler Django Docker 환경 설정 스크립트

set -e

echo "🐳 KDPII Labeler Django - Docker 환경 설정"
echo "=========================================="

# Docker가 설치되어 있는지 확인
if ! command -v docker &> /dev/null; then
    echo "❌ Docker가 설치되어 있지 않습니다."
    echo "Docker Desktop을 설치하고 WSL 2 통합을 활성화해주세요."
    echo "https://docs.docker.com/desktop/windows/wsl/"
    exit 1
fi

# Docker Compose가 설치되어 있는지 확인
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose가 설치되어 있지 않습니다."
    exit 1
fi

echo "✅ Docker 및 Docker Compose가 설치되어 있습니다."

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리 중..."
docker-compose down -v --remove-orphans 2>/dev/null || true

# Docker 이미지 빌드 및 컨테이너 실행
echo "🔨 Docker 이미지 빌드 중..."
docker-compose build

echo "🚀 컨테이너 실행 중..."
docker-compose up -d

# 서비스 상태 확인
echo "⏳ 서비스 시작 대기 중..."
sleep 10

echo "📊 컨테이너 상태 확인:"
docker-compose ps

# 로그 확인
echo "📝 Django 애플리케이션 로그:"
docker-compose logs web --tail=20

echo ""
echo "✅ Docker 환경 설정 완료!"
echo ""
echo "🌐 애플리케이션 접속 URL:"
echo "   http://localhost:8080"
echo ""
echo "📋 유용한 명령어들:"
echo "   - 로그 확인: docker-compose logs -f web"
echo "   - 컨테이너 정지: docker-compose down"
echo "   - 데이터베이스 접속: docker-compose exec db psql -U ysy -d kdpii_labeler_db"
echo "   - Django 관리자 명령: docker-compose exec web python manage.py [명령어]"
echo ""