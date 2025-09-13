#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def check_table_schema(db_path, table_name):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 스키마 확인
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print(f"\n=== {table_name} 테이블 스키마 ===")
        for col in columns:
            print(f"{col[1]} ({col[2]}) - NULL: {bool(col[3])}")
        
        # 샘플 데이터 몇 개 확인
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        rows = cursor.fetchall()
        
        print(f"\n=== {table_name} 샘플 데이터 ===")
        for i, row in enumerate(rows):
            print(f"Row {i+1}: {row}")
            
        conn.close()
        
    except Exception as e:
        print(f"{table_name} 테이블 확인 실패: {e}")

# 주요 테이블들 확인
db_path = "backups/working_state_20250912/daham_meal.db"
tables = ['users', 'business_locations', 'ingredients', 'suppliers']

for table in tables:
    check_table_schema(db_path, table)