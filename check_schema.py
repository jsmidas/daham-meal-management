#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def check_schema():
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()

        # 테이블 구조 확인
        cursor.execute("PRAGMA table_info(menu_recipes)")
        columns = cursor.fetchall()

        print("=== menu_recipes 테이블 구조 ===")
        for col in columns:
            print(f"{col[1]} ({col[2]})")

        # 샘플 데이터 확인
        print("\n=== 샘플 데이터 ===")
        cursor.execute("SELECT * FROM menu_recipes LIMIT 3")
        rows = cursor.fetchall()

        for row in rows:
            print(row)

        conn.close()

    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    check_schema()