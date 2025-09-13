import sqlite3
import json

# DB 연결
db_path = 'backups/working_state_20250912/daham_meal.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== 사용자 테이블 확인 ===")

# 테이블 목록 확인
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("\n테이블 목록:")
for table in tables:
    print(f"  - {table[0]}")

# users 테이블 스키마 확인
print("\n=== users 테이블 스키마 ===")
cursor.execute("PRAGMA table_info(users);")
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# 사용자 데이터 확인
print("\n=== 사용자 데이터 (상위 5개) ===")
cursor.execute("SELECT * FROM users LIMIT 5;")
users = cursor.fetchall()
for user in users:
    print(f"  ID: {user[0]}, Username: {user[1]}, Role: {user[3] if len(user) > 3 else 'N/A'}")

# 전체 사용자 수
cursor.execute("SELECT COUNT(*) FROM users;")
total = cursor.fetchone()[0]
print(f"\n총 사용자 수: {total}")

conn.close()