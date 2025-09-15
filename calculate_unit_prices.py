import sqlite3
import re
from decimal import Decimal, InvalidOperation

def parse_specification(spec_text):
    """
    규격 텍스트를 파싱하여 수량과 단위를 추출
    예: "1kg*10ea" -> (10, "kg", 1000)
        "500g*20pac" -> (20, "pac", 500)
        "18L*1ea" -> (1, "L", 18000)
        "3kg" -> (1, "kg", 3000)
    """
    if not spec_text:
        return None, None, None

    # 일반적인 패턴들
    patterns = [
        # 무게 * 수량 패턴 (예: 1kg*10ea, 500g*20pac)
        r'(\d+(?:\.\d+)?)\s*(kg|g|mg)\s*[*×xX]\s*(\d+)\s*(ea|pac|개|포|봉|박스|box)?',
        # 부피 * 수량 패턴 (예: 18L*1ea, 500ml*24개)
        r'(\d+(?:\.\d+)?)\s*(L|l|ml|ML)\s*[*×xX]\s*(\d+)\s*(ea|pac|개|포|봉|박스|box)?',
        # 무게만 있는 패턴 (예: 1kg, 500g)
        r'(\d+(?:\.\d+)?)\s*(kg|g|mg)(?:\s|$)',
        # 부피만 있는 패턴 (예: 1L, 500ml)
        r'(\d+(?:\.\d+)?)\s*(L|l|ml|ML)(?:\s|$)',
        # 수량 * 무게 패턴 (예: 10ea*1kg)
        r'(\d+)\s*(ea|pac|개|포|봉|박스|box)\s*[*×xX]\s*(\d+(?:\.\d+)?)\s*(kg|g|mg)',
        # 수량 * 부피 패턴 (예: 24개*500ml)
        r'(\d+)\s*(ea|pac|개|포|봉|박스|box)\s*[*×xX]\s*(\d+(?:\.\d+)?)\s*(L|l|ml|ML)',
    ]

    for pattern in patterns:
        match = re.search(pattern, spec_text, re.IGNORECASE)
        if match:
            groups = match.groups()

            # 패턴에 따라 파싱
            if len(groups) == 4:  # 무게/부피 * 수량
                value = float(groups[0])
                unit = groups[1].lower()
                quantity = float(groups[2]) if groups[2] else 1

                # 단위를 그램으로 변환
                if unit in ['kg']:
                    total_grams = value * 1000 * quantity
                elif unit in ['g']:
                    total_grams = value * quantity
                elif unit in ['mg']:
                    total_grams = value / 1000 * quantity
                elif unit in ['l']:
                    total_grams = value * 1000 * quantity  # 1L = 1000ml로 가정
                elif unit in ['ml']:
                    total_grams = value * quantity
                else:
                    total_grams = value * quantity

                return quantity, unit, total_grams

            elif len(groups) == 2:  # 무게/부피만
                value = float(groups[0])
                unit = groups[1].lower()
                quantity = 1

                # 단위를 표준화
                if unit in ['kg']:
                    total_grams = value * 1000
                elif unit in ['g']:
                    total_grams = value
                elif unit in ['mg']:
                    total_grams = value / 1000
                elif unit in ['l']:
                    total_grams = value * 1000
                elif unit in ['ml']:
                    total_grams = value
                else:
                    total_grams = value

                return quantity, unit, total_grams

    # 패턴이 매치되지 않으면 숫자만 추출 시도
    numbers = re.findall(r'\d+(?:\.\d+)?', spec_text)
    if numbers:
        # 첫 번째 숫자를 기본값으로 사용
        return 1, "unit", float(numbers[0])

    return None, None, None

def calculate_unit_price(price, specification):
    """
    가격과 규격을 기반으로 단위당 가격 계산
    """
    if not price or price == 0:
        return None

    quantity, unit, total_value = parse_specification(specification)

    if total_value and total_value > 0:
        # 단위당 가격 = 전체 가격 / 전체 수량(그램 또는 ml)
        unit_price = float(price) / total_value
        return unit_price

    return None

def update_database_with_unit_prices():
    """
    데이터베이스의 모든 식자재에 대해 단위당 가격 계산 및 업데이트
    """
    conn = sqlite3.connect('backups/daham_meal.db')
    cursor = conn.cursor()

    # price_per_unit 컬럼이 없으면 추가
    cursor.execute("PRAGMA table_info(ingredients)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'price_per_unit' not in columns:
        cursor.execute("ALTER TABLE ingredients ADD COLUMN price_per_unit REAL")
        print("price_per_unit 컬럼 추가됨")

    # 모든 식자재 조회
    cursor.execute("""
        SELECT id, specification, purchase_price
        FROM ingredients
        WHERE purchase_price > 0 AND specification IS NOT NULL AND specification != ''
    """)

    ingredients = cursor.fetchall()
    updated_count = 0
    failed_count = 0

    print(f"총 {len(ingredients)}개 식자재 처리 시작...")

    for ing_id, spec, price in ingredients:
        try:
            unit_price = calculate_unit_price(price, spec)

            if unit_price is not None:
                cursor.execute("""
                    UPDATE ingredients
                    SET price_per_unit = ?
                    WHERE id = ?
                """, (unit_price, ing_id))
                updated_count += 1

                if updated_count % 100 == 0:
                    print(f"  {updated_count}개 처리 완료...")
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
            if failed_count <= 5:  # 처음 5개 오류만 출력
                print(f"  오류 (ID {ing_id}): {spec} - {str(e)}")

    # 변경사항 저장
    conn.commit()

    print(f"\n처리 완료:")
    print(f"  - 성공: {updated_count}개")
    print(f"  - 실패: {failed_count}개")

    # 샘플 데이터 확인
    cursor.execute("""
        SELECT ingredient_name, specification, purchase_price, price_per_unit
        FROM ingredients
        WHERE price_per_unit IS NOT NULL
        LIMIT 5
    """)

    print("\n샘플 데이터:")
    for row in cursor.fetchall():
        name, spec, price, unit_price = row
        print(f"  {name}: {spec} / KRW {price:,} -> KRW {unit_price:.4f}/단위")

    conn.close()

if __name__ == "__main__":
    # 테스트 케이스
    test_cases = [
        ("1kg*10ea", 50000),
        ("500g*20pac", 30000),
        ("18L*1ea", 45000),
        ("3kg", 15000),
        ("250ml*24개", 24000),
        ("5kg*2봉", 35000),
    ]

    print("규격 파싱 테스트:")
    for spec, price in test_cases:
        quantity, unit, total_value = parse_specification(spec)
        unit_price = calculate_unit_price(price, spec)
        print(f"  {spec} (KRW {price:,})")
        print(f"    -> 수량: {quantity}, 단위: {unit}, 총량: {total_value}")
        if unit_price:
            print(f"    -> 단위당 가격: KRW {unit_price:.4f}")
        print()

    # 데이터베이스 업데이트
    print("\n데이터베이스 업데이트 시작...")
    update_database_with_unit_prices()