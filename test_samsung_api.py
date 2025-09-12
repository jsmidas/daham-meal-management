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
        conn = sqlite3.connect('daham_meal.db')
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
            "contact_person": supplier[2],
            "contact_phone": supplier[3]
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
        conn = sqlite3.connect('daham_meal.db')
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

@app.get("/api/admin/dashboard-stats")
async def get_dashboard_stats():
    """관리자 대시보드 통계 데이터"""
    try:
        conn = sqlite3.connect('daham_meal.db')
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8006)