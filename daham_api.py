#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
삼성웰스토리 식자재 데이터 테스트 API
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json

app = FastAPI()

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

@app.get("/")
async def root():
    """API 서버 상태 확인"""
    return {
        "message": "다함 식자재 관리 API 서버가 정상 작동 중입니다",
        "status": "running",
        "port": 8000,
        "endpoints": [
            "/test-samsung-welstory",
            "/all-ingredients-for-suppliers"
        ]
    }

@app.get("/test-samsung-welstory")
async def test_samsung_welstory():
    """삼성웰스토리 식자재 데이터 직접 조회"""
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        # 삼성웰스토리 공급업체 정보 조회
        cursor.execute("""
            SELECT id, name, representative, headquarters_phone 
            FROM suppliers 
            WHERE name LIKE '%웰스토리%' OR name LIKE '%삼성%'
        """)
        supplier = cursor.fetchone()
        
        if not supplier:
            return {"success": False, "message": "삼성웰스토리 공급업체를 찾을 수 없습니다"}
        
        supplier_info = {
            "id": supplier[0],
            "name": supplier[1],
            "contact_person": supplier[2] or "미지정",
            "contact_phone": supplier[3] or "미지정"
        }
        
        # 식자재 데이터 조회
        cursor.execute("""
            SELECT ingredient_name, category, unit, selling_price, notes
            FROM ingredients 
            WHERE supplier_name LIKE '%웰스토리%' OR supplier_name LIKE '%삼성%'
            LIMIT 50
        """)
        
        ingredients_data = cursor.fetchall()
        
        ingredients = []
        for ing in ingredients_data:
            ingredients.append({
                "name": ing[0],
                "category": ing[1],
                "unit": ing[2],
                "cost_per_unit": float(ing[3]) if ing[3] else 0.0,
                "description": ing[4] or ""
            })
        
        # 전체 개수 조회
        cursor.execute("""
            SELECT COUNT(*) 
            FROM ingredients 
            WHERE supplier_name LIKE '%웰스토리%' OR supplier_name LIKE '%삼성%'
        """)
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "success": True,
            "supplier": supplier_info,
            "ingredients": ingredients,
            "total_count": total_count,
            "shown_count": len(ingredients)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/all-ingredients-for-suppliers")
async def get_all_ingredients_for_suppliers(page: int = 1, limit: int = 100, supplier_filter: str = None):
    """모든 식자재를 업체별로 그룹화해서 반환 (업체별 식자재 현황 박스용)"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        # 기본 WHERE 조건
        where_conditions = ["supplier_name IS NOT NULL", "supplier_name != ''"]
        params = []
        
        # 공급업체 필터 추가
        if supplier_filter:
            where_conditions.append("supplier_name LIKE ?")
            params.append(f"%{supplier_filter}%")
        
        # 전체 데이터 수 확인
        count_query = f"SELECT COUNT(*) FROM ingredients WHERE {' AND '.join(where_conditions)}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # 페이지네이션 계산
        offset = (page - 1) * limit
        total_pages = (total_count + limit - 1) // limit
        
        # 페이지 컬럼 구조에 맞춘 식자재 조회 (g당 단가 계산 포함)
        query = f"""
            SELECT 
                category,
                sub_category,
                ingredient_code,
                ingredient_name,
                origin,
                posting_status,
                specification,
                unit,
                tax_type,
                delivery_days,
                purchase_price,
                selling_price,
                supplier_name,
                notes,
                created_date,
                price_per_gram
            FROM ingredients 
            WHERE {' AND '.join(where_conditions)}
            ORDER BY supplier_name, ingredient_name
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        cursor.execute(query, params)
        
        ingredients_data = cursor.fetchall()
        
        # 데이터를 한국어 컬럼명으로 변환
        ingredients = []
        
        for row in ingredients_data:
            # g당 단가 계산
            price_per_gram = row[15] if row[15] is not None else 0.0
            if price_per_gram == 0.0 and row[11] is not None:  # selling_price가 있는 경우
                # 간단한 g당 단가 계산 (판매가를 기준으로)
                try:
                    selling_price = float(row[11])
                    # 단위가 g인 경우는 그대로, kg인 경우는 1000으로 나누기, EA인 경우는 대략 100g 추정
                    unit = row[7] or 'EA'
                    if 'g' in unit.lower() and 'kg' not in unit.lower():
                        # 이미 g 단위
                        price_per_gram = selling_price / 100  # 100g 기준으로 대략 계산
                    elif 'kg' in unit.lower():
                        price_per_gram = selling_price / 1000  # 1kg = 1000g
                    else:
                        # EA 단위는 대략 100g으로 추정
                        price_per_gram = selling_price / 100
                except:
                    price_per_gram = 0.0
            
            ingredient_dict = {
                '분류(대분류)': row[0] or '',
                '기본식자재(세분류)': row[1] or '',
                '고유코드': row[2] or '',
                '식자재명': row[3] or '',
                '원산지': row[4] or '',
                '게시유무': row[5] or '',
                '규격': row[6] or '',  # 페이지에서 찾는 컬럼명
                '단위': row[7] or '',  # 페이지에서 찾는 컬럼명
                '면세': row[8] or '',  # 페이지에서 찾는 컬럼명 (면세여부 아닌 면세)
                '선발주일': row[9] or '',  # 페이지에서 찾는 컬럼명
                '입고가': float(row[10]) if row[10] is not None else 0.0,
                '판매가': float(row[11]) if row[11] is not None else 0.0,
                '거래처명': row[12] or '',
                '비고': row[13] or '',
                '등록일': row[14] or '',
                'g당단가': round(price_per_gram, 2)
            }
            ingredients.append(ingredient_dict)
        
        # 업체별 통계
        cursor.execute("""
            SELECT 
                supplier_name,
                COUNT(*) as ingredient_count
            FROM ingredients 
            WHERE supplier_name IS NOT NULL AND supplier_name != ''
            GROUP BY supplier_name
            ORDER BY ingredient_count DESC
        """)
        
        supplier_stats = {}
        for row in cursor.fetchall():
            supplier_stats[row[0]] = row[1]
        
        conn.close()
        
        return {
            "success": True,
            "ingredients": ingredients,
            "supplier_stats": supplier_stats,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "items_per_page": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "total_ingredients": len(ingredients),
            "total_suppliers": len(supplier_stats)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/users")
async def get_admin_users():
    """관리자용 사용자 목록 조회"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, contact_info, role, is_active, created_at
            FROM users
            ORDER BY created_at DESC
        """)

        users_data = cursor.fetchall()
        users = []

        for user in users_data:
            users.append({
                "id": user[0],
                "username": user[1],
                "email": user[2],
                "role": user[3],
                "active": bool(user[4]),
                "created_at": user[5]
            })

        conn.close()

        return {
            "success": True,
            "users": users,
            "total": len(users)
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/users/stats")
async def get_users_stats():
    """사용자 통계 조회"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        active_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_users = cursor.fetchone()[0]

        conn.close()

        return {
            "success": True,  # user_management.html이 기대하는 필드 추가
            "stats": {
                "total_users": total_users,
                "active_users": active_users,
                "admin_users": admin_users,
                "inactive_users": total_users - active_users
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/users")
async def get_users(page: int = 1, limit: int = 10):
    """사용자 목록 조회 (페이징)"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()

        offset = (page - 1) * limit

        cursor.execute("""
            SELECT id, username, contact_info, role, is_active, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        users_data = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_count = cursor.fetchone()[0]

        users = []
        for user in users_data:
            users.append({
                "id": user[0],
                "username": user[1],
                "name": user[2] or user[1],
                "role": user[3] or "user",
                "isActive": bool(user[4]) if user[4] is not None else True,
                "createdAt": user[5] or ""
            })

        conn.close()

        return {
            "success": True,  # user_management.html이 기대하는 필드 추가
            "users": users,
            "pagination": {
                "current_page": page,
                "total_pages": (total_count + limit - 1) // limit,
                "has_prev": page > 1,
                "has_next": page < (total_count + limit - 1) // limit,
                "total_items": total_count,
                "items_per_page": limit
            }
        }

    except Exception as e:
        return {"error": str(e)}

@app.get("/api/admin/list-users-simple")
async def list_users_simple():
    """사용자 목록 조회 (단순화된 버전)"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, contact_info, role, is_active, created_at
            FROM users
            ORDER BY created_at DESC
        """)

        users_data = cursor.fetchall()
        users = []

        for user in users_data:
            users.append({
                "id": user[0],
                "username": user[1],
                "email": user[2] or "",
                "role": user[3] or "user",
                "active": bool(user[4]) if user[4] is not None else True,
                "created_at": user[5] or ""
            })

        conn.close()

        return {
            "success": True,
            "users": users,
            "total": len(users)
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/suppliers")
async def get_suppliers(page: int = 1, limit: int = 10, search: str = None):
    """협력업체 목록 조회 (페이징)"""
    try:
        # daham_meal.db 사용 (실제 suppliers 테이블이 있는 DB)
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()

        offset = (page - 1) * limit

        # Count query first
        if search:
            cursor.execute("""
                SELECT COUNT(*) FROM suppliers
                WHERE name LIKE ? OR parent_code LIKE ?
            """, (f'%{search}%', f'%{search}%'))
        else:
            cursor.execute("SELECT COUNT(*) FROM suppliers")

        total_count = cursor.fetchone()[0]

        # Then data query
        if search:
            cursor.execute("""
                SELECT id, name, parent_code, business_number, business_type,
                       representative, headquarters_phone, email, is_active, created_at
                FROM suppliers
                WHERE name LIKE ? OR parent_code LIKE ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (f'%{search}%', f'%{search}%', limit, offset))
        else:
            cursor.execute("""
                SELECT id, name, parent_code, business_number, business_type,
                       representative, headquarters_phone, email, is_active, created_at
                FROM suppliers
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))

        suppliers_data = cursor.fetchall()

        suppliers = []
        for supplier in suppliers_data:
            suppliers.append({
                "id": supplier[0],
                "name": supplier[1],
                "code": supplier[2],
                "businessNumber": supplier[3],
                "businessType": supplier[4],
                "representative": supplier[5],
                "phone": supplier[6],
                "email": supplier[7],
                "isActive": bool(supplier[8]),
                "createdAt": supplier[9]
            })

        conn.close()

        return {
            "success": True,
            "suppliers": suppliers,
            "pagination": {
                "current_page": page,
                "total_pages": (total_count + limit - 1) // limit,
                "has_prev": page > 1,
                "has_next": page < (total_count + limit - 1) // limit,
                "total_items": total_count,
                "items_per_page": limit
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/suppliers/stats")
async def get_supplier_stats():
    """협력업체 통계 조회"""
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM suppliers")
        total_suppliers = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM suppliers WHERE is_active = 1")
        active_suppliers = cursor.fetchone()[0]

        conn.close()

        return {
            "success": True,
            "stats": {
                "total_suppliers": total_suppliers,
                "active_suppliers": active_suppliers
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/suppliers")
async def get_admin_suppliers():
    """관리자용 협력업체 목록 조회 (구 버전 호환용)"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()

        # suppliers 테이블이 있는지 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='suppliers'")
        suppliers_table_exists = cursor.fetchone()
        
        if suppliers_table_exists:
            cursor.execute("""
                SELECT id, name, representative, headquarters_phone, email, is_active
                FROM suppliers
                ORDER BY name ASC
            """)
            
            suppliers_data = cursor.fetchall()
            suppliers = []
            
            for supplier in suppliers_data:
                suppliers.append({
                    "id": supplier[0],
                    "name": supplier[1],
                    "contact_person": supplier[2] or "미지정",
                    "contact_phone": supplier[3] or "미지정",
                    "email": supplier[4] or "미지정",
                    "active": bool(supplier[5])
                })
        else:
            # suppliers 테이블이 없으면 ingredients에서 추출
            cursor.execute("""
                SELECT DISTINCT supplier_name, COUNT(*) as ingredient_count
                FROM ingredients 
                WHERE supplier_name IS NOT NULL AND supplier_name != ''
                GROUP BY supplier_name
                ORDER BY supplier_name ASC
            """)
            
            suppliers_data = cursor.fetchall()
            suppliers = []
            
            for i, supplier in enumerate(suppliers_data):
                suppliers.append({
                    "id": i + 1,
                    "name": supplier[0],
                    "contact_person": "미지정",
                    "contact_phone": "미지정", 
                    "email": "미지정",
                    "active": True,
                    "ingredient_count": supplier[1]
                })
        
        conn.close()
        
        return {
            "success": True,
            "suppliers": suppliers,
            "total": len(suppliers)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/ingredients-new")
async def get_admin_ingredients_new(page: int = 1, limit: int = 20, search: str = None, category: str = None):
    """관리자용 식자재 목록 (페이징, 검색, 필터링)"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        # WHERE 조건 구성
        where_conditions = []
        params = []
        
        if search:
            where_conditions.append("ingredient_name LIKE ?")
            params.append(f"%{search}%")
        
        if category:
            where_conditions.append("category = ?")
            params.append(category)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # 총 개수 조회
        count_query = f"SELECT COUNT(*) FROM ingredients {where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # 페이징 계산
        total_pages = (total_count + limit - 1) // limit
        offset = (page - 1) * limit
        
        # 데이터 조회
        data_query = f"""
            SELECT 
                id,
                ingredient_name,
                category,
                supplier_name,
                purchase_price,
                selling_price,
                unit,
                origin,
                specification,
                created_at
            FROM ingredients 
            {where_clause}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(data_query, params + [limit, offset])
        ingredients = []
        
        for row in cursor.fetchall():
            ingredients.append({
                "id": row[0],
                "name": row[1] or "이름 없음",
                "category": row[2] or "미분류",
                "supplier": row[3] or "미지정",
                "purchase_price": row[4] or 0,
                "selling_price": row[5] or 0,
                "unit": row[6] or "개",
                "origin": row[7] or "미표기",
                "specification": row[8] or "",
                "created_at": row[9] or ""
            })
        
        conn.close()
        
        return {
            "success": True,
            "ingredients": ingredients,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "items_per_page": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/ingredients")
async def create_ingredient(ingredient_data: dict):
    """관리자용 식자재 추가"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO ingredients (
                ingredient_name, category, supplier_name, 
                purchase_price, selling_price, unit, origin, specification, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            ingredient_data.get('name'),
            ingredient_data.get('category'),
            ingredient_data.get('supplier'),
            ingredient_data.get('purchase_price', 0),
            ingredient_data.get('selling_price', 0),
            ingredient_data.get('unit'),
            ingredient_data.get('origin'),
            ingredient_data.get('specification')
        ))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "식자재가 추가되었습니다."}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/admin/ingredients/{ingredient_id}")
async def update_ingredient(ingredient_id: int, ingredient_data: dict):
    """관리자용 식자재 수정"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE ingredients SET
                ingredient_name = ?,
                category = ?,
                supplier_name = ?,
                purchase_price = ?,
                selling_price = ?,
                unit = ?,
                origin = ?,
                specification = ?
            WHERE id = ?
        """, (
            ingredient_data.get('name'),
            ingredient_data.get('category'),
            ingredient_data.get('supplier'),
            ingredient_data.get('purchase_price'),
            ingredient_data.get('selling_price'),
            ingredient_data.get('unit'),
            ingredient_data.get('origin'),
            ingredient_data.get('specification'),
            ingredient_id
        ))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "식자재가 수정되었습니다."}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/admin/ingredients/{ingredient_id}")
async def delete_ingredient(ingredient_id: int):
    """관리자용 식자재 삭제"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM ingredients WHERE id = ?", (ingredient_id,))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "식자재가 삭제되었습니다."}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/meal-pricing")
async def get_admin_meal_pricing(page: int = 1, limit: int = 20, location_name: str = None, meal_type: str = None):
    """관리자용 식단가 목록 (페이징, 검색, 필터링)"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        # WHERE 조건 구성
        where_conditions = []
        params = []
        
        if location_name:
            where_conditions.append("location_name LIKE ?")
            params.append(f"%{location_name}%")
        
        if meal_type:
            where_conditions.append("meal_type = ?")
            params.append(meal_type)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # 총 개수 조회
        count_query = f"SELECT COUNT(*) FROM meal_pricing {where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # 페이징 계산
        total_pages = (total_count + limit - 1) // limit
        offset = (page - 1) * limit
        
        # 데이터 조회
        data_query = f"""
            SELECT 
                id,
                location_name,
                meal_plan_type,
                meal_type,
                plan_name,
                apply_date_start,
                apply_date_end,
                selling_price,
                material_cost_guideline,
                cost_ratio,
                is_active,
                created_at
            FROM meal_pricing 
            {where_clause}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(data_query, params + [limit, offset])
        meal_pricings = []
        
        for row in cursor.fetchall():
            meal_pricings.append({
                "id": row[0],
                "location_name": row[1] or "미지정",
                "meal_plan_type": row[2] or "기본",
                "meal_type": row[3] or "중식",
                "plan_name": row[4] or "기본 플랜",
                "apply_date_start": row[5] or "",
                "apply_date_end": row[6] or "",
                "selling_price": row[7] or 0,
                "material_cost_guideline": row[8] or 0,
                "cost_ratio": row[9] or 0,
                "is_active": bool(row[10]),
                "created_at": row[11] or ""
            })
        
        conn.close()
        
        return {
            "success": True,
            "meal_pricings": meal_pricings,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "items_per_page": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/meal-pricing")
async def create_meal_pricing(pricing_data: dict):
    """관리자용 식단가 추가"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO meal_pricing (
                location_id, location_name, meal_plan_type, meal_type, plan_name,
                apply_date_start, apply_date_end, selling_price, 
                material_cost_guideline, cost_ratio, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            pricing_data.get('location_id', 1),
            pricing_data.get('location_name'),
            pricing_data.get('meal_plan_type'),
            pricing_data.get('meal_type'),
            pricing_data.get('plan_name'),
            pricing_data.get('apply_date_start'),
            pricing_data.get('apply_date_end'),
            pricing_data.get('selling_price', 0),
            pricing_data.get('material_cost_guideline', 0),
            pricing_data.get('cost_ratio', 0),
            pricing_data.get('is_active', True)
        ))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "식단가가 추가되었습니다."}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/admin/meal-pricing/{pricing_id}")
async def update_meal_pricing(pricing_id: int, pricing_data: dict):
    """관리자용 식단가 수정"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
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
            pricing_data.get('location_name'),
            pricing_data.get('meal_plan_type'),
            pricing_data.get('meal_type'),
            pricing_data.get('plan_name'),
            pricing_data.get('apply_date_start'),
            pricing_data.get('apply_date_end'),
            pricing_data.get('selling_price'),
            pricing_data.get('material_cost_guideline'),
            pricing_data.get('cost_ratio'),
            pricing_data.get('is_active', True),
            pricing_id
        ))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "식단가가 수정되었습니다."}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/admin/meal-pricing/{pricing_id}")
async def delete_meal_pricing(pricing_id: int):
    """관리자용 식단가 삭제"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM meal_pricing WHERE id = ?", (pricing_id,))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "식단가가 삭제되었습니다."}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/business-locations")
async def get_admin_business_locations(page: int = 1, limit: int = 20, site_name: str = None, site_type: str = None):
    """관리자용 사업장 목록 (페이징, 검색, 필터링)"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        # WHERE 조건 구성
        where_conditions = []
        params = []
        
        if site_name:
            where_conditions.append("site_name LIKE ?")
            params.append(f"%{site_name}%")
        
        if site_type:
            where_conditions.append("site_type = ?")
            params.append(site_type)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # 총 개수 조회
        count_query = f"SELECT COUNT(*) FROM business_locations {where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # 페이징 계산
        total_pages = (total_count + limit - 1) // limit
        offset = (page - 1) * limit
        
        # 데이터 조회
        data_query = f"""
            SELECT 
                id, site_code, site_name, site_type, region, address,
                phone, manager_name, manager_phone, manager_email,
                meal_capacity, kitchen_type, is_active, created_at
            FROM business_locations 
            {where_clause}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(data_query, params + [limit, offset])
        locations = []
        
        for row in cursor.fetchall():
            locations.append({
                "id": row[0],
                "site_code": row[1] or "미지정",
                "site_name": row[2] or "이름 없음",
                "site_type": row[3] or "기본",
                "region": row[4] or "",
                "address": row[5] or "",
                "phone": row[6] or "",
                "manager_name": row[7] or "",
                "manager_phone": row[8] or "",
                "manager_email": row[9] or "",
                "meal_capacity": row[10] or 0,
                "kitchen_type": row[11] or "",
                "is_active": bool(row[12]),
                "created_at": row[13] or ""
            })
        
        conn.close()
        
        return {
            "success": True,
            "locations": locations,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "items_per_page": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/business-locations")
async def create_business_location(location_data: dict):
    """관리자용 사업장 추가"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO business_locations (
                site_code, site_name, site_type, region, address, phone,
                manager_name, manager_phone, manager_email, meal_capacity,
                kitchen_type, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            location_data.get('site_code'),
            location_data.get('site_name'),
            location_data.get('site_type'),
            location_data.get('region'),
            location_data.get('address'),
            location_data.get('phone'),
            location_data.get('manager_name'),
            location_data.get('manager_phone'),
            location_data.get('manager_email'),
            location_data.get('meal_capacity', 0),
            location_data.get('kitchen_type'),
            location_data.get('is_active', True)
        ))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "사업장이 추가되었습니다."}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/admin/business-locations/{location_id}")
async def update_business_location(location_id: int, location_data: dict):
    """관리자용 사업장 수정"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE business_locations SET
                site_code = ?, site_name = ?, site_type = ?, region = ?,
                address = ?, phone = ?, manager_name = ?, manager_phone = ?,
                manager_email = ?, meal_capacity = ?, kitchen_type = ?,
                is_active = ?, updated_at = datetime('now')
            WHERE id = ?
        """, (
            location_data.get('site_code'),
            location_data.get('site_name'),
            location_data.get('site_type'),
            location_data.get('region'),
            location_data.get('address'),
            location_data.get('phone'),
            location_data.get('manager_name'),
            location_data.get('manager_phone'),
            location_data.get('manager_email'),
            location_data.get('meal_capacity'),
            location_data.get('kitchen_type'),
            location_data.get('is_active', True),
            location_id
        ))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "사업장이 수정되었습니다."}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/admin/business-locations/{location_id}")
async def delete_business_location(location_id: int):
    """관리자용 사업장 삭제"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM business_locations WHERE id = ?", (location_id,))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "사업장이 삭제되었습니다."}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/ingredients-summary")
async def get_admin_ingredients_summary():
    """관리자용 식자재 요약 통계"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        # 총 식자재 수
        cursor.execute("SELECT COUNT(*) FROM ingredients")
        total_ingredients = cursor.fetchone()[0]
        
        # 카테고리별 통계
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM ingredients
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
        """)
        
        categories = {}
        for row in cursor.fetchall():
            categories[row[0]] = row[1]
        
        # 업체별 통계
        cursor.execute("""
            SELECT supplier_name, COUNT(*) as count
            FROM ingredients
            WHERE supplier_name IS NOT NULL AND supplier_name != ''
            GROUP BY supplier_name
            ORDER BY count DESC
            LIMIT 10
        """)
        
        suppliers = {}
        for row in cursor.fetchall():
            suppliers[row[0]] = row[1]
        
        # 최근 추가된 식자재
        cursor.execute("""
            SELECT ingredient_name, supplier_name, category
            FROM ingredients
            WHERE ingredient_name IS NOT NULL
            ORDER BY rowid DESC
            LIMIT 20
        """)
        
        recent_ingredients = []
        for row in cursor.fetchall():
            recent_ingredients.append({
                "name": row[0],
                "supplier": row[1] or "미지정",
                "category": row[2] or "미지정"
            })
        
        conn.close()
        
        return {
            "success": True,
            "summary": {
                "total_ingredients": total_ingredients,
                "categories": categories,
                "suppliers": suppliers,
                "recent_ingredients": recent_ingredients
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/dashboard-stats")
async def get_dashboard_stats():
    """관리자 대시보드 통계 데이터"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        # 사용자 수
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # 사업장 수
        cursor.execute("SELECT COUNT(*) FROM business_locations")
        total_sites = cursor.fetchone()[0]
        
        # 식자재 수
        cursor.execute("SELECT COUNT(*) FROM ingredients")
        total_ingredients = cursor.fetchone()[0]
        
        # 공급업체 수 
        cursor.execute("SELECT COUNT(DISTINCT supplier_name) FROM ingredients WHERE supplier_name IS NOT NULL")
        total_suppliers = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "success": True,
            "totalUsers": total_users,
            "totalSites": total_sites,
            "totalIngredients": total_ingredients,
            "totalSuppliers": total_suppliers
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/recent-activity")
async def get_recent_activity():
    """최근 활동 로그"""
    try:
        # 간단한 더미 데이터 반환
        activities = [
            {"time": "2025-09-13 02:30", "user": "관리자", "action": "식자재 데이터 업데이트", "status": "완료"},
            {"time": "2025-09-13 02:25", "user": "관리자", "action": "사용자 추가", "status": "완료"},
            {"time": "2025-09-13 02:20", "user": "영양사", "action": "식단 등록", "status": "완료"}
        ]
        
        return {
            "success": True,
            "activities": activities
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/sites")
async def get_sites():
    """사업장 목록 조회"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        # UTF-8 텍스트 처리 설정 추가
        conn.text_factory = lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, site_name, site_type, region, address, phone, is_active 
            FROM business_locations 
            ORDER BY site_name
        """)
        sites = cursor.fetchall()
        
        conn.close()
        
        sites_list = []
        for site in sites:
            sites_list.append({
                "id": site[0],
                "name": site[1],  # site_name
                "type": site[2],  # site_type
                "parent_id": site[3],  # region
                "address": site[4],
                "contact_info": site[5],  # phone
                "status": "활성" if site[6] else "비활성"  # is_active
            })
        
        return {
            "success": True,
            "sites": sites_list
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/sites/{site_id}")
async def get_site(site_id: int):
    """개별 사업장 조회"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        # UTF-8 텍스트 처리 설정 추가
        conn.text_factory = lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, site_name, site_type, region, address, phone, is_active 
            FROM business_locations 
            WHERE id = ?
        """, (site_id,))
        site = cursor.fetchone()
        
        conn.close()
        
        if not site:
            return {"success": False, "error": "사업장을 찾을 수 없습니다"}
        
        site_info = {
            "id": site[0],
            "name": site[1],  # site_name
            "type": site[2],  # site_type
            "parent_id": site[3],  # region
            "address": site[4],
            "contact_info": site[5],  # phone
            "status": "활성" if site[6] else "비활성"  # is_active
        }
        
        return {
            "success": True,
            "site": site_info
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/sites")
async def create_site(site_data: dict):
    """사업장 추가"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        conn.text_factory = lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO business_locations (site_name, site_type, region, address, phone, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            site_data.get('name', ''),
            site_data.get('type', ''),
            site_data.get('parent_id', '전국'),
            site_data.get('address', ''),
            site_data.get('contact_info', ''),
            True
        ))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "사업장이 추가되었습니다"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/admin/sites/{site_id}")
async def update_site(site_id: int, site_data: dict):
    """사업장 수정"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        conn.text_factory = lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE business_locations 
            SET site_name = ?, site_type = ?, region = ?, address = ?, phone = ?
            WHERE id = ?
        """, (
            site_data.get('name', ''),
            site_data.get('type', ''),
            site_data.get('parent_id', '전국'),
            site_data.get('address', ''),
            site_data.get('contact_info', ''),
            site_id
        ))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "사업장이 수정되었습니다"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/admin/sites/{site_id}")
async def delete_site(site_id: int):
    """사업장 삭제"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        conn.text_factory = lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM business_locations WHERE id = ?", (site_id,))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "사업장이 삭제되었습니다"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/users")
async def get_users():
    """사용자 목록 조회"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, contact_info, role, is_active, created_at 
            FROM users 
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        
        conn.close()
        
        users_list = []
        for user in users:
            users_list.append({
                "id": user[0],
                "username": user[1],
                "contact_info": user[2],
                "email": "",  # 이메일 컬럼이 없음
                "role": user[3],
                "is_active": bool(user[4]),
                "created_at": user[5]
            })
        
        return {
            "success": True,
            "users": users_list
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/suppliers/enhanced")
async def get_suppliers_enhanced(page: int = 1, limit: int = 20, search: str = ""):
    """협력업체 목록 조회 (향상된 버전)"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        # 검색 조건 추가
        search_condition = ""
        params = []
        if search.strip():
            search_condition = "WHERE supplier_name LIKE ?"
            params.append(f"%{search}%")
        
        # 공급업체별 통계 조회
        cursor.execute(f"""
            SELECT 
                supplier_name,
                COUNT(*) as ingredient_count,
                AVG(purchase_price) as avg_price,
                MIN(purchase_price) as min_price,
                MAX(purchase_price) as max_price
            FROM ingredients 
            WHERE supplier_name IS NOT NULL {search_condition.replace('WHERE', 'AND') if search_condition else ''}
            GROUP BY supplier_name
            ORDER BY ingredient_count DESC
            LIMIT ? OFFSET ?
        """, params + [limit, (page - 1) * limit])
        
        suppliers = cursor.fetchall()
        
        # 총 개수 조회
        cursor.execute(f"""
            SELECT COUNT(DISTINCT supplier_name) 
            FROM ingredients 
            WHERE supplier_name IS NOT NULL {search_condition}
        """, params)
        
        total_count = cursor.fetchone()[0]
        total_pages = (total_count + limit - 1) // limit
        
        conn.close()
        
        suppliers_list = []
        for supplier in suppliers:
            suppliers_list.append({
                "id": supplier[0],  # supplier_name을 ID로 사용
                "name": supplier[0],
                "ingredient_count": supplier[1],
                "avg_price": round(supplier[2] or 0, 2),
                "min_price": supplier[3] or 0,
                "max_price": supplier[4] or 0,
                "status": "활성",
                "last_updated": "2025-09-13"
            })
        
        return {
            "success": True,
            "suppliers": suppliers_list,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "items_per_page": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/customer-supplier-mappings")
async def get_customer_supplier_mappings():
    """고객-협력업체 매핑 목록 조회"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        # 매핑 데이터를 고객 및 협력업체 정보와 함께 조회
        cursor.execute("""
            SELECT 
                csm.id,
                csm.customer_id,
                csm.supplier_id,
                c.name as customer_name,
                s.name as supplier_name,
                csm.delivery_code,
                csm.priority_order,
                csm.is_primary_supplier,
                csm.contract_start_date,
                csm.contract_end_date,
                csm.is_active,
                csm.notes,
                csm.created_at
            FROM customer_supplier_mappings csm
            LEFT JOIN customers c ON csm.customer_id = c.id
            LEFT JOIN suppliers s ON csm.supplier_id = s.id
            ORDER BY csm.priority_order, c.name, s.name
        """)
        mappings_data = cursor.fetchall()
        
        conn.close()
        
        mappings = []
        for mapping in mappings_data:
            mappings.append({
                "id": mapping[0],
                "customer_id": mapping[1],
                "supplier_id": mapping[2],
                "customer_name": mapping[3],
                "supplier_name": mapping[4],
                "delivery_code": mapping[5],
                "priority_order": mapping[6] or 0,
                "is_primary_supplier": bool(mapping[7]),
                "contract_start_date": mapping[8],
                "contract_end_date": mapping[9],
                "is_active": bool(mapping[10]),
                "notes": mapping[11] or "",
                "created_at": mapping[12]
            })
        
        return {
            "success": True,
            "mappings": mappings
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/customer-supplier-mappings/{mapping_id}")
async def get_customer_supplier_mapping(mapping_id: int):
    """특정 고객-협력업체 매핑 조회"""
    try:
        conn = sqlite3.connect('backups/working_state_20250912/daham_meal.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                csm.id,
                csm.customer_id,
                csm.supplier_id,
                c.name as customer_name,
                s.name as supplier_name,
                csm.delivery_code,
                csm.priority_order,
                csm.is_primary_supplier,
                csm.contract_start_date,
                csm.contract_end_date,
                csm.is_active,
                csm.notes,
                csm.created_at
            FROM customer_supplier_mappings csm
            LEFT JOIN customers c ON csm.customer_id = c.id
            LEFT JOIN suppliers s ON csm.supplier_id = s.id
            WHERE csm.id = ?
        """, (mapping_id,))
        
        mapping_data = cursor.fetchone()
        conn.close()
        
        if not mapping_data:
            return {"success": False, "error": "매핑을 찾을 수 없습니다"}
        
        mapping = {
            "id": mapping_data[0],
            "customer_id": mapping_data[1],
            "supplier_id": mapping_data[2],
            "customer_name": mapping_data[3],
            "supplier_name": mapping_data[4],
            "delivery_code": mapping_data[5],
            "priority_order": mapping_data[6] or 0,
            "is_primary_supplier": bool(mapping_data[7]),
            "contract_start_date": mapping_data[8],
            "contract_end_date": mapping_data[9],
            "is_active": bool(mapping_data[10]),
            "notes": mapping_data[11] or "",
            "created_at": mapping_data[12]
        }
        
        return {
            "success": True,
            "mapping": mapping
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    import os
    
    # 환경 변수에서 포트 읽기, 기본값은 8013
    port = int(os.getenv("API_PORT", "8013"))
    host = os.getenv("API_HOST", "127.0.0.1")
    
    print(f"API 서버 시작: {host}:{port}")
    uvicorn.run(app, host=host, port=port)