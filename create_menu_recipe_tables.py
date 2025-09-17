import sqlite3
import os

# 데이터베이스 경로
db_path = 'backups/daham_meal.db'

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 새로운 메뉴 레시피 테이블 생성
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS menu_recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_code VARCHAR(50) UNIQUE NOT NULL,
        recipe_name VARCHAR(200) NOT NULL,
        category VARCHAR(50) NOT NULL,
        food_color VARCHAR(30),
        total_cost DECIMAL(10, 2),
        serving_size INTEGER DEFAULT 1,
        cooking_note TEXT,
        image_path VARCHAR(500),
        image_thumbnail VARCHAR(500),
        created_by VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        supplier_id INTEGER,
        business_location_id INTEGER
    )
    """)

    # 메뉴 레시피 재료 테이블 생성
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS menu_recipe_ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipe_id INTEGER NOT NULL,
        ingredient_code VARCHAR(100),
        ingredient_name VARCHAR(200) NOT NULL,
        specification VARCHAR(100),
        unit VARCHAR(50),
        delivery_days INTEGER DEFAULT 0,
        selling_price DECIMAL(10, 2),
        quantity DECIMAL(10, 3),
        amount DECIMAL(10, 2),
        supplier_name VARCHAR(100),
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (recipe_id) REFERENCES menu_recipes(id) ON DELETE CASCADE
    )
    """)

    # 인덱스 생성
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_menu_recipes_category ON menu_recipes(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_menu_recipe_ingredients_recipe ON menu_recipe_ingredients(recipe_id)")

    conn.commit()
    conn.close()

    print("✅ menu_recipes 및 menu_recipe_ingredients 테이블이 성공적으로 생성되었습니다.")
else:
    print("❌ 데이터베이스 파일을 찾을 수 없습니다.")