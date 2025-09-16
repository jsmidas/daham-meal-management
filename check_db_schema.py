import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('backups/daham_meal.db')
cursor = conn.cursor()

# ingredients 테이블 구조 확인
cursor.execute("PRAGMA table_info(ingredients)")
columns = cursor.fetchall()

print("=== ingredients 테이블 구조 ===")
for col in columns:
    print(f"{col[1]:20} {col[2]:15} {'NOT NULL' if col[3] else 'NULL':10} Default: {col[4] or 'None'}")

print("\n=== 샘플 데이터 (첫 3개) ===")
cursor.execute("SELECT * FROM ingredients LIMIT 3")
rows = cursor.fetchall()
col_names = [col[1] for col in columns]

for row in rows:
    print("\n---")
    for i, value in enumerate(row):
        if value:
            print(f"{col_names[i]:20}: {str(value)[:50]}")

# 누락된 필드 확인
expected_fields = [
    'specification', 'origin', 'posting_status', 'tax_free',
    'pre_order_days', 'memo', 'created_at', 'price_per_gram'
]

existing_fields = [col[1] for col in columns]
missing_fields = [f for f in expected_fields if f not in existing_fields]

if missing_fields:
    print(f"\n=== 누락된 필드 ===")
    for field in missing_fields:
        print(f"- {field}")

conn.close()
