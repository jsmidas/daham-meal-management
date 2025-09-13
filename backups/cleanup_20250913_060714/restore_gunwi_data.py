#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
from datetime import datetime, date

def restore_gunwi_data():
    """군위고 식단가 데이터를 복원합니다."""
    
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        print("=== 군위고 식단가 데이터 복원 ===\n")
        
        # 먼저 기존 군위고 데이터 확인
        cursor.execute("""
            SELECT COUNT(*) FROM meal_pricing 
            WHERE location_name = '군위고'
        """)
        existing_count = cursor.fetchone()[0]
        print(f"기존 군위고 데이터: {existing_count}개")
        
        # 기존 데이터 삭제
        if existing_count > 0:
            cursor.execute("""
                DELETE FROM meal_pricing 
                WHERE location_name = '군위고'
            """)
            print(f"기존 {existing_count}개 데이터를 삭제했습니다.")
        
        # 군위고 식단가 데이터 정의
        gunwi_data = [
            {
                "location_id": 4,
                "location_name": "군위고",
                "meal_plan_type": "일반식단",
                "meal_type": "breakfast",
                "plan_name": "아침식단",
                "selling_price": 4500,
                "material_cost_guideline": 3150,  # 70%
                "apply_date_start": "2024-01-01"
            },
            {
                "location_id": 4,
                "location_name": "군위고",
                "meal_plan_type": "일반식단",
                "meal_type": "lunch",
                "plan_name": "점심식단",
                "selling_price": 5500,
                "material_cost_guideline": 3850,  # 70%
                "apply_date_start": "2024-01-01"
            },
            {
                "location_id": 4,
                "location_name": "군위고",
                "meal_plan_type": "일반식단",
                "meal_type": "dinner",
                "plan_name": "저녁식단",
                "selling_price": 5000,
                "material_cost_guideline": 3500,  # 70%
                "apply_date_start": "2024-01-01"
            },
            {
                "location_id": 4,
                "location_name": "군위고",
                "meal_plan_type": "특식",
                "meal_type": "lunch",
                "plan_name": "특별식단",
                "selling_price": 6500,
                "material_cost_guideline": 4550,  # 70%
                "apply_date_start": "2024-01-01"
            }
        ]
        
        # 새 데이터 삽입
        for data in gunwi_data:
            cursor.execute("""
                INSERT INTO meal_pricing (
                    location_id, location_name, meal_plan_type, meal_type,
                    plan_name, selling_price, material_cost_guideline,
                    apply_date_start, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["location_id"],
                data["location_name"], 
                data["meal_plan_type"],
                data["meal_type"],
                data["plan_name"],
                data["selling_price"],
                data["material_cost_guideline"],
                data["apply_date_start"],
                1,  # is_active
                datetime.now().isoformat()
            ))
        
        conn.commit()
        print(f"군위고 식단가 데이터 {len(gunwi_data)}개를 생성했습니다.")
        
        # 생성된 데이터 확인
        cursor.execute("""
            SELECT id, location_name, meal_type, plan_name, selling_price, 
                   material_cost_guideline, apply_date_start
            FROM meal_pricing 
            WHERE location_name = '군위고'
            ORDER BY meal_type, plan_name
        """)
        
        rows = cursor.fetchall()
        print(f"\n=== 생성된 군위고 식단가 데이터 ({len(rows)}개) ===")
        
        for row in rows:
            percentage = (row[5] / row[4] * 100) if row[4] > 0 else 0
            print(f"ID {row[0]}: {row[1]} - {row[2]} ({row[3]})")
            print(f"  판매가: {row[4]:,}원, 목표식재료비: {row[5]:,}원 ({percentage:.1f}%)")
            print(f"  적용일: {row[6]}")
            print()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"데이터 복원 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    restore_gunwi_data()