"""
인증 관련 API 라우터
- 로그인/로그아웃
- 세션 관리  
- 권한 확인
"""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
# 기존 imports (main.py에서 이동 필요)
from models import User
from pydantic import BaseModel

# 임시로 main.py의 세션 관리자 import
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

router = APIRouter()

# 스키마 정의 (나중에 app/schemas/auth.py로 이동)
class LoginRequest(BaseModel):
    username: str
    password: str

# 세션 관리 (나중에 app/core/session.py로 이동)
active_sessions = {}

class SessionManager:
    @staticmethod
    def create_session(user_id: int, username: str, role: str) -> str:
        """세션 생성"""
        from datetime import datetime, timedelta
        import secrets
        
        session_token = secrets.token_urlsafe(32)
        expiry = datetime.now() + timedelta(hours=8)
        
        active_sessions[session_token] = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'expires_at': expiry
        }
        
        return session_token
    
    @staticmethod
    def get_session(session_token: str):
        """세션 조회"""
        return active_sessions.get(session_token)
    
    @staticmethod
    def delete_session(session_token: str):
        """세션 삭제"""
        if session_token in active_sessions:
            del active_sessions[session_token]

# 유틸리티 함수들
def get_current_user(request: Request):
    """현재 로그인한 사용자 정보 반환"""
    session_token = request.cookies.get('session_token')
    if not session_token:
        return None
    
    session_data = SessionManager.get_session(session_token)
    if not session_data:
        return None
        
    return session_data

def require_admin(request: Request):
    """관리자 권한이 필요한 엔드포인트용"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")
    
    if user['role'] not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    
    return user

# API 엔드포인트들
@router.get("/login")
async def serve_login_page():
    """로그인 페이지 서빙"""
    return FileResponse("login.html")

@router.post("/api/auth/login")
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """사용자 로그인 API"""
    try:
        # 데이터베이스에서 사용자 조회
        user = db.query(User).filter(User.username == login_data.username).first()
        
        if not user:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "존재하지 않는 사용자입니다."}
            )
        
        # 간단한 비밀번호 확인 (나중에 해시 기반으로 변경)
        import hashlib
        if user.password_hash:
            # 해시된 비밀번호 확인
            password_hash = hashlib.sha256(login_data.password.encode()).hexdigest()
            if user.password_hash != password_hash:
                return JSONResponse(
                    status_code=401,
                    content={"success": False, "message": "비밀번호가 올바르지 않습니다."}
                )
        else:
            # 데모 패스워드
            demo_passwords = {
                'admin': 'admin',
                'nutritionist': 'nutri123'
            }
            expected_password = demo_passwords.get(login_data.username)
            if not expected_password or login_data.password != expected_password:
                return JSONResponse(
                    status_code=401,
                    content={"success": False, "message": "비밀번호가 올바르지 않습니다."}
                )
        
        # 세션 생성
        role_for_session = 'admin' if user.username == 'admin' else str(user.role)
        session_token = SessionManager.create_session(
            user_id=user.id,
            username=user.username, 
            role=role_for_session
        )
        
        # 응답 생성
        response_data = {
            "success": True,
            "message": "로그인 성공",
            "redirect": "/admin",
            "user": {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'department': getattr(user, 'department', ''),
                'position': getattr(user, 'position', '')
            }
        }
        
        response = JSONResponse(content=response_data)
        
        # 세션 토큰을 쿠키로 설정
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=8*60*60,  # 8시간
            httponly=True,
            secure=False,  # 개발환경
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"로그인 처리 중 오류가 발생했습니다: {str(e)}"}
        )

@router.post("/api/auth/logout")
async def logout(request: Request):
    """로그아웃 API"""
    session_token = request.cookies.get('session_token')
    if session_token:
        SessionManager.delete_session(session_token)
    
    response = JSONResponse(
        content={"success": True, "message": "로그아웃되었습니다."}
    )
    response.delete_cookie(key="session_token")
    return response