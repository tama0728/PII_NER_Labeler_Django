# KDPII Labeler

한국 개인정보보호법(KDPII) 준수를 위한 NER(Named Entity Recognition) 라벨링 도구입니다. Django와 PostgreSQL을 기반으로 구축되었으며, 33개의 KDPII 개인정보 유형을 지원합니다.

## 🌟 주요 기능

- **📊 프로젝트 관리**: 여러 라벨링 프로젝트를 관리하고 워크스페이스별로 작업
- **🏷️ KDPII 라벨링**: 33개의 한국 개인정보 유형 자동 지원
- **🎨 직관적인 UI**: 웹 기반 인터페이스로 쉬운 텍스트 어노테이션
- **🔍 실시간 검색**: 프로젝트, 작업, 어노테이션 실시간 검색
- **👥 다중 사용자**: Django Admin을 통한 사용자 및 권한 관리
- **📈 진행 추적**: 프로젝트별 진행 상황 및 통계 제공
- **💾 PostgreSQL**: 확장 가능한 데이터베이스 백엔드

## 🏷️ 지원 KDPII 라벨 (33개)

### 개인 식별 정보
- `PS_NAME` - 성명
- `PS_NICKNAME` - 별명/닉네임  
- `PS_ID` - 개인 식별자

### 생체/신체 정보
- `DT_BIRTH` - 생년월일
- `QT_AGE` - 나이
- `CV_SEX` - 성별
- `QT_LENGTH` - 신장
- `QT_WEIGHT` - 체중
- `TM_BLOOD_TYPE` - 혈액형

### 위치 정보
- `LCP_COUNTRY` - 국가
- `LC_ADDRESS` - 주소
- `LC_PLACE` - 장소

### 연락처 정보
- `QT_MOBILE` - 휴대폰번호
- `QT_PHONE` - 전화번호
- `TMI_EMAIL` - 이메일

### 식별 번호
- `QT_RESIDENT_NUMBER` - 주민등록번호
- `QT_ALIEN_NUMBER` - 외국인등록번호
- `QT_PASSPORT_NUMBER` - 여권번호
- `QT_DRIVER_NUMBER` - 운전면허번호
- `QT_CARD_NUMBER` - 카드번호
- `QT_ACCOUNT_NUMBER` - 계좌번호
- `QT_PLATE_NUMBER` - 차량번호

### 직업/교육 정보
- `OG_WORKPLACE` - 직장
- `OG_DEPARTMENT` - 부서
- `CV_POSITION` - 직위
- `OGG_EDUCATION` - 학력
- `QT_GRADE` - 성적
- `FD_MAJOR` - 전공

### 기타 정보
- `OGG_RELIGION` - 종교
- `OGG_CLUB` - 단체/클럽
- `TMI_SITE` - 웹사이트
- `QT_IP` - IP주소
- `CV_MILITARY_CAMP` - 병역

## 🚀 빠른 시작

### 1. 자동 배포 (권장)

```bash
# 저장소 클론
git clone <repository-url>
cd kdpii_labeler_django

# 자동 배포 스크립트 실행
chmod +x deploy.sh
./deploy.sh
```

### 2. 수동 설치

#### 필수 요구사항
- Python 3.8+
- PostgreSQL 12+
- Git

#### 설치 단계

1. **저장소 클론**
```bash
git clone <repository-url>
cd kdpii_labeler_django
```

2. **가상환경 생성 (선택사항)**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\\Scripts\\activate   # Windows
```

3. **의존성 설치**
```bash
pip install -r requirements.txt
```

4. **환경 변수 설정**
```bash
cp .env.example .env
# .env 파일을 편집하여 데이터베이스 설정 등을 수정
```

5. **데이터베이스 설정**
```bash
# PostgreSQL 데이터베이스 생성
sudo -u postgres createdb kdpii_labeler
sudo -u postgres createuser kdpii_user

# 또는 자동 설정 스크립트 사용
./setup_database.sh
```

6. **Django 마이그레이션**
```bash
python manage.py makemigrations
python manage.py migrate
```

7. **KDPII 라벨 로드**
```bash
python manage.py load_global_tags
```

8. **관리자 계정 생성**
```bash
python manage.py createsuperuser
```

9. **정적 파일 수집**
```bash
python manage.py collectstatic
```

10. **서버 시작**
```bash
python manage.py runserver 0.0.0.0:8000
```

## 📁 프로젝트 구조

```
kdpii_labeler_django/
├── kdpii_labeler_django/     # Django 프로젝트 설정
│   ├── settings.py           # Django 설정
│   ├── urls.py              # URL 라우팅
│   └── wsgi.py              # WSGI 설정
├── ner_labeler/             # 메인 애플리케이션
│   ├── models.py            # 데이터 모델
│   ├── views.py             # API 뷰
│   ├── serializers.py       # DRF 시리얼라이저
│   ├── admin.py             # Django Admin 설정
│   └── management/commands/  # 관리 명령어
│       ├── load_tags.py     # 프로젝트별 라벨 로드
│       └── load_global_tags.py # 전역 라벨 로드
├── templates/               # Django 템플릿
│   ├── dashboard.html       # 메인 대시보드
│   └── workspace_ner_interface.html # NER 라벨링 인터페이스
├── frontend/static/         # 정적 파일
│   ├── css/                # 스타일시트
│   ├── js/                 # JavaScript
│   └── tag.json           # KDPII 라벨 정의
├── requirements.txt         # Python 의존성
├── .env.example            # 환경 변수 예시
├── deploy.sh               # 자동 배포 스크립트
├── setup_database.sh       # 데이터베이스 설정 스크립트
└── README.md               # 이 파일
```

## 🖥️ 사용법

### 1. 관리자 페이지 접속
- URL: `http://localhost:8000/admin/`
- Django 슈퍼유저 계정으로 로그인

### 2. 프로젝트 생성
1. 관리자 페이지에서 "Projects" → "Add Project"
2. 프로젝트 이름, 설명 입력
3. 저장

### 3. 작업(Task) 추가
1. "Tasks" → "Add Task"  
2. 라벨링할 텍스트 입력
3. 프로젝트 선택
4. 저장

### 4. NER 라벨링 작업
1. 대시보드에서 워크스페이스 선택
2. 텍스트에서 개인정보 부분을 마우스로 드래그 선택
3. 적절한 KDPII 라벨 클릭 (예: PS_NAME, QT_MOBILE 등)
4. 어노테이션 자동 저장

### 5. 진행 상황 확인
- 대시보드에서 프로젝트별 진행률 확인
- 완료된 작업 수, 전체 작업 수 표시

## 🔧 관리 명령어

### 라벨 관리
```bash
# 전역 KDPII 라벨 로드 (모든 프로젝트에서 사용)
python manage.py load_global_tags

# 기존 전역 라벨 삭제 후 재로드
python manage.py load_global_tags --clear

# 특정 프로젝트에 라벨 추가 (구버전)
python manage.py load_tags --project-id 1
```

### 데이터베이스 관리
```bash
# 마이그레이션 생성
python manage.py makemigrations

# 마이그레이션 적용
python manage.py migrate

# 데이터베이스 초기화 (주의!)
python manage.py flush
```

### 정적 파일 관리
```bash
# 정적 파일 수집
python manage.py collectstatic

# 정적 파일 수집 (덮어쓰기)
python manage.py collectstatic --clear
```

## 🌐 배포

### 개발 환경
```bash
python manage.py runserver 0.0.0.0:8000
```

### 프로덕션 환경

#### Nginx + uWSGI
```bash
# uWSGI 설치
pip install uwsgi

# uWSGI 실행
uwsgi --http :8000 --module kdpii_labeler_django.wsgi

# Nginx 리버스 프록시 설정 (deploy.sh 참조)
```

#### Docker (선택사항)
```dockerfile
# Dockerfile 예시
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 🔒 보안 고려사항

### 프로덕션 배포시 필수 설정

1. **SECRET_KEY 변경**
```python
# .env 파일에서 고유한 시크릿 키 설정
SECRET_KEY=your-unique-secret-key-here
```

2. **DEBUG 모드 비활성화**
```python
DEBUG=False
```

3. **ALLOWED_HOSTS 설정**
```python
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

4. **데이터베이스 보안**
- 강력한 데이터베이스 비밀번호 사용
- 데이터베이스 접근 제한
- SSL/TLS 연결 사용

5. **HTTPS 사용**
- SSL 인증서 설정
- HTTP → HTTPS 리다이렉트

## 🛠️ 문제 해결

### 자주 발생하는 문제

#### 1. PostgreSQL 연결 오류
```bash
# PostgreSQL 서비스 시작
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 데이터베이스 존재 확인
sudo -u postgres psql -l
```

#### 2. 라벨이 표시되지 않는 문제
```bash
# 전역 라벨 재로드
python manage.py load_global_tags --clear

# 브라우저 캐시 삭제 후 새로고침
```

#### 3. 정적 파일이 로드되지 않는 문제
```bash
# 정적 파일 재수집
python manage.py collectstatic --clear

# Nginx 설정 확인 (배포 환경)
sudo nginx -t
```

#### 4. 마이그레이션 오류
```bash
# 마이그레이션 상태 확인
python manage.py showmigrations

# 가짜 마이그레이션 적용 (필요한 경우)
python manage.py migrate --fake-initial
```

## 📊 API 문서

### 주요 엔드포인트

- `GET /api/projects/` - 프로젝트 목록
- `GET /api/projects/{id}/tasks/` - 프로젝트별 작업 목록  
- `GET /api/labels/` - 라벨 목록
- `POST /api/projects/{id}/tasks/{task_id}/annotations/` - 어노테이션 생성
- `GET /admin/` - Django 관리자 페이지

### API 사용 예시
```bash
# 프로젝트 목록 조회
curl http://localhost:8000/api/projects/

# 라벨 목록 조회 (특정 프로젝트)
curl http://localhost:8000/api/labels/?project=1
```

## 🤝 기여하기

1. 이 저장소를 포크합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원

문제가 발생하거나 질문이 있으시면:

1. GitHub Issues에 이슈를 등록해 주세요
2. 문서를 확인해 주세요
3. 로그를 확인해 주세요: `python manage.py runserver`의 출력

## 🔄 업데이트 이력

### v2.0.0 (현재)
- Flask에서 Django로 마이그레이션
- PostgreSQL 데이터베이스 지원
- 전역 KDPII 라벨 시스템
- 개선된 웹 인터페이스
- Django Admin 통합

### v1.0.0 (이전)
- Flask 기반 초기 버전
- SQLite 데이터베이스
- 기본 NER 라벨링 기능

---

**🎯 KDPII Labeler로 한국 개인정보보호법을 준수하는 안전한 데이터 라벨링을 시작하세요!**