"""
식단표 작성 시스템 - 메뉴 블록 조합 방식
레시피를 선택해서 날짜별 식단표를 구성하는 시스템
"""

import sqlite3
from datetime import datetime, date
from typing import List, Dict, Optional
import json

class MealPlanBuilder:
    def __init__(self, db_path: str = "daham_meal.db"):
        self.db_path = db_path
    
    def get_connection(self):
        """DB 연결 반환"""
        return sqlite3.connect(self.db_path)
    
    def search_recipes(self, keyword: str = "", limit: int = 20) -> List[Dict]:
        """레시피 검색"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if keyword:
            cursor.execute("""
                SELECT id, name, evaluation_score 
                FROM recipes 
                WHERE name LIKE ?
                ORDER BY evaluation_score DESC, name
                LIMIT ?
            """, (f"%{keyword}%", limit))
        else:
            cursor.execute("""
                SELECT id, name, evaluation_score 
                FROM recipes 
                ORDER BY evaluation_score DESC, name
                LIMIT ?
            """, (limit,))
        
        recipes = []
        for row in cursor.fetchall():
            recipes.append({
                'id': row[0],
                'name': row[1], 
                'score': row[2] or 0
            })
        
        conn.close()
        return recipes
    
    def get_recipe_ingredients(self, recipe_id: int) -> List[Dict]:
        """레시피의 식재료 정보 조회"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ri.quantity, ri.unit, i.name, i.price
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = ?
        """, (recipe_id,))
        
        ingredients = []
        for row in cursor.fetchall():
            ingredients.append({
                'quantity': float(row[0]),
                'unit': row[1],
                'ingredient_name': row[2],
                'price': float(row[3]) if row[3] else 0
            })
        
        conn.close()
        return ingredients
    
    def create_diet_plan(self, category: str, plan_date: date, description: str = "") -> int:
        """새로운 식단표 생성"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO diet_plans (category, date, description, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (category, plan_date, description, datetime.now(), datetime.now()))
        
        diet_plan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return diet_plan_id
    
    def add_menu_to_plan(self, diet_plan_id: int, menu_type: str, 
                        target_persons: int, target_cost: float = None) -> int:
        """식단표에 메뉴 추가 (예: 중식A)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO menus (diet_plan_id, menu_type, target_num_persons, 
                              target_food_cost, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (diet_plan_id, menu_type, target_persons, target_cost, 
              datetime.now(), datetime.now()))
        
        menu_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return menu_id
    
    def add_menu_item(self, menu_id: int, recipe_id: int, 
                     portion_persons: int = None, yield_rate: float = 1.0) -> int:
        """메뉴에 레시피 추가"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 레시피명 조회
        cursor.execute("SELECT name FROM recipes WHERE id = ?", (recipe_id,))
        recipe_name = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO menu_items (menu_id, name, portion_num_persons, 
                                   yield_rate, recipe_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (menu_id, recipe_name, portion_persons, yield_rate, recipe_id,
              datetime.now(), datetime.now()))
        
        menu_item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return menu_item_id
    
    def calculate_menu_cost(self, menu_id: int) -> Dict:
        """메뉴의 예상 비용 계산"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                m.target_num_persons,
                mi.yield_rate,
                ri.quantity,
                i.price,
                i.name as ingredient_name,
                r.name as recipe_name
            FROM menus m
            JOIN menu_items mi ON m.id = mi.menu_id
            JOIN recipes r ON mi.recipe_id = r.id
            JOIN recipe_ingredients ri ON r.id = ri.recipe_id
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE m.id = ?
        """, (menu_id,))
        
        total_cost = 0
        items_detail = []
        
        current_recipe = None
        recipe_cost = 0
        
        for row in cursor.fetchall():
            target_persons, yield_rate, quantity, price, ingredient_name, recipe_name = row
            
            if current_recipe != recipe_name:
                if current_recipe:
                    items_detail.append({
                        'recipe_name': current_recipe,
                        'recipe_cost': recipe_cost
                    })
                current_recipe = recipe_name
                recipe_cost = 0
            
            # 실제 필요량 = (1인량 × 인분수) ÷ 수율
            actual_quantity = (quantity * target_persons) / yield_rate
            ingredient_cost = actual_quantity * (price or 0)
            
            recipe_cost += ingredient_cost
            total_cost += ingredient_cost
        
        # 마지막 레시피 추가
        if current_recipe:
            items_detail.append({
                'recipe_name': current_recipe,
                'recipe_cost': recipe_cost
            })
        
        conn.close()
        
        return {
            'total_cost': total_cost,
            'target_persons': target_persons,
            'cost_per_person': total_cost / target_persons if target_persons > 0 else 0,
            'items': items_detail
        }
    
    def get_diet_plan_summary(self, diet_plan_id: int) -> Dict:
        """식단표 요약 정보"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # 기본 정보
        cursor.execute("""
            SELECT category, date, description 
            FROM diet_plans 
            WHERE id = ?
        """, (diet_plan_id,))
        
        plan_info = cursor.fetchone()
        if not plan_info:
            return None
            
        # 메뉴 정보
        cursor.execute("""
            SELECT 
                m.id,
                m.menu_type,
                m.target_num_persons,
                m.target_food_cost,
                COUNT(mi.id) as item_count
            FROM menus m
            LEFT JOIN menu_items mi ON m.id = mi.menu_id
            WHERE m.diet_plan_id = ?
            GROUP BY m.id, m.menu_type, m.target_num_persons, m.target_food_cost
        """, (diet_plan_id,))
        
        menus = []
        total_estimated_cost = 0
        
        for row in cursor.fetchall():
            menu_id, menu_type, target_persons, target_cost, item_count = row
            
            # 각 메뉴의 예상 비용 계산
            cost_info = self.calculate_menu_cost(menu_id)
            total_estimated_cost += cost_info['total_cost']
            
            menus.append({
                'id': menu_id,
                'menu_type': menu_type,
                'target_persons': target_persons,
                'target_cost': float(target_cost) if target_cost else 0,
                'estimated_cost': cost_info['total_cost'],
                'item_count': item_count
            })
        
        conn.close()
        
        return {
            'id': diet_plan_id,
            'category': plan_info[0],
            'date': plan_info[1],
            'description': plan_info[2],
            'menus': menus,
            'total_estimated_cost': total_estimated_cost
        }

# 사용 예시
if __name__ == "__main__":
    builder = MealPlanBuilder()
    
    print("=== 식단표 작성 시스템 테스트 ===\n")
    
    # 1. 레시피 검색
    print("1. 레시피 검색 (키워드: 찌개)")
    recipes = builder.search_recipes("찌개", 5)
    for i, recipe in enumerate(recipes, 1):
        print(f"   {i}. {recipe['name']} (평점: {recipe['score']})")
    
    if recipes:
        # 2. 새 식단표 생성
        print(f"\n2. 새 식단표 생성 (학교, 2025-08-28)")
        diet_plan_id = builder.create_diet_plan("학교", date(2025, 8, 28), "테스트 식단표")
        print(f"   식단표 ID: {diet_plan_id}")
        
        # 3. 중식 메뉴 추가
        print(f"\n3. 중식 메뉴 추가 (100명분)")
        menu_id = builder.add_menu_to_plan(diet_plan_id, "중식A", 100, 50000)
        print(f"   메뉴 ID: {menu_id}")
        
        # 4. 레시피 추가
        recipe_id = recipes[0]['id']
        print(f"\n4. 레시피 추가: {recipes[0]['name']}")
        menu_item_id = builder.add_menu_item(menu_id, recipe_id, 100, 0.8)
        print(f"   메뉴아이템 ID: {menu_item_id}")
        
        # 5. 비용 계산
        print(f"\n5. 메뉴 비용 계산")
        cost_info = builder.calculate_menu_cost(menu_id)
        print(f"   총 비용: {cost_info['total_cost']:,.0f}원")
        print(f"   1인당 비용: {cost_info['cost_per_person']:,.0f}원")
        
        # 6. 식단표 요약
        print(f"\n6. 식단표 요약")
        summary = builder.get_diet_plan_summary(diet_plan_id)
        print(f"   날짜: {summary['date']}")
        print(f"   카테고리: {summary['category']}")
        print(f"   메뉴 수: {len(summary['menus'])}")
        print(f"   총 예상비용: {summary['total_estimated_cost']:,.0f}원")