# 🚀 다함 식자재 관리 시스템 - GitHub 배포 가이드

## 🎯 GitHub 배포의 장점 (초보자 추천!)
- ✅ **버전 관리**: 코드 변경 이력 자동 추적
- ✅ **쉬운 배포**: 파일 업로드만으로 배포 완료
- ✅ **협업 가능**: 팀원과 함께 개발 가능
- ✅ **무료 사용**: GitHub 계정만 있으면 OK
- ✅ **롤백 간편**: 문제 발생시 이전 버전으로 쉽게 복구

## 📋 GitHub 배포 단계별 가이드 (초보자용)

### 🚀 방법 1: GitHub + 운영 서버 (추천!)

#### 1단계: GitHub 저장소 생성
```
1. GitHub.com 접속 → 로그인
2. "New Repository" 클릭
3. Repository name: "daham-meal-management"
4. Private 선택 (중요!)
5. "Create repository" 클릭
```

#### 2단계: 로컬 코드를 GitHub에 업로드
```bash
# Windows에서 실행 (Git Bash 또는 명령 프롬프트)
cd C:\Dev\daham-meal-management

# Git 초기화 (처음에만)
git init
git branch -M main

# GitHub 저장소 연결
git remote add origin https://github.com/당신의계정명/daham-meal-management.git

# 파일 추가 및 커밋
git add .
git commit -m "다함 식자재 관리 시스템 - 최초 업로드"

# GitHub에 업로드
git push -u origin main
```

#### 3단계: 운영 서버에서 GitHub에서 다운로드
```bash
# 운영 서버 SSH 접속
ssh sos1253@34.64.237.181

# GitHub에서 코드 다운로드
cd /home/daham
git clone https://github.com/당신의계정명/daham-meal-management.git app

# 애플리케이션 시작
cd app
python ★test_samsung_api.py
```

### 🔄 업데이트 및 재배포 (매우 간단!)

#### 방법 1: 웹 브라우저에서 직접 수정
```
1. GitHub.com → 본인 저장소 접속
2. 수정할 파일 클릭 (예: ★test_samsung_api.py)
3. "Edit this file" (연필 아이콘) 클릭
4. 코드 수정
5. "Commit changes" 클릭
6. 운영 서버에서 git pull 실행
```

#### 방법 2: 로컬에서 수정 후 업로드
```bash
# 로컬에서 파일 수정 후
git add .
git commit -m "식자재 관리 기능 개선"
git push

# 운영 서버에서 업데이트
ssh sos1253@34.64.237.181
cd /home/daham/app
git pull
python ★test_samsung_api.py
```

## 🛠️ GitHub 초보자 가이드

### Git 설치 (Windows)
```
1. https://git-scm.com/download/win 접속
2. Git for Windows 다운로드 및 설치
3. Git Bash 실행 (시작 메뉴에서 검색)
```

### GitHub 계정 설정
```bash
# Git 사용자 정보 설정 (처음에만)
git config --global user.name "당신의이름"
git config --global user.email "당신의이메일@example.com"
```

## 🔧 프로젝트 설정 (중요!)

### .gitignore 파일 생성
```bash
# C:\Dev\daham-meal-management\.gitignore 파일 생성
# 민감한 파일들을 GitHub에 업로드하지 않도록 설정

# 백업 파일들
backups/
*.db-shm
*.db-wal
*_backup_*.db

# 로그 파일들
*.log
server_log.txt

# 임시 파일들
*.tmp
*.temp
deploy_package/
daham_deploy_*.zip

# 개발 도구
.vscode/
__pycache__/
*.pyc

# 민감한 설정 파일 (있다면)
.env
secrets.txt
```

### README.md 파일 생성
```markdown
# 다함 식자재 관리 시스템

## 🚀 빠른 시작
```bash
# 코드 다운로드
git clone https://github.com/당신의계정명/daham-meal-management.git

# 실행
cd daham-meal-management
python ★test_samsung_api.py
```

## 📊 주요 기능
- 84,215개 식자재 데이터 관리
- AI 학습 기반 단가 계산
- 실시간 검색 및 필터링
- 협력업체 매핑 관리
- 사용자 권한 관리

## 🌐 접속 정보
- 관리자 대시보드: http://localhost:8010/admin_dashboard.html
- 식자재 관리: http://localhost:8010/ingredients_management.html
```

## 🚨 자주 발생하는 문제들 (FAQ)

### Q1: "git: command not found" 오류가 발생해요
```bash
# Windows: Git for Windows 설치 필요
# https://git-scm.com/download/win 에서 다운로드

# 설치 후 Git Bash 또는 명령 프롬프트에서 확인
git --version
```

### Q2: GitHub에 파일 업로드가 안 돼요
```bash
# 인증 설정 확인
git config --global user.name "당신의이름"
git config --global user.email "당신의이메일"

# Personal Access Token 생성 (GitHub.com)
# Settings → Developer settings → Personal access tokens → Generate new token
# repo 권한 체크 후 생성된 토큰을 비밀번호 대신 사용
```

### Q3: 서버에서 "python: command not found" 오류
```bash
# Python 설치 확인
python3 --version
pip3 --version

# 필요시 Python 설치
sudo apt update
sudo apt install python3 python3-pip
```

### Q4: 데이터베이스 오류가 발생해요
```bash
# 데이터베이스 권한 설정
chmod 644 daham_meal.db

# 백업에서 복구
cp daham_meal_backup_최신날짜.db daham_meal.db
```

## 🎯 GitHub 배포의 핵심 명령어 정리

### 처음 설정할 때
```bash
git init
git remote add origin https://github.com/계정명/daham-meal-management.git
git add .
git commit -m "최초 업로드"
git push -u origin main
```

### 업데이트할 때 (매일 사용)
```bash
# 로컬에서 수정 후
git add .
git commit -m "수정사항 설명"
git push

# 서버에서 업데이트
git pull
```

### 문제 발생 시 복구
```bash
# 이전 버전으로 되돌리기
git log --oneline  # 커밋 이력 확인
git reset --hard 커밋ID  # 특정 커밋으로 복구
git push --force  # 강제 푸시 (주의!)
```

## 🎉 배포 완료 확인 체크리스트

- [ ] ✅ GitHub 저장소 생성 완료
- [ ] ✅ 로컬 코드 GitHub 업로드 완료
- [ ] ✅ 운영 서버에서 git clone 완료
- [ ] ✅ Python 서버 정상 실행
- [ ] ✅ 웹 브라우저에서 접속 확인
- [ ] ✅ 로그인 기능 테스트 완료
- [ ] ✅ 식자재 검색 기능 확인
- [ ] ✅ 단가 계산 기능 확인

## 💡 초보자를 위한 추가 팁

### Visual Studio Code 확장 프로그램 (추천)
- **Git Graph**: 커밋 이력을 시각적으로 확인
- **GitLens**: Git 관련 기능 강화
- **Python**: Python 개발 지원

### GitHub Desktop (GUI 도구)
```
명령어가 어려우면 GitHub Desktop 사용:
1. https://desktop.github.com/ 에서 다운로드
2. GUI로 쉽게 commit, push, pull 가능
3. 초보자에게 매우 편리함
```

### 백업 전략
```bash
# 정기적으로 데이터베이스 백업
# 운영 서버에서 실행
cp daham_meal.db daham_meal_backup_$(date +%Y%m%d).db

# GitHub에도 정기적으로 백업 업로드
git add daham_meal_backup_*.db
git commit -m "데이터베이스 백업"
git push
```

---

**🎉 축하합니다!** 이제 GitHub를 활용한 전문적인 배포 시스템을 구축했습니다!

**📞 도움이 필요하면**: GitHub Issues 탭을 활용하여 문제점을 기록하고 관리하세요.