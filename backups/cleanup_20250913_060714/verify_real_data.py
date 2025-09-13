#!/usr/bin/env python3
"""
실제 등록된 사업장과 협력업체 데이터 vs 매핑 데이터 비교
"""
import sqlite3

def verify_data():
    """실제 등록 데이터와 매핑 데이터 비교"""
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        print("=== 실제 등록된 사업장 vs 매핑의 사업장 비교 ===")
        
        # 1. 실제 등록된 사업장 (사업장 관리에서 보이는 것)
        cursor.execute("""
            SELECT id, name, code, is_active 
            FROM customers 
            WHERE is_active = 1
            ORDER BY id
        """)
        real_customers = cursor.fetchall()
        print(f"\n[사업장] 사업장 관리에 등록된 활성 사업장 ({len(real_customers)}개):")
        for customer in real_customers:
            print(f"  ID {customer[0]}: {customer[1]} (코드: {customer[2]})")
            
        # 2. 실제 등록된 협력업체 (협력업체 관리에서 보이는 것)
        cursor.execute("""
            SELECT id, name, parent_code, is_active, business_number
            FROM suppliers 
            WHERE is_active = 1
            ORDER BY id
        """)
        real_suppliers = cursor.fetchall()
        print(f"\n[협력업체] 협력업체 관리에 등록된 활성 협력업체 ({len(real_suppliers)}개):")
        for supplier in real_suppliers:
            print(f"  ID {supplier[0]}: {supplier[1]} (코드: {supplier[2]}) - 사업자: {supplier[4]}")
            
        # 3. 매핑에서 사용된 사업장 확인
        cursor.execute("""
            SELECT DISTINCT csm.customer_id, c.name
            FROM customer_supplier_mappings csm
            LEFT JOIN customers c ON csm.customer_id = c.id
            ORDER BY csm.customer_id
        """)
        mapped_customers = cursor.fetchall()
        print(f"\n[매핑확인] 매핑에서 사용된 사업장 ({len(mapped_customers)}개):")
        for customer in mapped_customers:
            status = "OK-등록됨" if customer[0] in [c[0] for c in real_customers] else "NG-미등록"
            print(f"  ID {customer[0]}: {customer[1]} - {status}")
            
        # 4. 매핑에서 사용된 협력업체 확인
        cursor.execute("""
            SELECT DISTINCT csm.supplier_id, s.name
            FROM customer_supplier_mappings csm
            LEFT JOIN suppliers s ON csm.supplier_id = s.id
            ORDER BY csm.supplier_id
        """)
        mapped_suppliers = cursor.fetchall()
        print(f"\n[매핑확인] 매핑에서 사용된 협력업체 ({len(mapped_suppliers)}개):")
        for supplier in mapped_suppliers:
            status = "OK-등록됨" if supplier[0] in [s[0] for s in real_suppliers] else "NG-미등록"
            print(f"  ID {supplier[0]}: {supplier[1]} - {status}")
            
        # 5. 더미 데이터 식별
        real_customer_ids = set(c[0] for c in real_customers)
        real_supplier_ids = set(s[0] for s in real_suppliers)
        mapped_customer_ids = set(c[0] for c in mapped_customers)
        mapped_supplier_ids = set(s[0] for s in mapped_suppliers)
        
        dummy_customers = mapped_customer_ids - real_customer_ids
        dummy_suppliers = mapped_supplier_ids - real_supplier_ids
        
        print(f"\n[결론] 더미 데이터 식별:")
        if dummy_customers:
            print(f"  더미 사업장 ID: {dummy_customers}")
        if dummy_suppliers:
            print(f"  더미 협력업체 ID: {dummy_suppliers}")
            
        if not dummy_customers and not dummy_suppliers:
            print("  OK: 더미 데이터 없음 - 모든 매핑이 실제 등록된 데이터")
        else:
            print(f"  NG: 더미 데이터 발견 - 사업장: {len(dummy_customers)}개, 협력업체: {len(dummy_suppliers)}개")
            
        # 6. 구체적인 더미 매핑 조회
        if dummy_customers or dummy_suppliers:
            print(f"\n[더미매핑] 더미 데이터를 사용한 매핑:")
            cursor.execute("""
                SELECT 
                    csm.id,
                    csm.customer_id,
                    c.name as customer_name,
                    csm.supplier_id,
                    s.name as supplier_name,
                    csm.delivery_code
                FROM customer_supplier_mappings csm
                LEFT JOIN customers c ON csm.customer_id = c.id
                LEFT JOIN suppliers s ON csm.supplier_id = s.id
                WHERE csm.customer_id NOT IN (
                    SELECT id FROM customers WHERE is_active = 1
                ) OR csm.supplier_id NOT IN (
                    SELECT id FROM suppliers WHERE is_active = 1
                )
                ORDER BY csm.id
            """)
            dummy_mappings = cursor.fetchall()
            for mapping in dummy_mappings:
                print(f"  매핑 ID {mapping[0]}: 사업장 {mapping[1]}({mapping[2]}) ↔ 협력업체 {mapping[3]}({mapping[4]}) - {mapping[5]}")
                
        conn.close()
        
    except sqlite3.Error as e:
        print(f"데이터베이스 오류: {e}")
    except Exception as e:
        print(f"예상치 못한 오류: {e}")

if __name__ == "__main__":
    verify_data()