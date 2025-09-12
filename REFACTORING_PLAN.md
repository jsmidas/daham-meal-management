# 🏗️ 시스템 리팩토링 계획

## 현재 문제점
- admin_dashboard.html: 5,700+ 라인 (관리 불가)
- 중복 JavaScript 함수들
- 복잡한 의존성
- 디버깅 어려움

## 해결책: 기능별 모듈 분리

### 1단계: 핵심 기능들 독립 파일로 분리
```
✅ sites_management.html      (사업장 관리) - 완료
⏳ users_management.html      (사용자 관리)  
⏳ suppliers_management.html  (협력업체 관리)
⏳ menu_management.html       (메뉴 관리)
⏳ meal_plans.html           (식단 관리)
⏳ ingredients.html          (식재료 관리)
⏳ ordering.html             (발주 관리)
⏳ receiving.html            (입고 관리)
```

### 2단계: 공통 컴포넌트 추출
```
common/
├── modal.js              (모달 관리)
├── api.js               (API 호출)  
├── table.js             (테이블 렌더링)
├── forms.js             (폼 관리)
└── utils.js             (유틸리티)
```

### 3단계: 메인 대시보드 단순화
```
dashboard.html           (200라인 이하)
├── 네비게이션만
├── 각 모듈로 링크
└── 기본 통계만
```

## 예상 결과
- 각 파일: 200-400 라인 (관리 가능)
- 중복 제거: 코드 50% 감소
- 디버깅: 문제 발생 시 해당 파일만 확인
- 수정: 한 파일만 수정하면 됨
- 테스트: 기능별 독립 테스트 가능

## 우선순위
1. 자주 사용하는 기능부터
2. 문제가 많이 발생하는 기능부터
3. 복잡도가 높은 기능부터

## 시간 투자 대비 효과
- 초기 투자: 1-2주
- 장기 효과: 개발/수정 시간 80% 단축