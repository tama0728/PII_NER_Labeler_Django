# KDPII Labeler Django - Docker 환경 설정

이 문서는 Docker를 사용하여 KDPII Labeler Django 애플리케이션을 실행하는 방법을 설명합니다.

## 사전 요구사항

1. **Docker Desktop 설치**
   - Windows: [Docker Desktop for Windows](https://docs.docker.com/desktop/windows/install/)
   - WSL 2 백엔드 사용 권장

2. **WSL 2 통합 활성화**
   - Docker Desktop Settings → Resources → WSL Integration
   - Ubuntu-22.04 (또는 사용 중인 WSL 배포판) 체크

## 빠른 시작

### 1. 자동 설정 스크립트 실행
```bash
./docker-setup.sh
```

### 2. 수동 설정
```bash
# 컨테이너 빌드 및 실행
docker-compose up --build -d

# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f web
```

## 서비스 구성

### PostgreSQL 데이터베이스
- 이미지: `postgres:15`
- 포트: `5432`
- 데이터베이스: `kdpii_labeler_db`
- 사용자: `ysy`
- 비밀번호: `kdpii_labeler_2024`

### Django 웹 애플리케이션
- 빌드: `Dockerfile`
- 포트: `8080`
- URL: http://localhost:8080

## 주요 명령어

### 컨테이너 관리
```bash
# 컨테이너 시작
docker-compose up -d

# 컨테이너 정지
docker-compose down

# 컨테이너 재시작
docker-compose restart

# 볼륨까지 삭제
docker-compose down -v
```

### 로그 확인
```bash
# 전체 로그
docker-compose logs

# 웹 서비스 로그만
docker-compose logs -f web

# 데이터베이스 로그만
docker-compose logs -f db
```

### Django 관리 명령
```bash
# 마이그레이션
docker-compose exec web python manage.py migrate

# 슈퍼유저 생성
docker-compose exec web python manage.py createsuperuser

# 정적 파일 수집
docker-compose exec web python manage.py collectstatic

# Django shell
docker-compose exec web python manage.py shell
```

### 데이터베이스 접속
```bash
# PostgreSQL shell 접속
docker-compose exec db psql -U ysy -d kdpii_labeler_db

# 데이터베이스 백업
docker-compose exec db pg_dump -U ysy kdpii_labeler_db > backup.sql

# 백업 복원
docker-compose exec -T db psql -U ysy -d kdpii_labeler_db < backup.sql
```

## 개발 환경

### 소스 코드 변경사항 반영
- 소스 코드는 볼륨 마운트되어 있어 실시간으로 반영됩니다.
- Django 개발 서버가 자동으로 재시작됩니다.

### 의존성 변경 시
```bash
# requirements.txt 변경 후 이미지 재빌드
docker-compose build web
docker-compose up -d
```

### 데이터베이스 초기화
```bash
# 데이터베이스 볼륨 삭제 후 재시작
docker-compose down -v
docker-compose up -d
```

## 트러블슈팅

### Docker Desktop이 실행되지 않는 경우
- Windows에서 Docker Desktop이 실행 중인지 확인
- WSL 2 통합이 활성화되어 있는지 확인

### 포트 충돌 문제
```bash
# 포트 사용 확인
netstat -an | findstr :8080
netstat -an | findstr :5432

# 다른 포트로 변경 (docker-compose.yml 수정)
```

### 권한 문제
```bash
# 파일 권한 확인
ls -la docker-setup.sh

# 실행 권한 부여
chmod +x docker-setup.sh
```

### 컨테이너 상태 확인
```bash
# 실행 중인 컨테이너 확인
docker-compose ps

# 모든 컨테이너 상태
docker ps -a

# 리소스 사용량
docker stats
```

## 프로덕션 배포

현재 설정은 개발 환경용입니다. 프로덕션 배포 시 다음 사항을 고려하세요:

1. `DEBUG=False` 설정
2. 강력한 `SECRET_KEY` 생성
3. 환경변수를 통한 민감한 정보 관리
4. NGINX 리버스 프록시 사용
5. SSL/TLS 인증서 설정
6. 로그 관리 시스템 구축

## 지원

문제가 발생하면 다음을 확인해주세요:
1. Docker Desktop 실행 상태
2. WSL 2 통합 설정
3. 네트워크 연결 상태
4. 포트 사용 가능 여부