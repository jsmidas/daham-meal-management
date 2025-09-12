#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3

def check_backup_database():
    """백업 데이터베이스의 meal_pricing 데이터를 확인합니다."""
    
    try:
        conn = sqlite3.connect('backups/daham_meal_backup_20250911_final.db')
        cursor = conn.cursor()
        
        print("=== 백업 DB meal_pricing 테이블 데이터 ===\n")
        
        cursor.execute("""
            SELECT id, location_id, location_name, meal_plan_type, meal_type, 
                   plan_name, apply_date_start, apply_date_end, selling_price,
                   material_cost_guideline, is_active
            FROM meal_pricing 
            ORDER BY location_name, meal_type
        """)
        meal_pricing = cursor.fetchall()
        
        if meal_pricing:
            print(f"백업 DB에 {len(meal_pricing)}개의 meal_pricing 레코드:")
            print()
            for i, pricing in enumerate(meal_pricing, 1):
                print(f"{i}. ID: {pricing[0]}")
                print(f"   장소ID: {pricing[1]}")
                print(f"   장소명: {pricing[2]}")
                print(f"   식단계획타입: {pricing[3]}")
                print(f"   식사타입: {pricing[4]}")
                print(f"   플랜명: {pricing[5]}")
                print(f"   시작일: {pricing[6]}")
                print(f"   종료일: {pricing[7]}")
                print(f"   판매가: {pricing[8]}")
                print(f"   재료비가이드: {pricing[9]}")
                print(f"   활성상태: {pricing[10]}")
                print()
        else:
            print("백업 DB에 meal_pricing 데이터가 없습니다.")
        
        conn.close()
        
    except Exception as e:
        print(f"백업 DB 확인 중 오류 발생: {e}")

if __name__ == "__main__":
    check_backup_database()