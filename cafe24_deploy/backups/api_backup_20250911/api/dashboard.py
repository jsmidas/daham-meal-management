"""
대시보드 및 유틸리티 API 라우터
- 대시보드 페이지
- 원가 분석
- 데이터 통계
- 샘플 데이터 생성
- 식재료 관리 페이지
- 테스트 및 기타 유틸리티
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, func
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from pydantic import BaseModel
import json
import pandas as pd
import io

# 로컬 임포트
from app.database import get_db, DATABASE_URL, test_db_connection
from app.api.auth import get_current_user
from models import (
    DietPlan, Menu, MenuItem, Recipe, Ingredient, Supplier, Customer,
    MealCount, PurchaseOrder, ReceivingRecord, User
)
from business_logic import MenuCalculator, NutritionCalculator, CostAnalyzer

router = APIRouter()

# ==============================================================================
# Pydantic 모델 정의
# ==============================================================================

class ImportDataRequest(BaseModel):
    data_type: str
    data: List[Dict[str, Any]]

class SampleDataRequest(BaseModel):
    count: int
    data_type: str

# ==============================================================================
# 페이지 서빙
# ==============================================================================

@router.get("/dashboard")
async def serve_dashboard():
    """대시보드 페이지"""
    return FileResponse("dashboard.html")

@router.get("/cost-analysis")
async def serve_cost_analysis():
    """원가 분석 페이지"""
    return FileResponse("cost_analysis.html")

@router.get("/ingredients-management")
async def serve_ingredients_management():
    """식재료 관리 페이지"""
    return FileResponse("ingredients_management.html")

@router.get("/ingredients")
async def serve_ingredients():
    """식재료 페이지"""
    return FileResponse("ingredients_management.html")

# ==============================================================================
# 식재료 조회 API
# ==============================================================================

@router.get("/api/ingredients/list")
async def get_ingredients_list(
    category: str = Query(""),
    search: str = Query(""),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """식재료 목록 조회 (직접 SQL 사용)"""
    try:
        import sqlite3
        
        # 직접 SQL 쿼리 사용
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        # 기본 쿼리
        sql = """
            SELECT id, category, sub_category, ingredient_code, ingredient_name, 
                   origin, posting_status, specification, unit, tax_type, 
                   delivery_days, purchase_price, selling_price, supplier_name, notes
            FROM ingredients 
            WHERE 1=1
        """
        
        params = []
        
        if search:
            sql += " AND ingredient_name LIKE ?"
            params.append(f"%{search}%")
            
        if category:
            sql += " AND category = ?"
            params.append(category)
            
        sql += f" LIMIT {limit}"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        ingredient_list = []
        for row in rows:
            ingredient_list.append({
                "id": row[0],
                "category": row[1],
                "subcategory": row[2], 
                "code": row[3],
                "name": row[4],
                "origin": row[5],
                "calculation": row[6],
                "specification": row[7],
                "base_unit": row[8],
                "tax_free": row[9],
                "selective_order": row[10],
                "purchase_price": float(row[11]) if row[11] else None,
                "price": float(row[12]) if row[12] else None,
                "supplier_name": row[13],
                "memo": row[14]
            })
        
        conn.close()
        
        return {"success": True, "ingredients": ingredient_list}
        
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/api/ingredients-simple/list")
async def get_ingredients_simple_list():
    """식재료 목록 조회 (간단 버전)"""
    try:
        import sqlite3
        
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, category, sub_category, ingredient_code, ingredient_name, 
                   origin, posting_status, specification, unit, tax_type, 
                   delivery_days, purchase_price, selling_price, supplier_name, notes
            FROM ingredients 
            ORDER BY id
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        ingredient_list = []
        for row in rows:
            ingredient_list.append({
                "id": row[0],
                "category": row[1] or "",
                "subcategory": row[2] or "", 
                "code": row[3] or "",
                "name": row[4] or "",
                "origin": row[5] or "",
                "calculation": row[6] or "",
                "specification": row[7] or "",
                "base_unit": row[8] or "",
                "tax_free": row[9] or "",
                "selective_order": row[10] or "",
                "purchase_price": float(row[11]) if row[11] else 0,
                "price": float(row[12]) if row[12] else 0,
                "supplier_name": row[13] or "",
                "memo": row[14] or ""
            })
        
        return {"success": True, "ingredients": ingredient_list}
        
    except Exception as e:
        import traceback
        return {"success": False, "message": str(e), "trace": traceback.format_exc()}

@router.get("/api/ingredients")
async def get_ingredients_detailed(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: str = Query(""),
    category: str = Query(""),
    supplier_id: int = Query(None),
    db: Session = Depends(get_db)
):
    """식재료 상세 목록 조회"""
    try:
        query = db.query(Ingredient)
        
        # 필터링
        if search:
            search_term = f"%{search}%"
            query = query.filter(Ingredient.ingredient_name.ilike(search_term))
        
        if category:
            query = query.filter(Ingredient.category == category)
        
        if supplier_id:
            query = query.filter(Ingredient.supplier_id == supplier_id)
        
        total = query.count()
        
        # 페이징
        offset = (page - 1) * limit
        ingredients = query.order_by(Ingredient.ingredient_name).offset(offset).limit(limit).all()
        
        ingredient_list = []
        for ingredient in ingredients:
            # 공급업체 정보 조회
            supplier = db.query(Supplier).filter(Supplier.id == ingredient.supplier_id).first() if ingredient.supplier_id else None
            
            ingredient_list.append({
                "id": ingredient.id,
                "name": ingredient.ingredient_name,
                "category": ingredient.category,
                "unit": ingredient.unit,
                "cost_per_unit": float(ingredient.selling_price) if ingredient.selling_price else 0,
                "supplier_id": None,  # 위탁 업체 ID 필드 제거
                "supplier_name": ingredient.supplier_name or "미지정",
                "description": ingredient.notes,
                "created_at": ingredient.created_at.isoformat() if ingredient.created_at else None
            })
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "success": True,
            "ingredients": ingredient_list,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/admin/ingredients/upload-excel")
async def upload_ingredients_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """식재료 Excel 파일 업로드"""
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            return {"success": False, "error": "Excel 파일만 업로드 가능합니다."}
        
        # 파일 읽기
        import pandas as pd
        import io
        from decimal import Decimal
        
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        total_rows = len(df)
        success_count = 0
        error_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # 필수 필드 검증
                if pd.isna(row.iloc[2]) or pd.isna(row.iloc[3]):  # 고유코드, 식재료명
                    error_count += 1
                    errors.append(f"행 {index + 2}: 고유코드 또는 식재료명이 비어있습니다.")
                    continue
                
                code = str(row.iloc[2]).strip()
                name = str(row.iloc[3]).strip()
                
                # 기존 식재료 확인
                existing = db.query(Ingredient).filter(Ingredient.ingredient_code == code).first()
                
                # 가격 처리
                purchase_price = 0
                selling_price = 0
                
                if not pd.isna(row.iloc[10]):  # K열: 입고가
                    try:
                        purchase_price = Decimal(str(row.iloc[10]).replace(',', ''))
                    except:
                        pass
                
                if not pd.isna(row.iloc[11]):  # L열: 판매가
                    try:
                        selling_price = Decimal(str(row.iloc[11]).replace(',', ''))
                    except:
                        pass
                
                if existing:
                    # 업데이트
                    existing.category = str(row.iloc[0]) if not pd.isna(row.iloc[0]) else existing.category
                    existing.sub_category = str(row.iloc[1]) if not pd.isna(row.iloc[1]) else existing.sub_category
                    existing.ingredient_name = name
                    existing.origin = str(row.iloc[4]) if not pd.isna(row.iloc[4]) else existing.origin
                    existing.posting_status = str(row.iloc[5]) if not pd.isna(row.iloc[5]) else existing.posting_status
                    existing.specification = str(row.iloc[6]) if not pd.isna(row.iloc[6]) else existing.specification
                    existing.unit = str(row.iloc[7]) if not pd.isna(row.iloc[7]) else existing.unit
                    existing.tax_type = str(row.iloc[8]) if not pd.isna(row.iloc[8]) else existing.tax_type
                    existing.delivery_days = str(row.iloc[9]) if not pd.isna(row.iloc[9]) else existing.delivery_days
                    existing.purchase_price = purchase_price
                    existing.selling_price = selling_price
                    existing.supplier_name = str(row.iloc[12]) if not pd.isna(row.iloc[12]) else existing.supplier_name
                    existing.notes = str(row.iloc[13]) if not pd.isna(row.iloc[13]) else existing.notes
                else:
                    # 새로 생성
                    new_ingredient = Ingredient(
                        category=str(row.iloc[0]) if not pd.isna(row.iloc[0]) else "기타",
                        sub_category=str(row.iloc[1]) if not pd.isna(row.iloc[1]) else "기타",
                        ingredient_code=code,
                        ingredient_name=name,
                        origin=str(row.iloc[4]) if not pd.isna(row.iloc[4]) else None,
                        posting_status=str(row.iloc[5]) if not pd.isna(row.iloc[5]) else None,
                        specification=str(row.iloc[6]) if not pd.isna(row.iloc[6]) else None,
                        unit=str(row.iloc[7]) if not pd.isna(row.iloc[7]) else "EA",
                        tax_type=str(row.iloc[8]) if not pd.isna(row.iloc[8]) else None,
                        delivery_days=str(row.iloc[9]) if not pd.isna(row.iloc[9]) else "1",
                        purchase_price=purchase_price,
                        selling_price=selling_price,
                        supplier_name=str(row.iloc[12]) if not pd.isna(row.iloc[12]) else "미지정",
                        notes=str(row.iloc[13]) if not pd.isna(row.iloc[13]) else None,
                        created_date=datetime.now()
                    )
                    db.add(new_ingredient)
                
                success_count += 1
                
                # 50개마다 커밋
                if (index + 1) % 50 == 0:
                    db.commit()
                    
            except Exception as row_error:
                error_count += 1
                errors.append(f"행 {index + 2}: {str(row_error)}")
                continue
        
        # 최종 커밋
        db.commit()
        
        return {
            "success": True,
            "total": total_rows,
            "success": success_count,
            "errors": error_count,
            "error_details": errors[:10] if errors else []
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "error": f"업로드 처리 중 오류: {str(e)}"}

@router.post("/api/ingredients")
async def create_ingredient(
    request: Request,
    db: Session = Depends(get_db)
):
    """식재료 생성"""
    try:
        data = await request.json()
        
        # 고유코드 중복 확인
        if data.get('code'):
            existing = db.query(Ingredient).filter(Ingredient.ingredient_code == data['code']).first()
            if existing:
                return {"success": False, "error": "이미 존재하는 고유코드입니다."}
        
        new_ingredient = Ingredient(
            category=data.get('category', ''),
            sub_category=data.get('subcategory', ''),
            ingredient_code=data.get('code', ''),
            ingredient_name=data.get('name', ''),
            origin=data.get('origin'),
            posting_status=data.get('calculation'),
            specification=data.get('specification'),
            unit=data.get('base_unit', 'EA'),
            tax_type=data.get('tax_free'),
            delivery_days=data.get('selective_order', '1'),
            purchase_price=Decimal(str(data.get('purchase_price', 0))),
            selling_price=Decimal(str(data.get('price', 0))),
            supplier_name=data.get('supplier_name', '미지정'),
            notes=data.get('memo'),
            created_date=datetime.now()
        )
        
        db.add(new_ingredient)
        db.commit()
        
        return {"success": True, "message": "식재료가 생성되었습니다."}
        
    except Exception as e:
        db.rollback()
        return {"success": False, "error": f"식재료 생성 중 오류: {str(e)}"}

@router.put("/api/ingredients/{ingredient_id}")
async def update_ingredient(
    ingredient_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """식재료 수정"""
    try:
        data = await request.json()
        
        ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        if not ingredient:
            return {"success": False, "error": "식재료를 찾을 수 없습니다."}
        
        # 필드 업데이트
        if 'category' in data:
            ingredient.category = data['category']
        if 'subcategory' in data:
            ingredient.sub_category = data['subcategory']
        if 'code' in data:
            ingredient.ingredient_code = data['code']
        if 'name' in data:
            ingredient.ingredient_name = data['name']
        if 'origin' in data:
            ingredient.origin = data['origin']
        if 'calculation' in data:
            ingredient.posting_status = data['calculation']
        if 'specification' in data:
            ingredient.specification = data['specification']
        if 'base_unit' in data:
            ingredient.unit = data['base_unit']
        if 'tax_free' in data:
            ingredient.tax_type = data['tax_free']
        if 'selective_order' in data:
            ingredient.delivery_days = data['selective_order']
        if 'purchase_price' in data:
            ingredient.purchase_price = Decimal(str(data['purchase_price'])) if data['purchase_price'] else None
        if 'price' in data:
            ingredient.selling_price = Decimal(str(data['price'])) if data['price'] else None
        if 'supplier_name' in data:
            ingredient.supplier_name = data['supplier_name']
        if 'memo' in data:
            ingredient.notes = data['memo']
        
        db.commit()
        
        return {"success": True, "message": "식재료가 수정되었습니다."}
        
    except Exception as e:
        db.rollback()
        return {"success": False, "error": f"식재료 수정 중 오류: {str(e)}"}

@router.delete("/api/ingredients/{ingredient_id}")
async def delete_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db)
):
    """식재료 삭제"""
    try:
        ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        if not ingredient:
            return {"success": False, "error": "식재료를 찾을 수 없습니다."}
        
        db.delete(ingredient)
        db.commit()
        
        return {"success": True, "message": "식재료가 삭제되었습니다."}
        
    except Exception as e:
        db.rollback()
        return {"success": False, "error": f"식재료 삭제 중 오류: {str(e)}"}

@router.get("/suppliers/{supplier_id}/ingredients")
async def get_supplier_ingredients(supplier_id: int, db: Session = Depends(get_db)):
    """특정 공급업체의 식재료 목록 조회"""
    try:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            return {"success": False, "message": "존재하지 않는 공급업체입니다."}
        
        ingredients = db.query(Ingredient).filter(Ingredient.supplier_id == supplier_id).all()
        
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_list.append({
                "id": ingredient.id,
                "name": ingredient.name,
                "category": ingredient.category,
                "unit": ingredient.unit,
                "cost_per_unit": float(ingredient.cost_per_unit) if ingredient.cost_per_unit else 0,
                "description": ingredient.description
            })
        
        return {
            "success": True,
            "supplier": {
                "id": supplier.id,
                "name": supplier.name,
                "contact_person": supplier.contact_person,
                "contact_phone": supplier.contact_phone
            },
            "ingredients": ingredient_list
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

# ==============================================================================
# 데이터 통계 API
# ==============================================================================

@router.get("/data-statistics")
async def get_data_statistics(db: Session = Depends(get_db)):
    """데이터 통계 조회"""
    try:
        stats = {
            "customers": db.query(Customer).count(),
            "suppliers": db.query(Supplier).count(),
            "ingredients": db.query(Ingredient).count(),
            "recipes": db.query(Recipe).count(),
            "menus": db.query(Menu).count(),
            "diet_plans": db.query(DietPlan).count(),
            "meal_counts": db.query(MealCount).count(),
            "purchase_orders": db.query(PurchaseOrder).count(),
            "receiving_records": db.query(ReceivingRecord).count()
        }
        
        # 추가 통계 정보
        today = date.today()
        
        # 이번 주 식단수
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        week_diet_plans = db.query(DietPlan).filter(
            DietPlan.date >= week_start,
            DietPlan.date <= week_end
        ).count()
        
        # 이번 달 발주서 수
        month_start = today.replace(day=1)
        month_orders = db.query(PurchaseOrder).filter(
            PurchaseOrder.order_date >= month_start
        ).count()
        
        # 카테고리별 식재료 수
        ingredient_categories = db.query(
            Ingredient.category,
            func.count(Ingredient.id).label('count')
        ).group_by(Ingredient.category).all()
        
        category_stats = {category: count for category, count in ingredient_categories}
        
        extended_stats = {
            **stats,
            "week_diet_plans": week_diet_plans,
            "month_orders": month_orders,
            "ingredient_categories": category_stats
        }
        
        return {"success": True, "statistics": extended_stats}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ==============================================================================
# 샘플 데이터 생성 API
# ==============================================================================

@router.get("/create-sample-data")
async def create_sample_data(db: Session = Depends(get_db)):
    """샘플 데이터 생성"""
    try:
        created_counts = {
            "customers": 0,
            "suppliers": 0,
            "ingredients": 0,
            "recipes": 0,
            "menus": 0
        }
        
        # 샘플 고객 데이터
        sample_customers = [
            {"name": "A사업장", "code": "A001", "site_type": "사무실", "contact_person": "김담당", "contact_phone": "02-1234-5678"},
            {"name": "B사업장", "code": "B001", "site_type": "공장", "contact_person": "이담당", "contact_phone": "02-2345-6789"},
            {"name": "C사업장", "code": "C001", "site_type": "학교", "contact_person": "박담당", "contact_phone": "02-3456-7890"}
        ]
        
        for customer_data in sample_customers:
            existing = db.query(Customer).filter(Customer.code == customer_data["code"]).first()
            if not existing:
                new_customer = Customer(
                    name=customer_data["name"],
                    code=customer_data["code"],
                    site_type=customer_data["site_type"],
                    contact_person=customer_data["contact_person"],
                    contact_phone=customer_data["contact_phone"],
                    created_at=datetime.now()
                )
                db.add(new_customer)
                created_counts["customers"] += 1
        
        # 샘플 공급업체 데이터
        sample_suppliers = [
            {"name": "신선식품", "code": "SUP001", "contact_person": "홍공급", "contact_phone": "031-111-2222"},
            {"name": "건강농산", "code": "SUP002", "contact_person": "정공급", "contact_phone": "031-222-3333"},
            {"name": "맛있는육류", "code": "SUP003", "contact_person": "조공급", "contact_phone": "031-333-4444"}
        ]
        
        for supplier_data in sample_suppliers:
            existing = db.query(Supplier).filter(Supplier.code == supplier_data["code"]).first()
            if not existing:
                new_supplier = Supplier(
                    name=supplier_data["name"],
                    code=supplier_data["code"],
                    contact_person=supplier_data["contact_person"],
                    contact_phone=supplier_data["contact_phone"],
                    created_at=datetime.now()
                )
                db.add(new_supplier)
                created_counts["suppliers"] += 1
        
        db.commit()
        
        # 공급업체 ID 조회 (식재료 생성용)
        suppliers = db.query(Supplier).limit(3).all()
        supplier_ids = [s.id for s in suppliers]
        
        # 샘플 식재료 데이터
        sample_ingredients = [
            {"name": "양파", "category": "채소류", "unit": "kg", "cost_per_unit": 2000},
            {"name": "당근", "category": "채소류", "unit": "kg", "cost_per_unit": 2500},
            {"name": "감자", "category": "채소류", "unit": "kg", "cost_per_unit": 3000},
            {"name": "쌀", "category": "곡류", "unit": "kg", "cost_per_unit": 3500},
            {"name": "돼지고기", "category": "육류", "unit": "kg", "cost_per_unit": 15000},
            {"name": "닭고기", "category": "육류", "unit": "kg", "cost_per_unit": 8000}
        ]
        
        for i, ingredient_data in enumerate(sample_ingredients):
            existing = db.query(Ingredient).filter(Ingredient.ingredient_name == ingredient_data["name"]).first()
            if not existing:
                new_ingredient = Ingredient(
                    name=ingredient_data["name"],
                    category=ingredient_data["category"],
                    unit=ingredient_data["unit"],
                    cost_per_unit=Decimal(str(ingredient_data["cost_per_unit"])),
                    supplier_id=supplier_ids[i % len(supplier_ids)] if supplier_ids else None,
                    created_at=datetime.now()
                )
                db.add(new_ingredient)
                created_counts["ingredients"] += 1
        
        # 샘플 레시피 데이터
        sample_recipes = [
            {"name": "김치찌개", "category": "찌개류", "description": "맛있는 김치찌개", "servings": 4},
            {"name": "된장찌개", "category": "찌개류", "description": "구수한 된장찌개", "servings": 4},
            {"name": "불고기", "category": "구이류", "description": "달콤한 불고기", "servings": 3}
        ]
        
        for recipe_data in sample_recipes:
            existing = db.query(Recipe).filter(Recipe.name == recipe_data["name"]).first()
            if not existing:
                new_recipe = Recipe(
                    name=recipe_data["name"],
                    category=recipe_data["category"],
                    description=recipe_data["description"],
                    servings=recipe_data["servings"],
                    created_at=datetime.now()
                )
                db.add(new_recipe)
                created_counts["recipes"] += 1
        
        # 샘플 메뉴 데이터
        sample_menus = [
            {"name": "한식세트A", "category": "한식", "description": "전통 한식 메뉴"},
            {"name": "한식세트B", "category": "한식", "description": "건강 한식 메뉴"},
            {"name": "양식세트A", "category": "양식", "description": "서양식 메뉴"}
        ]
        
        for menu_data in sample_menus:
            existing = db.query(Menu).filter(Menu.name == menu_data["name"]).first()
            if not existing:
                new_menu = Menu(
                    name=menu_data["name"],
                    category=menu_data["category"],
                    description=menu_data["description"],
                    created_at=datetime.now()
                )
                db.add(new_menu)
                created_counts["menus"] += 1
        
        db.commit()
        
        total_created = sum(created_counts.values())
        
        return {
            "success": True,
            "message": f"샘플 데이터 생성 완료 (총 {total_created}개)",
            "created_counts": created_counts
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"샘플 데이터 생성 중 오류가 발생했습니다: {str(e)}"}

# ==============================================================================
# 데이터 가져오기 API
# ==============================================================================

@router.post("/import-real-data")
async def import_real_data(
    import_request: ImportDataRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """실제 데이터 가져오기"""
    # 인증 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        imported_count = 0
        
        if import_request.data_type == "ingredients":
            for item_data in import_request.data:
                # 중복 체크
                existing = db.query(Ingredient).filter(Ingredient.ingredient_name == item_data["name"]).first()
                if not existing:
                    new_ingredient = Ingredient(
                        name=item_data["name"],
                        category=item_data.get("category", "기타"),
                        unit=item_data.get("unit", "kg"),
                        cost_per_unit=Decimal(str(item_data.get("cost_per_unit", 0))),
                        supplier_id=item_data.get("supplier_id"),
                        description=item_data.get("description", ""),
                        created_at=datetime.now()
                    )
                    db.add(new_ingredient)
                    imported_count += 1
        
        elif import_request.data_type == "customers":
            for item_data in import_request.data:
                existing = db.query(Customer).filter(Customer.name == item_data["name"]).first()
                if not existing:
                    new_customer = Customer(
                        name=item_data["name"],
                        code=item_data.get("code"),
                        site_type=item_data.get("site_type", "일반"),
                        contact_person=item_data.get("contact_person"),
                        contact_phone=item_data.get("contact_phone"),
                        address=item_data.get("address"),
                        created_at=datetime.now()
                    )
                    db.add(new_customer)
                    imported_count += 1
        
        elif import_request.data_type == "suppliers":
            for item_data in import_request.data:
                existing = db.query(Supplier).filter(Supplier.name == item_data["name"]).first()
                if not existing:
                    new_supplier = Supplier(
                        name=item_data["name"],
                        code=item_data.get("code"),
                        contact_person=item_data.get("contact_person"),
                        contact_phone=item_data.get("contact_phone"),
                        email=item_data.get("email"),
                        address=item_data.get("address"),
                        created_at=datetime.now()
                    )
                    db.add(new_supplier)
                    imported_count += 1
        
        else:
            return {"success": False, "message": f"지원하지 않는 데이터 타입입니다: {import_request.data_type}"}
        
        db.commit()
        
        return {
            "success": True,
            "message": f"{import_request.data_type} 데이터 {imported_count}개가 가져와졌습니다.",
            "imported_count": imported_count
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"데이터 가져오기 중 오류가 발생했습니다: {str(e)}"}

# ==============================================================================
# 테스트 및 개발용 API
# ==============================================================================

@router.get("/test-db")
async def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        db_status = test_db_connection()
        
        if db_status:
            # 추가적인 테이블 존재 확인
            engine = create_engine(DATABASE_URL)
            with engine.connect() as conn:
                # 주요 테이블들 확인
                tables_to_check = [
                    'customers', 'suppliers', 'ingredients', 'recipes', 'menus',
                    'diet_plans', 'menu_items', 'meal_counts', 'users'
                ]
                
                table_status = {}
                for table in tables_to_check:
                    try:
                        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                        table_status[table] = {"exists": True, "count": result[0]}
                    except:
                        table_status[table] = {"exists": False, "count": 0}
                
                return {
                    "success": True,
                    "message": "데이터베이스 연결 성공",
                    "database": "connected",
                    "tables": table_status
                }
        else:
            return {
                "success": False,
                "message": "데이터베이스 연결 실패",
                "database": "disconnected"
            }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"데이터베이스 테스트 중 오류가 발생했습니다: {str(e)}",
            "database": "error"
        }

@router.post("/api/create_supplier_ingredient_data")
async def create_supplier_ingredient_data(db: Session = Depends(get_db)):
    """공급업체-식재료 연결 데이터 생성"""
    try:
        # 공급업체와 식재료 매핑
        suppliers = db.query(Supplier).all()
        ingredients = db.query(Ingredient).all()
        
        if not suppliers or not ingredients:
            return {"success": False, "message": "공급업체나 식재료 데이터가 없습니다."}
        
        updated_count = 0
        
        # 식재료에 공급업체 할당 (순환 할당)
        for i, ingredient in enumerate(ingredients):
            if not ingredient.supplier_id:
                supplier_idx = i % len(suppliers)
                ingredient.supplier_id = suppliers[supplier_idx].id
                ingredient.updated_at = datetime.now()
                updated_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"공급업체-식재료 연결 데이터가 생성되었습니다. ({updated_count}개 업데이트)",
            "updated_count": updated_count
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"데이터 생성 중 오류가 발생했습니다: {str(e)}"}

@router.post("/api/create_test_data")
async def create_test_data(db: Session = Depends(get_db)):
    """통합 테스트 데이터 생성"""
    try:
        created_data = {
            "customers": 0,
            "suppliers": 0,
            "ingredients": 0,
            "menus": 0,
            "menu_items": 0,
            "diet_plans": 0
        }
        
        # 고객 데이터 (이미 있다면 스킵)
        if db.query(Customer).count() < 3:
            sample_customers = [
                {"name": "테스트사업장A", "code": "TEST001", "site_type": "사무실"},
                {"name": "테스트사업장B", "code": "TEST002", "site_type": "공장"},
                {"name": "테스트사업장C", "code": "TEST003", "site_type": "학교"}
            ]
            
            for customer_data in sample_customers:
                existing = db.query(Customer).filter(Customer.code == customer_data["code"]).first()
                if not existing:
                    new_customer = Customer(
                        name=customer_data["name"],
                        code=customer_data["code"],
                        site_type=customer_data["site_type"],
                        created_at=datetime.now()
                    )
                    db.add(new_customer)
                    created_data["customers"] += 1
        
        # 공급업체 데이터
        if db.query(Supplier).count() < 2:
            sample_suppliers = [
                {"name": "테스트공급업체A", "code": "TSUP001", "contact_phone": "02-111-2222"},
                {"name": "테스트공급업체B", "code": "TSUP002", "contact_phone": "02-222-3333"}
            ]
            
            for supplier_data in sample_suppliers:
                existing = db.query(Supplier).filter(Supplier.code == supplier_data["code"]).first()
                if not existing:
                    new_supplier = Supplier(
                        name=supplier_data["name"],
                        code=supplier_data["code"],
                        contact_phone=supplier_data["contact_phone"],
                        created_at=datetime.now()
                    )
                    db.add(new_supplier)
                    created_data["suppliers"] += 1
        
        db.commit()
        
        # 공급업체 ID 조회
        suppliers = db.query(Supplier).all()
        supplier_id = suppliers[0].id if suppliers else None
        
        # 식재료 데이터
        if db.query(Ingredient).count() < 5:
            sample_ingredients = [
                {"name": "테스트양파", "category": "채소류", "unit": "kg", "cost_per_unit": 2000},
                {"name": "테스트쌀", "category": "곡류", "unit": "kg", "cost_per_unit": 3500},
                {"name": "테스트돼지고기", "category": "육류", "unit": "kg", "cost_per_unit": 15000}
            ]
            
            for ingredient_data in sample_ingredients:
                existing = db.query(Ingredient).filter(Ingredient.ingredient_name == ingredient_data["name"]).first()
                if not existing:
                    new_ingredient = Ingredient(
                        name=ingredient_data["name"],
                        category=ingredient_data["category"],
                        unit=ingredient_data["unit"],
                        cost_per_unit=Decimal(str(ingredient_data["cost_per_unit"])),
                        supplier_id=supplier_id,
                        created_at=datetime.now()
                    )
                    db.add(new_ingredient)
                    created_data["ingredients"] += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": "통합 테스트 데이터가 생성되었습니다.",
            "created_data": created_data
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"테스트 데이터 생성 중 오류가 발생했습니다: {str(e)}"}