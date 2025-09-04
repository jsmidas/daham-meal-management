"""
사업장(고객) 관리 API 라우터
- 사업장 CRUD 작업
- 사업장-협력업체 매핑 관리
- 사업장 관련 페이지 서빙
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

# 로컬 임포트
from app.database import get_db, DATABASE_URL
from app.api.auth import get_current_user
from models import Customer, CustomerSupplierMapping
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter()

# ==============================================================================
# Pydantic 모델 정의
# ==============================================================================

class CustomerCreate(BaseModel):
    name: str
    code: Optional[str] = None
    site_type: Optional[str] = "일반"
    site_code: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[int] = 1
    sort_order: Optional[int] = 0
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    site_type: Optional[str] = None
    site_code: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[int] = None
    sort_order: Optional[int] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    portion_size: Optional[int] = None
    is_active: Optional[bool] = None

class CustomerSupplierMappingCreate(BaseModel):
    customer_id: int
    supplier_id: int
    delivery_code: str
    priority_order: Optional[int] = 1
    is_primary_supplier: Optional[bool] = False
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = True

class CustomerSupplierMappingUpdate(BaseModel):
    customer_id: Optional[int] = None
    supplier_id: Optional[int] = None
    delivery_code: Optional[str] = None
    priority_order: Optional[int] = None
    is_primary_supplier: Optional[bool] = None
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

# ==============================================================================
# 사업장 페이지 서빙
# ==============================================================================

@router.get("/admin/business-locations")
async def serve_admin_business_locations(request: Request):
    """관리자 사업장관리 페이지 서빙 (관리자 권한 필요)"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # 관리자 권한 확인
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    return FileResponse("business_location_management_v2.html")

# ==============================================================================
# 사업장 기본 API
# ==============================================================================

@router.get("/api/customers")
async def get_customers(db: Session = Depends(get_db)):
    """사업장 목록 조회 (단가관리용)"""
    try:
        customers = db.query(Customer).order_by(Customer.sort_order).all()
        
        customer_list = []
        for customer in customers:
            customer_list.append({
                "id": customer.id,
                "name": customer.name,
                "code": customer.code,
                "site_type": customer.site_type,
                "site_code": customer.site_code
            })
        
        return {"success": True, "customers": customer_list}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ==============================================================================
# 관리자용 사업장 API
# ==============================================================================

@router.get("/api/admin/customers")
async def get_customers_admin(
    request: Request,
    page: int = Query(1, ge=1), 
    limit: int = Query(20, ge=1, le=100), 
    search: str = Query(""), 
    db: Session = Depends(get_db)
):
    """관리자용 사업장 목록 조회 (페이징, 검색 기능 포함)"""
    # 인증 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        # 검색 조건 구성
        query = db.query(Customer)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                Customer.name.ilike(search_term) | 
                Customer.code.ilike(search_term) |
                Customer.site_code.ilike(search_term)
            )
        
        # 전체 개수 조회
        total = query.count()
        
        # 페이징 적용
        offset = (page - 1) * limit
        customers = query.order_by(Customer.sort_order).offset(offset).limit(limit).all()
        
        # 결과 구성
        customer_list = []
        for customer in customers:
            customer_list.append({
                "id": customer.id,
                "name": customer.name,
                "code": customer.code,
                "site_type": customer.site_type,
                "site_code": customer.site_code,
                "parent_id": customer.parent_id,
                "level": customer.level,
                "sort_order": customer.sort_order,
                "contact_person": customer.contact_person,
                "contact_phone": customer.contact_phone,
                "address": customer.address,
                "description": customer.description,
                "created_at": customer.created_at.isoformat() if customer.created_at else None
            })
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "success": True,
            "customers": customer_list,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/admin/customers/create")
async def create_customer(request: Request, customer_data: CustomerCreate, db: Session = Depends(get_db)):
    """새 사업장 생성"""
    # 인증 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        # 중복 체크 (이름 또는 코드)
        existing_customer = db.query(Customer).filter(
            (Customer.name == customer_data.name) | 
            (Customer.code == customer_data.code and customer_data.code is not None)
        ).first()
        
        if existing_customer:
            return {"success": False, "message": "이미 존재하는 사업장명 또는 코드입니다."}
        
        # 새 사업장 생성
        new_customer = Customer(
            name=customer_data.name,
            code=customer_data.code,
            site_type=customer_data.site_type,
            site_code=customer_data.site_code,
            parent_id=customer_data.parent_id,
            level=customer_data.level,
            sort_order=customer_data.sort_order,
            contact_person=customer_data.contact_person,
            contact_phone=customer_data.contact_phone,
            address=customer_data.address,
            description=customer_data.description,
            created_at=datetime.now()
        )
        
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)
        
        return {
            "success": True, 
            "message": "사업장이 성공적으로 생성되었습니다.",
            "customer_id": new_customer.id
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"사업장 생성 중 오류가 발생했습니다: {str(e)}"}

@router.get("/api/admin/customers/{customer_id}/detail")
async def get_customer_detail(request: Request, customer_id: int, db: Session = Depends(get_db)):
    """사업장 상세 정보 조회"""
    # 인증 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"success": False, "message": "존재하지 않는 사업장입니다."}
        
        customer_data = {
            "id": customer.id,
            "name": customer.name,
            "code": customer.code,
            "site_type": customer.site_type,
            "site_code": customer.site_code,
            "parent_id": customer.parent_id,
            "level": customer.level,
            "sort_order": customer.sort_order,
            "contact_person": customer.contact_person,
            "contact_phone": customer.contact_phone,
            "address": customer.address,
            "description": customer.description,
            "created_at": customer.created_at.isoformat() if customer.created_at else None
        }
        
        return {"success": True, "customer": customer_data}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.put("/api/admin/customers/{customer_id}/update")
async def update_customer(request: Request, customer_id: int, customer_data: CustomerUpdate, db: Session = Depends(get_db)):
    """사업장 정보 수정"""
    # 인증 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"success": False, "message": "존재하지 않는 사업장입니다."}
        
        # 업데이트할 필드만 수정
        update_data = customer_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)
        
        customer.updated_at = datetime.now()
        db.commit()
        
        return {"success": True, "message": "사업장 정보가 수정되었습니다."}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"사업장 정보 수정 중 오류가 발생했습니다: {str(e)}"}

@router.delete("/api/admin/customers/{customer_id}/delete")
async def delete_customer(request: Request, customer_id: int, db: Session = Depends(get_db)):
    """사업장 삭제"""
    # 인증 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            return {"success": False, "message": "존재하지 않는 사업장입니다."}
        
        # 관련 데이터 확인 (참조 무결성)
        # TODO: 관련 데이터 체크 로직 추가 (메뉴, 주문 등)
        
        db.delete(customer)
        db.commit()
        
        return {"success": True, "message": "사업장이 삭제되었습니다."}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"사업장 삭제 중 오류가 발생했습니다: {str(e)}"}

# ==============================================================================
# 사업장-협력업체 매핑 API
# ==============================================================================

@router.get("/api/admin/customer-supplier-mappings")
async def get_customer_supplier_mappings(db: Session = Depends(get_db)):
    """사업장-협력업체 매핑 목록 조회"""
    try:
        # 직접 SQL로 조인 처리 (모델 의존성 문제 해결)
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    csm.id as mapping_id,
                    csm.customer_id,
                    c.name as customer_name,
                    csm.supplier_id,
                    s.name as supplier_name,
                    csm.delivery_code,
                    csm.priority_order,
                    csm.is_primary_supplier,
                    csm.contract_start_date,
                    csm.contract_end_date,
                    csm.notes,
                    csm.is_active,
                    csm.created_at,
                    csm.updated_at
                FROM customer_supplier_mappings csm
                JOIN customers c ON csm.customer_id = c.id
                JOIN suppliers s ON csm.supplier_id = s.id
                ORDER BY c.name, csm.priority_order
            """)
            
            results = conn.execute(query).fetchall()
        
        mapping_list = []
        for row in results:
            mapping_list.append({
                "id": row.mapping_id,
                "customer_id": row.customer_id,
                "customer_name": row.customer_name,
                "supplier_id": row.supplier_id,
                "supplier_name": row.supplier_name,
                "delivery_code": row.delivery_code,
                "priority_order": row.priority_order,
                "is_primary_supplier": row.is_primary_supplier,
                "contract_start_date": row.contract_start_date.isoformat() if row.contract_start_date and hasattr(row.contract_start_date, 'isoformat') else str(row.contract_start_date) if row.contract_start_date else None,
                "contract_end_date": row.contract_end_date.isoformat() if row.contract_end_date and hasattr(row.contract_end_date, 'isoformat') else str(row.contract_end_date) if row.contract_end_date else None,
                "notes": row.notes,
                "is_active": row.is_active,
                "created_at": row.created_at.isoformat() if row.created_at and hasattr(row.created_at, 'isoformat') else str(row.created_at) if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at and hasattr(row.updated_at, 'isoformat') else str(row.updated_at) if row.updated_at else None
            })
        
        return {"success": True, "mappings": mapping_list}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/admin/customer-supplier-mappings")  
async def create_customer_supplier_mapping(mapping_data: CustomerSupplierMappingCreate, request: Request):
    """사업장-협력업체 매핑 생성"""
    try:
        # DB 연결 직접 생성 (SQLAlchemy 모델 의존성 문제 해결)
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # 중복 검사
            existing_result = conn.execute(
                text("SELECT COUNT(*) FROM customer_supplier_mappings WHERE customer_id = :customer_id AND supplier_id = :supplier_id"),
                {"customer_id": mapping_data.customer_id, "supplier_id": mapping_data.supplier_id}
            ).fetchone()
            
            if existing_result[0] > 0:
                return {"success": False, "message": "이미 존재하는 매핑입니다."}
            
            # 고객 존재 확인
            customer_result = conn.execute(
                text("SELECT COUNT(*) FROM customers WHERE id = :customer_id"),
                {"customer_id": mapping_data.customer_id}
            ).fetchone()
            
            if customer_result[0] == 0:
                return {"success": False, "message": "존재하지 않는 사업장입니다."}
            
            # 협력업체 존재 확인  
            supplier_result = conn.execute(
                text("SELECT COUNT(*) FROM suppliers WHERE id = :supplier_id"),
                {"supplier_id": mapping_data.supplier_id}
            ).fetchone()
            
            if supplier_result[0] == 0:
                return {"success": False, "message": "존재하지 않는 협력업체입니다."}
            
            # 매핑 생성
            conn.execute(
                text("""
                    INSERT INTO customer_supplier_mappings 
                    (customer_id, supplier_id, delivery_code, priority_order, is_primary_supplier, 
                     contract_start_date, contract_end_date, notes, is_active, created_at, updated_at)
                    VALUES (:customer_id, :supplier_id, :delivery_code, :priority_order, :is_primary_supplier,
                            :contract_start_date, :contract_end_date, :notes, :is_active, :created_at, :updated_at)
                """),
                {
                    "customer_id": mapping_data.customer_id,
                    "supplier_id": mapping_data.supplier_id,
                    "delivery_code": mapping_data.delivery_code,
                    "priority_order": mapping_data.priority_order,
                    "is_primary_supplier": mapping_data.is_primary_supplier,
                    "contract_start_date": mapping_data.contract_start_date,
                    "contract_end_date": mapping_data.contract_end_date,
                    "notes": mapping_data.notes,
                    "is_active": mapping_data.is_active,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            )
            conn.commit()
        
        return {"success": True, "message": "매핑이 생성되었습니다."}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.put("/api/admin/customer-supplier-mappings/{mapping_id}")
async def update_customer_supplier_mapping(mapping_id: int, mapping_data: CustomerSupplierMappingUpdate, db: Session = Depends(get_db)):
    """사업장-협력업체 매핑 수정"""
    try:
        mapping = db.query(CustomerSupplierMapping).filter(CustomerSupplierMapping.id == mapping_id).first()
        if not mapping:
            return {"success": False, "message": "존재하지 않는 매핑입니다."}
        
        # 업데이트할 필드만 수정
        update_data = mapping_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(mapping, field):
                setattr(mapping, field, value)
        
        mapping.updated_at = datetime.now()
        db.commit()
        
        return {"success": True, "message": "매핑이 수정되었습니다."}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

@router.delete("/api/admin/customer-supplier-mappings/{mapping_id}")
async def delete_customer_supplier_mapping(mapping_id: int, db: Session = Depends(get_db)):
    """사업장-협력업체 매핑 삭제"""
    try:
        mapping = db.query(CustomerSupplierMapping).filter(CustomerSupplierMapping.id == mapping_id).first()
        if not mapping:
            return {"success": False, "message": "존재하지 않는 매핑입니다."}
        
        db.delete(mapping)
        db.commit()
        
        return {"success": True, "message": "매핑이 삭제되었습니다."}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

@router.get("/api/admin/customer-supplier-mappings/{mapping_id}")
async def get_customer_supplier_mapping(mapping_id: int, db: Session = Depends(get_db)):
    """특정 사업장-협력업체 매핑 조회"""
    try:
        # 직접 SQL로 조인 처리
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    csm.id as mapping_id,
                    csm.customer_id,
                    c.name as customer_name,
                    csm.supplier_id,
                    s.name as supplier_name,
                    csm.delivery_code,
                    csm.priority_order,
                    csm.is_primary_supplier,
                    csm.contract_start_date,
                    csm.contract_end_date,
                    csm.notes,
                    csm.is_active,
                    csm.created_at,
                    csm.updated_at
                FROM customer_supplier_mappings csm
                JOIN customers c ON csm.customer_id = c.id
                JOIN suppliers s ON csm.supplier_id = s.id
                WHERE csm.id = :mapping_id
            """)
            
            result = conn.execute(query, {"mapping_id": mapping_id}).fetchone()
        
        if not result:
            return {"success": False, "message": "존재하지 않는 매핑입니다."}
        
        mapping_data = {
            "id": result.mapping_id,
            "customer_id": result.customer_id,
            "customer_name": result.customer_name,
            "supplier_id": result.supplier_id,
            "supplier_name": result.supplier_name,
            "delivery_code": result.delivery_code,
            "priority_order": result.priority_order,
            "is_primary_supplier": result.is_primary_supplier,
            "contract_start_date": result.contract_start_date.isoformat() if result.contract_start_date else None,
            "contract_end_date": result.contract_end_date.isoformat() if result.contract_end_date else None,
            "notes": result.notes,
            "is_active": result.is_active,
            "created_at": result.created_at.isoformat() if result.created_at else None,
            "updated_at": result.updated_at.isoformat() if result.updated_at else None
        }
        
        return {"success": True, "mapping": mapping_data}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.delete("/api/admin/customers/{customer_id}/supplier-mappings")
async def delete_customer_supplier_mappings(customer_id: int, request: Request):
    """특정 고객의 모든 협력업체 매핑 삭제"""
    try:
        # 직접 SQL로 삭제 (SQLAlchemy 모델 의존성 문제 방지)
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(
                text("DELETE FROM customer_supplier_mappings WHERE customer_id = :customer_id"),
                {"customer_id": customer_id}
            )
            conn.commit()
            
        return {"success": True, "message": f"사업장 ID {customer_id}의 모든 협력업체 매핑이 삭제되었습니다.", "deleted_count": result.rowcount}
    except Exception as e:
        return {"success": False, "message": str(e)}