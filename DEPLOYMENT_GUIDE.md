# 🚀 다함푸드 클라우드 배포 가이드

## 🎯 현재 상황 분석
- ✅ 도메인 구매: `dahamfood.kr`
- ✅ DNS A 레코드 설정 완료 (www.dahamfood.kr → 125.247.255.182)
- ❌ 현재 로컬 개발환경 → 클라우드 환경으로 변경 필요

## 📋 클라우드 배포 옵션

### 옵션 1: AWS EC2 (추천)
```bash
# 1. EC2 인스턴스 생성 (Ubuntu 20.04)
# 2. 도메인 DNS 변경: 125.247.255.182 → EC2 퍼블릭 IP

# 3. 서버에 코드 업로드
scp -r daham-meal-management/ ubuntu@your-ec2-ip:/home/ubuntu/

# 4. 서버에서 실행
ssh ubuntu@your-ec2-ip
cd /home/ubuntu/daham-meal-management
sudo apt update && sudo apt install docker.io docker-compose -y
sudo docker-compose up -d
```

### 옵션 2: DigitalOcean Droplet
```bash
# 1. Droplet 생성 ($6/월)
# 2. DNS 변경: A 레코드를 Droplet IP로
# 3. 동일한 Docker 배포 과정
```

### 옵션 3: 현재 서버 활용 (125.247.255.182)
```bash
# 현재 IP가 이미 설정되어 있으므로 바로 사용 가능
# 1. 해당 서버에 SSH 접속
# 2. Python 환경 설정
# 3. 애플리케이션 배포
```

## 🔧 배포 전 필수 수정사항

### 1. API 서버 설정 변경
현재 개발용 설정을 프로덕션용으로 변경:

```python
# ★test_samsung_api.py 수정 필요
if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))  # 8010 → 8080
    host = os.getenv("API_HOST", "0.0.0.0")

    print(f"🚀 다함푸드 API 서버 시작: {host}:{port}")
    uvicorn.run(app, host=host, port=port)
```

### 2. 프론트엔드 설정 변경
```html
<!-- HTML 파일들에서 config.js → config_production.js 로 변경 -->
<script src="config_production.js"></script>
```

### 3. 데이터베이스 경로 수정
```python
# 절대 경로로 변경
DATABASE_PATH = os.getenv("DATABASE_PATH", "/app/data/daham_meal.db")
```

## 🐳 Docker 배포 (추천)

### 1. Docker 이미지 빌드
```bash
docker build -t daham-food .
```

### 2. 컨테이너 실행
```bash
docker run -d -p 80:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/backups:/app/backups \
  --name daham-food \
  daham-food
```

### 3. Docker Compose 사용 (더 쉬운 방법)
```bash
docker-compose up -d
```

## 🌐 Nginx 리버스 프록시 설정

### nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    upstream daham_app {
        server daham-app:8080;
    }

    server {
        listen 80;
        server_name dahamfood.kr www.dahamfood.kr;

        location / {
            proxy_pass http://daham_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
```

## 🔒 SSL 인증서 설정 (HTTPS)

### Let's Encrypt 무료 SSL
```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d dahamfood.kr -d www.dahamfood.kr

# 자동 갱신 설정
sudo crontab -e
# 추가: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 배포 후 확인사항

### 1. 웹사이트 접속 확인
- http://dahamfood.kr
- http://www.dahamfood.kr

### 2. API 엔드포인트 확인
- http://dahamfood.kr/api/admin/dashboard-stats

### 3. 로그인 기능 확인
- 관리자 로그인
- 협력업체 로그인

## 🚨 주의사항

### 1. 환경 변수 설정
```bash
# .env 파일 생성
PORT=8080
API_HOST=0.0.0.0
DATABASE_PATH=/app/data/daham_meal.db
SECRET_KEY=your-secret-key-here
```

### 2. 방화벽 설정
```bash
# Ubuntu/Debian
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### 3. 데이터베이스 백업
```bash
# 정기 백업 스크립트
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp /app/data/daham_meal.db /app/backups/daham_meal_backup_$DATE.db
```

## 🎉 배포 완료 후

1. ✅ http://dahamfood.kr 접속 확인
2. ✅ 로그인 기능 테스트
3. ✅ 데이터 정상 로드 확인
4. ✅ 모든 메뉴 기능 동작 확인

## 🆘 문제 해결

### 포트 80 권한 오류
```bash
# 1. 포트 8080으로 변경 후 Nginx 프록시
# 2. 또는 sudo로 실행
sudo docker-compose up -d
```

### DNS 전파 확인
```bash
# DNS 전파 상태 확인
nslookup dahamfood.kr
```

### 로그 확인
```bash
# Docker 로그 확인
docker logs daham-food

# Nginx 로그 확인
docker logs nginx_container_name
```

---

**다음 단계**: 위 옵션 중 하나를 선택하여 배포를 진행하세요. AWS EC2를 추천하며, Docker를 사용하면 배포가 매우 간단해집니다.