#!/bin/bash

# KDPII Labeler 배포 스크립트
# 새로운 서버에 KDPII Labeler를 배포하기 위한 전체 설정 스크립트

set -e  # 오류 발생시 스크립트 중단

echo "🚀 KDPII Labeler 배포를 시작합니다..."

# 시스템 업데이트
echo "📦 시스템 패키지를 업데이트합니다..."
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
echo "📦 필수 패키지를 설치합니다..."
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib nginx git curl

# Python 가상환경 생성 (선택사항)
echo "🐍 Python 가상환경을 생성하시겠습니까? (y/N)"
read -r create_venv

if [[ $create_venv =~ ^[Yy]$ ]]; then
    echo "📁 Python 가상환경을 생성합니다..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 가상환경이 활성화되었습니다."
fi

# Python 의존성 설치
echo "📦 Python 의존성을 설치합니다..."
pip3 install -r requirements.txt

# 환경 변수 설정
if [ ! -f .env ]; then
    echo "⚙️  환경 변수 파일을 생성합니다..."
    cp .env.example .env
    
    echo "🔧 .env 파일을 편집하여 환경 설정을 완료하세요:"
    echo "   - SECRET_KEY: Django 시크릿 키"
    echo "   - DB_PASSWORD: 데이터베이스 비밀번호"  
    echo "   - ALLOWED_HOSTS: 허용된 호스트 도메인"
    echo "   - CORS_ALLOWED_ORIGINS: CORS 허용 도메인"
    
    echo "계속하려면 Enter를 누르세요..."
    read -r
fi

# 데이터베이스 설정
echo "🗄️  데이터베이스를 설정합니다..."
./setup_database.sh

# Nginx 설정 (선택사항)
echo "🌐 Nginx 웹서버를 설정하시겠습니까? (y/N)"
read -r setup_nginx

if [[ $setup_nginx =~ ^[Yy]$ ]]; then
    echo "🌐 Nginx 설정을 생성합니다..."
    
    # Nginx 설정 파일 생성
    sudo tee /etc/nginx/sites-available/kdpii_labeler << EOF
server {
    listen 80;
    server_name localhost;

    client_max_body_size 100M;

    location /static/ {
        alias /var/www/kdpii_labeler/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/kdpii_labeler/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

    # Nginx 사이트 활성화
    sudo ln -sf /etc/nginx/sites-available/kdpii_labeler /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    
    echo "✅ Nginx 설정이 완료되었습니다."
fi

# 정적 파일 디렉토리 생성
echo "📁 정적 파일 디렉토리를 생성합니다..."
sudo mkdir -p /var/www/kdpii_labeler/static/
sudo mkdir -p /var/www/kdpii_labeler/media/
sudo chown -R $USER:$USER /var/www/kdpii_labeler/

# systemd 서비스 설정 (선택사항)
echo "🔧 systemd 서비스를 설정하시겠습니까? (y/N)"
read -r setup_service

if [[ $setup_service =~ ^[Yy]$ ]]; then
    echo "🔧 systemd 서비스를 생성합니다..."
    
    sudo tee /etc/systemd/system/kdpii_labeler.service << EOF
[Unit]
Description=KDPII Labeler Django Application
After=network.target postgresql.service

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python manage.py runserver 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable kdpii_labeler
    
    echo "✅ systemd 서비스가 생성되었습니다."
    echo "서비스 시작: sudo systemctl start kdpii_labeler"
    echo "서비스 상태: sudo systemctl status kdpii_labeler"
fi

echo ""
echo "🎉 KDPII Labeler 배포가 완료되었습니다!"
echo ""
echo "📋 다음 단계:"
echo "   1. .env 파일을 편집하여 환경 설정 완료"
echo "   2. Django 서버 시작: python3 manage.py runserver 0.0.0.0:8000"
echo "   3. 브라우저에서 접속: http://localhost:8000"
echo "   4. 관리자 페이지: http://localhost:8000/admin/"
echo ""
echo "🔧 유용한 명령어:"
echo "   - 서버 시작: python3 manage.py runserver 0.0.0.0:8000"
echo "   - 라벨 재로드: python3 manage.py load_global_tags --clear"
echo "   - 정적파일 수집: python3 manage.py collectstatic"
echo "   - 마이그레이션: python3 manage.py migrate"
echo ""