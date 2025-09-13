#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def remove_gunwi_data():
    """추가된 군위고 데이터를 삭제합니다."""
    
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        print("=== 군위고 데이터 삭제 ===\n")
        
        # 먼저 군위고 데이터 확인
        cursor.execute("""
            SELECT id, location_name, meal_type, plan_name, selling_price
            FROM meal_pricing 
            WHERE location_name = '군위고'
        """)
        gunwi_records = cursor.fetchall()
        
        if gunwi_records:
            print(f"삭제할 군위고 데이터 {len(gunwi_records)}개:")
            for record in gunwi_records:
                print(f"  - ID {record[0]}: {record[1]} {record[2]} ({record[3]}) - {record[4]}원")
            
            # 군위고 데이터 삭제
            cursor.execute("""
                DELETE FROM meal_pricing 
                WHERE location_name = '군위고'
            """)
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            print(f"\n✅ {deleted_count}개의 군위고 데이터를 삭제했습니다.")
            
        else:
            print("삭제할 군위고 데이터가 없습니다.")
        
        # 삭제 후 전체 데이터 개수 확인
        cursor.execute("SELECT COUNT(*) FROM meal_pricing")
        total_count = cursor.fetchone()[0]
        
        print(f"현재 meal_pricing 테이블에 {total_count}개의 레코드가 있습니다.")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"데이터 삭제 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    remove_gunwi_data()