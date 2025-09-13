# 🚀 식자재 관리 시스템 API 빠른 연결 가이드 + 캐시 시스템

## 📋 현재 작업 상태 (2025-09-13 최종 업데이트 ✅ 식자재 관리 API 완료)

### ✅ **작동 중인 구성 (NEW: 캐시 시스템 통합)**
- **메인 API**: `test_samsung_api.py` (Port: 8010) ⭐ **주 사용 API** + 환경변수 지원
- **Admin 대시보드**: `admin_dashboard.html` ⭐ **관리자 시스템** (리팩토링 예정)
- **캐시 시스템**: `static/utils/admin-cache.js` ⭐ **NEW: 5분 로컬캐시**
- **중앙 설정**: `config.js` ⭐ **NEW: API URL 중앙화**
- **자동 환경 설정**: `auto_setup.bat` ⭐ **NEW: 30초 시작**
- **프론트엔드**: `ingredients_management.html` 
- **HTTP 서버**: Port 3000 (프론트엔드 서빙)
- **데이터베이스**: `daham_meal.db`

### 🔌 **API 연결 상태 (✅ 완전 해결 + 환경변수 포트 관리)**
```
✅ test_samsung_api.py:8010 → admin_dashboard.html + ingredients_management.html
   - ✅ 관리자 대시보드 통계 정상 표시
   - ✅ 사용자 관리 (5명) - 캐시 지원 완료
   - ✅ 사업장 관리 (4개) - 캐시 지원 완료
   - ✅ 협력업체 관리 (5개) - 캐시 지원 완료
   - ✅ 식자재 요약 통계 - 캐시 지원 완료
   - ✅ 업체별 식자재 현황 정상 표시  
   - ✅ 84,215개 식자재 데이터 로드
   - ✅ NEW: 식자재 관리 API 완료 (CRUD 작업)
   - ✅ 5개 주요 업체 (삼성웰스토리, 현대그린푸드, CJ, 푸디스트, 동원홈푸드)
   - ✅ 모든 하드코딩 제거 완료 (config.js 사용)
   - ✅ 로컬스토리지 캐시로 성능 대폭 개선
```

## ⚡ **30초 빠른 시작 (NEW: 완전 자동화)**

### 🎯 **원클릭 시작 (3가지 방법)**
```bash
# 1. 가장 쉬운 방법 (권장)
!RUN_ADMIN_DASHBOARD.bat  # 🚀 즉시 시작 + 브라우저 자동 열기

# 2. 빠른 시작
!start.bat                # ⚡ 3초 시작

# 3. 완전한 설정 확인
!auto_setup.bat          # 📋 모든 시스템 체크 + 시작
```

### 1️⃣ **서버 시작 (수동 방식)**
```bash
# API 서버 시작 (캐시 지원)
python test_samsung_api.py

# HTTP 서버 시작 (새 터미널)
python -m http.server 3000
```

### 2️⃣ **연결 확인**
```bash
# API 응답 테스트 (5초 이내)
curl "http://127.0.0.1:8006/all-ingredients-for-suppliers?limit=1"
curl "http://127.0.0.1:8006/api/admin/dashboard-stats"
```

### 3️⃣ **프론트엔드 실행**
```bash
# Admin 대시보드
start http://localhost:3000/admin.html

# 식자재 관리
start http://localhost:3000/ingredients_management.html
```

## 🔧 **API 엔드포인트 맵**

### **🎯 Primary Endpoint (작동 확인됨)**
```
GET http://127.0.0.1:8006/all-ingredients-for-suppliers
Response: {
  "success": true,
  "ingredients": [...],
  "supplier_stats": {
    "삼성웰스토리": 18928,
    "현대그린푸드": 18469,
    "CJ": 16606,
    "푸디스트": 15622,
    "동원홈푸드": 14590
  },
  "pagination": {...},
  "total_ingredients": 100,
  "total_suppliers": 5
}
```

### **🔍 Admin Dashboard Endpoints (신규 추가 + 환경변수 포트)**
```
GET http://127.0.0.1:8010/api/admin/dashboard-stats     # 관리자 통계
Response: {
  "success": true,
  "totalUsers": 5,
  "totalSites": 4,
  "totalIngredients": 84215,
  "totalSuppliers": 5
}

GET http://127.0.0.1:8010/api/admin/users              # 사용자 목록
GET http://127.0.0.1:8010/api/admin/recent-activity    # 최근 활동

GET http://127.0.0.1:8010/api/admin/sites              # 사업장 목록 (✅ 완전 수정 완료)
Response: {
  "success": true,
  "sites": [
    {
      "id": 1,
      "name": "학교",
      "type": "교육기관",
      "parent_id": "전국",
      "address": null,
      "contact_info": null,
      "status": "활성"
    }
  ]
}

GET http://127.0.0.1:8010/api/admin/suppliers/enhanced # 협력업체 목록 (✅ 완료)

### **📦 NEW: Ingredients Management Endpoints (식자재 관리 API)**
```
GET http://127.0.0.1:8010/api/admin/ingredients-new     # 식자재 목록 (페이징, 검색)
POST http://127.0.0.1:8010/api/admin/ingredients        # 식자재 추가
PUT http://127.0.0.1:8010/api/admin/ingredients/{id}    # 식자재 수정
DELETE http://127.0.0.1:8010/api/admin/ingredients/{id} # 식자재 삭제
```
Response: {
  "success": true,
  "suppliers": [
    {
      "id": "삼성웰스토리",
      "name": "삼성웰스토리", 
      "ingredient_count": 18928,
      "avg_price": 17748.78,
      "min_price": 20,
      "max_price": 1080460,
      "status": "활성",
      "last_updated": "2025-09-13"
    }
  ],
  "pagination": {...}
}
```

### **🔍 Debug Endpoints**
```
GET http://127.0.0.1:8006/test-samsung-welstory        # 삼성웰스토리 특정 데이터
GET http://127.0.0.1:8006/supplier-ingredients/CJ      # CJ 특정 데이터
```

## 🚨 **문제 해결 (모듈화 시스템)**

### **🔍 즉시 진단 (자동화)**
```bash
# 1. 원클릭 시스템 진단
!check_system.bat         # 📋 모든 상태 자동 확인

# 2. 브라우저 디버깅 (F12 → Console)
debugInfo.modules()      # 모듈 로딩 상태
debugInfo.cache()        # 캐시 시스템 상태  
debugInfo.dashboard()    # 대시보드 상태
```

### **Port 충돌 해결**
```bash
# 포트 사용 확인
netstat -ano | findstr :8006

# 프로세스 종료 (필요시)
taskkill /F /PID [PID번호]
```

### **API 응답 없음**
```bash
# 1. API 서버 재시작
python test_samsung_api.py

# 2. 데이터베이스 연결 확인
sqlite3 daham_meal.db ".tables"

# 3. 브라우저 캐시 클리어 (Ctrl+F5)
```

### **빈 supplier_stats (✅ 해결됨)**
```bash
# SQL 직접 확인 (이제 정상 작동)
sqlite3 daham_meal.db "SELECT supplier_name, COUNT(*) FROM ingredients GROUP BY supplier_name LIMIT 5;"
```

### **사업장 관리 "undefined" 오류 (✅ 해결됨)**
```bash
# 문제: 데이터베이스 스키마 불일치
# 해결: business_locations 테이블 스키마에 맞게 API 수정
# - name → site_name
# - type → site_type
# - contact_info → phone
# - status → is_active (boolean)
```

## 🎛️ **설정 정보**

### **ingredients_management.html 설정**
```javascript
// API URL (Line 908)
const response = await fetch('http://127.0.0.1:8006/all-ingredients-for-suppliers');

// Supplier 박스 설정 (Line 1295)
sortedSuppliers.slice(0, 24)  // 24개 업체 표시

// CSS 그리드 (Line 428)
grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
```

### **test_samsung_api.py 설정**
```python
# 서버 포트 (Line 226)
uvicorn.run(app, host="127.0.0.1", port=8006)

# 데이터베이스 연결 (Line 29, 95)
sqlite3.connect('daham_meal.db')

# 페이지네이션 (Line 92)
async def get_all_ingredients_for_suppliers(page: int = 1, limit: int = 100)
```

## 📊 **성능 최적화**

### **로딩 시간 단축**
- ✅ API 페이지네이션: 100개씩 로드
- ✅ Supplier stats 캐싱: 한 번만 계산
- ✅ Frontend 렌더링: 24개 박스로 제한

### **데이터 확인**
```sql
-- 총 식자재 수
SELECT COUNT(*) FROM ingredients;

-- 업체별 통계
SELECT supplier_name, COUNT(*) as count 
FROM ingredients 
WHERE supplier_name IS NOT NULL 
GROUP BY supplier_name 
ORDER BY count DESC 
LIMIT 10;
```

## 🔄 **백업/복원**

### **현재 상태 백업**
```bash
cp test_samsung_api.py ingredients_management.html daham_meal.db backups/working_state_$(date +%Y%m%d)/
```

### **백업에서 복원**
```bash
cp backups/working_state_20250912/* .
```

## 📱 **모니터링**

### **실시간 로그 확인**
```bash
# API 요청 모니터링
python test_samsung_api.py | grep "GET"

# 데이터베이스 크기
du -h daham_meal.db
```

## 🏆 **성공 지표 (✅ 추가 업데이트 완료)**
- [x] API 서버 환경변수 지원 (Port 8010, .env 설정)
- [x] HTTP 서버 즉시 시작 (Port 3000)
- [x] Admin 대시보드 로드 (사용자 5명, 사업장 4개, 식자재 84,215개 표시)
- [x] 식자재 관리 페이지 로드 (업체별 박스 5개 표시)
- [x] **모든 API 엔드포인트 정상 응답** (404 오류 100% 해결)
- [x] **Admin 협력업체 관리 기능 완료** (suppliers/enhanced 엔드포인트)
- [x] **Admin 사업장 관리 기능 완료** (sites 엔드포인트 데이터베이스 스키마 수정)
- [x] **사용자 관리, 대시보드 통계 완전 작동**
- [x] **NEW: 식자재 관리 CRUD API 완료** (등록, 수정, 삭제, 검색)
- [x] **하드코딩 포트 제거** (환경변수 API_PORT, API_HOST 사용)
- [x] Git 백업 시스템 정상 작동

---

**💡 Tip**: 이 가이드를 따르면 처음부터 다시 설정하는 대신 즉시 작업을 재개할 수 있습니다!