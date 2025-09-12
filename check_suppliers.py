import sqlite3

conn = sqlite3.connect('daham_meal.db')
cursor = conn.cursor()

# 테이블 구조 확인
print("=== Suppliers 테이블 컬럼 ===")
cursor.execute('PRAGMA table_info(suppliers)')
for col in cursor.fetchall():
    print(f"  {col[1]}")

# 동원 데이터 확인
print("\n=== 동원 업체 데이터 ===")
cursor.execute("SELECT * FROM suppliers WHERE id = 3")
cols = [desc[0] for desc in cursor.description]
row = cursor.fetchone()
if row:
    for i, col in enumerate(cols):
        print(f"  {col}: {row[i]}")

conn.close()