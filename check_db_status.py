#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def check_database():
    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()

    print("=== 현재 활성화된 메뉴 목록 ===")
    cursor.execute("SELECT id, recipe_name, category, is_active FROM menu_recipes WHERE is_active = 1")
    menus = cursor.fetchall()

    for menu in menus:
        print(f"ID: {menu[0]}, 이름: {menu[1]}, 카테고리: {menu[2]}")

    print(f"\n총 {len(menus)}개의 활성화된 메뉴가 있습니다.")

    print("\n=== 각 메뉴별 재료 개수 확인 ===")
    for menu in menus:
        menu_id = menu[0]
        menu_name = menu[1]

        cursor.execute("SELECT COUNT(*) FROM menu_recipe_ingredients WHERE recipe_id = ?", (menu_id,))
        ingredient_count = cursor.fetchone()[0]

        print(f"메뉴 '{menu_name}' (ID: {menu_id}): {ingredient_count}개 재료")

        if ingredient_count == 0:
            print(f"  → 빈 메뉴입니다. 삭제 대상!")

    conn.close()

if __name__ == "__main__":
    check_database()