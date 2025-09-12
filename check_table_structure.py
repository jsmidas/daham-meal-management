#!/usr/bin/env python3
"""
메뉴 관련 테이블 구조 확인
"""
import sqlite3

def check_table_structure():
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        # 모든 테이블 목록
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"전체 테이블 ({len(tables)}개):", tables)
        
        # 각 메뉴 관련 테이블 구조 확인
        menu_tables = ['menus', 'menu_items', 'customer_menus']
        
        for table in menu_tables:
            if table in tables:
                print(f"\n=== {table} 테이블 구조 ===")
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"  {col[1]} ({col[2]})")
                
                # 데이터 개수 확인
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  데이터 개수: {count}")
                
                if count > 0:
                    # 샘플 데이터 확인 (최대 3개)
                    cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                    samples = cursor.fetchall()
                    print(f"  샘플 데이터:")
                    for i, sample in enumerate(samples, 1):
                        print(f"    {i}: {sample}")
        
        # meal_pricing 관련 테이블도 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%meal%'")
        meal_tables = [table[0] for table in cursor.fetchall()]
        print(f"\nmeal 관련 테이블들: {meal_tables}")
        
        for table in meal_tables:
            print(f"\n=== {table} 테이블 구조 ===")
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  데이터 개수: {count}")
            
            if count > 0 and count < 20:
                cursor.execute(f"SELECT * FROM {table} LIMIT 5")
                samples = cursor.fetchall()
                print(f"  샘플 데이터:")
                for i, sample in enumerate(samples, 1):
                    print(f"    {i}: {sample}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"데이터베이스 오류: {e}")

if __name__ == "__main__":
    check_table_structure()