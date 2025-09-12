#!/usr/bin/env python3
"""
세부식단표에서 군위고 데이터 확인
"""
import sqlite3

def check_detailed_menus():
    """세부식단표 데이터 확인"""
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        # 세부식단표 테이블 확인
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%menu%'
        """)
        menu_tables = cursor.fetchall()
        print("메뉴 관련 테이블들:", [table[0] for table in menu_tables])
        
        # menus 테이블에서 군위고 검색
        try:
            cursor.execute("SELECT * FROM menus WHERE name LIKE '%군위%' OR description LIKE '%군위%'")
            gunwi_menus = cursor.fetchall()
            
            if gunwi_menus:
                print(f"\n군위 관련 메뉴 ({len(gunwi_menus)}개):")
                for menu in gunwi_menus:
                    print(f"  {menu}")
            else:
                print("\nmenus 테이블에서 군위 관련 데이터 없음")
                
            # 모든 메뉴 조회 (최대 10개)
            cursor.execute("SELECT * FROM menus LIMIT 10")
            all_menus = cursor.fetchall()
            
            print(f"\n전체 메뉴 ({len(all_menus)}개):")
            for menu in all_menus:
                print(f"  {menu}")
                
        except sqlite3.Error as e:
            print(f"menus 테이블 오류: {e}")
            
        # customer_menus 테이블에서 군위고 검색
        try:
            cursor.execute("SELECT * FROM customer_menus LIMIT 10")
            customer_menus = cursor.fetchall()
            
            print(f"\ncustomer_menus 테이블 ({len(customer_menus)}개):")
            for menu in customer_menus:
                print(f"  {menu}")
                
        except sqlite3.Error as e:
            print(f"customer_menus 테이블 오류: {e}")
            
        # menu_items 테이블에서도 확인
        try:
            cursor.execute("SELECT * FROM menu_items WHERE name LIKE '%군위%' LIMIT 10")
            gunwi_items = cursor.fetchall()
            
            if gunwi_items:
                print(f"\n군위 관련 메뉴 아이템 ({len(gunwi_items)}개):")
                for item in gunwi_items:
                    print(f"  {item}")
            else:
                print("\nmenu_items 테이블에서 군위 관련 데이터 없음")
                
        except sqlite3.Error as e:
            print(f"menu_items 테이블 오류: {e}")
            
        conn.close()
        
    except sqlite3.Error as e:
        print(f"데이터베이스 연결 오류: {e}")

if __name__ == "__main__":
    check_detailed_menus()