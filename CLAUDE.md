# 🍱 다함 식자재 관리 시스템 - 개발 가이드

## 📌 프로젝트 개요
다함 식자재 관리 시스템은 급식업체와 협력업체 간의 식자재 관리, 가격 관리, 매핑 관리를 통합한 웹 기반 관리 시스템입니다.

## 🚀 빠른 시작

### 1. 서버 시작 (한 번에 모든 서버 실행)
```bash
# Windows 환경
python test_samsung_api.py  # API 서버 (포트 8010)

# 또는 통합 컨트롤 타워 사용
python unified_control_tower.py  # 포트 8080
```

### 2. 관리자 대시보드 접속
```
http://127.0.0.1:8080/admin_dashboard.html
```

## 🏗️ 시스템 구조

### ⚠️ 중요: 모듈화 구조 유지
**admin_dashboard.html은 203줄의 뼈대만 유지합니다!**
- ❌ HTML 파일에 직접 스타일이나 스크립트 추가 금지
- ✅ 모든 기능은 별도 모듈로 분리
- ✅ 동적 로딩을 통한 확장

### 📁 주요 디렉토리 구조
```
daham-meal-management/
├── admin_dashboard.html          # 메인 대시보드 (203줄 뼈대만!)
├── test_samsung_api.py          # API 서버 (포트 8010)
├── unified_control_tower.py     # 통합 컨트롤 서버 (포트 8080)
├── daham_api.py                 # 레거시 API
├── backups/                     # 데이터베이스 백업
│   └── daham_meal.db           # SQLite 데이터베이스
├── static/                      # 정적 리소스
│   ├── css/                    # 스타일시트
│   │   ├── admin-dashboard-main.css     # 메인 스타일
│   │   └── admin-dashboard-styles.css   # 커스텀 스타일
│   ├── js/                     # JavaScript 파일
│   │   └── dashboard-init.js   # 초기화 스크립트 (308줄 분리)
│   ├── templates/              # HTML 템플릿 (동적 로드용)
│   │   ├── users-section.html  # 사용자 관리 섹션
│   │   ├── suppliers-section.html # 협력업체 섹션
│   │   └── sites-section.html  # 사업장 섹션
│   └── modules/                # 모듈별 JavaScript
│       ├── dashboard-core/     # 대시보드 코어
│       ├── ingredients/        # 식자재 관리
│       ├── suppliers/          # 협력업체 관리
│       ├── users/              # 사용자 관리
│       │   ├── users.js       # 사용자 관리 메인
│       │   ├── user-modal.html # 사용자 모달 (별도 파일)
│       │   └── user-permissions.js # 권한 관리 (10개 사업장)
│       ├── sites/              # 사업장 관리
│       ├── mappings/           # 협력업체 매핑
│       └── meal-pricing/       # 식단가 관리
└── config.js                    # 설정 파일
```

## 📊 데이터베이스 구조

### 주요 테이블
- **users**: 사용자 정보 (js, admin 등)
- **suppliers**: 협력업체 정보 (삼성웰스토리, 현대그린푸드, CJ, 푸디스트, 동원홈푸드 등)
- **business_locations**: 사업장 정보 (도시락, 운반, 학교, 요양원 등)
- **ingredients**: 식자재 정보 (84,215개 데이터)
- **customer_supplier_mappings**: 협력업체-사업장 매핑 (28개 매핑)

### 📈 현재 데이터 현황
- 총 식자재: 84,215개
- 주요 협력업체:
  - 삼성웰스토리: 18,928개
  - 현대그린푸드: 18,469개
  - CJ: 16,606개
  - 푸디스트: 15,622개
  - 동원홈푸드: 14,590개

## 🔧 API 엔드포인트

### 기본 URL
- API 서버: `http://127.0.0.1:8010`
- 통합 서버: `http://127.0.0.1:8080`

### 주요 엔드포인트
```
GET  /api/admin/dashboard-stats          # 대시보드 통계
GET  /api/admin/users                    # 사용자 목록
GET  /api/admin/suppliers                # 협력업체 목록
GET  /api/admin/business-locations       # 사업장 목록
GET  /api/admin/ingredients-new          # 식자재 목록 (페이징)
GET  /api/admin/customer-supplier-mappings # 매핑 목록
POST /api/admin/ingredients              # 식자재 추가
PUT  /api/admin/ingredients/{id}         # 식자재 수정
DELETE /api/admin/ingredients/{id}       # 식자재 삭제
```

## 🔴 핵심 규칙: 뼈대 구조 유지

### admin_dashboard.html 작업 시 필수 준수사항:
1. **절대 하지 말아야 할 것:**
   - ❌ HTML 파일에 인라인 스타일 추가
   - ❌ HTML 파일에 스크립트 직접 작성
   - ❌ HTML 파일을 500줄 이상으로 늘리기
   - ❌ 모달이나 복잡한 UI를 HTML에 직접 포함

2. **반드시 해야 할 것:**
   - ✅ 새 기능은 별도 모듈로 생성
   - ✅ 스타일은 CSS 파일로 분리
   - ✅ 스크립트는 JS 파일로 분리
   - ✅ 복잡한 UI는 템플릿으로 분리
   - ✅ 203줄 이내 유지 (현재 상태)

3. **파일 크기 제한:**
   - admin_dashboard.html: 최대 250줄
   - 각 모듈 JS: 최대 500줄
   - 각 템플릿 HTML: 최대 200줄

## 💻 모듈별 기능

### 1. 대시보드 (Dashboard)
- 실시간 통계 표시
- 최근 활동 로그
- 주요 지표 시각화

### 2. 협력업체 관리 (Suppliers)
- 협력업체 목록 조회
- 협력업체별 식자재 현황
- 거래 상태 관리

### 3. 사용자 관리 (Users)
- 사용자 권한 관리
- 로그인 이력 추적
- 접근 권한 설정

### 4. 사업장 관리 (Sites)
- 사업장 정보 관리
- 지역별 분류
- 운영 상태 관리

### 5. 협력업체 매핑 (Supplier Mapping)
- 사업장-협력업체 연결
- 협력업체 코드 관리
- 배송 코드 설정
- 통계 및 현황 표시

### 6. 식자재 관리 (Ingredients)
- 84,215개 식자재 데이터 관리
- 카테고리별 분류
- 가격 정보 관리
- 재고 추적

### 7. 식단가 관리 (Meal Pricing)
- 단가 계산
- 가격 이력 관리
- 비용 분석

## 🎨 UI/UX 특징

### 디자인 원칙
- **컴팩트 뷰**: 한 화면에 최대한 많은 정보 표시
- **빠른 응답**: API 응답 시간 ~200ms
- **직관적 네비게이션**: 사이드바 메뉴 구조
- **실시간 업데이트**: 자동 새로고침 기능

### 주요 UI 컴포넌트
- 통계 박스 (대시보드)
- 데이터 테이블 (페이징 지원)
- 모달 다이얼로그 (편집/추가)
- 필터 및 검색 기능

## 🐛 문제 해결

### 포트 충돌 시
```bash
# Windows에서 포트 사용 프로세스 확인
netstat -ano | findstr :8010

# Python 프로세스 종료
taskkill /F /IM python.exe
```

### 데이터베이스 오류 시
- 백업 파일 확인: `backups/daham_meal.db`
- SQLite 직접 접근: `sqlite3 backups/daham_meal.db`

### 모듈 로딩 실패 시
1. 브라우저 캐시 삭제
2. F12 개발자 도구에서 콘솔 확인
3. 네트워크 탭에서 404 오류 확인

## 📝 개발 규칙

### 코드 스타일
- JavaScript: ES6+ 문법 사용
- Python: PEP 8 준수
- HTML/CSS: BEM 명명 규칙

### 커밋 메시지
```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 추가
chore: 빌드 업무 수정
```

### API 응답 형식
```json
{
  "success": true,
  "data": {...},
  "message": "성공",
  "timestamp": "2025-01-14T10:00:00Z"
}
```

## 🔒 보안 고려사항

### 필수 보안 규칙
- ❌ 실제 API 키를 코드에 하드코딩 금지
- ❌ 실제 비밀번호를 평문으로 저장 금지
- ✅ 환경 변수 사용 권장
- ✅ HTTPS 사용 (프로덕션)
- ✅ SQL 인젝션 방지 (파라미터화된 쿼리)

## 📱 브라우저 호환성
- Chrome 90+ (권장)
- Firefox 88+
- Safari 14+
- Edge 90+

## 🚦 서버 상태 확인

### 실행 중인 서버 확인
```bash
# API 서버 상태
curl http://127.0.0.1:8010/api/admin/dashboard-stats

# 통합 서버 상태
curl http://127.0.0.1:8080/control
```

## 📞 문제 발생 시

### 로그 확인
1. 브라우저 콘솔 (F12)
2. Python 서버 콘솔
3. 네트워크 탭 확인

### 일반적인 해결책
1. 서버 재시작
2. 브라우저 캐시 삭제
3. 포트 충돌 확인
4. 데이터베이스 경로 확인

## 🔄 업데이트 이력

### 2025-09-14
- 협력업체 매핑 관리 개선
- 테이블 컴팩트 뷰 적용
- 통계 박스 추가
- 모달 최적화

### 2025-09-13
- API 포트 통합 (8010)
- 모듈 로딩 최적화
- display 속성 직접 제어

## 📚 참고 문서
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [SQLite 문서](https://www.sqlite.org/docs.html)
- [JavaScript MDN](https://developer.mozilla.org/)

---

**주의**: 이 시스템은 다함 내부용으로 개발되었으며, 실제 운영 환경에서는 추가적인 보안 설정이 필요합니다.

**개발 환경**: Windows 10/11, Python 3.8+, 모던 브라우저

## ⚠️ 메뉴/레시피 시스템 중요 주의사항

### 재료 저장 문제 재발 방지
```python
# ❌ 절대 이렇게 하지 말 것 - 프록시 구조
@app.post("/api/recipe/save")
async def save_recipe_proxy(request: Request):
    response = await client.post("http://127.0.0.1:8011/api/recipe/save", ...)

# ✅ 반드시 이렇게 - 직접 구현
@app.post("/api/recipe/save")
async def save_recipe_direct(request: Request):
    # FormData 파싱
    form = await request.form()
    # 직접 DB 저장
    conn = sqlite3.connect(DATABASE_PATH)
    # ...
```

### 테이블 구조 확인 필수
```bash
# 개발 전 반드시 확인
python -c "
import sqlite3
conn = sqlite3.connect('daham_meal.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(menu_recipe_ingredients)')
print(cursor.fetchall())
"
```

### 자동 검증 실행
```bash
# 시스템 수정 후 반드시 실행
python validate_system.py
```

**마지막 업데이트**: 2025-09-19