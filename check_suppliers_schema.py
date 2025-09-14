import sqlite3

conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
cursor = conn.cursor()

# 모든 테이블 목록 확인
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("데이터베이스의 모든 테이블:")
print("-" * 50)
for table in tables:
    print(f"- {table[0]}")

# ingredients 테이블에서 supplier 관련 정보 확인
print("\ningredients 테이블의 supplier 관련 컬럼:")
print("-" * 50)
cursor.execute("PRAGMA table_info(ingredients)")
columns = cursor.fetchall()
for col in columns:
    if 'supplier' in col[1].lower():
        print(f"Column: {col[1]}, Type: {col[2]}")

# 고유한 supplier 목록 확인
print("\n고유한 supplier_name 목록:")
print("-" * 50)
cursor.execute("SELECT DISTINCT supplier_name FROM ingredients WHERE supplier_name IS NOT NULL LIMIT 10")
suppliers = cursor.fetchall()
for supplier in suppliers:
    print(f"- {supplier[0]}")

conn.close()