#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 연결 상태 간단 체크 스크립트 (윈도우 호환)
"""
import requests
import sqlite3

def check_api_status():
    """API 연결 상태 확인"""
    api_url = "http://127.0.0.1:8006/all-ingredients-for-suppliers"
    
    print("=== API 연결 상태 체크 ===")
    
    try:
        response = requests.get(f"{api_url}?limit=1", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✓ API 연결 성공!")
                
                supplier_stats = data.get('supplier_stats', {})
                print(f"✓ 업체 수: {len(supplier_stats)}개")
                
                for supplier, count in list(supplier_stats.items())[:3]:
                    print(f"  - {supplier}: {count:,}개")
                
                return True
            
    except Exception as e:
        print(f"✗ API 연결 실패: {str(e)}")
        print("해결방법: python test_samsung_api.py 실행")
    
    return False

def check_database():
    """데이터베이스 상태 확인"""
    try:
        print("\n=== 데이터베이스 체크 ===")
        
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM ingredients")
        total = cursor.fetchone()[0]
        print(f"✓ 총 식자재: {total:,}개")
        
        cursor.execute("""
            SELECT supplier_name, COUNT(*) 
            FROM ingredients 
            WHERE supplier_name IS NOT NULL 
            GROUP BY supplier_name 
            ORDER BY COUNT(*) DESC 
            LIMIT 3
        """)
        
        suppliers = cursor.fetchall()
        print("✓ 상위 공급업체:")
        for supplier, count in suppliers:
            print(f"  - {supplier}: {count:,}개")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ 데이터베이스 오류: {str(e)}")
        return False

if __name__ == "__main__":
    print("다함 식자재 관리 시스템 - 상태 체크")
    print("=" * 50)
    
    api_ok = check_api_status()
    db_ok = check_database()
    
    print("\n" + "=" * 50)
    if api_ok and db_ok:
        print("모든 시스템 정상!")
        print("브라우저에서 ingredients_management.html 열어주세요.")
    else:
        print("시스템 점검 필요")
        print("자세한 내용은 API_QUICK_START_GUIDE.md 참조")