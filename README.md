# AWS SAA 시험 연습 앱

AWS SAA (Solutions Architect Associate) 시험을 위한 PDF 문제집 기반 연습 애플리케이션입니다.

Vibe Coding으로 제작된 애플리케이션입니다.

## 🎯 주요 기능

### 사용자 기능
- **PDF 업로드**: 드래그 앤 드롭으로 PDF 문제집 업로드
- **시험 모드**: 실제 시험과 동일한 환경 (타이머, 답안 숨김)
- **학습 모드**: 즉시 답안 확인 및 설명 제공
- **진행률 추적**: 실시간 진행 상황 및 점수 표시
- **응답 저장**: 자동 저장 및 세션 복구
- **메모 및 플래그**: 문제별 메모 작성 및 중요 표시

### 관리자 기능
- **대시보드**: 전체 통계 및 최근 세션 모니터링
- **시험 관리**: PDF 업로드, 시험 삭제, 문제 관리
- **통계 분석**: 문제별 정답률, 사용자 성과 분석
- **세션 관리**: 사용자 세션 추적 및 관리

## 🛠 기술 스택

### 백엔드
- **FastAPI**: 현대적이고 빠른 웹 프레임워크
- **SQLAlchemy Async**: 비동기 데이터베이스 ORM
- **Uvicorn**: ASGI 서버
- **PyMuPDF**: PDF 파싱 및 텍스트 추출
- **SQLite**: 경량 데이터베이스

### 프론트엔드
- **Jinja2**: 서버사이드 템플릿 엔진
- **Tailwind CSS**: 유틸리티 우선 CSS 프레임워크
- **Alpine.js**: 경량 반응형 JavaScript 프레임워크
- **HTMX**: 동적 HTML 업데이트
- **Vanilla JavaScript**: 커스텀 기능 구현

### 개발 도구
- **Python 3.8+**: 메인 프로그래밍 언어
- **Conda**: 환경 관리
- **Greenlet**: SQLAlchemy 비동기 지원

## 📦 설치 및 실행

### 1. 환경 설정

#### Conda 사용 (권장)
```bash
# Conda 환경 생성
conda create -n aws-exam-app python=3.11
conda activate aws-exam-app

# 의존성 설치
pip install -r requirements.txt
```

#### pip 사용
```bash
# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 애플리케이션 실행

```bash
# 개발 모드 (자동 재시작)
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# 프로덕션 모드
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 3. 접속

브라우저에서 `http://localhost:8000` 접속

## 🚀 사용 방법

### PDF 업로드
1. 메인 페이지에서 PDF 파일을 드래그 앤 드롭하거나 파일 선택
2. 자동으로 문제 파싱 및 데이터베이스 저장
3. 업로드 완료 후 시험 목록에 추가됨

### 시험 응시
1. 시험 목록에서 원하는 시험 선택
2. 시험 모드 또는 학습 모드 선택
3. 문제 풀이 및 답안 선택
4. 시험 완료 후 결과 확인

### 관리자 기능
1. `/admin` 페이지 접속
2. 통계 확인 및 시험 관리
3. PDF 업로드 및 시험 삭제

## ⌨️ 키보드 단축키

- **화살표 키**: 이전/다음 문제 이동
- **1-4 키**: 선택지 A-D 선택
- **Ctrl/Cmd + S**: 응답 저장
- **Ctrl/Cmd + Enter**: 시험 제출

## 📁 프로젝트 구조

```
dump_webapp/
├── app.py                 # FastAPI 메인 애플리케이션
├── database.py            # 데이터베이스 설정
├── models.py              # SQLAlchemy 모델
├── pdf_parser.py          # PDF 파싱 로직
├── exam_service.py        # 비즈니스 로직
├── requirements.txt       # Python 의존성
├── README.md             # 프로젝트 문서
├── exam_app.db           # SQLite 데이터베이스
├── templates/            # Jinja2 템플릿
│   ├── base.html         # 기본 레이아웃
│   ├── index.html        # 메인 페이지
│   ├── exam_detail.html  # 시험 상세
│   ├── session.html      # 세션 시작
│   ├── question.html     # 문제 페이지
│   ├── result.html       # 결과 페이지
│   ├── admin.html        # 관리자 대시보드
│   └── admin_questions.html # 문제 관리
└── static/               # 정적 파일
    ├── css/
    │   └── style.css     # 커스텀 스타일
    ├── js/
    │   └── app.js        # 메인 JavaScript
    └── images/           # 이미지 파일
```

## 🗄️ 데이터베이스 모델

### 핵심 엔티티
- **Exam**: 시험 정보 (제목, 버전, 설명)
- **Section**: 시험 섹션 (기본적으로 하나)
- **Question**: 문제 (텍스트, 순서, 이미지)
- **Choice**: 선택지 (A, B, C, D)
- **Answer**: 정답 정보 (정답 선택지, 설명)
- **Session**: 시험 세션 (모드, 시작/종료 시간, 점수)
- **Response**: 응답 기록 (선택한 답안, 메모, 플래그)

### 관계
- Exam → Section → Question → Choice/Answer
- Session → Response → Question
- 모든 관계는 CASCADE 삭제로 설정

## 📄 PDF 파싱

### 지원 형식
- **문제 형식**: `QUESTION NO: [번호]`
- **선택지 형식**: `A. [내용]`, `B. [내용]`, `C. [내용]`, `D. [내용]`
- **답안 형식**: `Answer: [A/B/C/D]`
- **설명 형식**: `Explanation: [설명]`

### 파싱 과정
1. PDF 텍스트 추출 (PyMuPDF)
2. 정규표현식으로 문제 블록 분할
3. 각 문제에서 텍스트, 선택지, 답안, 설명 추출
4. 데이터베이스에 저장

## 🎨 주요 페이지

### 사용자 페이지
- **메인 페이지** (`/`): PDF 업로드, 시험 목록
- **시험 상세** (`/exam/{id}`): 시험 정보, 모드 선택
- **문제 페이지** (`/session/{id}/question/{qid}`): 문제 풀이
- **결과 페이지** (`/session/{id}/result`): 시험 결과

### 관리자 페이지
- **대시보드** (`/admin`): 통계, 시험 관리
- **문제 관리** (`/admin/exam/{id}/questions`): 문제별 통계

## 🔧 개발 및 배포

### 개발 환경
```bash
# 개발 서버 실행
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# 데이터베이스 초기화
python -c "from database import init_db; import asyncio; asyncio.run(init_db())"
```

### 프로덕션 배포
```bash
# 프로덕션 서버 실행
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4

# 또는 Gunicorn 사용
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Docker 배포
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## ✅ 기능 완성도

### 완료된 기능 ✅
- [x] PDF 업로드 및 파싱
- [x] 시험 모드 (타이머, 답안 숨김)
- [x] 학습 모드 (즉시 답안 확인)
- [x] 응답 저장 및 복구
- [x] 진행률 추적
- [x] 메모 및 플래그
- [x] 관리자 대시보드
- [x] 시험 관리 (업로드, 삭제)
- [x] 드래그 앤 드롭 업로드
- [x] 반응형 디자인

### 향후 계획 🚧
- [ ] 이미지 추출 및 표시
- [ ] 문제 편집 기능
- [ ] 사용자 인증
- [ ] 성과 분석 리포트
- [ ] 문제 랜덤화
- [ ] 타이머 설정
- [ ] 다국어 지원

## ⚠️ 주의사항

### PDF 형식
- 표준 dump 형식의 PDF만 지원
- 이미지가 포함된 문제는 텍스트만 추출
- 복잡한 레이아웃은 파싱 정확도 저하 가능

### 성능
- 대용량 PDF 업로드 시 처리 시간 소요
- 동시 사용자 수에 따른 성능 고려 필요

### 보안
- 현재 사용자 인증 없음
- 프로덕션 배포 시 보안 설정 필요

## 🐛 문제 해결

### 일반적인 오류

#### ModuleNotFoundError: No module named 'fastapi'
```bash
# 올바른 환경 활성화 확인
conda activate aws-exam-app
# 또는
source venv/bin/activate
```

#### ValueError: the greenlet library is required
```bash
# greenlet 설치
pip install greenlet==3.2.4
```

#### DeprecationWarning: on_event is deprecated
- 이미 수정됨: `lifespan` 이벤트 핸들러 사용

#### Internal Server Error
- 템플릿 파일 누락 확인
- 데이터베이스 초기화 확인

### 로그 확인
```bash
# 애플리케이션 로그
tail -f app.log

# 데이터베이스 로그
sqlite3 exam_app.db ".log on"
```

## 📞 지원

문제가 발생하거나 기능 요청이 있으시면 이슈를 등록해주세요.

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
