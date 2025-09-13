"""
BOKSILI 시스템 전체 데이터 구조 분석 및 예측
공급업체 데이터 + 주간 식단표 데이터 = 실제 시스템 구조 예측
"""

import json
import pandas as pd
from pathlib import Path

def analyze_boksili_system():
    """BOKSILI 시스템 전체 구조 분석"""
    
    print("="*80)
    print("BOKSILI 시스템 전체 구조 분석 및 예측")
    print("="*80)
    
    # 1. 공급업체 데이터 분석 결과 로드
    supplier_analysis = load_analysis_file('supplier_data_analysis.json')
    
    # 2. 주간 식단표 분석 결과 로드  
    weekly_analysis = load_analysis_file('weekly_meal_plan_analysis.json')
    
    # 3. 통합 분석
    system_structure = predict_system_structure(supplier_analysis, weekly_analysis)
    
    # 4. 결과 출력
    print_system_analysis(system_structure)
    
    # 5. DB 스키마 제안
    suggest_database_schema(system_structure)
    
    # 6. API 구조 제안
    suggest_api_structure(system_structure)

def load_analysis_file(filename):
    """분석 결과 파일 로드"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"경고: {filename} 파일을 찾을 수 없습니다.")
        return {}

def predict_system_structure(supplier_data, weekly_data):
    """실제 BOKSILI 시스템 구조 예측"""
    
    structure = {
        'system_name': 'BOKSILI - 위탁급식 식자재 발주관리 전산시스템',
        'main_modules': {},
        'data_flow': {},
        'user_roles': {},
        'key_features': {}
    }
    
    # 1. 주요 모듈 분석
    structure['main_modules'] = {
        'supplier_management': {
            'description': '공급업체 관리',
            'features': [
                '공급업체별 식자재 단가표 관리',
                '주기적 단가 업데이트 (주간/월간)',
                '공급업체별 고유 코드 체계',
                '원산지, 규격, 단위 정보 관리'
            ],
            'data_sources': list(supplier_data.keys()) if supplier_data else [],
            'suppliers_count': len([f for f in supplier_data.values() if f.get('filename_info', {}).get('supplier')]) if supplier_data else 0
        },
        'meal_planning': {
            'description': '식단표 관리',
            'features': [
                '주간 단위 식단표 작성',
                '카테고리별 식단 관리 (도시락, 요양원, 학교, 운반)',
                '요일별 × 식사별 메뉴 배치',
                '메뉴별 레시피 정보 연결'
            ],
            'data_sources': list(weekly_data.keys()) if weekly_data else [],
            'categories': list(set([f.get('date_info', {}).get('category') for f in weekly_data.values() if f.get('date_info', {}).get('category')])) if weekly_data else []
        },
        'ordering_system': {
            'description': '발주 시스템',
            'features': [
                '식단표 기반 자동 발주량 계산',
                '공급업체별 발주서 생성',
                '발주 승인 프로세스',
                '협력업체 발주시스템 (OOS) 연동'
            ],
            'integration_points': ['supplier_management', 'meal_planning']
        }
    }
    
    # 2. 데이터 흐름 분석
    structure['data_flow'] = {
        'input_stage': {
            '공급업체 단가표 업로드': '엑셀 파일 → 파싱 → DB 저장',
            '식단표 작성': '웹 인터페이스 → 메뉴 선택 → 주간 계획 → DB 저장'
        },
        'processing_stage': {
            '발주량 계산': '식단표 + 인분수 → 식자료 소요량 계산',
            '가격 계산': '소요량 + 최신 단가 → 예상 비용 계산',
            '발주서 생성': '소요량 + 공급업체 정보 → 발주서 자동 생성'
        },
        'output_stage': {
            '발주서 출력': 'PDF/엑셀 형태 발주서',
            '비용 리포트': '카테고리별/기간별 비용 분석',
            '재고 관리': '입고/출고 현황 관리'
        }
    }
    
    # 3. 사용자 역할 분석
    structure['user_roles'] = {
        '영양사': {
            'permissions': ['식단표 작성', '메뉴 관리', '영양 정보 관리'],
            'main_tasks': ['주간 식단표 계획', '메뉴 선택 및 조합', '영양 균형 검토']
        },
        '구매담당자': {
            'permissions': ['발주서 생성', '공급업체 관리', '단가표 업데이트'],
            'main_tasks': ['발주량 확인', '공급업체 협의', '가격 협상']
        },
        '관리자': {
            'permissions': ['전체 시스템 관리', '사용자 관리', '시스템 설정'],
            'main_tasks': ['사용자 권한 관리', '시스템 모니터링', '데이터 백업']
        },
        '협력업체': {
            'permissions': ['발주서 확인', '납품 현황 업데이트'],
            'main_tasks': ['발주 내역 확인', '납품 일정 관리', '재고 현황 보고']
        }
    }
    
    # 4. 핵심 기능 분석
    structure['key_features'] = analyze_key_features(supplier_data, weekly_data)
    
    return structure

def analyze_key_features(supplier_data, weekly_data):
    """핵심 기능 분석"""
    
    features = {}
    
    # 공급업체 데이터 기반 기능
    if supplier_data:
        total_items = sum([
            data.get('sheets', {}).get(sheet, {}).get('shape', [0])[0] 
            for data in supplier_data.values()
            for sheet in data.get('sheets', {})
        ])
        
        suppliers = set([
            data.get('filename_info', {}).get('supplier')
            for data in supplier_data.values()
            if data.get('filename_info', {}).get('supplier')
        ])
        
        features['supplier_management'] = {
            'total_suppliers': len(suppliers),
            'total_items': total_items,
            'suppliers': list(suppliers),
            'price_update_cycle': '주간/월간',
            'data_format': 'Excel 기반'
        }
    
    # 식단표 데이터 기반 기능
    if weekly_data:
        categories = set([
            data.get('date_info', {}).get('category')
            for data in weekly_data.values()
            if data.get('date_info', {}).get('category')
        ])
        
        total_menus = sum([
            len([item for item in data.get('sheets', {}).values() 
                for item_list in [item.get('menu_items', [])] 
                for item in item_list])
            for data in weekly_data.values()
        ])
        
        features['meal_planning'] = {
            'categories': list(categories),
            'planning_unit': '주간 (7일)',
            'structure': '요일 × 식사 매트릭스',
            'estimated_menus': total_menus
        }
    
    return features

def print_system_analysis(structure):
    """시스템 분석 결과 출력"""
    
    print(f"\n시스템명: {structure['system_name']}")
    print("\n" + "="*60)
    
    # 주요 모듈
    print("주요 모듈:")
    for module_name, module_info in structure['main_modules'].items():
        print(f"\n  {module_name.upper()}:")
        print(f"    설명: {module_info['description']}")
        
        if 'suppliers_count' in module_info:
            print(f"    공급업체 수: {module_info['suppliers_count']}")
        if 'categories' in module_info:
            print(f"    카테고리: {', '.join(module_info['categories'])}")
        
        print("    주요 기능:")
        for feature in module_info['features']:
            print(f"      - {feature}")
    
    # 사용자 역할
    print(f"\n사용자 역할:")
    for role, role_info in structure['user_roles'].items():
        print(f"  {role}:")
        print(f"    주요 업무: {', '.join(role_info['main_tasks'])}")
    
    # 핵심 기능 통계
    print(f"\n시스템 규모:")
    if 'supplier_management' in structure['key_features']:
        sm = structure['key_features']['supplier_management']
        print(f"  공급업체: {sm['total_suppliers']}개")
        print(f"  총 식자재: {sm['total_items']:,}개")
    
    if 'meal_planning' in structure['key_features']:
        mp = structure['key_features']['meal_planning']
        print(f"  식단 카테고리: {len(mp['categories'])}개")
        print(f"  계획 단위: {mp['planning_unit']}")

def suggest_database_schema(structure):
    """DB 스키마 제안"""
    
    print(f"\n" + "="*60)
    print("제안 DB 스키마 (BOKSILI 시스템 최적화)")
    print("="*60)
    
    schema_suggestion = """
-- 1. 공급업체 관리
CREATE TABLE suppliers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE,
    contact_info JSON,
    update_frequency ENUM('weekly', 'monthly', 'realtime'),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. 식자재 마스터 (공급업체별)
CREATE TABLE ingredients (
    id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_id INT REFERENCES suppliers(id),
    supplier_code VARCHAR(50),
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50),
    subcategory VARCHAR(50),
    origin VARCHAR(100),
    unit VARCHAR(20),
    specification TEXT,
    is_tax_free BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_supplier_code (supplier_id, supplier_code)
);

-- 3. 식자재 가격 이력 (시계열 데이터)
CREATE TABLE ingredient_prices (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ingredient_id INT REFERENCES ingredients(id),
    cost_price DECIMAL(10, 2),
    selling_price DECIMAL(10, 2),
    effective_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_effective_date (ingredient_id, effective_date)
);

-- 4. 식단표 (주간 단위)
CREATE TABLE weekly_meal_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    category ENUM('도시락', '요양원', '학교', '운반'),
    week_start_date DATE,
    week_end_date DATE,
    target_persons INT,
    status ENUM('draft', 'approved', 'executed') DEFAULT 'draft',
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_week_category (week_start_date, category)
);

-- 5. 식단 상세 (요일별 × 식사별)
CREATE TABLE meal_plan_details (
    id INT PRIMARY KEY AUTO_INCREMENT,
    weekly_plan_id INT REFERENCES weekly_meal_plans(id),
    day_of_week TINYINT, -- 0=월요일, 6=일요일  
    meal_type ENUM('아침', '점심', '저녁'),
    menu_name VARCHAR(200),
    recipe_id INT, -- 레시피 연결용
    portion_size INT,
    notes TEXT,
    INDEX idx_weekly_day_meal (weekly_plan_id, day_of_week, meal_type)
);

-- 6. 발주서
CREATE TABLE purchase_orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    weekly_plan_id INT REFERENCES weekly_meal_plans(id),
    supplier_id INT REFERENCES suppliers(id),
    order_date DATE,
    delivery_date DATE,
    total_amount DECIMAL(12, 2),
    status ENUM('pending', 'sent', 'confirmed', 'delivered') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 발주 상세
CREATE TABLE purchase_order_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT REFERENCES purchase_orders(id),
    ingredient_id INT REFERENCES ingredients(id),
    quantity DECIMAL(10, 3),
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(12, 2),
    notes TEXT
);
"""
    
    print(schema_suggestion)

def suggest_api_structure(structure):
    """API 구조 제안"""
    
    print(f"\n" + "="*60)
    print("제안 API 구조 (CodeIgniter 기반)")
    print("="*60)
    
    api_suggestion = """
# 1. 공급업체 관리 API
GET  /api/suppliers              # 공급업체 목록
POST /api/suppliers              # 새 공급업체 등록
PUT  /api/suppliers/{id}         # 공급업체 정보 수정
POST /api/suppliers/upload       # 단가표 업로드 (Excel)

# 2. 식자재 관리 API  
GET  /api/ingredients            # 식자재 목록 (필터링 지원)
GET  /api/ingredients/search     # 식자재 검색
GET  /api/ingredients/{id}/prices # 가격 이력
POST /api/ingredients/sync       # 공급업체 데이터 동기화

# 3. 식단표 관리 API
GET  /api/meal-plans             # 주간 식단표 목록
POST /api/meal-plans             # 새 식단표 생성
PUT  /api/meal-plans/{id}        # 식단표 수정
GET  /api/meal-plans/{id}/cost   # 식단표 비용 계산

# 4. 발주 관리 API
POST /api/orders/generate        # 식단표 기반 발주서 자동 생성
GET  /api/orders                 # 발주서 목록
PUT  /api/orders/{id}/status     # 발주 상태 변경
GET  /api/orders/{id}/export     # 발주서 PDF/Excel 내보내기

# 5. 협력업체 API (OOS)
GET  /oos/orders                 # 협력업체용 발주서 조회
POST /oos/orders/{id}/confirm    # 발주서 확인
POST /oos/deliveries             # 납품 현황 업데이트

# 6. 리포트 API
GET  /api/reports/cost-analysis  # 비용 분석 리포트
GET  /api/reports/supplier-performance # 공급업체 성과 분석
GET  /api/reports/menu-popularity # 메뉴 인기도 분석
"""
    
    print(api_suggestion)
    
    print(f"\n핵심 구현 포인트:")
    print(f"  1. Excel 업로드 → 파싱 → DB 저장 자동화")
    print(f"  2. 식단표 기반 발주량 자동 계산 알고리즘") 
    print(f"  3. 실시간 가격 업데이트 시스템")
    print(f"  4. 협력업체 연동 API (OOS)")
    print(f"  5. 권한별 사용자 인터페이스")

if __name__ == "__main__":
    analyze_boksili_system()