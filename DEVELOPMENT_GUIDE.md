# 🚀 다함 식자재 관리 시스템 - 개발 가이드

## 🎯 **"미친짓 중단" - 표준 개발 워크플로**

### ⚡ **30초 시작법**
```bash
# 1. 자동 설정 실행 (모든 서버 자동 시작)
auto_setup.bat

# 2. 브라우저에서 확인
http://localhost:3000/admin_dashboard.html
```

## 🔧 **설정 변경이 필요할 때**

### **API 포트 변경**
```javascript
// config.js 파일에서 한 번만 수정
API: {
    BASE_URL: 'http://127.0.0.1:NEW_PORT',  // 여기만 바꾸면 됨
}
```

### **환경 변수 변경**
```bash
# .env 파일에서 수정
API_PORT=NEW_PORT
```

## 📋 **절대 하지 말아야 할 것들**

### ❌ **절대 금지 사항**
1. **HTML 파일에서 직접 API URL 수정** - config.js만 사용
2. **여러 파일에서 포트 번호 하드코딩** - 중앙 설정만 사용
3. **매번 새로운 설정 파일 생성** - 기존 구조 활용
4. **서버 포트를 무작정 변경** - 표준 포트 사용

### ✅ **올바른 방법**
1. **config.js에서만 설정 변경**
2. **auto_setup.bat으로 자동 시작**
3. **문제 발생 시 auto_stop.bat → auto_setup.bat**

## 🛠️ **표준 개발 프로세스**

### **1. 개발 시작**
```bash
auto_setup.bat  # 모든 환경 자동 설정
```

### **2. 개발 중**
- HTML/JS 수정 → 브라우저 새로고침만
- API 변경 → 서버 재시작 (auto_stop.bat → auto_setup.bat)

### **3. 개발 완료**
```bash
auto_stop.bat   # 모든 서버 안전 종료
```

## 🔍 **문제 해결**

### **API 연결 안될 때**
1. `netstat -an | findstr ":8006"` - 서버 실행 확인
2. `curl http://127.0.0.1:8006/api/admin/dashboard-stats` - API 테스트
3. config.js의 BASE_URL 확인

### **데이터 연결 안될 때**
1. `.env`에서 DB_PATH 확인
2. 백업 폴더의 DB 파일 존재 확인
3. auto_setup.bat 재실행

## 📊 **파일 구조**
```
📁 프로젝트/
├── 🔧 config.js          # 중앙 설정 (가장 중요!)
├── 🌍 .env               # 환경 변수
├── ⚡ auto_setup.bat     # 자동 시작
├── 🛑 auto_stop.bat      # 자동 종료
├── 📱 admin_dashboard.html
├── 🛠️ admin_simple.html
└── 🐍 test_samsung_api.py # API 서버
```

## 🎯 **핵심 원칙**

### **One Source of Truth (단일 진실 원칙)**
- 모든 API URL은 **config.js**에서만 관리
- 환경 설정은 **.env**에서만 관리
- 자동화는 **auto_setup.bat**으로만 실행

### **DRY (Don't Repeat Yourself)**
- 같은 설정을 여러 파일에 복사하지 않음
- 중앙 설정을 모든 곳에서 참조

### **Zero Configuration**
- 개발자가 포트나 URL을 직접 수정할 필요 없음
- auto_setup.bat 실행만으로 모든 환경 자동 구성

## 🚨 **긴급 복구**
```bash
# 모든 것이 망가졌을 때
auto_stop.bat           # 일단 모든 서버 종료
del config.js           # 설정 파일 삭제 후
# config.js 다시 생성 또는 백업에서 복사
auto_setup.bat          # 재시작
```

---
**💡 이제 매번 포트 찾고 API 연결하는 미친짓은 끝! 한 번 설정하면 영원히 자동화!**