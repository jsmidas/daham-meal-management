import sqlite3
import json

# 데이터베이스 연결
conn = sqlite3.connect('daham_meal.db')
cursor = conn.cursor()

# 전체 식자재 개수 확인
cursor.execute("SELECT COUNT(*) FROM ingredients")
total_count = cursor.fetchone()[0]
print(f"전체 식자재 개수: {total_count:,}개")

# 거래처명 필드의 실제 값들 확인 (처음 10개)
print("\n거래처명 필드 샘플 데이터 (처음 10개):")
cursor.execute('SELECT "거래처명", "식자재명", "고유코드" FROM ingredients LIMIT 10')
for row in cursor.fetchall():
    supplier, name, code = row
    print(f"  거래처명: {supplier}, 식자재명: {name}, 코드: {code}")

# 거래처명 필드의 고유값 확인
cursor.execute('SELECT DISTINCT "거래처명" FROM ingredients LIMIT 20')
unique_suppliers = cursor.fetchall()
print(f"\n고유한 거래처명 값들 (최대 20개):")
for supplier in unique_suppliers:
    print(f"  - {supplier[0]}")

# 거래처명이 NULL이거나 빈 값인 개수
cursor.execute('SELECT COUNT(*) FROM ingredients WHERE "거래처명" IS NULL OR "거래처명" = ""')
empty_count = cursor.fetchone()[0]
print(f"\n거래처명이 비어있는 레코드: {empty_count:,}개")

# 거래처명이 "거래처명"인 개수
cursor.execute('SELECT COUNT(*) FROM ingredients WHERE "거래처명" = "거래처명"')
default_count = cursor.fetchone()[0]
print(f"거래처명이 '거래처명'인 레코드: {default_count:,}개")

# 거래처명이 "미지정"인 개수
cursor.execute('SELECT COUNT(*) FROM ingredients WHERE "거래처명" = "미지정"')
unassigned_count = cursor.fetchone()[0]
print(f"거래처명이 '미지정'인 레코드: {unassigned_count:,}개")

conn.close()