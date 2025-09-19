# 🚀 구글 클라우드 배포 가이드 - 다함푸드

## 🎯 Google Cloud Platform (GCP) 배포

### ✅ 왜 구글 클라우드?
- **$300 무료 크레딧** (새 계정)
- **한국 서버** (Seoul Region)
- **안정적인 성능**
- **간단한 설정**

## 📋 1단계: GCP 계정 생성

1. **Google Cloud Console 접속**
   - https://console.cloud.google.com/
   - Gmail 계정으로 로그인

2. **새 프로젝트 생성**
   - 프로젝트 이름: `daham-food`
   - 위치: 조직 없음

3. **결제 계정 설정**
   - $300 무료 크레딧 활성화
   - 신용카드 등록 (무료 기간 중 과금 없음)

## 🖥️ 2단계: VM 인스턴스 생성

### Compute Engine → VM 인스턴스 → 만들기

**기본 설정:**
```
이름: daham-food-server
지역: asia-northeast3 (서울)
영역: asia-northeast3-a
```

**머신 구성:**
```
시리즈: E2
머신 유형: e2-small (2 vCPU, 2GB 메모리)
월 예상 비용: ~$15
```

**부팅 디스크:**
```
운영체제: Ubuntu
버전: Ubuntu 20.04 LTS
부팅 디스크 유형: 표준 영구 디스크
크기: 20GB
```

**방화벽:**
```
✅ HTTP 트래픽 허용
✅ HTTPS 트래픽 허용
```

## 🔑 3단계: SSH 접속 설정

### 방법 1: 브라우저 SSH (가장 쉬움)
1. VM 인스턴스 목록에서 **SSH** 버튼 클릭
2. 새 브라우저 창에서 터미널 열림

### 방법 2: 로컬 SSH (Windows)
```bash
# Google Cloud SDK 설치 (선택사항)
gcloud compute ssh daham-food-server --zone=asia-northeast3-a
```

## 📦 4단계: 서버 환경 설정

### Docker 설치
```bash
# 패키지 업데이트
sudo apt update

# Docker 설치
sudo apt install docker.io docker-compose -y

# Docker 서비스 시작
sudo systemctl start docker
sudo systemctl enable docker

# 현재 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER

# 로그아웃 후 재로그인 (또는 newgrp docker)
newgrp docker
```

## 📁 5단계: 코드 업로드

### 방법 1: GitHub 사용 (추천)
```bash
# Git 설치
sudo apt install git -y

# 코드 클론 (GitHub에 업로드 필요)
git clone https://github.com/your-username/daham-meal-management.git
cd daham-meal-management
```

### 방법 2: 파일 직접 업로드
```bash
# 로컬에서 실행 (개발 컴퓨터)
# WinSCP 또는 SCP 사용하여 파일 업로드
scp -r daham-meal-management/ username@외부IP:/home/username/
```

### 방법 3: Google Cloud Console 파일 업로드
1. SSH 터미널에서 **⚙️ 설정** → **파일 업로드**
2. ZIP 파일로 압축하여 업로드
3. `unzip daham-meal-management.zip`

## 🚀 6단계: 애플리케이션 배포

```bash
# 프로젝트 디렉토리로 이동
cd daham-meal-management

# 환경 설정 파일 생성
cat > .env << EOF
PORT=8080
API_HOST=0.0.0.0
DATABASE_PATH=/app/data/daham_meal.db
BACKUP_PATH=/app/backups/
EOF

# Docker Compose로 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f
```

## 🌐 7단계: 방화벽 설정

### GCP 방화벽 규칙 생성
```bash
# HTTP 트래픽 허용 (포트 80)
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP traffic"

# HTTPS 트래픽 허용 (포트 443)
gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTPS traffic"

# 애플리케이션 포트 허용 (포트 8080)
gcloud compute firewall-rules create allow-app \
    --allow tcp:8080 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow application traffic"
```

### 또는 Console에서 설정:
1. **VPC 네트워크** → **방화벽**
2. **방화벽 규칙 만들기**
3. 트래픽 방향: 수신, 대상: 지정된 대상 태그
4. 포트: 80, 443, 8080 허용

## 📡 8단계: DNS 설정 변경

### 1. VM 외부 IP 확인
```bash
# 외부 IP 주소 확인
gcloud compute instances list
```

### 2. 카페24 DNS 설정 변경
```
A 레코드 수정:
호스트: @
값: [GCP VM 외부 IP]

A 레코드 수정:
호스트: www
값: [GCP VM 외부 IP]
```

### 3. DNS 전파 확인 (5-10분 소요)
```bash
# DNS 확인
nslookup dahamfood.kr
nslookup www.dahamfood.kr
```

## 🔒 9단계: SSL 인증서 설정 (HTTPS)

### Let's Encrypt 무료 SSL
```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx -y

# Nginx 설치
sudo apt install nginx -y

# Nginx 설정
sudo nano /etc/nginx/sites-available/daham-food
```

**Nginx 설정 파일:**
```nginx
server {
    listen 80;
    server_name dahamfood.kr www.dahamfood.kr;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 설정 활성화
sudo ln -s /etc/nginx/sites-available/daham-food /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# SSL 인증서 발급
sudo certbot --nginx -d dahamfood.kr -d www.dahamfood.kr
```

## ✅ 10단계: 배포 완료 확인

### 웹사이트 접속 테스트
- ✅ http://dahamfood.kr
- ✅ https://dahamfood.kr
- ✅ https://www.dahamfood.kr

### API 테스트
```bash
# API 응답 확인
curl http://dahamfood.kr/api/admin/dashboard-stats
```

### 기능 테스트
1. ✅ 로그인 페이지 접속
2. ✅ 관리자 로그인 테스트
3. ✅ 협력업체 로그인 테스트
4. ✅ 대시보드 데이터 로드

## 🔧 관리 및 모니터링

### 서버 상태 확인
```bash
# Docker 컨테이너 상태
docker ps

# 애플리케이션 로그
docker-compose logs -f

# 시스템 리소스 확인
htop
df -h
```

### 자동 백업 설정
```bash
# 백업 스크립트 생성
sudo nano /home/username/backup.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cd /home/username/daham-meal-management
docker-compose exec daham-app cp /app/data/daham_meal.db /app/backups/backup_$DATE.db
```

```bash
# 실행 권한 부여
chmod +x /home/username/backup.sh

# Cron 작업 추가 (매일 새벽 2시)
crontab -e
# 추가: 0 2 * * * /home/username/backup.sh
```

## 💰 비용 관리

### 예상 월 비용 (Seoul Region)
- **e2-small**: ~$15/월
- **디스크 20GB**: ~$2/월
- **네트워크**: ~$1/월
- **총합**: ~$18/월

### 비용 절약 팁
1. **프리 티어 활용** ($300 크레딧)
2. **인스턴스 스케줄링** (야간 자동 종료)
3. **디스크 정리** (로그 파일 관리)

## 🆘 문제 해결

### 일반적인 문제들

**1. 포트 접속 안됨**
```bash
# 방화벽 상태 확인
sudo ufw status
gcloud compute firewall-rules list
```

**2. Docker 권한 오류**
```bash
# Docker 그룹 확인
groups $USER
newgrp docker
```

**3. 메모리 부족**
```bash
# 메모리 사용량 확인
free -h
# 필요시 인스턴스 타입 업그레이드
```

**4. SSL 인증서 갱신**
```bash
# 인증서 갱신 테스트
sudo certbot renew --dry-run

# 자동 갱신 설정
sudo crontab -e
# 추가: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🎉 배포 완료!

축하합니다! 다함푸드 시스템이 구글 클라우드에 성공적으로 배포되었습니다.

### 최종 접속 주소:
- **메인 사이트**: https://dahamfood.kr
- **관리자**: https://dahamfood.kr/admin_dashboard.html
- **협력업체**: https://dahamfood.kr/supplier_login.html

### 다음 단계:
1. 📊 모니터링 설정
2. 🔒 보안 강화
3. 📈 성능 최적화
4. 🔄 정기 백업 자동화

---

**문제 발생시**:
- GCP 콘솔에서 로그 확인
- SSH로 서버 접속하여 디버깅
- Docker 로그 확인: `docker-compose logs`