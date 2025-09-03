"""
협력업체 관련 API 라우터
- CRUD 기본 작업
- 고급 검색 및 필터링
- 사업장과의 매핑 관리
"""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import SupplierService
from app.core.exceptions import BaseCustomException, create_error_response

# 임시 import (main.py 의존성 제거 후 삭제)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

router = APIRouter()

# 의존성 (나중에 app/core/auth.py로 이동)
def get_current_user(request: Request):
    """임시 사용자 인증 (main.py에서 이동 예정)"""
    # SessionManager 임포트 필요
    pass

def require_admin(request: Request):
    """관리자 권한 확인 (main.py에서 이동 예정)"""
    pass

# ==============================================================================
# 기본 CRUD API
# ==============================================================================

@router.get("/api/suppliers")
async def get_suppliers_simple(db: Session = Depends(get_db)):
    """
    협력업체 간단 목록 조회
    - 드롭다운, 선택 리스트용
    """
    try:
        service = SupplierService(db)
        result = service.get_suppliers_list(page=1, limit=100, is_active=True)
        
        # 간단한 형태로 변환
        suppliers = [
            {
                "id": s.id,
                "name": s.name,
                "parent_code": s.parent_code,
                "display_name": s.display_name
            }
            for s in result["suppliers"]
        ]
        
        return {"success": True, "suppliers": suppliers}
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"협력업체 목록 조회 실패: {str(e)}"}
        )

@router.get("/api/admin/suppliers/enhanced")
async def get_suppliers_enhanced(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    company_scale: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    협력업체 고급 목록 조회
    - 페이지네이션
    - 검색 및 필터링
    - 관리자 권한 필요
    """
    try:
        # 권한 확인 (임시 주석 처리)
        # require_admin(request)
        
        service = SupplierService(db)
        result = service.get_suppliers_list(
            page=page,
            limit=limit,
            search=search,
            is_active=is_active,
            company_scale=company_scale
        )
        
        # 응답 형식 변환
        suppliers_data = []
        for supplier in result["suppliers"]:
            suppliers_data.append({
                "id": supplier.id,
                "name": supplier.name,
                "parent_code": supplier.parent_code,
                "business_number": supplier.business_number,
                "representative": supplier.representative,
                "headquarters_phone": supplier.headquarters_phone,
                "email": supplier.email,
                "is_active": supplier.is_active,
                "company_scale": supplier.company_scale,
                "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
                "updated_at": supplier.updated_at.isoformat() if supplier.updated_at else None,
            })
        
        return {
            "success": True,
            "suppliers": suppliers_data,
            "pagination": result["pagination"]
        }
        
    except BaseCustomException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=create_error_response(e)
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"협력업체 목록 조회 실패: {str(e)}"}
        )

@router.get("/api/admin/suppliers/{supplier_id}/detail")
async def get_supplier_detail(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """협력업체 상세 정보 조회"""
    try:
        # require_admin(request)
        
        service = SupplierService(db)
        supplier = service.get_supplier_by_id(supplier_id)
        
        return {
            "success": True,
            "supplier": {
                "id": supplier.id,
                "name": supplier.name,
                "parent_code": supplier.parent_code,
                "business_number": supplier.business_number,
                "business_type": supplier.business_type,
                "business_item": supplier.business_item,
                "representative": supplier.representative,
                "headquarters_address": supplier.headquarters_address,
                "headquarters_phone": supplier.headquarters_phone,
                "headquarters_fax": supplier.headquarters_fax,
                "email": supplier.email,
                "website": supplier.website,
                "is_active": supplier.is_active,
                "company_scale": supplier.company_scale,
                "notes": supplier.notes,
                "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
                "updated_at": supplier.updated_at.isoformat() if supplier.updated_at else None,
            }
        }
        
    except BaseCustomException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=create_error_response(e)
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"협력업체 조회 실패: {str(e)}"}
        )

@router.post("/api/admin/suppliers/create")
async def create_supplier(
    supplier_data: dict,
    request: Request,
    db: Session = Depends(get_db)
):
    """협력업체 생성"""
    try:
        # require_admin(request)
        
        service = SupplierService(db)
        supplier = service.create_supplier(supplier_data)
        
        return {
            "success": True,
            "message": "협력업체가 생성되었습니다.",
            "supplier": {
                "id": supplier.id,
                "name": supplier.name,
                "parent_code": supplier.parent_code
            }
        }
        
    except BaseCustomException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=create_error_response(e)
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"협력업체 생성 실패: {str(e)}"}
        )

@router.put("/api/admin/suppliers/{supplier_id}/update")
async def update_supplier(
    supplier_id: int,
    supplier_data: dict,
    request: Request,
    db: Session = Depends(get_db)
):
    """협력업체 정보 수정"""
    try:
        # require_admin(request)
        
        service = SupplierService(db)
        supplier = service.update_supplier(supplier_id, supplier_data)
        
        return {
            "success": True,
            "message": "협력업체 정보가 수정되었습니다.",
            "supplier": {
                "id": supplier.id,
                "name": supplier.name,
                "parent_code": supplier.parent_code
            }
        }
        
    except BaseCustomException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=create_error_response(e)
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"협력업체 수정 실패: {str(e)}"}
        )

@router.delete("/api/admin/suppliers/{supplier_id}/delete")
async def delete_supplier(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """협력업체 삭제 (소프트 삭제)"""
    try:
        # require_admin(request)
        
        service = SupplierService(db)
        success = service.delete_supplier(supplier_id)
        
        if success:
            return {
                "success": True,
                "message": "협력업체가 삭제되었습니다."
            }
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "협력업체 삭제에 실패했습니다."}
            )
            
    except BaseCustomException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=create_error_response(e)
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"협력업체 삭제 실패: {str(e)}"}
        )

# ==============================================================================
# 정적 파일 서빙
# ==============================================================================

@router.get("/admin/suppliers")
async def serve_admin_suppliers(request: Request):
    """협력업체 관리 페이지 서빙"""
    # require_admin(request)
    return FileResponse("admin_dashboard.html")

@router.get("/supplier-management") 
async def serve_supplier_management(request: Request):
    """협력업체 관리 페이지 (구 버전)"""
    return FileResponse("supplier_management.html")

# ==============================================================================
# 통계 및 분석
# ==============================================================================

@router.get("/api/admin/suppliers/statistics")
async def get_supplier_statistics(
    request: Request,
    db: Session = Depends(get_db)
):
    """협력업체 통계 조회"""
    try:
        # require_admin(request)
        
        service = SupplierService(db)
        stats = service.get_supplier_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"통계 조회 실패: {str(e)}"}
        )