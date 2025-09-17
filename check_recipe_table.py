import sqlite3
import os

# 데이터베이스 경로
db_paths = [
    'backups/daham_meal.db',
    'daham_meal.db',
    os.getenv("DAHAM_DB_PATH", "daham_meal.db")
]

for db_path in db_paths:
    if os.path.exists(db_path):
        print(f"\n=== {db_path} ===")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # recipes 테이블 구조 확인
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='recipes'")
        result = cursor.fetchone()

        if result:
            print("recipes 테이블 구조:")
            print(result[0])
        else:
            print("recipes 테이블이 없습니다.")

        conn.close()
        break
else:
    print("데이터베이스 파일을 찾을 수 없습니다.")