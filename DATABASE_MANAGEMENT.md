# 데이터베이스 관리 가이드

## 중복 문제 방지 체계

### 1. 통일된 데이터베이스 경로
- **메인 DB**: `daham_meal.db`
- **백업 DB**: `backups/` 폴더
- 모든 API와 스크립트는 `daham_meal.db`를 사용하도록 통일됨

### 2. 자동 검증 시스템
서버 시작 시 자동으로 데이터 무결성을 검증하고 복구합니다.

#### 검증 항목:
- ✅ 사업장 개수 (정확히 6개)
- ✅ 사업장명 중복 여부
- ✅ 올바른 사업장명 존재 여부
- ✅ 매핑 데이터 유효성
- ✅ 필수 컬럼 존재 여부

### 3. 정상 사업장 데이터
```
1. 도시락 (BIZ001) - 급식업체
2. 운반 (BIZ002) - 운반업체
3. 학교 (BIZ003) - 학교급식
4. 요양원 (BIZ004) - 요양급식
5. 영남 도시락 (BIZ005) - 급식업체
6. 영남 운반 (BIZ006) - 운반업체
```

## 서버 시작 방법

### 권장 방법 (자동 검증 포함):
```batch
START_SERVER_WITH_VALIDATION.bat
```

### 수동 검증:
```bash
python validate_database.py
```

### 제약조건 적용:
```bash
python add_database_constraints.py
```

## 문제 발생 시 대처법

### 1. 중복 사업장 발견 시
- `validate_database.py` 실행하면 자동 복구됨

### 2. 매핑 오류 시
- 잘못된 매핑은 자동으로 삭제됨
- 유효한 매핑만 유지됨

### 3. 데이터베이스 손상 시
- `backups/` 폴더에서 백업 파일 복원
- `validate_database.py` 실행하여 정상화

## 주의사항

1. **직접 DB 수정 금지**: 항상 API를 통해 데이터 수정
2. **정기 백업**: 중요한 변경 전 백업 생성
3. **검증 스크립트 실행**: 주기적으로 `validate_database.py` 실행

## 스크립트 설명

### validate_database.py
- 데이터 무결성 검증 및 자동 복구
- 모든 데이터베이스 파일 검사

### add_database_constraints.py
- UNIQUE 제약조건 추가
- 중복 데이터 삽입 방지

### START_SERVER_WITH_VALIDATION.bat
- 서버 시작 전 자동 검증
- 안전한 서버 시작 보장

---

이 시스템으로 인해 앞으로는 중복 사업장 문제가 발생하지 않습니다.