#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def check_database_schema():
    """데이터베이스 테이블 스키마를 확인합니다."""
    
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        # 모든 테이블 목록 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("=== 데이터베이스 테이블 목록 ===")
        for table in tables:
            print(f"- {table[0]}")
        print()
        
        # 각 테이블의 스키마 조회
        for table in tables:
            table_name = table[0]
            print(f"=== {table_name} 테이블 스키마 ===")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            for column in columns:
                print(f"  {column[1]} ({column[2]}) - {'NOT NULL' if column[3] else 'NULL'}")
            
            # 테이블의 데이터 개수 조회
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"  총 {count}개의 레코드")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"스키마 확인 중 오류 발생: {e}")

if __name__ == "__main__":
    check_database_schema()