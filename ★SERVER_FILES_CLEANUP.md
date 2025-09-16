# 🧹 서버 파일 정리 가이드

## 📌 현재 사용 중인 서버 파일 (유지)

### ⭐ 핵심 서버 파일
1. **unified_control_tower.py** ✅ [메인 서버]
   - 포트: 8080
   - 기능: 웹서버 + API 관리 + 모니터링 통합
   - **이것만 있으면 모든 기능 사용 가능**

2. **test_samsung_api.py** ✅ [API 서버]
   - 포트: 8010, 8015
   - 기능: FastAPI 기반 데이터베이스 API
   - 식자재, 협력업체, 사용자 관리 API

3. **simple_server.py** ✅ [백업용 웹서버]
   - 포트: 9000
   - 기능: 정적 파일 서빙
   - unified_control_tower가 있으면 불필요

### ⭐ 시작 파일 (유지)
- **★QUICK_START.bat** - 대화형 서버 시작 메뉴
- **★START_SERVER.bat** - 자동 서버 시작
- **★server_control_panel.html** - 웹 기반 서버 관리 패널

---

## 🗑️ 삭제 가능한 중복/구버전 파일

### 구버전 서버 파일
1. **server_control_tower.py** ❌
   - unified_control_tower.py로 대체됨
   - 삭제 가능

2. **server_manager.py** ❌
   - 구버전 서버 관리 도구
   - unified_control_tower.py로 기능 통합됨
   - 삭제 가능

3. **server_manager_simple.py** ❌
   - server_manager의 간소화 버전
   - 더 이상 필요 없음
   - 삭제 가능

4. **server_monitor.py** ❌
   - 별도 모니터링 도구
   - unified_control_tower에 모니터링 기능 포함
   - 삭제 가능

5. **test_monitor.py** ❌
   - 모니터링 테스트 파일
   - 삭제 가능

### 구버전 API 파일
6. **daham_api.py** ❌
   - 구버전 API 서버
   - test_samsung_api.py로 대체됨
   - 삭제 가능

7. **user_api_server.py** ❌
   - 사용자 전용 API (구버전)
   - test_samsung_api.py에 통합됨
   - 삭제 가능

8. **add_meal_pricing_api.py** ❌
   - 단일 기능 API 추가 파일
   - test_samsung_api.py에 이미 포함됨
   - 삭제 가능

---

## 📂 정리 후 구조

```
daham-meal-management/
├── ⭐ 핵심 서버 파일
│   ├── unified_control_tower.py    # 메인 통합 서버
│   ├── test_samsung_api.py        # API 서버
│   └── simple_server.py           # 백업 웹서버
│
├── ⭐ 시작/관리 파일
│   ├── ★QUICK_START.bat          # 대화형 시작 메뉴
│   ├── ★START_SERVER.bat         # 자동 시작
│   └── ★server_control_panel.html # 웹 관리 패널
│
└── 📁 기타 파일들
    ├── admin_dashboard.html       # 관리자 대시보드
    ├── backups/                   # 데이터베이스 백업
    └── static/                    # 정적 리소스
```

---

## 🎯 권장 사항

### 즉시 실행 방법:
1. **★QUICK_START.bat** 실행
2. **1번 선택** (통합 컨트롤 타워)
3. 브라우저에서 자동으로 서버 컨트롤 패널 열림

### 삭제 명령어:
```batch
# 구버전 서버 파일 삭제
del server_control_tower.py
del server_manager.py
del server_manager_simple.py
del server_monitor.py
del test_monitor.py
del daham_api.py
del user_api_server.py
del add_meal_pricing_api.py
```

### 백업 권장:
삭제 전에 backups 폴더에 백업을 만들어두는 것을 권장합니다.

---

## ✅ 정리 결과

- **이전**: 11개의 서버 관련 파일
- **이후**: 3개의 핵심 파일 + 3개의 시작 파일
- **효과**: 파일 수 45% 감소, 관리 복잡도 대폭 감소

모든 기능은 **unified_control_tower.py** 하나로 통합되어 있으므로,
이것만 실행하면 웹서버, API 관리, 모니터링을 모두 사용할 수 있습니다.