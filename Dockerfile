FROM python:3.9-slim

WORKDIR /app

# 시스템 패키지 업데이트 및 필요 패키지 설치
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Python 종속성 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 파일 복사
COPY . .

# 데이터 디렉토리 생성
RUN mkdir -p /app/data /app/backups

# 데이터베이스 파일 복사 (있는 경우)
RUN if [ -f "backups/daham_meal.db" ]; then cp backups/daham_meal.db /app/data/daham_meal.db; fi

# 포트 노출
EXPOSE 8080

# 환경 변수 설정
ENV PORT=8080
ENV API_HOST=0.0.0.0
ENV DATABASE_PATH=/app/data/daham_meal.db
ENV BACKUP_PATH=/app/backups/

# 서버 실행
CMD ["python", "★test_samsung_api.py"]