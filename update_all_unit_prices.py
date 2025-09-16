import sqlite3
import re
from improved_unit_price_calculator import calculate_unit_price_improved
import time
from datetime import datetime

def update_all_unit_prices():
    """
    모든 식자재의 단위당 가격을 계산하여 데이터베이스에 저장
    """
    start_time = time.time()

    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()

    # 먼저 단위당 단가 컬럼이 있는지 확인
    cursor.execute("PRAGMA table_info(ingredients)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'price_per_unit' not in columns:
        print("price_per_unit 컬럼 추가 중...")
        cursor.execute("ALTER TABLE ingredients ADD COLUMN price_per_unit REAL")
        conn.commit()
        print("price_per_unit 컬럼 추가 완료")

    # 전체 레코드 수 확인
    cursor.execute("SELECT COUNT(*) FROM ingredients WHERE purchase_price IS NOT NULL AND purchase_price != '' AND purchase_price != 0")
    total_count = cursor.fetchone()[0]
    print(f"\n총 처리할 레코드: {total_count:,}개")

    # 배치 처리를 위해 데이터 가져오기
    cursor.execute("""
        SELECT id, specification, unit, purchase_price, ingredient_name
        FROM ingredients
        WHERE purchase_price IS NOT NULL AND purchase_price != '' AND purchase_price != 0
        ORDER BY id
    """)

    batch_size = 1000
    processed = 0
    success_count = 0
    skip_count = 0
    error_count = 0

    # 계산 통계
    patterns_found = {}

    while True:
        rows = cursor.fetchmany(batch_size)
        if not rows:
            break

        updates = []

        for row in rows:
            ingredient_id, spec, unit, price, name = row

            try:
                # 가격을 float로 변환
                if isinstance(price, str):
                    price = float(price.replace(',', '').replace('원', ''))

                # 단위당 가격 계산
                unit_price = calculate_unit_price_improved(price, spec, unit)

                if unit_price is not None and unit_price > 0:
                    updates.append((unit_price, ingredient_id))
                    success_count += 1

                    # 패턴 통계 수집
                    if spec:
                        # 주요 패턴 감지
                        if re.search(r'\d+\s*[Gg]\s*\*\s*\d+\s*입', spec):
                            patterns_found['G*N입'] = patterns_found.get('G*N입', 0) + 1
                        elif re.search(r'\d+\s*[Kk][Gg]\s*\(', spec):
                            patterns_found['KG(세부)'] = patterns_found.get('KG(세부)', 0) + 1
                        elif re.search(r'\d+\s*입', spec):
                            patterns_found['N입'] = patterns_found.get('N입', 0) + 1
                        elif re.search(r'[Kk][Gg]/[Ee][Aa]', spec):
                            patterns_found['KG/EA'] = patterns_found.get('KG/EA', 0) + 1
                else:
                    updates.append((None, ingredient_id))
                    skip_count += 1

            except Exception as e:
                updates.append((None, ingredient_id))
                error_count += 1
                if error_count <= 5:  # 처음 5개 오류만 출력
                    print(f"오류 - ID {ingredient_id} [{name}]: {str(e)}")

        # 배치 업데이트
        if updates:
            cursor.executemany(
                "UPDATE ingredients SET price_per_unit = ? WHERE id = ?",
                updates
            )
            conn.commit()

        processed += len(rows)

        # 진행 상황 출력
        progress = (processed / total_count) * 100
        elapsed = time.time() - start_time
        rate = processed / elapsed if elapsed > 0 else 0
        eta = (total_count - processed) / rate if rate > 0 else 0

        print(f"\r진행: {processed:,}/{total_count:,} ({progress:.1f}%) | "
              f"성공: {success_count:,} | 스킵: {skip_count:,} | "
              f"속도: {rate:.0f}/초 | 예상 남은 시간: {eta:.0f}초", end='')

    print("\n")

    # 최종 통계
    cursor.execute("SELECT COUNT(*) FROM ingredients WHERE price_per_unit IS NOT NULL")
    final_count = cursor.fetchone()[0]

    # 샘플 데이터 확인
    print("\n=== 계산 샘플 (10개) ===")
    cursor.execute("""
        SELECT ingredient_name, specification, unit, purchase_price, price_per_unit
        FROM ingredients
        WHERE price_per_unit IS NOT NULL
        ORDER BY RANDOM()
        LIMIT 10
    """)

    for row in cursor.fetchall():
        name, spec, unit, price, unit_price = row
        print(f"{name[:20]:<20} | {spec[:30]:<30} | {unit:<5} | 입고가: {price:>8} | 단위당: {unit_price:.2f}")

    conn.close()

    total_time = time.time() - start_time

    print("\n" + "="*80)
    print(f"업데이트 완료!")
    print(f"총 처리 시간: {total_time:.1f}초 ({total_time/60:.1f}분)")
    print(f"처리 속도: {total_count/total_time:.0f} 레코드/초")
    print(f"\n처리 결과:")
    print(f"  - 성공: {success_count:,}개 ({success_count/total_count*100:.1f}%)")
    print(f"  - 계산 불가: {skip_count:,}개 ({skip_count/total_count*100:.1f}%)")
    print(f"  - 오류: {error_count:,}개 ({error_count/total_count*100:.1f}%)")
    print(f"  - DB 저장된 단가: {final_count:,}개")

    print(f"\n발견된 패턴 분포:")
    for pattern, count in sorted(patterns_found.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {pattern}: {count:,}개")

    return success_count, skip_count, error_count

def verify_calculations():
    """
    계산 결과 검증
    """
    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()

    print("\n=== 계산 검증 ===")

    # 특정 패턴별 검증
    test_patterns = [
        ("200G*10입", "200G*10%"),
        ("150G*10입", "150G*10%"),
        ("2KG(200", "%2KG(200%"),
        ("1.5KG(150", "%1.5KG(150%"),
        ("입", "%입"),
    ]

    for pattern_name, sql_pattern in test_patterns:
        cursor.execute(f"""
            SELECT COUNT(*), AVG(price_per_unit), MIN(price_per_unit), MAX(price_per_unit)
            FROM ingredients
            WHERE specification LIKE ?
            AND price_per_unit IS NOT NULL
        """, (sql_pattern,))

        count, avg_price, min_price, max_price = cursor.fetchone()
        if count and count > 0:
            print(f"{pattern_name:15} | 개수: {count:6,} | 평균: {avg_price:.2f} | 최소: {min_price:.2f} | 최대: {max_price:.2f}")

    conn.close()

if __name__ == "__main__":
    print("="*80)
    print("식자재 단위당 가격 전체 업데이트")
    print("="*80)
    print(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        update_all_unit_prices()
        verify_calculations()
        print(f"\n종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n[SUCCESS] 모든 작업이 성공적으로 완료되었습니다!")

    except KeyboardInterrupt:
        print("\n\n[WARN] 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n\n[ERROR] 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()