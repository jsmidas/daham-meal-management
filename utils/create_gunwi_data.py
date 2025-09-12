#!/usr/bin/env python3
"""
군위고 식단가 데이터 생성 스크립트
"""
from sqlalchemy.orm import sessionmaker
from app.database import engine
from models import MealPricing
from datetime import datetime, date

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    # 군위고 식단가 데이터 생성
    gunwi_data = [
        {
            "location_id": 4,
            "location_name": "군위고",
            "meal_plan_type": "일반식단",
            "meal_type": "breakfast",
            "plan_name": "아침식단",
            "selling_price": 4500,
            "material_cost_guideline": 3150,  # 70%
            "apply_date_start": date(2024, 1, 1)
        },
        {
            "location_id": 4,
            "location_name": "군위고",
            "meal_plan_type": "일반식단",
            "meal_type": "lunch",
            "plan_name": "점심식단",
            "selling_price": 5500,
            "material_cost_guideline": 3850,  # 70%
            "apply_date_start": date(2024, 1, 1)
        },
        {
            "location_id": 4,
            "location_name": "군위고",
            "meal_plan_type": "일반식단",
            "meal_type": "dinner",
            "plan_name": "저녁식단",
            "selling_price": 5000,
            "material_cost_guideline": 3500,  # 70%
            "apply_date_start": date(2024, 1, 1)
        },
        {
            "location_id": 4,
            "location_name": "군위고",
            "meal_plan_type": "특식",
            "meal_type": "lunch",
            "plan_name": "특별식단",
            "selling_price": 6500,
            "material_cost_guideline": 4550,  # 70%
            "apply_date_start": date(2024, 1, 1)
        }
    ]
    
    # 기존 군위고 데이터 삭제
    db.query(MealPricing).filter(MealPricing.location_name == "군위고").delete()
    
    # 새 데이터 추가
    for data in gunwi_data:
        meal_pricing = MealPricing(
            location_id=data["location_id"],
            location_name=data["location_name"],
            meal_plan_type=data["meal_plan_type"],
            meal_type=data["meal_type"],
            plan_name=data["plan_name"],
            selling_price=data["selling_price"],
            material_cost_guideline=data["material_cost_guideline"],
            apply_date_start=data["apply_date_start"],
            created_at=datetime.now()
        )
        db.add(meal_pricing)
    
    db.commit()
    print(f"군위고 식단가 데이터 {len(gunwi_data)}개를 생성했습니다.")
    
    # 생성된 데이터 확인
    rows = db.query(MealPricing).filter(MealPricing.location_name == "군위고").all()
    for row in rows:
        percentage = (row.material_cost_guideline / row.selling_price * 100) if row.selling_price > 0 else 0
        print(f"사업장: {row.location_name}, 식사시간: {row.meal_type}, 세부식단표: {row.plan_name}, "
              f"판매가: {row.selling_price:,}원, 목표식재료비: {row.material_cost_guideline:,}원, "
              f"비율: {percentage:.1f}%")
        
finally:
    db.close()