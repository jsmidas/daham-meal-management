#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사용자 관리 전용 API 서버
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import json
import os
import hashlib
import datetime
from typing import Optional
import uvicorn

app = FastAPI()

# Pydantic 모델 정의
class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    contact_info: Optional[str] = ""
    department: Optional[str] = ""
    position: Optional[str] = ""
    managed_site: Optional[str] = ""

class UserUpdate(BaseModel):
    username: Optional[str] = None
    contact_info: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    managed_site: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

# 데이터베이스 경로
DATABASE_PATH = "backups/working_state_20250912/daham_meal.db"

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """API 서버 상태 확인"""
    return {
        "message": "사용자 관리 API 서버가 정상 작동 중입니다",
        "status": "running",
        "port": 8013,
        "endpoints": ["/api/users"]
    }

# 사용자 관리 API 엔드포인트
@app.get("/api/users")
async def get_all_users(page: int = 1, limit: int = 20, search: str = "", role: str = ""):
    """사용자 목록 조회 (페이징, 검색, 필터링)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # WHERE 조건 구성
        where_conditions = []
        params = []

        if search.strip():
            where_conditions.append("(username LIKE ? OR contact_info LIKE ? OR department LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        if role.strip():
            where_conditions.append("role = ?")
            params.append(role)

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # 총 개수 조회
        count_query = f"SELECT COUNT(*) FROM users {where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # 페이징 계산
        total_pages = (total_count + limit - 1) // limit
        offset = (page - 1) * limit

        # 데이터 조회
        data_query = f"""
            SELECT
                id, username, role, contact_info, department, position,
                managed_site, is_active, created_at, updated_at, last_login,
                operator, semi_operator
            FROM users
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """

        cursor.execute(data_query, params + [limit, offset])
        users = []

        for row in cursor.fetchall():
            users.append({
                "id": row[0],
                "username": row[1],
                "role": row[2],
                "contact_info": row[3] or "",
                "department": row[4] or "",
                "position": row[5] or "",
                "managed_site": row[6] or "",
                "is_active": bool(row[7]),
                "created_at": row[8],
                "updated_at": row[9],
                "last_login": row[10],
                "operator": bool(row[11]),
                "semi_operator": bool(row[12])
            })

        conn.close()

        return {
            "success": True,
            "users": users,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "items_per_page": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/users/stats")
async def get_user_stats():
    """사용자 통계 정보"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 전체 사용자 수
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        # 활성 사용자 수
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        active_users = cursor.fetchone()[0]

        # 비활성 사용자 수
        inactive_users = total_users - active_users

        # 권한별 통계
        cursor.execute("""
            SELECT role, COUNT(*) as count
            FROM users
            WHERE is_active = 1
            GROUP BY role
            ORDER BY count DESC
        """)

        role_stats = {}
        for row in cursor.fetchall():
            role_stats[row[0]] = row[1]

        # 최근 가입자 (최근 30일)
        cursor.execute("""
            SELECT COUNT(*)
            FROM users
            WHERE created_at >= date('now', '-30 days')
        """)
        recent_registrations = cursor.fetchone()[0]

        conn.close()

        return {
            "success": True,
            "stats": {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "role_distribution": role_stats,
                "recent_registrations": recent_registrations
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """개별 사용자 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id, username, role, contact_info, department, position,
                managed_site, is_active, created_at, updated_at, last_login,
                operator, semi_operator
            FROM users
            WHERE id = ?
        """, (user_id,))
        user = cursor.fetchone()

        conn.close()

        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        user_info = {
            "id": user[0],
            "username": user[1],
            "role": user[2],
            "contact_info": user[3] or "",
            "department": user[4] or "",
            "position": user[5] or "",
            "managed_site": user[6] or "",
            "is_active": bool(user[7]),
            "created_at": user[8],
            "updated_at": user[9],
            "last_login": user[10],
            "operator": bool(user[11]),
            "semi_operator": bool(user[12])
        }

        return {
            "success": True,
            "user": user_info
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/users")
async def create_user(user_data: UserCreate):
    """사용자 추가"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 필수 항목 검증
        if not user_data.username.strip():
            raise HTTPException(status_code=400, detail="사용자명은 필수 항목입니다")

        if not user_data.password.strip():
            raise HTTPException(status_code=400, detail="비밀번호는 필수 항목입니다")

        if not user_data.role.strip():
            raise HTTPException(status_code=400, detail="권한은 필수 항목입니다")

        # 역할 유효성 검사
        valid_roles = ['admin', 'nutritionist', 'operator', 'viewer']
        if user_data.role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"권한은 다음 중 하나여야 합니다: {', '.join(valid_roles)}")

        # 사용자명 중복 검사
        cursor.execute("SELECT id FROM users WHERE username = ?", (user_data.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다")

        # 비밀번호 해시화
        password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()

        # 사용자 생성
        cursor.execute("""
            INSERT INTO users (
                username, password_hash, role, contact_info, department,
                position, managed_site, operator, semi_operator,
                is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_data.username,
            password_hash,
            user_data.role,
            user_data.contact_info,
            user_data.department,
            user_data.position,
            user_data.managed_site,
            False,  # operator
            False,  # semi_operator
            True,   # is_active
            datetime.datetime.now().isoformat(),
            datetime.datetime.now().isoformat()
        ))

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "사용자가 성공적으로 추가되었습니다",
            "user_id": user_id
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/users/{user_id}")
async def update_user(user_id: int, user_data: UserUpdate):
    """사용자 정보 수정"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 사용자 존재 확인
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        # 업데이트할 필드 구성
        update_fields = []
        params = []

        if user_data.username is not None:
            if not user_data.username.strip():
                raise HTTPException(status_code=400, detail="사용자명은 필수 항목입니다")

            # 사용자명 중복 검사 (자신 제외)
            cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", (user_data.username, user_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="이미 존재하는 사용자명입니다")

            update_fields.append("username = ?")
            params.append(user_data.username)

        if user_data.contact_info is not None:
            update_fields.append("contact_info = ?")
            params.append(user_data.contact_info)

        if user_data.department is not None:
            update_fields.append("department = ?")
            params.append(user_data.department)

        if user_data.position is not None:
            update_fields.append("position = ?")
            params.append(user_data.position)

        if user_data.managed_site is not None:
            update_fields.append("managed_site = ?")
            params.append(user_data.managed_site)

        if user_data.role is not None:
            if not user_data.role.strip():
                raise HTTPException(status_code=400, detail="권한은 필수 항목입니다")

            valid_roles = ['admin', 'nutritionist', 'operator', 'viewer']
            if user_data.role not in valid_roles:
                raise HTTPException(status_code=400, detail=f"권한은 다음 중 하나여야 합니다: {', '.join(valid_roles)}")

            update_fields.append("role = ?")
            params.append(user_data.role)

        if user_data.is_active is not None:
            update_fields.append("is_active = ?")
            params.append(user_data.is_active)

        if not update_fields:
            raise HTTPException(status_code=400, detail="업데이트할 필드가 없습니다")

        # 업데이트 시간 추가
        update_fields.append("updated_at = ?")
        params.append(datetime.datetime.now().isoformat())

        # 사용자 정보 업데이트
        params.append(user_id)
        update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(update_query, params)

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "사용자 정보가 성공적으로 수정되었습니다"
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int):
    """사용자 삭제 (논리적 삭제 - is_active를 False로 설정)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 사용자 존재 확인
        cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        # 논리적 삭제 (is_active를 False로 설정)
        cursor.execute("""
            UPDATE users
            SET is_active = ?, updated_at = ?
            WHERE id = ?
        """, (False, datetime.datetime.now().isoformat(), user_id))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"사용자 '{user[1]}'가 비활성화되었습니다"
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/users/{user_id}/activate")
async def activate_user(user_id: int):
    """사용자 활성화"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 사용자 존재 확인
        cursor.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        # 사용자 활성화
        cursor.execute("""
            UPDATE users
            SET is_active = ?, updated_at = ?
            WHERE id = ?
        """, (True, datetime.datetime.now().isoformat(), user_id))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"사용자 '{user[1]}'가 활성화되었습니다"
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("사용자 관리 API 서버 시작: 127.0.0.1:8013")
    uvicorn.run(app, host="127.0.0.1", port=8013)