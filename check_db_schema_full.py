import sqlite3
import os

# 데이터베이스 경로
db_path = 'backups/daham_meal.db'

if os.path.exists(db_path):
    print(f"데이터베이스 파일 확인: {db_path}")
    print("=" * 80)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. 모든 테이블 목록
    print("\n1. 데이터베이스의 모든 테이블:")
    print("-" * 40)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        if 'recipe' in table_name.lower():
            print(f"  [RECIPE] {table_name}: {count}개 데이터")
        else:
            print(f"  {table_name}: {count}개 데이터")

    # 2. recipes 테이블 확인
    print("\n2. recipes 테이블 구조 확인:")
    print("-" * 40)
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='recipes'")
    result = cursor.fetchone()
    if result:
        print("recipes 테이블 존재:")
        print(result[0])

        # recipes 테이블의 칼럼 정보
        cursor.execute("PRAGMA table_info(recipes)")
        columns = cursor.fetchall()
        print("\nrecipes 테이블 칼럼 목록:")
        for col in columns:
            print(f"  - {col[1]}: {col[2]}")
    else:
        print("recipes 테이블이 없습니다.")

    # 3. menu_recipes 테이블 확인
    print("\n3. menu_recipes 테이블 구조 확인:")
    print("-" * 40)
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='menu_recipes'")
    result = cursor.fetchone()
    if result:
        print("menu_recipes 테이블 존재:")
        print(result[0])

        # menu_recipes 테이블의 칼럼 정보
        cursor.execute("PRAGMA table_info(menu_recipes)")
        columns = cursor.fetchall()
        print("\nmenu_recipes 테이블 칼럼 목록:")
        for col in columns:
            print(f"  - {col[1]}: {col[2]}")
    else:
        print("menu_recipes 테이블이 없습니다.")

    # 4. menu_recipe_ingredients 테이블 확인
    print("\n4. menu_recipe_ingredients 테이블 구조 확인:")
    print("-" * 40)
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='menu_recipe_ingredients'")
    result = cursor.fetchone()
    if result:
        print("menu_recipe_ingredients 테이블 존재:")
        print(result[0])

        # menu_recipe_ingredients 테이블의 칼럼 정보
        cursor.execute("PRAGMA table_info(menu_recipe_ingredients)")
        columns = cursor.fetchall()
        print("\nmenu_recipe_ingredients 테이블 칼럼 목록:")
        for col in columns:
            print(f"  - {col[1]}: {col[2]}")
    else:
        print("menu_recipe_ingredients 테이블이 없습니다.")

    # 5. 데이터 확인
    print("\n5. 저장된 레시피 데이터 확인:")
    print("-" * 40)

    # menu_recipes에서 데이터 확인
    cursor.execute("SELECT COUNT(*) FROM menu_recipes")
    count = cursor.fetchone()[0]
    print(f"menu_recipes 테이블의 총 레시피 수: {count}")

    if count > 0:
        cursor.execute("SELECT id, recipe_code, recipe_name, category, created_at FROM menu_recipes ORDER BY id DESC LIMIT 5")
        recent = cursor.fetchall()
        print("\n최근 저장된 레시피 5개:")
        for r in recent:
            print(f"  ID: {r[0]}, Code: {r[1]}, Name: {r[2]}, Category: {r[3]}, Created: {r[4]}")

    conn.close()
    print("\n" + "=" * 80)
    print("스키마 확인 완료!")
else:
    print(f"데이터베이스 파일을 찾을 수 없습니다: {db_path}")