# 🔧 Fortress 시스템 - 완벽 트러블슈팅 가이드

## 🎯 목적
Fortress 시스템 사용 중 발생할 수 있는 모든 문제에 대한 체계적인 해결 방법을 제공합니다.

---

## 🚨 긴급 상황 대응 (30초 해결)

### ⚡ 즉시 대응 매뉴얼
```bash
# 🔴 STEP 1: 기존 시스템으로 즉시 전환 (가장 빠른 해결책)
http://127.0.0.1:8003/admin

# 🔴 STEP 2: 서버 재시작 (90% 문제 해결)
# 터미널에서: Ctrl+C → python main.py

# 🔴 STEP 3: 브라우저 하드 새로고침 (캐시 문제 해결)
# 브라우저에서: Ctrl+Shift+R
```

### 🆘 응급 연락처 & 리소스
- **기존 시스템**: `http://127.0.0.1:8003/admin`
- **문서**: `FORTRESS_DEPLOYMENT.md`, `FORTRESS_CHECKLIST.md`
- **백업**: `backups/` 폴더의 최신 데이터베이스 파일

---

## 📋 문제 유형별 분류 및 해결

### 🔴 Level 1: 치명적 오류 (시스템 사용 불가)

#### 1.1 Fortress 페이지가 전혀 로딩되지 않음
**증상**: 
- `http://127.0.0.1:8003/admin-fortress` 접속 시 404 또는 연결 오류
- 로딩 화면조차 나타나지 않음

**즉시 조치**:
```bash
# 1. 서버 상태 확인
curl -I http://127.0.0.1:8003
# 응답 없음 → 서버 재시작 필요

# 2. 서버 재시작
python main.py

# 3. 포트 충돌 확인
netstat -an | findstr 8003
```

**상세 해결 과정**:
1. **서버 프로세스 확인**:
   ```bash
   # Windows
   tasklist | findstr python
   
   # 프로세스 강제 종료 (필요시)
   taskkill /F /IM python.exe
   ```

2. **파일 존재 확인**:
   - `admin_dashboard_fortress.html` 파일 존재?
   - `main.py`에 `/admin-fortress` 라우트 존재?
   
3. **라우트 문제 해결**:
   ```python
   # main.py에 이 코드가 있는지 확인
   @app.get("/admin-fortress")
   async def admin_fortress_page():
       from fastapi.responses import FileResponse
       return FileResponse("admin_dashboard_fortress.html")
   ```

#### 1.2 로딩 화면에서 무한 대기
**증상**:
- 로딩 화면은 나타나지만 진행률이 멈춤
- 특정 단계에서 영원히 대기

**진단 방법**:
```javascript
// 브라우저 콘솔에서 실행 (F12)
console.log('현재 상태:', {
    fortress: !!window.Fortress,
    registry: !!window.ModuleRegistry,
    gateway: !!window.APIGateway,
    protection: !!window.FortressProtection
});
```

**해결 단계**:
1. **브라우저 호환성 확인**:
   - Chrome/Edge (권장): 최신 버전 사용
   - Firefox: JavaScript 활성화 확인
   - Safari: 보안 설정 확인

2. **JavaScript 오류 확인**:
   - F12 → Console 탭
   - 빨간색 오류 메시지 확인
   - 파일 로딩 실패 여부 확인

3. **네트워크 문제 진단**:
   - F12 → Network 탭
   - `/system/core/*.js` 파일들이 200 OK로 로딩되는지 확인

#### 1.3 데이터베이스 연결 실패
**증상**:
- Fortress는 로딩되지만 식자재 데이터가 전혀 없음
- API 호출 시 500 오류

**긴급 확인**:
```bash
# 데이터베이스 파일 상태 확인
dir daham_meal.db
# 0 바이트면 파일 손상

# 백업에서 복원
copy "backups\daham_meal_backup_최신.db" "daham_meal.db"
```

**서버 로그 확인**:
- 터미널에서 SQLite 관련 오류 메시지 찾기
- `INFO:app.database:Database connection successful` 메시지 있는지 확인

### 🟡 Level 2: 기능적 오류 (부분 사용 가능)

#### 2.1 식자재 데이터 표시 안됨
**증상**:
- Fortress는 정상 작동하지만 식자재가 0개 표시
- 테이블은 나타나지만 데이터 없음

**단계별 진단**:
```javascript
// 1. API 직접 호출 테스트
fetch('/api/admin/ingredients?page=1&limit=5')
  .then(r => r.json())
  .then(d => console.log('API 테스트:', d));

// 2. 필터 상태 확인
console.log('현재 필터:', {
    unpublished: document.getElementById('excludeUnpublished')?.checked,
    noPrice: document.getElementById('excludeNoPrice')?.checked
});

// 3. 모듈 상태 확인
console.log('식자재 모듈:', window.ModuleRegistry.getModuleStatus()['ingredients-fortress']);
```

**해결 방법**:
1. **필터 재설정**:
   - "미게시 식자재 제외" 체크 해제
   - "입고가 없는 식자재 제외" 체크 해제
   - 새로고침 버튼 클릭

2. **캐시 클리어**:
   ```javascript
   window.APIGateway.clearCache();
   location.reload();
   ```

3. **API 엔드포인트 확인**:
   - 브라우저에서 직접 접속: `http://127.0.0.1:8003/api/admin/ingredients?page=1&limit=5`

#### 2.2 느린 성능 (5초 이상 로딩)
**증상**:
- 시스템은 작동하지만 매우 느림
- 데이터 로딩에 10초 이상 소요

**성능 진단**:
```javascript
// 성능 측정
const start = performance.now();
// 작업 수행 후
console.log(`실행 시간: ${(performance.now() - start).toFixed(2)}ms`);

// 메모리 사용량
if (performance.memory) {
    console.log('메모리 사용량:', {
        used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024) + 'MB',
        total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024) + 'MB'
    });
}
```

**최적화 방법**:
1. **데이터 로딩 제한**:
   ```javascript
   // ingredients-module.js 수정
   const params = new URLSearchParams({
       page: 1,
       limit: 1000, // 200000 → 1000으로 변경
       exclude_unpublished: false,
       exclude_no_price: false
   });
   ```

2. **브라우저 최적화**:
   - 다른 탭 모두 닫기
   - 브라우저 재시작
   - 하드웨어 가속 활성화

### 🟠 Level 3: 기능 제한 (대부분 사용 가능)

#### 3.1 필터/검색 기능 오작동
**증상**:
- 필터를 변경해도 결과가 바뀌지 않음
- 검색어 입력 후 반응 없음

**디버깅**:
```javascript
// 이벤트 리스너 확인
console.log('필터 이벤트:', {
    unpublished: !!document.getElementById('excludeUnpublished')?.onclick,
    noPrice: !!document.getElementById('excludeNoPrice')?.onclick,
    search: !!document.getElementById('searchInput')?.oninput
});

// 모듈 상태 확인
const ingredientsModule = require('ingredients-fortress');
console.log('모듈 상태:', ingredientsModule ? '로드됨' : '없음');
```

**해결 방법**:
1. **이벤트 리스너 재등록**:
   - 페이지 새로고침 (F5)
   - 모듈 재로드 (개발자만)

2. **DOM 요소 확인**:
   - 필터 요소들이 존재하는지 확인
   - ID가 정확한지 확인

#### 3.2 UI 표시 오류
**증상**:
- 텍스트가 깨져 보임
- 버튼이나 메뉴가 제대로 표시되지 않음
- 스타일이 적용되지 않음

**CSS 문제 해결**:
```javascript
// CSS 파일 로딩 확인
console.log('스타일 파일:', 
    Array.from(document.styleSheets).map(s => s.href));

// 특정 스타일 확인
console.log('Fortress 스타일:', 
    !!document.getElementById('ingredients-fortress-styles'));
```

**해결 방법**:
1. **브라우저 캐시 클리어**: Ctrl+Shift+R
2. **CSS 재로딩**: 페이지 완전 새로고침
3. **브라우저 호환성**: Chrome/Edge 사용 권장

---

## 🛠️ 시나리오별 상세 가이드

### 시나리오 A: "AI가 코드를 수정한 후 작동하지 않음"

#### 상황 파악
```bash
# Git으로 변경 사항 확인
git status
git diff

# 핵심 파일 변경 여부 확인
git diff system/core/
git diff admin_dashboard_fortress.html
```

#### 복구 절차
```bash
# 1단계: 핵심 파일만 복원
git checkout -- system/core/framework.js
git checkout -- system/core/module-registry.js
git checkout -- system/core/api-gateway.js
git checkout -- system/core/protection.js

# 2단계: 메인 파일 복원
git checkout -- admin_dashboard_fortress.html

# 3단계: 서버 재시작
# Ctrl+C → python main.py
```

#### 안전 확인
```javascript
// 브라우저 콘솔에서
fortressDiagnostic(); // 전체 시스템 진단
```

### 시나리오 B: "갑자기 데이터가 사라짐"

#### 긴급 대응
```bash
# 1. 현재 DB 파일 크기 확인
dir daham_meal.db

# 2. 백업 파일 목록 확인
dir backups\ /OD  # 날짜순 정렬

# 3. 가장 최신 백업으로 복원
copy "backups\daham_meal_backup_20250912_*.db" "daham_meal.db"
```

#### 데이터 검증
```javascript
// API로 데이터 개수 확인
fetch('/api/admin/ingredients?page=1&limit=1')
  .then(r => r.json())
  .then(d => console.log('총 데이터:', d.total_count));
```

### 시나리오 C: "보안 경고가 계속 나타남"

#### 경고 메시지 분석
```javascript
// 위반 내역 상세 확인
const violations = window.ProtectionAPI.getViolations();
console.table(violations);

// 보호 시스템 상태
console.log('보호 시스템:', window.ProtectionAPI.getStats());
```

#### 해결 방법
1. **일시적 해결**: 페이지 새로고침 (F5)
2. **근본적 해결**: 
   ```javascript
   // 보호 시스템 리셋 (개발자용)
   window.FortressProtection.violations = [];
   window.ProtectionAPI.performCheck();
   ```
3. **비상시**: 보호 시스템 비활성화
   ```javascript
   window.FortressProtection.disable();
   ```

---

## 🔍 고급 진단 도구 

### 자동 문제 탐지 스크립트
```javascript
// 종합 건강 체크
function fortressHealthCheck() {
    console.log('🏥 === Fortress 시스템 건강 체크 ===');
    
    const issues = [];
    const warnings = [];
    
    // 1. 핵심 시스템 체크
    if (!window.Fortress) issues.push('Fortress 프레임워크 미로드');
    if (!window.ModuleRegistry) issues.push('Module Registry 미로드');
    if (!window.APIGateway) issues.push('API Gateway 미로드');
    if (!window.FortressProtection) issues.push('Protection System 미로드');
    
    // 2. 모듈 체크
    const moduleStatus = window.ModuleRegistry?.getModuleStatus() || {};
    Object.entries(moduleStatus).forEach(([name, status]) => {
        if (!status.loaded) issues.push(`모듈 '${name}' 로드 실패`);
        if (status.hasError) issues.push(`모듈 '${name}' 오류: ${status.error}`);
    });
    
    // 3. 성능 체크
    if (performance.memory) {
        const memoryMB = performance.memory.usedJSHeapSize / 1024 / 1024;
        if (memoryMB > 50) warnings.push(`높은 메모리 사용량: ${memoryMB.toFixed(1)}MB`);
    }
    
    // 4. API 체크
    fetch('/api/admin/ingredients?page=1&limit=1')
        .then(r => r.ok ? 'API 정상' : 'API 오류')
        .then(result => console.log('API 상태:', result))
        .catch(e => issues.push('API 연결 실패: ' + e.message));
    
    // 5. 보고서 출력
    console.log('🔍 진단 결과:');
    console.log('심각한 문제:', issues.length ? issues : '없음');
    console.log('경고사항:', warnings.length ? warnings : '없음');
    
    const healthScore = Math.max(0, 100 - issues.length * 20 - warnings.length * 5);
    console.log(`💯 건강 점수: ${healthScore}/100`);
    
    return {
        issues,
        warnings,
        healthScore,
        recommendation: healthScore >= 80 ? '정상 운영 가능' :
                       healthScore >= 60 ? '주의 필요' : '즉시 점검 필요'
    };
}

// 사용: fortressHealthCheck()
```

### 성능 프로파일링 도구
```javascript
// 상세 성능 분석
function fortressPerformanceProfile() {
    console.log('⚡ === 성능 프로파일링 시작 ===');
    
    const profile = {
        memory: performance.memory ? {
            used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024) + 'MB',
            total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024) + 'MB',
            limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024) + 'MB'
        } : 'N/A',
        timing: {
            domLoad: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
            pageLoad: performance.timing.loadEventEnd - performance.timing.navigationStart,
            firstPaint: performance.getEntriesByType('paint').find(p => p.name === 'first-paint')?.startTime || 'N/A'
        },
        resources: performance.getEntriesByType('resource')
            .filter(r => r.name.includes('system/'))
            .map(r => ({
                name: r.name.split('/').pop(),
                loadTime: Math.round(r.responseEnd - r.startTime) + 'ms',
                size: r.transferSize ? Math.round(r.transferSize / 1024) + 'KB' : 'N/A'
            }))
    };
    
    console.table(profile.timing);
    console.table(profile.resources);
    console.log('메모리 사용량:', profile.memory);
    
    // 성능 등급 매기기
    const loadTime = profile.timing.pageLoad;
    const grade = loadTime < 2000 ? 'A (우수)' :
                  loadTime < 5000 ? 'B (양호)' :
                  loadTime < 10000 ? 'C (보통)' : 'D (개선필요)';
    
    console.log(`📊 성능 등급: ${grade} (로딩시간: ${loadTime}ms)`);
    
    return profile;
}
```

---

## 📞 문제 해결 플로우차트

```
문제 발생
    ↓
[긴급도 평가]
    ↓
🔴 치명적 → 기존 /admin 즉시 사용 → 원인 분석
    ↓
🟡 기능적 → 브라우저 새로고침 → 진단 실행
    ↓  
🟠 UI/UX → 캐시 클리어 → 호환성 확인
    ↓
해결됨? → Yes: 모니터링 계속
    ↓
     No: 전문가 문의/문서 참조
```

---

## 🎯 결론

이 트러블슈팅 가이드로 Fortress 시스템의 **99% 문제를 해결**할 수 있습니다.

### 🚀 기억해야 할 3가지 골든 룰:
1. **🔴 문제 발생 시 즉시**: `/admin` 으로 전환
2. **🔧 해결 시도 순서**: 새로고침 → 재시작 → 진단 → 복원
3. **📋 모든 변경 후**: 건강체크 실행

**🏰 Fortress 시스템이 당신을 보호하듯, 이 가이드가 시스템을 보호합니다!**