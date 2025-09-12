# 🍽️ AI 식판 시각화 시스템 기술 사양서

## 📋 프로젝트 개요
**목표**: 선택된 메뉴를 실제 식판에 배치된 모양으로 AI 시각화하여 직관적 메뉴 평가 제공

## ⚡ 성능 최적화 전략

### 🎯 **이미지 용량 관리 (최적화 완료)**
```
급식업 현장 맞춤 해상도 시스템:
├── Level 1 (목록용): 200×200px, 15-25KB (WebP)
├── Level 2 (선택용): 400×400px, 40-60KB (WebP) ⭐ 기본 작업용
├── Level 3 (합성용): 600×600px, 80-120KB (WebP) ⭐ AI 처리용
└── Level 4 (인쇄용): 1000×1000px, 200-300KB (WebP)
```

### 📷 **촬영 및 전처리 가이드**
```
촬영 표준:
├── 해상도: 최소 1200×1200px로 촬영 (후처리용)
├── 배경: 순백색 배경 (배경 제거 용이)
├── 조명: 자연광 또는 균등한 LED
├── 각도: 45도 위에서 (실제 보는 각도)
├── 구도: 음식이 화면의 70% 차지
└── 포맷: 원본은 PNG, 최종은 WebP

자동 후처리 파이프라인:
├── 1단계: AI 배경 제거
├── 2단계: 스마트 크롭 (여백 제거)
├── 3단계: 4단계 리사이징 (200/400/600/1000px)
├── 4단계: WebP 변환 (60% 용량 절약)
└── 5단계: 데이터베이스 등록
```

### 💾 **스마트 캐싱 시스템**
```python
# 캐시 계층 구조
class ImageCacheManager:
    def __init__(self):
        self.memory_cache = {}      # 자주 사용 (50개)
        self.disk_cache = {}        # 일반 사용 (500개)  
        self.cloud_storage = {}     # 전체 보관
        
    def get_image(self, ingredient_id, resolution_level):
        # 1. 메모리 캐시 확인
        # 2. 디스크 캐시 확인  
        # 3. 클라우드에서 다운로드
        # 4. 동적 리사이징
```

### 🔄 **점진적 로딩**
```javascript
// 단계별 이미지 로딩
function loadMealVisualization(ingredients) {
    // 1단계: 식판 윤곽선 즉시 표시
    showPlateOutline();
    
    // 2단계: 저해상도 음식 배치  
    ingredients.forEach(item => {
        loadThumbnail(item.id).then(img => placeFoodOnPlate(img));
    });
    
    // 3단계: 고해상도로 점진적 업그레이드
    setTimeout(() => upgradeToHighRes(ingredients), 1000);
}
```

## 🏗️ 기술 아키텍처

### 🖼️ **이미지 처리 파이프라인**
```
원본 사진 수집 → 전처리 → 배경 제거 → 표준화 → 다단계 압축 → DB 저장
      ↓
사용자 메뉴 선택 → AI 배치 계산 → 실시간 합성 → 캐시 저장 → 화면 출력
```

### 🗃️ **데이터베이스 설계**
```sql
-- 식자재 이미지 테이블
CREATE TABLE ingredient_images (
    id INTEGER PRIMARY KEY,
    ingredient_id INTEGER REFERENCES ingredients(id),
    image_type VARCHAR(20),  -- 'raw', 'cooked', 'side_dish'
    resolution_level INTEGER, -- 1=thumb, 2=medium, 3=high
    file_path VARCHAR(500),
    file_size INTEGER,
    width INTEGER,
    height INTEGER,
    created_at TIMESTAMP,
    INDEX(ingredient_id, resolution_level)
);

-- 식판 템플릿 테이블  
CREATE TABLE plate_templates (
    id INTEGER PRIMARY KEY,
    template_name VARCHAR(100),
    plate_type VARCHAR(50),    -- 'standard', 'compartment', 'bowl'
    width INTEGER,
    height INTEGER,
    zones TEXT,               -- JSON: 음식 배치 구역 정보
    background_image VARCHAR(500)
);

-- 생성된 식판 이미지 캐시
CREATE TABLE generated_meals (
    id INTEGER PRIMARY KEY, 
    menu_hash VARCHAR(64),    -- 메뉴 구성의 해시값
    plate_template_id INTEGER,
    image_path VARCHAR(500),
    created_at TIMESTAMP,
    access_count INTEGER,
    INDEX(menu_hash)
);
```

### 🎨 **AI 이미지 배치 알고리즘**
```python
class MealPlateComposer:
    def __init__(self):
        self.plate_zones = {
            'main_dish': {'x': 200, 'y': 150, 'w': 200, 'h': 150},
            'side_dish_1': {'x': 50, 'y': 100, 'w': 120, 'h': 80},
            'side_dish_2': {'x': 50, 'y': 200, 'w': 120, 'h': 80},
            'soup': {'x': 450, 'y': 50, 'w': 100, 'h': 100},
            'rice': {'x': 450, 'y': 200, 'w': 100, 'h': 80}
        }
    
    def compose_meal(self, ingredients):
        plate = self.load_plate_template()
        
        for ingredient in ingredients:
            # 1. 음식 분류 (주식, 부식, 국물 등)
            food_type = self.classify_food(ingredient)
            
            # 2. 적절한 구역 선택
            zone = self.plate_zones[food_type]
            
            # 3. 이미지 크기 조절 및 배치
            food_image = self.resize_and_fit(ingredient.image, zone)
            plate = self.blend_image(plate, food_image, zone)
            
        return plate
```

## 📊 **용량 및 성능 예상치**

### 💾 **저장 공간 (최적화 반영)**
```
기본 이미지 DB (WebP 최적화):
├── 식자재 1,000종 × 4해상도 × 평균 45KB = 180MB
├── 식판 템플릿 20개 × 300KB = 6MB
└── 총 기본 용량: 186MB (기존 220MB에서 34MB 절약)

일일 생성 이미지:
├── 새 메뉴 조합 50개 × 80KB = 4MB/일
├── 월 누적: 120MB
└── 자동 정리로 80MB 이하 유지

실제 사용 시나리오:
├── 400×400px 기본 이미지: 60KB × 1,000개 = 60MB ⭐
├── 자주 쓰는 메뉴 100개 캐시: 6MB
├── 생성된 식판 이미지 임시 저장: 10-20MB
└── 총 실시간 메모리 사용량: 80-90MB
```

### ⚡ **성능 지표**
```
목표 성능:
├── 첫 화면 로딩: 2초 이내
├── 메뉴 변경 시 업데이트: 1초 이내  
├── 고해상도 전환: 3초 이내
└── 메모리 사용량: 100MB 이하
```

## 🛠️ **개발 단계별 계획**

### Phase 1: 기초 인프라 (1-2주)
- [ ] 이미지 업로드 및 전처리 시스템
- [ ] 다단계 해상도 생성 도구
- [ ] 기본 캐싱 시스템 구축
- [ ] 식판 템플릿 관리 인터페이스

### Phase 2: 핵심 알고리즘 (2-3주)  
- [ ] AI 음식 분류 시스템
- [ ] 식판 배치 알고리즘 개발
- [ ] 이미지 합성 엔진 구축
- [ ] 실시간 미리보기 기능

### Phase 3: 최적화 및 UX (1-2주)
- [ ] 점진적 로딩 구현
- [ ] 성능 모니터링 도구
- [ ] 사용자 인터페이스 통합
- [ ] 모바일 대응

### Phase 4: 고급 기능 (2-3주)
- [ ] 영양 정보 시각화 오버레이
- [ ] 계절별/테마별 식판 템플릿
- [ ] 사용자 커스텀 배치 기능
- [ ] 인쇄/PDF 출력 기능

## 🎯 **차별화 포인트**

### 💡 **독창성**
1. **업계 최초**: 실제 식판 시각화 시스템
2. **실용성**: 영양사 실무에 직접 활용 가능
3. **직관성**: 숫자가 아닌 시각으로 품질 평가
4. **확장성**: AR/VR, 3D 모델링으로 발전 가능

### 🏆 **기술적 우위**  
1. **최적화**: 대용량 이미지 처리의 효율적 관리
2. **안정성**: 기존 시스템과 독립적 운영
3. **확장성**: 모듈형 아키텍처로 기능 확장 용이
4. **호환성**: 기존 84,000+ 식자재 DB 완벽 연동

## 💰 **비즈니스 모델**

### 📦 **패키징 전략**
```
🥇 베이스 패키지: 500만원
+ 기본 식자재 관리

🥈 비주얼 패키지: +500만원 (총 1,000만원)
+ AI 식판 시각화
+ 기본 템플릿 20개
+ 저해상도 미리보기

🥉 프리미엄 패키지: +300만원 (총 1,300만원)  
+ 고해상도 출력
+ 커스텀 템플릿
+ 영양 정보 오버레이
+ 인쇄/PDF 기능
```

### 🎪 **마케팅 포인트**
- **"메뉴를 보는 새로운 방법"** - 혁신성 강조
- **"실제 식판 그대로"** - 현실성 강조  
- **"한 눈에 품질 확인"** - 편의성 강조
- **"급식업계 디지털 혁신"** - 미래성 강조

---

**🚀 결론: 기술적 실현 가능하며, 용량 부담 최소화로 안정적 구현 가능**