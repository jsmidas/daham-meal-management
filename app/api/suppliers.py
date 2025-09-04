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
# from app.services import SupplierService  # Temporarily disabled due to model mismatch
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from models import Supplier
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
        suppliers = db.query(Supplier).filter(Supplier.is_active == True).limit(100).all()
        
        # 간단한 형태로 변환
        suppliers_data = [
            {
                "id": s.id,
                "name": s.name,
                "parent_code": s.parent_code,
                "display_name": f"{s.name} ({s.parent_code})"
            }
            for s in suppliers
        ]
        
        return {"success": True, "suppliers": suppliers_data}
        
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
        
        # 기본 쿼리
        query = db.query(Supplier)
        
        # 필터 적용
        if search:
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    Supplier.name.like(f"%{search}%"),
                    Supplier.parent_code.like(f"%{search}%"),
                    Supplier.business_number.like(f"%{search}%"),
                    Supplier.representative.like(f"%{search}%")
                )
            )
        
        if is_active is not None:
            query = query.filter(Supplier.is_active == is_active)
        else:
            # 기본값으로 활성화된 협력업체만 표시
            query = query.filter(Supplier.is_active == True)
            
        if company_scale:
            query = query.filter(Supplier.company_scale == company_scale)
        
        # 총 개수 조회
        total_count = query.count()
        total_pages = (total_count + limit - 1) // limit
        
        # 페이지네이션 적용
        offset = (page - 1) * limit
        suppliers = query.order_by(
            Supplier.name
        ).offset(offset).limit(limit).all()
        
        # 응답 형식 변환
        suppliers_data = []
        for supplier in suppliers:
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
                "created_at": supplier.created_at.isoformat() if hasattr(supplier, 'created_at') and supplier.created_at else None,
                "updated_at": supplier.updated_at.isoformat() if hasattr(supplier, 'updated_at') and supplier.updated_at else None,
            })
        
        return {
            "success": True,
            "suppliers": suppliers_data,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
                "limit": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
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
        
        # SupplierService 대신 직접 데이터베이스 조회
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        
        if not supplier:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "협력업체를 찾을 수 없습니다."}
            )
        
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
                # 웹 인터페이스 호환을 위한 필드명
                "address": supplier.headquarters_address,
                "phone": supplier.headquarters_phone,
                "fax": supplier.headquarters_fax,
                # 데이터베이스 필드명도 유지 (하위 호환성)
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
        
    except Exception as e:
        # 로깅 제거 (한글 인코딩 문제 방지)
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"협력업체 조회 실패: {str(e)}"}
        )

@router.post("/api/admin/suppliers/create")
async def create_supplier(
    request: Request,
    db: Session = Depends(get_db)
):
    """협력업체 생성"""
    try:
        # require_admin(request)
        
        # Request body에서 JSON 데이터 가져오기 (인코딩 안전 처리)
        try:
            supplier_data = await request.json()
        except UnicodeDecodeError:
            # 인코딩 문제가 있을 때 원본 바이트로 읽어서 처리
            body_bytes = await request.body()
            try:
                body_str = body_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # UTF-8로 디코딩 실패 시 오류 무시하고 처리
                body_str = body_bytes.decode('utf-8', errors='ignore')
            
            import json
            supplier_data = json.loads(body_str)
        
        # 로깅 제거 (한글 인코딩 문제 방지)
        
        # 필수 필드 확인
        if not supplier_data.get('name', '').strip():
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "협력업체명은 필수입니다."}
            )
        
        # 안전한 값 정리 함수
        def clean_value(value):
            """빈 문자열과 None을 NULL로 변환하고 한글 안전 처리"""
            if value is None or value == '':
                return None
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned == '':
                    return None
                # 인코딩 안전성 확인
                try:
                    cleaned.encode('utf-8')
                    return cleaned
                except UnicodeEncodeError:
                    return cleaned.encode('utf-8', errors='ignore').decode('utf-8')
            return value
        
        # 필드 안전 처리 
        clean_name = clean_value(supplier_data.get('name')) or '협력업체'
        clean_parent_code = clean_value(supplier_data.get('parent_code'))
        clean_business_number = clean_value(supplier_data.get('business_number'))
        
        # UNIQUE 제약 조건 체크
        if clean_parent_code:
            existing = db.query(Supplier).filter(Supplier.parent_code == clean_parent_code).first()
            if existing:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": f"모코드 '{clean_parent_code}'가 이미 존재합니다."}
                )
        
        if clean_business_number:
            existing = db.query(Supplier).filter(Supplier.business_number == clean_business_number).first()
            if existing:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": f"사업자번호 '{clean_business_number}'가 이미 존재합니다."}
                )
            
        # 새로운 협력업체 생성
        new_supplier = Supplier(
            name=clean_name,
            parent_code=clean_parent_code,
            business_number=clean_business_number,
            business_type=clean_value(supplier_data.get('business_type')),
            business_item=clean_value(supplier_data.get('business_item')),
            representative=clean_value(supplier_data.get('representative')),
            headquarters_address=clean_value(supplier_data.get('address')),
            headquarters_phone=clean_value(supplier_data.get('phone')),
            headquarters_fax=clean_value(supplier_data.get('fax')),
            email=clean_value(supplier_data.get('email')),
            website=clean_value(supplier_data.get('website')),
            is_active=True,  # 새로 생성되는 협력업체는 활성화
            company_scale=clean_value(supplier_data.get('company_scale')),
            notes=clean_value(supplier_data.get('notes'))
        )
        # 데이터베이스에 추가 (디버깅 로그 제거)
        try:
            db.add(new_supplier)
            db.commit()
            db.refresh(new_supplier)
        except Exception as e:
            db.rollback()
            if "UNIQUE constraint failed" in str(e):
                if "parent_code" in str(e):
                    error_message = "모코드가 이미 존재합니다. 다른 모코드를 사용해주세요."
                elif "business_number" in str(e):
                    error_message = "사업자번호가 이미 존재합니다. 다른 사업자번호를 사용해주세요."
                else:
                    error_message = "중복된 데이터가 존재합니다. 다른 값을 사용해주세요."
                return JSONResponse(
                    status_code=400, 
                    content={"success": False, "message": error_message}
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content={"success": False, "message": f"협력업체 생성 실패: {str(e)}"}
                )
        
        # 안전한 응답 생성 (한글 인코딩 문제 방지)
        try:
            response_data = {
                "success": True,
                "message": "협력업체가 생성되었습니다.",
                "supplier": {
                    "id": new_supplier.id,
                    "name": clean_value(new_supplier.name) or "Unknown",
                    "parent_code": clean_value(new_supplier.parent_code)
                }
            }
            return response_data
        except Exception as e:
            # 완전 안전한 응답 생성
            return {
                "success": True,
                "message": "Supplier created successfully",
                "supplier": {
                    "id": new_supplier.id,
                    "name": "Created",
                    "parent_code": None
                }
            }
        
    except BaseCustomException as e:
        return JSONResponse(
            status_code=e.status_code,
            content=create_error_response(e)
        )
    except Exception as e:
        # UNIQUE 제약 위반 처리
        if "UNIQUE constraint failed" in str(e):
            if "parent_code" in str(e):
                error_message = "모코드가 이미 존재합니다. 다른 모코드를 사용해주세요."
            elif "business_number" in str(e):
                error_message = "사업자번호가 이미 존재합니다. 다른 사업자번호를 사용해주세요."
            else:
                error_message = "중복된 데이터가 존재합니다. 다른 값을 사용해주세요."
            
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": error_message}
            )
        
        # 로깅 제거 (한글 인코딩 문제 방지)
            
        try:
            error_message = f"협력업체 생성 실패: {str(e)}"
        except UnicodeEncodeError:
            error_message = "협력업체 생성 실패: 텍스트 인코딩 오류"
            
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": error_message}
        )

@router.put("/api/admin/suppliers/{supplier_id}/update")
async def update_supplier(
    supplier_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """협력업체 정보 수정"""
    try:
        # Request body에서 JSON 데이터 가져오기
        supplier_data = await request.json()
        # 로깅 제거 (한글 인코딩 문제 방지)
        
        # 협력업체 찾기
        existing_supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        
        if not existing_supplier:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "협력업체를 찾을 수 없습니다."}
            )
        
        # 필드 매핑 (웹 인터페이스 필드명 → 데이터베이스 필드명)
        field_mapping = {
            'phone': 'headquarters_phone',
            'address': 'headquarters_address', 
            'fax': 'headquarters_fax',
            'contact': 'representative',  # 'contact'를 대표자명으로 매핑
            # 직접 매핑되는 필드들
            'name': 'name',
            'parent_code': 'parent_code',
            'business_number': 'business_number',
            'business_type': 'business_type',
            'business_item': 'business_item',
            'representative': 'representative',
            'email': 'email',
            'website': 'website',
            'is_active': 'is_active',
            'company_scale': 'company_scale',
            'notes': 'notes'
        }
        
        # 필드 값 처리 함수 (빈 문자열을 None으로 처리)
        def process_field_value(value, field_name):
            """필드 값을 처리: 빈 문자열을 None으로 변환 (name 필드 제외)"""
            if field_name == 'name':  # 필수 필드는 빈 문자열도 유지
                return value if value else ''
            return value if value and value.strip() else None
        
        # 데이터 업데이트
        for key, value in supplier_data.items():
            # 매핑된 필드명 가져오기
            db_field = field_mapping.get(key)
            if db_field and hasattr(existing_supplier, db_field):
                processed_value = process_field_value(value, db_field)
                setattr(existing_supplier, db_field, processed_value)
                pass  # 업데이트 완료
            else:
                pass  # 알려지지 않은 필드 건너뛰기
        
        # 저장
        db.commit()
        db.refresh(existing_supplier)
        
        return {
            "success": True,
            "message": "협력업체 정보가 수정되었습니다.",
            "supplier": {
                "id": existing_supplier.id,
                "name": existing_supplier.name,
                "parent_code": existing_supplier.parent_code
            }
        }
        
    except Exception as e:
        # 로깅 제거 (한글 인코딩 문제 방지)
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
        
        # 협력업체 찾기
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        
        if not supplier:
            return JSONResponse(
                status_code=404,
                content={"success": False, "message": "협력업체를 찾을 수 없습니다."}
            )
        
        # 소프트 삭제 (is_active를 False로 설정)
        supplier.is_active = False
        db.commit()
        db.refresh(supplier)
        
        return {
            "success": True,
            "message": "협력업체가 삭제되었습니다."
        }
            
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
        
        # service = SupplierService(db)  # 임시 비활성화
        # stats = service.  # 임시 비활성화get_supplier_statistics()
        
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"통계 조회 실패: {str(e)}"}
        )