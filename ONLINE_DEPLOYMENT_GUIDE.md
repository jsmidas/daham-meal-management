# 🌐 온라인 배포 가이드

## 🚨 보안 필수 사항

### 1. 인증 시스템 강화
```python
# 현재 문제: 메뉴 관리가 인증 없이 접근 가능
# 해결: JWT 토큰 기반 인증 추가

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/api/recipe/save")
async def save_recipe(request: Request, current_user: str = Depends(get_current_user)):
    # 인증된 사용자만 메뉴 저장 가능
    pass
```

### 2. 데이터베이스 보안
```sql
-- 사용자별 메뉴 소유권 확인
SELECT * FROM menu_recipes WHERE created_by = 'current_user';

-- 권한별 접근 제어
-- admin: 모든 메뉴 CRUD
-- nutritionist: 자신의 메뉴만 CRUD
-- viewer: 읽기 전용
```

## 📊 추가해야 할 DB 컬럼들

### 1. 메뉴 테이블 개선
```sql
ALTER TABLE menu_recipes ADD COLUMN visibility VARCHAR(20) DEFAULT 'private';
-- 'public', 'private', 'shared'

ALTER TABLE menu_recipes ADD COLUMN approved_by VARCHAR(100);
-- 관리자 승인 시스템

ALTER TABLE menu_recipes ADD COLUMN approval_status VARCHAR(20) DEFAULT 'pending';
-- 'pending', 'approved', 'rejected'

ALTER TABLE menu_recipes ADD COLUMN version INTEGER DEFAULT 1;
-- 메뉴 버전 관리

ALTER TABLE menu_recipes ADD COLUMN tags TEXT;
-- 검색용 태그 (JSON 형태)
```

### 2. 새로운 테이블 추가
```sql
-- 메뉴 공유 권한 테이블
CREATE TABLE menu_permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_id INTEGER,
    user_id INTEGER,
    permission_type VARCHAR(20), -- 'read', 'write', 'admin'
    granted_by VARCHAR(100),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (menu_id) REFERENCES menu_recipes(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 메뉴 변경 이력 테이블
CREATE TABLE menu_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_id INTEGER,
    action VARCHAR(50), -- 'create', 'update', 'delete', 'approve'
    changed_by VARCHAR(100),
    old_values TEXT, -- JSON
    new_values TEXT, -- JSON
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (menu_id) REFERENCES menu_recipes(id)
);

-- 사용자 세션 테이블
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    session_token VARCHAR(255),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## 🔒 보안 설정

### 1. 환경 변수 설정
```bash
# .env 파일 생성
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=sqlite:///./daham_meal.db
ADMIN_EMAIL=admin@daham.com
CORS_ORIGINS=https://yourdomain.com
```

### 2. CORS 설정
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # 실제 도메인만 허용
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### 3. Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/recipe/save")
@limiter.limit("10/minute")  # 분당 10회 제한
async def save_recipe(request: Request):
    pass
```

## 📱 사용자 경험 개선

### 1. 메뉴 공유 기능
- 사용자별 개인 메뉴 공간
- 공개 메뉴 갤러리
- 팀/부서별 공유 메뉴

### 2. 승인 워크플로우
- 영양사가 메뉴 등록 → 관리자 검토 → 승인/반려
- 승인된 메뉴만 공개 표시

### 3. 검색 및 필터링
- 카테고리별 검색
- 재료별 검색
- 가격대별 필터링
- 영양성분 기준 필터링

## 🚀 배포 환경 설정

### 1. 서버 보안
```bash
# HTTPS 필수
sudo certbot --nginx -d yourdomain.com

# 방화벽 설정
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. 데이터베이스 백업
```bash
# 정기 백업 크론잡
0 2 * * * /usr/bin/sqlite3 /path/to/daham_meal.db ".backup /backup/daham_meal_$(date +\%Y\%m\%d).db"
```

### 3. 모니터링
```python
# 로그 설정
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

## ⚠️ 주의사항

### 1. 데이터 유효성 검사 강화
- 모든 입력값 sanitization
- SQL injection 방지
- XSS 공격 방지

### 2. 파일 업로드 보안
- 이미지 파일 크기 제한
- 허용된 확장자만 업로드
- 바이러스 스캔

### 3. 개인정보 보호
- 사용자 데이터 암호화
- GDPR 준수
- 데이터 보존 정책

## 📈 성능 최적화

### 1. 데이터베이스 최적화
```sql
-- 인덱스 추가
CREATE INDEX idx_menu_recipes_created_by ON menu_recipes(created_by);
CREATE INDEX idx_menu_recipes_category ON menu_recipes(category);
CREATE INDEX idx_menu_recipes_created_at ON menu_recipes(created_at);
```

### 2. 캐싱
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

# Redis 캐싱 설정
FastAPICache.init(RedisBackend(), prefix="daham-cache")
```

## 🎯 단계별 배포 계획

### Phase 1: 기본 보안 (1주)
- [ ] JWT 인증 구현
- [ ] CORS 설정
- [ ] Rate limiting
- [ ] 기본 권한 시스템

### Phase 2: 사용자 기능 (2주)
- [ ] 메뉴 소유권 시스템
- [ ] 공유 기능
- [ ] 승인 워크플로우

### Phase 3: 고급 기능 (3주)
- [ ] 검색/필터링
- [ ] 파일 업로드 보안
- [ ] 모니터링 및 로깅

### Phase 4: 성능 최적화 (1주)
- [ ] 데이터베이스 최적화
- [ ] 캐싱 구현
- [ ] CDN 설정