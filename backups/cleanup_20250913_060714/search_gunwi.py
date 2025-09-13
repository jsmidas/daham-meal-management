#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import sys

def search_gunwi_data():
    """군위고 관련 데이터를 모든 테이블에서 검색합니다."""
    
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        print("=== 군위고 검색 결과 ===\n")
        
        # 1. customers 테이블에서 검색
        print("1. customers 테이블:")
        cursor.execute("""
            SELECT id, code, name, site_type, contact_person, 
                   contact_phone, address, description
            FROM customers 
            WHERE name LIKE '%군위%' OR name LIKE '%Gunwi%'
        """)
        customers = cursor.fetchall()
        
        if customers:
            for customer in customers:
                print(f"  - ID: {customer[0]}")
                print(f"    코드: {customer[1]}")
                print(f"    이름: {customer[2]}")
                print(f"    사이트타입: {customer[3]}")
                print(f"    담당자: {customer[4]}")
                print(f"    연락처: {customer[5]}")
                print(f"    주소: {customer[6]}")
                print(f"    설명: {customer[7]}")
                print()
        else:
            print("  검색 결과 없음\n")
        
        # 2. business_locations 테이블에서 검색
        print("2. business_locations 테이블:")
        cursor.execute("""
            SELECT id, site_code, site_name, site_type, region,
                   address, phone, manager_name, manager_phone
            FROM business_locations 
            WHERE site_name LIKE '%군위%' OR site_name LIKE '%Gunwi%'
        """)
        locations = cursor.fetchall()
        
        if locations:
            for location in locations:
                print(f"  - ID: {location[0]}")
                print(f"    사이트코드: {location[1]}")
                print(f"    사이트명: {location[2]}")
                print(f"    사이트타입: {location[3]}")
                print(f"    지역: {location[4]}")
                print(f"    주소: {location[5]}")
                print(f"    전화: {location[6]}")
                print(f"    관리자: {location[7]}")
                print(f"    관리자전화: {location[8]}")
                print()
        else:
            print("  검색 결과 없음\n")
        
        # 3. meal_pricing 테이블에서 검색
        print("3. meal_pricing 테이블:")
        cursor.execute("""
            SELECT id, location_id, location_name, meal_plan_type, meal_type, 
                   plan_name, apply_date_start, apply_date_end, selling_price,
                   material_cost_guideline
            FROM meal_pricing 
            WHERE location_name LIKE '%군위%' OR location_name LIKE '%Gunwi%'
        """)
        meal_pricing = cursor.fetchall()
        
        if meal_pricing:
            for pricing in meal_pricing:
                print(f"  - ID: {pricing[0]}")
                print(f"    장소ID: {pricing[1]}")
                print(f"    장소명: {pricing[2]}")
                print(f"    식단계획타입: {pricing[3]}")
                print(f"    식사타입: {pricing[4]}")
                print(f"    플랜명: {pricing[5]}")
                print(f"    시작일: {pricing[6]}")
                print(f"    종료일: {pricing[7]}")
                print(f"    판매가: {pricing[8]}")
                print(f"    재료비가이드: {pricing[9]}")
                print()
        else:
            print("  검색 결과 없음\n")
        
        # 4. 모든 테이블에서 고등학교 관련 데이터 검색
        print("4. 고등학교 관련 데이터:")
        
        # customers에서 고등학교 검색
        cursor.execute("""
            SELECT id, code, name
            FROM customers 
            WHERE name LIKE '%고등학교%' OR name LIKE '%고%'
            ORDER BY name
        """)
        high_schools = cursor.fetchall()
        
        if high_schools:
            print("  customers 테이블의 고등학교:")
            for school in high_schools:
                print(f"    - ID {school[0]} ({school[1]}): {school[2]}")
            print()
        
        # business_locations에서 고등학교 검색
        cursor.execute("""
            SELECT id, site_code, site_name, site_type
            FROM business_locations 
            WHERE site_name LIKE '%고등학교%' OR site_name LIKE '%고%'
            ORDER BY site_name
        """)
        location_schools = cursor.fetchall()
        
        if location_schools:
            print("  business_locations 테이블의 고등학교:")
            for school in location_schools:
                print(f"    - ID {school[0]} ({school[1]}): {school[2]} [{school[3]}]")
            print()
        
        # meal_pricing에서 고등학교 검색
        cursor.execute("""
            SELECT DISTINCT location_name, location_id
            FROM meal_pricing 
            WHERE location_name LIKE '%고등학교%' OR location_name LIKE '%고%'
            ORDER BY location_name
        """)
        pricing_schools = cursor.fetchall()
        
        if pricing_schools:
            print("  meal_pricing 테이블의 고등학교:")
            for school in pricing_schools:
                print(f"    - {school[0]} (장소ID: {school[1]})")
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"검색 중 오류 발생: {e}")
        return False
    
    return True

if __name__ == "__main__":
    search_gunwi_data()