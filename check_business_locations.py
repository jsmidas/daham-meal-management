import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('daham_meal.db')
cursor = conn.cursor()

# business_locations 테이블 확인
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='business_locations'")
if cursor.fetchone():
    print("business_locations 테이블 확인")
    cursor.execute("SELECT * FROM business_locations")
    locations = cursor.fetchall()

    # 컬럼 정보 확인
    cursor.execute("PRAGMA table_info(business_locations)")
    columns = cursor.fetchall()
    print("\n컬럼 정보:")
    for col in columns:
        print(f"  {col[1]}: {col[2]}")

    print(f"\n총 {len(locations)}개의 사업장")
    print("\n사업장 목록:")
    for loc in locations:
        print(f"  - {loc}")
else:
    # 다른 테이블 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Available tables:")
    for table in tables:
        print(f"  - {table[0]}")

    # sites 테이블 확인
    cursor.execute("SELECT * FROM sites LIMIT 10")
    sites = cursor.fetchall()
    print(f"\nsites 테이블 데이터 ({len(sites)}개):")
    for site in sites:
        print(f"  - {site}")

conn.close()