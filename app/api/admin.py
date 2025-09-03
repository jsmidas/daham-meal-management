"""
관리자 API 라우터
- 관리자 대시보드
- 사용자 관리
- 사이트 관리
- 식재료 관리
- 기타 관리자 기능
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query, File, UploadFile
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
import hashlib
import secrets
import json

# 로컬 임포트
from app.database import get_db, DATABASE_URL
from app.api.auth import get_current_user
from models import User, Customer, Supplier, Ingredient, MealCount, MealPricing

router = APIRouter()

# ==============================================================================
# Pydantic 모델 정의
# ==============================================================================

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    department: Optional[str] = None
    position: Optional[str] = None
    managed_site: Optional[str] = None
    contact_info: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    managed_site: Optional[str] = None
    contact_info: Optional[str] = None
    is_active: Optional[bool] = None

class SiteCreate(BaseModel):
    name: str
    code: Optional[str] = None
    site_type: Optional[str] = "일반"
    parent_id: Optional[int] = None
    level: Optional[int] = 1
    sort_order: Optional[int] = 0
    description: Optional[str] = None

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    site_type: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[int] = None
    sort_order: Optional[int] = None
    description: Optional[str] = None

class MealCountCreate(BaseModel):
    site_id: int
    date: date
    breakfast_count: Optional[int] = 0
    lunch_count: Optional[int] = 0
    dinner_count: Optional[int] = 0
    snack_count: Optional[int] = 0
    notes: Optional[str] = None

class MealCountUpdate(BaseModel):
    breakfast_count: Optional[int] = None
    lunch_count: Optional[int] = None
    dinner_count: Optional[int] = None
    snack_count: Optional[int] = None
    notes: Optional[str] = None

class MealPricingCreate(BaseModel):
    customer_id: int
    meal_type: str
    price: Decimal
    effective_date: date
    notes: Optional[str] = None

# ==============================================================================
# 관리자 페이지 서빙
# ==============================================================================

@router.get("/admin")
async def serve_admin_dashboard(request: Request):
    """관리자 대시보드 페이지 서빙 (로그인 필요)"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    print(f"[DEBUG] User role check: '{user['role']}' - type: {type(user['role'])}")
    # 한글 인코딩 문제로 인해 영문 role로 변경
    valid_roles = ['admin', 'nutritionist', 'manager', '관리자', '영양사', '매니저']
    if user['role'] not in valid_roles:
        print(f"[DEBUG] Role '{user['role']}' not in valid roles: {valid_roles}")
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    return FileResponse("admin_dashboard.html")

@router.get("/admin/ingredient-upload-test")
async def serve_ingredient_upload_test():
    """식재료 업로드 테스트 페이지"""
    return FileResponse("templates/ingredient_upload_test.html")

@router.get("/admin/simple-test")  
async def serve_simple_test():
    """간단한 테스트 페이지"""
    return FileResponse("templates/simple_test.html")

@router.get("/admin/suppliers")
async def serve_admin_suppliers(request: Request):
    """관리자 협력업체관리 페이지 서빙 (관리자 권한 필요)"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # 관리자 권한 확인
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    return FileResponse("templates/admin_suppliers.html")

@router.get("/admin/ingredient-upload")
async def serve_ingredient_upload(request: Request):
    """관리자 식재료 업로드 페이지 서빙 (관리자 권한 필요)"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # 관리자 권한 확인
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    return FileResponse("templates/admin_ingredient_upload.html")

# ==============================================================================
# 관리자 권한 확인
# ==============================================================================

@router.get("/api/admin/check-access")
async def check_admin_access(request: Request):
    """관리자 접근 권한 확인"""
    try:
        user = get_current_user(request)
        if not user:
            return {"success": False, "message": "인증이 필요합니다.", "has_access": False}
        
        admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
        has_admin_access = user['role'] in admin_roles
        
        return {
            "success": True,
            "has_access": has_admin_access,
            "user": {
                "username": user['username'],
                "role": user['role'],
                "department": user.get('department', ''),
                "position": user.get('position', '')
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e), "has_access": False}

# ==============================================================================
# 대시보드 통계 API
# ==============================================================================

@router.get("/api/admin/dashboard-stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """관리자 대시보드 통계 데이터"""
    try:
        # 사용자 수 (임시 데이터)
        total_users = 5
        active_users = 4
        
        # 사업장 수
        total_sites = db.query(Customer).count()
        
        # 협력업체 수
        total_suppliers = db.query(Supplier).count()
        
        # 식재료 수
        total_ingredients = db.query(Ingredient).count()
        
        # 오늘 급식수
        today = datetime.now().date()
        today_meal_counts = db.query(MealCount).filter(MealCount.date == today).all()
        today_total_meals = sum([
            (mc.breakfast_count or 0) + (mc.lunch_count or 0) + (mc.dinner_count or 0) + (mc.snack_count or 0)
            for mc in today_meal_counts
        ])
        
        return {
            "success": True,
            "stats": {
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "inactive": total_users - active_users
                },
                "sites": {
                    "total": total_sites,
                    "active": total_sites  # 임시로 모두 활성으로 설정
                },
                "suppliers": {
                    "total": total_suppliers,
                    "active": total_suppliers  # 임시로 모두 활성으로 설정
                },
                "ingredients": {
                    "total": total_ingredients
                },
                "meals": {
                    "today": today_total_meals
                }
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/api/admin/recent-activity")
async def get_recent_activity():
    """최근 활동 내역 조회"""
    try:
        # 임시 데이터 (실제로는 활동 로그 테이블에서 조회)
        activities = [
            {
                "id": 1,
                "type": "user_login",
                "description": "관리자(admin)가 로그인했습니다.",
                "timestamp": "2025-08-30 14:30:25",
                "user": "admin",
                "ip_address": "127.0.0.1"
            },
            {
                "id": 2,
                "type": "ingredient_upload",
                "description": "새로운 식재료 50개가 업로드되었습니다.",
                "timestamp": "2025-08-30 13:45:12",
                "user": "nutritionist1",
                "ip_address": "192.168.1.100"
            },
            {
                "id": 3,
                "type": "menu_update",
                "description": "9월 1주차 식단이 수정되었습니다.",
                "timestamp": "2025-08-30 11:20:33",
                "user": "nutritionist2",
                "ip_address": "192.168.1.101"
            },
            {
                "id": 4,
                "type": "user_created",
                "description": "새 사용자(chef1)가 생성되었습니다.",
                "timestamp": "2025-08-30 10:15:44",
                "user": "admin",
                "ip_address": "127.0.0.1"
            },
            {
                "id": 5,
                "type": "site_updated",
                "description": "사업장 'A동 1층 사무실' 정보가 수정되었습니다.",
                "timestamp": "2025-08-30 09:30:15",
                "user": "manager1",
                "ip_address": "192.168.1.102"
            }
        ]
        
        return {"success": True, "activities": activities}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ==============================================================================
# 사용자 관리 API
# ==============================================================================

@router.get("/api/admin/users")
async def get_users(page: int = Query(1, ge=1), limit: int = Query(20, ge=1, le=100), search: str = Query(""), db: Session = Depends(get_db)):
    """사용자 목록 조회"""
    try:
        # 임시 사용자 데이터 (실제로는 User 테이블에서 조회)
        sample_users = [
            {
                "id": 1,
                "username": "admin",
                "role": "admin",
                "department": "관리부",
                "position": "관리자",
                "managed_site": "본사",
                "is_active": True,
                "last_login": "2025-08-30 14:30",
                "contact_info": "010-1234-5678",
                "created_at": "2025-01-01 09:00:00"
            },
            {
                "id": 2,
                "username": "nutritionist1",
                "role": "nutritionist",
                "department": "영양팀",
                "position": "영양사",
                "managed_site": "A동",
                "is_active": True,
                "last_login": "2025-08-30 13:45",
                "contact_info": "010-2345-6789",
                "created_at": "2025-01-02 10:00:00"
            },
            {
                "id": 3,
                "username": "manager1",
                "role": "manager",
                "department": "운영팀",
                "position": "매니저",
                "managed_site": "B동",
                "is_active": True,
                "last_login": "2025-08-29 16:20",
                "contact_info": "010-3456-7890",
                "created_at": "2025-01-03 11:00:00"
            },
            {
                "id": 4,
                "username": "chef1",
                "role": "chef",
                "department": "조리팀",
                "position": "조리사",
                "managed_site": "중앙주방",
                "is_active": True,
                "last_login": "2025-08-29 08:30",
                "contact_info": "010-4567-8901",
                "created_at": "2025-01-04 12:00:00"
            },
            {
                "id": 5,
                "username": "inactive_user",
                "role": "user",
                "department": "기타",
                "position": "사용자",
                "managed_site": "",
                "is_active": False,
                "last_login": "2025-08-20 15:00",
                "contact_info": "010-5678-9012",
                "created_at": "2025-01-05 13:00:00"
            }
        ]
        
        # 검색 필터 적용
        if search:
            search_term = search.lower()
            sample_users = [
                user for user in sample_users
                if (search_term in user['username'].lower() or 
                    search_term in user['department'].lower() or
                    search_term in user['position'].lower())
            ]
        
        total = len(sample_users)
        
        # 페이징 적용
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        users = sample_users[start_idx:end_idx]
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "success": True,
            "users": users,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/admin/users/{user_id}")
async def get_user_detail(user_id: int, db: Session = Depends(get_db)):
    """특정 사용자 상세 정보 조회"""
    try:
        # 임시 데이터 (실제로는 User 테이블에서 조회)
        if user_id == 1:
            user_data = {
                "id": 1,
                "username": "admin",
                "role": "admin",
                "department": "관리부",
                "position": "관리자",
                "managed_site": "본사",
                "is_active": True,
                "last_login": "2025-08-30 14:30:25",
                "contact_info": "010-1234-5678",
                "created_at": "2025-01-01 09:00:00",
                "updated_at": "2025-01-01 09:00:00"
            }
        else:
            return {"success": False, "message": "사용자를 찾을 수 없습니다."}
        
        return {"success": True, "user": user_data}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/admin/users")
async def create_user(user_data: UserCreate, request: Request):
    """새 사용자 생성"""
    # 인증 및 권한 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    if user['role'] not in ['admin', '관리자']:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        # 비밀번호 해싱
        salt = secrets.token_hex(32)
        password_hash = hashlib.sha256((user_data.password + salt).encode()).hexdigest()
        
        # TODO: 실제 User 모델에 저장
        # new_user = User(
        #     username=user_data.username,
        #     password_hash=password_hash,
        #     salt=salt,
        #     role=user_data.role,
        #     department=user_data.department,
        #     position=user_data.position,
        #     managed_site=user_data.managed_site,
        #     contact_info=user_data.contact_info,
        #     is_active=True,
        #     created_at=datetime.now()
        # )
        
        return {
            "success": True,
            "message": "사용자가 성공적으로 생성되었습니다.",
            "user_id": 999  # 임시 ID
        }
    except Exception as e:
        return {"success": False, "message": f"사용자 생성 중 오류가 발생했습니다: {str(e)}"}

@router.put("/api/admin/users/{user_id}")
async def update_user(user_id: int, user_data: UserUpdate, request: Request):
    """사용자 정보 수정"""
    # 인증 및 권한 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    if user['role'] not in ['admin', '관리자']:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        # TODO: 실제 User 모델에서 업데이트
        return {"success": True, "message": "사용자 정보가 수정되었습니다."}
    except Exception as e:
        return {"success": False, "message": f"사용자 정보 수정 중 오류가 발생했습니다: {str(e)}"}

@router.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: int, request: Request):
    """사용자 삭제"""
    # 인증 및 권한 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    if user['role'] not in ['admin', '관리자']:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        if user_id == 1:  # 관리자 계정은 삭제 불가
            return {"success": False, "message": "관리자 계정은 삭제할 수 없습니다."}
        
        # TODO: 실제 User 모델에서 삭제 또는 비활성화
        return {"success": True, "message": "사용자가 삭제되었습니다."}
    except Exception as e:
        return {"success": False, "message": f"사용자 삭제 중 오류가 발생했습니다: {str(e)}"}

@router.post("/api/admin/users/{user_id}/reset-password")
async def reset_user_password(user_id: int, request: Request):
    """사용자 비밀번호 초기화"""
    # 인증 및 권한 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    if user['role'] not in ['admin', '관리자']:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        # 임시 비밀번호 생성
        temp_password = secrets.token_urlsafe(8)
        
        # TODO: 실제 비밀번호 업데이트 로직
        
        return {
            "success": True,
            "message": "비밀번호가 초기화되었습니다.",
            "temp_password": temp_password
        }
    except Exception as e:
        return {"success": False, "message": f"비밀번호 초기화 중 오류가 발생했습니다: {str(e)}"}

# ==============================================================================
# 사이트 관리 API (사업장 관리와 별개의 시스템 사이트)
# ==============================================================================

@router.get("/api/admin/sites")
async def get_sites(db: Session = Depends(get_db)):
    """사이트 목록 조회"""
    try:
        # 임시 데이터 (실제로는 Site 테이블에서 조회)
        sites = [
            {
                "id": 1,
                "name": "본사",
                "code": "HQ",
                "site_type": "본사",
                "parent_id": None,
                "level": 0,
                "sort_order": 1,
                "description": "본사 사이트",
                "created_at": "2025-01-01 09:00:00"
            },
            {
                "id": 2,
                "name": "A동",
                "code": "A",
                "site_type": "사무동",
                "parent_id": 1,
                "level": 1,
                "sort_order": 1,
                "description": "A동 사무실",
                "created_at": "2025-01-02 09:00:00"
            }
        ]
        
        return {"success": True, "sites": sites}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/api/admin/sites/tree")
async def get_sites_tree():
    """사이트 트리 구조 조회"""
    try:
        # 임시 트리 데이터
        tree_data = [
            {
                "id": 1,
                "name": "본사",
                "code": "HQ",
                "level": 0,
                "children": [
                    {
                        "id": 2,
                        "name": "A동",
                        "code": "A",
                        "level": 1,
                        "children": []
                    },
                    {
                        "id": 3,
                        "name": "B동",
                        "code": "B", 
                        "level": 1,
                        "children": []
                    }
                ]
            }
        ]
        
        return {"success": True, "tree": tree_data}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ==============================================================================
# 식재료 관리 API
# ==============================================================================

@router.get("/api/admin/ingredients")
async def get_ingredients_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: str = Query(""),
    category: str = Query(""),
    db: Session = Depends(get_db)
):
    """관리자용 식재료 목록 조회"""
    try:
        query = db.query(Ingredient)
        
        # 검색 조건
        if search:
            search_term = f"%{search}%"
            query = query.filter(Ingredient.name.ilike(search_term))
        
        if category:
            query = query.filter(Ingredient.category == category)
        
        total = query.count()
        
        # 페이징
        offset = (page - 1) * limit
        ingredients = query.offset(offset).limit(limit).all()
        
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_list.append({
                "id": ingredient.id,
                "name": ingredient.name,
                "category": ingredient.category,
                "unit": ingredient.unit,
                "cost_per_unit": float(ingredient.cost_per_unit) if ingredient.cost_per_unit else 0,
                "supplier_id": ingredient.supplier_id,
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

@router.get("/api/admin/ingredient-template")
async def get_ingredient_template():
    """식재료 업로드 템플릿 다운로드"""
    try:
        template_data = {
            "headers": ["이름", "카테고리", "단위", "단가", "공급업체ID", "설명"],
            "sample_data": [
                ["양파", "채소류", "kg", "2000", "1", "국내산 양파"],
                ["당근", "채소류", "kg", "2500", "1", "국내산 당근"],
                ["감자", "채소류", "kg", "3000", "2", "국내산 감자"]
            ]
        }
        return {"success": True, "template": template_data}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/admin/upload-ingredients")
async def upload_ingredients(request: Request, file: UploadFile = File(...)):
    """식재료 일괄 업로드"""
    # 인증 및 권한 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            return {"success": False, "message": "CSV 또는 Excel 파일만 업로드 가능합니다."}
        
        # TODO: 파일 처리 로직 구현
        # - 파일 읽기 (pandas 사용)
        # - 데이터 검증
        # - 데이터베이스에 저장
        
        return {
            "success": True,
            "message": "식재료 데이터가 성공적으로 업로드되었습니다.",
            "uploaded_count": 0  # 임시값
        }
    except Exception as e:
        return {"success": False, "message": f"파일 업로드 중 오류가 발생했습니다: {str(e)}"}

# ==============================================================================
# 급식수 관리 API
# ==============================================================================

@router.get("/api/admin/meal-counts")
async def get_meal_counts_admin(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    site_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """관리자용 급식수 목록 조회"""
    try:
        query = db.query(MealCount)
        
        # 필터링
        if start_date:
            query = query.filter(MealCount.date >= start_date)
        if end_date:
            query = query.filter(MealCount.date <= end_date)
        if site_id:
            query = query.filter(MealCount.site_id == site_id)
        
        total = query.count()
        
        # 페이징
        offset = (page - 1) * limit
        meal_counts = query.order_by(MealCount.date.desc()).offset(offset).limit(limit).all()
        
        meal_count_list = []
        for mc in meal_counts:
            meal_count_list.append({
                "id": mc.id,
                "site_id": mc.site_id,
                "date": mc.date.isoformat(),
                "breakfast_count": mc.breakfast_count or 0,
                "lunch_count": mc.lunch_count or 0,
                "dinner_count": mc.dinner_count or 0,
                "snack_count": mc.snack_count or 0,
                "total_count": (mc.breakfast_count or 0) + (mc.lunch_count or 0) + (mc.dinner_count or 0) + (mc.snack_count or 0),
                "notes": mc.notes,
                "created_at": mc.created_at.isoformat() if mc.created_at else None
            })
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "success": True,
            "meal_counts": meal_count_list,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/admin/meal-counts")
async def create_meal_count(meal_count_data: MealCountCreate, request: Request, db: Session = Depends(get_db)):
    """급식수 생성"""
    # 인증 및 권한 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    try:
        # 중복 체크
        existing = db.query(MealCount).filter(
            MealCount.site_id == meal_count_data.site_id,
            MealCount.date == meal_count_data.date
        ).first()
        
        if existing:
            return {"success": False, "message": "해당 날짜의 급식수가 이미 존재합니다."}
        
        new_meal_count = MealCount(
            site_id=meal_count_data.site_id,
            date=meal_count_data.date,
            breakfast_count=meal_count_data.breakfast_count,
            lunch_count=meal_count_data.lunch_count,
            dinner_count=meal_count_data.dinner_count,
            snack_count=meal_count_data.snack_count,
            notes=meal_count_data.notes,
            created_at=datetime.now()
        )
        
        db.add(new_meal_count)
        db.commit()
        db.refresh(new_meal_count)
        
        return {
            "success": True,
            "message": "급식수가 성공적으로 생성되었습니다.",
            "meal_count_id": new_meal_count.id
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"급식수 생성 중 오류가 발생했습니다: {str(e)}"}

# ==============================================================================
# 급식 단가 관리 API
# ==============================================================================

@router.post("/api/admin/meal-pricing")
async def create_meal_pricing(pricing_data: MealPricingCreate, request: Request, db: Session = Depends(get_db)):
    """급식 단가 설정"""
    # 인증 및 권한 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        new_pricing = MealPricing(
            customer_id=pricing_data.customer_id,
            meal_type=pricing_data.meal_type,
            price=pricing_data.price,
            effective_date=pricing_data.effective_date,
            notes=pricing_data.notes,
            created_at=datetime.now()
        )
        
        db.add(new_pricing)
        db.commit()
        db.refresh(new_pricing)
        
        return {
            "success": True,
            "message": "급식 단가가 설정되었습니다.",
            "pricing_id": new_pricing.id
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"단가 설정 중 오류가 발생했습니다: {str(e)}"}

@router.get("/api/admin/meal-pricing")
async def get_meal_pricing(
    customer_id: Optional[int] = Query(None),
    meal_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """급식 단가 조회"""
    try:
        query = db.query(MealPricing)
        
        # 필터링
        if customer_id:
            query = query.filter(MealPricing.customer_id == customer_id)
        if meal_type:
            query = query.filter(MealPricing.meal_type == meal_type)
        
        total = query.count()
        
        # 페이징
        offset = (page - 1) * limit
        pricings = query.order_by(MealPricing.effective_date.desc()).offset(offset).limit(limit).all()
        
        pricing_list = []
        for pricing in pricings:
            pricing_list.append({
                "id": pricing.id,
                "customer_id": pricing.customer_id,
                "meal_type": pricing.meal_type,
                "price": float(pricing.price),
                "effective_date": pricing.effective_date.isoformat(),
                "notes": pricing.notes,
                "created_at": pricing.created_at.isoformat() if pricing.created_at else None
            })
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "success": True,
            "pricings": pricing_list,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    except Exception as e:
        return {"success": False, "message": str(e)}