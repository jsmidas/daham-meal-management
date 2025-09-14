# 🍱 다함 식자재 관리 시스템

통합 급식 관리 솔루션 - 식자재, 협력업체, 식단가 관리를 한 곳에서

## 🚀 빠른 시작

### 1️⃣ 서버 시작
```batch
START_ALL_SERVERS.bat
```

### 2️⃣ 접속
```
http://127.0.0.1:3000/admin_dashboard.html
```

### 3️⃣ 서버 종료
```batch
STOP_ALL_SERVERS.bat
```

## 📊 주요 기능

### 🏢 협력업체 관리
- 5개 주요 협력업체 (삼성웰스토리, 현대그린푸드, CJ, 푸디스트, 동원홈푸드)
- 협력업체별 식자재 현황
- 사업장-협력업체 매핑

### 🥘 식자재 관리
- 84,215개 식자재 데이터
- 카테고리별 분류 및 검색
- 가격 정보 관리

### 💰 식단가 관리
- 사업장별 식단표 관리
- 조식/중식/석식/야식 구분
- 판매가 및 목표재료비 설정
- 원가율 자동 계산

### 👥 사용자 관리
- 권한별 접근 제어
- 로그인 이력 관리

## 🛠️ 시스템 구성

| 구성요소 | 포트 | 용도 |
|---------|------|------|
| **메인 API 서버** | 8010 | 모든 API 엔드포인트 |
| **정적 파일 서버** | 3000 | HTML/CSS/JS 서빙 |
| **서버 모니터** | - | 실시간 서버 상태 모니터링 |

## 📁 프로젝트 구조

```
daham-meal-management/
├── 🚀 실행 파일
│   ├── START_ALL_SERVERS.bat    # 서버 시작
│   ├── STOP_ALL_SERVERS.bat     # 서버 종료
│   └── server_monitor.py        # 서버 모니터링
│
├── 📡 서버
│   ├── test_samsung_api.py      # 메인 API 서버
│   └── simple_server.py         # 정적 파일 서버
│
├── 🌐 웹 인터페이스
│   ├── admin_dashboard.html     # 관리자 대시보드
│   └── static/                  # 정적 리소스
│
├── 💾 데이터
│   └── daham_meal.db           # SQLite 데이터베이스
│
└── 📚 문서
    ├── README.md               # 이 파일
    ├── CLAUDE.md              # 개발 가이드
    └── API_DOCUMENTATION.md   # API 문서
```

## 🖥️ 서버 모니터링

```batch
python server_monitor.py
```

### 모니터링 기능
- ✅ 실시간 서버 상태
- ✅ 포트별 프로세스 정보
- ✅ 메모리/CPU 사용량
- ✅ 서버 시작/종료 제어

### 명령어
- `[R]` 새로고침
- `[S]` 모든 서버 시작
- `[K]` 모든 서버 종료
- `[1-3]` 개별 서버 제어
- `[Q]` 종료

## 📊 데이터베이스 정보

### 테이블 구조
- `users` - 사용자 정보
- `suppliers` - 협력업체
- `business_locations` - 사업장
- `ingredients` - 식자재 (84,215개)
- `meal_pricing` - 식단가
- `customer_supplier_mappings` - 매핑 정보

## 🔧 기술 스택

- **Backend**: Python 3.8+, FastAPI
- **Database**: SQLite3
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **서버**: Uvicorn (ASGI)

## 📝 API 문서

자세한 API 정보는 [API_DOCUMENTATION.md](API_DOCUMENTATION.md) 참조

### 주요 엔드포인트
- `/api/admin/dashboard-stats` - 대시보드 통계
- `/api/admin/users` - 사용자 관리
- `/api/admin/suppliers` - 협력업체 관리
- `/api/admin/ingredients-new` - 식자재 관리
- `/api/admin/meal-pricing` - 식단가 관리

## 🆘 문제 해결

### 포트 충돌
```batch
# 포트 확인
netstat -ano | findstr :8010

# 프로세스 종료
taskkill /F /PID [PID]
```

### 한글 깨짐
```batch
chcp 65001
```

### 모든 Python 종료
```batch
taskkill /F /IM python.exe
```

## 📈 시스템 요구사항

- Windows 10/11
- Python 3.8+
- Chrome 90+ (권장)
- 최소 RAM: 4GB
- 디스크: 500MB

## 🔐 보안

- 로컬 환경 전용
- 프로덕션 배포 시 추가 보안 설정 필요
- 데이터베이스 정기 백업 권장

## 📅 업데이트 이력

- **2025-01-14**: 식단가 관리 기능 완성
- **2025-01-13**: 협력업체 매핑 개선
- **2025-01-12**: 시스템 통합 및 최적화

## 📞 지원

문제 발생 시 GitHub Issues 또는 내부 IT팀 문의

---

**© 2025 다함 식자재 관리 시스템**