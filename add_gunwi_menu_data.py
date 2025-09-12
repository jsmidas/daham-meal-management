#!/usr/bin/env python3
"""
군위고 세부식단표 데이터를 추가하여 완전한 식단가 관리 데이터 구성
"""
import sqlite3
from datetime import datetime

def add_gunwi_menu_data():
    """군위고 세부식단표를 포함한 완전한 식단가 데이터 추가"""
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        print("=== 군위고 세부식단표 데이터 추가 ===")
        
        # 현재 meal_pricing 데이터 확인
        cursor.execute("SELECT COUNT(*) FROM meal_pricing")
        current_count = cursor.fetchone()[0]
        print(f"현재 식단가 데이터 개수: {current_count}")
        
        # 군위고 세부식단표 데이터 추가 (학교 사업장에서 군위고라는 세부식단표를 운영)
        gunwi_menu_data = [
            {
                'location_id': 1,  # business_locations의 '학교' ID
                'location_name': '학교',
                'meal_plan_type': '중식',
                'meal_type': '급식',
                'plan_name': '군위고',  # 세부식단표 이름
                'apply_date_start': '2025-08-11',
                'apply_date_end': '2025-12-31',
                'selling_price': 4500,
                'material_cost_guideline': 2250,
                'cost_ratio': 50.0,
                'is_active': True
            },
            {
                'location_id': 1,
                'location_name': '학교',
                'meal_plan_type': '석식',
                'meal_type': '급식',
                'plan_name': '군위고',
                'apply_date_start': '2025-08-11',
                'apply_date_end': '2025-12-31',
                'selling_price': 5000,
                'material_cost_guideline': 2500,
                'cost_ratio': 50.0,
                'is_active': True
            },
            # 저녁단과 세부식단표 추가 (도시락 사업장에서)
            {
                'location_id': 2,
                'location_name': '도시락',
                'meal_plan_type': '석식',
                'meal_type': '도시락',
                'plan_name': '저녁단과',
                'apply_date_start': '2025-08-11',
                'apply_date_end': '2025-12-31',
                'selling_price': 8000,
                'material_cost_guideline': 4000,
                'cost_ratio': 50.0,
                'is_active': True
            },
            # 아침단과 세부식단표 추가 (요양원 사업장에서)
            {
                'location_id': 4,
                'location_name': '요양원',
                'meal_plan_type': '조식',
                'meal_type': '케어',
                'plan_name': '아침단과',
                'apply_date_start': '2025-08-11',
                'apply_date_end': '2025-12-31',
                'selling_price': 4000,
                'material_cost_guideline': 2000,
                'cost_ratio': 50.0,
                'is_active': True
            }
        ]
        
        # 데이터베이스에 삽입
        insert_query = """
        INSERT INTO meal_pricing (
            location_id, location_name, meal_plan_type, meal_type, plan_name,
            apply_date_start, apply_date_end, selling_price, material_cost_guideline,
            cost_ratio, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        current_time = datetime.now().isoformat()
        
        for data in gunwi_menu_data:
            cursor.execute(insert_query, (
                data['location_id'],
                data['location_name'],
                data['meal_plan_type'],
                data['meal_type'],
                data['plan_name'],
                data['apply_date_start'],
                data['apply_date_end'],
                data['selling_price'],
                data['material_cost_guideline'],
                data['cost_ratio'],
                data['is_active'],
                current_time,
                current_time
            ))
        
        conn.commit()
        print(f"세부식단표 데이터 {len(gunwi_menu_data)}개 추가 완료")
        
        # 결과 확인
        cursor.execute("""
            SELECT id, location_name, plan_name, meal_plan_type, meal_type, selling_price
            FROM meal_pricing 
            ORDER BY location_name, plan_name, meal_plan_type
        """)
        results = cursor.fetchall()
        
        print(f"\n=== 전체 식단가 데이터 ({len(results)}개) ===")
        for result in results:
            print(f"ID {result[0]}: {result[1]} - '{result[2]}' ({result[3]}/{result[4]}) - {result[5]:,}원")
        
        # 사업장별로 그룹화해서 보기
        print(f"\n=== 사업장별 세부식단표 현황 ===")
        cursor.execute("""
            SELECT location_name, plan_name, COUNT(*) as plan_count
            FROM meal_pricing 
            GROUP BY location_name, plan_name
            ORDER BY location_name, plan_name
        """)
        grouped_results = cursor.fetchall()
        
        current_location = None
        for result in grouped_results:
            location, plan, count = result
            if location != current_location:
                print(f"\n📍 {location}:")
                current_location = location
            print(f"  - {plan}: {count}개 식단")
        
        conn.close()
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    add_gunwi_menu_data()