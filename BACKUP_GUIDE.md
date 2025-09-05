# 📋 데이터 손실 방지 가이드

## 🚨 문제 상황 분석
- **일시**: 2025-09-04 (어제)
- **원인**: admin_dashboard.html 모듈화 과정에서 사업장 데이터 삭제
- **해결**: 샘플 데이터로 복구 완료 (5개 사업장)

## 🛡️ 데이터 손실 방지 방안

### 1. 자동 백업 시스템
```bash
# 매일 자동 백업 실행
python backup_script.py
```

### 2. 작업 전 필수 체크리스트
- [ ] 현재 데이터 개수 확인
- [ ] 백업 파일 생성
- [ ] 중요 테이블 데이터 검증
- [ ] Git 커밋으로 버전 관리

### 3. 안전한 모듈화 절차
1. **준비 단계**
   ```bash
   # 1. 현재 상태 백업
   python backup_script.py
   
   # 2. Git 커밋
   git add -A
   git commit -m "모듈화 전 백업 커밋"
   ```

2. **모듈화 실행**
   - 한 번에 한 모듈씩 분리
   - 각 단계마다 데이터 검증
   - 기능 테스트 후 다음 단계 진행

3. **검증 단계**
   ```bash
   # 데이터 검증
   python -c "
   import sqlite3
   conn = sqlite3.connect('daham_meal.db')
   cursor = conn.cursor()
   cursor.execute('SELECT COUNT(*) FROM business_locations')
   print(f'사업장: {cursor.fetchone()[0]}개')
   conn.close()
   "
   ```

### 4. 복구된 사업장 데이터
```
✅ 복구 완료 (5개 사업장):
- HQ001: 다함 본사 (headquarters)
- BR001: 서울 강남지점 (branch)  
- BR002: 서울 마포지점 (branch)
- BR003: 부산 해운대지점 (branch)
- ST001: 인천 송도지점 (satellite)
```

### 5. 향후 모듈화 권장사항

#### 우선순위 1: 독립적 모듈
1. Settings 페이지 (로직 단순)
2. Dashboard 차트 (읽기 전용)  
3. Logs 페이지 (표시만)

#### 우선순위 2: CRUD 모듈  
1. Users 관리
2. Suppliers 관리
3. Ingredients 관리

#### 우선순위 3: 복잡한 모듈
1. Business Locations (트리 구조)
2. Supplier Mapping (관계형)
3. Pricing (복잡한 계산)

## ⚠️ 경고사항
- **절대 main 브랜치에서 직접 작업 금지**
- **모듈화 전 반드시 백업 생성**
- **각 단계마다 데이터 검증 필수**
- **문제 발생시 즉시 이전 상태로 복구**

## 🔧 복구 명령어
```bash
# 긴급 복구 (백업에서)
cp backups/daham_meal_backup_YYYYMMDD_HHMMSS.db daham_meal.db

# 샘플 데이터 재생성
python restore_business_locations.py
```