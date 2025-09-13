import sqlite3
import json

# 데이터베이스 연결
conn = sqlite3.connect('daham_meal.db')
cursor = conn.cursor()

# customer_supplier_mappings 테이블에서 실제 데이터 조회
query = """
SELECT
    m.id,
    m.customer_id,
    m.supplier_id,
    m.delivery_code,
    m.is_active,
    m.created_at,
    s.name as supplier_name,
    b.name as customer_name
FROM customer_supplier_mappings m
LEFT JOIN suppliers s ON m.supplier_id = s.id
LEFT JOIN business_locations b ON m.customer_id = b.id
LIMIT 10
"""

cursor.execute(query)
mappings = cursor.fetchall()

print("=== 실제 customer_supplier_mappings 데이터 ===")
print("-" * 50)

for mapping in mappings:
    print(f"ID: {mapping[0]}")
    print(f"고객: {mapping[7]} (ID: {mapping[1]})")
    print(f"공급업체: {mapping[6]} (ID: {mapping[2]})")
    print(f"배송코드: {mapping[3]}")
    print(f"활성상태: {'활성' if mapping[4] else '비활성'}")
    print(f"생성일: {mapping[5]}")
    print("-" * 50)

# JavaScript 배열 형식으로 출력
print("\n=== JavaScript 배열 형식 ===")
js_mappings = []
for mapping in mappings:
    js_mappings.append({
        'id': mapping[0],
        'customer_name': mapping[7] or '알 수 없음',
        'supplier_name': mapping[6] or '알 수 없음',
        'delivery_code': mapping[3] or '',
        'is_active': bool(mapping[4])
    })

print(json.dumps(js_mappings, ensure_ascii=False, indent=2))

conn.close()