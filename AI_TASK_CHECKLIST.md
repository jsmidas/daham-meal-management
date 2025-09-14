# 🤖 AI 작업 지시서 - 다함 식자재 관리 시스템

## 📅 작성일: 2025-09-14
## 🔄 최종 업데이트: 2025-09-14 14:10

## 🚨 필수 준수사항: admin_dashboard.html은 203줄 뼈대만 유지!
- ❌ HTML에 직접 코드 추가 금지
- ✅ 모든 기능은 별도 모듈로 분리
- ✅ 스타일은 CSS, 스크립트는 JS 파일로

---

## 🎯 프로젝트 개요
다함 식자재 관리 시스템의 관리자 대시보드 완성 및 세부 기능 구현

### 🖥️ 현재 서버 구성
- **API 서버**: `test_samsung_api.py` (포트: 8010)
- **정적 파일 서버**: `simple_server.py` (포트: 3000)
- **데이터베이스**: `daham_meal.db` (SQLite)
- **메인 대시보드**: `admin_dashboard.html` (203줄 뼈대만!)

### 📂 모듈화 구조
```
admin_dashboard.html (203줄)
├── static/css/admin-dashboard-styles.css (분리된 스타일)
├── static/js/dashboard-init.js (분리된 스크립트)
├── static/templates/ (동적 로드 템플릿)
└── static/modules/users/ (사용자 관리 모듈)
    ├── user-modal.html
    └── user-permissions.js (10개 사업장 권한)
```

### 📁 백업 위치
- `C:\Dev\daham-meal-management\backups\2025-09-14-07-26\`
- 문제 발생 시 이 백업으로 복구 가능

---

## ✅ 완료된 작업 (체크된 항목)

### 1. 기본 인프라 ✅
- [x] 서버 통합 (포트 8010으로 통일)
- [x] 서버 모니터링 도구 (`server_monitor.py`)
- [x] 서버 시작/종료 스크립트 (`START_ALL_SERVERS.bat`, `STOP_ALL_SERVERS.bat`)
- [x] API 문서화 (`API_DOCUMENTATION.md`)

### 2. 대시보드 기본 기능 ✅
- [x] 메인 대시보드 레이아웃
- [x] 페이지 전환 기능
- [x] 대시보드 통계 표시
- [x] 모듈 동적 로딩

### 3. 사용자 관리 개선 ✅
- [x] 사용자-사업장 권한 테이블 생성 (`user_site_permissions`)
- [x] 모달에 사업장 권한 체크박스 추가
- [x] 비밀번호 초기화 기능
- [x] API 엔드포인트 추가
  - [x] `GET /api/users/{user_id}/permissions`
  - [x] `POST /api/users/{user_id}/reset-password`

### 4. 🎉 모듈화 완료 (2025-09-14 14:00) ✅
- [x] **admin_dashboard.html 962줄 → 203줄로 감소 (79% 감소)**
- [x] 인라인 스타일 → CSS 파일로 분리
- [x] 인라인 스크립트 → JS 파일로 분리
- [x] 각 섹션 → HTML 템플릿으로 분리
- [x] 사용자 권한 관리: 10개 사업장 듀얼 리스트 선택기

---

## ❌ 미완성 작업 (다음 AI가 수행해야 할 작업)

### ⚠️ 중요: 작업 시 반드시 모듈화 규칙 준수
- admin_dashboard.html에 직접 코드 추가 금지
- 새 기능은 별도 모듈로 생성할 것

### 1. 사용자 관리 세부 기능 🔴
- [ ] **사용자 추가 버튼 작동**
  - 현재 상태: 버튼 클릭 시 모달이 열리지 않음
  - 파일: `admin_dashboard.html`, `static/modules/users/users.js`
  - 해결방법: `openCreateModal()` 함수 연결 확인

- [ ] **사용자 수정 기능**
  - 현재 상태: 수정 버튼 클릭 시 데이터 로드 안됨
  - 파일: `static/modules/users/users.js`
  - 해결방법: `editUser()` 함수 디버깅

- [ ] **사용자 삭제 기능**
  - 현재 상태: 구현되지 않음
  - 필요 작업: 삭제 확인 다이얼로그 및 API 연결

- [ ] **벌크 액션 (일괄 선택/삭제)**
  - 현재 상태: UI는 있으나 작동하지 않음
  - 파일: `admin_dashboard.html` 320-323번 줄

### 2. 협력업체 관리 🔴
- [ ] **협력업체 추가/수정/삭제**
  - 현재 상태: 목록 표시만 가능
  - 파일: `static/modules/suppliers/suppliers.js`

- [ ] **협력업체 통계 오류 수정**
  - 현재 오류: `GET /api/admin/suppliers/stats 422`
  - 원인: API 응답 형식 불일치

### 3. 사업장 관리 🔴
- [ ] **사업장 추가 모달**
  - 현재 상태: "새 사업장 추가" 버튼 작동 안함
  - 파일: `static/modules/sites/sites.js`

- [ ] **사업장 수정/삭제**
  - 현재 상태: 미구현

### 4. 식자재 관리 🔴
- [ ] **식자재 검색 기능**
  - 현재 상태: 84,215개 데이터 중 검색 불가

- [ ] **페이지네이션**
  - 현재 상태: 한 페이지에 모든 데이터 표시

- [ ] **식자재 추가/수정/삭제**
  - 현재 상태: 읽기 전용

### 5. 식단가 관리 🔴
- [ ] **데이터 유효성 검사**
  - 판매가와 목표재료비 검증
  - 원가율 자동 계산 확인

- [ ] **엑셀 내보내기/가져오기**
  - 현재 상태: 미구현

### 6. 협력업체 매핑 🔴
- [ ] **매핑 추가/수정/삭제**
  - 현재 상태: 조회만 가능

---

## 🛠️ 작업 순서 권장사항

### Phase 1: 긴급 수정 (1-2시간)
1. **사용자 추가 버튼 수정**
   ```javascript
   // admin_dashboard.html 315번 줄
   onclick="window.userManagement?.openCreateModal()"
   ```

2. **협력업체 통계 API 수정**
   ```python
   # test_samsung_api.py
   # /api/admin/suppliers/stats 응답 형식 확인
   ```

### Phase 2: CRUD 기능 완성 (3-4시간)
1. 각 모듈의 추가/수정/삭제 기능 구현
2. 모달 다이얼로그 연결
3. API 엔드포인트 테스트

### Phase 3: 고급 기능 (2-3시간)
1. 검색 및 필터링
2. 페이지네이션
3. 엑셀 내보내기/가져오기

---

## 🔍 디버깅 팁

### 1. 브라우저 콘솔 확인
```javascript
// F12 → Console 탭에서 오류 확인
// 주요 확인 사항:
// - 404 Not Found: API 경로 문제
// - 422 Unprocessable: 데이터 형식 문제
// - undefined 오류: 객체 속성 접근 문제
```

### 2. API 테스트
```bash
# 사용자 통계 확인
curl http://127.0.0.1:8010/api/admin/users/stats

# 협력업체 통계 확인
curl http://127.0.0.1:8010/api/admin/suppliers/stats
```

### 3. 캐시 문제 해결
```
Ctrl + Shift + R (강제 새로고침)
또는
F12 → Network 탭 → Disable cache 체크
```

---

## 📌 중요 파일 위치

### Frontend
- `admin_dashboard.html` - 메인 대시보드
- `static/modules/users/users.js` - 사용자 관리
- `static/modules/suppliers/suppliers.js` - 협력업체 관리
- `static/modules/sites/sites.js` - 사업장 관리
- `static/modules/ingredients/ingredients.js` - 식자재 관리
- `static/modules/meal-pricing/meal-pricing.js` - 식단가 관리

### Backend
- `test_samsung_api.py` - 메인 API 서버
- `daham_meal.db` - SQLite 데이터베이스

### 설정
- `config.js` - API 서버 설정 (BASE_URL)
- `CLAUDE.md` - 개발 가이드

---

## ⚠️ 주의사항

1. **Git 사용**: 작업 전 반드시 커밋
   ```bash
   git add -A
   git commit -m "작업 시작 전 백업"
   ```

2. **서버 재시작**: 코드 수정 후
   ```bash
   # Python 서버는 수동 재시작 필요
   Ctrl + C → python test_samsung_api.py
   ```

3. **데이터베이스 백업**: 구조 변경 전
   ```bash
   cp daham_meal.db backups/daham_meal_backup_$(date +%Y%m%d_%H%M%S).db
   ```

---

## 📞 테스트 계정

- **관리자**: admin / (비밀번호는 DB 확인)
- **일반 사용자**: js / (비밀번호는 DB 확인)

---

## 🎯 최종 목표

모든 CRUD 기능이 작동하는 완전한 관리자 대시보드 완성:
- ✅ 모든 추가/수정/삭제 버튼 작동
- ✅ 검색 및 필터링 기능
- ✅ 페이지네이션
- ✅ 데이터 유효성 검사
- ✅ 에러 처리 및 사용자 피드백

---

## 💡 추가 개선 사항 (선택)

- [ ] 다크 모드
- [ ] 반응형 디자인 (모바일 지원)
- [ ] 실시간 알림
- [ ] 데이터 차트/그래프
- [ ] 감사 로그 (audit trail)

---

**작성자**: Claude (이전 AI)
**다음 작업자**: [작업자 이름을 여기에 기록]
**작업 시작 시간**: [시작 시간 기록]
**작업 완료 시간**: [완료 시간 기록]