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

    # ± 오차 범위 제거 (예: "34±1g" -> "34g", "29±1입" -> "29입")
    spec_text = re.sub(r'(\d+)±\d+', r'\1', spec_text)

    # 특수 패턴들을 먼저 처리 (± 제거 후이므로 더 간단해짐)
    special_patterns = [
        # "2KG(200G*10EA)/BOX" 패턴 -> 2000g (전체 무게 우선)
        (r'(\d+(?:\.\d+)?)\s*(KG|kg)\s*\((\d+)\s*(G|g)\s*[*×xX]\s*(\d+)\s*(EA|ea|입)?\)', 'total_with_detail'),
        # "1.5KG(150G*10EA)/PAC" 패턴 -> 1500g (전체 무게 우선)
        (r'(\d+(?:\.\d+)?)\s*(KG|kg)\s*\(.*?\)', 'total_weight_priority'),
        # "(왕돈까스_300g*5입 1.5Kg/EA)" 패턴 -> 1500g (전체 무게 사용)
        (r'\([^)]*?(\d+)\s*(g|kg)\s*[*×xX]\s*(\d+)\s*입\s+(\d+(?:\.\d+)?)\s*(Kg|kg|g)\s*/\s*EA\)', 'parenthesis_with_total'),
        # "(71입 1Kg/EA)" 패턴 -> 1000g (전체 무게 사용)
        (r'\((\d+)\s*입\s+(\d+(?:\.\d+)?)\s*(Kg|kg|g)\s*/\s*EA\)', 'pieces_with_total_ea'),
        # "300G*5입/EA" 패턴 -> 1500g
        (r'(\d+)\s*(G|g|KG|kg)\s*[*×xX]\s*(\d+)\s*입\s*/\s*EA', 'weight_pieces_ea'),
        # "130G*18입/2.34KG" 패턴 -> 2340g (전체 무게 사용)
        (r'(\d+)\s*(G|g)\s*[*×xX]\s*(\d+)\s*입\s*/\s*(\d+(?:\.\d+)?)\s*(KG|kg)', 'weight_pieces_total'),
        # "2KG*5입/BOX" 패턴 -> 10kg = 10000g
        (r'(\d+(?:\.\d+)?)\s*(KG|kg)\s*[*×xX]\s*(\d+)\s*입\s*/\s*BOX', 'weight_pieces_box'),
        # "2KG*1입/BOX" 패턴 -> 2kg = 2000g
        (r'(\d+(?:\.\d+)?)\s*(KG|kg)\s*[*×xX]\s*(\d+)\s*입\s*/\s*BOX', 'weight_pieces_box'),
        # "200G*10입" 패턴 -> 2000g (더 유연한 매칭)
        (r'(\d+)\s*(G|g|KG|kg)\s*[*×xX]\s*(\d+)\s*입(?![/])', 'simple_weight_pieces'),
        # "50입*4EA/BOX" 패턴 -> 200개
        (r'(\d+)\s*입\s*[*×xX]\s*(\d+)\s*EA\s*/\s*BOX', 'pieces_ea_box'),
        # "10입" 같은 단순 입 패턴 (숫자입)
        (r'^(\d+)\s*입\s*$', 'simple_pieces'),
        # "입" 단독 패턴 -> 1개로 간주
        (r'^입\s*$', 'single_piece'),
        # "800G(80G*10입)" 패턴 -> 800g
        (r'(\d+(?:\.\d+)?)\s*(G|g|KG|kg)\s*\([^)]*\)', 'total_weight_with_detail'),
        # "(130g*10입 저장용 1.3Kg/EA)" 패턴 -> 1300g
        (r'\((\d+(?:\.\d+)?)\s*(g|kg)\s*[*×xX]\s*(\d+)\s*입.*?(\d+(?:\.\d+)?)\s*(Kg|kg|g)\s*/\s*EA\)', 'detail_with_total'),
        # "(100g*10입 1Kg/EA)" 패턴 -> 1000g
        (r'\((\d+(?:\.\d+)?)\s*(g|kg)\s*[*×xX]\s*(\d+)\s*입\s+(\d+(?:\.\d+)?)\s*(Kg|kg|g)\s*/\s*EA\)', 'detail_with_total_simple'),
        # "(80g*10입 800g/EA)" 패턴 -> 800g
        (r'\((\d+(?:\.\d+)?)\s*(g|kg)\s*[*×xX]\s*(\d+)\s*입\s+(\d+(?:\.\d+)?)\s*(g|kg)\s*/\s*EA\)', 'detail_with_total_simple'),
        # "120g_3입" 패턴 -> 120g × 3 = 360g
        (r'(\d+(?:\.\d+)?)\s*(g|kg|mg)\s*[_\-]\s*(\d+)\s*입', 'weight_multiple'),
        # "500매입" 패턴 -> 500개
        (r'(\d+)\s*매입', 'pieces'),
        # "300입" 패턴 -> 300개 (다른 패턴에 매칭되지 않은 경우)
        (r'(\d+)\s*입', 'pieces'),
        # "21KG/EA" 패턴 -> 21kg
        (r'(\d+(?:\.\d+)?)\s*(KG|kg|Kg)\s*/\s*EA', 'weight_per_ea'),
        # "700ml_50입" 패턴 -> 700ml × 50 = 35000ml
        (r'(\d+(?:\.\d+)?)\s*(ml|ML|l|L)\s*[_\-]\s*(\d+)\s*입', 'volume_multiple'),
    ]

    for pattern, pattern_type in special_patterns:
        match = re.search(pattern, spec_text, re.IGNORECASE)
        if match:
            if pattern_type == 'total_weight_with_detail':
                # "800G(80G*10입)" 형태 - 전체 무게를 사용
                value = float(match.group(1))
                unit = match.group(2).lower()

                if unit in ['kg']:
                    total = value * 1000
                else:
                    total = value

                return 1, 'g', total

            elif pattern_type in ['detail_with_total', 'detail_with_total_simple']:
                # "(130g*10입 저장용 1.3Kg/EA)" 형태 - 전체 무게 사용
                # 마지막에 나오는 전체 무게 사용
                total_value = float(match.group(4))
                total_unit = match.group(5).lower()

                if total_unit in ['kg']:
                    total = total_value * 1000
                else:
                    total = total_value

                return 1, 'g', total

            elif pattern_type == 'weight_multiple':
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
                # N매입 또는 N입 패턴 - 입 앞의 숫자가 총 개수
                count = float(match.group(1))
                return 1, "pieces", count  # 총 개수를 반환 (개당 가격 계산용)

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

            elif pattern_type == 'total_with_detail':
                # "2KG(200G*10EA)/BOX" 형태 - 전체 무게 사용
                total_value = float(match.group(1))
                total_unit = match.group(2).lower()

                if total_unit in ['kg']:
                    total = total_value * 1000
                else:
                    total = total_value

                return 1, 'g', total

            elif pattern_type == 'total_weight_priority':
                # "1.5KG(150G*10EA)/PAC" 형태 - 전체 무게 우선
                total_value = float(match.group(1))
                total_unit = match.group(2).lower()

                if total_unit in ['kg']:
                    total = total_value * 1000
                else:
                    total = total_value

                return 1, 'g', total

            elif pattern_type == 'parenthesis_with_total':
                # "(왕돈까스_300g*5입 1.5Kg/EA)" 형태 - 전체 무게 사용
                total_value = float(match.group(4))
                total_unit = match.group(5).lower()

                if total_unit in ['kg']:
                    total = total_value * 1000
                else:
                    total = total_value

                return 1, 'g', total

            elif pattern_type == 'pieces_with_total_ea':
                # "(71입 1Kg/EA)" 형태 - 전체 무게 사용
                total_value = float(match.group(2))
                total_unit = match.group(3).lower()

                if total_unit in ['kg']:
                    total = total_value * 1000
                else:
                    total = total_value

                return 1, 'g', total

            elif pattern_type == 'weight_pieces_total':
                # "130G*18입/2.34KG" 형태 - 전체 무게 사용
                total_value = float(match.group(4))
                total_unit = match.group(5).lower()

                if total_unit in ['kg']:
                    total = total_value * 1000
                else:
                    total = total_value

                return 1, 'g', total

            elif pattern_type == 'weight_pieces_box':
                # "2KG*5입/BOX" 형태 - 무게 × 개수
                value = float(match.group(1))
                unit = match.group(2).lower()
                count = float(match.group(3))

                if unit in ['kg']:
                    total = value * 1000 * count
                else:
                    total = value * count

                return 1, 'g', total

            elif pattern_type == 'simple_weight_pieces':
                # "200G*10입" 형태 - 무게 × 개수
                value = float(match.group(1))
                unit = match.group(2).lower()
                count = float(match.group(3))

                if unit in ['kg']:
                    total = value * 1000 * count
                elif unit in ['g']:
                    total = value * count
                else:
                    total = value * count

                return 1, 'g', total

            elif pattern_type == 'pieces_ea_box':
                # "50입*4EA/BOX" 형태 - 개수 × EA수
                pieces = float(match.group(1))
                ea_count = float(match.group(2))
                total = pieces * ea_count

                return total, "pieces", total

            elif pattern_type == 'weight_pieces_ea':
                # "300G*5입/EA" 형태 - 무게 × 개수
                value = float(match.group(1))
                unit = match.group(2).lower()
                count = float(match.group(3))

                if unit in ['kg']:
                    total = value * 1000 * count
                elif unit in ['g']:
                    total = value * count
                else:
                    total = value * count

                return 1, 'g', total

            elif pattern_type == 'simple_pieces':
                # "10입" 형태 - 입 앞의 숫자가 총 개수
                count = float(match.group(1))
                return 1, "pieces", count  # 1개 단위당 가격 계산을 위해 총 개수 반환

            elif pattern_type == 'single_piece':
                # "입" 단독 - 1개로 간주
                return 1, "pieces", 1

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

    # 단위가 이미 KG인 경우 특별 처리
    if unit and unit.upper() == 'KG':
        # 규격에서 수량 정보를 찾아보기
        spec_lower = specification.lower() if specification else ""

        # 패턴: "냉동/100g내외", "80g내외" -> 개별 중량이 100g이지만 KG 단위로 판매
        # KG 단위일 때 g내외는 개별 포장 단위를 의미하므로 KG당 가격으로 계산
        match = re.search(r'(\d+)\s*g\s*내외', spec_lower)
        if match:
            # KG 단위 판매이므로 1kg = 1000g당 가격
            return float(price) / 1000

        # 패턴: "180G내외" -> 개별 180g지만 KG 단위 판매
        match = re.search(r'(\d+)\s*[gG]\s*내외', specification)
        if match:
            # KG 단위 판매이므로 1kg = 1000g당 가격
            return float(price) / 1000

        # 패턴: "(1±0.2cm두께 돈까스용 KG)" -> KG당 가격이므로 1000g당 가격
        if 'kg' in spec_lower or '돈까스용' in spec_lower:
            # KG 단위 그대로이므로 g당 가격 계산 (1kg = 1000g)
            return float(price) / 1000

        # 그 외 KG 단위는 kg당 가격 그대로 반환 (g당으로 변환)
        return float(price) / 1000

    # EA나 기타 단위인 경우 기존 로직 사용
    result = parse_specification_improved(specification, unit)

    if result is None:
        # 단위가 EA이고 규격에 정보가 없으면 계산 불가
        if unit and unit.upper() in ['EA', 'BOX', 'PAC']:
            return None
        # 기타 단위는 그대로 반환 (단위당 가격)
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
        # 새로운 KG 단위 테스트 케이스
        ("냉동/100g내외", "KG", 10000, "KG당 10원/g (개별 100g)"),
        ("냉동/80g내외", "KG", 12000, "KG당 12원/g (개별 80g)"),
        ("80g내외", "KG", 8000, "KG당 8원/g (개별 80g)"),
        ("180G내외", "KG", 11720, "KG당 11.72원/g (개별 180g)"),
        ("(1±0.2cm두께 돈까스용 KG)", "KG", 13400, "KG당 13.40원/g"),
        ("냉동/80g내외/500g포장", "EA", 8050, "500g 포장으로 16.10원/g"),
        # 새로 추가된 패턴들
        ("(34±1g*29±1입 1Kg/EA)", "EA", 1000, "1000g로 계산 -> 1원/g"),
        ("2KG*1입/BOX", "BOX", 4000, "2000g로 계산 -> 2원/g"),
        ("(71±3입 1Kg/EA)", "EA", 1500, "1000g로 계산 -> 1.5원/g"),
        ("200G*10입", "EA", 2000, "2000g로 계산 -> 1원/g"),
        ("(리뉴얼_200g*10입 2Kg/EA)", "EA", 3000, "2000g로 계산 -> 1.5원/g"),
        ("130G*18입/2.34KG", "EA", 2340, "2340g로 계산 -> 1원/g"),
        ("2KG*5입/BOX", "BOX", 10000, "10000g로 계산 -> 1원/g"),
        ("50입*4EA/BOX", "BOX", 800, "200개로 계산 -> 4원/개"),
        # 추가 패턴 테스트
        ("300G*5입/EA", "EA", 1500, "1500g로 계산 -> 1원/g"),
        ("(왕돈까스_300g*5입 1.5Kg/EA)", "EA", 2250, "1500g로 계산 -> 1.5원/g"),
        ("(산양유가함유된_100g*10입 1Kg/EA)", "EA", 1000, "1000g로 계산 -> 1원/g"),
        ("10입", "EA", 100, "10개 전체 -> 10원/개"),
        ("입", "EA", 50, "1개로 계산 -> 50원/개"),
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