#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
샘플 메뉴/레시피 데이터 생성 스크립트
"""
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Recipe, Menu, DietPlan, MenuItem, Ingredient, RecipeIngredient
from datetime import datetime, date

DATABASE_PATH = "meal_management.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

def create_sample_menu_data():
    """샘플 메뉴/레시피 데이터 생성"""
    if not os.path.exists(DATABASE_PATH):
        print(f"[ERROR] 데이터베이스 파일을 찾을 수 없습니다: {DATABASE_PATH}")
        return False
    
    try:
        # 데이터베이스 연결
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print(f"[INFO] 데이터베이스 연결 성공: {DATABASE_URL}")
        
        # 기존 데이터 확인
        existing_recipes = session.query(Recipe).count()
        print(f"[INFO] 기존 레시피 수: {existing_recipes}")
        
        # 샘플 식재료 데이터
        sample_ingredients = [
            {"name": "쌀", "base_unit": "kg", "price": 3000},
            {"name": "돼지고기", "base_unit": "kg", "price": 15000},
            {"name": "닭고기", "base_unit": "kg", "price": 8000},
            {"name": "양파", "base_unit": "kg", "price": 2000},
            {"name": "당근", "base_unit": "kg", "price": 2500},
            {"name": "감자", "base_unit": "kg", "price": 1500},
            {"name": "배추", "base_unit": "kg", "price": 1800},
            {"name": "무", "base_unit": "kg", "price": 1200},
            {"name": "두부", "base_unit": "모", "price": 1500},
            {"name": "계란", "base_unit": "개", "price": 300},
        ]
        
        # 식재료 생성
        ingredient_ids = {}
        for ingredient_data in sample_ingredients:
            existing_ingredient = session.query(Ingredient).filter(Ingredient.name == ingredient_data['name']).first()
            if not existing_ingredient:
                new_ingredient = Ingredient(**ingredient_data)
                session.add(new_ingredient)
                session.flush()  # ID 생성을 위해 flush
                ingredient_ids[ingredient_data['name']] = new_ingredient.id
                print(f"[CREATE] 새 식재료 생성: {ingredient_data['name']}")
            else:
                ingredient_ids[ingredient_data['name']] = existing_ingredient.id
                print(f"[EXISTS] 기존 식재료 사용: {ingredient_data['name']}")
        
        # 샘플 레시피 데이터
        sample_recipes = [
            {
                "name": "김치찌개",
                "version": "v1.0",
                "effective_date": date.today(),
                "notes": "매콤하고 시원한 김치찌개",
                "nutrition_data": {
                    "calories": 180,
                    "protein": 12.5,
                    "carbohydrates": 8.3,
                    "fat": 11.2,
                    "sodium": 850
                },
                "evaluation_score": 85,
                "ingredients": [
                    {"name": "돼지고기", "quantity": 0.08, "unit": "kg"},  # 80g per person
                    {"name": "배추", "quantity": 0.15, "unit": "kg"},    # 150g per person
                    {"name": "양파", "quantity": 0.05, "unit": "kg"},    # 50g per person
                    {"name": "두부", "quantity": 0.3, "unit": "모"}      # 0.3모 per person
                ]
            },
            {
                "name": "불고기",
                "version": "v1.0",
                "effective_date": date.today(),
                "notes": "달콤한 간장 양념의 불고기",
                "nutrition_data": {
                    "calories": 250,
                    "protein": 20.8,
                    "carbohydrates": 12.5,
                    "fat": 13.7,
                    "sodium": 920
                },
                "evaluation_score": 92,
                "ingredients": [
                    {"name": "돼지고기", "quantity": 0.12, "unit": "kg"},  # 120g per person
                    {"name": "양파", "quantity": 0.08, "unit": "kg"},     # 80g per person
                    {"name": "당근", "quantity": 0.04, "unit": "kg"}      # 40g per person
                ]
            },
            {
                "name": "된장찌개", 
                "version": "v1.0",
                "effective_date": date.today(),
                "notes": "구수한 된장찌개",
                "nutrition_data": {
                    "calories": 160,
                    "protein": 10.2,
                    "carbohydrates": 9.8,
                    "fat": 8.5,
                    "sodium": 780
                },
                "evaluation_score": 88,
                "ingredients": [
                    {"name": "두부", "quantity": 0.4, "unit": "모"},      # 0.4모 per person
                    {"name": "무", "quantity": 0.1, "unit": "kg"},       # 100g per person
                    {"name": "양파", "quantity": 0.03, "unit": "kg"}     # 30g per person
                ]
            },
            {
                "name": "닭볶음탕",
                "version": "v1.0", 
                "effective_date": date.today(),
                "notes": "매콤한 닭볶음탕",
                "nutrition_data": {
                    "calories": 280,
                    "protein": 25.3,
                    "carbohydrates": 15.2,
                    "fat": 14.8,
                    "sodium": 950
                },
                "evaluation_score": 90,
                "ingredients": [
                    {"name": "닭고기", "quantity": 0.15, "unit": "kg"},   # 150g per person
                    {"name": "감자", "quantity": 0.1, "unit": "kg"},     # 100g per person
                    {"name": "당근", "quantity": 0.05, "unit": "kg"},    # 50g per person
                    {"name": "양파", "quantity": 0.06, "unit": "kg"}     # 60g per person
                ]
            },
            {
                "name": "계란찜",
                "version": "v1.0",
                "effective_date": date.today(),
                "notes": "부드러운 계란찜",
                "nutrition_data": {
                    "calories": 120,
                    "protein": 8.5,
                    "carbohydrates": 2.1,
                    "fat": 8.8,
                    "sodium": 320
                },
                "evaluation_score": 85,
                "ingredients": [
                    {"name": "계란", "quantity": 1.5, "unit": "개"}      # 1.5개 per person
                ]
            }
        ]
        
        # 레시피 생성
        recipe_ids = {}
        for recipe_data in sample_recipes:
            existing_recipe = session.query(Recipe).filter(Recipe.name == recipe_data['name']).first()
            if not existing_recipe:
                # 재료 정보 분리
                ingredients = recipe_data.pop('ingredients', [])
                
                # 레시피 생성
                new_recipe = Recipe(**recipe_data)
                session.add(new_recipe)
                session.flush()  # ID 생성을 위해 flush
                recipe_ids[recipe_data['name']] = new_recipe.id
                
                # 레시피 재료 관계 생성
                for ingredient_info in ingredients:
                    if ingredient_info['name'] in ingredient_ids:
                        recipe_ingredient = RecipeIngredient(
                            recipe_id=new_recipe.id,
                            ingredient_id=ingredient_ids[ingredient_info['name']],
                            quantity=ingredient_info['quantity'],
                            unit=ingredient_info['unit']
                        )
                        session.add(recipe_ingredient)
                
                print(f"[CREATE] 새 레시피 생성: {recipe_data['name']}")
            else:
                recipe_ids[recipe_data['name']] = existing_recipe.id
                print(f"[EXISTS] 기존 레시피 사용: {recipe_data['name']}")
        
        # 샘플 식단표 생성
        sample_diet_plan = {
            "category": "일반식",
            "date": date.today(),
            "description": "샘플 일반식 식단표"
        }
        
        existing_diet_plan = session.query(DietPlan).filter(
            DietPlan.category == sample_diet_plan['category'],
            DietPlan.date == sample_diet_plan['date']
        ).first()
        
        if not existing_diet_plan:
            new_diet_plan = DietPlan(**sample_diet_plan)
            session.add(new_diet_plan)
            session.flush()
            diet_plan_id = new_diet_plan.id
            print(f"[CREATE] 새 식단표 생성: {sample_diet_plan['category']}")
        else:
            diet_plan_id = existing_diet_plan.id
            print(f"[EXISTS] 기존 식단표 사용: {sample_diet_plan['category']}")
        
        # 샘플 메뉴 데이터
        sample_menus = [
            {
                "diet_plan_id": diet_plan_id,
                "menu_type": "중식",
                "target_num_persons": 100,
                "target_food_cost": 3500,
                "evaluation_score": 88,
                "items": ["김치찌개", "불고기", "계란찜"]
            },
            {
                "diet_plan_id": diet_plan_id,
                "menu_type": "석식",
                "target_num_persons": 80,
                "target_food_cost": 3200,
                "evaluation_score": 85,
                "items": ["된장찌개", "닭볶음탕"]
            }
        ]
        
        # 메뉴 생성
        for menu_data in sample_menus:
            items = menu_data.pop('items', [])
            
            existing_menu = session.query(Menu).filter(
                Menu.diet_plan_id == menu_data['diet_plan_id'],
                Menu.menu_type == menu_data['menu_type']
            ).first()
            
            if not existing_menu:
                new_menu = Menu(**menu_data)
                session.add(new_menu)
                session.flush()
                
                # 메뉴 아이템 생성
                for item_name in items:
                    if item_name in recipe_ids:
                        menu_item = MenuItem(
                            menu_id=new_menu.id,
                            name=item_name,
                            recipe_id=recipe_ids[item_name],
                            portion_num_persons=menu_data['target_num_persons']
                        )
                        session.add(menu_item)
                
                print(f"[CREATE] 새 메뉴 생성: {menu_data['menu_type']}")
            else:
                print(f"[EXISTS] 기존 메뉴 사용: {menu_data['menu_type']}")
        
        # 변경사항 저장
        session.commit()
        
        # 결과 확인
        total_recipes = session.query(Recipe).count()
        total_menus = session.query(Menu).count()
        total_ingredients = session.query(Ingredient).count()
        
        print(f"[SUCCESS] 샘플 데이터 생성 완료")
        print(f"  - 총 레시피 수: {total_recipes}")
        print(f"  - 총 메뉴 수: {total_menus}")
        print(f"  - 총 식재료 수: {total_ingredients}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] 샘플 데이터 생성 중 오류 발생: {e}")
        if 'session' in locals():
            session.rollback()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("샘플 메뉴/레시피 데이터 생성 시작")
    print("=" * 60)
    
    success = create_sample_menu_data()
    
    print("=" * 60)
    if success:
        print("샘플 데이터 생성 성공!")
        print("\n이제 관리자 대시보드에서 메뉴/레시피 관리 탭을 확인해보세요.")
    else:
        print("샘플 데이터 생성 실패!")
    print("=" * 60)