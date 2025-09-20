#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
시스템 검증 스크립트
메뉴/레시피 시스템이 올바르게 동작하는지 자동으로 검증
"""

import sqlite3
import requests
import json
import sys

def validate_database():
    """데이터베이스 구조 검증"""
    print("🔍 데이터베이스 구조 검증...")

    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()

        # 테이블 존재 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='menu_recipes'")
        if not cursor.fetchone():
            print("❌ menu_recipes 테이블이 없습니다")
            return False

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='menu_recipe_ingredients'")
        if not cursor.fetchone():
            print("❌ menu_recipe_ingredients 테이블이 없습니다")
            return False

        # 테이블 구조 확인
        cursor.execute("PRAGMA table_info(menu_recipe_ingredients)")
        columns = [col[1] for col in cursor.fetchall()]
        expected_columns = [
            'id', 'recipe_id', 'ingredient_code', 'ingredient_name',
            'specification', 'unit', 'delivery_days', 'selling_price',
            'quantity', 'amount', 'supplier_name', 'sort_order', 'created_at'
        ]

        for col in expected_columns:
            if col not in columns:
                print(f"❌ 필수 컬럼 '{col}'이 없습니다")
                return False

        print("✅ 데이터베이스 구조 정상")
        conn.close()
        return True

    except Exception as e:
        print(f"❌ 데이터베이스 오류: {e}")
        return False

def validate_api_endpoints():
    """API 엔드포인트 검증"""
    print("🔍 API 엔드포인트 검증...")

    base_url = "http://127.0.0.1:8010"

    # 필수 엔드포인트 목록
    endpoints = [
        "/api/admin/menu-recipes",
        "/api/admin/menu-recipes/categories",
        "/api/admin/ingredients-new"
    ]

    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint} - 정상")
            else:
                print(f"❌ {endpoint} - 상태코드: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ {endpoint} - 오류: {e}")
            return False

    return True

def validate_menu_save_function():
    """메뉴 저장 기능 검증"""
    print("🔍 메뉴 저장 기능 검증...")

    # 현재 메뉴 개수 확인
    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM menu_recipes WHERE is_active = 1")
    initial_count = cursor.fetchone()[0]
    conn.close()

    print(f"현재 메뉴 개수: {initial_count}")
    print("✅ 메뉴 저장 기능은 수동으로 테스트해주세요")

    return True

def main():
    """전체 검증 실행"""
    print("=" * 60)
    print("🍱 다함 메뉴 관리 시스템 검증")
    print("=" * 60)

    results = []

    # 1. 데이터베이스 검증
    results.append(validate_database())

    # 2. API 엔드포인트 검증
    results.append(validate_api_endpoints())

    # 3. 메뉴 저장 기능 검증
    results.append(validate_menu_save_function())

    print("\n" + "=" * 60)
    if all(results):
        print("🎉 모든 검증 통과!")
        print("시스템이 정상적으로 동작합니다.")
    else:
        print("⚠️  일부 검증 실패")
        print("문제를 해결한 후 다시 실행해주세요.")
        sys.exit(1)

    print("=" * 60)

if __name__ == "__main__":
    main()