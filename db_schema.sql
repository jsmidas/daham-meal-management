-- Daham Menu Manager DB 스키마 (PostgreSQL)

-- DietPlans: 식단표 (예: 학교 급식)
CREATE TABLE DietPlans (
    id SERIAL PRIMARY KEY,
    category VARCHAR(10) NOT NULL, -- 예: 학교
    date DATE NOT NULL, -- 예: 2025-08-14
    description TEXT, -- 예: 학교 급식 계획
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers: 공급업체 (Ingredients에서 참조하므로 먼저 정의)
CREATE TABLE Suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL, -- 예: 식자재왕
    contact VARCHAR(100),
    update_frequency VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ingredients: 식재료
CREATE TABLE Ingredients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL, -- 예: 냉동쥬키니호박
    base_unit VARCHAR(10) NOT NULL, -- 예: kg
    price DECIMAL(10, 2),
    supplier_id INT REFERENCES Suppliers(id),
    moq DECIMAL(10, 3) DEFAULT 1.0, -- 예: 1kg
    allergy_codes JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recipe: 레시피
CREATE TABLE Recipe (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL, -- 예: 호박새우젓국찌개
    version VARCHAR(10),
    effective_date DATE,
    notes TEXT, -- 예: 저염 조리
    nutrition_data JSON,
    evaluation_score INT CHECK (evaluation_score BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RecipeIngredients: 레시피-식재료 연결 테이블
CREATE TABLE RecipeIngredients (
    recipe_id INT REFERENCES Recipe(id) ON DELETE CASCADE,
    ingredient_id INT REFERENCES Ingredients(id),
    quantity DECIMAL(10, 3) NOT NULL, -- 1인량 (예: 0.045)
    unit VARCHAR(10) NOT NULL, -- 예: kg
    unit_in_kg DECIMAL(10, 3),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (recipe_id, ingredient_id)
);

-- Menus: 세부식단표 (예: 중식A)
CREATE TABLE Menus (
    id SERIAL PRIMARY KEY,
    diet_plan_id INT REFERENCES DietPlans(id) ON DELETE CASCADE,
    menu_type VARCHAR(15) NOT NULL, -- 예: 중식
    target_num_persons INT NOT NULL, -- 식수 (예: 105)
    target_food_cost DECIMAL(10, 2), -- 목표식재료비 (한글 컬럼명 수정)
    evaluation_score INT CHECK (evaluation_score BETWEEN 1 AND 5),
    color VARCHAR(20), -- ENUM 대신 VARCHAR 사용 (PostgreSQL에서 더 유연함)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MenuItems: 단일 식단표 (예: 호박새우젓국찌개)
CREATE TABLE MenuItems (
    id SERIAL PRIMARY KEY,
    menu_id INT REFERENCES Menus(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL, -- 예: 호박새우젓국찌개
    portion_num_persons INT, -- 식수 (기본: target_num_persons)
    yield_rate DECIMAL(3, 2) DEFAULT 1.0, -- 수율 (예: 0.7)
    recipe_id INT REFERENCES Recipe(id),
    photo_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- updated_at 자동 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

-- 각 테이블에 updated_at 트리거 적용
CREATE TRIGGER update_dietplans_timestamp
    BEFORE UPDATE ON DietPlans
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_suppliers_timestamp
    BEFORE UPDATE ON Suppliers
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_ingredients_timestamp
    BEFORE UPDATE ON Ingredients
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_recipe_timestamp
    BEFORE UPDATE ON Recipe
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_recipeingredients_timestamp
    BEFORE UPDATE ON RecipeIngredients
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_menus_timestamp
    BEFORE UPDATE ON Menus
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_menuitems_timestamp
    BEFORE UPDATE ON MenuItems
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- 성능 최적화를 위한 인덱스
CREATE INDEX idx_dietplans_date ON DietPlans(date);
CREATE INDEX idx_menus_diet_plan_id ON Menus(diet_plan_id);
CREATE INDEX idx_menus_menu_type ON Menus(menu_type);
CREATE INDEX idx_menuitems_menu_id ON MenuItems(menu_id);
CREATE INDEX idx_menuitems_recipe_id ON MenuItems(recipe_id);
CREATE INDEX idx_recipeingredients_recipe_id ON RecipeIngredients(recipe_id);
CREATE INDEX idx_recipeingredients_ingredient_id ON RecipeIngredients(ingredient_id);
CREATE INDEX idx_ingredients_supplier_id ON Ingredients(supplier_id);
CREATE INDEX idx_ingredients_name ON Ingredients(name);

-- 샘플 데이터 (엑셀 기반: 중식A, 식수 105, 호박새우젓국찌개, 쥬키니호박 0.045kg/인, 수율 0.7)

-- 1. 공급업체 추가
INSERT INTO Suppliers (name, contact, update_frequency) VALUES 
('식자재왕', '010-1234-5678', '주 2회');

-- 2. 식재료 추가
INSERT INTO Ingredients (name, base_unit, price, supplier_id, moq, allergy_codes) VALUES 
('쥬키니호박', 'kg', 5000, 1, 1.0, '[]'),
('새우젓', 'kg', 15000, 1, 0.5, '["갑각류"]'),
('대파', 'kg', 3000, 1, 1.0, '[]'),
('마늘', 'kg', 8000, 1, 1.0, '[]'),
('고춧가루', 'kg', 12000, 1, 0.5, '[]');

-- 3. 레시피 추가
INSERT INTO Recipe (name, version, effective_date, notes, nutrition_data, evaluation_score) VALUES 
('호박새우젓국찌개', '1.0', '2025-08-14', '저염 조리, 쥬키니호박 사용', 
'{"calories": 150, "protein": 8, "carbs": 12, "fat": 6, "sodium": 800}', 4);

-- 4. 레시피-식재료 연결 (1인분 기준)
INSERT INTO RecipeIngredients (recipe_id, ingredient_id, quantity, unit, unit_in_kg) VALUES 
(1, 1, 0.045, 'kg', 0.045), -- 쥬키니호박 45g/인
(1, 2, 0.003, 'kg', 0.003), -- 새우젓 3g/인
(1, 3, 0.008, 'kg', 0.008), -- 대파 8g/인
(1, 4, 0.002, 'kg', 0.002), -- 마늘 2g/인
(1, 5, 0.001, 'kg', 0.001); -- 고춧가루 1g/인

-- 5. 식단표 추가
INSERT INTO DietPlans (category, date, description) VALUES 
('학교', '2025-08-14', '2025년 8월 14일 학교 급식 계획');

-- 6. 메뉴 추가 (중식A, 식수 105명)
INSERT INTO Menus (diet_plan_id, menu_type, target_num_persons, target_food_cost, evaluation_score, color) VALUES 
(1, '중식A', 105, 50000, 4, 'blue');

-- 7. 메뉴 아이템 추가 (수율 0.7 적용)
INSERT INTO MenuItems (menu_id, name, portion_num_persons, yield_rate, recipe_id, photo_url) VALUES 
(1, '호박새우젓국찌개', 105, 0.7, 1, 'https://example.com/photos/pumpkin_soup.jpg');

-- 데이터 검증을 위한 뷰 생성
CREATE VIEW menu_cost_analysis AS
SELECT 
    dp.date,
    m.menu_type,
    m.target_num_persons,
    mi.name as dish_name,
    mi.yield_rate,
    r.name as recipe_name,
    SUM(ri.quantity * i.price * m.target_num_persons / mi.yield_rate) as estimated_cost
FROM DietPlans dp
JOIN Menus m ON dp.id = m.diet_plan_id
JOIN MenuItems mi ON m.id = mi.menu_id
JOIN Recipe r ON mi.recipe_id = r.id
JOIN RecipeIngredients ri ON r.id = ri.recipe_id
JOIN Ingredients i ON ri.ingredient_id = i.id
GROUP BY dp.date, m.menu_type, m.target_num_persons, mi.name, mi.yield_rate, r.name;