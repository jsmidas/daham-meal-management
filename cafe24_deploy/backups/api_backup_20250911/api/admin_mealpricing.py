"""
식단가 관리 전용 API 모듈
- 식단가 등록, 조회, 수정, 삭제
- 깔끔하고 독립적인 기능 구현
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
import json

# 로컬 임포트
from app.database import get_db
from app.api.auth import get_current_user
from models import Customer, MealPricing

router = APIRouter(prefix="/api/admin", tags=["meal-pricing"])

# 새로운 API 엔드포인트 추가
@router.get("/meal-pricing/by-location/{location_id}")
async def get_meal_plans_by_location(location_id: int, db: Session = Depends(get_db)):
    """특정 사업장의 식단가 목록 조회 (JavaScript 연동용)"""
    try:
        # meal_pricing 테이블에서 데이터 조회
        query = text("""
            SELECT id, location_id, location_name, meal_type, plan_name,
                   selling_price, material_cost_guideline, cost_ratio
            FROM meal_pricing
            WHERE location_id = :location_id AND is_active = 1
            ORDER BY meal_type, plan_name
        """)
        
        result = db.execute(query, {"location_id": location_id})
        rows = result.fetchall()
        
        meal_plans = []
        for row in rows:
            meal_plans.append({
                "id": row[0],
                "location_id": row[1],
                "location_name": row[2],
                "meal_time": row[3],  # meal_type을 meal_time으로 매핑
                "name": row[4],  # plan_name을 name으로 매핑
                "selling_price": float(row[5]) if row[5] else 0,
                "target_material_cost": float(row[6]) if row[6] else 0,
                "cost_ratio": float(row[7]) if row[7] else 0
            })
        
        response_data = {
            "success": True,
            "mealPlans": meal_plans,
            "count": len(meal_plans)
        }
        
        # JSON 응답에서 한글이 유니코드로 이스케이프되지 않도록 설정
        return JSONResponse(
            content=response_data,
            media_type="application/json; charset=utf-8",
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
        
    except Exception as e:
        print(f"식단가 조회 오류: {str(e)}")
        return {
            "success": False,
            "mealPlans": [],
            "error": str(e)
        }

# ==============================================================================
# Pydantic 모델들
# ==============================================================================

class MealPricingCreate(BaseModel):
    customer_id: int
    meal_type: str  # breakfast, lunch, dinner, snack
    price: Decimal
    effective_date: date
    notes: Optional[str] = None
    material_cost_guideline: Optional[Decimal] = 0

class MealPricingResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    meal_type: str
    price: float
    effective_date: str
    notes: str
    created_at: str

# ==============================================================================
# 인증 헬퍼
# ==============================================================================

def verify_admin_access(request: Request):
    """관리자 권한 확인"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    return user

# ==============================================================================
# 식단가 관리 API
# ==============================================================================

@router.post("/meal-pricing")
async def create_meal_pricing(pricing_data: MealPricingCreate, request: Request, db: Session = Depends(get_db)):
    """식단가 등록"""
    verify_admin_access(request)
    
    try:
        # 사업장 정보 확인
        customer = db.query(Customer).filter(Customer.id == pricing_data.customer_id).first()
        if not customer:
            return {"success": False, "message": "존재하지 않는 사업장입니다."}
        
        # 새 식단가 생성
        new_pricing = MealPricing(
            location_id=pricing_data.customer_id,
            location_name=customer.name,
            meal_plan_type="기본",
            meal_type=pricing_data.meal_type,
            plan_name=pricing_data.notes or f"{pricing_data.meal_type} 식단",  # notes 사용
            apply_date_start=pricing_data.effective_date,
            selling_price=pricing_data.price,
            material_cost_guideline=pricing_data.material_cost_guideline or 0,  # 목표재료비
            created_at=datetime.now()
        )
        
        db.add(new_pricing)
        db.commit()
        db.refresh(new_pricing)
        
        return {
            "success": True,
            "message": "식단가가 등록되었습니다.",
            "pricing_id": new_pricing.id
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"식단가 등록 중 오류: {str(e)}"}

@router.get("/meal-pricing/debug")
async def debug_meal_pricing_table(db: Session = Depends(get_db)):
    """식단가 테이블 구조 및 데이터 디버깅"""
    try:
        # 테이블 스키마 확인
        result = db.execute(text("PRAGMA table_info(meal_pricing)"))
        columns = result.fetchall()
        
        # 실제 데이터 확인
        data_result = db.execute(text("SELECT * FROM meal_pricing LIMIT 5"))
        data_rows = data_result.fetchall()
        
        return {
            "success": True,
            "table_info": [
                {"name": row[1], "type": row[2], "nullable": not row[3]}
                for row in columns
            ],
            "sample_data": [
                {f"col_{i}": str(value) for i, value in enumerate(row)}
                for row in data_rows
            ],
            "data_count": len(data_rows)
        }
    except Exception as e:
        return {"success": False, "message": f"디버깅 오류: {str(e)}"}

@router.get("/meal-pricing/simple")
async def get_meal_pricing_simple(db: Session = Depends(get_db)):
    """간단한 식단가 조회 (디버그용)"""
    try:
        result = db.execute(text("SELECT COUNT(*) as count FROM meal_pricing"))
        count = result.fetchone().count
        return {
            "success": True,
            "message": f"DB에 {count}개의 식단가 데이터가 있습니다",
            "count": count
        }
    except Exception as e:
        return {"success": False, "message": f"오류: {str(e)}"}

@router.get("/meal-pricing/test")
async def get_meal_pricing_test():
    """완전히 간단한 테스트 엔드포인트"""
    return {"success": True, "message": "API가 작동합니다", "test": True}

@router.get("/meal-pricing/test-filter")
async def test_filter_endpoint(location_id: int = Query(4), db: Session = Depends(get_db)):
    """필터링 테스트 전용 엔드포인트"""
    try:
        print(f"[TEST] location_id parameter: {location_id}")
        
        # 직접 ORM 사용해서 필터링
        pricings = db.query(MealPricing).filter(MealPricing.location_id == location_id).all()
        print(f"[TEST] ORM filtered results: {len(pricings)} records")
        
        result_list = []
        for p in pricings:
            result_list.append({
                "id": p.id,
                "location_id": p.location_id,
                "location_name": p.location_name,
                "meal_type": p.meal_type,
                "selling_price": float(p.selling_price) if p.selling_price else 0,
                "plan_name": p.plan_name
            })
        
        return {
            "success": True,
            "location_id": location_id,
            "count": len(result_list),
            "pricings": result_list
        }
    except Exception as e:
        print(f"[TEST] Error: {e}")
        return {"success": False, "error": str(e)}

@router.get("/meal-pricing/working")
async def get_meal_pricing_working(db: Session = Depends(get_db)):
    """작동하는 식단가 조회 (인증 없음, 디버그용)"""
    try:
        sql = text("""
            SELECT id, location_id, location_name, meal_type, 
                   selling_price, apply_date_start, plan_name,
                   material_cost_guideline
            FROM meal_pricing 
            WHERE location_id = 3
            LIMIT 10
        """)
        result = db.execute(sql)
        rows = result.fetchall()
        
        data = []
        for row in rows:
            data.append({
                "id": row.id,
                "customer_id": row.location_id,
                "customer_name": row.location_name,
                "meal_type": row.meal_type,
                "price": float(row.selling_price) if row.selling_price else 0,
                "effective_date": str(row.apply_date_start) if row.apply_date_start else "",
                "notes": row.plan_name or "",
                "material_cost_guideline": float(row.material_cost_guideline) if row.material_cost_guideline else 0
            })
        
        return {
            "success": True,
            "pricings": data,
            "total": len(data),
            "message": f"학교(ID:3)의 식단가 {len(data)}건을 성공적으로 로드했습니다"
        }
    except Exception as e:
        print(f"[DEBUG] Working endpoint error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"오류: {str(e)}"}

@router.get("/meal-pricing")
async def get_meal_pricing(
    customer_id: Optional[int] = Query(None),
    location_id: Optional[int] = Query(None),
    meal_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """식단가 목록 조회 - Raw SQL로 완전히 재작성"""
    try:
        # location_id가 우선, 없으면 customer_id 사용 (하위 호환성)
        target_location_id = location_id or customer_id
        print(f"[DEBUG] get_meal_pricing called with location_id={target_location_id}, meal_type={meal_type}")
        
        # WHERE 조건 구성
        where_conditions = []
        params = {"limit": limit, "offset": (page - 1) * limit}
        
        if target_location_id:
            where_conditions.append("location_id = :location_id")
            params["location_id"] = target_location_id
        
        if meal_type:
            where_conditions.append("meal_type = :meal_type")
            params["meal_type"] = meal_type
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # 카운트 쿼리
        count_sql = text(f"SELECT COUNT(*) as total FROM meal_pricing{where_clause}")
        count_result = db.execute(count_sql, params)
        total = count_result.fetchone().total
        print(f"[DEBUG] Found {total} total records with location_id={target_location_id}")
        
        # 데이터 쿼리
        sql_text = f"""
            SELECT id, location_id, location_name, meal_type, 
                   selling_price, apply_date_start, plan_name,
                   material_cost_guideline, created_at
            FROM meal_pricing 
            {where_clause}
            ORDER BY id DESC
            LIMIT :limit OFFSET :offset
        """
        print(f"[DEBUG] Executing SQL: {sql_text}")
        print(f"[DEBUG] With params: {params}")
        
        sql = text(sql_text)
        result = db.execute(sql, params)
        
        rows = result.fetchall()
        print(f"[DEBUG] Raw SQL returned {len(rows)} rows")
        
        pricing_list = []
        for row in rows:
            pricing_list.append({
                "id": row.id,
                "customer_id": row.location_id,
                "customer_name": row.location_name or "이름 없음",
                "meal_type": row.meal_type,
                "price": float(row.selling_price) if row.selling_price else 0.0,
                "effective_date": str(row.apply_date_start) if row.apply_date_start else "",
                "notes": row.plan_name or "",
                "material_cost_guideline": float(row.material_cost_guideline) if row.material_cost_guideline else 0.0,
                "created_at": str(row.created_at) if row.created_at else ""
            })
        
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        
        print(f"[DEBUG] Successfully processed {len(pricing_list)} pricings")
        return {
            "success": True,
            "pricings": pricing_list,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
        
    except Exception as e:
        print(f"[DEBUG] Exception in get_meal_pricing: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"식단가 조회 중 오류: {str(e)}"}

@router.put("/meal-pricing/{pricing_id}")
async def update_meal_pricing(pricing_id: int, pricing_data: MealPricingCreate, request: Request, db: Session = Depends(get_db)):
    """식단가 수정"""
    verify_admin_access(request)
    
    try:
        pricing = db.query(MealPricing).filter(MealPricing.id == pricing_id).first()
        if not pricing:
            return {"success": False, "message": "존재하지 않는 식단가입니다."}
        
        # 사업장 정보 확인
        customer = db.query(Customer).filter(Customer.id == pricing_data.customer_id).first()
        if not customer:
            return {"success": False, "message": "존재하지 않는 사업장입니다."}
        
        # 정보 업데이트
        pricing.location_id = pricing_data.customer_id
        pricing.location_name = customer.name
        pricing.meal_type = pricing_data.meal_type
        pricing.selling_price = pricing_data.price
        pricing.apply_date_start = pricing_data.effective_date
        pricing.plan_name = pricing_data.notes or f"{pricing_data.meal_type} 식단"  # notes 사용
        pricing.material_cost_guideline = pricing_data.material_cost_guideline or 0  # 목표재료비
        
        db.commit()
        
        return {"success": True, "message": "식단가가 수정되었습니다."}
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"식단가 수정 중 오류: {str(e)}"}

@router.delete("/meal-pricing/{pricing_id}")
async def delete_meal_pricing(pricing_id: int, request: Request, db: Session = Depends(get_db)):
    """식단가 삭제"""
    verify_admin_access(request)
    
    try:
        pricing = db.query(MealPricing).filter(MealPricing.id == pricing_id).first()
        if not pricing:
            return {"success": False, "message": "존재하지 않는 식단가입니다."}
        
        db.delete(pricing)
        db.commit()
        
        return {"success": True, "message": "식단가가 삭제되었습니다."}
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"식단가 삭제 중 오류: {str(e)}"}

@router.get("/meal-pricing/statistics")
async def get_meal_pricing_statistics(db: Session = Depends(get_db)):
    """식단가 통계"""
    try:
        stats_sql = """
        SELECT 
            COUNT(*) as total_count,
            COUNT(DISTINCT location_id) as customer_count,
            COUNT(DISTINCT meal_type) as meal_type_count,
            AVG(selling_price) as avg_price,
            MIN(selling_price) as min_price,
            MAX(selling_price) as max_price
        FROM meal_pricing
        """
        
        result = db.execute(text(stats_sql))
        row = result.fetchone()
        
        return {
            "success": True,
            "stats": {
                "total_pricings": row.total_count or 0,
                "total_customers": row.customer_count or 0,
                "meal_types": row.meal_type_count or 0,
                "average_price": float(row.avg_price) if row.avg_price else 0.0,
                "min_price": float(row.min_price) if row.min_price else 0.0,
                "max_price": float(row.max_price) if row.max_price else 0.0
            }
        }
        
    except Exception as e:
        return {"success": False, "message": f"통계 조회 중 오류: {str(e)}"}

# ==============================================================================
# 호환성을 위한 복수형 엔드포인트들
# ==============================================================================

@router.get("/meal-pricings")
async def get_meal_pricings_compat(
    customer_id: Optional[int] = Query(None),
    meal_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """식단가 목록 조회 (복수형 호환성)"""
    return await get_meal_pricing(customer_id, meal_type, page, limit, db)

@router.post("/meal-pricings")
async def create_meal_pricing_compat(pricing_data: MealPricingCreate, request: Request, db: Session = Depends(get_db)):
    """식단가 등록 (복수형 호환성)"""
    return await create_meal_pricing(pricing_data, request, db)

@router.put("/meal-pricings/{pricing_id}")
async def update_meal_pricing_compat(pricing_id: int, pricing_data: MealPricingCreate, request: Request, db: Session = Depends(get_db)):
    """식단가 수정 (복수형 호환성)"""
    return await update_meal_pricing(pricing_id, pricing_data, request, db)

@router.delete("/meal-pricings/{pricing_id}")
async def delete_meal_pricing_compat(pricing_id: int, request: Request, db: Session = Depends(get_db)):
    """식단가 삭제 (복수형 호환성)"""
    return await delete_meal_pricing(pricing_id, request, db)

@router.get("/meal-pricing-stats")
async def get_meal_pricing_stats_compat(db: Session = Depends(get_db)):
    """식단가 통계 (호환성)"""
    return await get_meal_pricing_statistics(db)# Trigger reload

# Trigger reload
