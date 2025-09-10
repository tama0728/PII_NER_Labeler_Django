# KDPII NER Labeler (Django Version)

Flask에서 Django로 마이그레이션된 Named Entity Recognition (NER) 라벨링 도구입니다.

## 주요 기능

- 🏷️ **NER 주석 작업**: 텍스트에서 개체명 인식 라벨링
- 📊 **프로젝트 관리**: 여러 프로젝트 동시 관리
- 👥 **팀 협업**: 협업 워크스페이스 지원
- 📈 **통계 대시보드**: 작업 진행 상황 및 성과 분석
- 🔧 **관리자 인터페이스**: Django Admin을 통한 데이터 관리
- 📤 **다양한 내보내기**: JSON, CSV, CoNLL, Label Studio 형식 지원

## 기술 스택

- **Backend**: Django 4.2.7 + Django REST Framework
- **Database**: PostgreSQL
- **Frontend**: Bootstrap 5 + jQuery
- **Authentication**: Django 내장 인증 시스템

## 빠른 시작

### 1. 환경 설정

```bash
cd /home/ysy/kdpii_labler/kdpii_labeler_django
pip install -r requirements.txt
```

### 2. 데이터베이스 설정

PostgreSQL이 설치되어 있지 않다면:
```bash
./setup_postgresql.sh
```

데이터베이스 마이그레이션:
```bash
python3 manage.py migrate
```

### 3. 서버 시작 (포트 8080)

**방법 1: 간단한 스크립트 사용**
```bash
./run.sh
```

**방법 2: Python 스크립트 사용**
```bash
python3 start_server.py
```

**방법 3: 직접 명령어 사용**
```bash
python3 manage.py runserver 0.0.0.0:8080
```

**다른 포트로 시작하려면:**
```bash
./run.sh 9000              # 포트 9000으로 시작
python3 start_server.py 9000   # 포트 9000으로 시작
```

## 접속 URL

- **메인 대시보드**: http://localhost:8080/
- **협업 페이지**: http://localhost:8080/collaborate/
- **작업 인터페이스**: http://localhost:8080/workspace/
- **관리자 페이지**: http://localhost:8080/admin/

## 관리자 계정

기본 관리자 계정:
- **사용자명**: admin
- **비밀번호**: admin123

## API 엔드포인트

### RESTful API
- `GET /api/v1/projects/` - 프로젝트 목록
- `GET /api/v1/tasks/` - 작업 목록
- `GET /api/v1/annotations/` - 주석 목록
- `GET /api/v1/labels/` - 라벨 목록

### Legacy API (호환성)
- `GET /api/statistics/` - 통계 정보
- `GET /api/tasks/` - 작업 목록
- `POST /api/tasks/` - 새 작업 생성
- `GET /api/labels/` - 라벨 목록

## 프로젝트 구조

```
kdpii_labeler_django/
├── kdpii_labeler_django/     # Django 프로젝트 설정
├── ner_labeler/              # 메인 앱
│   ├── models.py            # 데이터 모델
│   ├── views.py             # API 뷰
│   ├── admin.py             # 관리자 인터페이스
│   ├── serializers.py       # DRF 시리얼라이저
│   └── urls.py              # URL 라우팅
├── templates/               # Django 템플릿
├── static/                  # 정적 파일
├── .env                     # 환경 변수
├── run.sh                   # 서버 시작 스크립트
├── start_server.py          # Python 서버 시작 스크립트
└── requirements.txt         # 패키지 의존성
```

## 환경 변수 (.env)

```env
SECRET_KEY=your-secret-key
DEBUG=True
DEFAULT_PORT=8080

# PostgreSQL 설정
DB_ENGINE=django.db.backends.postgresql
DB_NAME=kdpii_labeler_db
DB_USER=ysy
DB_PASSWORD=kdpii_labeler_2024
DB_HOST=localhost
DB_PORT=5432

# 허용된 호스트
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

## 개발자 가이드

### 새로운 기능 추가

1. **모델 수정**: `ner_labeler/models.py`
2. **API 개발**: `ner_labeler/views.py` + `ner_labeler/serializers.py`
3. **URL 라우팅**: `ner_labeler/urls.py`
4. **관리자 인터페이스**: `ner_labeler/admin.py`
5. **프론트엔드**: `templates/` 폴더

### 데이터베이스 마이그레이션

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

### 슈퍼유저 생성

```bash
python3 manage.py createsuperuser
```

## 문제 해결

### 포트 충돌
```bash
# 포트 사용 중인 프로세스 확인
lsof -i :8080

# 프로세스 종료
kill -9 <PID>
```

### PostgreSQL 연결 오류
```bash
# PostgreSQL 서비스 상태 확인
sudo systemctl status postgresql

# 서비스 시작
sudo systemctl start postgresql
```

## 라이선스

이 프로젝트는 Flask 버전에서 Django로 마이그레이션된 버전입니다.