import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('daham_meal.db')
cursor = conn.cursor()

# 현재 데이터 확인
cursor.execute("SELECT COUNT(*) FROM business_locations")
count = cursor.fetchone()[0]
print(f"현재 business_locations 테이블에 {count}개의 레코드가 있습니다.")

if count > 0:
    cursor.execute("SELECT id, site_code, site_name FROM business_locations")
    print("\n현재 데이터:")
    for row in cursor.fetchall():
        print(f"  ID: {row[0]}, Code: {row[1]}, Name: {row[2]}")

# 모든 데이터 삭제
cursor.execute("DELETE FROM business_locations")
conn.commit()

# 삭제 확인
cursor.execute("SELECT COUNT(*) FROM business_locations")
new_count = cursor.fetchone()[0]
print(f"\n삭제 완료! 현재 레코드 수: {new_count}")

conn.close()
print("\n사업장 테이블이 초기화되었습니다. 이제 새로 추가할 수 있습니다.")