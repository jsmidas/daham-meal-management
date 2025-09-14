#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3

def fix_business_locations():
    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()

    # 사업장 이름 수정
    updates = [
        (1, '학교'),
        (2, '도시락'),
        (3, '운반'),
        (4, '요양원')
    ]

    for id, name in updates:
        cursor.execute('UPDATE business_locations SET site_name = ? WHERE id = ?', (name, id))
        print(f'Updated ID {id}: {name}')

    conn.commit()

    # 확인
    cursor.execute('SELECT id, site_name FROM business_locations')
    print('\n업데이트 후 데이터:')
    for row in cursor.fetchall():
        print(f'ID: {row[0]}, Name: {row[1]}')

    conn.close()

def fix_suppliers():
    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()

    # 협력업체 이름 수정
    updates = [
        (1, '씨제이'),
        (2, '웰스토리'),
        (3, '동원홈푸드'),
        (4, '싱싱닭고기'),
        (5, '푸디스트'),
        (6, '현대그린푸드'),
        (7, '영유통')
    ]

    for id, name in updates:
        cursor.execute('UPDATE suppliers SET name = ? WHERE id = ?', (name, id))
        print(f'Updated Supplier ID {id}: {name}')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    print('데이터베이스 인코딩 수정 시작...\n')
    fix_business_locations()
    print('\n')
    fix_suppliers()
    print('\n인코딩 수정 완료!')