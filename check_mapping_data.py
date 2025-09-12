#!/usr/bin/env python3
"""
협력업체 매핑 데이터 확인 스크립트
"""
import sqlite3
from datetime import datetime

def check_mapping_data():
    """협력업체 매핑 데이터 조회"""
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        # 매핑 테이블 존재 여부 확인
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name LIKE '%mapping%'
        """)
        tables = cursor.fetchall()
        print("매핑 관련 테이블:", tables)
        
        # customer_supplier_mappings 테이블 데이터 확인
        try:
            cursor.execute("""
                SELECT 
                    csm.id,
                    csm.customer_id,
                    csm.supplier_id,
                    c.name as customer_name,
                    s.name as supplier_name,
                    csm.delivery_code,
                    csm.is_active,
                    csm.is_primary_supplier,
                    csm.priority_order,
                    csm.contract_start_date,
                    csm.contract_end_date,
                    csm.notes,
                    csm.created_at
                FROM customer_supplier_mappings csm
                LEFT JOIN customers c ON csm.customer_id = c.id
                LEFT JOIN suppliers s ON csm.supplier_id = s.id
                ORDER BY csm.id
            """)
            
            mappings = cursor.fetchall()
            print(f"\n실제 매핑 데이터 ({len(mappings)}개):")
            print("="*80)
            
            if mappings:
                for mapping in mappings:
                    print(f"ID: {mapping[0]}")
                    print(f"  사업장: {mapping[3]} (ID: {mapping[1]})")
                    print(f"  협력업체: {mapping[4]} (ID: {mapping[2]})")
                    print(f"  배송코드: {mapping[5]}")
                    print(f"  활성상태: {'활성' if mapping[6] else '비활성'}")
                    print(f"  주 협력업체: {'예' if mapping[7] else '아니오'}")
                    print(f"  우선순위: {mapping[8]}")
                    print(f"  계약기간: {mapping[9]} ~ {mapping[10]}")
                    print(f"  비고: {mapping[11]}")
                    print(f"  생성일: {mapping[12]}")
                    print("-" * 60)
            else:
                print("매핑 데이터가 없습니다.")
                
        except sqlite3.Error as e:
            print(f"매핑 테이블 조회 오류: {e}")
        
        # 사업장 목록 확인 (사업장 관리에 등록된 것들)
        try:
            cursor.execute("""
                SELECT id, name, code, is_active, created_at 
                FROM customers 
                ORDER BY id
            """)
            customers = cursor.fetchall()
            print(f"\n사업장 관리에 등록된 사업장 ({len(customers)}개):")
            for customer in customers:
                status = "활성" if customer[3] else "비활성"
                print(f"  ID {customer[0]}: {customer[1]} ({customer[2]}) - {status} - 등록일: {customer[4]}")
        except sqlite3.Error as e:
            print(f"사업장 조회 오류: {e}")
            
        # 매핑에만 있는 사업장 ID 확인 (등록되지 않은 이상한 사업장 찾기)
        try:
            cursor.execute("""
                SELECT DISTINCT csm.customer_id, csm.supplier_id
                FROM customer_supplier_mappings csm
                LEFT JOIN customers c ON csm.customer_id = c.id
                WHERE c.id IS NULL
            """)
            orphan_mappings = cursor.fetchall()
            if orphan_mappings:
                print(f"\n⚠️  등록되지 않은 사업장 ID가 매핑에 있음 ({len(orphan_mappings)}개):")
                for mapping in orphan_mappings:
                    print(f"  사업장 ID {mapping[0]} - 협력업체 ID {mapping[1]}")
            else:
                print(f"\n✅ 모든 매핑이 등록된 사업장과 연결됨")
        except sqlite3.Error as e:
            print(f"고아 매핑 조회 오류: {e}")
            
        # 협력업체 목록 확인  
        try:
            cursor.execute("SELECT id, name FROM suppliers ORDER BY id")
            suppliers = cursor.fetchall()
            print(f"\n협력업체 목록 ({len(suppliers)}개):")
            for supplier in suppliers:
                print(f"  {supplier[0]}: {supplier[1]}")
        except sqlite3.Error as e:
            print(f"협력업체 조회 오류: {e}")
            
        conn.close()
        
    except sqlite3.Error as e:
        print(f"데이터베이스 연결 오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")

if __name__ == "__main__":
    check_mapping_data()