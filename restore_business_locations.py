#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3
from datetime import datetime

def restore_business_locations():
    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()

    # 샘플 사업장 데이터 생성
    sample_sites = [
        ('HQ001', '다함 본사', 'headquarters', '서울', '서울시 강남구 테헤란로 123', '02-1234-5678', '02-1234-5679', '김관리', '010-1234-5678', 'manager1@daham.co.kr', '08:00-18:00', 200, 'central_kitchen', '본사 중앙 주방', True),
        ('BR001', '서울 강남지점', 'branch', '서울', '서울시 강남구 역삼로 456', '02-2345-6789', '02-2345-6790', '이지점', '010-2345-6789', 'gangnam@daham.co.kr', '07:00-19:00', 150, 'branch_kitchen', '강남 지역 주요 지점', True),
        ('BR002', '서울 마포지점', 'branch', '서울', '서울시 마포구 홍익로 789', '02-3456-7890', '02-3456-7891', '박지점', '010-3456-7890', 'mapo@daham.co.kr', '07:30-18:30', 120, 'small_kitchen', '홍대 인근 지점', True),
        ('BR003', '부산 해운대지점', 'branch', '부산', '부산시 해운대구 센텀로 321', '051-1234-5678', '051-1234-5679', '최부산', '010-4567-8901', 'busan@daham.co.kr', '07:00-19:00', 180, 'branch_kitchen', '부산 주요 지점', True),
        ('ST001', '인천 송도지점', 'satellite', '인천', '인천시 연수구 송도대로 654', '032-5678-9012', '032-5678-9013', '정송도', '010-5678-9012', 'songdo@daham.co.kr', '08:00-17:00', 80, 'small_kitchen', '송도신도시 지점', True),
    ]

    current_time = datetime.now().isoformat()

    for site in sample_sites:
        cursor.execute('''
            INSERT INTO business_locations 
            (site_code, site_name, site_type, region, address, phone, fax, manager_name, 
             manager_phone, manager_email, operating_hours, meal_capacity, kitchen_type, 
             special_notes, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', site + (current_time, current_time))

    conn.commit()
    
    # 결과 확인
    cursor.execute('SELECT COUNT(*) FROM business_locations')
    count = cursor.fetchone()[0]
    print(f'사업장 데이터 복구 완료: {count}개')

    # 생성된 데이터 확인
    cursor.execute('SELECT site_code, site_name, site_type FROM business_locations')
    sites = cursor.fetchall()
    print('\n생성된 사업장:')
    for site in sites:
        print(f'  - {site[0]}: {site[1]} ({site[2]})')

    conn.close()
    return count

if __name__ == '__main__':
    restore_business_locations()