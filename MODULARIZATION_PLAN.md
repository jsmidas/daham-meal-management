# main.py 모듈화 계획 (4907라인 → 분산)

## 현재 상황
- **총 라인**: 4907라인
- **API 엔드포인트**: 117개
- **함수**: 132개
- **문제**: 모든 로직이 하나의 파일에 집중

## 분리 계획

### 1. API 라우터 분리
```
app/api/
├── auth.py          # 인증 관련 (2개 API)
├── suppliers.py     # 협력업체 관련 (17개 API)  
├── customers.py     # 사업장 관련 (12개 API)
├── admin.py         # 관리자 기능 (53개 API)
├── meal_plans.py    # 식단 관리
├── ingredients.py   # 식재료 관리
├── ordering.py      # 발주 관리
└── dashboard.py     # 대시보드 관련
```

### 2. 서비스 레이어 분리
```
app/services/
├── auth_service.py
├── supplier_service.py    # 이미 생성됨
├── customer_service.py
├── meal_plan_service.py
└── ingredient_service.py
```

### 3. 스키마 분리
```  
app/schemas/
├── auth.py
├── suppliers.py
├── customers.py
└── common.py
```

### 4. 새로운 main.py (최소화)
- FastAPI 앱 생성
- 라우터 등록
- 미들웨어 설정
- 예외 핸들러
- 약 100라인 이하로 축소

## 우선순위
1. **Phase 1**: API 라우터 분리 (auth, suppliers, customers)
2. **Phase 2**: 서비스 레이어 완성
3. **Phase 3**: 스키마 정의
4. **Phase 4**: main.py 최소화
5. **Phase 5**: 테스트 코드 작성