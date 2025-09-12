import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('daham_meal.db')
cursor = conn.cursor()

# 전체 식자재 개수 확인
cursor.execute("SELECT COUNT(*) FROM ingredients")
total_count = cursor.fetchone()[0]
print(f"전체 식자재 개수: {total_count:,}개")

# 웰스토리 데이터 개수 확인
cursor.execute("SELECT COUNT(*) FROM ingredients WHERE \"거래처명\" LIKE '%웰스토리%'")
welstory_count = cursor.fetchone()[0]
print(f"웰스토리 식자재 개수: {welstory_count:,}개")

# 거래처별 식자재 개수 (상위 10개)
print("\n거래처별 식자재 개수 (상위 10개):")
cursor.execute("""
    SELECT "거래처명", COUNT(*) as count 
    FROM ingredients 
    GROUP BY "거래처명" 
    ORDER BY count DESC 
    LIMIT 10
""")

for row in cursor.fetchall():
    supplier, count = row
    print(f"  {supplier}: {count:,}개")

# 전체 거래처 수
cursor.execute("SELECT COUNT(DISTINCT \"거래처명\") FROM ingredients")
supplier_count = cursor.fetchone()[0]
print(f"\n전체 거래처 수: {supplier_count}개")

conn.close()