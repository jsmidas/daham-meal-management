#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime

def fix_meal_pricing_locations():
    """meal_pricing 테이블의 사업장 참조를 올바르게 수정합니다."""
    
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        print("=== meal_pricing 사업장 참조 수정 ===\n")
        
        # 현재 잘못된 데이터 확인
        cursor.execute("""
            SELECT id, location_id, location_name, plan_name, meal_type
            FROM meal_pricing 
            WHERE location_id = 7
            ORDER BY id
        """)
        wrong_data = cursor.fetchall()
        
        print(f"수정할 군위고 데이터 {len(wrong_data)}개:")
        for row in wrong_data:
            print(f"  ID {row[0]}: location_id={row[1]}, location_name='{row[2]}', plan_name='{row[3]}', meal_type='{row[4]}'")
        print()
        
        # 1. location_id=7 (customers의 군위고)를 location_id=1 (business_locations의 학교)로 변경
        # 2. location_name을 "군위고"에서 "학교"로 변경 
        # 3. plan_name을 "군위고"로 설정 (세부식단표 명)
        
        update_sql = """
            UPDATE meal_pricing 
            SET location_id = 1,
                location_name = '학교',
                plan_name = '군위고'
            WHERE location_id = 7
        """
        
        cursor.execute(update_sql)
        updated_count = cursor.rowcount
        
        conn.commit()
        print(f"✅ {updated_count}개의 레코드를 수정했습니다.")
        
        # 수정된 데이터 확인
        cursor.execute("""
            SELECT id, location_id, location_name, plan_name, meal_type, selling_price
            FROM meal_pricing 
            WHERE location_id = 1 AND plan_name = '군위고'
            ORDER BY meal_type
        """)
        fixed_data = cursor.fetchall()
        
        print(f"\n수정된 데이터 ({len(fixed_data)}개):")
        for row in fixed_data:
            print(f"  ID {row[0]}: 사업장='{row[2]}' (ID:{row[1]}), 세부식단표='{row[3]}', 식사='{row[4]}', 가격={row[5]:,}원")
        
        # business_locations와 올바르게 연결되었는지 확인
        print(f"\n=== 사업장관리(business_locations) 연결 확인 ===")
        cursor.execute("""
            SELECT bl.id, bl.site_name, bl.site_type, COUNT(mp.id) as meal_pricing_count
            FROM business_locations bl
            LEFT JOIN meal_pricing mp ON bl.id = mp.location_id
            GROUP BY bl.id, bl.site_name, bl.site_type
            ORDER BY bl.id
        """)
        connection_check = cursor.fetchall()
        
        for row in connection_check:
            print(f"  사업장 ID {row[0]}: {row[1]} ({row[2]}) - 식단가 {row[3]}개")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"수정 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    fix_meal_pricing_locations()