#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 연결 상태 체크 스크립트
"""
import requests
import json
import time

def check_api_status():
    """API 연결 상태 및 데이터 확인"""
    api_url = "http://127.0.0.1:8006/all-ingredients-for-suppliers"
    
    print("🔍 API 연결 상태 체크")
    print("=" * 50)
    
    try:
        # API 연결 테스트
        print("📡 API 서버 연결 테스트...")
        start_time = time.time()
        response = requests.get(f"{api_url}?limit=1", timeout=5)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ API 연결 성공! (응답시간: {response_time:.2f}초)")
            
            data = response.json()
            if data.get('success'):
                print(f"✅ 데이터 로드 성공!")
                
                # supplier_stats 확인
                supplier_stats = data.get('supplier_stats', {})
                print(f"📊 업체별 현황 ({len(supplier_stats)}개 업체):")
                for supplier, count in list(supplier_stats.items())[:5]:
                    print(f"   - {supplier}: {count:,}개")
                
                # 전체 통계
                total_ingredients = data.get('total_ingredients', 0)
                total_suppliers = data.get('total_suppliers', 0)
                print(f"📈 총 식자재: {total_ingredients:,}개")
                print(f"🏢 총 공급업체: {total_suppliers}개")
                
                print("\n🎯 주요 엔드포인트:")
                print(f"   - 전체 데이터: {api_url}")
                print(f"   - 삼성웰스토리: http://127.0.0.1:8006/test-samsung-welstory")
                print(f"   - CJ 특정: http://127.0.0.1:8006/supplier-ingredients/CJ")
                
                return True
            else:
                print("❌ API 응답 실패:", data.get('message', '알 수 없는 오류'))
                
        else:
            print(f"❌ API 연결 실패 (Status: {response.status_code})")
            
    except requests.exceptions.ConnectionError:
        print("❌ 연결 실패: API 서버가 실행되지 않았습니다.")
        print("💡 해결방법: python test_samsung_api.py 실행")
    except requests.exceptions.Timeout:
        print("❌ 타임아웃: API 응답 시간 초과")
        print("💡 해결방법: 서버 재시작 또는 데이터베이스 확인")
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {str(e)}")
    
    return False

def check_database():
    """데이터베이스 상태 확인"""
    try:
        import sqlite3
        print("\n🗄️ 데이터베이스 상태 체크")
        print("=" * 50)
        
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        # 테이블 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 테이블 수: {len(tables)}개")
        
        # 식자재 개수 확인
        cursor.execute("SELECT COUNT(*) FROM ingredients")
        total_ingredients = cursor.fetchone()[0]
        print(f"📊 총 식자재: {total_ingredients:,}개")
        
        # 공급업체별 통계
        cursor.execute("""
            SELECT supplier_name, COUNT(*) 
            FROM ingredients 
            WHERE supplier_name IS NOT NULL AND supplier_name != ''
            GROUP BY supplier_name 
            ORDER BY COUNT(*) DESC 
            LIMIT 5
        """)
        
        suppliers = cursor.fetchall()
        print(f"🏢 상위 공급업체:")
        for supplier, count in suppliers:
            print(f"   - {supplier}: {count:,}개")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 오류: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 다함 식자재 관리 시스템 - API 상태 체크")
    print("=" * 60)
    
    api_ok = check_api_status()
    db_ok = check_database()
    
    print("\n" + "=" * 60)
    if api_ok and db_ok:
        print("🎉 모든 시스템이 정상 작동 중입니다!")
        print("🌐 브라우저에서 ingredients_management.html을 열어주세요.")
    else:
        print("⚠️ 일부 시스템에 문제가 있습니다.")
        print("📖 자세한 해결방법은 API_QUICK_START_GUIDE.md를 참조하세요.")