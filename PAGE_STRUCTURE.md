# 📋 다함 식자재 관리 시스템 - 페이지 구조 문서

## 🎯 페이지 구분 체계

### 🔴 관리자 전용 페이지 (Admin Only)
> 빨간색 배지로 표시 | 배경: #e74c3c

| 파일명 | 용도 | 주요 기능 | 접근 권한 |
|--------|------|-----------|-----------|
| `admin_dashboard.html` | 관리자 대시보드 | - 전체 시스템 통계<br>- 사용자 관리<br>- 협력업체 관리<br>- 사업장 관리 | 관리자만 |
| `supplier_management.html` | 협력업체 상세 관리 | - 협력업체 추가/수정/삭제<br>- 계약 관리 | 관리자만 |

### 🔵 사용자 페이지 (User Pages)
> 파란색 배지로 표시 | 배경: #3498db

| 파일명 | 용도 | 주요 기능 | 접근 권한 |
|--------|------|-----------|-----------|
| `dashboard.html` | 사용자 대시보드 | - 오늘의 급식 현황<br>- 개인 업무 현황 | 모든 사용자 |
| `menu_recipe_management.html` | 메뉴/레시피 관리 | - 메뉴 등록<br>- 레시피 작성<br>- Excel 스타일 편집 | 조리팀 |
| `ingredients_management.html` | 식자재 관리 | - 식자재 검색<br>- 가격 조회<br>- 재고 확인 | 모든 사용자 |
| `meal_plan_management.html` | 식단 관리 | - 주간/월간 식단 계획<br>- 식단표 작성 | 영양사 |
| `meal_count_management.html` | 식수 관리 | - 일일 식수 등록<br>- 식수 통계 | 모든 사용자 |
| `ordering_management.html` | 발주 관리 | - 발주서 작성<br>- 발주 승인 요청 | 구매팀 |
| `receiving_management.html` | 입고명세서 관리 | - 입고 확인<br>- 검수 기록 | 창고팀 |
| `preprocessing_management.html` | 전처리 지시서 | - 전처리 작업 지시<br>- 작업 현황 | 조리팀 |
| `cooking_instruction_management.html` | 조리 지시서 | - 조리 방법 안내<br>- 조리 순서 | 조리팀 |
| `portion_instruction_management.html` | 소분 지시서 | - 소분 작업 지시<br>- 포장 규격 | 조리팀 |

### ⚪ 공통 페이지 (Shared)
> 배지 없음

| 파일명 | 용도 | 주요 기능 |
|--------|------|-----------|
| `login.html` | 로그인 | 사용자 인증 |
| `user_dashboard.html` | 사용자 선택 화면 | 사용자용 메뉴 선택 |

## 🎨 시각적 구분 방법

### 1. 페이지 상단 배지
```html
<!-- 관리자 페이지 -->
🔐 관리자 전용 페이지 - ADMIN ONLY (빨간색 배경)

<!-- 사용자 페이지 -->
👤 사용자 페이지 - USER DASHBOARD (파란색 배경)
```

### 2. 사이드바 색상
- **관리자**: 상단 빨간 띠 (3px solid #e74c3c)
- **사용자**: 상단 파란 띠 (3px solid #3498db)

### 3. ADMIN 버튼
- **관리자 페이지**: 사용자 대시보드로 이동 버튼
- **사용자 페이지**: ADMIN 대시보드로 이동 버튼

## 📁 디렉토리 구조 (현재)

```
daham-meal-management/
├── admin_dashboard.html          # 관리자 메인
├── dashboard.html                 # 사용자 메인
├── user_dashboard.html            # 사용자 선택 화면
├── login.html                     # 로그인
│
├── menu_recipe_management.html    # 메뉴/레시피
├── ingredients_management.html    # 식자재
├── meal_plan_management.html      # 식단
├── meal_count_management.html     # 식수
├── ordering_management.html       # 발주
├── receiving_management.html      # 입고
├── preprocessing_management.html  # 전처리
├── cooking_instruction_management.html  # 조리
└── portion_instruction_management.html  # 소분
```

## 🔒 권한 매트릭스

| 기능 | admin | js (일반) | test | 비고 |
|------|-------|-----------|------|------|
| 관리자 대시보드 | ✅ | ❌ | ❌ | admin만 |
| 사용자 관리 | ✅ | ❌ | ❌ | admin만 |
| 협력업체 관리 | ✅ | ❌ | ❌ | admin만 |
| 사업장 관리 | ✅ | ❌ | ❌ | admin만 |
| 메뉴/레시피 | ✅ | ✅ | 🔍 | test는 조회만 |
| 식자재 관리 | ✅ | ✅ | 🔍 | test는 조회만 |
| 식단 관리 | ✅ | ✅ | 🔍 | test는 조회만 |
| 발주 관리 | ✅ | ✅ | ❌ | test 불가 |
| 가격 수정 | ✅ | ❌ | ❌ | admin만 |

## 🚦 네비게이션 규칙

### 관리자 로그인 시
1. `admin_dashboard.html`로 자동 이동
2. 모든 페이지 접근 가능
3. 사이드바에 모든 메뉴 표시

### 일반 사용자 로그인 시
1. `dashboard.html` 또는 `user_dashboard.html`로 이동
2. 권한 있는 페이지만 접근
3. 사이드바에 허용된 메뉴만 표시

## 📝 개발 가이드

### 새 페이지 추가 시
1. 페이지 타입 결정 (admin/user/shared)
2. 적절한 배지 색상 추가
3. 이 문서에 페이지 정보 업데이트
4. 권한 체크 코드 추가

### 권한 체크 예시
```javascript
// 페이지 로드 시 권한 확인
async function checkPageAccess() {
    const response = await fetch('/api/current-user');
    const user = await response.json();

    // 관리자 페이지 접근 제한
    if (PAGE_TYPE === 'admin' && user.role !== 'admin') {
        alert('관리자 권한이 필요합니다');
        window.location.href = 'dashboard.html';
    }
}
```

## 🔄 업데이트 이력

| 날짜 | 변경사항 |
|------|---------|
| 2025-01-17 | 페이지 구조 문서 생성 |
| 2025-01-17 | 시각적 배지 시스템 도입 |
| 2025-01-17 | admin/user 구분 명확화 |

---

**마지막 업데이트**: 2025년 1월 17일
**작성자**: 다함 개발팀