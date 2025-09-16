-- 레시피 메인 테이블
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_code VARCHAR(50) UNIQUE NOT NULL, -- 레시피 고유 코드 (예: RCP_2025_001)
    recipe_name VARCHAR(200) NOT NULL,       -- 메뉴명
    category VARCHAR(50) NOT NULL,           -- 분류 (국, 밥, 찌개 등)
    food_color VARCHAR(30),                  -- 음식 색상
    total_cost DECIMAL(10, 2),               -- 총 재료비
    serving_size INTEGER DEFAULT 1,          -- 인분수
    cooking_note TEXT,                        -- 조리법 메모
    image_path VARCHAR(500),                 -- 이미지 파일 경로
    image_thumbnail VARCHAR(500),            -- 썸네일 이미지 경로
    created_by VARCHAR(100),                 -- 작성자
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,             -- 사용 여부
    supplier_id INTEGER,                     -- 협력업체 ID
    business_location_id INTEGER,            -- 사업장 ID
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
    FOREIGN KEY (business_location_id) REFERENCES business_locations(id)
);

-- 레시피 상세 (재료) 테이블
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    ingredient_code VARCHAR(100),            -- 식자재코드
    ingredient_name VARCHAR(200) NOT NULL,   -- 식자재명
    specification VARCHAR(100),              -- 규격
    unit VARCHAR(50),                        -- 단위
    delivery_days INTEGER DEFAULT 0,         -- 선발주일
    selling_price DECIMAL(10, 2),            -- 판매가
    quantity DECIMAL(10, 3),                 -- 1인소요량
    amount DECIMAL(10, 2),                   -- 1인재료비
    supplier_name VARCHAR(100),              -- 거래처명
    sort_order INTEGER DEFAULT 0,            -- 정렬 순서
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);

-- 레시피 이미지 테이블 (여러 이미지 저장 가능)
CREATE TABLE IF NOT EXISTS recipe_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    image_type VARCHAR(50) DEFAULT 'main',   -- main, step1, step2, result 등
    original_path VARCHAR(500),              -- 원본 이미지 경로
    compressed_path VARCHAR(500),            -- 압축된 이미지 경로
    thumbnail_path VARCHAR(500),             -- 썸네일 경로
    file_size INTEGER,                       -- 파일 크기 (bytes)
    width INTEGER,                           -- 이미지 너비
    height INTEGER,                          -- 이미지 높이
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX idx_recipes_category ON recipes(category);
CREATE INDEX idx_recipes_supplier ON recipes(supplier_id);
CREATE INDEX idx_recipes_location ON recipes(business_location_id);
CREATE INDEX idx_recipe_ingredients_recipe ON recipe_ingredients(recipe_id);
CREATE INDEX idx_recipe_images_recipe ON recipe_images(recipe_id);

-- 뷰 생성: 레시피 요약 정보
CREATE VIEW recipe_summary AS
SELECT
    r.id,
    r.recipe_code,
    r.recipe_name,
    r.category,
    r.total_cost,
    r.image_thumbnail,
    COUNT(DISTINCT ri.id) as ingredient_count,
    s.supplier_name,
    bl.location_name
FROM recipes r
LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
LEFT JOIN suppliers s ON r.supplier_id = s.id
LEFT JOIN business_locations bl ON r.business_location_id = bl.id
WHERE r.is_active = 1
GROUP BY r.id;