#!/bin/bash

# KDPII Labeler 데이터베이스 설정 스크립트
# PostgreSQL 데이터베이스와 사용자를 생성하고 Django 마이그레이션을 실행합니다.

set -e  # 오류 발생시 스크립트 중단

echo "🚀 KDPII Labeler 데이터베이스 설정을 시작합니다..."

# PostgreSQL 설치 여부 확인
if ! command -v psql &> /dev/null; then
    echo "📦 PostgreSQL이 설치되어 있지 않습니다. 설치를 진행합니다..."
    
    # OS 확인 후 적절한 패키지 매니저로 설치
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            sudo apt-get update
            sudo apt-get install -y postgresql postgresql-contrib python3-psycopg2
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL
            sudo yum install -y postgresql-server postgresql-contrib python3-psycopg2
            sudo postgresql-setup initdb
        elif command -v dnf &> /dev/null; then
            # Fedora
            sudo dnf install -y postgresql-server postgresql-contrib python3-psycopg2
            sudo postgresql-setup --initdb
        else
            echo "❌ 지원되지 않는 Linux 배포판입니다. PostgreSQL을 수동으로 설치해주세요."
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install postgresql
        else
            echo "❌ Homebrew가 필요합니다. brew install postgresql 을 실행해주세요."
            exit 1
        fi
    else
        echo "❌ 지원되지 않는 운영체제입니다. PostgreSQL을 수동으로 설치해주세요."
        exit 1
    fi
    
    echo "✅ PostgreSQL 설치가 완료되었습니다."
fi

# PostgreSQL 서비스 상태 확인
if ! systemctl is-active --quiet postgresql; then
    echo "📦 PostgreSQL 서비스를 시작합니다..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# 환경 변수 로드 (.env 파일이 있는 경우)
if [ -f .env ]; then
    echo "📁 .env 파일에서 환경 변수를 로드합니다..."
    export $(cat .env | grep -v '#' | awk '/=/ {print $1}')
else
    echo "⚠️  .env 파일이 없습니다. 기본값을 사용합니다."
    DB_NAME=${DB_NAME:-kdpii_labeler}
    DB_USER=${DB_USER:-kdpii_user}
    DB_PASSWORD=${DB_PASSWORD:-kdpii_password}
fi

echo "🔧 PostgreSQL 데이터베이스와 사용자를 생성합니다..."

# PostgreSQL에서 데이터베이스와 사용자 생성
sudo -u postgres psql << EOF
-- 데이터베이스가 이미 존재하는지 확인
SELECT 1 FROM pg_database WHERE datname = '$DB_NAME';

-- 데이터베이스 생성 (존재하지 않는 경우)
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME') THEN
      PERFORM dblink_exec('dbname=' || current_database(), 'CREATE DATABASE $DB_NAME');
   END IF;
END
\$\$;

-- 사용자 생성 (존재하지 않는 경우)
DO \$\$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
      CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
   END IF;
END
\$\$;

-- 사용자에게 데이터베이스 권한 부여
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
ALTER USER $DB_USER CREATEDB;
EOF

echo "✅ PostgreSQL 설정이 완료되었습니다."

echo "🔄 Django 마이그레이션을 실행합니다..."

# Django 마이그레이션 실행
python3 manage.py makemigrations
python3 manage.py migrate

echo "👤 Django 슈퍼유저 생성 (선택사항)..."
echo "관리자 계정을 생성하시겠습니까? (y/N)"
read -r create_superuser

if [[ $create_superuser =~ ^[Yy]$ ]]; then
    python3 manage.py createsuperuser
fi

echo "🏷️  KDPII 글로벌 라벨을 로드합니다..."
python3 manage.py load_global_tags

echo "📊 정적 파일을 수집합니다..."
python3 manage.py collectstatic --noinput

echo ""
echo "🎉 데이터베이스 설정이 완료되었습니다!"
echo ""
echo "📋 설정 요약:"
echo "   - 데이터베이스: $DB_NAME"
echo "   - 사용자: $DB_USER"
echo "   - 글로벌 KDPII 라벨: 33개 로드됨"
echo ""
echo "🚀 서버를 시작하려면: python3 manage.py runserver 0.0.0.0:8000"
echo "🔧 관리자 페이지: http://localhost:8000/admin/"
echo ""