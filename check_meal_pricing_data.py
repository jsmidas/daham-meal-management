#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def check_meal_pricing_data():
    """meal_pricing 테이블의 모든 데이터를 확인합니다."""
    
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        print("=== meal_pricing 테이블 전체 데이터 ===\n")
        
        cursor.execute("""
            SELECT id, location_id, location_name, meal_plan_type, meal_type, 
                   plan_name, apply_date_start, apply_date_end, selling_price,
                   material_cost_guideline, is_active
            FROM meal_pricing 
            ORDER BY location_name, meal_type
        """)
        meal_pricing = cursor.fetchall()
        
        if meal_pricing:
            print(f"총 {len(meal_pricing)}개의 meal_pricing 레코드:")
            print()
            for i, pricing in enumerate(meal_pricing, 1):
                print(f"{i}. ID: {pricing[0]}")
                print(f"   장소ID: {pricing[1]}")
                print(f"   장소명: {pricing[2]}")
                print(f"   식단계획타입: {pricing[3]}")
                print(f"   식사타입: {pricing[4]}")
                print(f"   플랜명: {pricing[5]}")
                print(f"   시작일: {pricing[6]}")
                print(f"   종료일: {pricing[7]}")
                print(f"   판매가: {pricing[8]}")
                print(f"   재료비가이드: {pricing[9]}")
                print(f"   활성상태: {pricing[10]}")
                print()
        else:
            print("meal_pricing 테이블에 데이터가 없습니다.")
        
        # business_locations 테이블도 확인
        print("=== business_locations 테이블 전체 데이터 ===\n")
        
        cursor.execute("""
            SELECT id, site_code, site_name, site_type, region,
                   address, phone, manager_name, is_active
            FROM business_locations 
            ORDER BY site_name
        """)
        locations = cursor.fetchall()
        
        if locations:
            print(f"총 {len(locations)}개의 business_locations 레코드:")
            print()
            for i, location in enumerate(locations, 1):
                print(f"{i}. ID: {location[0]}")
                print(f"   사이트코드: {location[1]}")
                print(f"   사이트명: {location[2]}")
                print(f"   사이트타입: {location[3]}")
                print(f"   지역: {location[4]}")
                print(f"   주소: {location[5]}")
                print(f"   전화: {location[6]}")
                print(f"   관리자: {location[7]}")
                print(f"   활성상태: {location[8]}")
                print()
        else:
            print("business_locations 테이블에 데이터가 없습니다.")
        
        # customers 테이블도 확인
        print("=== customers 테이블 전체 데이터 ===\n")
        
        cursor.execute("""
            SELECT id, code, name, site_type, contact_person,
                   contact_phone, address, is_active
            FROM customers 
            ORDER BY name
        """)
        customers = cursor.fetchall()
        
        if customers:
            print(f"총 {len(customers)}개의 customers 레코드:")
            print()
            for i, customer in enumerate(customers, 1):
                print(f"{i}. ID: {customer[0]}")
                print(f"   코드: {customer[1]}")
                print(f"   이름: {customer[2]}")
                print(f"   사이트타입: {customer[3]}")
                print(f"   담당자: {customer[4]}")
                print(f"   연락처: {customer[5]}")
                print(f"   주소: {customer[6]}")
                print(f"   활성상태: {customer[7]}")
                print()
        else:
            print("customers 테이블에 데이터가 없습니다.")
            
        conn.close()
        
    except Exception as e:
        print(f"데이터 확인 중 오류 발생: {e}")

if __name__ == "__main__":
    check_meal_pricing_data()