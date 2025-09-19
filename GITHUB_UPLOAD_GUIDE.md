# 📚 GitHub 업로드 및 GCP 배포 가이드 - 다함푸드

## 🎯 개요
개발 PC의 코드를 GitHub에 업로드하고, GCP VM에서 다운로드하여 배포하는 전체 과정

---

## 📋 1단계: GitHub 저장소 생성

### 1.1 GitHub 웹사이트 접속
- https://github.com 접속
- 로그인

### 1.2 새 저장소 생성
1. **"+"** 버튼 클릭 → **"New repository"**
2. **Repository name**: `daham-food-system`
3. **Description**: `다함푸드 식단 관리 시스템`
4. **Public** 또는 **Private** 선택 (Private 추천)
5. **"Create repository"** 클릭

---

## 💻 2단계: 개발 PC에서 코드 업로드

### 2.1 Git 초기화 및 설정
```bash
# 프로젝트 폴더로 이동
cd C:\Dev\daham-meal-management

# Git 초기화
git init

# Git 사용자 정보 설정 (최초 1회만)
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

### 2.2 .gitignore 파일 생성
```bash
# .gitignore 파일 생성
echo "# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env

# Database
*.db-journal
*.sqlite3-journal

# Logs
*.log

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# Temporary files
temp/
tmp/
*.tmp

# Backup files
*.bak
*.backup" > .gitignore
```

### 2.3 파일 추가 및 커밋
```bash
# 모든 파일 추가 (중요 파일만)
git add .

# 첫 번째 커밋
git commit -m "🚀 다함푸드 식단 관리 시스템 - 초기 버전

- FastAPI 백엔드 서버
- 관리자 대시보드
- 협력업체 로그인 시스템
- 메뉴/레시피 관리
- SQLite 데이터베이스
- Docker 배포 설정 포함"
```

### 2.4 GitHub 원격 저장소 연결
```bash
# 원격 저장소 추가 (GitHub에서 복사한 URL 사용)
git remote add origin https://github.com/YOUR-USERNAME/daham-food-system.git

# 기본 브랜치 이름을 main으로 설정
git branch -M main

# GitHub에 업로드
git push -u origin main
```

---

## 🔐 3단계: GitHub 인증 설정

### 3.1 Personal Access Token 생성 (추천)
1. **GitHub** → **Settings** → **Developer settings**
2. **Personal access tokens** → **Tokens (classic)**
3. **"Generate new token"** 클릭
4. **Scopes** 선택:
   - `repo` (전체 저장소 액세스)
   - `workflow` (GitHub Actions)
5. **토큰 복사 및 안전한 곳에 보관**

### 3.2 인증 방법
```bash
# Username: GitHub 사용자명
# Password: 생성한 Personal Access Token 입력
```

---

## 🌐 4단계: GCP VM에서 코드 다운로드

### 4.1 VM SSH 접속
- **Google Cloud Console** → **Compute Engine** → **VM 인스턴스**
- **daham-food1** → **SSH** 버튼 클릭

### 4.2 Git 설치 및 코드 클론
```bash
# Git 설치
sudo apt update
sudo apt install git -y

# 홈 디렉토리로 이동
cd ~

# GitHub에서 코드 클론
git clone https://github.com/YOUR-USERNAME/daham-food-system.git

# 프로젝트 폴더로 이동
cd daham-food-system

# 파일 확인
ls -la
```

---

## 🐳 5단계: Docker로 애플리케이션 배포

### 5.1 환경 변수 설정
```bash
# .env 파일 생성
cat > .env << EOF
PORT=8080
API_HOST=0.0.0.0
DATABASE_PATH=/app/data/daham_meal.db
BACKUP_PATH=/app/backups/
SECRET_KEY=your-super-secret-key-change-this
EOF
```

### 5.2 데이터 디렉토리 생성
```bash
# 데이터 및 백업 디렉토리 생성
mkdir -p data backups

# 기존 데이터베이스 파일이 있다면 복사
if [ -f "backups/daham_meal.db" ]; then
    cp backups/daham_meal.db data/daham_meal.db
fi
```

### 5.3 Docker Compose로 실행
```bash
# Docker Compose 실행
sudo docker-compose up -d

# 실행 상태 확인
sudo docker-compose ps

# 로그 확인
sudo docker-compose logs -f
```

---

## 🔍 6단계: 배포 확인

### 6.1 애플리케이션 상태 확인
```bash
# 컨테이너 상태 확인
sudo docker ps

# 애플리케이션 로그 확인
sudo docker logs daham-food-system_daham-app_1

# 포트 확인
sudo netstat -tlnp | grep 8080
```

### 6.2 웹 접속 테스트
```bash
# 로컬에서 테스트
curl http://localhost:8080

# API 테스트
curl http://localhost:8080/api/admin/dashboard-stats
```

---

## 🌐 7단계: DNS 설정 업데이트

### 7.1 VM 외부 IP 확인
```bash
# 외부 IP 주소 확인
curl ifconfig.me
```

### 7.2 DNS 레코드 업데이트
**카페24 DNS 관리**에서:
```
A 레코드 수정:
호스트: @
값: [GCP VM 외부 IP]

A 레코드 수정:
호스트: www
값: [GCP VM 외부 IP]
```

---

## 🎉 8단계: 최종 확인

### 8.1 웹사이트 접속
- ✅ http://dahamfood.kr:8080
- ✅ http://www.dahamfood.kr:8080

### 8.2 주요 페이지 테스트
- ✅ **메인 로그인**: http://dahamfood.kr:8080/login.html
- ✅ **관리자 대시보드**: http://dahamfood.kr:8080/admin_dashboard.html
- ✅ **협력업체 로그인**: http://dahamfood.kr:8080/supplier_login.html
- ✅ **메뉴 관리**: http://dahamfood.kr:8080/menu_recipe_management.html

---

## 🔄 9단계: 코드 업데이트 시 (나중에)

### 9.1 개발 PC에서 변경사항 푸시
```bash
# 변경된 파일 추가
git add .

# 커밋 메시지 작성
git commit -m "✨ 새로운 기능 추가: 식단 통계 대시보드"

# GitHub에 푸시
git push origin main
```

### 9.2 VM에서 업데이트 적용
```bash
# SSH로 VM 접속
cd ~/daham-food-system

# 최신 코드 가져오기
git pull origin main

# Docker 컨테이너 재시작
sudo docker-compose down
sudo docker-compose up -d

# 상태 확인
sudo docker-compose logs -f
```

---

## 🛠️ 문제 해결

### 10.1 일반적인 문제들

**1. git push 권한 오류**
```bash
# Personal Access Token으로 다시 인증
git remote set-url origin https://YOUR-TOKEN@github.com/YOUR-USERNAME/daham-food-system.git
```

**2. Docker 권한 오류**
```bash
# 현재 사용자를 docker 그룹에 추가 후 재로그인
sudo usermod -aG docker $USER
logout
# SSH 재접속 후 sudo 없이 실행
```

**3. 포트 접근 불가**
```bash
# 방화벽 상태 확인
sudo ufw status

# 포트 8080 허용
sudo ufw allow 8080
```

**4. 데이터베이스 파일 오류**
```bash
# 데이터베이스 권한 설정
sudo chown -R $USER:$USER data/
chmod 644 data/daham_meal.db
```

### 10.2 유용한 명령어들

```bash
# 컨테이너 내부 접속
sudo docker exec -it daham-food-system_daham-app_1 bash

# 로그 실시간 확인
sudo docker-compose logs -f daham-app

# 시스템 리소스 확인
htop
df -h

# 네트워크 상태 확인
sudo netstat -tlnp
```

---

## 📚 부록: Git 기본 명령어

```bash
# 상태 확인
git status

# 변경사항 확인
git diff

# 커밋 이력 확인
git log --oneline

# 브랜치 확인
git branch -a

# 원격 저장소 확인
git remote -v

# 특정 파일 되돌리기
git checkout HEAD -- filename

# 마지막 커밋 수정
git commit --amend
```

---

## 🔒 보안 주의사항

### ⚠️ 절대 GitHub에 올리면 안 되는 것들:
- `.env` 파일 (환경 변수)
- `*.db` 파일 (데이터베이스)
- API 키, 비밀번호
- SSL 인증서
- 개인정보가 포함된 파일

### ✅ `.gitignore`에 반드시 추가:
```
.env
*.db
*.key
*.pem
secrets/
```

---

**🎯 이 가이드를 따라하면 30분 내에 GitHub에서 GCP로 완전한 배포가 가능합니다!**

**문제 발생 시**:
1. 단계별로 천천히 진행
2. 오류 메시지를 정확히 확인
3. 로그 파일 검토 (`docker-compose logs`)

**성공하면**: http://dahamfood.kr:8080 에서 다함푸드 시스템이 실행됩니다! 🚀