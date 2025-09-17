import sqlite3
import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple, Dict

def parse_specification_debug(spec_text: str, unit_text: str = None) -> Dict:
    """
    디버깅 정보를 포함한 개선된 규격 파싱 함수

    Returns:
        {
            'success': bool,
            'result': (수량, 단위, 전체값) or None,
            'debug_info': {
                'original_spec': str,
                'cleaned_spec': str,
                'matched_pattern': str,
                'pattern_type': str,
                'calculation_steps': [],
                'error': str or None
            }
        }
    """
    debug_info = {
        'original_spec': spec_text,
        'cleaned_spec': '',
        'matched_pattern': None,
        'pattern_type': None,
        'calculation_steps': [],
        'error': None
    }

    if not spec_text:
        debug_info['error'] = '규격 텍스트가 비어있음'
        return {'success': False, 'result': None, 'debug_info': debug_info}

    spec_text = spec_text.strip()

    # ± 오차 범위 제거
    cleaned_spec = re.sub(r'(\d+)±\d+~?\d*', r'\1', spec_text)
    debug_info['cleaned_spec'] = cleaned_spec
    debug_info['calculation_steps'].append(f"원본: {spec_text}")
    debug_info['calculation_steps'].append(f"정리됨: {cleaned_spec}")

    # 특수 패턴들 정의 - 순서가 중요함! 더 구체적인 패턴을 먼저 체크
    special_patterns = [
        # "(34g*29입 1Kg/EA)" 패턴 - 전체 무게가 명시된 경우 우선 사용
        (r'\([^)]*\d+\s*[gG]\s*[*×xX]\s*\d+\s*입\s+(\d+(?:\.\d+)?)\s*(Kg|KG|kg)\s*/\s*EA\)',
         'detail_with_total_weight_ea_kg',
         lambda m: (float(m.group(1)), m.group(2).lower())),

        # "(30gX17입 510g/EA)" 패턴 - 전체 무게 g 단위로 명시
        (r'\([^)]*\d+\s*[gG]\s*[*×xX]\s*\d+\s*입\s+(\d+(?:\.\d+)?)\s*(g|G)\s*/\s*EA\)',
         'detail_with_total_weight_ea_g',
         lambda m: (float(m.group(1)), m.group(2).lower())),

        # "(230G*10입)*4EA/BOX" 패턴 - 230g × 10 × 4 = 9200g
        (r'\((\d+(?:\.\d+)?)\s*(G|g|KG|kg)\s*[*×xX]\s*(\d+)\s*입\)\s*[*×xX]\s*(\d+)\s*EA\s*/\s*BOX',
         'weight_pieces_multiple_ea_box',
         lambda m: (float(m.group(1)), m.group(2).lower(), float(m.group(3)), float(m.group(4)))),

        # "(155G*10입)*6EA/BOX" 패턴 - 155g × 10 × 6 = 9300g
        (r'\((\d+(?:\.\d+)?)\s*(G|g|KG|kg)\s*[*×xX]\s*(\d+)\s*입\)\s*[*×xX]\s*(\d+)\s*EA\s*/\s*BOX',
         'weight_pieces_multiple_ea_box',
         lambda m: (float(m.group(1)), m.group(2).lower(), float(m.group(3)), float(m.group(4)))),

        # "(mini꼬마피자_40g*6입*16봉 3.84Kg/BOX" 패턴 - 전체 무게 3.84kg = 3840g 사용
        (r'\([^)]*?(\d+(?:\.\d+)?)\s*(g|G|kg|KG)\s*[*×xX]\s*(\d+)\s*입\s*[*×xX]\s*(\d+)\s*[봉개]\s+(\d+(?:\.\d+)?)\s*(Kg|KG|kg|g|G)\s*/\s*BOX',
         'complex_with_total_weight',
         lambda m: (float(m.group(5)), m.group(6).lower())),

        # "4.15Kg(415g*10입/10인치)" 패턴 - 전체 무게 4.15kg = 4150g 사용
        (r'(\d+(?:\.\d+)?)\s*(Kg|KG|kg)\s*\([^)]*?\)',
         'total_weight_with_detail',
         lambda m: (float(m.group(1)), m.group(2).lower())),

        # "150G*10입" 패턴 - 150g × 10 = 1500g (전체 무게가 없을 때만)
        (r'(\d+(?:\.\d+)?)\s*(G|g|KG|kg)\s*[*×xX]\s*(\d+)\s*입',
         'weight_times_pieces',
         lambda m: (float(m.group(1)), m.group(2).lower(), float(m.group(3)))),

        # "100입*5EA/BOX" 패턴 - 100 × 5 = 500개
        (r'(\d+)\s*입\s*[*×xX]\s*(\d+)\s*EA\s*/\s*BOX',
         'pieces_times_ea_box',
         lambda m: (float(m.group(1)), float(m.group(2)))),

        # "140G*10개*4EA/BOX" 패턴 - 140g × 10 × 4 = 5600g
        (r'(\d+(?:\.\d+)?)\s*(G|g|KG|kg)\s*[*×xX]\s*(\d+)\s*개\s*[*×xX]\s*(\d+)\s*EA\s*/\s*BOX',
         'weight_items_ea_box',
         lambda m: (float(m.group(1)), m.group(2).lower(), float(m.group(3)), float(m.group(4)))),
    ]

    # 패턴 매칭 시도
    for pattern, pattern_type, extractor in special_patterns:
        match = re.search(pattern, cleaned_spec, re.IGNORECASE)
        if match:
            debug_info['matched_pattern'] = pattern
            debug_info['pattern_type'] = pattern_type

            try:
                extracted = extractor(match)
                debug_info['calculation_steps'].append(f"매칭된 패턴: {pattern_type}")
                debug_info['calculation_steps'].append(f"추출된 값: {extracted}")

                # 계산 수행
                if pattern_type == 'weight_pieces_multiple_ea_box':
                    # (230G*10입)*4EA/BOX 형태
                    weight, unit, pieces, ea = extracted
                    if unit in ['kg']:
                        weight = weight * 1000
                    total = weight * pieces * ea
                    debug_info['calculation_steps'].append(f"계산: {weight}g × {pieces}입 × {ea}EA = {total}g")
                    return {'success': True, 'result': (1, 'g', total), 'debug_info': debug_info}

                elif pattern_type == 'detail_with_total_weight_ea_kg':
                    # "(34g*29입 1Kg/EA)" 형태 - 전체 무게 kg 사용
                    total_weight, unit = extracted
                    if unit in ['kg']:
                        total_weight = total_weight * 1000
                    debug_info['calculation_steps'].append(f"전체 무게(EA당) 명시됨: {total_weight}g")
                    return {'success': True, 'result': (1, 'g', total_weight), 'debug_info': debug_info}

                elif pattern_type == 'detail_with_total_weight_ea_g':
                    # "(30gX17입 510g/EA)" 형태 - 전체 무게 g 사용
                    total_weight, unit = extracted
                    debug_info['calculation_steps'].append(f"전체 무게(EA당) 명시됨: {total_weight}g")
                    return {'success': True, 'result': (1, 'g', total_weight), 'debug_info': debug_info}

                elif pattern_type == 'complex_with_total_weight':
                    # 전체 무게가 명시된 경우
                    total_weight, unit = extracted
                    if unit in ['kg']:
                        total_weight = total_weight * 1000
                    debug_info['calculation_steps'].append(f"전체 무게 사용: {total_weight}g")
                    return {'success': True, 'result': (1, 'g', total_weight), 'debug_info': debug_info}

                elif pattern_type == 'total_weight_with_detail':
                    # 전체 무게가 앞에 있는 경우
                    weight, unit = extracted
                    if unit in ['kg']:
                        weight = weight * 1000
                    debug_info['calculation_steps'].append(f"전체 무게: {weight}g")
                    return {'success': True, 'result': (1, 'g', weight), 'debug_info': debug_info}

                elif pattern_type == 'detail_with_total_weight_ea':
                    # 세부사항과 전체 무게가 있는 경우
                    total_weight, unit = extracted
                    if unit in ['kg']:
                        total_weight = total_weight * 1000
                    debug_info['calculation_steps'].append(f"전체 무게(EA당): {total_weight}g")
                    return {'success': True, 'result': (1, 'g', total_weight), 'debug_info': debug_info}

                elif pattern_type == 'weight_times_pieces':
                    # 150G*10입 형태
                    weight, unit, pieces = extracted
                    if unit in ['kg']:
                        weight = weight * 1000
                    total = weight * pieces
                    debug_info['calculation_steps'].append(f"계산: {weight}g × {pieces}입 = {total}g")
                    return {'success': True, 'result': (1, 'g', total), 'debug_info': debug_info}

                elif pattern_type == 'pieces_times_ea_box':
                    # 100입*5EA/BOX 형태
                    pieces, ea = extracted
                    total = pieces * ea
                    debug_info['calculation_steps'].append(f"계산: {pieces}입 × {ea}EA = {total}개")
                    return {'success': True, 'result': (1, '개', total), 'debug_info': debug_info}

                elif pattern_type == 'weight_items_ea_box':
                    # 140G*10개*4EA/BOX 형태
                    weight, unit, items, ea = extracted
                    if unit in ['kg']:
                        weight = weight * 1000
                    total = weight * items * ea
                    debug_info['calculation_steps'].append(f"계산: {weight}g × {items}개 × {ea}EA = {total}g")
                    return {'success': True, 'result': (1, 'g', total), 'debug_info': debug_info}

            except Exception as e:
                debug_info['error'] = f"계산 오류: {str(e)}"
                return {'success': False, 'result': None, 'debug_info': debug_info}

    # 기본 패턴 시도 (무게나 부피만 있는 경우)
    basic_patterns = [
        (r'(\d+(?:\.\d+)?)\s*(kg|KG|Kg)', 'basic_weight_kg'),
        (r'(\d+(?:\.\d+)?)\s*(g|G)', 'basic_weight_g'),
        (r'(\d+(?:\.\d+)?)\s*(L|l)', 'basic_volume_l'),
        (r'(\d+(?:\.\d+)?)\s*(ml|ML)', 'basic_volume_ml'),
    ]

    for pattern, pattern_type in basic_patterns:
        match = re.search(pattern, cleaned_spec, re.IGNORECASE)
        if match:
            debug_info['matched_pattern'] = pattern
            debug_info['pattern_type'] = pattern_type
            value = float(match.group(1))
            unit = match.group(2).lower()

            if unit in ['kg']:
                total = value * 1000
                debug_info['calculation_steps'].append(f"기본 무게: {value}kg = {total}g")
                return {'success': True, 'result': (1, 'g', total), 'debug_info': debug_info}
            elif unit in ['g']:
                debug_info['calculation_steps'].append(f"기본 무게: {value}g")
                return {'success': True, 'result': (1, 'g', value), 'debug_info': debug_info}
            elif unit in ['l']:
                total = value * 1000
                debug_info['calculation_steps'].append(f"기본 부피: {value}L = {total}ml")
                return {'success': True, 'result': (1, 'ml', total), 'debug_info': debug_info}
            elif unit in ['ml']:
                debug_info['calculation_steps'].append(f"기본 부피: {value}ml")
                return {'success': True, 'result': (1, 'ml', value), 'debug_info': debug_info}

    debug_info['error'] = '매칭되는 패턴 없음'
    return {'success': False, 'result': None, 'debug_info': debug_info}


def calculate_unit_price_debug(price: float, specification: str, unit: str = None) -> Dict:
    """
    디버깅 정보를 포함한 단위당 단가 계산

    Returns:
        {
            'success': bool,
            'unit_price': float or None,
            'unit': str,
            'debug_info': dict
        }
    """
    if not price or price == 0:
        return {
            'success': False,
            'unit_price': None,
            'unit': '',
            'debug_info': {'error': '가격이 0이거나 없음'}
        }

    if not specification:
        return {
            'success': False,
            'unit_price': None,
            'unit': '',
            'debug_info': {'error': '규격 정보 없음'}
        }

    # 규격 파싱
    parse_result = parse_specification_debug(specification, unit)

    if not parse_result['success'] or not parse_result['result']:
        return {
            'success': False,
            'unit_price': None,
            'unit': '',
            'debug_info': parse_result['debug_info']
        }

    quantity, parsed_unit, total = parse_result['result']

    # 단위당 가격 계산
    if total > 0:
        unit_price = price / total

        # 단위 결정
        if parsed_unit == 'g':
            display_unit = 'g당'
        elif parsed_unit == 'ml':
            display_unit = 'ml당'
        elif parsed_unit == '개':
            display_unit = '개당'
        else:
            display_unit = f'{parsed_unit}당'

        debug_info = parse_result['debug_info']
        debug_info['price'] = price
        debug_info['total_amount'] = total
        debug_info['unit_price'] = unit_price
        debug_info['calculation'] = f"{price}원 ÷ {total}{parsed_unit} = {unit_price:.2f}원/{parsed_unit}"

        return {
            'success': True,
            'unit_price': unit_price,
            'unit': display_unit,
            'debug_info': debug_info
        }

    return {
        'success': False,
        'unit_price': None,
        'unit': '',
        'debug_info': {'error': '총량이 0'}
    }


# 테스트 함수
def test_specifications():
    """제공된 규격들 테스트"""
    test_cases = [
        "(230G*10입)*4EA/BOX",
        "(155G*10입)*6EA/BOX",
        "(mini꼬마피자_40g*6입*16봉 3.84Kg/BOX",
        "4.15Kg(415g*10입/10인치)",
        "(30gX17±1~2입 510g/EA)",
        "150G*10입",
        "100입*5EA/BOX",
        "140G*10개*4EA/BOX"
    ]

    print("="*80)
    print("규격 파싱 테스트 결과")
    print("="*80)

    for spec in test_cases:
        result = parse_specification_debug(spec)
        print(f"\n규격: {spec}")
        print("-"*40)

        if result['success']:
            quantity, unit, total = result['result']
            print(f"[SUCCESS] 총 {total}{unit}")
        else:
            print(f"[FAIL] {result['debug_info']['error']}")

        print("\n계산 과정:")
        for step in result['debug_info']['calculation_steps']:
            print(f"  • {step}")

        if result['debug_info']['matched_pattern']:
            print(f"\n매칭 패턴: {result['debug_info']['pattern_type']}")


if __name__ == "__main__":
    test_specifications()