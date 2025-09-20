import sqlite3
import re
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple, Dict, List
from datetime import datetime

# 기존 함수 import
from improved_unit_price_calculator import calculate_unit_price_improved as original_calculate_unit_price_improved

DATABASE_PATH = "daham_meal.db"

class LearningPriceCalculator:
    """학습 기반 단가 계산 시스템"""

    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.pattern_cache = {}
        self.load_patterns()

    def load_patterns(self):
        """저장된 패턴들을 메모리에 로드"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT specification_pattern, unit_pattern, extraction_method,
                       extraction_value, success_count, failure_count
                FROM price_calculation_patterns
                ORDER BY success_count DESC, last_used DESC
            """)

            for row in cursor.fetchall():
                pattern_key = f"{row[0]}|{row[1]}"
                self.pattern_cache[pattern_key] = {
                    'method': row[2],
                    'value': row[3],
                    'success_count': row[4],
                    'failure_count': row[5],
                    'confidence': row[4] / (row[4] + row[5]) if (row[4] + row[5]) > 0 else 0.5
                }

            conn.close()
            print(f"학습된 패턴 {len(self.pattern_cache)}개 로드 완료")

        except Exception as e:
            print(f"패턴 로드 실패: {e}")

    def find_matching_patterns(self, specification: str, unit: str) -> List[Dict]:
        """규격-단위에 매칭되는 패턴들 찾기"""
        matches = []

        for pattern_key, pattern_info in self.pattern_cache.items():
            spec_pattern, unit_pattern = pattern_key.split('|')

            # 와일드카드 패턴 매칭
            if self._pattern_matches(specification, spec_pattern) and \
               self._pattern_matches(unit, unit_pattern):
                matches.append({
                    'pattern_key': pattern_key,
                    'confidence': pattern_info['confidence'],
                    'method': pattern_info['method'],
                    'value': pattern_info['value'],
                    'success_count': pattern_info['success_count']
                })

        # 신뢰도 순으로 정렬
        matches.sort(key=lambda x: x['confidence'], reverse=True)
        return matches

    def _pattern_matches(self, text: str, pattern: str) -> bool:
        """패턴 매칭 (와일드카드 지원)"""
        if not text or not pattern:
            return False

        # 와일드카드 패턴을 정규식으로 변환
        pattern_regex = pattern.replace('*', '.*').replace('?', '.')
        return bool(re.search(pattern_regex, text, re.IGNORECASE))

    def extract_value_by_method(self, specification: str, unit: str, method: str, base_value: float) -> Optional[float]:
        """추출 방법에 따라 값 계산"""

        if method == 'direct_g':
            # 그램 단위 직접 추출
            match = re.search(r'(\d+(?:\.\d+)?)\s*g', specification, re.IGNORECASE)
            return float(match.group(1)) if match else None

        elif method == 'direct_kg':
            # 킬로그램을 그램으로 변환
            match = re.search(r'(\d+(?:\.\d+)?)\s*kg', specification, re.IGNORECASE)
            return float(match.group(1)) * 1000 if match else None

        elif method == 'extract_count_per_kg':
            # "20개입" 같은 패턴에서 개수 추출하여 1000으로 나누기
            match = re.search(r'(\d+)\s*개입', specification, re.IGNORECASE)
            if match:
                count = float(match.group(1))
                return 1000 / count if count > 0 else None
            return None

        elif method == 'extract_pack_weight':
            # 팩/포 중량 추출 (예: "500g*10팩" -> 5000g)
            patterns = [
                r'(\d+(?:\.\d+)?)\s*g\s*[*×x]\s*(\d+)\s*팩',
                r'(\d+(?:\.\d+)?)\s*g\s*[*×x]\s*(\d+)\s*포',
                r'(\d+(?:\.\d+)?)\s*kg\s*[*×x]\s*(\d+)\s*팩',
                r'(\d+(?:\.\d+)?)\s*kg\s*[*×x]\s*(\d+)\s*포',
            ]

            for pattern in patterns:
                match = re.search(pattern, specification, re.IGNORECASE)
                if match:
                    weight = float(match.group(1))
                    quantity = float(match.group(2))
                    if 'kg' in pattern:
                        weight *= 1000  # kg를 g로 변환
                    return weight * quantity
            return None

        elif method == 'weight_pieces_total':
            # "130G*18입" 같은 패턴에서 총 중량 계산
            match = re.search(r'(\d+(?:\.\d+)?)\s*g\s*[*×x]\s*(\d+)\s*입', specification, re.IGNORECASE)
            if match:
                weight_per_piece = float(match.group(1))
                pieces = float(match.group(2))
                return weight_per_piece * pieces
            return None

        else:
            # 기본값 반환
            return base_value

    def save_pattern(self, specification: str, unit: str, method: str, extraction_value: float, success: bool = True):
        """새로운 패턴 저장 또는 기존 패턴 업데이트"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 패턴 일반화 (숫자를 와일드카드로 변환)
            spec_pattern = re.sub(r'\d+(?:\.\d+)?', '*', specification)
            unit_pattern = unit if unit else '*'

            # 기존 패턴 확인
            cursor.execute("""
                SELECT id, success_count, failure_count
                FROM price_calculation_patterns
                WHERE specification_pattern = ? AND unit_pattern = ? AND extraction_method = ?
            """, (spec_pattern, unit_pattern, method))

            existing = cursor.fetchone()

            if existing:
                # 기존 패턴 업데이트
                pattern_id, success_count, failure_count = existing
                if success:
                    success_count += 1
                else:
                    failure_count += 1

                cursor.execute("""
                    UPDATE price_calculation_patterns
                    SET success_count = ?, failure_count = ?, last_used = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (success_count, failure_count, pattern_id))

                print(f"패턴 업데이트: {spec_pattern}|{unit_pattern} (성공:{success_count}, 실패:{failure_count})")
            else:
                # 새 패턴 저장
                cursor.execute("""
                    INSERT INTO price_calculation_patterns
                    (specification_pattern, unit_pattern, extraction_method, extraction_value,
                     success_count, failure_count, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (spec_pattern, unit_pattern, method, extraction_value,
                      1 if success else 0, 0 if success else 1, f"자동 학습된 패턴"))

                print(f"새 패턴 저장: {spec_pattern}|{unit_pattern} -> {method}")

            conn.commit()
            conn.close()

            # 캐시 업데이트
            self.load_patterns()

        except Exception as e:
            print(f"패턴 저장 실패: {e}")

    def save_feedback(self, ingredient_id: int, specification: str, unit: str,
                     original_price: float, calculated_price: float,
                     corrected_price: float = None, feedback_type: str = "auto"):
        """계산 피드백 저장"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO calculation_feedback
                (ingredient_id, original_specification, original_unit, original_price,
                 calculated_unit_price, corrected_unit_price, feedback_type, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ingredient_id, specification, unit, original_price,
                  calculated_price, corrected_price, feedback_type, "system"))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"피드백 저장 실패: {e}")

    def calculate_with_learning(self, price: float, specification: str, unit: str,
                              ingredient_id: int = None) -> Optional[float]:
        """학습 기반 단가 계산"""

        if not price or price <= 0 or not specification:
            return None

        print(f"학습 계산 시작: 가격={price}, 규격={specification}, 단위={unit}")

        # 1. 학습된 패턴으로 먼저 시도
        matching_patterns = self.find_matching_patterns(specification, unit or "")

        for pattern in matching_patterns[:3]:  # 상위 3개 패턴만 시도
            if pattern['confidence'] > 0.7:  # 70% 이상 신뢰도만
                try:
                    total_weight = self.extract_value_by_method(
                        specification, unit, pattern['method'], pattern['value']
                    )

                    if total_weight and total_weight > 0:
                        unit_price = price / total_weight
                        print(f"학습 패턴 매칭: {pattern['method']} -> {unit_price:.4f}")

                        # 성공한 패턴 강화
                        self.save_pattern(specification, unit, pattern['method'],
                                        pattern['value'], success=True)

                        # 피드백 저장
                        if ingredient_id:
                            self.save_feedback(ingredient_id, specification, unit,
                                             price, unit_price, feedback_type="learned_pattern")

                        return unit_price

                except Exception as e:
                    print(f"패턴 계산 실패: {e}")
                    # 실패한 패턴 기록
                    self.save_pattern(specification, unit, pattern['method'],
                                    pattern['value'], success=False)

        # 2. 기존 알고리즘으로 폴백
        print("기존 알고리즘으로 폴백")
        fallback_result = original_calculate_unit_price_improved(price, specification, unit)

        if fallback_result and fallback_result > 0:
            print(f"기존 알고리즘 성공: {fallback_result:.4f}")

            # 성공한 계산을 새로운 패턴으로 학습
            self._learn_from_successful_calculation(specification, unit, price, fallback_result)

            # 피드백 저장
            if ingredient_id:
                self.save_feedback(ingredient_id, specification, unit,
                                 price, fallback_result, feedback_type="fallback_success")

            return fallback_result

        print("모든 계산 방법 실패")

        # 실패 피드백 저장
        if ingredient_id:
            self.save_feedback(ingredient_id, specification, unit,
                             price, None, feedback_type="calculation_failed")

        return None

    def _learn_from_successful_calculation(self, specification: str, unit: str, price: float, result: float):
        """성공한 계산으로부터 패턴 학습"""
        try:
            # 역산으로 추출된 총 중량 계산
            total_weight = price / result

            # 추출 방법 추론
            method = "auto_learned"
            if "kg" in specification.lower():
                method = "auto_kg_pattern"
            elif "g" in specification.lower():
                method = "auto_g_pattern"
            elif "입" in specification:
                method = "auto_pieces_pattern"
            elif "팩" in specification or "포" in specification:
                method = "auto_pack_pattern"

            # 패턴 저장
            self.save_pattern(specification, unit, method, total_weight, success=True)

        except Exception as e:
            print(f"학습 실패: {e}")

# 글로벌 계산기 인스턴스
_calculator = LearningPriceCalculator()

def calculate_unit_price_with_learning(price: float, specification: str, unit: str, ingredient_id: int = None) -> Optional[float]:
    """학습 기반 단가 계산 - 기존 함수를 대체하는 인터페이스"""
    return _calculator.calculate_with_learning(price, specification, unit, ingredient_id)

def record_manual_correction(ingredient_id: int, specification: str, unit: str,
                           original_price: float, calculated_price: float, corrected_price: float):
    """수동 수정사항을 학습 시스템에 반영"""
    _calculator.save_feedback(ingredient_id, specification, unit, original_price,
                            calculated_price, corrected_price, "manual_correction")

    # 수정된 값으로 패턴 재학습
    if corrected_price and corrected_price > 0:
        total_weight = original_price / corrected_price
        _calculator.save_pattern(specification, unit, "manual_correction", total_weight, success=True)
        print(f"수동 수정사항 학습 완료: {specification} -> {corrected_price}")

def get_calculation_stats():
    """계산 통계 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 패턴 통계
        cursor.execute("""
            SELECT COUNT(*) as pattern_count,
                   SUM(success_count) as total_success,
                   SUM(failure_count) as total_failure
            FROM price_calculation_patterns
        """)
        pattern_stats = cursor.fetchone()

        # 피드백 통계
        cursor.execute("""
            SELECT feedback_type, COUNT(*) as count
            FROM calculation_feedback
            GROUP BY feedback_type
        """)
        feedback_stats = cursor.fetchall()

        conn.close()

        return {
            "patterns": {
                "count": pattern_stats[0],
                "success": pattern_stats[1],
                "failure": pattern_stats[2]
            },
            "feedback": dict(feedback_stats)
        }

    except Exception as e:
        print(f"통계 조회 실패: {e}")
        return {}