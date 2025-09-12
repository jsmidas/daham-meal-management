"""
사용자 관리 전용 API 모듈
- 사용자 CRUD 작업
- 권한 관리
- 비밀번호 재설정
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import hashlib
import secrets

# 로컬 임포트
from app.database import get_db
from app.api.auth import get_current_user
from models import User, Customer, RoleEnum

router = APIRouter(prefix="/api/admin", tags=["users"])

# ==============================================================================
# Pydantic 모델들
# ==============================================================================

class UserCreate(BaseModel):
    username: str
    password: str
    contact_info: str
    role: Optional[str] = "nutritionist"
    is_active: Optional[bool] = True

class UserUpdate(BaseModel):
    contact_info: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    contact_info: str
    role: str
    is_active: bool
    created_at: Optional[str]

# ==============================================================================
# 인증 헬퍼
# ==============================================================================

def verify_admin_access(request: Request):
    """관리자 권한 확인 (임시 비활성화 - 개발용)"""
    # 임시로 인증 체크를 비활성화하고 더미 사용자 반환
    return {
        'id': 1,
        'username': 'admin',
        'role': 'admin',
        'name': '관리자'
    }

# ==============================================================================
# 사용자 관리 API
# ==============================================================================

@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=1000),
    search: Optional[str] = Query(None),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """사용자 목록 조회"""
    verify_admin_access(request)
    
    try:
        query = db.query(User)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.username.ilike(search_term)) |
                (User.contact_info.ilike(search_term))
            )
        
        skip = (page - 1) * limit
        users = query.offset(skip).limit(limit).all()
        print(f"Found {len(users)} users")
        
        user_list = []
        for user in users:
            try:
                print(f"Processing user: {user.username}, role: {user.role} (type: {type(user.role)}), active: {user.is_active}")
                
                # Role enum 처리
                role_str = str(user.role) if hasattr(user.role, 'value') else user.role
                if hasattr(user.role, 'value'):
                    role_str = user.role.value
                
                user_data = UserResponse(
                    id=user.id,
                    username=user.username,
                    contact_info=user.contact_info or "",
                    role=role_str,
                    is_active=user.is_active,
                    created_at=user.created_at.isoformat() if user.created_at else None
                )
                user_list.append(user_data)
                print(f"Successfully processed user: {user.username}")
            except Exception as e:
                print(f"Error processing user {user.username}: {e}")
                continue
        
        print(f"Returning {len(user_list)} users")
        
        # JavaScript에서 기대하는 형식으로 반환
        total_count = db.query(User).count()
        return {
            "success": True,
            "users": user_list,
            "total": total_count,
            "page": page,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 조회 중 오류: {str(e)}")

@router.get("/user-stats")
async def get_user_stats(db: Session = Depends(get_db)):
    """사용자 통계"""
    try:
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        admin_users = db.query(User).filter(User.role == RoleEnum.admin).count()
        
        return {
            "success": True,
            "stats": {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
                "admin_users": admin_users,
                "regular_users": total_users - admin_users
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류: {str(e)}")

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    """특정 사용자 조회"""
    verify_admin_access(request)
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    return UserResponse(
        id=user.id,
        username=user.username,
        contact_info=user.contact_info,
        role=str(user.role),
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None
    )

@router.post("/users")
async def create_user(request: Request, db: Session = Depends(get_db)):
    """새 사용자 생성"""
    try:
        verify_admin_access(request)
        
        # Raw JSON data 가져오기
        json_data = await request.json()
        print(f"Raw JSON received: {json_data}")
        
        # 필수 필드 검증
        required_fields = ['username', 'password', 'contact_info']
        for field in required_fields:
            if field not in json_data or not json_data[field]:
                raise HTTPException(status_code=400, detail=f"필수 필드가 누락되었습니다: {field}")
        
        # UserCreate 모델로 검증
        try:
            user_data = UserCreate(**json_data)
            print(f"Validated user data: {user_data}")
        except Exception as validation_error:
            print(f"Validation error: {validation_error}")
            raise HTTPException(status_code=422, detail=f"데이터 검증 오류: {str(validation_error)}")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"General error in create_user: {e}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")
    
    try:
        # 중복 사용자명 확인
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다.")
        
        # 비밀번호 해시화
        hashed_password = hashlib.sha256(user_data.password.encode()).hexdigest()
        
        # 새 사용자 생성
        new_user = User(
            username=user_data.username,
            password_hash=hashed_password,
            contact_info=user_data.contact_info,
            role=user_data.role,
            is_active=user_data.is_active,
            created_at=datetime.now()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {
            "success": True,
            "message": "사용자가 성공적으로 생성되었습니다.",
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "contact_info": new_user.contact_info,
                "role": new_user.role,
                "is_active": new_user.is_active,
                "created_at": new_user.created_at.isoformat() if new_user.created_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"사용자 생성 중 오류: {str(e)}")

@router.put("/users/{user_id}")
async def update_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    """사용자 정보 수정"""
    try:
        verify_admin_access(request)
        
        # Raw JSON data 가져오기
        json_data = await request.json()
        print(f"Update user {user_id} with data: {json_data}")
        
        # UserUpdate 모델로 검증
        try:
            user_data = UserUpdate(**json_data)
            print(f"Validated update data: {user_data}")
        except Exception as validation_error:
            print(f"Update validation error: {validation_error}")
            raise HTTPException(status_code=422, detail=f"데이터 검증 오류: {str(validation_error)}")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"General error in update_user: {e}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # 필드 업데이트
        if user_data.contact_info is not None:
            user.contact_info = user_data.contact_info
        if user_data.role is not None:
            user.role = user_data.role
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        if user_data.password is not None and user_data.password.strip():
            # 비밀번호가 제공된 경우에만 업데이트
            user.password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
        
        db.commit()
        db.refresh(user)
        
        return {
            "success": True,
            "message": "사용자가 성공적으로 수정되었습니다.",
            "user": {
                "id": user.id,
                "username": user.username,
                "contact_info": user.contact_info,
                "role": str(user.role),
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"사용자 수정 중 오류: {str(e)}")

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    """사용자 삭제"""
    verify_admin_access(request)
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        db.delete(user)
        db.commit()
        
        return {"success": True, "message": "사용자가 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"사용자 삭제 중 오류: {str(e)}")

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(user_id: int, request: Request, db: Session = Depends(get_db)):
    """사용자 비밀번호 재설정"""
    verify_admin_access(request)
    
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
        # 임시 비밀번호 생성 (8자리)
        temp_password = secrets.token_urlsafe(6)
        hashed_password = hashlib.sha256(temp_password.encode()).hexdigest()
        
        user.password_hash = hashed_password
        db.commit()
        
        return {
            "success": True,
            "message": "비밀번호가 재설정되었습니다.",
            "temporary_password": temp_password
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"비밀번호 재설정 중 오류: {str(e)}")


# ==============================================================================
# 간단한 사용자 생성 API (테스트용)
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
            contact_info=f"테스트 사용자 {username}",
            role=RoleEnum.admin,
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
                "contact_info": new_user.contact_info
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
                    "contact_info": user.contact_info,
                    "role": user.role,
                    "is_active": user.is_active
                }
                for user in users
            ]
        }
        
    except Exception as e:
        return {"success": False, "message": f"사용자 목록 조회 실패: {str(e)}"}

@router.post("/debug-user-data")
async def debug_user_data(request: Request):
    """프론트엔드에서 보낸 원본 데이터 확인 (디버깅용)"""
    try:
        body = await request.body()
        print(f"Raw request body: {body}")
        
        json_data = await request.json()
        print(f"Parsed JSON data: {json_data}")
        
        return {
            "success": True,
            "raw_body": body.decode('utf-8') if body else None,
            "parsed_json": json_data,
            "content_type": request.headers.get('content-type')
        }
    except Exception as e:
        print(f"Debug error: {e}")
        return {"success": False, "error": str(e)}

@router.get("/auth-status")
async def get_auth_status(request: Request):
    """현재 인증 상태 확인 (디버깅용)"""
    session_token = request.cookies.get('session_token')
    user = get_current_user(request)
    
    return {
        "has_session_token": bool(session_token),
        "session_token": session_token[:10] + "..." if session_token else None,
        "user": user,
        "cookies": dict(request.cookies)
    }