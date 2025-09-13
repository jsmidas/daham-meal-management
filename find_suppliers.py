import sqlite3
import os

# 모든 DB 파일 확인
db_files = [
    'daham_ingredients.db',
    'daham_meal.db',
    'backups/working_state_20250912/daham_meal.db'
]

for db_file in db_files:
    if os.path.exists(db_file):
        print(f"\n=== {db_file} ===")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # 테이블 목록
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables:", [t[0] for t in tables])

        # ingredients 테이블 확인
        if any('ingredient' in t[0].lower() for t in tables):
            cursor.execute("SELECT * FROM ingredients LIMIT 3;")
            rows = cursor.fetchall()
            print("\nIngredients sample:")
            for row in rows:
                print(row)

            # supplier 관련 필드 확인
            cursor.execute("PRAGMA table_info(ingredients);")
            cols = cursor.fetchall()
            print("\nIngredients columns:")
            for col in cols:
                print(f"  {col[1]} ({col[2]})")

            # 주요 공급업체 찾기
            cursor.execute("""
                SELECT supplier, COUNT(*) as cnt
                FROM ingredients
                WHERE supplier IS NOT NULL
                GROUP BY supplier
                ORDER BY cnt DESC
                LIMIT 10;
            """)
            suppliers = cursor.fetchall()
            print("\nTop suppliers:")
            for s in suppliers:
                print(f"  {s[0]}: {s[1]}")

        conn.close()