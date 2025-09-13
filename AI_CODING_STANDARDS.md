# 🤖 AI 개발 표준 - "양식 바뀜 방지" 가이드

## 🚨 **AI 필수 준수사항**

### **❌ AI가 절대 하지 말아야 할 것**
1. **기존 HTML 구조 변경** - 레이아웃, 클래스명, ID 절대 건드리지 말 것
2. **새로운 CSS 프레임워크 도입** - Bootstrap, 기존 스타일 유지
3. **JavaScript 모듈 구조 변경** - 기존 모듈 패턴 그대로 사용
4. **데이터 구조 임의 변경** - DB 스키마, API 응답 형식 유지
5. **네이밍 컨벤션 변경** - 기존 변수명, 함수명 스타일 따르기

### **✅ AI가 반드시 해야 할 것**
1. **기존 코드 패턴 분석** - 새 기능도 동일한 스타일로
2. **템플릿 사용** - 아래 정의된 표준 템플릿만 사용
3. **점진적 개선** - 전체 구조 바꾸지 말고 부분 수정만
4. **일관성 유지** - 같은 타입의 기능은 같은 방식으로

## 📋 **표준 코드 템플릿**

### **HTML 템플릿 - 새 페이지 생성 시**
```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>다함 식자재 관리 - [페이지명]</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="config.js"></script>
</head>
<body>
    <div class="container-fluid">
        <!-- 표준 헤더 -->
        <div class="row">
            <div class="col-12">
                <h1 class="text-primary mb-4">🍽️ [기능명]</h1>
            </div>
        </div>
        
        <!-- 메인 컨텐츠 영역 -->
        <div class="row">
            <div class="col-12">
                <!-- 내용 -->
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // 표준 초기화
        document.addEventListener('DOMContentLoaded', function() {
            console.log('[페이지명] 초기화 완료');
        });
    </script>
</body>
</html>
```

### **JavaScript 모듈 템플릿**
```javascript
// 표준 모듈 구조 - 절대 변경하지 말 것
class [ModuleName]Module {
    constructor() {
        this.apiBase = CONFIG.API.BASE_URL;
        this.isLoading = false;
        this.data = [];
        this.init();
    }

    init() {
        console.log('[ModuleName] 모듈 초기화 시작');
        this.bindEvents();
        this.loadData();
    }

    bindEvents() {
        // 이벤트 바인딩
    }

    async loadData() {
        try {
            this.isLoading = true;
            const response = await API.get('ENDPOINT_NAME');
            const data = await response.json();
            this.data = data;
            this.render();
        } catch (error) {
            console.error('[ModuleName] 데이터 로드 에러:', error);
            this.showError();
        } finally {
            this.isLoading = false;
        }
    }

    render() {
        // 렌더링 로직
    }

    showError() {
        // 표준 에러 표시
        console.error('데이터 로드 실패');
    }
}

// 전역 초기화
if (typeof window !== 'undefined') {
    window.[ModuleName]Module = [ModuleName]Module;
}
```

### **CSS 클래스 표준**
```css
/* 절대 변경하지 말 것 - 기존 스타일 유지 */
.status-success { color: #28a745; }
.status-warning { color: #ffc107; }
.status-error { color: #dc3545; }
.loading { opacity: 0.6; pointer-events: none; }
.hidden { display: none; }
```

## 🔧 **AI 개발 워크플로**

### **1단계: 기존 코드 분석 (필수)**
```bash
# 항상 먼저 실행할 것
1. 관련 파일들의 패턴 파악
2. 변수명 규칙 확인  
3. 함수 구조 분석
4. CSS 클래스 사용법 확인
```

### **2단계: 템플릿 적용**
- 위의 표준 템플릿을 기반으로 코딩
- 기존 스타일과 100% 일치하도록

### **3단계: 검증**
- 기존 페이지와 동일한 look & feel 확인
- API 연결 방식 동일한지 확인
- 에러 처리 방식 통일되었는지 확인

## 📏 **네이밍 규칙 (절대 변경 금지)**

### **변수명**
```javascript
// 기존 패턴 유지
const apiUrl = CONFIG.API.BASE_URL;          // camelCase
const tableBody = document.getElementById(); // camelCase
let isLoading = false;                       // boolean은 is/has 접두사
```

### **함수명**
```javascript
// 기존 패턴 유지
async loadData() {}        // load + 명사
async saveData() {}        // save + 명사  
showModal() {}             // show/hide + UI요소
bindEvents() {}            // bind + Events
```

### **CSS 클래스**
```css
/* 기존 패턴 유지 */
.btn-primary { }           /* kebab-case */
.table-responsive { }      /* kebab-case */
.status-success { }        /* status- 접두사 */
```

## 🚫 **AI 금지 행동**

### **절대 하지 말 것**
1. "더 모던한 방식으로 개선하겠습니다" - NO!
2. "React/Vue로 변경하는 게 좋겠습니다" - NO!
3. "CSS Grid로 바꾸겠습니다" - NO!
4. "REST API를 GraphQL로" - NO!
5. "새로운 디자인 시스템 적용" - NO!

### **올바른 AI 응답**
1. "기존 패턴을 따라 구현하겠습니다"
2. "현재 구조를 유지하며 기능만 추가하겠습니다"
3. "동일한 스타일로 개발하겠습니다"

## 📚 **코드 예시 - DO & DON'T**

### ❌ **잘못된 방법 (AI가 자주 하는 실수)**
```javascript
// 매번 다른 구조 사용
const handleClick = async (event) => {
    try {
        const result = await fetchData(`${baseUrl}/api/data`);
        updateUI(result.data);
    } catch (err) {
        showErrorMessage(err.message);
    }
}
```

### ✅ **올바른 방법 (기존 패턴 따르기)**
```javascript
// 기존과 동일한 구조 사용
async loadIngredientsData() {
    try {
        this.isLoading = true;
        const response = await API.get('ALL_INGREDIENTS');
        const data = await response.json();
        this.displayIngredients(data.ingredients || []);
    } catch (error) {
        console.error('[Ingredients] 데이터 로드 에러:', error);
        this.showFallbackData();
    } finally {
        this.isLoading = false;
    }
}
```

## 🎯 **AI 체크리스트**

개발 전 반드시 확인할 것:
- [ ] 기존 HTML 구조 분석 완료
- [ ] 기존 CSS 클래스 사용법 파악
- [ ] 기존 JavaScript 패턴 확인
- [ ] API 호출 방식 통일성 확인
- [ ] 에러 처리 방식 일관성 확인
- [ ] 네이밍 컨벤션 일치 확인

---
**💡 AI야, 창의성은 나중에! 일관성이 먼저다! 기존 코드 스타일을 종교처럼 따라라!**