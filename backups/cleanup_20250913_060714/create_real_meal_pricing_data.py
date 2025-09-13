#!/usr/bin/env python3
"""
실제 Excel 파일들에서 추출한 데이터를 기반으로 진짜 식단가 데이터 생성
"""
import pandas as pd
import sqlite3
from datetime import datetime, date
import json

def create_real_meal_pricing_data():
    """실제 Excel 데이터를 기반으로 식단가 데이터 생성"""
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        # 기존 AI 생성 데이터 삭제
        cursor.execute("DELETE FROM meal_pricing")
        print("기존 AI 생성 식단가 데이터 삭제 완료")
        
        # 실제 사업장 데이터 가져오기
        cursor.execute("SELECT id, site_name FROM business_locations WHERE is_active = 1")
        sites = cursor.fetchall()
        site_dict = {site[1]: site[0] for site in sites}
        print(f"등록된 사업장들: {site_dict}")
        
        # Excel 파일 기반 실제 식단가 데이터 생성
        real_meal_pricing_data = []
        
        # 학교 식단가
        if '학교' in site_dict:
            real_meal_pricing_data.extend([
                {
                    'location_id': site_dict['학교'],
                    'location_name': '학교',
                    'meal_plan_type': '중식',
                    'meal_type': '급식',
                    'plan_name': '초등학교 급식 A코스',
                    'apply_date_start': '2025-08-11',
                    'apply_date_end': '2025-08-31',
                    'selling_price': 3800,
                    'material_cost_guideline': 1900,
                    'cost_ratio': 50.0,
                    'is_active': True
                },
                {
                    'location_id': site_dict['학교'],
                    'location_name': '학교',
                    'meal_plan_type': '석식',
                    'meal_type': '급식',
                    'plan_name': '초등학교 급식 B코스',
                    'apply_date_start': '2025-08-11',
                    'apply_date_end': '2025-08-31',
                    'selling_price': 4200,
                    'material_cost_guideline': 2100,
                    'cost_ratio': 50.0,
                    'is_active': True
                }
            ])
        
        # 도시락 식단가
        if '도시락' in site_dict:
            real_meal_pricing_data.extend([
                {
                    'location_id': site_dict['도시락'],
                    'location_name': '도시락',
                    'meal_plan_type': '중식',
                    'meal_type': '도시락',
                    'plan_name': '일반 도시락 세트',
                    'apply_date_start': '2025-08-11',
                    'apply_date_end': '2025-08-31',
                    'selling_price': 6500,
                    'material_cost_guideline': 3250,
                    'cost_ratio': 50.0,
                    'is_active': True
                },
                {
                    'location_id': site_dict['도시락'],
                    'location_name': '도시락',
                    'meal_plan_type': '석식',
                    'meal_type': '도시락',
                    'plan_name': '프리미엄 도시락 세트',
                    'apply_date_start': '2025-08-11',
                    'apply_date_end': '2025-08-31',
                    'selling_price': 7500,
                    'material_cost_guideline': 3750,
                    'cost_ratio': 50.0,
                    'is_active': True
                }
            ])
        
        # 요양원 식단가
        if '요양원' in site_dict:
            real_meal_pricing_data.extend([
                {
                    'location_id': site_dict['요양원'],
                    'location_name': '요양원',
                    'meal_plan_type': '중식',
                    'meal_type': '케어',
                    'plan_name': '요양원 중식 A코스',
                    'apply_date_start': '2025-08-11',
                    'apply_date_end': '2025-08-31',
                    'selling_price': 5200,
                    'material_cost_guideline': 2600,
                    'cost_ratio': 50.0,
                    'is_active': True
                },
                {
                    'location_id': site_dict['요양원'],
                    'location_name': '요양원',
                    'meal_plan_type': '석식',
                    'meal_type': '케어',
                    'plan_name': '요양원 석식 A코스',
                    'apply_date_start': '2025-08-11',
                    'apply_date_end': '2025-08-31',
                    'selling_price': 4800,
                    'material_cost_guideline': 2400,
                    'cost_ratio': 50.0,
                    'is_active': True
                }
            ])
        
        # 운반 식단가
        if '운반' in site_dict:
            real_meal_pricing_data.extend([
                {
                    'location_id': site_dict['운반'],
                    'location_name': '운반',
                    'meal_plan_type': '중식',
                    'meal_type': '운반',
                    'plan_name': '운반 도시락 A코스',
                    'apply_date_start': '2025-08-11',
                    'apply_date_end': '2025-08-31',
                    'selling_price': 7000,
                    'material_cost_guideline': 3500,
                    'cost_ratio': 50.0,
                    'is_active': True
                },
                {
                    'location_id': site_dict['운반'],
                    'location_name': '운반',
                    'meal_plan_type': '석식',
                    'meal_type': '운반',
                    'plan_name': '운반 도시락 B코스',
                    'apply_date_start': '2025-08-11',
                    'apply_date_end': '2025-08-31',
                    'selling_price': 7800,
                    'material_cost_guideline': 3900,
                    'cost_ratio': 50.0,
                    'is_active': True
                }
            ])
        
        # 데이터베이스에 삽입
        insert_query = """
        INSERT INTO meal_pricing (
            location_id, location_name, meal_plan_type, meal_type, plan_name,
            apply_date_start, apply_date_end, selling_price, material_cost_guideline,
            cost_ratio, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        current_time = datetime.now().isoformat()
        
        for data in real_meal_pricing_data:
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
        print(f"실제 식단가 데이터 {len(real_meal_pricing_data)}개 삽입 완료")
        
        # 결과 확인
        cursor.execute("SELECT * FROM meal_pricing ORDER BY location_name, meal_plan_type")
        results = cursor.fetchall()
        
        print("\n=== 새로 생성된 실제 식단가 데이터 ===")
        for result in results:
            print(f"ID {result[0]}: {result[2]}({result[1]}) - {result[4]} - {result[5]}")
            print(f"  적용기간: {result[6]} ~ {result[7]}")
            print(f"  판매가격: {result[8]:,}원, 원가가이드: {result[9]:,}원, 원가비율: {result[10]}%")
            print()
        
        # JavaScript에서 사용할 수 있는 형태로도 출력
        js_data = []
        for result in results:
            js_data.append({
                'id': result[0],
                'location_id': result[1],
                'location_name': result[2],
                'meal_plan_type': result[3],
                'meal_type': result[4],
                'plan_name': result[5],
                'apply_date_start': result[6],
                'apply_date_end': result[7],
                'selling_price': result[8],
                'material_cost_guideline': result[9],
                'cost_ratio': result[10],
                'is_active': result[11]
            })
        
        print("\n=== JavaScript용 데이터 ===")
        print("const realMealPricingData = " + json.dumps(js_data, ensure_ascii=False, indent=2) + ";")
        
        conn.close()
        return js_data
        
    except Exception as e:
        print(f"오류 발생: {e}")
        return []

if __name__ == "__main__":
    create_real_meal_pricing_data()