import sqlite3
import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple

def parse_specification_improved(spec_text: str, unit_text: str = None) -> Optional[Tuple[float, str, float]]:
    """
    개선된 규격 파싱 함수

    Args:
        spec_text: 규격 텍스트 (예: "120g_3입", "500매입", "21KG/EA")
        unit_text: 단위 텍스트 (예: "EA", "BOX", "PAC")

    Returns:
        (수량, 단위, 전체값) 또는 None
    """
    if not spec_text:
        return None

    spec_text = spec_text.strip()

    # 특수 패턴들을 먼저 처리
    special_patterns = [
        # "120g_3입" 패턴 -> 120g × 3 = 360g
        (r'(\d+(?:\.\d+)?)\s*(g|kg|mg)\s*[_\-]\s*(\d+)\s*입', 'weight_multiple'),
        # "500매입" 패턴 -> 500개
        (r'(\d+)\s*매입', 'pieces'),
        # "300입" 패턴 -> 300개
        (r'(\d+)\s*입', 'pieces'),
        # "21KG/EA" 패턴 -> 21kg
        (r'(\d+(?:\.\d+)?)\s*(KG|kg|Kg)\s*/\s*EA', 'weight_per_ea'),
        # "9.5KG/EA" 패턴 -> 9.5kg
        (r'(\d+(?:\.\d+)?)\s*(KG|kg|Kg)\s*/\s*EA', 'weight_per_ea'),
        # "700ml_50입" 패턴 -> 700ml × 50 = 35000ml
        (r'(\d+(?:\.\d+)?)\s*(ml|ML|l|L)\s*[_\-]\s*(\d+)\s*입', 'volume_multiple'),
    ]

    for pattern, pattern_type in special_patterns:
        match = re.search(pattern, spec_text, re.IGNORECASE)
        if match:
            if pattern_type == 'weight_multiple':
                # 무게_수량입 패턴
                value = float(match.group(1))
                unit = match.group(2).lower()
                count = float(match.group(3))

                if unit == 'kg':
                    total = value * 1000 * count  # kg를 g로 변환
                elif unit == 'g':
                    total = value * count
                elif unit == 'mg':
                    total = (value / 1000) * count
                else:
                    total = value * count

                return count, f"{unit}_pieces", total

            elif pattern_type == 'pieces':
                # N매입 또는 N입 패턴
                count = float(match.group(1))
                return count, "pieces", count  # 개수 단위

            elif pattern_type == 'weight_per_ea':
                # KG/EA 패턴
                value = float(match.group(1))
                return 1, "kg", value * 1000  # kg를 g로 변환

            elif pattern_type == 'volume_multiple':
                # 부피_수량입 패턴
                value = float(match.group(1))
                unit = match.group(2).lower()
                count = float(match.group(3))

                if unit in ['l']:
                    total = value * 1000 * count  # L를 ml로 변환
                elif unit in ['ml']:
                    total = value * count
                else:
                    total = value * count

                return count, f"{unit}_pieces", total

    # 일반적인 패턴들 (대소문자 구분 없이 처리)
    general_patterns = [
        # "1kg*10ea" 형태
        (r'(\d+(?:\.\d+)?)\s*(kg|g|mg|KG|G|MG)\s*[*×xX]\s*(\d+)\s*(ea|pac|개|포|봉|박스|box)?', 'weight_qty'),
        # "18L*1ea" 형태
        (r'(\d+(?:\.\d+)?)\s*(L|l|ml|ML|ℓ|㎖)\s*[*×xX]\s*(\d+)\s*(ea|pac|개|포|봉|박스|box)?', 'volume_qty'),
        # "1kg" 형태
        (r'(\d+(?:\.\d+)?)\s*(kg|g|mg|KG|G|MG)\b', 'weight_only'),
        # "1L", "300ML", "415ml" 형태 (대소문자 무관)
        (r'(\d+(?:\.\d+)?)\s*(L|l|ml|ML|ℓ|㎖|Ml|mL)\b', 'volume_only'),
        # 단순 "300ML", "415ml" 같은 표기 (전체 문자열이 숫자+ML인 경우)
        (r'^(\d+(?:\.\d+)?)\s*(ML|ml|Ml|mL)$', 'volume_simple'),
    ]

    for pattern, pattern_type in general_patterns:
        match = re.search(pattern, spec_text, re.IGNORECASE)
        if match:
            if pattern_type in ['weight_qty', 'volume_qty']:
                value = float(match.group(1))
                unit = match.group(2).lower()
                quantity = float(match.group(3))

                if unit in ['kg']:
                    total = value * 1000 * quantity
                elif unit in ['g']:
                    total = value * quantity
                elif unit in ['mg']:
                    total = (value / 1000) * quantity
                elif unit in ['l']:
                    total = value * 1000 * quantity
                elif unit in ['ml']:
                    total = value * quantity
                else:
                    total = value * quantity

                return quantity, unit, total

            elif pattern_type in ['weight_only', 'volume_only', 'volume_simple']:
                value = float(match.group(1))
                unit = match.group(2).lower()

                if unit in ['kg']:
                    total = value * 1000
                elif unit in ['g']:
                    total = value
                elif unit in ['mg']:
                    total = value / 1000
                elif unit in ['l', 'ℓ']:
                    total = value * 1000
                elif unit in ['ml', '㎖']:
                    total = value
                else:
                    total = value

                return 1, unit, total

    # EA 단위이지만 규격에서 정보를 찾을 수 없는 경우
    # 계산하지 않고 None 반환
    if unit_text and unit_text.upper() == 'EA':
        # EA인데 규격에서 수량이나 무게 정보를 찾을 수 없으면 계산 불가
        return None

    return None

def calculate_unit_price_improved(price: float, specification: str, unit: str = None) -> Optional[float]:
    """
    개선된 단위당 가격 계산

    Args:
        price: 입고가
        specification: 규격
        unit: 단위

    Returns:
        단위당 가격 또는 None (계산 불가능한 경우)
    """
    if not price or price == 0:
        return None

    result = parse_specification_improved(specification, unit)

    if result is None:
        return None

    quantity, parsed_unit, total_value = result

    if total_value and total_value > 0:
        # 개수 단위인 경우 (매, 입 등)
        if parsed_unit == "pieces":
            # 개당 가격
            unit_price = float(price) / total_value
        else:
            # 그램당 또는 ml당 가격
            unit_price = float(price) / total_value

        return unit_price

    return None

def test_examples():
    """
    사용자가 제공한 예제들을 테스트
    """
    test_cases = [
        # (규격, 단위, 입고가, 예상 계산값)
        ("120g_3입", "EA", 1000, "360g으로 계산 -> 2.78원/g"),
        ("500매입", "EA", 5000, "500개로 계산 -> 10원/개"),
        ("검정_대_190*85mm_300입", "BOX", 3000, "300개로 계산 -> 10원/개"),
        ("백색_190mm_300입", "BOX", 3000, "300개로 계산 -> 10원/개"),
        ("PP_158파이*60mm_700ml_50입", "EA", 2500, "50개로 계산 -> 50원/개"),
        ("21KG/EA", "EA", 21000, "21kg로 계산 -> 1원/g"),
        ("9.5KG/EA", "EA", 9500, "9.5kg로 계산 -> 1원/g"),
        ("300ML", "EA", 300, "300ml로 계산 -> 1원/ml"),
        ("415ml", "EA", 415, "415ml로 계산 -> 1원/ml"),
        ("500ML", "BOX", 1000, "500ml로 계산 -> 2원/ml"),
    ]

    print("테스트 결과:")
    print("=" * 80)

    for spec, unit, price, expected in test_cases:
        result = calculate_unit_price_improved(price, spec, unit)
        parsed = parse_specification_improved(spec, unit)

        print(f"규격: {spec}")
        print(f"단위: {unit}")
        print(f"입고가: {price:,}원")
        if parsed:
            qty, parsed_unit, total = parsed
            print(f"파싱 결과: 수량={qty}, 단위={parsed_unit}, 총량={total}")
        if result:
            print(f"단위당 가격: {result:.2f}원")
        else:
            print(f"단위당 가격: 계산 불가")
        print(f"예상: {expected}")
        print("-" * 40)

def update_database_improved():
    """
    개선된 로직으로 데이터베이스 업데이트
    """
    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()

    # 먼저 단위당 단가 컬럼이 있는지 확인
    cursor.execute("PRAGMA table_info(ingredients)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'price_per_unit' not in columns:
        cursor.execute("ALTER TABLE ingredients ADD COLUMN price_per_unit REAL")
        print("price_per_unit 컬럼 추가됨")

    # 모든 식자재 조회
    cursor.execute("""
        SELECT id, specification, unit, purchase_price
        FROM ingredients
        WHERE purchase_price IS NOT NULL AND purchase_price != '' AND purchase_price != 0
    """)

    ingredients = cursor.fetchall()

    success_count = 0
    skip_count = 0
    error_count = 0

    for ingredient_id, spec, unit, price in ingredients:
        try:
            # 가격을 float로 변환
            if isinstance(price, str):
                price = float(price.replace(',', '').replace('원', ''))

            # 개선된 로직으로 단위당 가격 계산
            unit_price = calculate_unit_price_improved(price, spec, unit)

            if unit_price is not None:
                cursor.execute(
                    "UPDATE ingredients SET price_per_unit = ? WHERE id = ?",
                    (unit_price, ingredient_id)
                )
                success_count += 1
            else:
                # 계산 불가능한 경우 NULL로 설정
                cursor.execute(
                    "UPDATE ingredients SET price_per_unit = NULL WHERE id = ?",
                    (ingredient_id,)
                )
                skip_count += 1

        except Exception as e:
            error_count += 1
            print(f"Error processing ID {ingredient_id}: {str(e)}")

    conn.commit()
    conn.close()

    print(f"\n업데이트 완료:")
    print(f"성공: {success_count}개")
    print(f"계산 불가 (건너뜀): {skip_count}개")
    print(f"오류: {error_count}개")
    print(f"총 처리: {success_count + skip_count + error_count}개")

if __name__ == "__main__":
    print("개선된 단위당 가격 계산 테스트")
    print("=" * 80)
    test_examples()

    print("\n\n데이터베이스 업데이트를 시작하시겠습니까? (y/n): ", end="")
    response = input().strip().lower()

    if response == 'y':
        update_database_improved()
    else:
        print("업데이트 취소됨")