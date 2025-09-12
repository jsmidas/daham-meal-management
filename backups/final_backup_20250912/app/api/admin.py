"""
모듈화된 관리자 API - 핵심 기능만 포함
- 사용자 관리: admin_users.py로 이동
- 사업장 관리: admin_sites.py로 이동  
- 식재료 관리: admin_ingredients.py로 이동
- 식단가 관리: admin_mealpricing.py로 이동
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
import hashlib
import secrets
import pandas as pd
import io
import os

# 로컬 임포트
from app.database import get_db
from app.api.auth import get_current_user
from models import User, Customer, Supplier, Ingredient, MealCount, MealPricing, IngredientUploadHistory

router = APIRouter(prefix="/api", tags=["admin"])

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
# 페이지 서빙 엔드포인트 (간소화)
# ==============================================================================

@router.get("/admin/ingredient-upload-test")
async def serve_ingredient_upload_test():
    """식재료 업로드 테스트 페이지"""
    return FileResponse("templates/ingredient_upload_test.html")

@router.get("/admin/ingredient-upload")
async def serve_ingredient_upload(request: Request):
    """관리자 식재료 업로드 페이지 서빙"""
    user = get_current_user(request)
    if not user or user['role'] not in ['admin', 'manager', '관리자', '매니저', 'nutritionist']:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다.")
    
    return FileResponse("templates/admin_ingredient_upload.html")

# ==============================================================================
# 통계/대시보드 API
# ==============================================================================

@router.get("/admin/dashboard-stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """관리자 대시보드 통계 (핵심 통계만)"""
    try:
        # 기본 통계
        total_users = db.query(User).count()
        total_suppliers = db.query(Supplier).count()
        total_sites = db.query(Customer).count()
        total_ingredients = db.query(Ingredient).count()
        
        # 최근 활동 (간소화)
        recent_activities = [
            {
                "id": 1,
                "type": "user_login",
                "description": f"총 {total_users}명의 사용자가 등록되어 있습니다.",
                "timestamp": datetime.now().isoformat(),
                "user": "시스템"
            }
        ]
        
        # 메뉴별 통계
        stats = {
            "users": {
                "total": total_users,
                "active": total_users  # 간소화
            },
            "suppliers": {
                "total": total_suppliers,
                "active": total_suppliers  # 간소화
            },
            "sites": {
                "total": total_sites,
                "active": total_sites  # 간소화
            },
            "ingredients": {
                "total": total_ingredients
            }
        }
        
        return {
            "success": True,
            "stats": stats,
            "recent_activities": recent_activities
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"통계 조회 중 오류 발생: {str(e)}"
        }

# ==============================================================================
# 간단한 테스트 엔드포인트들 (기존 유지)
# ==============================================================================

@router.post("/create-user-simple")
async def create_user_simple(db: Session = Depends(get_db)):
    """간단한 사용자 생성 (테스트용)"""
    try:
        username = f"user_{secrets.token_hex(4)}"
        password = "password123"
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        new_user = User(
            username=username,
            password_hash=hashed_password,
            name=f"테스트 사용자 {username}",
            role="user",
            is_active=True,
            created_at=datetime.now()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "success": True,
            "message": "테스트 사용자 생성 완료",
            "user": {
                "id": new_user.id,
                "username": username,
                "password": password,
                "name": new_user.name
            }
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"사용자 생성 실패: {str(e)}"}

@router.get("/list-users-simple")
async def list_users_simple(db: Session = Depends(get_db)):
    """간단한 사용자 목록 (테스트용)"""
    try:
        users = db.query(User).limit(10).all()
        
        return {
            "success": True,
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "role": user.role,
                    "is_active": user.is_active
                }
                for user in users
            ]
        }
        
    except Exception as e:
        return {"success": False, "message": f"사용자 목록 조회 실패: {str(e)}"}

# ==============================================================================
# 급식수 관리 API (핵심 기능만)
# ==============================================================================

class MealCountCreate(BaseModel):
    site_id: int
    meal_type: str  # breakfast, lunch, dinner, snack
    target_date: date
    planned_count: int
    actual_count: Optional[int] = None
    notes: Optional[str] = None

@router.get("/api/admin/meal-counts")
async def get_meal_counts(
    site_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """급식수 목록 조회 (간소화)"""
    try:
        query = db.query(MealCount)
        
        if site_id:
            query = query.filter(MealCount.site_id == site_id)
            
        meal_counts = query.limit(100).all()  # 간소화: 최대 100개만
        
        return {
            "success": True,
            "meal_counts": [
                {
                    "id": mc.id,
                    "site_id": mc.site_id,
                    "meal_type": mc.meal_type,
                    "planned_count": mc.planned_count,
                    "actual_count": mc.actual_count,
                    "target_date": mc.target_date.isoformat() if mc.target_date else None,
                    "created_at": mc.created_at.isoformat() if mc.created_at else None
                }
                for mc in meal_counts
            ]
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/admin/meal-counts")
async def create_meal_count(meal_count_data: MealCountCreate, request: Request, db: Session = Depends(get_db)):
    """급식수 등록"""
    verify_admin_access(request)
    
    try:
        new_meal_count = MealCount(**meal_count_data.dict(), created_at=datetime.now())
        db.add(new_meal_count)
        db.commit()
        db.refresh(new_meal_count)
        
        return {"success": True, "message": "급식수가 등록되었습니다.", "meal_count_id": new_meal_count.id}
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"급식수 등록 중 오류: {str(e)}"}

# ==============================================================================
# 기본 헬스체크
# ==============================================================================

@router.get("/admin/recent-activity")
async def get_recent_activity():
    """최근 활동 내역 조회 (대시보드용)"""
    try:
        # 임시로 더미 데이터 반환
        recent_activities = [
            {
                "id": 1,
                "type": "user_login",
                "message": "사용자 로그인",
                "user": "admin",
                "timestamp": "2025-09-08T10:30:00"
            },
            {
                "id": 2,
                "type": "ingredient_upload",
                "message": "식재료 업로드 완료",
                "user": "nutritionist",
                "timestamp": "2025-09-08T09:15:00"
            },
            {
                "id": 3,
                "type": "site_created",
                "message": "새 사업장 등록",
                "user": "admin",
                "timestamp": "2025-09-08T08:45:00"
            }
        ]
        
        return {
            "success": True,
            "activities": recent_activities
        }
        
    except Exception as e:
        return {"success": False, "message": f"최근 활동 조회 중 오류: {str(e)}"}

@router.get("/admin/health")
async def admin_health_check():
    """관리자 API 헬스체크"""
    return {
        "status": "healthy",
        "module": "admin_core",
        "version": "2.0.0",
        "modularized": True,
        "message": "핵심 관리자 기능만 포함된 간소화된 모듈"
    }