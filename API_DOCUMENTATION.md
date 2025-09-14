# 📚 다함 식자재 관리 시스템 - API 문서

## 🌐 서버 구성

### 메인 서버
| 서버명 | 포트 | 파일 | 용도 | 상태 |
|--------|------|------|------|------|
| **메인 API 서버** | 8010 | test_samsung_api.py | 모든 API 엔드포인트 제공 | ✅ 운영중 |
| **정적 파일 서버** | 3000 | simple_server.py | HTML/CSS/JS 파일 서빙 | ✅ 운영중 |
| **통합 컨트롤 타워** | 8080 | unified_control_tower.py | 서버 관리 및 모니터링 | 🔄 선택적 |

### 레거시 서버 (사용 중단)
- daham_api.py (포트 8013) - 구버전 API
- server_manager.py - 구버전 서버 관리
- 기타 test_*.py 파일들

---

## 📡 API 엔드포인트 (포트: 8010)

### 1. 대시보드 API

#### 대시보드 통계
```
GET /api/admin/dashboard-stats
```
**응답:**
```json
{
  "success": true,
  "totalUsers": 5,
  "totalSites": 4,
  "totalIngredients": 84215,
  "totalSuppliers": 5
}
```

---

### 2. 사용자 관리 API

#### 사용자 목록 조회
```
GET /api/admin/users
```

#### 사용자 추가
```
POST /api/admin/users
Content-Type: application/json

{
  "username": "새사용자",
  "password": "비밀번호",
  "role": "admin"
}
```

#### 사용자 수정
```
PUT /api/admin/users/{user_id}
```

#### 사용자 삭제
```
DELETE /api/admin/users/{user_id}
```

---

### 3. 협력업체 관리 API

#### 협력업체 목록
```
GET /api/admin/suppliers
```

#### 협력업체 통계
```
GET /api/admin/suppliers/stats
```

#### 협력업체 추가
```
POST /api/suppliers
```

#### 협력업체 수정
```
PUT /api/suppliers/{supplier_id}
```

---

### 4. 사업장 관리 API

#### 사업장 목록
```
GET /api/admin/business-locations
```

#### 사업장 추가
```
POST /api/admin/sites
```

#### 사업장 수정
```
PUT /api/admin/sites/{site_id}
```

#### 사업장 삭제
```
DELETE /api/admin/sites/{site_id}
```

---

### 5. 식자재 관리 API

#### 식자재 목록 (페이징)
```
GET /api/admin/ingredients-new?page=1&limit=50&search=김치
```

**파라미터:**
- `page`: 페이지 번호 (기본값: 1)
- `limit`: 페이지당 항목 수 (기본값: 50)
- `search`: 검색어 (선택)
- `category`: 카테고리 필터 (선택)

#### 식자재 추가
```
POST /api/admin/ingredients
Content-Type: application/json

{
  "ingredient_name": "새 식자재",
  "category": "육류",
  "supplier_name": "삼성웰스토리",
  "purchase_price": 10000,
  "selling_price": 12000,
  "unit": "kg"
}
```

#### 식자재 수정
```
PUT /api/admin/ingredients/{ingredient_id}
```

#### 식자재 삭제
```
DELETE /api/admin/ingredients/{ingredient_id}
```

---

### 6. 협력업체 매핑 API

#### 매핑 목록
```
GET /api/admin/customer-supplier-mappings
```

#### 매핑 상세
```
GET /api/admin/customer-supplier-mappings/{mapping_id}
```

---

### 7. 식단가 관리 API

#### 식단가 목록
```
GET /api/admin/meal-pricing
```

**응답:**
```json
{
  "success": true,
  "meal_pricing": [
    {
      "id": 1,
      "location_id": 1,
      "location_name": "학교",
      "meal_plan_type": "중식",
      "meal_type": "급식",
      "plan_name": "학교 급식 중식",
      "selling_price": 5500,
      "material_cost_guideline": 2200,
      "cost_ratio": 40,
      "is_active": true
    }
  ],
  "statistics": {
    "total": 5,
    "active": 5,
    "locations": 4,
    "avg_selling_price": 8300,
    "avg_cost_ratio": 40
  }
}
```

#### 식단가 추가
```
POST /api/admin/meal-pricing
Content-Type: application/json

{
  "location_id": 1,
  "location_name": "학교",
  "meal_plan_type": "조식",
  "meal_type": "급식",
  "plan_name": "아침 급식",
  "selling_price": 4000,
  "material_cost_guideline": 1600,
  "cost_ratio": 40,
  "is_active": 1
}
```

#### 식단가 수정
```
PUT /api/admin/meal-pricing/{pricing_id}
```

#### 식단가 삭제
```
DELETE /api/admin/meal-pricing/{pricing_id}
```

---

## 🚀 서버 시작 방법

### 1. 통합 시작 (권장)
```batch
START_ALL_SERVERS.bat
```
- 모든 필요한 서버를 자동으로 시작
- 서버 모니터링 옵션 제공

### 2. 개별 서버 시작
```batch
# API 서버
python test_samsung_api.py

# 정적 파일 서버
python simple_server.py
```

### 3. 서버 모니터링
```batch
python server_monitor.py
```
- 실시간 서버 상태 확인
- 포트별 프로세스 정보
- 메모리 및 CPU 사용량
- 서버 시작/종료 제어

### 4. 서버 종료
```batch
STOP_ALL_SERVERS.bat
```

---

## 📁 프로젝트 구조

```
daham-meal-management/
│
├── 🚀 서버 관리
│   ├── START_ALL_SERVERS.bat     # 통합 서버 시작
│   ├── STOP_ALL_SERVERS.bat      # 모든 서버 종료
│   └── server_monitor.py         # 서버 모니터링 도구
│
├── 📡 API 서버
│   ├── test_samsung_api.py       # 메인 API 서버 (포트 8010)
│   └── simple_server.py          # 정적 파일 서버 (포트 3000)
│
├── 🌐 웹 인터페이스
│   ├── admin_dashboard.html      # 관리자 대시보드
│   └── static/                   # 정적 리소스
│       ├── css/                  # 스타일시트
│       ├── js/                   # JavaScript
│       └── modules/              # 기능별 모듈
│
├── 💾 데이터베이스
│   ├── daham_meal.db            # SQLite 데이터베이스
│   └── backups/                  # 백업 파일
│
└── 📚 문서
    ├── CLAUDE.md                 # 개발 가이드
    ├── API_DOCUMENTATION.md      # API 문서 (이 파일)
    └── README.md                 # 프로젝트 설명

```

---

## 🔧 개발 환경

- **Python**: 3.8+
- **데이터베이스**: SQLite3
- **프레임워크**: FastAPI, Flask
- **프론트엔드**: Vanilla JavaScript, HTML5, CSS3

---

## 📌 주의사항

1. **포트 충돌**: 8010, 3000 포트가 사용 중이면 서버 시작 실패
2. **인코딩**: Windows에서 UTF-8 인코딩 필수 (chcp 65001)
3. **데이터베이스**: daham_meal.db 파일 백업 권장
4. **브라우저**: Chrome 90+ 권장

---

## 🆘 문제 해결

### 포트 사용 중 오류
```batch
# 포트 확인
netstat -ano | findstr :8010

# 프로세스 종료
taskkill /F /PID [PID번호]
```

### 한글 깨짐
```batch
# UTF-8 설정
chcp 65001
```

### 모든 Python 프로세스 종료
```batch
taskkill /F /IM python.exe
```

---

## 📞 연락처

- **개발자**: 다함 IT팀
- **최종 업데이트**: 2025-01-14

---