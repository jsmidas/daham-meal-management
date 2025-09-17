import sqlite3
import os

db_path = 'backups/daham_meal.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 모든 테이블 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()

    print("=== 데이터베이스 테이블 목록 ===")
    for table in tables:
        if 'recipe' in table[0].lower():
            print(f"✅ {table[0]}")
        else:
            print(f"   {table[0]}")

    # menu_recipes 테이블 구조 확인
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='menu_recipes'")
    result = cursor.fetchone()
    if result:
        print("\n=== menu_recipes 테이블 구조 ===")
        print(result[0])
    else:
        print("\n❌ menu_recipes 테이블이 없습니다.")

    # menu_recipe_ingredients 테이블 구조 확인
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='menu_recipe_ingredients'")
    result = cursor.fetchone()
    if result:
        print("\n=== menu_recipe_ingredients 테이블 구조 ===")
        print(result[0])
    else:
        print("\n❌ menu_recipe_ingredients 테이블이 없습니다.")

    conn.close()
else:
    print("데이터베이스 파일을 찾을 수 없습니다.")