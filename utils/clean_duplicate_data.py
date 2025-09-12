#!/usr/bin/env python3
"""
중복 식단가 데이터 정리 스크립트
"""
from sqlalchemy.orm import sessionmaker
from app.database import engine
from models import MealPricing
from datetime import datetime

# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    print("=== location_id=3 (학교) 중복 데이터 정리 ===")
    
    # location_id=3인 모든 데이터 조회
    school_pricings = db.query(MealPricing).filter(MealPricing.location_id == 3).order_by(MealPricing.id.desc()).all()
    print(f"정리 전: {len(school_pricings)}개")
    
    # 각 meal_type별로 최신 1개씩만 남기고 나머지 삭제
    meal_types_to_keep = {}
    
    for pricing in school_pricings:
        meal_type = pricing.meal_type
        if meal_type not in meal_types_to_keep:
            # 최신 데이터 보존
            meal_types_to_keep[meal_type] = pricing
            print(f"보존: ID:{pricing.id} | {meal_type} | {pricing.plan_name} | {pricing.selling_price}원")
        else:
            # 중복 데이터 삭제
            print(f"삭제: ID:{pricing.id} | {meal_type} | {pricing.plan_name} | {pricing.selling_price}원")
            db.delete(pricing)
    
    db.commit()
    
    # 정리 후 상태 확인
    remaining = db.query(MealPricing).filter(MealPricing.location_id == 3).all()
    print(f"\n정리 후: {len(remaining)}개")
    for pricing in remaining:
        print(f"남은 데이터: ID:{pricing.id} | {pricing.meal_type} | {pricing.plan_name} | {pricing.selling_price}원")
        
finally:
    db.close()