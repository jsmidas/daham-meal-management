# 🎨 현재 시스템 브랜딩 요소 분석

## 📊 **발견된 브랜딩 요소들**

### 🏷️ **회사명/시스템명**
```
주요 브랜딩 텍스트:
├── "다함식단관리" (메인 시스템명)
├── "다함 급식관리" (서브 시스템명)
├── "다함 식자재 관리" (모듈명)
├── "다함식단관리시스템" (전체명)
├── "다함" (단축명)
└── "🍽️ 다함식단관리시스템" (아이콘 포함)
```

### 📍 **브랜딩 위치별 분포**

#### HTML 파일별 브랜딩 요소:
```
admin_dashboard.html:
├── <title>다함식단관리 - 관리자 대시보드</title> (라인 6)
└── <p>다함식단관리</p> (라인 1402 - 사이드바)

dashboard.html:
├── <title>📈 대시보드 - 다함식단관리시스템</title>
└── <h1>다함 급식관리</h1>

ingredients_management.html:
├── <title>다함 식자재 관리</title>  
└── <h1>다함 급식관리</h1>

meal_count_management.html:
├── <title>식수 등록 관리 - 다함식단관리시스템</title>
└── <h1>다함 급식관리</h1>

cooking_instruction_management.html:
├── <title>다함 조리지시서 관리</title>
└── <h1>다함 급식관리</h1>
```

### 🎨 **시각적 브랜딩 요소**

#### 컬러 스킴 (현재):
```css
주 브랜드 색상:
├── 그라데이션: linear-gradient(135deg, #667eea 0%, #764ba2 100%)
├── Primary: #667eea (밝은 보라)  
├── Secondary: #764ba2 (진한 보라)
└── Background: #f5f5f5 (연한 회색)
```

#### 로고 관련:
```
현재 상태:
├── 텍스트 로고만 사용 (이미지 로고 없음)
├── 아이콘: 🍽️ (식기 이모지)
├── 파비콘: 기본 브라우저 아이콘
└── 브랜드 이미지: 없음
```

## 🛠️ **화이트라벨 변환 타겟 항목들**

### ⚡ **즉시 변경 가능 (Level 1)**
```
1. HTML 제목 태그 (<title>)
   - 총 20개 파일에서 "다함" 포함 제목
   
2. 사이드바 시스템명
   - admin_dashboard.html 라인 1402: <p>다함식단관리</p>
   
3. 헤더 시스템명  
   - 각 관리 페이지의 <h1>다함 급식관리</h1>
   
4. 네비게이션 로고
   - meal_count_timeline.html의 "🍽️ 다함식단관리시스템"
```

### 🎨 **브랜딩 강화 필요 (Level 2)**
```
1. 로고 이미지 추가
   - 파비콘 (16x16, 32x32)
   - 사이드바 로고 (200x60)
   - 로그인 페이지 로고 (300x100)
   
2. 컬러 테마 시스템
   - CSS 변수 도입
   - 고객사별 브랜드 컬러 적용
   
3. 푸터/저작권 정보
   - 고객사 연락처 정보
   - 지원팀 연락처
```

## 🔍 **기술적 구현 방안**

### 📝 **텍스트 치환 리스트**
```python
BRAND_REPLACEMENTS = {
    # 기본 시스템명
    '다함식단관리': '{{SYSTEM_NAME}}',
    '다함 급식관리': '{{COMPANY_NAME}} 급식관리', 
    '다함 식자재 관리': '{{COMPANY_NAME}} 식자재 관리',
    '다함식단관리시스템': '{{SYSTEM_NAME}}',
    '🍽️ 다함식단관리시스템': '🍽️ {{SYSTEM_NAME}}',
    
    # 단축형
    '다함': '{{COMPANY_NAME}}',
    
    # 메타 정보
    '다함식단관리 - 관리자 대시보드': '{{SYSTEM_NAME}} - 관리자 대시보드',
    '📈 대시보드 - 다함식단관리시스템': '📈 대시보드 - {{SYSTEM_NAME}}',
    '식수 등록 관리 - 다함식단관리시스템': '식수 등록 관리 - {{SYSTEM_NAME}}',
    '다함 조리지시서 관리': '{{COMPANY_NAME}} 조리지시서 관리'
}
```

### 🎨 **CSS 변수 시스템 도입**
```css
/* 현재 하드코딩된 색상들을 변수로 변경 */
:root {
    --brand-primary: #667eea;
    --brand-secondary: #764ba2; 
    --brand-gradient: linear-gradient(135deg, var(--brand-primary) 0%, var(--brand-secondary) 100%);
    --company-name: "다함";
    --system-name: "다함식단관리";
}

/* 사용 예시 */
.sidebar {
    background: var(--brand-gradient);
}
```

## 🚀 **1단계 화이트라벨 구현 계획**

### ⏰ **즉시 시작 가능한 작업 (30분 내)**
1. **브랜딩 설정 파일 생성**
   ```python
   # white_label_config.py
   CUSTOMER_BRANDING = {
       'company_name': '고객사명',
       'system_name': '고객사 급식관리 시스템',
       'primary_color': '#007bff',
       'secondary_color': '#6c757d'
   }
   ```

2. **텍스트 치환 스크립트 작성**
   ```python
   # replace_branding.py
   def replace_brand_text(file_path, branding_config):
       # HTML 파일의 브랜딩 텍스트 자동 치환
   ```

### 📅 **오늘 완료 목표**
- [ ] 브랜딩 요소 완전 분석 완료 ✅
- [ ] 자동 치환 스크립트 작성
- [ ] 테스트 고객사로 브랜딩 변경 실험
- [ ] 변경 전후 스크린샷 비교

---

**🎯 다음 단계: 자동 치환 스크립트 개발하여 실제로 테스트해보기!**