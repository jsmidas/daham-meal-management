"""
사업장 관리 전용 API 모듈
- 사업장 CRUD 작업
- 트리 구조 관리
- 사업장 이동/위치 관리
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

# 로컬 임포트
from app.database import get_db
from app.api.auth import get_current_user
from models import BusinessLocation

router = APIRouter(prefix="/api/admin", tags=["sites"])

# ==============================================================================
# Pydantic 모델들
# ==============================================================================

class SiteCreate(BaseModel):
    name: str
    code: Optional[str] = None
    site_type: Optional[str] = "일반"
    parent_id: Optional[int] = None
    level: Optional[int] = 1
    sort_order: Optional[int] = 0
    portion_size: Optional[int] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = True

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    site_type: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[int] = None
    sort_order: Optional[int] = None
    portion_size: Optional[int] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class SiteResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    site_type: str
    parent_id: Optional[int]
    level: int
    sort_order: int
    portion_size: Optional[int]
    contact_person: Optional[str]
    contact_phone: Optional[str]
    address: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: Optional[str]

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
# 사업장 관리 API
# ==============================================================================

@router.get("/sites")
async def get_sites(db: Session = Depends(get_db)):
    """사이트 목록 조회 - 실제 데이터베이스에서 조회"""
    print("[DEBUG] get_sites 함수가 호출되었습니다!")
    try:
        # 실제 데이터베이스에서 사업장 목록 조회
        all_sites = db.query(BusinessLocation).order_by(BusinessLocation.id).all()
        sites_list = []
        for site in all_sites:
            sites_list.append({
                "id": site.id,
                "name": site.site_name,
                "code": site.site_code,
                "site_type": site.site_type if site.site_type else "일반",
                "parent_id": None,  # BusinessLocation doesn't have parent_id
                "level": 1,  # Default level
                "sort_order": 0,  # Default sort order
                "description": site.special_notes if site.special_notes else "",
                "created_at": site.created_at.isoformat() if site.created_at else None,
                "contact_person": site.manager_name if site.manager_name else "",
                "contact_phone": site.phone if site.phone else "",
                "address": site.address if site.address else "",
                "is_active": site.is_active if hasattr(site, 'is_active') else True
            })
        
        return {"success": True, "sites": sites_list, "count": len(sites_list)}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/sites/debug")
async def debug_sites(db: Session = Depends(get_db)):
    """디버깅용 - 모든 사업장 목록 반환"""
    try:
        all_sites = db.query(Customer).order_by(Customer.id).all()
        sites_list = []
        for site in all_sites:
            sites_list.append({
                "id": site.id,
                "name": site.name,
                "code": site.code,
                "site_type": site.site_type if hasattr(site, 'site_type') else "",
                "level": site.level,
                "parent_id": site.parent_id
            })
        return {"success": True, "sites": sites_list, "count": len(sites_list)}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/sites/tree")
async def get_sites_tree(db: Session = Depends(get_db)):
    """사업장 트리 구조 조회"""
    try:
        # 모든 사업장을 조회하여 parent_id가 None인 것들을 루트로 설정
        all_sites = db.query(BusinessLocation).order_by(BusinessLocation.id).all()
        
        root_sites = []
        
        # parent_id가 None인 모든 사업장을 루트 레벨에 표시
        for site in all_sites:
            if site.parent_id is None:
                site_data = {
                    "id": site.id,
                    "name": site.name,
                    "code": site.code,
                    "site_type": site.site_type if site.site_type else "일반",
                    "level": site.level if site.level else 1,
                    "sort_order": site.sort_order if site.sort_order else 0,
                    "children": []
                }
                
                # 이 사업장의 자식들을 찾아서 추가
                for child_site in all_sites:
                    if child_site.parent_id == site.id:
                        child_data = {
                            "id": child_site.id,
                            "name": child_site.name,
                            "code": child_site.code,
                            "site_type": child_site.site_type if child_site.site_type else "일반",
                            "level": child_site.level if child_site.level else 2,
                            "sort_order": child_site.sort_order if child_site.sort_order else 0,
                            "children": []
                        }
                        site_data["children"].append(child_data)
                
                root_sites.append(site_data)
        
        return {"success": True, "sites": root_sites}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/sites/{site_id}")
async def get_site(site_id: int, request: Request, db: Session = Depends(get_db)):
    """사업장 상세 조회"""
    verify_admin_access(request)
    
    try:
        site = db.query(BusinessLocation).filter(BusinessLocation.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="사업장을 찾을 수 없습니다.")
        
        return {
            "success": True,
            "site": {
                "id": site.id,
                "code": site.code,
                "name": site.name,
                "site_type": site.site_type,
                "parent_id": site.parent_id,
                "level": site.level,
                "sort_order": site.sort_order,
                "portion_size": site.portion_size,
                "contact_person": site.contact_person,
                "contact_phone": site.contact_phone,
                "address": site.address,
                "description": site.description,
                "is_active": site.is_active if hasattr(site, 'is_active') else True,
                "created_at": site.created_at.isoformat() if site.created_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/sites")
async def create_site(site_data: SiteCreate, request: Request, db: Session = Depends(get_db)):
    """사업장 추가"""
    verify_admin_access(request)
    
    try:
        print(f"[DEBUG] 받은 사업장 데이터: {site_data}")
        print(f"[DEBUG] name: {site_data.name}, code: {site_data.code}, level: {site_data.level}")
        print(f"[DEBUG] site_type: {site_data.site_type}, parent_id: {site_data.parent_id}")
        # 코드 중복 체크
        if site_data.code:
            existing_site = db.query(Customer).filter(Customer.code == site_data.code).first()
            if existing_site:
                raise HTTPException(status_code=400, detail="이미 존재하는 사업장 코드입니다.")
        
        new_site = Customer(
            code=site_data.code,
            name=site_data.name,
            site_type=site_data.site_type,
            parent_id=site_data.parent_id,
            level=site_data.level,
            sort_order=site_data.sort_order,
            portion_size=site_data.portion_size,
            contact_person=site_data.contact_person,
            contact_phone=site_data.contact_phone,
            address=site_data.address,
            description=site_data.description,
            is_active=site_data.is_active
        )
        
        db.add(new_site)
        db.commit()
        db.refresh(new_site)
        
        return {
            "success": True,
            "message": "사업장이 추가되었습니다.",
            "site": {
                "id": new_site.id,
                "code": new_site.code,
                "name": new_site.name,
                "site_type": new_site.site_type,
                "parent_id": new_site.parent_id,
                "level": new_site.level,
                "sort_order": new_site.sort_order,
                "portion_size": new_site.portion_size,
                "contact_person": new_site.contact_person,
                "contact_phone": new_site.contact_phone,
                "address": new_site.address,
                "description": new_site.description,
                "is_active": new_site.is_active,
                "created_at": new_site.created_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

@router.put("/sites/{site_id}")
async def update_site(site_id: int, site_data: SiteUpdate, request: Request, db: Session = Depends(get_db)):
    """사업장 수정"""
    verify_admin_access(request)
    
    try:
        site = db.query(BusinessLocation).filter(BusinessLocation.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="사업장을 찾을 수 없습니다.")
        
        # 코드 중복 체크 (다른 사업장에 동일한 코드가 있는지)
        if site_data.code and site_data.code != site.code:
            existing_site = db.query(Customer).filter(Customer.code == site_data.code).first()
            if existing_site:
                raise HTTPException(status_code=400, detail="이미 존재하는 사업장 코드입니다.")
        
        # 필드 업데이트
        if site_data.name is not None:
            site.name = site_data.name
        if site_data.code is not None:
            site.code = site_data.code
        if site_data.site_type is not None:
            site.site_type = site_data.site_type
        if site_data.parent_id is not None:
            site.parent_id = site_data.parent_id
        if site_data.level is not None:
            site.level = site_data.level
        if site_data.sort_order is not None:
            site.sort_order = site_data.sort_order
        if site_data.portion_size is not None:
            site.portion_size = site_data.portion_size
        if site_data.contact_person is not None:
            site.contact_person = site_data.contact_person
        if site_data.contact_phone is not None:
            site.contact_phone = site_data.contact_phone
        if site_data.address is not None:
            site.address = site_data.address
        if site_data.description is not None:
            site.description = site_data.description
        if site_data.is_active is not None:
            site.is_active = site_data.is_active
        
        db.commit()
        db.refresh(site)
        
        return {
            "success": True,
            "message": "사업장이 수정되었습니다.",
            "site": {
                "id": site.id,
                "code": site.code,
                "name": site.name,
                "site_type": site.site_type,
                "parent_id": site.parent_id,
                "level": site.level,
                "sort_order": site.sort_order,
                "portion_size": site.portion_size,
                "contact_person": site.contact_person,
                "contact_phone": site.contact_phone,
                "address": site.address,
                "description": site.description,
                "is_active": site.is_active if hasattr(site, 'is_active') else True,
                "created_at": site.created_at.isoformat() if site.created_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

@router.delete("/sites/{site_id}")
async def delete_site(site_id: int, request: Request, db: Session = Depends(get_db)):
    """사업장 삭제"""
    verify_admin_access(request)
    
    try:
        site = db.query(BusinessLocation).filter(BusinessLocation.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="사업장을 찾을 수 없습니다.")
        
        # 하위 사업장이 있는지 확인
        child_sites = db.query(Customer).filter(Customer.parent_id == site_id).count()
        if child_sites > 0:
            raise HTTPException(status_code=400, detail="하위 사업장이 있어 삭제할 수 없습니다.")
        
        db.delete(site)
        db.commit()
        
        return {
            "success": True,
            "message": "사업장이 삭제되었습니다."
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

@router.post("/sites/{site_id}/move")
async def move_site(site_id: int, move_data: dict, request: Request, db: Session = Depends(get_db)):
    """사이트 위치 이동 (트리 구조)"""
    verify_admin_access(request)
    
    try:
        site = db.query(BusinessLocation).filter(BusinessLocation.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="사이트를 찾을 수 없습니다.")
        
        # 트리 구조에서 위치 이동 로직
        # 실제 구현은 트리 구조에 따라 다를 수 있음
        new_parent_id = move_data.get('parent_id')
        new_position = move_data.get('position', 0)
        
        # 간단한 구현 - parent_id 업데이트
        if hasattr(site, 'parent_id'):
            site.parent_id = new_parent_id
        site.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "message": "사이트가 이동되었습니다."
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

# ==============================================================================
# 간단한 사업장 관리 API (테스트용)
# ==============================================================================

@router.post("/create-site-simple")
async def create_site_simple(site_data: dict, db: Session = Depends(get_db)):
    """단순한 사업장 생성 (인증 우회)"""
    print(f"[SIMPLE] 사업장 생성 요청: {site_data}")
    
    try:
        name = site_data.get('name', 'tessite' + str(datetime.now().timestamp()))
        code = site_data.get('code', 'TEST' + str(int(datetime.now().timestamp())))
        
        # 중복 확인
        existing = db.query(Customer).filter(Customer.code == code).first()
        if existing:
            return {"success": False, "message": f"사업장 코드 '{code}' 이미 존재"}
        
        # 새 사업장 생성
        new_site = Customer(
            name=name,
            code=code,
            site_type=site_data.get('site_type', '일반'),
            level=site_data.get('level', 1),
            parent_id=site_data.get('parent_id', None),
            address=site_data.get('address', ''),
            contact_person=site_data.get('contact_person', ''),
            contact_phone=site_data.get('contact_phone', ''),
            contact_email=site_data.get('contact_email', ''),
            special_requirements=site_data.get('special_requirements', ''),
            created_at=datetime.now()
        )
        
        db.add(new_site)
        db.commit()
        db.refresh(new_site)
        
        print(f"[SIMPLE] 사업장 생성 성공: ID={new_site.id}")
        
        return {
            "success": True,
            "message": f"사업장 '{name}' 생성 성공",
            "site_id": new_site.id,
            "name": new_site.name,
            "code": new_site.code
        }
        
    except Exception as e:
        db.rollback()
        print(f"[SIMPLE] 사업장 생성 오류: {str(e)}")
        return {"success": False, "message": f"오류: {str(e)}"}

@router.get("/list-sites-simple")
async def list_sites_simple(db: Session = Depends(get_db)):
    """단순한 사업장 목록 (인증 우회)"""
    try:
        sites = db.query(Customer).all()
        site_list = []
        
        for site in sites:
            site_list.append({
                "id": site.id,
                "name": site.name,
                "code": site.code,
                "site_type": site.site_type,
                "level": site.level,
                "parent_id": site.parent_id,
                "address": site.address,
                "contact_person": site.contact_person,
                "contact_phone": site.contact_phone,
                "created_at": site.created_at.strftime('%Y-%m-%d %H:%M:%S') if site.created_at else None
            })
        
        return {
            "success": True,
            "sites": site_list,
            "total": len(site_list)
        }
        
    except Exception as e:
        print(f"[SIMPLE] 사업장 목록 오류: {str(e)}")
        return {"success": False, "message": f"오류: {str(e)}"}

@router.get("/site-stats")
async def get_site_stats(request: Request, db: Session = Depends(get_db)):
    """사업장 통계"""
    verify_admin_access(request)
    try:
        total_sites = db.query(Customer).count()
        active_sites = db.query(Customer).filter(Customer.is_active == True).count() if hasattr(Customer, 'is_active') else total_sites
        
        # 사업장 타입별 통계
        site_types = db.query(Customer.site_type).distinct().all()
        type_stats = {}
        for site_type in site_types:
            if site_type[0]:
                count = db.query(Customer).filter(Customer.site_type == site_type[0]).count()
                type_stats[site_type[0]] = count
        
        return {
            "total_sites": total_sites,
            "active_sites": active_sites,
            "inactive_sites": total_sites - active_sites,
            "site_types": type_stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류: {str(e)}")

@router.get("/sites/stats")
async def get_site_stats_legacy(db: Session = Depends(get_db)):
    """사업장 통계 (레거시 호환)"""
    try:
        total_sites = db.query(Customer).count()
        active_sites = db.query(Customer).filter(Customer.is_active == True).count() if hasattr(Customer, 'is_active') else total_sites
        
        # 사업장 타입별 통계
        site_types = db.query(Customer.site_type).distinct().all()
        type_stats = {}
        for site_type in site_types:
            if site_type[0]:
                count = db.query(Customer).filter(Customer.site_type == site_type[0]).count()
                type_stats[site_type[0]] = count
        
        return {
            "success": True,
            "stats": {
                "total_sites": total_sites,
                "active_sites": active_sites,
                "inactive_sites": total_sites - active_sites,
                "site_types": type_stats
            }
        }
    except Exception as e:
        return {"success": False, "message": f"통계 조회 중 오류: {str(e)}"}