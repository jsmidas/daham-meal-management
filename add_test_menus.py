#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
테스트용 메뉴 데이터 추가 스크립트
"""

import sqlite3
import datetime

def add_test_menus():
    """테스트용 메뉴 데이터를 데이터베이스에 추가"""

    # 데이터베이스 연결
    conn = sqlite3.connect('backups/daham_meal.db')
    cursor = conn.cursor()

    # 테스트 메뉴 데이터
    test_menus = [
        {
            'menu_name': '김치찌개',
            'category': '찌개',
            'cooking_note': '김치를 충분히 볶아서 깊은 맛을 내는 것이 포인트입니다.',
            'serving_size': 4,
            'total_cost': 3500,
            'created_by': 'dev_user',
            'creator_organization': '테스트푸드'
        },
        {
            'menu_name': '된장찌개',
            'category': '찌개',
            'cooking_note': '된장은 체에 한번 걸러서 사용하면 더 깔끔한 맛이 납니다.',
            'serving_size': 4,
            'total_cost': 2800,
            'created_by': 'dev_user',
            'creator_organization': '테스트푸드'
        },
        {
            'menu_name': '제육볶음',
            'category': '볶음',
            'cooking_note': '고기는 미리 양념에 재워두었다가 볶으면 더 맛있습니다.',
            'serving_size': 4,
            'total_cost': 4500,
            'created_by': 'dev_user',
            'creator_organization': '테스트푸드'
        },
        {
            'menu_name': '미역국',
            'category': '국',
            'cooking_note': '미역은 찬물에 충분히 불려서 사용해야 합니다.',
            'serving_size': 4,
            'total_cost': 2000,
            'created_by': 'dev_user',
            'creator_organization': '테스트푸드'
        },
        {
            'menu_name': '비빔밥',
            'category': '밥',
            'cooking_note': '나물들은 각각 따로 조리해서 색깔과 맛을 살려주세요.',
            'serving_size': 4,
            'total_cost': 5000,
            'created_by': 'dev_user',
            'creator_organization': '테스트푸드'
        }
    ]

    # 기존 테스트 데이터 삭제 (있다면)
    cursor.execute("DELETE FROM menu_recipes WHERE created_by = 'dev_user'")

    # 테스트 메뉴 추가
    for menu in test_menus:
        cursor.execute("""
            INSERT INTO menu_recipes (
                menu_name, category, cooking_note,
                serving_size, total_cost, is_active, created_by,
                creator_organization, created_at, updated_at, has_photo
            ) VALUES (?, ?, ?, ?, ?, 1, ?, ?, datetime('now'), datetime('now'), 0)
        """, (
            menu['menu_name'],
            menu['category'],
            menu['cooking_note'],
            menu['serving_size'],
            menu['total_cost'],
            menu['created_by'],
            menu['creator_organization']
        ))

        print(f"추가됨: {menu['menu_name']}")

    # 변경사항 저장
    conn.commit()

    # 결과 확인
    cursor.execute("SELECT COUNT(*) FROM menu_recipes WHERE is_active = 1")
    count = cursor.fetchone()[0]
    print(f"\n총 활성 메뉴 수: {count}개")

    # 추가된 메뉴 목록 출력
    cursor.execute("""
        SELECT menu_name, category, total_cost
        FROM menu_recipes
        WHERE is_active = 1
        ORDER BY id DESC
        LIMIT 10
    """)

    print("\n최근 추가된 메뉴:")
    for row in cursor.fetchall():
        print(f"- {row[0]} ({row[1]}) - {row[2]:,}원")

    conn.close()
    print("\n테스트 메뉴 추가 완료!")

if __name__ == "__main__":
    add_test_menus()