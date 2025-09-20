#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메뉴 데이터 확인용 스크립트
사용법: python check_menus.py
"""

import sqlite3
import json
from datetime import datetime

def check_menu_data():
    """메뉴 데이터 상세 조회"""
    print("=" * 60)
    print("🍱 다함 급식관리 시스템 - 메뉴 데이터 확인")
    print("=" * 60)

    try:
        # 데이터베이스 연결
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()

        # 1. 메뉴 통계
        cursor.execute("SELECT COUNT(*) FROM menu_recipes WHERE is_active = 1")
        total_menus = cursor.fetchone()[0]

        cursor.execute("SELECT category, COUNT(*) FROM menu_recipes WHERE is_active = 1 GROUP BY category")
        categories = cursor.fetchall()

        print(f"📊 메뉴 통계:")
        print(f"   총 메뉴 개수: {total_menus}개")
        print(f"   카테고리별 분포:")
        for cat, count in categories:
            print(f"     - {cat}: {count}개")

        print("\n" + "=" * 60)

        # 2. 메뉴 목록 (최신순)
        cursor.execute("""
            SELECT id, recipe_name, category, total_cost, created_at,
                   (SELECT COUNT(*) FROM menu_recipe_ingredients WHERE recipe_id = menu_recipes.id) as ingredient_count
            FROM menu_recipes
            WHERE is_active = 1
            ORDER BY updated_at DESC
        """)

        menus = cursor.fetchall()

        print("📋 메뉴 목록 (최신순):")
        print(f"{'ID':<4} {'메뉴명':<20} {'카테고리':<8} {'재료수':<6} {'비용':<8} {'생성일':<12}")
        print("-" * 70)

        for menu in menus:
            menu_id, name, category, cost, created_at, ingredient_count = menu
            cost_str = f"{cost:,}원" if cost else "미설정"
            created_date = created_at[:10] if created_at else "미설정"
            print(f"{menu_id:<4} {name:<20} {category:<8} {ingredient_count:<6} {cost_str:<8} {created_date:<12}")

        print("\n" + "=" * 60)

        # 3. 최근 생성된 메뉴 상세 정보
        cursor.execute("""
            SELECT id, recipe_name, category, cooking_note, total_cost
            FROM menu_recipes
            WHERE is_active = 1
            ORDER BY created_at DESC
            LIMIT 3
        """)

        recent_menus = cursor.fetchall()

        print("🔍 최근 메뉴 상세 정보 (Top 3):")

        for i, menu in enumerate(recent_menus, 1):
            menu_id, name, category, note, cost = menu
            print(f"\n{i}. {name} (ID: {menu_id})")
            print(f"   카테고리: {category}")
            print(f"   비용: {cost:,}원" if cost else "   비용: 미설정")
            print(f"   조리법: {note[:50]}..." if note and len(note) > 50 else f"   조리법: {note or '미설정'}")

            # 재료 정보
            cursor.execute("""
                SELECT ingredient_name, specification, quantity, amount, supplier_name
                FROM menu_recipe_ingredients
                WHERE recipe_id = ?
                ORDER BY sort_order
            """, (menu_id,))

            ingredients = cursor.fetchall()
            if ingredients:
                print(f"   재료 ({len(ingredients)}개):")
                for ing in ingredients[:3]:  # 최대 3개만 표시
                    ing_name, spec, qty, amount, supplier = ing
                    print(f"     - {ing_name} {spec} {qty}개 ({amount:,}원)" if amount else f"     - {ing_name} {spec} {qty}개")
                if len(ingredients) > 3:
                    print(f"     ... 외 {len(ingredients)-3}개")
            else:
                print("   재료: 없음")

        print("\n" + "=" * 60)
        print("✅ 메뉴 데이터 확인 완료!")
        print(f"📍 데이터베이스: {conn.execute('PRAGMA database_list').fetchall()[0][2]}")

        conn.close()

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    check_menu_data()