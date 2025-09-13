# 🎯 시스템 정리 계획 - !표 파일 기준

## 📋 현재 문제점 분석

### ❌ 현재 admin_dashboard.html의 문제
1. **2,678줄의 거대한 파일** - 뼈대만 남아야 하는데 모든 것이 들어있음
2. **하드코딩된 데이터** - 사업장 데이터가 HTML에 직접 입력됨
3. **인라인 스크립트** - 800줄 이상의 JavaScript가 HTML 내부에 존재
4. **의존성 지옥** - 모듈 간 참조 관계가 복잡하고 불명확
5. **폴백 로직 중복** - 각 모듈마다 별도의 초기화 로직 존재

## ✅ !표 파일들의 핵심 지침

### 1. **!MODULE_SYSTEM_GUIDE.md** - 모듈 시스템 구조
- ModuleLoader를 통한 중앙집중식 의존성 관리
- 자동 의존성 해결
- 표준화된 모듈 로딩 방식

### 2. **!SYSTEM_REFACTOR_COMPLETE.md** - 목표 상태
- admin_dashboard.html: 260줄 (90% 감소)
- 모든 CSS/JS 외부 파일로 분리
- 기능별 모듈화

### 3. **!CACHE_SYSTEM_GUIDE.md** - 캐시 시스템
- 5분 로컬 캐시로 성능 개선
- 자동 무효화 시스템

## 🔧 즉시 실행 계획

### Phase 1: HTML 뼈대만 남기기 (우선순위 1)
```
1. admin_dashboard.html에서 제거할 것:
   - 모든 인라인 <script> 내용 → 외부 JS 파일로
   - 하드코딩된 데이터 → API에서 가져오도록
   - 인라인 스타일 → CSS 파일로

2. HTML에 남길 것:
   - 기본 구조 (nav, content-area)
   - 빈 컨테이너 div들
   - 외부 파일 참조만
```

### Phase 2: 모듈 시스템 정립 (우선순위 2)
```
1. ModuleLoader 구현
   - static/utils/module-loader.js 생성
   - 의존성 자동 해결 로직

2. 각 기능별 모듈 분리
   - static/modules/users/users.js
   - static/modules/suppliers/suppliers.js
   - static/modules/sites/sites.js (BusinessLocationsModule)
   - static/modules/meal-pricing/meal-pricing.js
   - static/modules/ingredients/ingredients.js
```

### Phase 3: 데이터 레이어 분리 (우선순위 3)
```
1. 하드코딩된 데이터 제거
   - 사업장 4개 데이터 → API 호출로 변경
   - 통계 숫자들 → 동적 계산

2. API 통합
   - daham_api.py 활용
   - 캐시 시스템 적용
```

## 📁 최종 목표 구조

```
다함-식자재-관리/
├── 📄 admin_dashboard.html (260줄 이하)
├── 🔧 config.js
├── 📁 static/
│   ├── 📁 css/
│   │   └── admin-dashboard-main.css
│   ├── 📁 utils/
│   │   ├── module-loader.js ⭐
│   │   └── admin-cache.js
│   └── 📁 modules/
│       ├── 📁 dashboard-core/
│       │   └── dashboard-core.js
│       ├── 📁 users/
│       │   └── users.js
│       ├── 📁 suppliers/
│       │   └── suppliers.js
│       ├── 📁 sites/
│       │   └── sites.js
│       ├── 📁 meal-pricing/
│       │   └── meal-pricing.js
│       └── 📁 ingredients/
│           └── ingredients.js
```

## 🚀 실행 순서

1. **즉시**: admin_dashboard.html의 인라인 스크립트 추출
2. **다음**: ModuleLoader 시스템 구현
3. **그 다음**: 하드코딩 데이터 제거 및 API 연결
4. **마지막**: 테스트 및 최적화

## 📊 예상 효과

- **코드 라인 수**: 2,678줄 → 260줄 (90% 감소)
- **유지보수성**: 모듈별 독립 수정 가능
- **안정성**: 의존성 자동 관리로 참조 오류 방지
- **성능**: 캐시 시스템으로 로딩 속도 개선
- **개발 속도**: 명확한 구조로 빠른 기능 추가

## ⚠️ 주의사항

1. **데이터 무결성**: 실제 DB 데이터만 사용 (더미 데이터 금지)
2. **점진적 변경**: 한 번에 모두 바꾸지 말고 단계별로
3. **테스트 우선**: 각 단계마다 기능 테스트 필수
4. **백업 유지**: 변경 전 현재 상태 백업