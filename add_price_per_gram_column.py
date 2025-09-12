#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def add_price_per_gram_column():
    """ingredients 테이블에 price_per_gram 컬럼을 추가합니다."""
    
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        # price_per_gram 컬럼이 이미 존재하는지 확인
        cursor.execute("PRAGMA table_info(ingredients)")
        columns = cursor.fetchall()
        
        column_names = [column[1] for column in columns]
        
        if 'price_per_gram' in column_names:
            print("price_per_gram 컬럼이 이미 존재합니다.")
            return True
        
        # price_per_gram 컬럼 추가
        cursor.execute("""
            ALTER TABLE ingredients 
            ADD COLUMN price_per_gram DECIMAL(8,4)
        """)
        
        conn.commit()
        print("ingredients 테이블에 price_per_gram 컬럼을 추가했습니다.")
        
        # 추가된 컬럼 확인
        cursor.execute("PRAGMA table_info(ingredients)")
        columns = cursor.fetchall()
        
        print("\n현재 ingredients 테이블 컬럼:")
        for column in columns:
            if column[1] == 'price_per_gram':
                print(f"  ✓ {column[1]} ({column[2]}) - {'NOT NULL' if column[3] else 'NULL'}")
            else:
                print(f"    {column[1]} ({column[2]}) - {'NOT NULL' if column[3] else 'NULL'}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"컬럼 추가 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    add_price_per_gram_column()