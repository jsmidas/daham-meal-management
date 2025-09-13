from decimal import Decimal, ROUND_UP
from typing import Dict, List
import math

class MenuCalculator:
    """메뉴 관련 계산 로직을 담당하는 클래스"""
    
    @staticmethod
    def calculate_required_quantity(
        portion_num_persons: int,
        quantity_per_person: Decimal,
        yield_rate: Decimal = Decimal('1.0')
    ) -> Decimal:
        """
        필요한 식재료 량을 계산합니다.
        
        Args:
            portion_num_persons: 실제 식수
            quantity_per_person: 1인량 (kg)
            yield_rate: 수율 (0.7 = 70%)
        
        Returns:
            조정된 필요량 (kg)
        
        Example:
            중식A (105인): 쥬키니호박 0.045kg * 105 / 0.7 = 6.75kg
        """
        if yield_rate <= 0:
            raise ValueError("수율은 0보다 커야 합니다")
        
        raw_quantity = Decimal(str(portion_num_persons)) * quantity_per_person
        adjusted_quantity = raw_quantity / yield_rate
        
        return adjusted_quantity.quantize(Decimal('0.001'), rounding=ROUND_UP)
    
    @staticmethod
    def apply_moq_adjustment(
        required_quantity: Decimal,
        moq: Decimal = Decimal('1.0')
    ) -> Decimal:
        """
        최소 발주량(MOQ)을 적용하여 실제 발주량을 계산합니다.
        
        Args:
            required_quantity: 필요량
            moq: 최소 발주량
        
        Returns:
            MOQ가 적용된 발주량
        
        Example:
            필요량 6.75kg, MOQ 1kg → 7kg
        """
        if moq <= 0:
            raise ValueError("MOQ는 0보다 커야 합니다")
        
        # MOQ의 배수로 올림
        multiplier = math.ceil(float(required_quantity / moq))
        return Decimal(str(multiplier)) * moq
    
    @staticmethod
    def calculate_total_cost(
        order_quantity: Decimal,
        unit_price: Decimal
    ) -> Decimal:
        """
        총 비용을 계산합니다.
        
        Args:
            order_quantity: 발주량
            unit_price: 단가
        
        Returns:
            총 비용
        """
        return order_quantity * unit_price
    
    @staticmethod
    def calculate_menu_item_requirements(
        menu_item_data: Dict,
        recipe_ingredients: List[Dict]
    ) -> List[Dict]:
        """
        메뉴 아이템의 모든 식재료 소요량을 계산합니다.
        
        Args:
            menu_item_data: {
                'portion_num_persons': 105,
                'yield_rate': 0.7
            }
            recipe_ingredients: [
                {
                    'ingredient_id': 1,
                    'ingredient_name': '냉동쥬키니호박',
                    'quantity_per_person': 0.045,
                    'unit': 'kg',
                    'moq': 1.0,
                    'unit_price': 5000
                }
            ]
        
        Returns:
            List of ingredient requirements with calculations
        """
        result = []
        
        portion_num_persons = menu_item_data['portion_num_persons']
        yield_rate = Decimal(str(menu_item_data['yield_rate']))
        
        for ingredient in recipe_ingredients:
            quantity_per_person = Decimal(str(ingredient['quantity_per_person']))
            moq = Decimal(str(ingredient['moq']))
            unit_price = Decimal(str(ingredient['unit_price']))
            
            # 1. 기본 필요량 계산 (수율 적용)
            required_quantity = MenuCalculator.calculate_required_quantity(
                portion_num_persons, quantity_per_person, yield_rate
            )
            
            # 2. MOQ 적용
            order_quantity = MenuCalculator.apply_moq_adjustment(required_quantity, moq)
            
            # 3. 총 비용 계산
            total_cost = MenuCalculator.calculate_total_cost(order_quantity, unit_price)
            
            requirement = {
                'ingredient_id': ingredient['ingredient_id'],
                'ingredient_name': ingredient['ingredient_name'],
                'unit': ingredient['unit'],
                'quantity_per_person': float(quantity_per_person),
                'portion_num_persons': portion_num_persons,
                'yield_rate': float(yield_rate),
                'required_quantity': float(required_quantity),
                'moq': float(moq),
                'order_quantity': float(order_quantity),
                'unit_price': float(unit_price),
                'total_cost': float(total_cost)
            }
            
            result.append(requirement)
        
        return result

class NutritionCalculator:
    """영양 정보 계산 로직"""
    
    @staticmethod
    def calculate_menu_nutrition(
        recipe_ingredients: List[Dict],
        portion_num_persons: int
    ) -> Dict:
        """
        메뉴의 영양 정보를 계산합니다.
        
        Args:
            recipe_ingredients: 레시피 식재료 목록
            portion_num_persons: 식수
        
        Returns:
            영양 정보 딕셔너리
        """
        total_nutrition = {
            'calories': 0,
            'protein': 0,
            'carbohydrates': 0,
            'fat': 0,
            'sodium': 0
        }
        
        for ingredient in recipe_ingredients:
            nutrition_data = ingredient.get('nutrition_data', {})
            quantity = ingredient['quantity_per_person'] * portion_num_persons
            
            for nutrient in total_nutrition:
                if nutrient in nutrition_data:
                    total_nutrition[nutrient] += nutrition_data[nutrient] * quantity
        
        # 1인당 영양 정보 계산
        per_person_nutrition = {
            f"{nutrient}_per_person": total_nutrition[nutrient] / portion_num_persons
            for nutrient in total_nutrition
        }
        
        return {
            'total_nutrition': total_nutrition,
            'per_person_nutrition': per_person_nutrition,
            'portion_num_persons': portion_num_persons
        }

class CostAnalyzer:
    """비용 분석 로직"""
    
    @staticmethod
    def analyze_menu_cost(
        target_food_cost: Decimal,
        actual_cost: Decimal
    ) -> Dict:
        """
        목표 대비 실제 비용을 분석합니다.
        
        Args:
            target_food_cost: 목표 식재료비
            actual_cost: 실제 계산된 비용
        
        Returns:
            비용 분석 결과
        """
        if target_food_cost <= 0:
            return {
                'target_cost': float(target_food_cost),
                'actual_cost': float(actual_cost),
                'difference': float(actual_cost),
                'difference_percentage': 0,
                'status': 'no_target'
            }
        
        difference = actual_cost - target_food_cost
        difference_percentage = (difference / target_food_cost) * 100
        
        if difference_percentage <= -10:
            status = 'under_budget'
        elif difference_percentage >= 10:
            status = 'over_budget'
        else:
            status = 'within_budget'
        
        return {
            'target_cost': float(target_food_cost),
            'actual_cost': float(actual_cost),
            'difference': float(difference),
            'difference_percentage': float(difference_percentage),
            'status': status
        }
    
    @staticmethod
    def calculate_cost_per_person(
        total_cost: Decimal,
        portion_num_persons: int
    ) -> Decimal:
        """1인당 비용을 계산합니다."""
        if portion_num_persons <= 0:
            raise ValueError("식수는 0보다 커야 합니다")
        
        return total_cost / Decimal(str(portion_num_persons))

# 유틸리티 함수들
def validate_yield_rate(yield_rate: float) -> bool:
    """수율 값이 유효한지 검증합니다."""
    return 0 < yield_rate <= 1.0

def validate_portion_persons(portion_num_persons: int) -> bool:
    """식수가 유효한지 검증합니다."""
    return portion_num_persons > 0

def format_currency(amount: Decimal) -> str:
    """금액을 한국 원화 형식으로 포맷합니다."""
    return f"{int(amount):,}원"

def format_weight(weight: Decimal, unit: str = "kg") -> str:
    """중량을 포맷합니다."""
    if unit == "kg":
        return f"{float(weight):.3f}kg"
    elif unit == "g":
        return f"{float(weight * 1000):.0f}g"
    else:
        return f"{float(weight):.3f}{unit}"