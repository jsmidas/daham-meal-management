#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
삼성웰스토리 식자재 데이터 테스트 API
"""

from fastapi import FastAPI, HTTPException, Request, File, UploadFile, Form, Query, Depends
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import sqlite3
import json
import os
import hashlib
import datetime
import re
from typing import Optional, List, Dict
import sys
import traceback
from pathlib import Path
import jwt
import secrets
sys.path.append('utils')
try:
    from image_processor import ImageProcessor
except ImportError:
    ImageProcessor = None  # 나중에 설치하면 사용
from improved_unit_price_calculator import calculate_unit_price_improved, parse_specification_improved
import httpx

app = FastAPI()

# ========== JWT 인증 시스템 ==========
SECRET_KEY = "daham_meal_secret_key_2025_super_secure_change_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8시간

security = HTTPBearer()

class TokenData(BaseModel):
    username: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class SupplierLogin(BaseModel):
    supplier_code: str
    username: str
    password: str

def create_access_token(data: dict):
    """JWT 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """토큰 검증"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return TokenData(username=username)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(token_data: TokenData = Depends(verify_token)):
    """현재 로그인된 사용자 정보 조회"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    user = cursor.execute("""
        SELECT * FROM users WHERE username = ? AND is_active = 1
    """, (token_data.username,)).fetchone()

    conn.close()

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return dict(user)

def require_admin(current_user: dict = Depends(get_current_user)):
    """관리자 권한 필요"""
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def require_nutritionist_or_admin(current_user: dict = Depends(get_current_user)):
    """영양사 또는 관리자 권한 필요"""
    if current_user['role'] not in ['admin', 'nutritionist']:
        raise HTTPException(status_code=403, detail="Nutritionist or Admin access required")
    return current_user

# 정적 파일 서빙 설정
app.mount("/static", StaticFiles(directory="static"), name="static")
# sample data 디렉토리 서빙 (띄어쓰기 포함된 경로)
if os.path.exists("sample data"):
    app.mount("/sample-data", StaticFiles(directory="sample data"), name="sample_data")

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

class SupplierCreate(BaseModel):
    name: str
    parent_code: Optional[str] = ""
    business_number: Optional[str] = ""
    representative: Optional[str] = ""
    headquarters_address: Optional[str] = ""
    headquarters_phone: Optional[str] = ""
    email: Optional[str] = ""
    notes: Optional[str] = ""

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    parent_code: Optional[str] = None
    business_number: Optional[str] = None
    representative: Optional[str] = None
    headquarters_address: Optional[str] = None
    headquarters_phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None

# 데이터베이스 경로를 환경 변수 또는 기본값으로 설정
DATABASE_PATH = os.getenv("DAHAM_DB_PATH", "daham_meal.db")

# 단위당 단가 계산 함수
def calculate_unit_price_old(price, specification):
    """규격을 파싱하여 단위당 단가 계산"""
    if not price or price == 0 or not specification:
        return None

    patterns = [
        # 무게 * 수량 패턴 (예: 1kg*10ea, 500g*20pac)
        r'(\d+(?:\.\d+)?)\s*(kg|g|mg)\s*[*×xX]\s*(\d+)',
        # 부피 * 수량 패턴 (예: 18L*1ea, 500ml*24개)
        r'(\d+(?:\.\d+)?)\s*(L|l|ml|ML)\s*[*×xX]\s*(\d+)',
        # 무게만 있는 패턴 (예: 1kg, 500g)
        r'(\d+(?:\.\d+)?)\s*(kg|g|mg)(?:\s|$)',
        # 부피만 있는 패턴 (예: 1L, 500ml)
        r'(\d+(?:\.\d+)?)\s*(L|l|ml|ML)(?:\s|$)',
    ]

    for pattern in patterns:
        match = re.search(pattern, specification, re.IGNORECASE)
        if match:
            groups = match.groups()

            if len(groups) >= 3:  # 무게/부피 * 수량
                value = float(groups[0])
                unit = groups[1].lower()
                quantity = float(groups[2])
            elif len(groups) == 2:  # 무게/부피만
                value = float(groups[0])
                unit = groups[1].lower()
                quantity = 1
            else:
                continue

            # 단위를 그램/ml로 통일
            if unit in ['kg']:
                total_value = value * 1000 * quantity
            elif unit in ['g']:
                total_value = value * quantity
            elif unit in ['mg']:
                total_value = value / 1000 * quantity
            elif unit in ['l']:
                total_value = value * 1000 * quantity
            elif unit in ['ml']:
                total_value = value * quantity
            else:
                continue

            if total_value > 0:
                return float(price) / total_value

    return None

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메소드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

@app.get("/favicon.ico")
async def favicon():
    """Return empty favicon to avoid 404 errors"""
    return Response(content=b"", media_type="image/x-icon")

@app.get("/")
async def root():
    """API 서버 상태 확인"""
    return {
        "message": "식자재 관리 API 서버가 정상 작동 중입니다",
        "status": "running",
        "port": 8010,
        "endpoints": [
            "/test-samsung-welstory",
            "/all-ingredients-for-suppliers",
            "/api/auth/login",
            "/api/users"
        ]
    }

@app.get("/login.html")
async def serve_login_page():
    """로그인 페이지 제공"""
    return FileResponse("login.html", media_type="text/html")

@app.get("/supplier_login.html")
async def serve_supplier_login_page():
    """협력업체 로그인 페이지 제공"""
    return FileResponse("supplier_login.html", media_type="text/html")

# ========== 인증 API ==========

@app.post("/api/auth/login")
async def login(user_credentials: UserLogin):
    """사용자 로그인"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 사용자 조회
        user = cursor.execute("""
            SELECT * FROM users WHERE username = ? AND is_active = 1
        """, (user_credentials.username,)).fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")

        # 비밀번호 검증 (해시된 비밀번호와 비교)
        password_hash = hashlib.sha256(user_credentials.password.encode()).hexdigest()

        if user['password_hash'] != password_hash:
            raise HTTPException(status_code=401, detail="비밀번호가 일치하지 않습니다")

        # JWT 토큰 생성
        access_token = create_access_token(data={"sub": user['username']})

        # 로그인 시간 업데이트
        cursor.execute("""
            UPDATE users SET last_login = datetime('now') WHERE id = ?
        """, (user['id'],))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "로그인 성공",
            "token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "role": user['role'],
                "department": user['department'],
                "position": user['position']
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"로그인 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="로그인 처리 중 오류가 발생했습니다")

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """현재 로그인된 사용자 정보 조회"""
    return {
        "success": True,
        "user": {
            "id": current_user['id'],
            "username": current_user['username'],
            "role": current_user['role'],
            "department": current_user['department'],
            "position": current_user['position'],
            "last_login": current_user['last_login']
        }
    }

@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """로그아웃 (클라이언트에서 토큰 삭제)"""
    return {
        "success": True,
        "message": "로그아웃되었습니다"
    }

@app.post("/api/auth/supplier-login")
async def supplier_login(supplier_credentials: SupplierLogin):
    """협력업체 로그인"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 협력업체 정보 조회
        supplier = cursor.execute("""
            SELECT * FROM suppliers WHERE supplier_code = ? AND is_active = 1
        """, (supplier_credentials.supplier_code,)).fetchone()

        if not supplier:
            raise HTTPException(status_code=401, detail="협력업체를 찾을 수 없습니다")

        # 협력업체 담당자 정보 확인 (임시로 간단한 검증)
        # 실제로는 별도의 supplier_users 테이블이 필요합니다
        valid_suppliers = {
            'SAMSUNG': {'admin': 'samsung123', 'manager': 'samsung456'},
            'HYUNDAI': {'admin': 'hyundai123', 'manager': 'hyundai456'},
            'CJ': {'admin': 'cj123', 'manager': 'cj456'},
            'PUDIST': {'admin': 'pudist123', 'manager': 'pudist456'},
            'DONGWON': {'admin': 'dongwon123', 'manager': 'dongwon456'}
        }

        supplier_code = supplier_credentials.supplier_code
        username = supplier_credentials.username
        password = supplier_credentials.password

        if (supplier_code not in valid_suppliers or
            username not in valid_suppliers[supplier_code] or
            valid_suppliers[supplier_code][username] != password):
            raise HTTPException(status_code=401, detail="담당자 정보가 일치하지 않습니다")

        # JWT 토큰 생성 (협력업체용)
        token_data = {
            "sub": f"supplier_{supplier_code}_{username}",
            "supplier_code": supplier_code,
            "role": "supplier"
        }
        access_token = create_access_token(data=token_data)

        # 로그인 기록 (향후 확장용)
        conn.close()

        return {
            "success": True,
            "message": "협력업체 로그인 성공",
            "token": access_token,
            "token_type": "bearer",
            "supplier": {
                "supplier_code": supplier_code,
                "supplier_name": supplier['name'],
                "username": username,
                "role": "supplier"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"협력업체 로그인 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="로그인 처리 중 오류가 발생했습니다")

@app.get("/test-samsung-welstory")
async def test_samsung_welstory():
    """삼성웰스토리 식자재 데이터 직접 조회"""
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 삼성웰스토리 공급업체 정보 조회
        cursor.execute("""
            SELECT id, name, representative, headquarters_phone 
            FROM suppliers 
            WHERE name LIKE '%웰스토리%' OR name LIKE '%삼성%'
        """)
        supplier = cursor.fetchone()
        
        if not supplier:
            return {"success": False, "message": "삼성웰스토리 공급업체를 찾을 수 없습니다"}
        
        supplier_info = {
            "id": supplier[0],
            "name": supplier[1],
            "contact_person": supplier[2],
            "contact_phone": supplier[3]
        }
        
        # 식자재 데이터 조회
        cursor.execute("""
            SELECT ingredient_name, category, unit, selling_price, notes
            FROM ingredients 
            WHERE supplier_name LIKE '%웰스토리%' OR supplier_name LIKE '%삼성%'
            LIMIT 50
        """)
        
        ingredients_data = cursor.fetchall()
        
        ingredients = []
        for ing in ingredients_data:
            ingredients.append({
                "name": ing[0],
                "category": ing[1],
                "unit": ing[2],
                "cost_per_unit": float(ing[3]) if ing[3] else 0.0,
                "description": ing[4] or ""
            })
        
        # 전체 개수 조회
        cursor.execute("""
            SELECT COUNT(*) 
            FROM ingredients 
            WHERE supplier_name LIKE '%웰스토리%' OR supplier_name LIKE '%삼성%'
        """)
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "success": True,
            "supplier": supplier_info,
            "ingredients": ingredients,
            "total_count": total_count,
            "shown_count": len(ingredients)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/all-ingredients-for-suppliers")
async def get_all_ingredients_for_suppliers(page: int = 1, limit: int = 100, supplier_filter: str = None):
    """모든 식자재를 업체별로 그룹화해서 반환 (업체별 식자재 현황 박스용)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 기본 WHERE 조건
        where_conditions = ["supplier_name IS NOT NULL", "supplier_name != ''"]
        params = []
        
        # 공급업체 필터 추가
        if supplier_filter:
            where_conditions.append("supplier_name LIKE ?")
            params.append(f"%{supplier_filter}%")
        
        # 전체 데이터 수 확인
        count_query = f"SELECT COUNT(*) FROM ingredients WHERE {' AND '.join(where_conditions)}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]
        
        # 페이지네이션 계산
        offset = (page - 1) * limit
        total_pages = (total_count + limit - 1) // limit
        
        # 페이지 컬럼 구조에 맞춘 식자재 조회 (g당 단가 계산 포함)
        query = f"""
            SELECT 
                category,
                sub_category,
                ingredient_code,
                ingredient_name,
                origin,
                posting_status,
                specification,
                unit,
                tax_type,
                delivery_days,
                purchase_price,
                selling_price,
                supplier_name,
                notes,
                created_date,
                price_per_unit
            FROM ingredients 
            WHERE {' AND '.join(where_conditions)}
            ORDER BY supplier_name, ingredient_name
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        cursor.execute(query, params)
        
        ingredients_data = cursor.fetchall()
        
        # 데이터를 한국어 컬럼명으로 변환
        ingredients = []
        
        for row in ingredients_data:
            # 데이터베이스에서 계산된 단위당 단가를 직접 사용
            price_per_unit = row[15] if row[15] is not None else 0.0
            
            ingredient_dict = {
                '분류(대분류)': row[0] or '',
                '기본식자재(세분류)': row[1] or '',
                '고유코드': row[2] or '',
                '식자재명': row[3] or '',
                '원산지': row[4] or '',
                '게시유무': row[5] or '',
                '규격': row[6] or '',  # 페이지에서 찾는 컬럼명
                '단위': row[7] or '',  # 페이지에서 찾는 컬럼명
                '면세': row[8] or '',  # 페이지에서 찾는 컬럼명 (면세여부 아닌 면세)
                '선발주일': row[9] or '',  # 페이지에서 찾는 컬럼명
                '입고가': float(row[10]) if row[10] is not None else 0.0,
                '판매가': float(row[11]) if row[11] is not None else 0.0,
                '거래처명': row[12] or '',
                '비고': row[13] or '',
                '등록일': row[14] or '',
                'g당단가': round(price_per_gram, 2)
            }
            ingredients.append(ingredient_dict)
        
        # 업체별 통계
        cursor.execute("""
            SELECT 
                supplier_name,
                COUNT(*) as ingredient_count
            FROM ingredients 
            WHERE supplier_name IS NOT NULL AND supplier_name != ''
            GROUP BY supplier_name
            ORDER BY ingredient_count DESC
        """)
        
        supplier_stats = {}
        for row in cursor.fetchall():
            supplier_stats[row[0]] = row[1]
        
        conn.close()
        
        return {
            "success": True,
            "ingredients": ingredients,
            "supplier_stats": supplier_stats,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "items_per_page": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "total_ingredients": len(ingredients),
            "total_suppliers": len(supplier_stats)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/users")
async def get_admin_users():
    """관리자용 사용자 목록 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, contact_info, role, is_active, created_at
            FROM users 
            ORDER BY created_at DESC
        """)
        
        users_data = cursor.fetchall()
        users = []
        
        for user in users_data:
            users.append({
                "id": user[0],
                "username": user[1],
                "contact_info": user[2],
                "role": user[3],
                "is_active": bool(user[4]),
                "created_at": user[5]
            })
        
        conn.close()
        
        return {
            "success": True,
            "users": users,
            "total": len(users)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/business-locations")
async def get_admin_business_locations():
    """관리자용 사업장 목록 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, site_code, site_name, site_type, region, address, manager_name, manager_phone, is_active
            FROM business_locations
            ORDER BY site_code ASC
        """)

        locations_data = cursor.fetchall()
        locations = []

        for location in locations_data:
            locations.append({
                "id": location[0],
                "site_code": location[1] or f"BIZ{location[0]:03d}",
                "site_name": location[2] or "",
                "site_type": location[3] or "미지정",
                "region": location[4] or "미지정",
                "address": location[5] or "",
                "manager_name": location[6] or "",
                "manager_phone": location[7] or "",
                "is_active": bool(location[8])
            })

        conn.close()

        return {
            "success": True,
            "locations": locations,
            "total": len(locations)
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/suppliers")
async def get_admin_suppliers():
    """관리자용 협력업체 목록 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.text_factory = lambda x: x.decode('utf-8', errors='replace') if isinstance(x, bytes) else x
        cursor = conn.cursor()

        # suppliers 테이블이 있는지 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='suppliers'")
        suppliers_table_exists = cursor.fetchone()

        if suppliers_table_exists:
            cursor.execute("""
                SELECT id, name, representative, headquarters_phone, email, is_active
                FROM suppliers
                ORDER BY name ASC
            """)

            suppliers_data = cursor.fetchall()
            suppliers = []

            for supplier in suppliers_data:
                suppliers.append({
                    "id": supplier[0],
                    "name": supplier[1],
                    "contact_person": supplier[2] or "미지정",
                    "contact_phone": supplier[3] or "미지정",
                    "email": supplier[4] or "미지정",
                    "active": bool(supplier[5])
                })
        else:
            # suppliers 테이블이 없으면 ingredients에서 추출
            cursor.execute("""
                SELECT DISTINCT supplier_name, COUNT(*) as ingredient_count
                FROM ingredients 
                WHERE supplier_name IS NOT NULL AND supplier_name != ''
                GROUP BY supplier_name
                ORDER BY supplier_name ASC
            """)
            
            suppliers_data = cursor.fetchall()
            suppliers = []
            
            for i, supplier in enumerate(suppliers_data):
                suppliers.append({
                    "id": i + 1,
                    "name": supplier[0],
                    "contact_person": "미지정",
                    "contact_phone": "미지정", 
                    "email": "미지정",
                    "active": True,
                    "ingredient_count": supplier[1]
                })
        
        conn.close()
        
        return {
            "success": True,
            "suppliers": suppliers,
            "total": len(suppliers)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/ingredients-new")
async def get_admin_ingredients_new(page: int = 1, per_page: int = 20, search: str = None, category: str = None, supplier: str = None):
    """관리자용 식자재 목록 (페이징, 검색, 필터링)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # WHERE 조건 구성
        where_conditions = []
        params = []

        if search:
            where_conditions.append("(ingredient_name LIKE ? OR ingredient_code LIKE ?)")
            params.append(f"%{search}%")
            params.append(f"%{search}%")

        if category:
            where_conditions.append("category = ?")
            params.append(category)

        if supplier:
            where_conditions.append("supplier_name = ?")
            params.append(supplier)

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # 총 개수 조회
        count_query = f"SELECT COUNT(*) FROM ingredients {where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # 페이징 계산 - 검색 시에는 제한 해제, 일반 조회 시에만 제한
        if search or supplier or category:
            # 검색/필터링 시에는 전체 결과 반환 (84,000개 모두 검색 가능)
            per_page = min(per_page, 100000)  # 충분히 큰 값으로 설정
        else:
            # 일반 조회 시에만 제한 적용
            per_page = min(per_page, 1000)
        total_pages = (total_count + per_page - 1) // per_page
        offset = (page - 1) * per_page
        
        # 데이터 조회
        data_query = f"""
            SELECT
                id,
                category,
                sub_category,
                ingredient_code,
                ingredient_name,
                origin,
                posting_status,
                specification,
                unit,
                tax_type,
                delivery_days,
                purchase_price,
                selling_price,
                supplier_name,
                notes,
                created_at
            FROM ingredients
            {where_clause}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """

        cursor.execute(data_query, params + [per_page, offset])
        ingredients = []

        for row in cursor.fetchall():
            # 단위당 단가 계산
            purchase_price = row[11] or 0
            specification = row[7] or ""
            unit = row[8] or ""
            price_per_unit = calculate_unit_price_improved(purchase_price, specification, unit)

            ingredients.append({
                "id": row[0],
                "category": row[1] or "-",
                "sub_category": row[2] or "-",
                "ingredient_code": row[3] or "-",
                "ingredient_name": row[4] or "-",
                "origin": row[5] or "-",
                "posting_status": row[6] or "미지정",
                "specification": row[7] or "-",
                "unit": row[8] or "-",
                "tax_type": row[9] or "-",
                "delivery_days": row[10] or "-",
                "purchase_price": row[11] or 0,
                "selling_price": row[12] or 0,
                "supplier_name": row[13] or "-",
                "notes": row[14] or "-",
                "created_at": row[15] or "",
                "price_per_unit": price_per_unit  # 실시간 계산된 단위당 단가
            })
        
        conn.close()
        
        return {
            "success": True,
            "ingredients": ingredients,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "items_per_page": per_page,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/ingredients")
async def create_ingredient(ingredient_data: dict):
    """관리자용 식자재 추가"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 단위당 단가 자동 계산
        purchase_price = ingredient_data.get('purchase_price', 0)
        specification = ingredient_data.get('specification', '')
        unit_price = calculate_unit_price(purchase_price, specification)

        # price_per_unit 컬럼 확인 및 추가
        cursor.execute("PRAGMA table_info(ingredients)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'price_per_unit' not in columns:
            cursor.execute("ALTER TABLE ingredients ADD COLUMN price_per_unit REAL")

        cursor.execute("""
            INSERT INTO ingredients (
                ingredient_name, category, supplier_name,
                purchase_price, selling_price, unit, origin, specification,
                price_per_unit, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            ingredient_data.get('name'),
            ingredient_data.get('category'),
            ingredient_data.get('supplier'),
            purchase_price,
            ingredient_data.get('selling_price', 0),
            ingredient_data.get('unit'),
            ingredient_data.get('origin'),
            specification,
            unit_price
        ))

        ingredient_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # 활동 로그 기록
        log_activity(
            action_type="식자재 추가",
            action_detail=f"새 식자재 '{ingredient_data.get('name')}' (공급업체: {ingredient_data.get('supplier', '미지정')}) 추가",
            user="관리자",
            entity_type="ingredient",
            entity_id=ingredient_id
        )

        return {"success": True, "message": "식자재가 추가되었습니다.", "unit_price": unit_price}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/admin/ingredients/{ingredient_id}")
async def update_ingredient(ingredient_id: int, ingredient_data: dict):
    """관리자용 식자재 수정"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE ingredients SET
                ingredient_name = ?,
                category = ?,
                supplier_name = ?,
                purchase_price = ?,
                selling_price = ?,
                unit = ?,
                origin = ?,
                specification = ?
            WHERE id = ?
        """, (
            ingredient_data.get('name'),
            ingredient_data.get('category'),
            ingredient_data.get('supplier'),
            ingredient_data.get('purchase_price'),
            ingredient_data.get('selling_price'),
            ingredient_data.get('unit'),
            ingredient_data.get('origin'),
            ingredient_data.get('specification'),
            ingredient_id
        ))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "식자재가 수정되었습니다."}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/ingredients/recalculate-unit-prices")
async def recalculate_all_unit_prices():
    """모든 식자재의 단위당 단가 재계산"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # price_per_unit 컬럼 확인 및 추가
        cursor.execute("PRAGMA table_info(ingredients)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'price_per_unit' not in columns:
            cursor.execute("ALTER TABLE ingredients ADD COLUMN price_per_unit REAL")

        # 모든 식자재 조회 - unit 정보도 함께 조회
        cursor.execute("""
            SELECT id, specification, unit, purchase_price
            FROM ingredients
            WHERE purchase_price > 0 AND specification IS NOT NULL AND specification != ''
        """)

        ingredients = cursor.fetchall()
        updated_count = 0

        for ing_id, spec, unit, price in ingredients:
            # 개선된 계산 로직 사용 - unit 정보도 함께 전달
            unit_price = calculate_unit_price_improved(price, spec, unit)
            if unit_price is not None:
                cursor.execute("""
                    UPDATE ingredients
                    SET price_per_unit = ?
                    WHERE id = ?
                """, (unit_price, ing_id))
                updated_count += 1

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": f"{updated_count}개 식자재의 단위당 단가가 재계산되었습니다.",
            "updated_count": updated_count
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/admin/ingredients/{ingredient_id}")
async def delete_ingredient(ingredient_id: int):
    """관리자용 식자재 삭제"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM ingredients WHERE id = ?", (ingredient_id,))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "식자재가 삭제되었습니다."}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/ingredients")
async def get_ingredients(page: int = 1, per_page: int = 20, search: str = None, category: str = None):
    """사용자용 식자재 목록 조회 (페이징, 검색, 필터링) - 대용량 지원"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # WHERE 조건 구성
        where_conditions = []
        params = []

        if search:
            where_conditions.append("ingredient_name LIKE ?")
            params.append(f"%{search}%")

        if category:
            where_conditions.append("category = ?")
            params.append(category)

        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # 총 개수 조회
        count_query = f"SELECT COUNT(*) FROM ingredients {where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # 페이징 계산
        total_pages = (total_count + per_page - 1) // per_page
        offset = (page - 1) * per_page

        # 데이터 조회 - 모든 필드 포함
        data_query = f"""
            SELECT
                id,
                category,
                sub_category,
                ingredient_code,
                ingredient_name,
                posting_status,
                origin,
                specification,
                unit,
                tax_type,
                delivery_days,
                purchase_price,
                selling_price,
                supplier_name,
                notes,
                created_date,
                extra_field1,
                extra_field2,
                extra_field3,
                is_active,
                created_by,
                upload_batch_id,
                created_at,
                updated_at,
                price_per_gram,
                price_per_unit
            FROM ingredients
            {where_clause}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """

        cursor.execute(data_query, params + [per_page, offset])
        ingredients = []

        for row in cursor.fetchall():
            # 단위당 단가 계산 (이미 DB에 있으면 그 값 사용)
            purchase_price = row[11] or 0
            specification = row[7] or ""
            unit = row[8] or ""
            db_price_per_unit = row[25]  # price_per_unit from DB

            # DB에 값이 없으면 계산
            if db_price_per_unit is None:
                price_per_unit = calculate_unit_price_improved(purchase_price, specification, unit)
            else:
                price_per_unit = db_price_per_unit

            ingredients.append({
                "id": row[0],
                "category": row[1] or "-",
                "sub_category": row[2] or "-",
                "ingredient_code": row[3] or "-",
                "ingredient_name": row[4] or "-",
                "posting_status": row[5] or "미지정",
                "origin": row[6] or "-",
                "specification": row[7] or "-",
                "unit": row[8] or "-",
                "tax_type": row[9] or "-",
                "delivery_days": row[10] or "-",
                "purchase_price": row[11] or 0,
                "selling_price": row[12] or 0,
                "supplier_name": row[13] or "-",
                "notes": row[14] or "-",
                "created_date": row[15] or "-",
                "extra_field1": row[16] or "-",
                "extra_field2": row[17] or "-",
                "extra_field3": row[18] or "-",
                "is_active": row[19] if row[19] is not None else 1,
                "created_by": row[20] or "-",
                "upload_batch_id": row[21] or "-",
                "created_at": row[22] or "-",
                "updated_at": row[23] or "-",
                "price_per_gram": row[24] or 0,
                "price_per_unit": price_per_unit
            })

        conn.close()

        return {
            "success": True,
            "ingredients": ingredients,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "items_per_page": per_page,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/ingredients-summary")
async def get_admin_ingredients_summary():
    """관리자용 식자재 요약 통계"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 총 식자재 수
        cursor.execute("SELECT COUNT(*) FROM ingredients")
        total_ingredients = cursor.fetchone()[0]
        
        # 카테고리별 통계
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM ingredients
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY count DESC
            LIMIT 10
        """)
        
        categories = {}
        for row in cursor.fetchall():
            categories[row[0]] = row[1]
        
        # 업체별 통계
        cursor.execute("""
            SELECT supplier_name, COUNT(*) as count
            FROM ingredients
            WHERE supplier_name IS NOT NULL AND supplier_name != ''
            GROUP BY supplier_name
            ORDER BY count DESC
            LIMIT 10
        """)
        
        suppliers = {}
        for row in cursor.fetchall():
            suppliers[row[0]] = row[1]
        
        # 최근 추가된 식자재
        cursor.execute("""
            SELECT ingredient_name, supplier_name, category
            FROM ingredients
            WHERE ingredient_name IS NOT NULL
            ORDER BY rowid DESC
            LIMIT 20
        """)
        
        recent_ingredients = []
        for row in cursor.fetchall():
            recent_ingredients.append({
                "name": row[0],
                "supplier": row[1] or "미지정",
                "category": row[2] or "미지정"
            })
        
        conn.close()
        
        return {
            "success": True,
            "summary": {
                "total_ingredients": total_ingredients,
                "categories": categories,
                "suppliers": suppliers,
                "recent_ingredients": recent_ingredients
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/dashboard-stats")
async def get_dashboard_stats():
    """관리자 대시보드 통계 데이터"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 사용자 수
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # 사업장 수
        cursor.execute("SELECT COUNT(*) FROM business_locations")
        total_sites = cursor.fetchone()[0]
        
        # 식자재 수
        cursor.execute("SELECT COUNT(*) FROM ingredients")
        total_ingredients = cursor.fetchone()[0]
        
        # 공급업체 수 
        cursor.execute("SELECT COUNT(DISTINCT supplier_name) FROM ingredients WHERE supplier_name IS NOT NULL")
        total_suppliers = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "success": True,
            "totalUsers": total_users,
            "totalSites": total_sites,
            "totalIngredients": total_ingredients,
            "totalSuppliers": total_suppliers
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/recent-activity")
async def get_recent_activity():
    """최근 활동 로그"""
    try:
        # 간단한 더미 데이터 반환
        activities = [
            {"time": "2025-09-13 02:30", "user": "관리자", "action": "식자재 데이터 업데이트", "status": "완료"},
            {"time": "2025-09-13 02:25", "user": "관리자", "action": "사용자 추가", "status": "완료"},
            {"time": "2025-09-13 02:20", "user": "영양사", "action": "식단 등록", "status": "완료"}
        ]
        
        return {
            "success": True,
            "activities": activities
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/sites")
async def get_sites():
    """사업장 목록 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        # UTF-8 텍스트 처리 설정 추가
        conn.text_factory = lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, site_name, site_type, region, address, phone, is_active 
            FROM business_locations 
            ORDER BY site_name
        """)
        sites = cursor.fetchall()
        
        conn.close()
        
        sites_list = []
        for site in sites:
            sites_list.append({
                "id": site[0],
                "name": site[1],  # site_name
                "type": site[2],  # site_type
                "parent_id": site[3],  # region
                "address": site[4],
                "contact_info": site[5],  # phone
                "status": "활성" if site[6] else "비활성"  # is_active
            })
        
        return {
            "success": True,
            "sites": sites_list
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/sites/{site_id}")
async def get_site(site_id: int):
    """개별 사업장 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        # UTF-8 텍스트 처리 설정 추가
        conn.text_factory = lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, site_name, site_type, region, address, phone, is_active 
            FROM business_locations 
            WHERE id = ?
        """, (site_id,))
        site = cursor.fetchone()
        
        conn.close()
        
        if not site:
            return {"success": False, "error": "사업장을 찾을 수 없습니다"}
        
        site_info = {
            "id": site[0],
            "name": site[1],  # site_name
            "type": site[2],  # site_type
            "parent_id": site[3],  # region
            "address": site[4],
            "contact_info": site[5],  # phone
            "status": "활성" if site[6] else "비활성"  # is_active
        }
        
        return {
            "success": True,
            "site": site_info
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/sites")
async def create_site(site_data: dict):
    """사업장 추가"""
    try:
        print(f"[CREATE SITE] Received data: {site_data}")

        conn = sqlite3.connect(DATABASE_PATH)
        conn.text_factory = lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
        cursor = conn.cursor()

        # site_code 자동 생성
        site_code = site_data.get('site_code', '')
        if not site_code:
            # 기존 최대 번호 찾기
            cursor.execute("""
                SELECT MAX(CAST(SUBSTR(site_code, 4) AS INTEGER))
                FROM business_locations
                WHERE site_code LIKE 'BIZ%'
            """)
            max_num = cursor.fetchone()[0]
            next_num = (max_num or 0) + 1
            site_code = f'BIZ{next_num:03d}'
            print(f"[CREATE SITE] Generated site_code: {site_code}")

        # site_code 중복 체크
        cursor.execute("SELECT id FROM business_locations WHERE site_code = ?", (site_code,))
        if cursor.fetchone():
            print(f"[CREATE SITE] Duplicate site_code: {site_code}")
            conn.close()
            return {"success": False, "error": f"사업장 코드 '{site_code}'가 이미 존재합니다."}

        # 삽입 쿼리
        print(f"[CREATE SITE] Inserting with site_code={site_code}, name={site_data.get('name', '')}")
        cursor.execute("""
            INSERT INTO business_locations (site_code, site_name, site_type, region, address, phone, manager_name, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            site_code,
            site_data.get('name', ''),
            site_data.get('type', ''),
            site_data.get('parent_id', '전국'),
            site_data.get('address', ''),
            site_data.get('contact_info', ''),
            site_data.get('manager_name', ''),
            True
        ))

        conn.commit()

        # 삽입 확인
        cursor.execute("SELECT COUNT(*) FROM business_locations WHERE site_code = ?", (site_code,))
        count = cursor.fetchone()[0]
        print(f"[CREATE SITE] After insert, found {count} records with site_code={site_code}")

        conn.close()

        return {"success": True, "message": "사업장이 추가되었습니다", "site_code": site_code}

    except Exception as e:
        print(f"[CREATE SITE] Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.put("/api/admin/sites/{site_id}")
async def update_site(site_id: int, site_data: dict):
    """사업장 수정"""
    try:
        # 디버깅을 위해 받은 데이터 출력
        print(f"[UPDATE SITE {site_id}] Received data:", site_data)

        conn = sqlite3.connect(DATABASE_PATH)  # 올바른 데이터베이스 경로 사용
        conn.text_factory = lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
        cursor = conn.cursor()

        # 필드명이 일치하도록 수정
        cursor.execute("""
            UPDATE business_locations
            SET site_name = ?, site_type = ?, region = ?, manager_name = ?, manager_phone = ?, is_active = ?
            WHERE id = ?
        """, (
            site_data.get('name', ''),
            site_data.get('type', ''),
            site_data.get('parent_id', '서울'),  # region 필드에 parent_id 값 사용
            site_data.get('manager_name', ''),  # manager_name 추가
            site_data.get('contact_info', ''),
            1 if site_data.get('is_active', True) else 0,
            site_id
        ))

        affected_rows = cursor.rowcount
        conn.commit()

        # 업데이트된 데이터 확인
        cursor.execute("SELECT site_name, site_type, region FROM business_locations WHERE id = ?", (site_id,))
        updated = cursor.fetchone()
        print(f"[UPDATE SITE {site_id}] Updated data: {updated}, Affected rows: {affected_rows}")

        conn.close()

        return {"success": True, "message": f"사업장이 수정되었습니다 (ID: {site_id})"}

    except Exception as e:
        print(f"[UPDATE SITE ERROR] {str(e)}")
        return {"success": False, "error": str(e)}

@app.delete("/api/admin/sites/{site_id}")
async def delete_site(site_id: int):
    """사업장 삭제"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.text_factory = lambda x: x.decode('utf-8') if isinstance(x, bytes) else x
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM business_locations WHERE id = ?", (site_id,))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "사업장이 삭제되었습니다"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/users")
async def get_users():
    """사용자 목록 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, contact_info, role, is_active, created_at 
            FROM users 
            ORDER BY created_at DESC
        """)
        users = cursor.fetchall()
        
        conn.close()
        
        users_list = []
        for user in users:
            users_list.append({
                "id": user[0],
                "username": user[1],
                "contact_info": user[2],
                "email": "",  # 이메일 컬럼이 없음
                "role": user[3],
                "is_active": bool(user[4]),
                "created_at": user[5]
            })
        
        return {
            "success": True,
            "users": users_list
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/suppliers/enhanced")
async def get_suppliers_enhanced(page: int = 1, limit: int = 20, search: str = ""):
    """협력업체 목록 조회 (향상된 버전)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # 검색 조건 추가
        search_condition = ""
        params = []
        if search.strip():
            search_condition = "WHERE supplier_name LIKE ?"
            params.append(f"%{search}%")
        
        # 공급업체별 통계 조회
        cursor.execute(f"""
            SELECT 
                supplier_name,
                COUNT(*) as ingredient_count,
                AVG(purchase_price) as avg_price,
                MIN(purchase_price) as min_price,
                MAX(purchase_price) as max_price
            FROM ingredients 
            WHERE supplier_name IS NOT NULL {search_condition.replace('WHERE', 'AND') if search_condition else ''}
            GROUP BY supplier_name
            ORDER BY ingredient_count DESC
            LIMIT ? OFFSET ?
        """, params + [limit, (page - 1) * limit])
        
        suppliers = cursor.fetchall()
        
        # 총 개수 조회
        cursor.execute(f"""
            SELECT COUNT(DISTINCT supplier_name) 
            FROM ingredients 
            WHERE supplier_name IS NOT NULL {search_condition}
        """, params)
        
        total_count = cursor.fetchone()[0]
        total_pages = (total_count + limit - 1) // limit
        
        conn.close()
        
        suppliers_list = []
        for supplier in suppliers:
            suppliers_list.append({
                "id": supplier[0],  # supplier_name을 ID로 사용
                "name": supplier[0],
                "ingredient_count": supplier[1],
                "avg_price": round(supplier[2] or 0, 2),
                "min_price": supplier[3] or 0,
                "max_price": supplier[4] or 0,
                "status": "활성",
                "last_updated": "2025-09-13"
            })
        
        return {
            "success": True,
            "suppliers": suppliers_list,
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

@app.get("/api/admin/customer-supplier-mappings")
async def get_customer_supplier_mappings():
    """고객-협력업체 매핑 목록 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.text_factory = lambda x: x.decode('utf-8', errors='replace') if isinstance(x, bytes) else x
        cursor = conn.cursor()
        
        # 매핑 데이터를 사업장 및 협력업체 정보와 함께 조회
        cursor.execute("""
            SELECT
                csm.id,
                csm.customer_id,
                csm.supplier_id,
                b.site_name as customer_name,
                s.name as supplier_name,
                csm.supplier_code,
                csm.delivery_code,
                csm.priority_order,
                csm.is_primary_supplier,
                csm.contract_start_date,
                csm.contract_end_date,
                csm.is_active,
                csm.notes,
                csm.created_at
            FROM customer_supplier_mappings csm
            LEFT JOIN business_locations b ON csm.customer_id = b.id
            LEFT JOIN suppliers s ON csm.supplier_id = s.id
            ORDER BY csm.priority_order, b.site_name, s.name
        """)
        mappings_data = cursor.fetchall()
        
        conn.close()
        
        mappings = []
        for mapping in mappings_data:
            mappings.append({
                "id": mapping[0],
                "customer_id": mapping[1],
                "supplier_id": mapping[2],
                "customer_name": mapping[3],
                "supplier_name": mapping[4],
                "supplier_code": mapping[5] or "",
                "delivery_code": mapping[6] or "",
                "priority_order": mapping[7] or 0,
                "is_primary_supplier": bool(mapping[8]),
                "contract_start_date": mapping[9],
                "contract_end_date": mapping[10],
                "is_active": bool(mapping[11]),
                "notes": mapping[12] or "",
                "created_at": mapping[13]
            })
        
        return {
            "success": True,
            "mappings": mappings
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/customer-supplier-mappings/{mapping_id}")
async def get_customer_supplier_mapping(mapping_id: int):
    """특정 고객-협력업체 매핑 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT
                csm.id,
                csm.customer_id,
                csm.supplier_id,
                b.site_name as customer_name,
                s.name as supplier_name,
                csm.supplier_code,
                csm.delivery_code,
                csm.priority_order,
                csm.is_primary_supplier,
                csm.contract_start_date,
                csm.contract_end_date,
                csm.is_active,
                csm.notes,
                csm.created_at
            FROM customer_supplier_mappings csm
            LEFT JOIN business_locations b ON csm.customer_id = b.id
            LEFT JOIN suppliers s ON csm.supplier_id = s.id
            WHERE csm.id = ?
        """, (mapping_id,))
        
        mapping_data = cursor.fetchone()
        conn.close()
        
        if not mapping_data:
            return {"success": False, "error": "매핑을 찾을 수 없습니다"}
        
        mapping = {
            "id": mapping_data[0],
            "customer_id": mapping_data[1],
            "supplier_id": mapping_data[2],
            "customer_name": mapping_data[3],
            "supplier_name": mapping_data[4],
            "supplier_code": mapping_data[5] or "",
            "delivery_code": mapping_data[6] or "",
            "priority_order": mapping_data[7] or 0,
            "is_primary_supplier": bool(mapping_data[8]),
            "contract_start_date": mapping_data[9],
            "contract_end_date": mapping_data[10],
            "is_active": bool(mapping_data[11]),
            "notes": mapping_data[12] or "",
            "created_at": mapping_data[13]
        }
        
        return {
            "success": True,
            "mapping": mapping
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/customer-supplier-mappings")
async def create_customer_supplier_mapping(mapping_data: dict):
    """고객-협력업체 매핑 생성"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO customer_supplier_mappings
            (customer_id, supplier_id, supplier_code, delivery_code, priority_order, is_primary_supplier, is_active, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mapping_data.get('customer_id'),
            mapping_data.get('supplier_id'),
            mapping_data.get('supplier_code', ''),
            mapping_data.get('delivery_code', ''),
            mapping_data.get('priority_order', 1),
            mapping_data.get('is_primary_supplier', False),
            mapping_data.get('is_active', True),
            mapping_data.get('notes', '')
        ))

        mapping_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "매핑이 생성되었습니다",
            "id": mapping_id
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/admin/customer-supplier-mappings/{mapping_id}")
async def update_customer_supplier_mapping(mapping_id: int, mapping_data: dict):
    """고객-협력업체 매핑 수정"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE customer_supplier_mappings
            SET customer_id = ?, supplier_id = ?, supplier_code = ?, delivery_code = ?, is_active = ?
            WHERE id = ?
        """, (
            mapping_data.get('customer_id'),
            mapping_data.get('supplier_id'),
            mapping_data.get('supplier_code', ''),
            mapping_data.get('delivery_code', ''),
            mapping_data.get('is_active', True),
            mapping_id
        ))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "매핑이 수정되었습니다"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/admin/customer-supplier-mappings/{mapping_id}")
async def delete_customer_supplier_mapping(mapping_id: int):
    """고객-협력업체 매핑 삭제"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM customer_supplier_mappings WHERE id = ?", (mapping_id,))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "매핑이 삭제되었습니다"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# 식단가 관리 API 엔드포인트
@app.get("/api/admin/meal-pricing")
async def get_meal_pricing():
    """식단가 목록 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        # UTF-8 디코딩을 위한 text_factory 설정
        conn.text_factory = lambda x: x.decode('utf-8', errors='replace') if isinstance(x, bytes) else x
        cursor = conn.cursor()

        # 식단가 데이터 조회
        cursor.execute("""
            SELECT
                id, location_id, location_name, meal_plan_type, meal_type,
                plan_name, apply_date_start, apply_date_end, selling_price,
                material_cost_guideline, cost_ratio, is_active, created_at
            FROM meal_pricing
            ORDER BY location_name, meal_plan_type, meal_type
        """)

        meal_pricing = []
        for row in cursor.fetchall():
            meal_pricing.append({
                "id": row[0],
                "location_id": row[1],
                "location_name": row[2],
                "meal_plan_type": row[3],
                "meal_type": row[4],
                "plan_name": row[5],
                "apply_date_start": row[6],
                "apply_date_end": row[7],
                "selling_price": float(row[8] or 0),
                "material_cost_guideline": float(row[9] or 0),
                "cost_ratio": float(row[10] or 0),
                "is_active": bool(row[11]),
                "created_at": row[12]
            })

        # 통계 계산
        total = len(meal_pricing)
        active = sum(1 for mp in meal_pricing if mp["is_active"])
        locations = len(set(mp["location_name"] for mp in meal_pricing))

        avg_selling_price = 0
        avg_cost_ratio = 0
        if meal_pricing:
            avg_selling_price = sum(mp["selling_price"] for mp in meal_pricing) / len(meal_pricing)
            avg_cost_ratio = sum(mp["cost_ratio"] for mp in meal_pricing) / len(meal_pricing)

        conn.close()

        return {
            "success": True,
            "meal_pricing": meal_pricing,
            "statistics": {
                "total": total,
                "active": active,
                "locations": locations,
                "avg_selling_price": avg_selling_price,
                "avg_cost_ratio": avg_cost_ratio
            }
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/meal-pricing")
async def create_meal_pricing(data: dict):
    """식단가 추가"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.text_factory = lambda x: x.decode('utf-8', errors='replace') if isinstance(x, bytes) else x
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO meal_pricing (
                location_id, location_name, meal_plan_type, meal_type,
                plan_name, apply_date_start, apply_date_end, selling_price,
                material_cost_guideline, cost_ratio, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, (
            data.get("location_id", 1),  # 기본값 1
            data.get("location_name"),
            data.get("meal_plan_type"),
            data.get("meal_type"),
            data.get("plan_name"),
            data.get("apply_date_start"),
            data.get("apply_date_end"),
            data.get("selling_price"),
            data.get("material_cost_guideline"),
            data.get("cost_ratio", 50),
            data.get("is_active", 1)
        ))

        conn.commit()
        new_id = cursor.lastrowid
        conn.close()

        return {"success": True, "id": new_id}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/admin/meal-pricing/{pricing_id}")
async def update_meal_pricing(pricing_id: int, data: dict):
    """식단가 수정"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.text_factory = lambda x: x.decode('utf-8', errors='replace') if isinstance(x, bytes) else x
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE meal_pricing SET
                location_name = ?,
                meal_plan_type = ?,
                meal_type = ?,
                plan_name = ?,
                apply_date_start = ?,
                apply_date_end = ?,
                selling_price = ?,
                material_cost_guideline = ?,
                cost_ratio = ?,
                is_active = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (
            data.get("location_name"),
            data.get("meal_plan_type"),
            data.get("meal_type"),
            data.get("plan_name"),
            data.get("apply_date_start"),
            data.get("apply_date_end"),
            data.get("selling_price"),
            data.get("material_cost_guideline"),
            data.get("cost_ratio"),
            data.get("is_active"),
            pricing_id
        ))

        conn.commit()
        conn.close()

        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/admin/meal-pricing/{pricing_id}")
async def delete_meal_pricing(pricing_id: int):
    """식단가 삭제"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.text_factory = lambda x: x.decode('utf-8', errors='replace') if isinstance(x, bytes) else x
        cursor = conn.cursor()

        cursor.execute("DELETE FROM meal_pricing WHERE id = ?", (pricing_id,))

        conn.commit()
        conn.close()

        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}

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

        # 활동 로그 기록
        log_activity(
            action_type="사용자 추가",
            action_detail=f"새 사용자 '{user_data.username}' (권한: {user_data.role}) 추가",
            user="관리자",
            entity_type="user",
            entity_id=user_id
        )

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

# 사용자 통계 API 엔드포인트 (충돌 방지를 위해 별도 경로 사용)
@app.get("/api/admin/users/stats")
async def get_users_stats():
    """사용자 통계 정보 반환"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 전체 사용자 수
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        # 활성 사용자 수 (is_active가 1인 사용자)
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        active_users = cursor.fetchone()[0]

        conn.close()

        return {
            "success": True,
            "total": total_users,
            "active": active_users
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/users")
async def create_user(user_data: dict):
    """새 사용자 생성"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users (username, contact_info, department, role, password_hash, notes, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (
            user_data.get("username"),
            user_data.get("contact_info"),
            user_data.get("department"),
            user_data.get("role"),
            f"hashed_{user_data.get('password', 'default')}",  # 간단한 해시 처리
            user_data.get("notes", "")
        ))

        conn.commit()

        # 새로 생성된 사용자 ID 가져오기
        new_user_id = cursor.lastrowid

        # 사업장 권한 추가
        if "site_permissions" in user_data:
            for site_id in user_data["site_permissions"]:
                cursor.execute("""
                    INSERT INTO user_site_permissions (user_id, site_id, can_view, can_edit)
                    VALUES (?, ?, 1, 0)
                """, (new_user_id, site_id))
            conn.commit()

        conn.close()

        return {"success": True, "message": "사용자가 생성되었습니다."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/users/{user_id}/deactivate")
async def deactivate_user(user_id: int):
    """사용자 비활성화"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

        return {"success": True, "message": "사용자가 비활성화되었습니다."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/users/{user_id}/activate")
async def activate_user(user_id: int):
    """사용자 활성화"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("UPDATE users SET is_active = 1 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()

        return {"success": True, "message": "사용자가 활성화되었습니다."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """특정 사용자 정보 반환"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, contact_info, department, role, is_active,
                   created_at, notes
            FROM users WHERE id = ?
        """, (user_id,))

        row = cursor.fetchone()
        if not row:
            return {"success": False, "error": "사용자를 찾을 수 없습니다."}

        user = {
            "id": row[0],
            "username": row[1],
            "contact_info": row[2],
            "department": row[3],
            "role": row[4],
            "is_active": bool(row[5]),
            "created_at": row[6],
            "notes": row[7]
        }

        conn.close()
        return user
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/users/{user_id}")
async def update_user(user_id: int, user_data: dict):
    """사용자 정보 수정"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET username = ?, contact_info = ?, department = ?, role = ?, notes = ?
            WHERE id = ?
        """, (
            user_data.get("username"),
            user_data.get("contact_info"),
            user_data.get("department"),
            user_data.get("role"),
            user_data.get("notes", ""),
            user_id
        ))

        conn.commit()

        # 사업장 권한 업데이트
        if "site_permissions" in user_data:
            # 기존 권한 삭제
            cursor.execute("DELETE FROM user_site_permissions WHERE user_id = ?", (user_id,))

            # 새로운 권한 추가
            for site_id in user_data["site_permissions"]:
                cursor.execute("""
                    INSERT INTO user_site_permissions (user_id, site_id, can_view, can_edit)
                    VALUES (?, ?, 1, 0)
                """, (user_id, site_id))

            conn.commit()

        conn.close()

        return {"success": True, "message": "사용자 정보가 수정되었습니다."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/users/{user_id}/permissions")
async def get_user_permissions(user_id: int):
    """사용자의 사업장 권한 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT site_id, can_view, can_edit
            FROM user_site_permissions
            WHERE user_id = ?
        """, (user_id,))

        permissions = []
        for row in cursor.fetchall():
            permissions.append({
                "site_id": row[0],
                "can_view": bool(row[1]),
                "can_edit": bool(row[2])
            })

        conn.close()
        return permissions
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/admin/users/{user_id}")
async def update_admin_user(user_id: int, user_data: dict):
    """관리자 페이지용 사용자 정보 수정"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 사용자 존재 확인
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

        # 업데이트할 필드 동적 구성
        update_fields = []
        params = []

        # 각 필드 처리
        if "username" in user_data:
            update_fields.append("username = ?")
            params.append(user_data["username"])

        if "password" in user_data and user_data["password"]:
            update_fields.append("password_hash = ?")
            params.append(f"hashed_{user_data['password']}")  # 실제로는 bcrypt 사용

        if "contact_info" in user_data:
            update_fields.append("contact_info = ?")
            params.append(user_data["contact_info"])

        # email 필드는 users 테이블에 없으므로 제외
        # if "email" in user_data:
        #     update_fields.append("email = ?")
        #     params.append(user_data["email"])

        if "department" in user_data:
            update_fields.append("department = ?")
            params.append(user_data["department"])

        if "position" in user_data:
            update_fields.append("position = ?")
            params.append(user_data["position"])

        if "role" in user_data:
            update_fields.append("role = ?")
            params.append(user_data["role"])

        if "operator" in user_data:
            update_fields.append("operator = ?")
            params.append(1 if user_data["operator"] else 0)

        if "semi_operator" in user_data:
            update_fields.append("semi_operator = ?")
            params.append(1 if user_data["semi_operator"] else 0)

        if "managed_site" in user_data:
            update_fields.append("managed_site = ?")
            params.append(user_data["managed_site"])

        if "is_active" in user_data:
            update_fields.append("is_active = ?")
            params.append(1 if user_data["is_active"] else 0)

        # notes 필드도 users 테이블에 없으므로 제외
        # if "notes" in user_data:
        #     update_fields.append("notes = ?")
        #     params.append(user_data["notes"])

        # 업데이트 실행
        if update_fields:
            update_fields.append("updated_at = ?")
            params.append(datetime.datetime.now().isoformat())
            params.append(user_id)

            query = f"""
                UPDATE users
                SET {', '.join(update_fields)}
                WHERE id = ?
            """

            cursor.execute(query, params)
            conn.commit()

        conn.close()
        return {"success": True, "message": "사용자 정보가 수정되었습니다."}

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"사용자 수정 오류: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/users")
async def create_admin_user(user_data: dict):
    """관리자 페이지용 새 사용자 추가"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 중복 사용자명 확인
        cursor.execute("SELECT id FROM users WHERE username = ?", (user_data.get("username", ""),))
        if cursor.fetchone():
            conn.close()
            return {"success": False, "message": "이미 존재하는 사용자명입니다."}

        # 필수 필드 확인
        if not user_data.get("username"):
            conn.close()
            return {"success": False, "message": "사용자명은 필수입니다."}

        # 새 사용자 추가
        cursor.execute("""
            INSERT INTO users (
                username, password_hash, contact_info,
                department, position, role,
                operator, semi_operator, managed_site,
                is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_data.get("username"),
            f"hashed_{user_data.get('password', '1234')}",  # 실제로는 bcrypt 사용
            user_data.get("contact_info", ""),
            user_data.get("department", ""),
            user_data.get("position", ""),
            user_data.get("role", "viewer"),
            1 if user_data.get("operator", False) else 0,
            1 if user_data.get("semi_operator", False) else 0,
            user_data.get("managed_site", ""),
            1 if user_data.get("is_active", True) else 0,
            datetime.datetime.now().isoformat(),
            datetime.datetime.now().isoformat()
        ))

        conn.commit()
        new_user_id = cursor.lastrowid
        conn.close()

        return {
            "success": True,
            "message": "사용자가 추가되었습니다.",
            "user_id": new_user_id
        }

    except Exception as e:
        print(f"사용자 추가 오류: {str(e)}")
        return {"success": False, "message": str(e)}

@app.post("/api/admin/users/{user_id}/reset-password")
async def reset_admin_user_password(user_id: int, data: dict):
    """관리자 페이지용 비밀번호 초기화"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        new_password = data.get("new_password", "1234")
        hashed_password = f"hashed_{new_password}"  # 실제로는 bcrypt 등을 사용해야 함

        cursor.execute("""
            UPDATE users
            SET password = ?
            WHERE id = ?
        """, (hashed_password, user_id))

        conn.commit()
        conn.close()

        return {"success": True, "message": "비밀번호가 초기화되었습니다."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/users/{user_id}/reset-password")
async def reset_user_password(user_id: int, data: dict):
    """사용자 비밀번호 초기화"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        new_password = data.get("new_password", "1234")
        hashed_password = f"hashed_{new_password}"  # 실제로는 bcrypt 등을 사용해야 함

        cursor.execute("""
            UPDATE users
            SET password = ?
            WHERE id = ?
        """, (hashed_password, user_id))

        conn.commit()
        conn.close()

        return {"success": True, "message": "비밀번호가 초기화되었습니다."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/users")
async def get_users(page: int = 1, per_page: int = 10, search: str = "", role: str = ""):
    """사용자 목록 반환 (페이지네이션 지원)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 기본 쿼리
        base_query = "FROM users WHERE 1=1"
        params = []

        # 검색 조건 추가
        if search:
            base_query += " AND (username LIKE ? OR contact_info LIKE ? OR department LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        # 권한 필터 추가
        if role:
            base_query += " AND role = ?"
            params.append(role)

        # 전체 개수 조회
        cursor.execute(f"SELECT COUNT(*) {base_query}", params)
        total_items = cursor.fetchone()[0]

        # 페이지네이션 계산
        offset = (page - 1) * per_page
        total_pages = (total_items + per_page - 1) // per_page

        # 사용자 목록 조회
        cursor.execute(f"""
            SELECT id, username, contact_info, department, role, is_active,
                   created_at, notes
            {base_query}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])

        users = []
        for row in cursor.fetchall():
            users.append({
                "id": row[0],
                "username": row[1],
                "contact_info": row[2],
                "department": row[3],
                "role": row[4],
                "is_active": bool(row[5]),
                "created_at": row[6],
                "notes": row[7]
            })

        conn.close()

        return {
            "success": True,
            "users": users,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_items,
                "items_per_page": per_page,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ===============================
# 협력업체 관리 API 엔드포인트들
# ===============================

@app.get("/api/admin/suppliers/stats")
async def get_supplier_stats():
    """협력업체 통계 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 총 협력업체 수
        cursor.execute("SELECT COUNT(*) FROM suppliers")
        total = cursor.fetchone()[0]

        # 활성 협력업체 수
        cursor.execute("SELECT COUNT(*) FROM suppliers WHERE is_active = 1")
        active = cursor.fetchone()[0]

        conn.close()

        return {
            "success": True,
            "total": total,
            "active": active
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/suppliers")
async def get_suppliers(page: int = 1, per_page: int = 10, search: str = "", status: str = ""):
    """협력업체 목록 조회 (페이지네이션, 검색, 필터링)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # WHERE 조건 구성
        where_conditions = []
        params = []

        if search:
            where_conditions.append("(name LIKE ? OR parent_code LIKE ? OR business_number LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])

        if status:
            if status == "active":
                where_conditions.append("is_active = 1")
            elif status == "inactive":
                where_conditions.append("is_active = 0")

        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)

        # 총 개수 조회
        count_query = f"SELECT COUNT(*) FROM suppliers {where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()[0]

        # 페이징 계산
        total_pages = (total_count + per_page - 1) // per_page
        offset = (page - 1) * per_page

        # 데이터 조회
        data_query = f"""
            SELECT id, name, parent_code, business_number, representative,
                   headquarters_phone, email, is_active, created_at
            FROM suppliers
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """

        cursor.execute(data_query, params + [per_page, offset])
        suppliers = []

        for row in cursor.fetchall():
            suppliers.append({
                "id": row[0],
                "name": row[1] or "",
                "parent_code": row[2] or "",
                "business_number": row[3] or "",
                "representative": row[4] or "",
                "headquarters_phone": row[5] or "",
                "email": row[6] or "",
                "is_active": bool(row[7]),
                "created_at": row[8]
            })

        conn.close()

        return {
            "success": True,
            "suppliers": suppliers,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_count,
                "items_per_page": per_page,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/suppliers")
async def create_supplier(supplier: SupplierCreate):
    """협력업체 생성"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 중복 이름 확인
        cursor.execute("SELECT id FROM suppliers WHERE name = ?", (supplier.name,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="이미 존재하는 협력업체 이름입니다.")

        # 사업자번호 중복 확인
        if supplier.business_number:
            cursor.execute("SELECT id FROM suppliers WHERE business_number = ?", (supplier.business_number,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="이미 존재하는 사업자번호입니다.")

        # 협력업체 추가
        cursor.execute("""
            INSERT INTO suppliers (
                name, parent_code, business_number, representative,
                headquarters_address, headquarters_phone, email, notes,
                is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, datetime('now'))
        """, (
            supplier.name,
            supplier.parent_code if supplier.parent_code else None,
            supplier.business_number if supplier.business_number else None,
            supplier.representative if supplier.representative else None,
            supplier.headquarters_address if supplier.headquarters_address else None,
            supplier.headquarters_phone if supplier.headquarters_phone else None,
            supplier.email if supplier.email else None,
            supplier.notes if supplier.notes else None
        ))

        supplier_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "협력업체가 생성되었습니다.",
            "supplier_id": supplier_id
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/suppliers/{supplier_id}")
async def get_supplier_detail(supplier_id: int):
    """협력업체 상세 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, parent_code, business_number, representative,
                   headquarters_address, headquarters_phone, email, notes,
                   is_active, created_at
            FROM suppliers
            WHERE id = ?
        """, (supplier_id,))

        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="협력업체를 찾을 수 없습니다.")

        supplier = {
            "id": row[0],
            "name": row[1] or "",
            "parent_code": row[2] or "",
            "business_number": row[3] or "",
            "representative": row[4] or "",
            "headquarters_address": row[5] or "",
            "headquarters_phone": row[6] or "",
            "email": row[7] or "",
            "notes": row[8] or "",
            "is_active": bool(row[9]),
            "created_at": row[10]
        }

        conn.close()
        return supplier

    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/suppliers/{supplier_id}")
async def update_supplier(supplier_id: int, supplier: SupplierUpdate):
    """협력업체 수정"""
    try:
        print(f"[UPDATE SUPPLIER {supplier_id}] Received data:", supplier.dict())

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 협력업체 존재 확인
        cursor.execute("SELECT id FROM suppliers WHERE id = ?", (supplier_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="협력업체를 찾을 수 없습니다.")

        # 이름 중복 확인 (본인 제외)
        if supplier.name:
            cursor.execute("SELECT id FROM suppliers WHERE name = ? AND id != ?", (supplier.name, supplier_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="이미 존재하는 협력업체 이름입니다.")

        # 사업자번호 중복 확인 (본인 제외)
        if supplier.business_number:
            cursor.execute("SELECT id FROM suppliers WHERE business_number = ? AND id != ?", (supplier.business_number, supplier_id))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="이미 존재하는 사업자번호입니다.")

        # 수정할 필드들 수집
        update_fields = []
        params = []

        for field_name, field_value in supplier.dict(exclude_unset=True).items():
            # 빈 문자열을 None으로 변환
            if field_value == "":
                field_value = None
            update_fields.append(f"{field_name} = ?")
            params.append(field_value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="수정할 데이터가 없습니다.")

        # 업데이트 실행
        params.append(supplier_id)
        update_query = f"""
            UPDATE suppliers
            SET {', '.join(update_fields)}, updated_at = datetime('now')
            WHERE id = ?
        """

        print(f"[UPDATE SUPPLIER {supplier_id}] Query:", update_query)
        print(f"[UPDATE SUPPLIER {supplier_id}] Params:", params)

        cursor.execute(update_query, params)
        affected = cursor.rowcount
        conn.commit()

        # 업데이트 확인
        cursor.execute("SELECT name, parent_code FROM suppliers WHERE id = ?", (supplier_id,))
        updated_data = cursor.fetchone()
        print(f"[UPDATE SUPPLIER {supplier_id}] Affected rows: {affected}")
        print(f"[UPDATE SUPPLIER {supplier_id}] Updated data: {updated_data}")

        conn.close()

        return {
            "success": True,
            "message": f"협력업체가 수정되었습니다. (영향받은 행: {affected})"
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/suppliers/{supplier_id}/activate")
async def activate_supplier(supplier_id: int):
    """협력업체 활성화"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM suppliers WHERE id = ?", (supplier_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="협력업체를 찾을 수 없습니다.")

        cursor.execute("""
            UPDATE suppliers
            SET is_active = 1, updated_at = datetime('now')
            WHERE id = ?
        """, (supplier_id,))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "협력업체가 활성화되었습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/suppliers/{supplier_id}/deactivate")
async def deactivate_supplier(supplier_id: int):
    """협력업체 비활성화"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM suppliers WHERE id = ?", (supplier_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="협력업체를 찾을 수 없습니다.")

        cursor.execute("""
            UPDATE suppliers
            SET is_active = 0, updated_at = datetime('now')
            WHERE id = ?
        """, (supplier_id,))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "협력업체가 비활성화되었습니다."
        }

    except HTTPException:
        raise
    except Exception as e:
        return {"success": False, "error": str(e)}

# HTML 파일 서빙
@app.get("/dashboard.html")
async def get_dashboard():
    """사용자 대시보드 HTML 반환"""
    try:
        with open("dashboard.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="dashboard.html not found")

@app.get("/admin_dashboard.html")
async def get_admin_dashboard():
    """관리자 대시보드 HTML 반환"""
    try:
        with open("admin_dashboard.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="admin_dashboard.html not found")

@app.get("/ingredients_management.html")
async def get_ingredients_management():
    """사용자 식자재 관리 HTML 반환"""
    try:
        with open("ingredients_management.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="ingredients_management.html not found")

@app.get("/meal_plans.html")
async def get_meal_plans():
    """식단 관리 HTML 반환"""
    try:
        with open("meal_plans.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="meal_plans.html not found")

@app.get("/meal_count.html")
async def get_meal_count():
    """식수 관리 HTML 반환"""
    try:
        with open("meal_count.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="meal_count.html not found")

@app.get("/purchase_order.html")
async def get_purchase_order():
    """발주 관리 HTML 반환"""
    try:
        with open("purchase_order.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="purchase_order.html not found")

@app.get("/receipt_statement.html")
async def get_receipt_statement():
    """입고 명세서 HTML 반환"""
    try:
        with open("receipt_statement.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="receipt_statement.html not found")

@app.get("/daily_logs.html")
async def get_daily_logs():
    """각종 일지 HTML 반환"""
    try:
        with open("daily_logs.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="daily_logs.html not found")

@app.get("/preprocessing.html")
async def get_preprocessing():
    """전처리 지시서 HTML 반환"""
    try:
        with open("preprocessing.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="preprocessing.html not found")

@app.get("/preprocessing_management.html")
async def get_preprocessing_management():
    """전처리 관리 HTML 반환"""
    try:
        with open("preprocessing_management.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="preprocessing_management.html not found")

@app.get("/cooking_instruction.html")
async def get_cooking_instruction():
    """조리 지시서 HTML 반환"""
    try:
        with open("cooking_instruction.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="cooking_instruction.html not found")

@app.get("/portioning.html")
async def get_portioning():
    """소분 지시서 HTML 반환"""
    try:
        with open("portioning.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="portioning.html not found")

@app.get("/ordering_management.html")
async def get_ordering_management():
    """발주 관리 시스템 HTML 반환"""
    try:
        with open("ordering_management.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="ordering_management.html not found")

@app.get("/cooking_instruction_management.html")
async def get_cooking_instruction_management():
    """조리 지시서 관리 HTML 반환"""
    try:
        with open("cooking_instruction_management.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="cooking_instruction_management.html not found")

@app.get("/portion_instruction_management.html")
async def get_portion_instruction_management():
    """소분 지시서 관리 HTML 반환"""
    try:
        with open("portion_instruction_management.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="portion_instruction_management.html not found")

@app.get("/receiving_management.html")
async def get_receiving_management():
    """입고명세서 관리 HTML 반환"""
    try:
        with open("receiving_management.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="receiving_management.html not found")

@app.get("/meal_plan_management.html")
async def get_meal_plan_management():
    """기존 식단표 관리 HTML 반환"""
    try:
        with open("meal_plan_management.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="meal_plan_management.html not found")

@app.get("/meal_count_management.html")
async def get_meal_count_management():
    """기존 식수 관리 HTML 반환"""
    try:
        with open("meal_count_management.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="meal_count_management.html not found")

@app.get("/meal_pricing_management_new.html")
async def get_meal_pricing_management():
    """기존 식단가 관리 HTML 반환"""
    try:
        with open("meal_pricing_management_new.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="meal_pricing_management_new.html not found")

# 식단 관리 페이지를 위한 API 엔드포인트
@app.get("/api/recipes")
async def get_recipes():
    """레시피(메뉴) 목록 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # recipes 테이블 확인 및 데이터 조회
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='menu_recipes'")
        table_exists = cursor.fetchone()

        if table_exists:
            cursor.execute("SELECT COUNT(*) FROM menu_recipes")
            count = cursor.fetchone()[0]

            if count > 0:
                cursor.execute("SELECT * FROM menu_recipes")
                recipes = cursor.fetchall()
                conn.close()
                return {"success": True, "recipes": recipes}

        # 테이블이 없거나 비어있으면 임시 데이터 반환
        mock_recipes = [
            {"id": 1, "name": "김치찌개", "category": "국/찌개", "price": 3000},
            {"id": 2, "name": "된장찌개", "category": "국/찌개", "price": 2800},
            {"id": 3, "name": "제육볶음", "category": "주찬", "price": 4500},
            {"id": 4, "name": "불고기", "category": "주찬", "price": 5000},
            {"id": 5, "name": "계란말이", "category": "부찬", "price": 2000},
            {"id": 6, "name": "시금치나물", "category": "부찬", "price": 1500},
            {"id": 7, "name": "김치", "category": "김치", "price": 1000},
            {"id": 8, "name": "쌀밥", "category": "밥", "price": 1000},
        ]
        conn.close()
        return {"success": True, "recipes": mock_recipes}
    except Exception as e:
        return {"success": False, "error": str(e), "recipes": []}

@app.post("/api/search_recipes")
async def search_recipes(request: Request):
    """메뉴 검색 API"""
    try:
        body = await request.json()
        keyword = body.get('keyword', '').strip()
        limit = body.get('limit', 1000)

        # 데이터베이스 연결
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 메뉴 테이블이 있는지 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='menu_recipes'")
        if not cursor.fetchone():
            conn.close()
            return {"success": True, "data": [], "recipes": [], "total": 0, "message": "메뉴 테이블이 없습니다"}

        # 키워드가 있으면 검색, 없으면 전체 조회
        if keyword:
            cursor.execute("""
                SELECT id, menu_name, category, created_by, total_cost, photo_path, created_at
                FROM menu_recipes
                WHERE menu_name LIKE ? AND is_active = 1
                ORDER BY id DESC
                LIMIT ?
            """, (f'%{keyword}%', limit))
        else:
            cursor.execute("""
                SELECT id, menu_name, category, created_by, total_cost, photo_path, created_at
                FROM menu_recipes
                WHERE is_active = 1
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))

        menus = []
        for row in cursor.fetchall():
            menu_data = {
                "id": row[0],
                "name": row[1],  # JavaScript에서 찾는 필드명
                "menu_name": row[1],  # 기존 필드명도 유지
                "recipe_name": row[1],  # 실제 DB 필드명
                "category": row[2] or "미분류",
                "created_by": row[3] or "시스템",
                "creator_organization": "테스트푸드",  # 기본값
                "total_cost": row[4] or 0,
                "photo_path": row[5] or "",
                "image_path": row[5] or "",
                "has_photo": bool(row[5]),
                "created_at": row[6]
            }
            menus.append(menu_data)

        conn.close()

        response_data = {
            "success": True,
            "data": menus,  # JavaScript에서 찾는 필드명
            "recipes": menus,  # 기존 필드명도 유지
            "total": len(menus),
            "message": f"{len(menus)}개 메뉴 검색됨"
        }
        print(f"[DEBUG] 응답 데이터: {response_data}")

        return JSONResponse(content=response_data)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"메뉴 검색 오류: {str(e)}"}
        )

@app.post("/api/admin/report-calculation-issue")
async def report_calculation_issue(request: Request):
    """단위당 단가 계산 실패 패턴 수집 및 재계산 시도"""
    try:
        body = await request.json()
        ingredient_id = body.get('id')
        specification = body.get('specification', '')
        purchase_price = body.get('purchase_price', 0)
        timestamp = body.get('timestamp')

        # 로그 파일에 문제 패턴 저장
        log_file = "calculation_issues.log"
        with open(log_file, "a", encoding='utf-8') as f:
            f.write(f"{timestamp}|{ingredient_id}|{specification}|{purchase_price}\n")

        # 개선된 계산기로 재계산 시도 (모듈 리로드)
        attempted_calculation = {}
        try:
            import importlib
            import improved_unit_price_calculator_debug
            importlib.reload(improved_unit_price_calculator_debug)
            from improved_unit_price_calculator_debug import calculate_unit_price_debug
            result = calculate_unit_price_debug(purchase_price, specification)

            if result['success']:
                attempted_calculation = {
                    'success': True,
                    'unit_price': result['unit_price'],
                    'unit': result['unit'],
                    'total_amount': result['debug_info'].get('total_amount'),
                    'calculation': result['debug_info'].get('calculation')
                }

                # 계산 성공 시 데이터베이스에 업데이트
                try:
                    conn = sqlite3.connect('./backups/daham_meal.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE ingredients
                        SET price_per_unit = ?
                        WHERE id = ?
                    ''', (result['unit_price'], ingredient_id))
                    conn.commit()
                    conn.close()
                except Exception as db_error:
                    print(f"DB 업데이트 실패: {db_error}")
            else:
                attempted_calculation = {
                    'success': False,
                    'error': result['debug_info'].get('error', '패턴 미매칭')
                }
        except Exception as calc_error:
            attempted_calculation = {
                'success': False,
                'error': str(calc_error)
            }

        return {
            "success": True,
            "message": "문제 패턴이 수집되었습니다",
            "ingredient_id": ingredient_id,
            "specification": specification,
            "attempted_calculation": attempted_calculation,
            "report_saved": True
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/meal-counts")
async def get_meal_counts():
    """식수 데이터 조회"""
    try:
        # 임시 데이터 반환
        mock_data = {
            "success": True,
            "data": [
                {"date": "2025-09-16", "breakfast": 100, "lunch": 250, "dinner": 180},
                {"date": "2025-09-15", "breakfast": 95, "lunch": 245, "dinner": 175},
                {"date": "2025-09-14", "breakfast": 102, "lunch": 255, "dinner": 185},
            ]
        }
        return mock_data
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/menu_recipe_management.html")
async def get_menu_recipe_management():
    """메뉴/레시피 관리 HTML 반환"""
    try:
        with open("menu_recipe_management.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="menu_recipe_management.html not found")

@app.get("/menu_recipe_grid.html")
async def get_menu_recipe_grid():
    """메뉴/레시피 그리드 페이지 (엑셀 스타일)"""
    try:
        with open("menu_recipe_grid.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="menu_recipe_grid.html not found")

@app.get("/test_recipe_save.html")
async def get_test_recipe_save():
    """레시피 저장 테스트 페이지"""
    try:
        with open("test_recipe_save.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="test_recipe_save.html not found")

@app.get("/sample%20data/food_sample.xls")
async def get_food_sample():
    """식자재 업로드 템플릿 파일 반환"""
    try:
        return FileResponse("sample data/food_sample.xls",
                           media_type="application/vnd.ms-excel",
                           filename="식자재_업로드_템플릿.xls")
    except:
        raise HTTPException(status_code=404, detail="Template file not found")

@app.get("/sample-data/food-template.xls")
async def get_food_sample_alt():
    """식자재 업로드 템플릿 파일 반환 (대체 경로)"""
    try:
        return FileResponse("sample data/food_sample.xls",
                           media_type="application/vnd.ms-excel",
                           filename="식자재_업로드_템플릿.xls")
    except:
        raise HTTPException(status_code=404, detail="Template file not found")

@app.get("/sample%20data/시스템32.JPG")
async def get_sample_image():
    """샘플 이미지 반환"""
    try:
        return FileResponse("sample data/시스템32.JPG",
                           media_type="image/jpeg")
    except:
        raise HTTPException(status_code=404, detail="Image file not found")

@app.get("/sample-data/system32.jpg")
async def get_sample_image_alt():
    """샘플 이미지 반환 (대체 경로)"""
    try:
        return FileResponse("sample data/시스템32.JPG",
                           media_type="image/jpeg")
    except:
        raise HTTPException(status_code=404, detail="Image file not found")

@app.get("/config.js")
async def get_config():
    """config.js 파일 반환"""
    try:
        return FileResponse("config.js", media_type="application/javascript")
    except:
        raise HTTPException(status_code=404, detail="config.js not found")

@app.get("/")
async def root():
    """루트 경로에서 admin_dashboard.html로 리다이렉트"""
    return HTMLResponse(content="""
        <html>
        <head>
            <meta http-equiv="refresh" content="0; url=/admin_dashboard.html">
        </head>
        <body>
            <p>Redirecting to <a href="/admin_dashboard.html">Admin Dashboard</a>...</p>
        </body>
        </html>
    """)

# ============ 활동 로그 관련 함수 ============
activity_logs = []  # 메모리에 임시 저장 (실제로는 DB 사용 권장)

def log_activity(action_type: str, action_detail: str, user: str = "관리자", entity_type: str = None, entity_id: int = None):
    """활동 로그 기록"""
    global activity_logs
    activity = {
        "id": len(activity_logs) + 1,
        "timestamp": datetime.datetime.now().isoformat(),
        "user": user,
        "action_type": action_type,
        "action_detail": action_detail,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "ip_address": "127.0.0.1"  # 실제로는 request에서 가져와야 함
    }
    activity_logs.insert(0, activity)  # 최신 활동을 앞에 추가

    # 최대 1000개까지만 메모리에 유지
    if len(activity_logs) > 1000:
        activity_logs = activity_logs[:1000]

    return activity

@app.get("/api/admin/activity-logs")
async def get_activity_logs(limit: int = 10, offset: int = 0):
    """최근 활동 로그 조회"""
    try:
        # 페이징 처리
        total_count = len(activity_logs)
        paginated_logs = activity_logs[offset:offset + limit]

        return {
            "success": True,
            "logs": paginated_logs,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/admin/activity-logs")
async def create_activity_log(log_data: dict):
    """활동 로그 생성 (다른 작업에서 호출)"""
    try:
        activity = log_activity(
            action_type=log_data.get("action_type", "기타"),
            action_detail=log_data.get("action_detail", ""),
            user=log_data.get("user", "관리자"),
            entity_type=log_data.get("entity_type"),
            entity_id=log_data.get("entity_id")
        )
        return {"success": True, "log": activity}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========== 누락된 라우트 추가 ==========
@app.get("/receiving_management.html")
async def get_receiving_management():
    """입고명세서 관리 HTML 반환"""
    try:
        with open("receiving_management.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="receiving_management.html not found")

@app.get("/preprocessing_management.html")
async def get_preprocessing_management():
    """전처리지시서 관리 HTML 반환"""
    try:
        with open("preprocessing_management.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="preprocessing_management.html not found")

@app.get("/cooking_instruction.html")
async def get_cooking_instruction():
    """조리지시서 HTML 반환"""
    try:
        with open("cooking_instruction.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="cooking_instruction.html not found")

@app.get("/portioning.html")
async def get_portioning():
    """소분지시서 HTML 반환"""
    try:
        with open("portioning.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="portioning.html not found")

# ========== 레시피 관련 API ==========

@app.post("/api/recipe/save")
async def save_recipe_direct(request: Request, current_user: dict = Depends(require_nutritionist_or_admin)):
    """레시피 저장 API - 직접 처리 (인증 필요)"""
    try:
        # FormData 파싱
        form = await request.form()

        # 기본 정보 추출
        recipe_name = form.get('recipe_name', '').strip()
        category = form.get('category', '').strip()
        cooking_note = form.get('cooking_note', '')
        recipe_id = form.get('recipe_id')  # 수정 시에만 있음

        print(f"[DEBUG] 저장 요청 - 이름: {recipe_name}, 카테고리: {category}, ID: {recipe_id}")

        if not recipe_name:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "메뉴명을 입력해주세요."}
            )

        if not category:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "분류를 선택해주세요."}
            )

        # 재료 정보 파싱
        ingredients_json = form.get('ingredients', '[]')
        try:
            ingredients = json.loads(ingredients_json)
        except:
            ingredients = []

        print(f"[DEBUG] 재료 개수: {len(ingredients)}")

        if not ingredients:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "최소 1개 이상의 식자재를 추가해주세요."}
            )

        # 식자재 코드 유효성 검사
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        for ingredient in ingredients:
            ingredient_code = ingredient.get('ingredient_code', '').strip()
            if not ingredient_code:
                conn.close()
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "모든 재료에 식자재 코드가 입력되어야 합니다."}
                )

            # 식자재 코드 존재 확인
            cursor.execute("SELECT id FROM ingredients WHERE ingredient_code = ?", (ingredient_code,))
            if not cursor.fetchone():
                conn.close()
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": f'식자재 코드 "{ingredient_code}"를 찾을 수 없습니다.'}
                )

        # 총 비용 계산
        total_cost = sum(ingredient.get('amount', 0) for ingredient in ingredients)

        if recipe_id:
            # 기존 메뉴 수정
            print(f"[DEBUG] 기존 메뉴 수정: ID {recipe_id}")

            # 중복 메뉴명 체크 (자기 자신 제외)
            cursor.execute("""
                SELECT COUNT(*) FROM menu_recipes
                WHERE recipe_name = ? AND is_active = 1 AND id != ?
            """, (recipe_name, recipe_id))

            if cursor.fetchone()[0] > 0:
                conn.close()
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": f'"{recipe_name}" 메뉴명이 이미 존재합니다.'}
                )

            # 메뉴 정보 업데이트
            cursor.execute("""
                UPDATE menu_recipes SET
                    recipe_name = ?, category = ?, cooking_note = ?,
                    total_cost = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (recipe_name, category, cooking_note, total_cost, recipe_id))

            # 기존 재료 삭제
            cursor.execute("DELETE FROM menu_recipe_ingredients WHERE recipe_id = ?", (recipe_id,))

            result_recipe_id = int(recipe_id)

        else:
            # 새 메뉴 생성
            print(f"[DEBUG] 새 메뉴 생성")

            # 중복 메뉴명 체크
            cursor.execute("""
                SELECT COUNT(*) FROM menu_recipes
                WHERE recipe_name = ? AND is_active = 1
            """, (recipe_name,))

            if cursor.fetchone()[0] > 0:
                conn.close()
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": f'"{recipe_name}" 메뉴명이 이미 존재합니다.'}
                )

            # 레시피 코드 생성
            import time
            recipe_code = f"RECIPE_{int(time.time())}"

            # 메뉴 생성
            cursor.execute("""
                INSERT INTO menu_recipes (
                    recipe_code, recipe_name, category, cooking_note,
                    total_cost, serving_size, is_active, created_by, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, 1, 1, ?, datetime('now'), datetime('now'))
            """, (recipe_code, recipe_name, category, cooking_note, total_cost, current_user['username']))

            result_recipe_id = cursor.lastrowid

        # 재료 정보 저장
        print(f"[DEBUG] 재료 {len(ingredients)}개 저장 시작")
        for i, ingredient in enumerate(ingredients):
            cursor.execute("""
                INSERT INTO menu_recipe_ingredients (
                    recipe_id, ingredient_code, ingredient_name, specification, unit,
                    delivery_days, selling_price, quantity, amount, supplier_name, sort_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result_recipe_id,
                ingredient.get('ingredient_code', ''),
                ingredient.get('ingredient_name', ''),
                ingredient.get('specification', ''),
                ingredient.get('unit', ''),
                ingredient.get('delivery_days', 0),
                ingredient.get('selling_price', 0),
                ingredient.get('quantity', 0),
                ingredient.get('amount', 0),
                ingredient.get('supplier_name', ''),
                i + 1
            ))

        conn.commit()
        print(f"[DEBUG] 저장 완료: 메뉴 ID {result_recipe_id}")

        # 저장 확인
        cursor.execute("SELECT COUNT(*) FROM menu_recipe_ingredients WHERE recipe_id = ?", (result_recipe_id,))
        ingredient_count = cursor.fetchone()[0]
        print(f"[DEBUG] 저장된 재료 개수: {ingredient_count}")

        conn.close()

        return JSONResponse(
            content={
                "success": True,
                "message": "레시피가 성공적으로 저장되었습니다.",
                "recipe_id": result_recipe_id,
                "recipe_code": recipe_code if not recipe_id else None
            }
        )

    except Exception as e:
        print(f"[ERROR] 레시피 저장 오류: {str(e)}")
        print(f"[ERROR] 스택: {traceback.format_exc()}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"저장 실패: {str(e)}"}
        )

@app.get("/api/recipe/list")
async def get_recipe_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None
):
    """레시피 목록 조회 API"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 조건 구성
        where_conditions = ["r.is_active = 1"]
        params = []

        if category:
            where_conditions.append("r.category = ?")
            params.append(category)

        if search:
            where_conditions.append("r.recipe_name LIKE ?")
            params.append(f"%{search}%")

        where_clause = " AND ".join(where_conditions)

        # 전체 개수
        count_query = f"""
            SELECT COUNT(*) as total
            FROM menu_recipes r
            WHERE {where_clause}
        """
        total = cursor.execute(count_query, params).fetchone()['total']

        # 페이징 데이터
        offset = (page - 1) * per_page
        params.extend([per_page, offset])

        query = f"""
            SELECT
                r.id, r.recipe_code, r.recipe_name, r.category,
                r.food_color, r.total_cost, r.image_thumbnail,
                r.created_at,
                COUNT(ri.id) as ingredient_count
            FROM menu_recipes r
            LEFT JOIN menu_recipe_ingredients ri ON r.id = ri.recipe_id
            WHERE {where_clause}
            GROUP BY r.id
            ORDER BY r.created_at DESC
            LIMIT ? OFFSET ?
        """

        recipes = cursor.execute(query, params).fetchall()

        return {
            'success': True,
            'recipes': [dict(row) for row in recipes],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }

    except Exception as e:
        print(f"레시피 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"레시피 목록 조회 실패: {str(e)}")
    finally:
        conn.close()

@app.get("/api/recipe/{recipe_id}")
async def get_recipe_detail(recipe_id: int):
    """레시피 상세 조회 API"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 레시피 기본 정보
        recipe = cursor.execute("""
            SELECT * FROM menu_recipes
            WHERE id = ? AND is_active = 1
        """, (recipe_id,)).fetchone()

        if not recipe:
            raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다.")

        # 재료 목록
        ingredients = cursor.execute("""
            SELECT * FROM menu_recipe_ingredients
            WHERE recipe_id = ?
            ORDER BY sort_order
        """, (recipe_id,)).fetchall()

        return {
            'success': True,
            'recipe': dict(recipe),
            'ingredients': [dict(row) for row in ingredients]
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"레시피 상세 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"레시피 상세 조회 실패: {str(e)}")
    finally:
        conn.close()

# =============================================================================
# 관리자용 메뉴/레시피 API 엔드포인트
# =============================================================================

@app.get("/api/admin/menu-recipes")
async def get_admin_menu_recipes(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    current_user: dict = Depends(require_nutritionist_or_admin)
):
    """메뉴/레시피 목록 조회 (인증 필요)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # WHERE 조건 구성
        conditions = ["r.is_active = 1"]
        params = []

        # 권한별 필터링
        if current_user['role'] != 'admin':
            # 관리자가 아닌 경우 자신의 메뉴만 조회
            conditions.append("r.created_by = ?")
            params.append(current_user['username'])

        if search:
            conditions.append("(r.recipe_name LIKE ? OR r.cooking_note LIKE ?)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param])

        if category:
            conditions.append("r.category = ?")
            params.append(category)

        where_clause = " AND ".join(conditions)

        # 총 개수 조회
        count_query = f"""
            SELECT COUNT(DISTINCT r.id)
            FROM menu_recipes r
            WHERE {where_clause}
        """
        total = cursor.execute(count_query, params).fetchone()[0]

        # 메뉴/레시피 목록 조회
        offset = (page - 1) * limit
        query = f"""
            SELECT
                r.id,
                r.recipe_name as name,
                r.category,
                r.cooking_note as description,
                r.serving_size as servings,
                r.total_cost,
                r.created_at,
                r.updated_at,
                r.image_path,
                r.image_thumbnail,
                COUNT(i.id) as ingredient_count
            FROM menu_recipes r
            LEFT JOIN menu_recipe_ingredients i ON r.id = i.recipe_id
            WHERE {where_clause}
            GROUP BY r.id
            ORDER BY r.updated_at DESC
            LIMIT ? OFFSET ?
        """

        params.extend([limit, offset])
        recipes = cursor.execute(query, params).fetchall()

        return {
            'success': True,
            'data': {
                'recipes': [dict(row) for row in recipes],
                'pagination': {
                    'page': page,
                    'limit': limit,
                    'total': total,
                    'total_pages': (total + limit - 1) // limit
                }
            }
        }

    except Exception as e:
        print(f"관리자 메뉴/레시피 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메뉴/레시피 목록 조회 실패: {str(e)}")
    finally:
        conn.close()

@app.get("/api/admin/menu-recipes/categories")
async def get_menu_categories():
    """메뉴 카테고리 목록 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        categories = cursor.execute("""
            SELECT DISTINCT category, COUNT(*) as count
            FROM menu_recipes
            WHERE is_active = 1 AND category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY category
        """).fetchall()

        return {
            'success': True,
            'data': {
                'categories': [{'name': row[0], 'count': row[1]} for row in categories]
            }
        }

    except Exception as e:
        print(f"메뉴 카테고리 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"카테고리 조회 실패: {str(e)}")
    finally:
        conn.close()

@app.get("/api/admin/menu-recipes/{recipe_id}")
async def get_admin_menu_recipe_detail(recipe_id: int):
    """관리자용 메뉴/레시피 상세 조회"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 레시피 기본 정보
        recipe = cursor.execute("""
            SELECT * FROM menu_recipes
            WHERE id = ?
        """, (recipe_id,)).fetchone()

        if not recipe:
            raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다.")

        # 재료 목록
        ingredients = cursor.execute("""
            SELECT * FROM menu_recipe_ingredients
            WHERE recipe_id = ?
            ORDER BY sort_order
        """, (recipe_id,)).fetchall()

        return {
            'success': True,
            'data': {
                'recipe': dict(recipe),
                'ingredients': [dict(row) for row in ingredients]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"관리자 메뉴/레시피 상세 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메뉴/레시피 상세 조회 실패: {str(e)}")
    finally:
        conn.close()

@app.post("/api/admin/menu-recipes")
async def create_admin_menu_recipe(recipe_data: dict):
    """관리자용 메뉴/레시피 생성"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 중복 메뉴명 체크
        menu_name = recipe_data.get('name', '').strip()
        if not menu_name:
            return {
                'success': False,
                'error': '메뉴명은 필수입니다.'
            }

        cursor.execute("""
            SELECT COUNT(*) FROM menu_recipes
            WHERE recipe_name = ? AND is_active = 1
        """, (menu_name,))

        if cursor.fetchone()[0] > 0:
            return {
                'success': False,
                'error': f'"{menu_name}" 메뉴명이 이미 존재합니다. 다른 이름을 사용해주세요.'
            }

        # 레시피 코드 생성
        import datetime
        recipe_code = f"RCP_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 레시피 기본 정보 삽입
        recipe_insert = """
            INSERT INTO menu_recipes (
                recipe_code, recipe_name, category, cooking_note,
                serving_size, total_cost, image_path,
                created_at, updated_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 1)
        """

        cursor.execute(recipe_insert, (
            recipe_code,
            recipe_data.get('name'),
            recipe_data.get('category'),
            recipe_data.get('description', ''),
            recipe_data.get('servings', 1),
            recipe_data.get('total_cost', 0),
            recipe_data.get('image_path', '')
        ))

        recipe_id = cursor.lastrowid

        # 재료 정보 삽입
        ingredients = recipe_data.get('ingredients', [])
        if not ingredients:
            return {
                'success': False,
                'error': '메뉴에는 최소 1개 이상의 식자재가 필요합니다.'
            }

        # 식자재 코드 검증
        for i, ingredient in enumerate(ingredients):
            ingredient_code = ingredient.get('ingredient_code', '').strip()
            ingredient_name = ingredient.get('ingredient_name', '').strip()

            if not ingredient_code:
                return {
                    'success': False,
                    'error': f'{i+1}번째 재료: 식자재 코드는 필수입니다.'
                }

            if not ingredient_name:
                return {
                    'success': False,
                    'error': f'{i+1}번째 재료: 식자재명은 필수입니다.'
                }

            # ingredients 테이블에서 해당 코드가 존재하는지 확인
            cursor.execute("""
                SELECT COUNT(*) FROM ingredients
                WHERE ingredient_code = ? AND supplier_name IS NOT NULL
            """, (ingredient_code,))

            if cursor.fetchone()[0] == 0:
                return {
                    'success': False,
                    'error': f'{i+1}번째 재료: 식자재 코드 "{ingredient_code}"가 시스템에 등록되지 않았습니다.'
                }

        # 재료 정보 삽입
        ingredient_insert = """
            INSERT INTO menu_recipe_ingredients (
                recipe_id, ingredient_code, ingredient_name, quantity, unit,
                amount, supplier_name, specification, sort_order
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        for i, ingredient in enumerate(ingredients):
            cursor.execute(ingredient_insert, (
                recipe_id,
                ingredient.get('ingredient_code', ''),
                ingredient.get('ingredient_name', ''),
                ingredient.get('quantity', 0),
                ingredient.get('unit', ''),
                ingredient.get('amount', 0),
                ingredient.get('supplier_name', ''),
                ingredient.get('specification', ''),
                i + 1
            ))

        conn.commit()

        return {
            'success': True,
            'data': {'recipe_id': recipe_id},
            'message': '메뉴/레시피가 성공적으로 생성되었습니다.'
        }

    except Exception as e:
        conn.rollback()
        print(f"관리자 메뉴/레시피 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메뉴/레시피 생성 실패: {str(e)}")
    finally:
        conn.close()

@app.put("/api/admin/menu-recipes/{recipe_id}")
async def update_admin_menu_recipe(recipe_id: int, recipe_data: dict):
    """관리자용 메뉴/레시피 수정"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 레시피 존재 확인
        existing = cursor.execute("SELECT id FROM menu_recipes WHERE id = ?", (recipe_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다.")

        # 중복 메뉴명 체크 (수정 시 자기 자신 제외)
        menu_name = recipe_data.get('name', '').strip()
        if menu_name:
            cursor.execute("""
                SELECT COUNT(*) FROM menu_recipes
                WHERE recipe_name = ? AND is_active = 1 AND id != ?
            """, (menu_name, recipe_id))

            if cursor.fetchone()[0] > 0:
                return {
                    'success': False,
                    'error': f'"{menu_name}" 메뉴명이 이미 존재합니다. 다른 이름을 사용해주세요.'
                }

        # 레시피 기본 정보 수정
        recipe_update = """
            UPDATE menu_recipes SET
                recipe_name = ?, category = ?, cooking_note = ?,
                serving_size = ?, total_cost = ?, image_path = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """

        cursor.execute(recipe_update, (
            recipe_data.get('name'),
            recipe_data.get('category'),
            recipe_data.get('description', ''),
            recipe_data.get('servings', 1),
            recipe_data.get('total_cost', 0),
            recipe_data.get('image_path', ''),
            recipe_id
        ))

        # 기존 재료 삭제
        cursor.execute("DELETE FROM menu_recipe_ingredients WHERE recipe_id = ?", (recipe_id,))

        # 재료 유효성 검사
        ingredients = recipe_data.get('ingredients', [])
        if not ingredients:
            return {
                'success': False,
                'error': '메뉴 수정을 위해서는 최소 1개 이상의 재료가 필요합니다.'
            }

        # 식자재 코드 유효성 검사
        for ingredient in ingredients:
            ingredient_code = ingredient.get('ingredient_code', '').strip()
            if not ingredient_code:
                return {
                    'success': False,
                    'error': '모든 재료에 식자재 코드가 입력되어야 합니다.'
                }

            # 식자재 코드가 실제 DB에 존재하는지 확인
            cursor.execute("""
                SELECT id FROM ingredients WHERE ingredient_code = ?
            """, (ingredient_code,))

            if not cursor.fetchone():
                return {
                    'success': False,
                    'error': f'식자재 코드 "{ingredient_code}"를 찾을 수 없습니다. 올바른 식자재를 선택해주세요.'
                }

        # 새 재료 정보 삽입
        if ingredients:
            ingredient_insert = """
                INSERT INTO menu_recipe_ingredients (
                    recipe_id, ingredient_name, quantity, unit,
                    amount, supplier_name, specification, sort_order, ingredient_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """

            for i, ingredient in enumerate(ingredients):
                cursor.execute(ingredient_insert, (
                    recipe_id,
                    ingredient.get('ingredient_name', ''),
                    ingredient.get('quantity', 0),
                    ingredient.get('unit', ''),
                    ingredient.get('amount', 0),
                    ingredient.get('supplier_name', ''),
                    ingredient.get('specification', ''),
                    i + 1,
                    ingredient.get('ingredient_code', '')
                ))

        conn.commit()

        return {
            'success': True,
            'message': '메뉴/레시피가 성공적으로 수정되었습니다.'
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        print(f"관리자 메뉴/레시피 수정 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메뉴/레시피 수정 실패: {str(e)}")
    finally:
        conn.close()

@app.delete("/api/admin/menu-recipes/{recipe_id}")
async def delete_admin_menu_recipe(recipe_id: int):
    """관리자용 메뉴/레시피 삭제 (소프트 삭제)"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 레시피 존재 확인
        existing = cursor.execute("SELECT id FROM menu_recipes WHERE id = ?", (recipe_id,)).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다.")

        # 소프트 삭제 (is_active = 0)
        cursor.execute("""
            UPDATE menu_recipes
            SET is_active = 0, updated_at = datetime('now')
            WHERE id = ?
        """, (recipe_id,))

        conn.commit()

        return {
            'success': True,
            'message': '메뉴/레시피가 성공적으로 삭제되었습니다.'
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        print(f"관리자 메뉴/레시피 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"메뉴/레시피 삭제 실패: {str(e)}")
    finally:
        conn.close()

# ========== 협력업체 대시보드 관련 API ==========

@app.get("/supplier_dashboard.html")
async def serve_supplier_dashboard():
    """협력업체 대시보드 페이지 제공"""
    return FileResponse("supplier_dashboard.html")

@app.get("/sample data/{file_name}")
async def serve_sample_data(file_name: str):
    """샘플 데이터 파일 제공"""
    import os
    file_path = os.path.join("sample data", file_name)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다")

@app.get("/api/supplier/dashboard-stats")
async def get_supplier_dashboard_stats():
    """협력업체 대시보드 통계 데이터"""
    try:
        # 임시 통계 데이터 (실제 구현 시 DB에서 조회)
        import random
        stats = {
            "today_orders": random.randint(5, 25),
            "pending_orders": random.randint(3, 18),
            "weekly_confirmed": random.randint(20, 70),
            "monthly_total": f"{random.randint(200, 700)}만원"
        }

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/supplier/orders")
async def get_supplier_orders(status: str = None, date: str = None):
    """협력업체 발주 목록 조회"""
    try:

        # 임시 발주 데이터 생성 (실제 구현 시 DB에서 조회)
        import random
        from datetime import datetime, timedelta

        sites = ['테스트푸드 본사', '서울지점', '부산지점', '대구지점']
        statuses = ['pending', 'confirmed', 'rejected']
        status_names = {'pending': '처리대기', 'confirmed': '확정', 'rejected': '반려'}

        orders = []
        for i in range(1, 16):
            order_date = datetime.now() - timedelta(days=random.randint(0, 7))
            order_status = random.choice(statuses)

            order = {
                "id": f"ORD-{str(i).zfill(4)}",
                "site": random.choice(sites),
                "date": order_date.strftime('%Y-%m-%d'),
                "items": random.randint(5, 25),
                "amount": f"{random.randint(100, 600)}만원",
                "status": order_status,
                "status_name": status_names[order_status],
                "supplier_code": supplier_code
            }
            orders.append(order)

        # 필터링
        if status:
            orders = [o for o in orders if o['status'] == status]
        if date:
            orders = [o for o in orders if o['date'] == date]

        # 날짜순 정렬
        orders.sort(key=lambda x: x['date'], reverse=True)

        return {
            "success": True,
            "orders": orders
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/supplier/orders/{order_id}/confirm")
async def confirm_supplier_order(order_id: str):
    """협력업체 발주 확정"""
    try:
        # 실제 구현 시 DB 업데이트
        # 여기서는 임시로 성공 응답

        return {
            "success": True,
            "message": f"발주 {order_id}가 확정되었습니다."
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/supplier/orders/{order_id}/reject")
async def reject_supplier_order(order_id: str, reason_data: dict):
    """협력업체 발주 반려"""
    try:
        reason = reason_data.get('reason', '')

        # 실제 구현 시 DB 업데이트
        # 여기서는 임시로 성공 응답

        return {
            "success": True,
            "message": f"발주 {order_id}가 반려되었습니다.",
            "reason": reason
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/supplier/orders/{order_id}/detail")
async def get_supplier_order_detail(order_id: str):
    """협력업체 발주 상세 조회"""
    try:

        # 임시 상세 데이터 (실제 구현 시 DB에서 조회)
        detail = {
            "id": order_id,
            "site": "테스트푸드 본사",
            "date": "2025-09-19",
            "status": "pending",
            "status_name": "처리대기",
            "items": [
                {"name": "쌀", "quantity": "10kg", "unit_price": "2,500원", "total": "25,000원"},
                {"name": "김치", "quantity": "5kg", "unit_price": "8,000원", "total": "40,000원"},
                {"name": "돼지고기", "quantity": "3kg", "unit_price": "15,000원", "total": "45,000원"}
            ],
            "total_amount": "110,000원",
            "notes": "급한 주문입니다. 빠른 처리 부탁드립니다."
        }

        return {
            "success": True,
            "detail": detail
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    import os

    # 환경 변수에서 포트 읽기, 기본값은 80
    port = int(os.getenv("API_PORT", "80"))
    host = os.getenv("API_HOST", "0.0.0.0")  # 외부 접속 허용

    print(f"API 서버 시작: {host}:{port}")
    uvicorn.run(app, host=host, port=port)