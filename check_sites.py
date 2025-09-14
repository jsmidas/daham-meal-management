import sqlite3

# 데이터베이스 연결
conn = sqlite3.connect('daham_meal.db')
cursor = conn.cursor()

print("=== 현재 business_locations 테이블 상태 ===")

# 현재 데이터 확인
cursor.execute("SELECT id, site_code, site_name FROM business_locations ORDER BY id")
rows = cursor.fetchall()

print(f"\n총 {len(rows)}개의 레코드:")
for row in rows:
    print(f"  ID: {row[0]}, Code: {row[1]}, Name: {row[2]}")

# site_code가 BIZ001인 레코드 확인
cursor.execute("SELECT * FROM business_locations WHERE site_code = 'BIZ001'")
biz001 = cursor.fetchone()

if biz001:
    print(f"\nBIZ001 레코드 발견:")
    print(f"  전체 데이터: {biz001}")

    # BIZ001 삭제
    cursor.execute("DELETE FROM business_locations WHERE site_code = 'BIZ001'")
    conn.commit()
    print("  -> BIZ001 삭제 완료")
else:
    print("\nBIZ001 레코드가 없습니다.")

# 모든 레코드 삭제 (완전 초기화)
cursor.execute("DELETE FROM business_locations")
conn.commit()
print("\n모든 사업장 데이터 삭제 완료")

# 최종 확인
cursor.execute("SELECT COUNT(*) FROM business_locations")
final_count = cursor.fetchone()[0]
print(f"최종 레코드 수: {final_count}")

conn.close()