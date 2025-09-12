# 🚀 식자재 관리 시스템 API 빠른 연결 가이드

## 📋 현재 작업 상태 (2025-09-12 백업)

### ✅ **작동 중인 구성**
- **메인 API**: `main.py` (Port: 8000)
- **테스트 API**: `test_samsung_api.py` (Port: 8006) ⭐ **주 사용 API**
- **프론트엔드**: `ingredients_management.html`
- **데이터베이스**: `daham_meal.db`

### 🔌 **API 연결 상태**
```
✅ test_samsung_api.py:8006 → ingredients_management.html
   - 업체별 식자재 현황 정상 표시
   - 84,215개 식자재 데이터 로드
   - 5개 주요 업체 (삼성웰스토리, 현대그린푸드, CJ, 푸디스트, 동원홈푸드)
```

## ⚡ **30초 빠른 시작**

### 1️⃣ **API 서버 시작**
```bash
# 백그라운드에서 테스트 API 실행
python test_samsung_api.py &
```

### 2️⃣ **연결 확인**
```bash
# API 응답 테스트 (5초 이내)
curl "http://127.0.0.1:8006/all-ingredients-for-suppliers?limit=1"
```

### 3️⃣ **프론트엔드 실행**
```bash
# 브라우저에서 페이지 열기
start ingredients_management.html
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

### **🔍 Debug Endpoints**
```
GET http://127.0.0.1:8006/test-samsung-welstory        # 삼성웰스토리 특정 데이터
GET http://127.0.0.1:8006/supplier-ingredients/CJ      # CJ 특정 데이터
```

## 🚨 **문제 해결 (Troubleshooting)**

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

### **빈 supplier_stats**
```bash
# SQL 직접 확인
sqlite3 daham_meal.db "SELECT supplier_name, COUNT(*) FROM ingredients GROUP BY supplier_name LIMIT 5;"
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

## 🏆 **성공 지표**
- [x] API 서버 30초 내 시작
- [x] 프론트엔드 10초 내 로드
- [x] 업체별 박스 5개 업체 표시
- [x] 식자재 데이터 84,215개 확인
- [x] 페이지네이션 정상 작동

---

**💡 Tip**: 이 가이드를 따르면 처음부터 다시 설정하는 대신 즉시 작업을 재개할 수 있습니다!