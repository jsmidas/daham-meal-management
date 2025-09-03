# 견고한 급식관리시스템 아키텍처 설계

## 설계 원칙
1. **단일 책임 원칙**: 각 모듈은 하나의 명확한 책임만 가짐
2. **계층화 아키텍처**: 명확한 레이어 분리
3. **의존성 역전**: 고수준 모듈이 저수준 모듈에 의존하지 않음
4. **데이터 무결성**: 견고한 데이터베이스 제약조건
5. **확장성**: 새로운 기능 추가 시 기존 코드 영향 최소화

## 디렉토리 구조
```
daham-meal-management/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 앱 진입점 (최소화)
│   ├── config.py            # 설정 관리
│   ├── database.py          # 데이터베이스 연결 관리
│   ├── models/              # 데이터 모델
│   │   ├── __init__.py
│   │   ├── base.py          # Base 모델 클래스
│   │   ├── suppliers.py     # 협력업체 모델
│   │   ├── customers.py     # 사업장 모델
│   │   └── mappings.py      # 관계 모델
│   ├── schemas/             # Pydantic 스키마
│   │   ├── __init__.py
│   │   ├── suppliers.py
│   │   └── customers.py
│   ├── api/                 # API 라우터
│   │   ├── __init__.py
│   │   ├── suppliers.py     # 협력업체 API
│   │   ├── customers.py     # 사업장 API
│   │   └── auth.py          # 인증 API
│   ├── services/            # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── supplier_service.py
│   │   └── customer_service.py
│   ├── core/                # 핵심 유틸리티
│   │   ├── __init__.py
│   │   ├── security.py      # 보안 관련
│   │   └── exceptions.py    # 예외 처리
│   └── static/              # 정적 파일
│       ├── css/
│       ├── js/
│       └── templates/
└── tests/                   # 테스트 코드
    ├── __init__.py
    ├── test_suppliers.py
    └── test_customers.py
```

## 핵심 모듈 역할

### 1. Models (데이터 모델)
- SQLAlchemy 기반 ORM 모델
- 데이터베이스 테이블 구조 정의
- 관계(Relationship) 정의

### 2. Schemas (데이터 검증)
- Pydantic 기반 데이터 검증
- API 입출력 스키마 정의
- 자동 문서화 지원

### 3. Services (비즈니스 로직)
- 핵심 비즈니스 로직 구현
- 트랜잭션 관리
- 복잡한 데이터 처리

### 4. API (인터페이스)
- FastAPI 라우터 기반
- HTTP 요청/응답 처리
- 인증/권한 검증

### 5. Core (공통 기능)
- 보안, 예외처리 등 공통 기능
- 설정 관리
- 유틸리티 함수

## 데이터베이스 설계
- Primary Key: 모든 테이블에 자동 증가 ID
- Foreign Key: 강제 참조 무결성
- Unique Constraints: 중복 방지
- Not Null: 필수 필드 강제
- Default Values: 기본값 설정
- Timestamps: 생성/수정 시간 자동 관리

## API 설계
- RESTful 원칙 준수
- 일관된 응답 형식
- 적절한 HTTP 상태 코드 사용
- 에러 처리 표준화
- 자동 API 문서화 (Swagger)

## 보안 고려사항
- JWT 기반 인증
- Role-based 접근 제어
- SQL Injection 방지
- XSS 방지
- CSRF 방지