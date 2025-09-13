#!/usr/bin/env python3
"""
식단가 테이블의 전체 데이터 확인
"""
import sqlite3

def check_meal_pricing_data():
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        print("=== meal_pricing 테이블 전체 데이터 ===")
        cursor.execute("SELECT * FROM meal_pricing ORDER BY id")
        all_pricing = cursor.fetchall()
        
        print(f"전체 식단가 데이터: {len(all_pricing)}개")
        
        for pricing in all_pricing:
            print(f"ID {pricing[0]}: {pricing[2]}({pricing[1]}) - {pricing[4]} - {pricing[5]}")
            print(f"  적용기간: {pricing[6]} ~ {pricing[7]}")
            print(f"  판매가격: {pricing[8]:,}원, 원가가이드: {pricing[9]:,}원, 원가비율: {pricing[10]}%")
            print(f"  활성: {pricing[11]}, 생성일: {pricing[12]}")
            print()
            
        conn.close()
        
    except sqlite3.Error as e:
        print(f"데이터베이스 오류: {e}")

if __name__ == "__main__":
    check_meal_pricing_data()