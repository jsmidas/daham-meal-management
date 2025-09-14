import sqlite3

conn = sqlite3.connect('daham_meal.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(business_locations)')
columns = cursor.fetchall()

print("business_locations 테이블 필드 정보:")
print("-" * 50)
for col in columns:
    col_id, name, data_type, not_null, default_val, pk = col
    required = "필수" if not_null else "선택"
    default = f" (기본값: {default_val})" if default_val else ""
    print(f"{name}: {required}{default}")

conn.close()