import sqlite3

# DB 연결
db_path = 'backups/working_state_20250912/daham_meal.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== 협력업체(공급업체) 관련 테이블 확인 ===\n")

# 테이블 목록 확인
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("전체 테이블 목록:")
for table in tables:
    table_name = table[0]
    if 'supplier' in table_name.lower() or 'vendor' in table_name.lower() or 'partner' in table_name.lower():
        print(f"  ✓ {table_name} (공급업체 관련)")
    else:
        print(f"    {table_name}")

# suppliers 테이블 확인
print("\n=== suppliers 테이블 확인 ===")
cursor.execute("PRAGMA table_info(suppliers);")
columns = cursor.fetchall()
print("컬럼 구조:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# 공급업체 데이터 확인
print("\n=== 공급업체 데이터 샘플 ===")
cursor.execute("SELECT * FROM suppliers LIMIT 10;")
suppliers = cursor.fetchall()
for supplier in suppliers:
    print(f"  {supplier}")

# 주요 공급업체 확인
print("\n=== 주요 공급업체 (동원, 푸디스트, 삼성, 현대, CJ) ===")
cursor.execute("""
    SELECT * FROM suppliers
    WHERE name LIKE '%동원%'
       OR name LIKE '%푸디스트%'
       OR name LIKE '%삼성%'
       OR name LIKE '%현대%'
       OR name LIKE '%CJ%'
    LIMIT 20;
""")
major_suppliers = cursor.fetchall()
for supplier in major_suppliers:
    print(f"  {supplier}")

# 전체 공급업체 수
cursor.execute("SELECT COUNT(*) FROM suppliers;")
total = cursor.fetchone()[0]
print(f"\n총 공급업체 수: {total}")

# 공급업체별 집계
print("\n=== 공급업체별 통계 ===")
cursor.execute("""
    SELECT name, COUNT(*) as cnt
    FROM suppliers
    GROUP BY name
    ORDER BY cnt DESC
    LIMIT 10;
""")
stats = cursor.fetchall()
for stat in stats:
    print(f"  {stat[0]}: {stat[1]}개")

conn.close()