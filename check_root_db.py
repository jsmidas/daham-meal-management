import sqlite3
import os

# 루트 디렉토리의 daham_meal.db 확인
db_path = 'daham_meal.db'

if os.path.exists(db_path):
    print(f"루트 디렉토리 데이터베이스 확인: {db_path}")
    print("=" * 80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # menu_recipes 테이블 데이터 확인
    cursor.execute("SELECT COUNT(*) FROM menu_recipes")
    count = cursor.fetchone()[0]
    print(f"\nmenu_recipes 테이블의 레시피 개수: {count}")

    if count > 0:
        cursor.execute("""
            SELECT id, recipe_code, recipe_name, category, total_cost, created_at
            FROM menu_recipes
            ORDER BY id DESC
            LIMIT 5
        """)
        recipes = cursor.fetchall()
        print("\n최근 저장된 레시피:")
        print("-" * 80)
        for r in recipes:
            print(f"ID: {r[0]}, Code: {r[1]}")
            print(f"   Name: {r[2]}")
            print(f"   Category: {r[3]}, Cost: {r[4]}, Created: {r[5]}")

            # 각 레시피의 재료도 확인
            cursor.execute("""
                SELECT ingredient_name, specification, quantity, amount
                FROM menu_recipe_ingredients
                WHERE recipe_id = ?
            """, (r[0],))
            ingredients = cursor.fetchall()
            if ingredients:
                print("   재료:")
                for ing in ingredients:
                    print(f"     - {ing[0]} ({ing[1]}): {ing[2]} 단위, {ing[3]}원")
            print()

    conn.close()
else:
    print(f"루트 디렉토리에 데이터베이스 파일이 없습니다: {db_path}")