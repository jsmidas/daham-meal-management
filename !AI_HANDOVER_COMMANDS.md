# AI 교체 시 필수 명령어 가이드

## 🚨 새로운 AI에게 첫 번째로 반드시 말해야 할 것

```
⚠️ 작업하기 전에 반드시 AI_HANDOVER_COMMANDS.md 파일을 처음부터 끝까지 읽어보세요.
읽지 않고 작업을 시작하면 시스템이 망가질 수 있습니다.

이 시스템은 AI-Resistant Fortress Architecture로 보호되고 있습니다.
절대로 admin_dashboard.html, framework.js, module-registry.js, api-gateway.js, protection.js 파일을 수정하지 마세요.
```

## 📋 단계별 AI 온보딩 명령어

### STEP 1: 시스템 이해 (5분)
```
1. ARCHITECTURE.md 파일을 읽어보세요
2. FORTRESS_DEPLOYMENT.md 파일을 읽어보세요  
3. 현재 시스템이 http://127.0.0.1:8003/admin-fortress 에서 실행 중인지 확인해보세요
4. python main.py 로 서버가 실행 중인지 확인해보세요
```

### STEP 2: 보호된 파일 확인 (3분)
```
다음 파일들은 절대 수정하면 안 됩니다:
- admin_dashboard.html (5,756줄의 메인 대시보드)
- static/js/framework.js (핵심 프레임워크)
- static/js/module-registry.js (모듈 관리)
- static/js/api-gateway.js (API 게이트웨이)
- static/js/protection.js (보호 시스템)

이 파일들을 읽기만 하고 절대 수정하지 마세요.
```

### STEP 3: 작업 전 필수 체크 (2분)
```
작업하기 전에 다음을 직접 실행하세요:

🌐 브라우저에서:
1. http://127.0.0.1:8003/admin 접속 → 기존 시스템 작동 확인
2. http://127.0.0.1:8003/admin-fortress 접속 → Fortress 시스템 로딩 확인
3. F12 개발자도구 Console에서 다음 명령어 실행:
   window.Fortress.getSystemInfo()
   window.ModuleRegistry.getModuleStatus()
   window.ProtectionAPI.getStats()

💻 터미널에서:
4. curl -I http://127.0.0.1:8003 실행 → HTTP 200 응답 확인
5. python main.py 가 실행 중인지 확인

위 5단계가 모두 성공해야 작업을 시작할 수 있습니다.
```

## 🛡️ 금지 명령어 (절대 하면 안 되는 것들)

### ❌ 절대 하지 말 것
```
- admin_dashboard.html 파일 수정
- framework.js, module-registry.js, api-gateway.js, protection.js 수정
- 기존 모듈 구조 변경
- 대규모 리팩토링
- "더 나은 방법으로 개선하겠습니다" 류의 제안
```

### ✅ 허용되는 작업
```
- modules/ 폴더 내 개별 모듈 수정
- app/api/ 폴더 내 백엔드 API 추가/수정
- 새로운 기능을 위한 별도 모듈 생성
- CSS 스타일 개선 (기존 구조 유지하에서)
- 버그 수정 (보호된 파일 제외)
```

## 🔧 일반적인 작업 명령어

### 새 기능 추가 시
```
1. modules/ 폴더에 새 모듈을 만들어주세요
2. 기존 패턴을 따라서 모듈을 작성해주세요
3. FORTRESS_CHECKLIST.md로 테스트해주세요
4. 기존 시스템에 영향을 주지 않는지 확인해주세요
```

### 버그 수정 시
```
1. 먼저 어떤 파일이 문제인지 확인해주세요
2. 보호된 파일이면 modules/ 폴더에서 우회 방법을 찾아주세요
3. 수정 후 FORTRESS_CHECKLIST.md Phase 1,2를 실행해주세요
```

### 데이터베이스 작업 시
```
1. models.py나 app/api/ 폴더에서 작업해주세요
2. 기존 테이블 구조를 변경하기 전에 백업을 만들어주세요
3. daham_meal.db 파일을 직접 수정하지 마세요
```

## 🚨 응급 상황 대응

### 시스템이 깨졌을 때
```
1. 즉시 http://127.0.0.1:8003/admin 으로 기존 시스템 접속하세요
2. FORTRESS_TROUBLESHOOTING.md의 응급 대응 매뉴얼을 따르세요
3. python main.py 재시작을 시도하세요
4. 그래도 안 되면 backups/ 폴더에서 복원하세요
```

### AI가 실수로 보호된 파일을 수정했을 때
```
1. 즉시 git status로 변경사항을 확인하세요
2. git checkout HEAD -- [파일명] 으로 되돌리세요
3. FORTRESS_CHECKLIST.md Phase 1을 실행해서 시스템 상태를 확인하세요
```

## 📚 필수 읽기 자료 순서

```
1. ARCHITECTURE.md (시스템 전체 구조 이해)
2. FORTRESS_DEPLOYMENT.md (배포 및 운영 가이드)  
3. FORTRESS_CHECKLIST.md (테스트 절차)
4. FORTRESS_TROUBLESHOOTING.md (문제 해결)
5. FORTRESS_PERFORMANCE.md (성능 최적화)
```

## 💡 AI별 특별 주의사항

### Claude 계열 AI
```
- 너무 적극적으로 개선하려 하지 마세요
- 기존 코드를 존중하고 점진적 개선만 하세요
- "더 나은 방법"을 제안하기 전에 현재 시스템의 이유를 이해하세요
```

### GPT 계열 AI  
```
- 대규모 리팩토링 제안을 하지 마세요
- 한 번에 많은 것을 바꾸려 하지 마세요
- 작은 단위로 나누어서 작업하세요
```

### 기타 AI
```
- 이 가이드를 먼저 완전히 이해한 후 작업을 시작하세요
- 확신이 서지 않으면 읽기 전용으로 시스템을 분석하세요
- 수정하기 전에 반드시 사용자에게 확인받으세요
```

## 📅 체크리스트 업데이트 가이드

### 🔄 업데이트가 필요한 상황들
- [ ] 새 모듈이 modules/ 폴더에 추가될 때
- [ ] 보호 대상 파일이 변경될 때  
- [ ] API 엔드포인트가 추가/변경될 때
- [ ] 데이터베이스 스키마가 변경될 때
- [ ] 새로운 보안 정책이 추가될 때

### 📝 업데이트 방법
```
1. 변경사항 발생 시 즉시 AI_HANDOVER_COMMANDS.md 수정
2. FORTRESS_CHECKLIST.md의 해당 Phase에 새 항목 추가
3. 새 AI에게 전달할 때 "최신 버전을 확인하세요" 명시
```

### 📊 문서 버전 추적
```
- AI_HANDOVER_COMMANDS.md 최종 수정: 2025-09-12
- 마지막 주요 업데이트: Fortress 아키텍처 완성
- 다음 예정 업데이트: 시스템 변경 시
```

---

**⚠️ 중요: 이 가이드를 새로운 AI에게 전달할 때는 반드시 전문을 복사해서 제공하세요.**
**📋 새로운 AI 온보딩 필수 명령어: "!AI_HANDOVER_COMMANDS.md 파일을 먼저 읽어보세요"**