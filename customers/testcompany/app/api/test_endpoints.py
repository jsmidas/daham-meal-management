"""
테스트용 엔드포인트 - 인증 없는 사용자/사업장 생성
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import hashlib
from datetime import datetime

from app.database import get_db
from models import User, Customer

router = APIRouter()

class TestUserCreate(BaseModel):
    username: str
    password: str = "test123"
    role: str = "nutritionist"
    department: Optional[str] = "테스트부서"
    position: Optional[str] = "테스터"
    contact_info: Optional[str] = "test@example.com"
    managed_site: Optional[str] = ""
    operator: Optional[bool] = False
    semi_operator: Optional[bool] = False

class TestSiteCreate(BaseModel):
    name: str
    code: Optional[str] = None
    site_type: Optional[str] = "일반"
    level: Optional[int] = 1
    sort_order: Optional[int] = 0
    address: Optional[str] = ""
    contact_phone: Optional[str] = ""
    contact_person: Optional[str] = ""
    description: Optional[str] = ""
    is_active: Optional[bool] = True
    parent_id: Optional[int] = None
    portion_size: Optional[int] = None

@router.post("/test-create-user")
async def test_create_user(user_data: TestUserCreate, db: Session = Depends(get_db)):
    """테스트용 사용자 생성 (인증 없음)"""
    print(f"[TEST-API] 사용자 생성 요청: {user_data.username}")
    
    try:
        # 중복 확인
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            return {"success": False, "message": f"사용자 '{user_data.username}'이 이미 존재합니다."}
        
        # 비밀번호 해싱
        password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
        
        # 새 사용자 생성
        new_user = User(
            username=user_data.username,
            password_hash=password_hash,
            role=user_data.role,
            department=user_data.department,
            position=user_data.position,
            managed_site=user_data.managed_site,
            contact_info=user_data.contact_info,
            operator=user_data.operator,
            semi_operator=user_data.semi_operator,
            created_at=datetime.now()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"[TEST-API] 사용자 생성 성공: ID={new_user.id}")
        
        return {
            "success": True,
            "message": f"사용자 '{new_user.username}'이 성공적으로 생성되었습니다.",
            "user_id": new_user.id,
            "username": new_user.username
        }
        
    except Exception as e:
        db.rollback()
        print(f"[TEST-API] 오류: {str(e)}")
        return {"success": False, "message": f"오류 발생: {str(e)}"}

@router.post("/test-create-site")
async def test_create_site(site_data: TestSiteCreate, db: Session = Depends(get_db)):
    """테스트용 사업장 생성 (인증 없음)"""
    print(f"[TEST-API] 사업장 생성 요청: {site_data.name}")
    
    try:
        # 자동 코드 생성
        if not site_data.code:
            site_data.code = site_data.name.upper().replace(" ", "")[:10]
        
        # 새 사업장 생성 (Customer 테이블 사용)
        new_site = Customer(
            name=site_data.name,
            code=site_data.code,
            site_type=site_data.site_type,
            level=site_data.level,
            sort_order=site_data.sort_order,
            address=site_data.address,
            contact_phone=site_data.contact_phone,
            contact_person=site_data.contact_person,
            description=site_data.description,
            is_active=site_data.is_active,
            parent_id=site_data.parent_id,
            portion_size=site_data.portion_size,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(new_site)
        db.commit()
        db.refresh(new_site)
        
        print(f"[TEST-API] 사업장 생성 성공: ID={new_site.id}")
        
        return {
            "success": True,
            "message": f"사업장 '{new_site.name}'이 성공적으로 생성되었습니다.",
            "site_id": new_site.id,
            "site_name": new_site.name
        }
        
    except Exception as e:
        db.rollback()
        print(f"[TEST-API] 오류: {str(e)}")
        return {"success": False, "message": f"오류 발생: {str(e)}"}

@router.get("/test-users")
async def test_get_users(db: Session = Depends(get_db)):
    """테스트용 사용자 목록 조회"""
    try:
        users = db.query(User).all()
        user_list = []
        
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "department": user.department or "-",
                "position": user.position or "-",
                "contact_info": user.contact_info or "-",
                "is_active": True,  # User 모델에 is_active가 없다면 기본값
                "created_at": user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else None
            })
        
        print(f"[TEST-API] 사용자 목록 조회: {len(user_list)}명")
        
        return {
            "success": True,
            "users": user_list,
            "total": len(user_list)
        }
        
    except Exception as e:
        print(f"[TEST-API] 사용자 목록 조회 오류: {str(e)}")
        return {"success": False, "message": f"오류 발생: {str(e)}"}

@router.get("/test-sites")
async def test_get_sites(db: Session = Depends(get_db)):
    """테스트용 사업장 목록 조회"""
    try:
        sites = db.query(Customer).all()
        site_list = []
        
        for site in sites:
            site_list.append({
                "id": site.id,
                "name": site.name or "이름없음",
                "code": site.code or "",
                "site_type": site.site_type or "",
                "level": site.level or 0,
                "sort_order": site.sort_order or 0,
                "is_active": site.is_active if hasattr(site, 'is_active') else True,
                "children": []  # 트리 구조용
            })
        
        print(f"[TEST-API] 사업장 목록 조회: {len(site_list)}개")
        
        return {
            "success": True,
            "tree": site_list,
            "sites": site_list,
            "total": len(site_list)
        }
        
    except Exception as e:
        print(f"[TEST-API] 사업장 목록 조회 오류: {str(e)}")
        return {"success": False, "message": f"오류 발생: {str(e)}"}