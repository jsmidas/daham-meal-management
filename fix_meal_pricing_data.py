#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
식단가 테이블 데이터 재생성 스크립트
기존 corrupted 데이터를 삭제하고 올바른 한글 데이터로 재생성
"""

import sqlite3
from datetime import datetime

def recreate_meal_pricing_data():
    """식단가 데이터 재생성"""
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()

        # 기존 데이터 삭제
        print("기존 식단가 데이터 삭제 중...")
        cursor.execute("DELETE FROM meal_pricing")

        # 새로운 데이터 생성
        meal_pricing_data = [
            # 학교 급식
            (1, "학교", "점심", "급식", "학교 점심 급식", "2025-01-01", "2025-12-31", 5500, 2200, 40.0, 1),
            (2, "학교", "저녁", "급식", "학교 저녁 급식", "2025-01-01", "2025-12-31", 6000, 2400, 40.0, 1),

            # 도시락
            (3, "도시락", "점심", "도시락", "일반 도시락", "2025-01-01", "2025-12-31", 8000, 3200, 40.0, 1),
            (4, "도시락", "저녁", "도시락", "프리미엄 도시락", "2025-01-01", "2025-12-31", 10000, 4000, 40.0, 1),

            # 운반
            (5, "운반", "점심", "뷔페", "점심 뷔페", "2025-01-01", "2025-12-31", 12000, 4800, 40.0, 1),
            (6, "운반", "저녁", "뷔페", "저녁 뷔페", "2025-01-01", "2025-12-31", 15000, 6000, 40.0, 1),

            # 요양원
            (7, "요양원", "아침", "일반식", "요양원 아침식", "2025-01-01", "2025-12-31", 4000, 1600, 40.0, 1),
            (8, "요양원", "점심", "일반식", "요양원 점심식", "2025-01-01", "2025-12-31", 5000, 2000, 40.0, 1),
            (9, "요양원", "저녁", "일반식", "요양원 저녁식", "2025-01-01", "2025-12-31", 5000, 2000, 40.0, 1),
            (10, "요양원", "야식", "특별식", "요양원 야식", "2025-01-01", "2025-12-31", 3500, 1400, 40.0, 1),

            # 추가 테스트 데이터
            (11, "학교", "아침", "조식", "학교 조식", "2025-01-01", "2025-12-31", 4500, 1800, 40.0, 0),
            (12, "도시락", "아침", "간편식", "간편 도시락", "2025-01-01", "2025-12-31", 6000, 2400, 40.0, 0),
        ]

        print("새로운 식단가 데이터 생성 중...")
        for data in meal_pricing_data:
            cursor.execute("""
                INSERT INTO meal_pricing (
                    location_id, location_name, meal_plan_type, meal_type,
                    plan_name, apply_date_start, apply_date_end, selling_price,
                    material_cost_guideline, cost_ratio, is_active, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, data)

        conn.commit()

        # 생성된 데이터 확인
        cursor.execute("SELECT COUNT(*) FROM meal_pricing")
        count = cursor.fetchone()[0]
        print(f"총 {count}개의 식단가 데이터 생성 완료")

        # 샘플 데이터 출력
        cursor.execute("""
            SELECT location_name, meal_plan_type, meal_type, selling_price, material_cost_guideline
            FROM meal_pricing
            WHERE is_active = 1
            LIMIT 5
        """)

        print("\n생성된 데이터 샘플:")
        print("-" * 70)
        print(f"{'사업장':<10} {'식단종류':<10} {'식사시간':<10} {'판매가':>10} {'목표원가':>10}")
        print("-" * 70)

        for row in cursor.fetchall():
            print(f"{row[0]:<10} {row[1]:<10} {row[2]:<10} {row[3]:>10,} {row[4]:>10,}")

        conn.close()
        print("\n✅ 식단가 데이터 재생성 완료!")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    recreate_meal_pricing_data()