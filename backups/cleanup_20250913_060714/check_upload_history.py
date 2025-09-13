import sqlite3

conn = sqlite3.connect('daham_meal.db')
cursor = conn.cursor()

# 테이블 구조 확인
print("=== 테이블 구조 ===")
cursor.execute('PRAGMA table_info(ingredient_upload_history)')
for col in cursor.fetchall():
    print(col)

# 컬럼 이름만 추출
cursor.execute('PRAGMA table_info(ingredient_upload_history)')
columns = [col[1] for col in cursor.fetchall()]
print("\n=== 컬럼 목록 ===")
print(columns)

# 데이터 샘플 확인
print("\n=== 첫 번째 레코드 ===")
cursor.execute('SELECT * FROM ingredient_upload_history LIMIT 1')
row = cursor.fetchone()
if row:
    for i, col in enumerate(columns):
        print(f"{col}: {row[i]}")

conn.close()