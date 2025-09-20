# 🚀 Git 설치 완료 후 진행할 작업들

## 📅 작성일: 2025-09-20
## 🎯 현재 상황: Git for Windows 설치 중

---

## ✅ Git 설치 완료 후 즉시 진행할 작업

### 1단계: Git 설치 확인
```bash
# Git Bash 실행 (시작 메뉴에서 검색)
git --version

# 사용자 정보 설정
git config --global user.name "사용자이름"
git config --global user.email "이메일@example.com"
```

### 2단계: GitHub 저장소 생성
```
1. https://github.com 접속
2. "New Repository" 클릭
3. Repository name: "daham-meal-management"
4. Private 선택
5. "Create repository" 클릭
```

### 3단계: 로컬 코드를 GitHub에 업로드
```bash
# C:\Dev\daham-meal-management 폴더에서 Git Bash 실행
cd C:/Dev/daham-meal-management

# Git 초기화
git init
git branch -M main

# GitHub 저장소 연결 (URL은 생성된 저장소 URL로 변경)
git remote add origin https://github.com/사용자계정명/daham-meal-management.git

# 파일 추가 및 커밋
git add .
git commit -m "다함 식자재 관리 시스템 - 최초 업로드 (84,215개 식자재, AI 학습 기반 단가 계산)"

# GitHub에 업로드
git push -u origin main
```

### 4단계: 운영 서버에서 GitHub 다운로드 및 배포
```bash
# 운영 서버 SSH 접속
ssh sos1253@34.64.237.181

# 기존 앱 백업 (있다면)
cd /home/daham
mv app app_backup_$(date +%Y%m%d_%H%M%S)

# GitHub에서 코드 다운로드
git clone https://github.com/사용자계정명/daham-meal-management.git app

# 애플리케이션 디렉토리로 이동
cd app

# 권한 설정
chmod +x *.py

# 학습 테이블 초기화 (최초 배포시만)
python3 create_learning_tables.py

# API 서버 시작
python3 ★test_samsung_api.py
```

### 5단계: 배포 후 동작 확인
```bash
# 웹 브라우저에서 접속 확인
# http://34.64.237.181:8010/admin_dashboard.html

# API 엔드포인트 확인
curl http://34.64.237.181:8010/api/admin/dashboard-stats

# 로그인 기능 테스트
# - 관리자 로그인
# - 식자재 검색 기능
# - 단가 계산 기능
```

---

## 📊 현재 시스템 상태 정보

### 🗂️ 배포 준비 완료된 파일들
- **메인 API 서버**: ★test_samsung_api.py (포트 8010)
- **데이터베이스**: daham_meal.db (84,215개 식자재)
- **AI 계산**: learning_price_calculator.py
- **개선된 계산**: improved_unit_price_calculator.py
- **학습 테이블 초기화**: create_learning_tables.py
- **관리자 대시보드**: admin_dashboard.html
- **식자재 관리**: ingredients_management.html (성능 최적화 완료)

### 🎯 주요 개선사항
- **성능 최적화**: 1,000개 식자재 빠른 로딩 (2-3초)
- **전체 검색**: 84,215개 전체 데이터베이스 검색
- **AI 학습**: 패턴 기반 단가 계산 정확도 향상
- **유니코드 안전**: Windows 환경 한글 파일명 처리

### 🔧 배포 설정
- **운영 서버**: 34.64.237.181 (sos1253 계정)
- **배포 경로**: /home/daham/app
- **포트**: 8010
- **배포 패키지**: daham_deploy_20250920_171807.zip (621개 파일)

---

## 🚨 주의사항

### Git 사용 시 주의점
- **첫 번째 push**: `git push -u origin main` (이후에는 `git push`만)
- **민감한 파일**: .gitignore에 이미 설정됨 (백업 파일, 로그 등 제외)
- **대용량 파일**: Git LFS 사용 고려 (100MB 이상 파일)

### 서버 배포 시 주의점
- **Python 버전**: python3 사용 (python2 아님)
- **권한 설정**: chmod +x *.py 필수
- **포트 충돌**: 기존 8010 포트 사용 프로세스 확인
- **방화벽**: 포트 8010 개방 확인

---

## 🔄 향후 업데이트 방법

### 로컬에서 수정 후 배포
```bash
# 1. 로컬에서 파일 수정
# 2. GitHub에 업로드
git add .
git commit -m "수정사항 설명"
git push

# 3. 운영 서버에서 업데이트
ssh sos1253@34.64.237.181
cd /home/daham/app
git pull
python3 ★test_samsung_api.py
```

### 웹 브라우저에서 직접 수정
```
1. GitHub.com → 저장소 접속
2. 파일 클릭 → Edit 버튼
3. 수정 후 Commit changes
4. 서버에서 git pull
```

---

## 📞 문제 해결 가이드

### Git 관련 문제
- **인증 오류**: Personal Access Token 생성 필요
- **충돌 오류**: git pull 먼저 실행 후 push
- **파일 크기**: 100MB 이상 파일은 Git LFS 사용

### 서버 관련 문제
- **포트 충돌**: `netstat -tulpn | grep 8010`으로 확인
- **권한 문제**: `chmod 644 daham_meal.db` 실행
- **Python 오류**: `python3 --version` 확인

---

**📅 마지막 업데이트**: 2025-09-20 17:30
**🔥 중요**: Git 설치 완료 후 이 파일을 참고하여 즉시 GitHub 배포 진행!