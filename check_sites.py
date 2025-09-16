import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('daham_meal.db')
cursor = conn.cursor()

print("=== 현재 business_locations 테이블 상태 ===")

# 테이블 구조 확인
cursor.execute("PRAGMA table_info(business_locations)")
columns = cursor.fetchall()
print("\n테이블 구조:")
for col in columns:
    print(f"  {col[1]:20} : {col[2]}")

# 현재 데이터 확인
cursor.execute("SELECT * FROM business_locations ORDER BY id")
rows = cursor.fetchall()

print(f"\n총 {len(rows)}개의 사업장:")
print("-" * 50)

if rows:
    # 컬럼명 가져오기
    col_names = [description[0] for description in cursor.description]

    for row in rows:
        print(f"\n사업장 ID {row[0]}:")
        for i, col_name in enumerate(col_names):
            if row[i] is not None:
                print(f"  {col_name:20} : {row[i]}")

    # 간단한 목록
    print("\n" + "=" * 50)
    print("사업장 목록 요약:")
    print("-" * 50)
    cursor.execute("SELECT id, site_code, site_name FROM business_locations ORDER BY id")
    for row in cursor.fetchall():
        print(f"  ID {row[0]:3} | Code: {row[1]:10} | Name: {row[2]}")
else:
    print("등록된 사업장이 없습니다.")

print("\n예상 사업장 목록:")
expected = ["도시락", "운반", "학교", "요양원", "영남 도시락", "영남 운반"]
print(f"  예상: {expected}")
print(f"  예상 개수: {len(expected)}개")
print(f"  실제 개수: {len(rows)}개")

if len(rows) < len(expected):
    print(f"\n⚠️ {len(expected) - len(rows)}개 사업장이 누락되었습니다!")

conn.close()