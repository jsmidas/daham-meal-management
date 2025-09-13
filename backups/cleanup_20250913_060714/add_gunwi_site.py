#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime

def add_gunwi_site():
    """군위고 사업장을 customers 테이블에 추가합니다."""
    
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        print("=== 군위고 사업장 추가 ===\n")
        
        # 먼저 군위고가 이미 있는지 확인
        cursor.execute("""
            SELECT id, name FROM customers 
            WHERE name = '군위고'
        """)
        existing = cursor.fetchone()
        
        if existing:
            print(f"군위고 사업장이 이미 존재합니다: ID {existing[0]}")
            return existing[0]
        
        # 새로운 ID 확인 (현재 최대 ID + 1)
        cursor.execute("SELECT MAX(id) FROM customers")
        max_id = cursor.fetchone()[0] or 0
        new_id = max_id + 1
        
        # 군위고 사업장 추가
        cursor.execute("""
            INSERT INTO customers (
                id, name, site_type, contact_person, contact_phone, 
                address, description, is_active, created_at, 
                parent_id, level, sort_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_id,
            '군위고',
            '학교',
            '관리자',
            '010-0000-0000',
            '경북 군위군',
            '군위고등학교',
            True,  # is_active
            datetime.now().isoformat(),
            None,  # parent_id
            1,     # level
            0      # sort_order
        ))
        
        conn.commit()
        
        print(f"✅ 군위고 사업장을 추가했습니다 (ID: {new_id})")
        
        # 추가된 데이터 확인
        cursor.execute("""
            SELECT id, name, site_type, contact_person, contact_phone, address
            FROM customers WHERE id = ?
        """, (new_id,))
        
        result = cursor.fetchone()
        if result:
            print("\n추가된 사업장 정보:")
            print(f"  ID: {result[0]}")
            print(f"  이름: {result[1]}")
            print(f"  타입: {result[2]}")
            print(f"  담당자: {result[3]}")
            print(f"  연락처: {result[4]}")
            print(f"  주소: {result[5]}")
        
        conn.close()
        return new_id
        
    except Exception as e:
        print(f"사업장 추가 중 오류 발생: {e}")
        return None

if __name__ == "__main__":
    add_gunwi_site()