#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
식단가 관리 API 엔드포인트 추가 스크립트
test_samsung_api.py에 추가할 코드
"""

meal_pricing_api_code = '''
@app.get("/api/admin/meal-pricing")
async def get_meal_pricing():
    """식단가 목록 조회"""
    try:
        conn = sqlite3.connect('daham_meal.db')
        conn.text_factory = str
        cursor = conn.cursor()

        # 식단가 데이터 조회
        cursor.execute("""
            SELECT
                id, location_id, location_name, meal_plan_type, meal_type,
                plan_name, apply_date_start, apply_date_end, selling_price,
                material_cost_guideline, cost_ratio, is_active, created_at
            FROM meal_pricing
            ORDER BY location_name, meal_plan_type, meal_type
        """)

        meal_pricing = []
        for row in cursor.fetchall():
            meal_pricing.append({
                "id": row[0],
                "location_id": row[1],
                "location_name": row[2],
                "meal_plan_type": row[3],
                "meal_type": row[4],
                "plan_name": row[5],
                "apply_date_start": row[6],
                "apply_date_end": row[7],
                "selling_price": float(row[8] or 0),
                "material_cost_guideline": float(row[9] or 0),
                "cost_ratio": float(row[10] or 0),
                "is_active": bool(row[11]),
                "created_at": row[12]
            })

        # 통계 계산
        total = len(meal_pricing)
        active = sum(1 for mp in meal_pricing if mp["is_active"])
        locations = len(set(mp["location_name"] for mp in meal_pricing))

        avg_selling_price = 0
        avg_cost_ratio = 0
        if meal_pricing:
            avg_selling_price = sum(mp["selling_price"] for mp in meal_pricing) / len(meal_pricing)
            avg_cost_ratio = sum(mp["cost_ratio"] for mp in meal_pricing) / len(meal_pricing)

        conn.close()

        return {
            "success": True,
            "meal_pricing": meal_pricing,
            "statistics": {
                "total": total,
                "active": active,
                "locations": locations,
                "avg_selling_price": avg_selling_price,
                "avg_cost_ratio": avg_cost_ratio
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/meal-pricing")
async def create_meal_pricing(data: dict):
    """식단가 추가"""
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO meal_pricing (
                location_id, location_name, meal_plan_type, meal_type,
                plan_name, apply_date_start, apply_date_end, selling_price,
                material_cost_guideline, cost_ratio, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            data.get("location_id"),
            data.get("location_name"),
            data.get("meal_plan_type"),
            data.get("meal_type"),
            data.get("plan_name"),
            data.get("apply_date_start"),
            data.get("apply_date_end"),
            data.get("selling_price"),
            data.get("material_cost_guideline"),
            data.get("cost_ratio", 50),
            data.get("is_active", 1)
        ))

        conn.commit()
        new_id = cursor.lastrowid
        conn.close()

        return {"success": True, "id": new_id}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/admin/meal-pricing/{pricing_id}")
async def update_meal_pricing(pricing_id: int, data: dict):
    """식단가 수정"""
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE meal_pricing SET
                location_name = ?,
                meal_plan_type = ?,
                meal_type = ?,
                plan_name = ?,
                apply_date_start = ?,
                apply_date_end = ?,
                selling_price = ?,
                material_cost_guideline = ?,
                cost_ratio = ?,
                is_active = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (
            data.get("location_name"),
            data.get("meal_plan_type"),
            data.get("meal_type"),
            data.get("plan_name"),
            data.get("apply_date_start"),
            data.get("apply_date_end"),
            data.get("selling_price"),
            data.get("material_cost_guideline"),
            data.get("cost_ratio"),
            data.get("is_active"),
            pricing_id
        ))

        conn.commit()
        conn.close()

        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/admin/meal-pricing/{pricing_id}")
async def delete_meal_pricing(pricing_id: int):
    """식단가 삭제"""
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()

        cursor.execute("DELETE FROM meal_pricing WHERE id = ?", (pricing_id,))

        conn.commit()
        conn.close()

        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}
'''

print("=" * 60)
print("식단가 관리 API 엔드포인트 코드")
print("=" * 60)
print()
print("아래 코드를 test_samsung_api.py의 적절한 위치에 추가하세요:")
print()
print(meal_pricing_api_code)
print()
print("=" * 60)
print("추가 위치: customer-supplier-mappings 엔드포인트 아래")
print("=" * 60)