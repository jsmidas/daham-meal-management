#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
데이터베이스 인코딩 문제를 완전히 해결하는 스크립트
"""

import sqlite3
import sys

# UTF-8 출력 설정
sys.stdout.reconfigure(encoding='utf-8')

def fix_business_locations():
    """사업장 데이터 수정"""
    print("사업장 데이터 수정 중...")

    conn = sqlite3.connect('daham_meal.db', isolation_level=None)
    conn.execute("PRAGMA encoding = 'UTF-8'")
    cursor = conn.cursor()

    # 현재 데이터 확인
    cursor.execute("SELECT id, site_name FROM business_locations ORDER BY id")
    print("\n현재 데이터:")
    for row in cursor.fetchall():
        print(f"  ID {row[0]}: {repr(row[1])}")

    # 데이터 수정
    updates = [
        (1, '학교', '교육기관'),
        (2, '도시락', '도시락업체'),
        (3, '운반', '운반업체'),
        (4, '요양원', '요양시설')
    ]

    print("\n데이터 업데이트 중...")
    for id, name, type in updates:
        cursor.execute(
            "UPDATE business_locations SET site_name = ?, site_type = ? WHERE id = ?",
            (name, type, id)
        )
        print(f"  업데이트: ID {id} -> {name} ({type})")

    conn.commit()

    # 업데이트 확인
    cursor.execute("SELECT id, site_name, site_type FROM business_locations ORDER BY id")
    print("\n업데이트 후 데이터:")
    for row in cursor.fetchall():
        print(f"  ID {row[0]}: {row[1]} - {row[2]}")

    conn.close()
    print("✓ 사업장 데이터 수정 완료")

def fix_suppliers():
    """협력업체 데이터 수정"""
    print("\n협력업체 데이터 수정 중...")

    conn = sqlite3.connect('daham_meal.db', isolation_level=None)
    conn.execute("PRAGMA encoding = 'UTF-8'")
    cursor = conn.cursor()

    # 현재 데이터 확인
    cursor.execute("SELECT id, name FROM suppliers WHERE id <= 7 ORDER BY id")
    print("\n현재 데이터:")
    for row in cursor.fetchall():
        print(f"  ID {row[0]}: {repr(row[1])}")

    # 데이터 수정
    updates = [
        (1, '씨제이'),
        (2, '웰스토리'),
        (3, '동원홈푸드'),
        (4, '싱싱닭고기'),
        (5, '푸디스트'),
        (6, '현대그린푸드'),
        (7, '영유통')
    ]

    print("\n데이터 업데이트 중...")
    for id, name in updates:
        cursor.execute("UPDATE suppliers SET name = ? WHERE id = ?", (name, id))
        print(f"  업데이트: ID {id} -> {name}")

    conn.commit()

    # 업데이트 확인
    cursor.execute("SELECT id, name FROM suppliers WHERE id <= 7 ORDER BY id")
    print("\n업데이트 후 데이터:")
    for row in cursor.fetchall():
        print(f"  ID {row[0]}: {row[1]}")

    conn.close()
    print("✓ 협력업체 데이터 수정 완료")

def verify_mapping_data():
    """매핑 데이터 확인"""
    print("\n매핑 데이터 확인 중...")

    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            m.id,
            b.site_name as customer_name,
            s.name as supplier_name,
            m.delivery_code
        FROM customer_supplier_mappings m
        LEFT JOIN business_locations b ON m.customer_id = b.id
        LEFT JOIN suppliers s ON m.supplier_id = s.id
        ORDER BY b.site_name, s.name
        LIMIT 10
    """)

    print("\n매핑 데이터 샘플:")
    for row in cursor.fetchall():
        customer = row[1] if row[1] else f"ID:{row[0]}"
        supplier = row[2] if row[2] else "Unknown"
        print(f"  {customer} ← → {supplier} (코드: {row[3]})")

    conn.close()
    print("✓ 매핑 데이터 확인 완료")

if __name__ == '__main__':
    print("=" * 50)
    print("데이터베이스 인코딩 수정 시작")
    print("=" * 50)

    try:
        fix_business_locations()
        fix_suppliers()
        verify_mapping_data()

        print("\n" + "=" * 50)
        print("✅ 모든 작업 완료!")
        print("=" * 50)

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()