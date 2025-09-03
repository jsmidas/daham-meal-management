from fastapi import FastAPI, HTTPException, Depends, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
import os
import json
import hashlib
import secrets
from datetime import datetime, date, timedelta

# 로컬 임포트
from models import (
    Base, DietPlan, Menu, MenuItem, Recipe, Ingredient, Supplier, Customer, User, CustomerMenu,
    MealCount, MealCountTimeline, MealCountTemplate,
    PurchaseOrder, PurchaseOrderItem, ReceivingRecord, ReceivingItem,
    PreprocessingMaster, PreprocessingInstruction, PreprocessingInstructionItem,
    CustomerSupplierMapping, OrderTypeEnum, ReceivingStatusEnum, MealPricing
)
from business_logic import MenuCalculator, NutritionCalculator, CostAnalyzer

# FastAPI 앱 생성
app = FastAPI(
    title="Daham Menu Manager API",
    description="다함식단관리 시스템 API",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="."), name="static")
app.mount("/templates", StaticFiles(directory="templates"), name="templates")

@app.get("/")
async def serve_homepage():
    return FileResponse("menu_recipe_management.html")

@app.get("/meal-plan")
async def serve_meal_plan():
    return FileResponse("meal_plan_management.html")

@app.get("/meal-count")
async def serve_meal_count():
    return FileResponse("meal_count_timeline.html")

@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse("dashboard.html")

@app.get("/ordering")
async def serve_ordering():
    return FileResponse("ordering_management.html")

@app.get("/receiving")
async def serve_receiving():
    return FileResponse("receiving_management.html")

@app.get("/preprocessing")
async def serve_preprocessing():
    """전처리 지시서 관리 페이지"""
    return FileResponse("preprocessing_management.html")

@app.get("/preprocessing-demo")
async def serve_preprocessing_demo():
    """전처리 지시서 데모 페이지"""
    return FileResponse("preprocessing_demo_sep2.html")


# 데이터베이스 연결 - 새로 생성한 SQLite 데이터베이스 사용
DATABASE_URL = "sqlite:///./daham_meal.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
print("Using SQLite database: daham_meal.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 데이터베이스 세션 의존성 수정
def get_db():
    db = SessionLocal()
    try:
        # 인코딩 설정 제거 - 연결 시점에 문제 발생
        # db.execute(text("SET client_encoding TO 'UTF8'"))
        yield db
    finally:
        db.close()

# ==============================================================================
# 인증 및 권한 관리 시스템
# ==============================================================================

# 간단한 메모리 기반 세션 저장소 (실제 운영에서는 Redis 등 사용)
active_sessions = {}

# Pydantic 모델들
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    redirect: Optional[str] = None
    session_token: Optional[str] = None
    user: Optional[dict] = None

# 세션 관리 클래스
class SessionManager:
    @staticmethod
    def create_session(user_id: int, username: str, role: str) -> str:
        """새 세션 생성"""
        session_token = secrets.token_urlsafe(32)
        session_data = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=8)  # 8시간 후 만료
        }
        active_sessions[session_token] = session_data
        return session_token
    
    @staticmethod
    def get_session(session_token: str) -> Optional[dict]:
        """세션 정보 조회"""
        if session_token not in active_sessions:
            return None
        
        session_data = active_sessions[session_token]
        
        # 만료 체크
        if datetime.now() > session_data['expires_at']:
            del active_sessions[session_token]
            return None
        
        # 활동 시간 갱신
        session_data['last_activity'] = datetime.now()
        return session_data
    
    @staticmethod
    def delete_session(session_token: str):
        """세션 삭제"""
        if session_token in active_sessions:
            del active_sessions[session_token]

# 비밀번호 해싱
def hash_password(password: str) -> str:
    """비밀번호 해시화"""
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), b'salt', 100000).hex()

def verify_password(password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return hash_password(password) == hashed_password

# 의존성: 현재 사용자 정보 가져오기
def get_current_user(request: Request):
    """현재 로그인한 사용자 정보 반환"""
    session_token = request.cookies.get('session_token')
    print(f"[DEBUG] Session token from cookie: {session_token}")
    if not session_token:
        print("[DEBUG] No session token found")
        return None
    
    session_data = SessionManager.get_session(session_token)
    print(f"[DEBUG] Session data from SessionManager: {session_data}")
    if not session_data:
        print("[DEBUG] No session data found")
        return None
        
    return session_data

# 의존성: 관리자 권한 확인
def require_admin(request: Request):
    """관리자 권한이 필요한 엔드포인트용"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")
    
    if user['role'] not in ['admin', 'super_admin']:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다")
    
    return user

# ==============================================================================
# 인증 관련 라우트
# ==============================================================================

@app.get("/login")
async def serve_login_page():
    """로그인 페이지 서빙"""
    return FileResponse("login.html")

@app.post("/api/auth/login")
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
        
        # 비밀번호 확인 (실제로는 해시 비교를 해야 하지만, 데모용으로 단순화)
        demo_passwords = {
            'admin': 'admin123',
            'nutritionist': 'nutri123'
        }
        
        expected_password = demo_passwords.get(login_data.username)
        if not expected_password or login_data.password != expected_password:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "비밀번호가 올바르지 않습니다."}
            )
        
        # 세션 생성 - role을 영문으로 매핑
        role_mapping = {
            'admin': 'admin',
            'nutritionist': 'nutritionist', 
            'manager': 'manager'
        }
        # role이 한글로 저장된 경우를 대비해 username으로 role 결정
        if user.username == 'admin':
            role_for_session = 'admin'
        elif user.username == 'nutritionist':
            role_for_session = 'nutritionist'
        else:
            role_for_session = str(user.role.value) if hasattr(user.role, 'value') else str(user.role)
            
        print(f"[DEBUG] Creating session for user: {user.username}, role: {role_for_session}")
        session_token = SessionManager.create_session(
            user_id=user.id,
            username=user.username, 
            role=role_for_session
        )
        print(f"[DEBUG] Session created: {session_token}")
        print(f"[DEBUG] All sessions after creation: {active_sessions}")
        
        # 응답 생성
        response_data = {
            "success": True,
            "message": "로그인 성공",
            "redirect": "/admin",
            "user": {
                'id': user.id,
                'username': user.username,
                'role': user.role.value,
                'department': user.department,
                'position': user.position
            }
        }
        
        response = JSONResponse(content=response_data)
        
        # 세션 토큰을 쿠키로 설정 (8시간 만료, HttpOnly, Secure)
        response.set_cookie(
            key="session_token",
            value=session_token,
            max_age=8*60*60,  # 8시간
            httponly=True,
            secure=False,  # 개발환경에서는 False, 운영에서는 True
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "message": f"로그인 처리 중 오류가 발생했습니다: {str(e)}"}
        )

@app.post("/api/auth/logout")
async def logout(request: Request):
    """로그아웃 API"""
    session_token = request.cookies.get('session_token')
    if session_token:
        SessionManager.delete_session(session_token)
    
    response_data = {"success": True, "message": "로그아웃되었습니다.", "redirect": "/login"}
    response = JSONResponse(content=response_data)
    
    # 세션 쿠키 삭제
    response.delete_cookie("session_token")
    
    return response

@app.get("/admin")
async def serve_admin_dashboard(request: Request):
    """관리자 대시보드 페이지 서빙 (로그인 필요)"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    print(f"[DEBUG] User role check: '{user['role']}' - type: {type(user['role'])}")
    # 한글 인코딩 문제로 인해 영문 role로 변경
    valid_roles = ['admin', 'nutritionist', 'manager', '관리자', '영양사', '매니저']
    if user['role'] not in valid_roles:
        print(f"[DEBUG] Role '{user['role']}' not in valid roles: {valid_roles}")
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    return FileResponse("admin_dashboard.html")

@app.get("/admin/ingredient-upload-test")
async def test_ingredient_route():
    """테스트 라우트"""
    return JSONResponse({"status": "working", "route": "ingredient-upload-test"})

@app.get("/admin/simple-test")  
async def simple_test():
    """매우 간단한 테스트"""
    return {"message": "simple test works"}

@app.get("/supplier-management")
async def serve_supplier_management(request: Request):
    """식자재 업체관리 페이지 서빙 (admin 권한 필요)"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # 최고관리자 권한 확인 (업체관리는 admin만 접근 가능)
    if user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="최고관리자(admin) 권한이 필요합니다.")
    
    return FileResponse("supplier_management.html")

@app.get("/suppliers")
async def serve_suppliers_short(request: Request):
    """식자재 업체관리 페이지 서빙 (admin 권한 필요)"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # 최고관리자 권한 확인 (업체관리는 admin만 접근 가능)
    if user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="최고관리자(admin) 권한이 필요합니다.")
    
    return FileResponse("supplier_management.html")

@app.get("/admin/suppliers")
async def serve_admin_suppliers(request: Request):
    """관리자 업체관리 페이지 서빙 (관리자 권한 필요)"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # 관리자 권한 확인 (업체관리는 관리자급 이상 접근 가능)
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    return FileResponse("supplier_management.html")

@app.get("/admin/business-locations")
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

@app.get("/admin/ingredient-upload")
async def serve_ingredient_upload_page(request: Request):
    """식자재 파일 업로드 페이지"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    return FileResponse("ingredient_file_upload.html")

@app.get("/ingredients-management")
async def serve_ingredients_management(request: Request):
    """식자재관리 페이지 서빙 (로그인 필요)"""
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=302)
    
    # 관리자 권한 확인
    valid_roles = ['admin', 'nutritionist', 'manager', '관리자', '영양사', '매니저']
    if user['role'] not in valid_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    return FileResponse("ingredients_management.html")

# 검색된 메뉴 원가 계산 API
@app.post("/api/calculate_menu_costs")
async def calculate_menu_costs(request: Request, db: Session = Depends(get_db)):
    """검색된 메뉴들에 대해서만 원가 계산"""
    try:
        # 바이트 데이터 직접 읽어서 디코딩 문제 해결
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        body = json.loads(body_str)
        menu_names = body.get('menu_names', [])
        if not menu_names:
            return {}
        
        # IN 절에 사용할 플레이스홀더 생성
        placeholders = ','.join([':name' + str(i) for i in range(len(menu_names))])
        params = {f'name{i}': name for i, name in enumerate(menu_names)}
        
        # 우선 간단한 쿼리로 메뉴 존재 여부만 확인
        cost_query = f"""
        SELECT 
            r.name,
            500 as total_cost
        FROM recipes r
        WHERE r.name IN ({placeholders})
        """
        
        print(f"Executing query with menu_names: {menu_names}")
        
        result = db.execute(text(cost_query), params)
        results = result.fetchall()
        
        print(f"Query results: {results}")
        
        # 결과를 딕셔너리로 변환
        costs = {row[0]: int(row[1]) for row in results}
        
        # 검색되었지만 원가 정보가 없는 메뉴들은 임시로 800원 설정 (테스트용)
        for menu_name in menu_names:
            if menu_name not in costs:
                costs[menu_name] = 800
                
        print(f"Final costs: {costs}")
        return costs
        
    except Exception as e:
        print(f"Error in calculate_menu_costs: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

# 메뉴별 발주 가능성 체크 API
class MenuOrderabilityRequest(BaseModel):
    menu_names: List[str]

@app.post("/api/check_menu_orderability")
async def check_menu_orderability(request: MenuOrderabilityRequest, db: Session = Depends(get_db)):
    """메뉴별 발주 가능성 체크"""
    try:
        orderability_status = {}
        
        for menu_name in request.menu_names:
            # 임시 로직: 실제로는 레시피 > 식재료 > 업체 단가표의 게시유무를 확인해야 함
            # 현재는 샘플 로직으로 일부 메뉴를 발주불가로 설정
            non_orderable_keywords = ['갈비', '한우', '전복', '참치', '연어', '새우']
            
            is_orderable = True
            non_orderable_ingredients = []
            
            for keyword in non_orderable_keywords:
                if keyword in menu_name:
                    is_orderable = False
                    non_orderable_ingredients.append(f"{keyword} 관련 식재료")
                    break
            
            orderability_status[menu_name] = {
                "is_orderable": is_orderable,
                "non_orderable_ingredients": non_orderable_ingredients,
                "message": "정상 발주 가능" if is_orderable else "일부 식재료 발주 불가"
            }
        
        return orderability_status
        
    except Exception as e:
        print(f"메뉴 발주 가능성 체크 실패: {e}")
        # 오류 시 모든 메뉴를 발주 가능으로 반환
        return {menu_name: {
            "is_orderable": True, 
            "non_orderable_ingredients": [], 
            "message": "정상 발주 가능"
        } for menu_name in request.menu_names}

# 식재료 일괄 대체 API
class IngredientBulkReplaceRequest(BaseModel):
    old_ingredient_code: str
    new_ingredient_code: str
    new_ingredient_name: str
    reason: str = "발주불가로 인한 대체"

@app.post("/api/preview_bulk_replace")
async def preview_bulk_replace(request: IngredientBulkReplaceRequest, db: Session = Depends(get_db)):
    """식재료 일괄 대체 미리보기 - 영향받는 레시피 목록 조회"""
    try:
        # 기존 식재료가 사용된 레시피 찾기
        recipe_query = """
        SELECT DISTINCT 
            r.id as recipe_id,
            r.name as recipe_name,
            ri.quantity,
            ri.unit
        FROM recipes r
        JOIN recipe_ingredients ri ON r.id = ri.recipe_id
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE i.code = :old_code
        ORDER BY r.name
        """
        
        affected_recipes = db.execute(text(recipe_query), {"old_code": request.old_ingredient_code}).fetchall()
        
        if not affected_recipes:
            return {
                "success": True,
                "message": f"식재료 코드 '{request.old_ingredient_code}'를 사용하는 레시피가 없습니다.",
                "affected_count": 0,
                "affected_recipes": []
            }
        
        # 결과 포맷팅
        recipe_list = []
        for recipe in affected_recipes:
            recipe_list.append({
                "recipe_id": recipe.recipe_id,
                "recipe_name": recipe.recipe_name,
                "amount": float(recipe.quantity) if recipe.quantity else 0,
                "unit": recipe.unit or ""
            })
        
        return {
            "success": True,
            "message": f"총 {len(recipe_list)}개 레시피에서 해당 식재료를 사용하고 있습니다.",
            "affected_count": len(recipe_list),
            "affected_recipes": recipe_list,
            "old_ingredient_code": request.old_ingredient_code,
            "new_ingredient_code": request.new_ingredient_code,
            "new_ingredient_name": request.new_ingredient_name
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"미리보기 조회 중 오류 발생: {str(e)}",
            "affected_count": 0,
            "affected_recipes": []
        }

@app.post("/api/bulk_replace_ingredient")
async def bulk_replace_ingredient(request: IngredientBulkReplaceRequest, db: Session = Depends(get_db)):
    """특정 식재료를 모든 레시피에서 일괄 대체"""
    try:
        # 1. 기존 식재료가 사용된 레시피 찾기
        recipe_query = """
        SELECT DISTINCT 
            r.id as recipe_id,
            r.name as recipe_name,
            ri.quantity,
            ri.unit
        FROM recipes r
        JOIN recipe_ingredients ri ON r.id = ri.recipe_id
        JOIN ingredients i ON ri.ingredient_id = i.id
        WHERE i.code = :old_code
        """
        
        affected_recipes = db.execute(text(recipe_query), {"old_code": request.old_ingredient_code}).fetchall()
        
        if not affected_recipes:
            return {
                "success": False,
                "message": f"식재료 코드 '{request.old_ingredient_code}'를 사용하는 레시피를 찾을 수 없습니다.",
                "affected_count": 0,
                "affected_recipes": []
            }
        
        # 2. 새 식재료가 이미 존재하는지 확인, 없으면 생성
        ingredient_check = db.execute(text("""
            SELECT id FROM ingredients WHERE code = :new_code
        """), {"new_code": request.new_ingredient_code}).fetchone()
        
        if not ingredient_check:
            # 새 식재료 생성
            db.execute(text("""
                INSERT INTO ingredients (code, name, base_unit, created_at)
                VALUES (:code, :name, 'kg', NOW())
            """), {
                "code": request.new_ingredient_code,
                "name": request.new_ingredient_name
            })
            db.commit()
            
            new_ingredient_id = db.execute(text("""
                SELECT id FROM ingredients WHERE code = :new_code
            """), {"new_code": request.new_ingredient_code}).fetchone()[0]
        else:
            new_ingredient_id = ingredient_check[0]
        
        # 3. 기존 식재료 ID 찾기
        old_ingredient_id = db.execute(text("""
            SELECT id FROM ingredients WHERE code = :old_code
        """), {"old_code": request.old_ingredient_code}).fetchone()[0]
        
        # 4. 모든 레시피에서 식재료 대체
        replace_count = 0
        for recipe in affected_recipes:
            # 기존 레시피 재료 업데이트
            db.execute(text("""
                UPDATE recipe_ingredients 
                SET ingredient_id = :new_id,
                    updated_at = NOW()
                WHERE recipe_id = :recipe_id 
                AND ingredient_id = :old_id
            """), {
                "new_id": new_ingredient_id,
                "recipe_id": recipe["recipe_id"],
                "old_id": old_ingredient_id
            })
            replace_count += 1
        
        db.commit()
        
        # 5. 변경 로그 기록
        db.execute(text("""
            INSERT INTO ingredient_change_log (
                old_ingredient_code, 
                new_ingredient_code, 
                affected_recipe_count, 
                change_reason, 
                created_at
            ) VALUES (:old_code, :new_code, :count, :reason, NOW())
        """), {
            "old_code": request.old_ingredient_code,
            "new_code": request.new_ingredient_code,
            "count": replace_count,
            "reason": request.reason
        })
        db.commit()
        
        return {
            "success": True,
            "message": f"식재료 일괄 대체 완료: {replace_count}개 레시피에서 변경됨",
            "affected_count": replace_count,
            "affected_recipes": [{"id": r["recipe_id"], "name": r["recipe_name"]} for r in affected_recipes],
            "old_ingredient": request.old_ingredient_code,
            "new_ingredient": request.new_ingredient_code
        }
        
    except Exception as e:
        db.rollback()
        print(f"식재료 일괄 대체 실패: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"식재료 일괄 대체 중 오류 발생: {str(e)}",
            "affected_count": 0,
            "affected_recipes": []
        }

# 메뉴별 식재료 정보 조회 API
@app.get("/api/menu_ingredients/{menu_name}")
async def get_menu_ingredients(menu_name: str, db: Session = Depends(get_db)):
    """특정 메뉴의 식재료 목록 조회"""
    try:
        # 메뉴의 식재료 정보 조회
        ingredient_query = """
        SELECT 
            i.name as ingredient_name,
            i.id as ingredient_code,
            ri.quantity,
            i.base_unit,
            s.name as supplier_name
        FROM recipes r
        LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
        LEFT JOIN ingredients i ON ri.ingredient_id = i.id
        LEFT JOIN supplier_ingredients si ON i.id = si.ingredient_id
        LEFT JOIN suppliers s ON si.supplier_id = s.id
        WHERE r.name = :menu_name
        ORDER BY ri.quantity DESC
        """
        
        result = db.execute(text(ingredient_query), {"menu_name": menu_name})
        ingredients = result.fetchall()
        
        print(f"메뉴 '{menu_name}' 식재료 조회 결과: {len(ingredients)}개")
        
        if not ingredients:
            # 식재료 정보가 없으면 임시 데이터 반환
            return {
                "menu_name": menu_name,
                "ingredients": ["쌀", "물", "소금"],  # 기본 식재료
                "ingredient_details": []
            }
        
        # 식재료 이름만 추출 (중복 제거)
        ingredient_names = list(set([
            row[0] for row in ingredients 
            if row[0] is not None
        ]))
        
        # 상세 정보도 함께 반환
        ingredient_details = [
            {
                "name": row[0],
                "code": row[1],
                "amount": float(row[2]) if row[2] else 0,
                "unit": row[3],
                "supplier": row[4]
            }
            for row in ingredients
            if row[0] is not None
        ]
        
        return {
            "menu_name": menu_name,
            "ingredients": ingredient_names[:8],  # 최대 8개까지만
            "ingredient_details": ingredient_details
        }
        
    except Exception as e:
        print(f"Error in get_menu_ingredients: {e}")
        import traceback
        traceback.print_exc()
        # 에러 시 기본 식재료 반환
        return {
            "menu_name": menu_name,
            "ingredients": ["재료정보없음"],
            "ingredient_details": [],
            "error": str(e)
        }

# 여러 메뉴의 식재료 정보 일괄 조회 API
@app.post("/api/menus_ingredients")
async def get_menus_ingredients(request: Request, db: Session = Depends(get_db)):
    """여러 메뉴의 식재료 정보 일괄 조회"""
    try:
        body_bytes = await request.body()
        body_str = body_bytes.decode('utf-8')
        body = json.loads(body_str)
        menu_names = body.get('menu_names', [])
        
        if not menu_names:
            return {}
        
        result = {}
        for menu_name in menu_names:
            ingredient_info = await get_menu_ingredients(menu_name, db)
            result[menu_name] = ingredient_info
        
        return result
        
    except Exception as e:
        print(f"Error in get_menus_ingredients: {e}")
        return {"error": str(e)}

# Pydantic 모델들
class DietPlanCreate(BaseModel):
    category: str
    date: date
    description: Optional[str] = None

class DietPlanResponse(BaseModel):
    id: int
    category: str
    date: date
    description: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class MenuCreate(BaseModel):
    diet_plan_id: int
    menu_type: str
    target_num_persons: int
    target_food_cost: Optional[Decimal] = None
    evaluation_score: Optional[int] = Field(None, ge=1, le=5)
    color: Optional[str] = None

class MenuResponse(BaseModel):
    id: int
    diet_plan_id: int
    menu_type: str
    target_num_persons: int
    target_food_cost: Optional[Decimal] = None
    evaluation_score: Optional[int] = None
    color: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class MenuItemCreate(BaseModel):
    menu_id: int
    name: str
    portion_num_persons: Optional[int] = None
    yield_rate: Optional[Decimal] = Decimal('1.0')
    recipe_id: Optional[int] = None
    photo_url: Optional[str] = None

class MenuItemResponse(BaseModel):
    id: int
    menu_id: int
    name: str
    portion_num_persons: Optional[int] = None
    yield_rate: Optional[Decimal] = None
    recipe_id: Optional[int] = None
    photo_url: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class RequirementCalculationRequest(BaseModel):
    menu_item_id: int
    portion_num_persons: Optional[int] = None
    yield_rate: Optional[Decimal] = None

class RequirementCalculationResponse(BaseModel):
    menu_item_id: int
    menu_item_name: str
    portion_num_persons: int
    yield_rate: Decimal
    ingredients: List[dict]
    total_cost: Decimal
    cost_per_person: Decimal

# API 엔드포인트들
@app.get("/")
async def root():
    return {"message": "다함식단관리 API에 오신 것을 환영합니다!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/diet-plans")
async def get_diet_plans(db: Session = Depends(get_db)):
    """식단표 목록 조회"""
    try:
        result = db.execute(text("SELECT * FROM DietPlans ORDER BY date DESC"))
        plans = [dict(row._mapping) for row in result]
        return {"success": True, "data": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/menus/{diet_plan_id}")
async def get_menus(diet_plan_id: int, db: Session = Depends(get_db)):
    """특정 식단표의 메뉴 목록 조회"""
    try:
        result = db.execute(
            text("SELECT * FROM Menus WHERE diet_plan_id = :plan_id"),
            {"plan_id": diet_plan_id}
        )
        menus = [dict(row._mapping) for row in result]
        return {"success": True, "data": menus}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/menu-items/{menu_id}")
async def get_menu_items(menu_id: int, db: Session = Depends(get_db)):
    """특정 메뉴의 메뉴 아이템 목록 조회"""
    try:
        result = db.execute(
            text("SELECT * FROM MenuItems WHERE menu_id = :menu_id"),
            {"menu_id": menu_id}
        )
        items = [dict(row._mapping) for row in result]
        return {"success": True, "data": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recipes")
async def serve_recipes():
    """레시피 관리 페이지 서빙"""
    return FileResponse("menu_recipe_management.html")

@app.get("/cooking")
async def serve_cooking_instruction():
    """조리지시서 관리 페이지 서빙"""
    return FileResponse("cooking_instruction_management.html")

@app.get("/portion")
async def serve_portion_instruction():
    """소분지시서 관리 페이지 서빙"""
    return FileResponse("portion_instruction_management.html")

@app.get("/api/recipes")
async def get_recipes(db: Session = Depends(get_db)):
    """레시피 목록 조회"""
    try:
        result = db.execute(text("SELECT * FROM recipes ORDER BY name"))
        plans = [dict(row._mapping) for row in result]
        return {"success": True, "data": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingredients")
async def serve_ingredients():
    """식재료 관리 페이지 서빙"""
    return FileResponse("ingredients_management.html")

@app.get("/api/ingredients/list")
async def get_ingredients(db: Session = Depends(get_db)):
    """식재료 목록 조회 API"""
    try:
        query = """
            SELECT i.id, i.name, i.base_unit, i.price, i.moq, i.allergy_codes,
                   i.supplier_id, s.name as supplier_name, s.update_frequency as delivery_schedule
            FROM ingredients i
            LEFT JOIN suppliers s ON i.supplier_id = s.id
            ORDER BY i.name
        """
        result = db.execute(text(query))
        ingredients = [dict(row._mapping) for row in result]
        return ingredients
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ingredients")
async def get_ingredients_api(db: Session = Depends(get_db)):
    """식재료 목록 조회 (API용) - 공급업체 가격 정보 포함"""
    try:
        query = """
            SELECT i.id, i.name, i.base_unit, i.moq, 
                   CAST(i.allergy_codes AS TEXT) as allergy_codes,
                   s.id as supplier_id, s.name as supplier_name, s.update_frequency as delivery_schedule,
                   si.preorder_date as preorder_date,
                   si.unit_price as unit_price,
                   si.selling_price as selling_price
            FROM ingredients i
            LEFT JOIN suppliers s ON i.supplier_id = s.id
            LEFT JOIN supplier_ingredients si ON i.id = si.ingredient_id AND s.id = si.supplier_id
            WHERE si.selling_price IS NOT NULL AND si.selling_price > 0
            ORDER BY si.selling_price ASC, i.name
        """
        result = db.execute(text(query))
        ingredients = [dict(row._mapping) for row in result]
        return ingredients
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/suppliers")
async def get_suppliers(db: Session = Depends(get_db)):
    """공급업체 목록 조회 (간단한 목록용)"""
    try:
        result = db.execute(text("SELECT id, name, parent_code FROM suppliers ORDER BY name"))
        suppliers = [dict(row._mapping) for row in result]
        return suppliers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search_recipes")
async def search_recipes(request: dict, db: Session = Depends(get_db)):
    """레시피 검색"""
    try:
        keyword = request.get("keyword", "").strip()
        limit = request.get("limit", 20)
        
        if keyword:
            # 키워드로 검색
            query = """
                SELECT r.id, r.name, r.evaluation_score as score, r.version, r.notes,
                       COUNT(ri.ingredient_id) as ingredient_count,
                       STRING_AGG(i.name, ', ' ORDER BY ri.quantity DESC) as main_ingredients
                FROM recipes r
                LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                LEFT JOIN ingredients i ON ri.ingredient_id = i.id
                WHERE r.name LIKE :keyword 
                GROUP BY r.id, r.name, r.evaluation_score, r.version, r.notes
                ORDER BY r.evaluation_score DESC, r.name
                LIMIT :limit
            """
            result = db.execute(text(query), {
                "keyword": f"%{keyword}%",
                "limit": limit
            })
        else:
            # 전체 목록 (평점 높은 순)
            query = """
                SELECT r.id, r.name, r.evaluation_score as score, r.version, r.notes,
                       COUNT(ri.ingredient_id) as ingredient_count,
                       STRING_AGG(i.name, ', ' ORDER BY ri.quantity DESC) as main_ingredients
                FROM recipes r
                LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                LEFT JOIN ingredients i ON ri.ingredient_id = i.id
                GROUP BY r.id, r.name, r.evaluation_score, r.version, r.notes
                ORDER BY r.evaluation_score DESC, r.name
                LIMIT :limit
            """
            result = db.execute(text(query), {"limit": limit})
        
        recipes = []
        for row in result:
            recipes.append({
                "id": row[0],
                "name": row[1], 
                "score": row[2] or 0,
                "version": row[3] or "1.0",
                "notes": row[4] or "",
                "ingredient_count": row[5] or 0,
                "main_ingredients": row[6] or ""
            })
        
        return recipes
    except Exception as e:
        print(f"검색 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/recipe/{recipe_id}")
async def get_recipe_detail(recipe_id: int, db: Session = Depends(get_db)):
    """레시피 상세 정보 조회"""
    try:
        # 기본 레시피 정보
        recipe_query = """
            SELECT id, name, version, evaluation_score, effective_date, notes, nutrition_data
            FROM recipes 
            WHERE id = :recipe_id
        """
        recipe_result = db.execute(text(recipe_query), {"recipe_id": recipe_id})
        recipe_row = recipe_result.first()
        
        if not recipe_row:
            raise HTTPException(status_code=404, detail="레시피를 찾을 수 없습니다")
        
        # 식자재 정보
        ingredients_query = """
            SELECT i.name, ri.quantity, ri.unit, ri.unit_in_kg, i.price
            FROM recipe_ingredients ri
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE ri.recipe_id = :recipe_id
            ORDER BY i.name
        """
        ingredients_result = db.execute(text(ingredients_query), {"recipe_id": recipe_id})
        
        ingredients = []
        total_cost_per_person = 0
        
        for ing_row in ingredients_result:
            ingredient = {
                "name": ing_row[0],
                "quantity": float(ing_row[1]) if ing_row[1] else 0,
                "unit": ing_row[2],
                "unit_in_kg": float(ing_row[3]) if ing_row[3] else 0,
                "price": float(ing_row[4]) if ing_row[4] else 0
            }
            
            # 1인당 비용 계산
            if ingredient["unit_in_kg"] and ingredient["price"]:
                cost_per_person = ingredient["unit_in_kg"] * ingredient["price"]
                total_cost_per_person += cost_per_person
                ingredient["cost_per_person"] = round(cost_per_person, 2)
            else:
                ingredient["cost_per_person"] = 0
            
            ingredients.append(ingredient)
        
        recipe_detail = {
            "id": recipe_row[0],
            "name": recipe_row[1],
            "version": recipe_row[2] or "1.0",
            "evaluation_score": recipe_row[3] or 0,
            "effective_date": str(recipe_row[4]) if recipe_row[4] else "-",
            "notes": recipe_row[5] or "비고 없음",
            "nutrition_data": recipe_row[6] if recipe_row[6] else {},
            "ingredients": ingredients,
            "total_cost_per_person": round(total_cost_per_person, 2)
        }
        
        return recipe_detail
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"레시피 상세 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/init_sample_recipes")
async def init_sample_recipes(db: Session = Depends(get_db)):
    """샘플 레시피 데이터 생성"""
    try:
        sample_recipes = [
            {"name": "김치찌개", "evaluation_score": 5, "notes": "돼지고기 듬뿍, 매콤한 맛"},
            {"name": "된장찌개", "evaluation_score": 4, "notes": "두부와 호박이 들어간 구수한 맛"},
            {"name": "불고기", "evaluation_score": 5, "notes": "달콤한 양념의 소고기 불고기"},
            {"name": "비빔밥", "evaluation_score": 4, "notes": "각종 나물과 고추장을 넣은 비빔밥"},
            {"name": "갈비탕", "evaluation_score": 5, "notes": "사골 우린 깔끔한 갈비탕"},
            {"name": "제육볶음", "evaluation_score": 4, "notes": "매콤달콤한 돼지고기 볶음"},
            {"name": "계란말이", "evaluation_score": 3, "notes": "부드러운 계란말이"},
            {"name": "잡채", "evaluation_score": 4, "notes": "당면과 각종 채소를 볶은 잡채"},
            {"name": "오징어볶음", "evaluation_score": 4, "notes": "매콤한 오징어볶음"},
            {"name": "콩나물국", "evaluation_score": 3, "notes": "시원한 콩나물국"},
            {"name": "미역국", "evaluation_score": 3, "notes": "소고기를 넣은 미역국"},
            {"name": "닭볶음탕", "evaluation_score": 5, "notes": "매콤한 닭볶음탕"},
            {"name": "삼겹살구이", "evaluation_score": 5, "notes": "구워낸 삼겹살"},
            {"name": "떡볶이", "evaluation_score": 4, "notes": "매콤달콤한 떡볶이"},
            {"name": "순두부찌개", "evaluation_score": 4, "notes": "부드러운 순두부찌개"},
            {"name": "김치볶음밥", "evaluation_score": 4, "notes": "김치와 함께 볶은 볶음밥"},
            {"name": "라면", "evaluation_score": 3, "notes": "간단한 라면"},
            {"name": "치킨", "evaluation_score": 5, "notes": "바삭한 프라이드 치킨"},
            {"name": "피자", "evaluation_score": 4, "notes": "치즈가 듬뿍 들어간 피자"},
            {"name": "햄버거", "evaluation_score": 4, "notes": "수제 햄버거"}
        ]
        
        for recipe_data in sample_recipes:
            # 중복 체크
            existing = db.execute(
                text("SELECT id FROM Recipe WHERE name = :name"),
                {"name": recipe_data["name"]}
            ).first()
            
            if not existing:
                db.execute(
                    text("""
                        INSERT INTO recipes (name, evaluation_score, notes, version, created_at, updated_at)
                        VALUES (:name, :score, :notes, '1.0', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """),
                    {
                        "name": recipe_data["name"],
                        "score": recipe_data["evaluation_score"],
                        "notes": recipe_data["notes"]
                    }
                )
        
        db.commit()
        return {"success": True, "message": "샘플 레시피 데이터가 추가되었습니다"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"샘플 데이터 추가 실패: {str(e)}")

@app.post("/api/admin/init_user_extensions")
async def init_user_extensions(request: Request, db: Session = Depends(get_db)):
    """사용자 관리 기능 확장을 위한 데이터베이스 업데이트"""
    user = get_current_user(request)
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        # 1. 사용자 테이블에 필드 추가
        alter_queries = [
            "ALTER TABLE users ADD COLUMN phone_number VARCHAR(20) DEFAULT NULL",
            "ALTER TABLE users ADD COLUMN birth_date DATE DEFAULT NULL", 
            "ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1",
            "ALTER TABLE users ADD COLUMN assigned_sites TEXT DEFAULT NULL"
        ]
        
        for query in alter_queries:
            try:
                db.execute(text(query))
            except Exception as e:
                print(f"Column might already exist: {e}")
        
        # 2. 사용자-사업장 관계 테이블 생성
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS user_business_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                business_location_id INTEGER NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (business_location_id) REFERENCES business_locations (id),
                UNIQUE(user_id, business_location_id)
            )
        """))
        
        db.commit()
        return {"success": True, "message": "사용자 관리 기능이 확장되었습니다."}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"데이터베이스 업데이트 실패: {str(e)}")

@app.get("/api/admin/users/{user_id}/sites")
async def get_user_sites(user_id: int, request: Request, db: Session = Depends(get_db)):
    """사용자가 접근 가능한 사업장 목록 조회"""
    user = get_current_user(request)
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        # 사용자에게 할당된 사업장 목록
        assigned_sites = db.execute(text("""
            SELECT bl.id, bl.name, bl.location, bl.business_type
            FROM business_locations bl
            JOIN user_business_locations ubl ON bl.id = ubl.business_location_id
            WHERE ubl.user_id = :user_id
        """), {"user_id": user_id}).fetchall()
        
        # 모든 사업장 목록
        all_sites = db.execute(text("""
            SELECT id, name, location, business_type
            FROM business_locations
            ORDER BY name
        """)).fetchall()
        
        assigned_site_ids = [site[0] for site in assigned_sites]
        
        return {
            "assigned_sites": [dict(site._mapping) for site in assigned_sites],
            "all_sites": [dict(site._mapping) for site in all_sites],
            "assigned_site_ids": assigned_site_ids
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/users/{user_id}/sites")
async def update_user_sites(user_id: int, site_data: dict, request: Request, db: Session = Depends(get_db)):
    """사용자의 접근 가능한 사업장 업데이트"""
    user = get_current_user(request)
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        site_ids = site_data.get('site_ids', [])
        
        # 기존 할당 삭제
        db.execute(text("DELETE FROM user_business_locations WHERE user_id = :user_id"), 
                  {"user_id": user_id})
        
        # 새로운 할당 추가
        for site_id in site_ids:
            db.execute(text("""
                INSERT INTO user_business_locations (user_id, business_location_id)
                VALUES (:user_id, :site_id)
            """), {"user_id": user_id, "site_id": site_id})
        
        db.commit()
        return {"success": True, "message": "사업장 할당이 업데이트되었습니다."}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/users/{user_id}/reset-password")
async def reset_user_password(user_id: int, request: Request, db: Session = Depends(get_db)):
    """사용자 비밀번호 초기화"""
    user = get_current_user(request)
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        # 기본 비밀번호를 "password123"으로 설정
        default_password = "password123"
        password_hash = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        db.execute(text("""
            UPDATE users 
            SET password_hash = :password_hash, updated_at = CURRENT_TIMESTAMP
            WHERE id = :user_id
        """), {"password_hash": password_hash, "user_id": user_id})
        
        db.commit()
        return {
            "success": True, 
            "message": f"비밀번호가 '{default_password}'로 초기화되었습니다.",
            "new_password": default_password
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/users/{user_id}")
async def update_user(user_id: int, user_data: dict, request: Request, db: Session = Depends(get_db)):
    """사용자 정보 업데이트"""
    user = get_current_user(request)
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        update_fields = []
        params = {"user_id": user_id}
        
        # 업데이트할 필드들
        updatable_fields = {
            'username': 'username',
            'role': 'role', 
            'contact_info': 'contact_info',
            'phone_number': 'phone_number',
            'birth_date': 'birth_date',
            'department': 'department',
            'position': 'position',
            'is_active': 'is_active',
            'managed_site': 'managed_site'
        }
        
        for key, db_field in updatable_fields.items():
            if key in user_data:
                update_fields.append(f"{db_field} = :{key}")
                params[key] = user_data[key]
        
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f"""
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE id = :user_id
            """
            
            db.execute(text(query), params)
            db.commit()
        
        return {"success": True, "message": "사용자 정보가 업데이트되었습니다."}
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        db.rollback()
        print(f"샘플 데이터 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create_supplier_ingredient_data")
async def create_supplier_ingredient_data(db: Session = Depends(get_db)):
    """공급업체-식재료 가격 데이터 생성"""
    try:
        # 기존 supplier_ingredients 데이터 삭제
        db.execute(text("DELETE FROM supplier_ingredients WHERE id > 0"))
        
        # 공급업체-식재료 가격 데이터 삽입
        supplier_ingredients_data = [
            # 신선마트 (야채류)
            {"supplier_id": 2, "ingredient_id": 101, "ingredient_code": "A001", "unit_price": 1200, "selling_price": 1500, "preorder_date": "1"},
            {"supplier_id": 2, "ingredient_id": 102, "ingredient_code": "A002", "unit_price": 1600, "selling_price": 2000, "preorder_date": "1"},
            {"supplier_id": 2, "ingredient_id": 103, "ingredient_code": "A003", "unit_price": 2400, "selling_price": 3000, "preorder_date": "1"},
            {"supplier_id": 2, "ingredient_id": 104, "ingredient_code": "A004", "unit_price": 960, "selling_price": 1200, "preorder_date": "2"},
            {"supplier_id": 2, "ingredient_id": 105, "ingredient_code": "A005", "unit_price": 1200, "selling_price": 1500, "preorder_date": "2"},
            
            # 육류전문점
            {"supplier_id": 4, "ingredient_id": 201, "ingredient_code": "M001", "unit_price": 28000, "selling_price": 35000, "preorder_date": "1"},
            {"supplier_id": 4, "ingredient_id": 202, "ingredient_code": "M002", "unit_price": 14400, "selling_price": 18000, "preorder_date": "1"},
            {"supplier_id": 4, "ingredient_id": 203, "ingredient_code": "M003", "unit_price": 6400, "selling_price": 8000, "preorder_date": "1"},
            {"supplier_id": 4, "ingredient_id": 204, "ingredient_code": "M004", "unit_price": 22400, "selling_price": 28000, "preorder_date": "1"},
            
            # 해산물직판
            {"supplier_id": 5, "ingredient_id": 301, "ingredient_code": "S001", "unit_price": 2400, "selling_price": 3000, "preorder_date": "2"},
            {"supplier_id": 5, "ingredient_id": 302, "ingredient_code": "S002", "unit_price": 3200, "selling_price": 4000, "preorder_date": "2"},
            {"supplier_id": 5, "ingredient_id": 303, "ingredient_code": "S003", "unit_price": 4000, "selling_price": 5000, "preorder_date": "3"},
            {"supplier_id": 5, "ingredient_id": 304, "ingredient_code": "S004", "unit_price": 20000, "selling_price": 25000, "preorder_date": "3"},
            
            # 냉동식품
            {"supplier_id": 6, "ingredient_id": 401, "ingredient_code": "F001", "unit_price": 6400, "selling_price": 8000, "preorder_date": "3"},
            {"supplier_id": 6, "ingredient_id": 402, "ingredient_code": "F002", "unit_price": 3200, "selling_price": 4000, "preorder_date": "3"},
            {"supplier_id": 6, "ingredient_id": 403, "ingredient_code": "F003", "unit_price": 2800, "selling_price": 3500, "preorder_date": "3"},
            
            # 조미료전문
            {"supplier_id": 7, "ingredient_id": 501, "ingredient_code": "C001", "unit_price": 2400, "selling_price": 3000, "preorder_date": "4"},
            {"supplier_id": 7, "ingredient_id": 502, "ingredient_code": "C002", "unit_price": 12000, "selling_price": 15000, "preorder_date": "4"},
            {"supplier_id": 7, "ingredient_id": 503, "ingredient_code": "C003", "unit_price": 6400, "selling_price": 8000, "preorder_date": "4"},
            {"supplier_id": 7, "ingredient_id": 504, "ingredient_code": "C004", "unit_price": 4800, "selling_price": 6000, "preorder_date": "4"},
            {"supplier_id": 7, "ingredient_id": 505, "ingredient_code": "C005", "unit_price": 3200, "selling_price": 4000, "preorder_date": "4"},
            
            # 식재료왕 (기본 식재료)
            {"supplier_id": 1, "ingredient_id": 1, "ingredient_code": None, "unit_price": 4000, "selling_price": 5000, "preorder_date": "2"},
            {"supplier_id": 1, "ingredient_id": 2, "ingredient_code": None, "unit_price": 12000, "selling_price": 15000, "preorder_date": "2"},
            {"supplier_id": 1, "ingredient_id": 3, "ingredient_code": None, "unit_price": 2400, "selling_price": 3000, "preorder_date": "2"},
            {"supplier_id": 1, "ingredient_id": 4, "ingredient_code": None, "unit_price": 6400, "selling_price": 8000, "preorder_date": "2"},
            {"supplier_id": 1, "ingredient_id": 5, "ingredient_code": None, "unit_price": 9600, "selling_price": 12000, "preorder_date": "2"},
        ]
        
        for data in supplier_ingredients_data:
            query = """
                INSERT INTO supplier_ingredients 
                (supplier_id, ingredient_id, ingredient_code, unit_price, selling_price, preorder_date, is_published)
                VALUES (:supplier_id, :ingredient_id, :ingredient_code, :unit_price, :selling_price, :preorder_date, true)
                ON CONFLICT DO NOTHING
            """
            db.execute(text(query), data)
        
        db.commit()
        return {"message": "공급업체-식재료 가격 데이터가 생성되었습니다."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create_test_data")
async def create_test_data(db: Session = Depends(get_db)):
    """테스트용 레시피와 식재료 데이터 생성"""
    try:
        # 기존 데이터를 삭제하지 않고 새 ID로 추가
        # 새로운 ID 범위 사용 (1000번대)
        test_id_start = 1000
        
        # 테스트 식재료 추가 (1000번대 ID 사용)
        ingredients_data = [
            (test_id_start+1, "감자(1KG)", "kg", 2000),
            (test_id_start+2, "양파(1KG)", "kg", 1500), 
            (test_id_start+3, "당근(1KG)", "kg", 3000),
            (test_id_start+4, "돼지고기(1KG)", "kg", 15000),
            (test_id_start+5, "된장(1KG)", "kg", 5000)
        ]
        
        for ing in ingredients_data:
            db.execute(text("""
                INSERT INTO ingredients (id, name, base_unit, price, created_at, updated_at)
                VALUES (:id, :name, :unit, :price, NOW(), NOW())
            """), {"id": ing[0], "name": ing[1], "unit": ing[2], "price": ing[3]})
        
        # 테스트 레시피 추가 (1000번대 ID 사용)
        recipes_data = [
            (test_id_start+1, "감자찜", "1.0", 4, "맛있는 감자찜입니다"),
            (test_id_start+2, "된장찌개", "1.0", 5, "구수한 된장찌개입니다"),
            (test_id_start+3, "돼지고기볶음", "1.0", 4, "고소한 돼지고기볶음입니다")
        ]
        
        for recipe in recipes_data:
            db.execute(text("""
                INSERT INTO recipes (id, name, version, evaluation_score, notes, created_at, updated_at)
                VALUES (:id, :name, :version, :score, :notes, NOW(), NOW())
            """), {"id": recipe[0], "name": recipe[1], "version": recipe[2], "score": recipe[3], "notes": recipe[4]})
        
        # 레시피-식재료 연결 데이터 추가 (1000번대 ID 사용)
        recipe_ingredients_data = [
            (test_id_start+1, test_id_start+1, 0.5, "kg", 0.5),  # 감자찜 - 감자 0.5kg
            (test_id_start+1, test_id_start+2, 0.1, "kg", 0.1),  # 감자찜 - 양파 0.1kg
            (test_id_start+2, test_id_start+1, 0.3, "kg", 0.3),  # 된장찌개 - 감자 0.3kg
            (test_id_start+2, test_id_start+2, 0.1, "kg", 0.1),  # 된장찌개 - 양파 0.1kg
            (test_id_start+2, test_id_start+5, 0.05, "kg", 0.05), # 된장찌개 - 된장 0.05kg
            (test_id_start+3, test_id_start+4, 0.3, "kg", 0.3),   # 돼지고기볶음 - 돼지고기 0.3kg
            (test_id_start+3, test_id_start+2, 0.1, "kg", 0.1),   # 돼지고기볶음 - 양파 0.1kg
        ]
        
        for ri in recipe_ingredients_data:
            db.execute(text("""
                INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, unit_in_kg, created_at, updated_at)
                VALUES (:recipe_id, :ingredient_id, :quantity, :unit, :unit_in_kg, NOW(), NOW())
            """), {
                "recipe_id": ri[0], 
                "ingredient_id": ri[1], 
                "quantity": ri[2], 
                "unit": ri[3], 
                "unit_in_kg": ri[4]
            })
        
        
        db.commit()
        
        return {"success": True, "message": f"테스트 데이터가 생성되었습니다: 레시피 {len(recipes_data)}개, 식재료 {len(ingredients_data)}개"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"테스트 데이터 생성 실패: {str(e)}")

@app.post("/api/import_recipes_from_json")
async def import_recipes_from_json(db: Session = Depends(get_db)):
    """JSON 파일에서 레시피 데이터 대량 임포트"""
    import json
    
    try:
        # recipes_clean.json 파일 읽기
        with open("recipes_clean.json", "r", encoding="utf-8") as f:
            recipes_data = json.load(f)
        
        imported_count = 0
        for recipe in recipes_data[:1000]:  # 처음 1000개만 임포트 (테스트용)
            recipe_name = recipe.get("ri_name", "").strip()
            if not recipe_name:
                continue
                
            # 중복 체크
            existing = db.execute(
                text("SELECT id FROM recipes WHERE name = :name"),
                {"name": recipe_name}
            ).first()
            
            if not existing:
                # 카테고리 매핑
                ctg_name = recipe.get("ctg_name", "기타")
                category = "기타"
                if "국" in ctg_name or "찌개" in ctg_name:
                    category = "국/찌개"
                elif "밥" in ctg_name or "면" in ctg_name:
                    category = "주식"
                elif "반찬" in ctg_name or "나물" in ctg_name:
                    category = "반찬"
                
                # 평가점수 계산 (랜덤하게 3-5점)
                import random
                score = random.choice([3, 4, 5])
                
                db.execute(
                    text("""
                        INSERT INTO recipes (name, evaluation_score, notes, version, created_at, updated_at)
                        VALUES (:name, :score, :notes, '1.0', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """),
                    {
                        "name": recipe_name,
                        "score": score,
                        "notes": f"{category} 메뉴"
                    }
                )
                imported_count += 1
        
        db.commit()
        return {"success": True, "message": f"{imported_count}개의 레시피가 임포트되었습니다"}
        
    except Exception as e:
        db.rollback()
        print(f"JSON 임포트 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cost-analysis")
async def get_cost_analysis(db: Session = Depends(get_db)):
    """메뉴별 비용 분석 조회"""
    try:
        result = db.execute(text("SELECT * FROM menu_cost_analysis"))
        analysis = [dict(row._mapping) for row in result]
        return {"success": True, "data": analysis}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        # ... existing code ...

@app.get("/test-db")
async def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        db = SessionLocal()
        # 간단한 쿼리 실행
        result = db.execute(text("SELECT 1 as test"))
        db.close()
        return {"success": True, "message": "데이터베이스 연결 성공", "test": result.fetchone()[0]}
    except Exception as e:
        return {"success": False, "error": str(e), "type": type(e).__name__}

# 새로운 API 엔드포인트들

@app.post("/diet-plans", response_model=DietPlanResponse)
async def create_diet_plan(diet_plan: DietPlanCreate, db: Session = Depends(get_db)):
    """식단표 생성"""
    try:
        db_diet_plan = DietPlan(**diet_plan.dict())
        db.add(db_diet_plan)
        db.commit()
        db.refresh(db_diet_plan)
        return db_diet_plan
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/menus", response_model=MenuResponse)
async def create_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    """세부식단표 생성"""
    try:
        db_menu = Menu(**menu.dict())
        db.add(db_menu)
        db.commit()
        db.refresh(db_menu)
        return db_menu
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/menu-items", response_model=MenuItemResponse)
async def create_menu_item(menu_item: MenuItemCreate, db: Session = Depends(get_db)):
    """메뉴 아이템 생성"""
    try:
        # 기본값 설정: portion_num_persons가 없으면 menu의 target_num_persons 사용
        if menu_item.portion_num_persons is None:
            menu = db.query(Menu).filter(Menu.id == menu_item.menu_id).first()
            if menu:
                menu_item.portion_num_persons = menu.target_num_persons
        
        db_menu_item = MenuItem(**menu_item.dict())
        db.add(db_menu_item)
        db.commit()
        db.refresh(db_menu_item)
        return db_menu_item
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculate-requirements", response_model=RequirementCalculationResponse)
async def calculate_menu_item_requirements(
    request: RequirementCalculationRequest,
    db: Session = Depends(get_db)
):
    """메뉴 아이템의 식재료 소요량 계산"""
    try:
        # 메뉴 아이템 조회
        menu_item = db.query(MenuItem).filter(MenuItem.id == request.menu_item_id).first()
        if not menu_item:
            raise HTTPException(status_code=404, detail="메뉴 아이템을 찾을 수 없습니다")
        
        # 요청값 또는 기본값 사용
        portion_num_persons = request.portion_num_persons or menu_item.portion_num_persons
        yield_rate = request.yield_rate or menu_item.yield_rate
        
        if not portion_num_persons:
            # menu의 target_num_persons 사용
            menu = db.query(Menu).filter(Menu.id == menu_item.menu_id).first()
            portion_num_persons = menu.target_num_persons if menu else 1
        
        # 레시피 정보 조회 (임시 데이터 - 실제로는 DB에서 조회)
        recipe_ingredients = [
            {
                'ingredient_id': 1,
                'ingredient_name': '냉동쥬키니호박',
                'quantity_per_person': 0.045,
                'unit': 'kg',
                'moq': 1.0,
                'unit_price': 5000
            }
        ]
        
        # 계산 실행
        menu_item_data = {
            'portion_num_persons': portion_num_persons,
            'yield_rate': float(yield_rate)
        }
        
        requirements = MenuCalculator.calculate_menu_item_requirements(
            menu_item_data, recipe_ingredients
        )
        
        # 총 비용 계산
        total_cost = sum(req['total_cost'] for req in requirements)
        cost_per_person = total_cost / portion_num_persons
        
        return RequirementCalculationResponse(
            menu_item_id=menu_item.id,
            menu_item_name=menu_item.name,
            portion_num_persons=portion_num_persons,
            yield_rate=yield_rate,
            ingredients=requirements,
            total_cost=Decimal(str(total_cost)),
            cost_per_person=Decimal(str(cost_per_person))
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/create-sample-data")
async def create_sample_data(db: Session = Depends(get_db)):
    """샘플 데이터 생성"""
    try:
        # 테이블 생성
        Base.metadata.create_all(bind=engine)
        
        # 기존 데이터 확인
        existing_diet_plan = db.query(DietPlan).first()
        if existing_diet_plan:
            return {"message": "샘플 데이터가 이미 존재합니다"}
        
        # 샘플 식단표 생성
        diet_plan = DietPlan(
            category="학교",
            date=datetime(2025, 8, 14).date(),
            description="학교 급식 계획"
        )
        db.add(diet_plan)
        db.commit()
        db.refresh(diet_plan)
        
        # 샘플 메뉴 생성
        menu = Menu(
            diet_plan_id=diet_plan.id,
            menu_type="중식A",
            target_num_persons=105,
            target_food_cost=Decimal('50000'),
            color="red"
        )
        db.add(menu)
        db.commit()
        db.refresh(menu)
        
        # 샘플 메뉴 아이템 생성
        menu_item = MenuItem(
            menu_id=menu.id,
            name="호박새우젓국찌개",
            portion_num_persons=105,
            yield_rate=Decimal('0.7')
        )
        db.add(menu_item)
        db.commit()
        db.refresh(menu_item)
        
        return {
            "message": "샘플 데이터가 성공적으로 생성되었습니다",
            "diet_plan_id": diet_plan.id,
            "menu_id": menu.id,
            "menu_item_id": menu_item.id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/import-real-data")
async def import_real_data(db: Session = Depends(get_db)):
    """실제 Excel 데이터를 데이터베이스로 임포트"""
    try:
        # 테이블 생성
        Base.metadata.create_all(bind=engine)
        
        # 데이터 임포트 실행
        from data_import import run_full_import
        
        print("실제 데이터 임포트 시작...")
        run_full_import(db)
        
        # 임포트 결과 통계
        supplier_count = db.query(Supplier).count()
        ingredient_count = db.query(Ingredient).count()
        diet_plan_count = db.query(DietPlan).count()
        menu_count = db.query(Menu).count()
        menu_item_count = db.query(MenuItem).count()
        
        return {
            "message": "실제 데이터 임포트가 완료되었습니다!",
            "statistics": {
                "suppliers": supplier_count,
                "ingredients": ingredient_count,
                "diet_plans": diet_plan_count,
                "menus": menu_count,
                "menu_items": menu_item_count
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"임포트 오류: {str(e)}")

@app.get("/data-statistics")
async def get_data_statistics(db: Session = Depends(get_db)):
    """데이터베이스 통계 조회"""
    try:
        stats = {
            "suppliers": db.query(Supplier).count(),
            "ingredients": db.query(Ingredient).count(),
            "diet_plans": db.query(DietPlan).count(), 
            "menus": db.query(Menu).count(),
            "menu_items": db.query(MenuItem).count(),
            "recipes": db.query(Recipe).count()
        }
        
        # 가장 비싼/싼 식재료 (상위 5개)
        try:
            from sqlalchemy import desc
            expensive_items = db.execute(
                text("""
                SELECT i.name, si.unit_price, s.name as supplier_name
                FROM supplier_ingredients si
                JOIN ingredients i ON si.ingredient_id = i.id  
                JOIN suppliers s ON si.supplier_id = s.id
                WHERE si.unit_price > 0
                ORDER BY si.unit_price DESC
                LIMIT 5
                """)
            ).fetchall()
            
            stats["most_expensive_items"] = [
                {
                    "name": row[0],
                    "price": float(row[1]),
                    "supplier": row[2]
                } for row in expensive_items
            ]
        except:
            stats["most_expensive_items"] = []
        
        return {"success": True, "data": stats}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 관리자 API 엔드포인트들
@app.get("/api/admin/dashboard-stats")
async def get_admin_dashboard_stats(db: Session = Depends(get_db)):
    """관리자 대시보드 통계 데이터"""
    try:
        # 사용자 수 계산 (User 테이블 기반)
        total_users = db.query(User).count()
        
        # 협력업체 수 (Supplier 테이블의 협력업체)
        total_suppliers = db.query(Supplier).count()
        
        # 오늘 식단 수
        from datetime import date
        today = date.today()
        today_menus = db.query(DietPlan).filter(DietPlan.date == today).count()
        
        # 최근 7일간 단가 업데이트 (임시 값)
        price_updates = 15  # 실제로는 가격 변경 로그에서 계산
        
        return {
            "success": True,
            "totalUsers": total_users,
            "totalSuppliers": total_suppliers, 
            "todayMenus": today_menus,
            "priceUpdates": price_updates
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/recent-activity")
async def get_recent_activity(db: Session = Depends(get_db)):
    """최근 활동 로그"""
    try:
        # 임시 활동 로그 데이터
        activities = [
            {
                "time": "14:30",
                "message": "새로운 식단이 등록되었습니다",
                "user": "영양사김"
            },
            {
                "time": "13:15",
                "message": "식재료 단가가 업데이트되었습니다",
                "user": "관리자박"
            },
            {
                "time": "12:00",
                "message": "사용자 권한이 변경되었습니다",
                "user": "시스템"
            },
            {
                "time": "11:45",
                "message": "메뉴가 복사되었습니다 (A학교 → B학교)",
                "user": "영양사이"
            },
            {
                "time": "10:30",
                "message": "새로운 사업장이 등록되었습니다",
                "user": "관리자최"
            }
        ]
        
        return activities
    except Exception as e:
        return []

# 권한 체크 함수들
def check_admin_permission(user_role: str) -> bool:
    """관리자 권한 확인"""
    admin_roles = ["admin", "super_admin", "system_admin"]
    return user_role in admin_roles

def get_user_permissions(user_id: int, db: Session) -> list:
    """사용자 권한 목록 가져오기"""
    # 실제 구현에서는 사용자 테이블에서 권한 조회
    # 임시로 하드코딩된 권한 반환
    return ["SUPER_ADMIN"]  # 임시

@app.get("/api/admin/check-access")
async def check_admin_access(db: Session = Depends(get_db)):
    """관리자 접근 권한 확인"""
    try:
        # 실제로는 JWT 토큰이나 세션에서 사용자 정보 확인
        # 임시로 관리자 권한 허용
        return {
            "hasAccess": True,
            "userRole": "admin",
            "permissions": ["SUPER_ADMIN"],
            "username": "관리자"
        }
    except Exception as e:
        return {"hasAccess": False, "error": str(e)}

# 사용자 관리 API 엔드포인트들
class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: str
    contact_info: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    managed_site: Optional[str] = None
    operator: bool = False
    semi_operator: bool = False

class UserUpdateRequest(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    contact_info: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    managed_site: Optional[str] = None
    operator: Optional[bool] = None
    semi_operator: Optional[bool] = None

@app.get("/api/admin/users")
async def get_users(page: int = 1, limit: int = 20, search: str = "", db: Session = Depends(get_db)):
    """사용자 목록 조회"""
    try:
        # 임시 사용자 데이터 (실제로는 User 테이블에서 조회)
        sample_users = [
            {
                "id": 1,
                "username": "admin",
                "role": "admin",
                "department": "관리부",
                "position": "관리자",
                "managed_site": "본사",
                "is_active": True,
                "last_login": "2025-08-30 14:30",
                "contact_info": "010-1234-5678"
            },
            {
                "id": 2,
                "username": "nutritionist1",
                "role": "nutritionist",
                "department": "영양관리부",
                "position": "영양사",
                "managed_site": "A학교",
                "is_active": True,
                "last_login": "2025-08-30 13:15",
                "contact_info": "010-2345-6789"
            },
            {
                "id": 3,
                "username": "nutritionist2",
                "role": "nutritionist", 
                "department": "영양관리부",
                "position": "영양사",
                "managed_site": "B학교",
                "is_active": True,
                "last_login": "2025-08-29 16:45",
                "contact_info": "010-3456-7890"
            },
            {
                "id": 4,
                "username": "manager1",
                "role": "admin",
                "department": "운영부",
                "position": "팀장",
                "managed_site": "C회사",
                "is_active": False,
                "last_login": "2025-08-28 09:20",
                "contact_info": "010-4567-8901"
            }
        ]
        
        # 검색 필터링 (임시)
        if search:
            sample_users = [
                user for user in sample_users
                if search.lower() in user["username"].lower() or
                   search.lower() in (user["department"] or "").lower() or
                   search.lower() in (user["managed_site"] or "").lower()
            ]
        
        # 페이지네이션 (임시)
        total_users = len(sample_users)
        total_pages = (total_users + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        users_page = sample_users[start_idx:end_idx]
        
        return {
            "success": True,
            "users": users_page,
            "currentPage": page,
            "totalPages": total_pages,
            "totalUsers": total_users
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """특정 사용자 정보 조회"""
    try:
        # 임시 데이터
        sample_user = {
            "id": user_id,
            "username": f"user{user_id}",
            "role": "nutritionist",
            "contact_info": "010-1234-5678",
            "department": "영양관리부",
            "position": "영양사", 
            "managed_site": "A학교",
            "operator": False,
            "semi_operator": True
        }
        
        return sample_user
    except Exception as e:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

@app.post("/api/admin/users")
async def create_user(user_data: UserCreateRequest, db: Session = Depends(get_db)):
    """새 사용자 생성"""
    try:
        # 실제로는 비밀번호 해싱 및 DB 저장
        import hashlib
        password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
        
        # 임시로 성공 응답
        return {
            "success": True,
            "message": "사용자가 성공적으로 생성되었습니다",
            "user_id": 999  # 임시 ID
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.put("/api/admin/users/{user_id}")
async def update_user(user_id: int, user_data: UserUpdateRequest, db: Session = Depends(get_db)):
    """사용자 정보 수정"""
    try:
        # 실제로는 DB에서 사용자 조회 및 업데이트
        
        # 비밀번호 변경이 있는 경우만 해싱
        if user_data.password:
            import hashlib
            password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
        
        return {
            "success": True,
            "message": "사용자 정보가 성공적으로 수정되었습니다"
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """사용자 삭제"""
    try:
        # 실제로는 DB에서 사용자 삭제 (또는 비활성화)
        return {
            "success": True,
            "message": "사용자가 성공적으로 삭제되었습니다"
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/admin/users/{user_id}/reset-password")
async def reset_user_password(user_id: int, db: Session = Depends(get_db)):
    """사용자 비밀번호 초기화"""
    try:
        # 임시 비밀번호 생성
        import random
        import string
        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        
        # 실제로는 해싱해서 DB에 저장
        import hashlib
        password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        
        return {
            "success": True,
            "message": "비밀번호가 초기화되었습니다",
            "newPassword": new_password
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/admin/sites")
async def get_admin_sites(db: Session = Depends(get_db)):
    """관리자용 사업장 목록 조회"""
    try:
        # 실제 데이터베이스에서 사업장 목록 조회
        customers = db.query(Customer).order_by(Customer.sort_order).all()
        
        sites = []
        for customer in customers:
            sites.append({
                "id": customer.id,
                "site_code": customer.site_code,
                "name": customer.name,
                "site_type": customer.site_type,
                "contact_person": customer.contact_person,
                "contact_phone": customer.contact_phone,
                "address": customer.address,
                "portion_size": customer.portion_size,
                "description": customer.description,
                "is_active": customer.is_active
            })
        
        return sites
    except Exception as e:
        print(f"사업장 목록 조회 중 오류: {e}")
        return []

# 사업장 관리 API 엔드포인트들
class SiteCreateRequest(BaseModel):
    site_code: Optional[str] = None  # 사업장코드
    name: str
    site_type: str  # 도시락, 운반, 학교, 요양원, 위탁, 일반음식점, 기타
    parent_id: Optional[int] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    portion_size: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True

class SiteUpdateRequest(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    portion_size: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

@app.get("/api/admin/sites/tree")
async def get_sites_tree(db: Session = Depends(get_db)):
    """사업장 계층 구조 트리 조회"""
    try:
        # 실제 데이터베이스에서 계층 구조 조회
        def build_customer_tree(customers, parent_id=None):
            """고객(사업장) 계층 트리 구조 생성"""
            tree = []
            for customer in customers:
                if customer.parent_id == parent_id:
                    # 하위 노드 재귀 조회
                    children = build_customer_tree(customers, customer.id)
                    
                    # 메뉴 수 계산 (임시: 0으로 설정)
                    menu_count = 0
                    
                    customer_dict = {
                        "id": customer.id,
                        "name": customer.name,
                        "site_type": customer.site_type,
                        "level": customer.level,
                        "is_active": customer.is_active,
                        "contact_person": customer.contact_person,
                        "contact_phone": customer.contact_phone,
                        "address": customer.address,
                        "portion_size": customer.portion_size,
                        "description": customer.description,
                        "menu_count": menu_count,
                        "children_count": len(children),
                        "children": children
                    }
                    tree.append(customer_dict)
            
            return tree
        
        # 모든 고객(사업장) 데이터 조회
        customers = db.query(Customer).order_by(Customer.sort_order).all()
        
        if not customers:
            return {
                "success": True,
                "message": "등록된 사업장이 없습니다.",
                "data": []
            }
        
        # 트리 구조 생성 (최상위 노드부터)
        sites_tree = build_customer_tree(customers, parent_id=None)
        
        return {"success": True, "sites": sites_tree}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/admin/sites/{site_id}")
async def get_site_detail(site_id: int, db: Session = Depends(get_db)):
    """특정 사업장 상세 정보 조회"""
    try:
        # 실제 데이터베이스에서 사업장 조회
        customer = db.query(Customer).filter(Customer.id == site_id).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="사업장을 찾을 수 없습니다")
        
        # 하위 사업장 수 계산
        children_count = db.query(Customer).filter(Customer.parent_id == customer.id).count()
        
        # 메뉴 수 계산 (임시로 0)
        menu_count = 0
        
        return {
            "id": customer.id,
            "name": customer.name,
            "site_type": customer.site_type,
            "contact_person": customer.contact_person,
            "contact_phone": customer.contact_phone,
            "address": customer.address,
            "portion_size": customer.portion_size,
            "description": customer.description,
            "is_active": customer.is_active,
            "menu_count": menu_count,
            "children_count": children_count,
            "parent_id": customer.parent_id,
            "level": customer.level,
            "sort_order": customer.sort_order
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="사업장 조회 중 오류가 발생했습니다")

@app.post("/api/admin/sites")
async def create_site(site_data: SiteCreateRequest, db: Session = Depends(get_db)):
    """새 사업장 생성"""
    try:
        print(f"[DEBUG] Received site_data: {site_data.dict()}")
        # 계층 레벨 계산
        level = 0
        if site_data.parent_id:
            parent = db.query(Customer).filter(Customer.id == site_data.parent_id).first()
            if not parent:
                return {"success": False, "message": "상위 사업장을 찾을 수 없습니다"}
            
            if site_data.site_type == "detail":
                level = 1
            elif site_data.site_type == "period":
                level = 2
        
        # 정렬 순서 계산
        max_sort_order = db.query(Customer.sort_order).order_by(Customer.sort_order.desc()).first()
        next_sort_order = (max_sort_order[0] + 1) if max_sort_order and max_sort_order[0] else 1
        
        # 새 사업장 생성
        new_customer = Customer(
            site_code=site_data.site_code,
            name=site_data.name,
            site_type=site_data.site_type,
            parent_id=site_data.parent_id,
            level=level,
            sort_order=next_sort_order,
            contact_person=site_data.contact_person,
            contact_phone=site_data.contact_phone,
            address=site_data.address,
            portion_size=site_data.portion_size,
            description=site_data.description,
            is_active=True
        )
        
        db.add(new_customer)
        db.commit()
        db.refresh(new_customer)
        
        # 사업장 생성 후 기본 식단표 자동 생성
        created_meal_plans = create_default_meal_plans(db, new_customer.id, new_customer.name)
        
        success_message = f"{getSiteTypeDisplay(site_data.site_type)}이(가) 성공적으로 생성되었습니다"
        if created_meal_plans > 0:
            success_message += f" (기본 식단표 {created_meal_plans}개 생성됨)"
        
        return {
            "success": True,
            "message": success_message,
            "site_id": new_customer.id
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"사업장 생성 중 오류가 발생했습니다: {str(e)}"}

@app.put("/api/admin/sites/{site_id}")
async def update_site(site_id: int, site_data: SiteUpdateRequest, db: Session = Depends(get_db)):
    """사업장 정보 수정"""
    try:
        # 기존 사업장 조회
        customer = db.query(Customer).filter(Customer.id == site_id).first()
        if not customer:
            return {"success": False, "message": "사업장을 찾을 수 없습니다"}
        
        # 수정할 필드 업데이트
        if site_data.name is not None:
            customer.name = site_data.name
        if site_data.contact_person is not None:
            customer.contact_person = site_data.contact_person
        if site_data.contact_phone is not None:
            customer.contact_phone = site_data.contact_phone
        if site_data.address is not None:
            customer.address = site_data.address
        if site_data.portion_size is not None:
            customer.portion_size = site_data.portion_size
        if site_data.description is not None:
            customer.description = site_data.description
        if site_data.is_active is not None:
            customer.is_active = site_data.is_active
            
        db.commit()
        
        return {
            "success": True,
            "message": "사업장 정보가 성공적으로 수정되었습니다"
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"사업장 수정 중 오류가 발생했습니다: {str(e)}"}

@app.delete("/api/admin/sites/{site_id}")
async def delete_site(site_id: int, db: Session = Depends(get_db)):
    """사업장 삭제"""
    try:
        # 기존 사업장 조회
        customer = db.query(Customer).filter(Customer.id == site_id).first()
        if not customer:
            return {"success": False, "message": "사업장을 찾을 수 없습니다"}
        
        # 하위 사업장이 있는지 확인
        children_count = db.query(Customer).filter(Customer.parent_id == site_id).count()
        if children_count > 0:
            return {
                "success": False, 
                "message": f"하위 사업장이 {children_count}개 있습니다. 먼저 하위 사업장을 삭제하세요."
            }
        
        # 사업장 삭제
        db.delete(customer)
        db.commit()
        
        return {
            "success": True,
            "message": "사업장이 성공적으로 삭제되었습니다"
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"사업장 삭제 중 오류가 발생했습니다: {str(e)}"}

# 사업장 이동 요청 모델
class SiteMoveRequest(BaseModel):
    new_parent_id: int

class MealCountCreate(BaseModel):
    delivery_site: str
    meal_type: str  # 조식/중식
    target_material_cost: Optional[float] = None
    site_name: str
    meal_count: int
    registration_date: str  # YYYY-MM-DD format

class MealCountUpdate(BaseModel):
    delivery_site: Optional[str] = None
    meal_type: Optional[str] = None
    target_material_cost: Optional[float] = None
    site_name: Optional[str] = None
    meal_count: Optional[int] = None
    registration_date: Optional[str] = None

class MealCountResponse(BaseModel):
    id: int
    delivery_site: str
    meal_type: str
    target_material_cost: Optional[float] = None
    site_name: str
    meal_count: int
    registration_date: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ===== 식자재 관리 API =====

@app.get("/api/admin/ingredients")
async def get_ingredients(request: Request, db: Session = Depends(get_db)):
    """식자재 목록 조회"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    try:
        ingredients = db.query(Ingredient).order_by(Ingredient.created_at.desc()).all()
        
        ingredients_data = []
        for ingredient in ingredients:
            ingredient_data = {
                "id": ingredient.id,
                "name": ingredient.name,
                "base_unit": ingredient.base_unit,
                "price": float(ingredient.price) if ingredient.price else None,
                "supplier_id": ingredient.supplier_id,
                "supplier_name": ingredient.supplier.name if ingredient.supplier else None,
                "moq": float(ingredient.moq) if ingredient.moq else None,
                "allergy_codes": ingredient.allergy_codes,
                "created_at": ingredient.created_at.isoformat(),
                "updated_at": ingredient.updated_at.isoformat()
            }
            ingredients_data.append(ingredient_data)
        
        return ingredients_data
        
    except Exception as e:
        print(f"[ERROR] 식자재 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="식자재 목록 조회 실패")

# 중복된 suppliers API 제거 - get_suppliers_enhanced 사용

@app.get("/api/admin/ingredient-template")
async def download_ingredient_template(request: Request):
    """식자재 업로드 템플릿 다운로드"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    template_path = "sample data/upload/food_sample.xls"
    if os.path.exists(template_path):
        return FileResponse(
            path=template_path,
            filename="식자재_업로드_템플릿.xls",
            media_type="application/vnd.ms-excel"
        )
    else:
        raise HTTPException(status_code=404, detail="템플릿 파일을 찾을 수 없습니다.")

@app.post("/api/admin/upload-ingredients")
async def upload_ingredients(
    request: Request, 
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """식자재 엑셀 파일 업로드"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    try:
        # 파일 형식 검증
        if not file.filename.endswith(('.xlsx', '.xls')):
            return {"success": False, "message": "엑셀 파일만 업로드 가능합니다."}
        
        # 파일 크기 검증 (10MB)
        if file.size > 10 * 1024 * 1024:
            return {"success": False, "message": "파일 크기는 10MB를 초과할 수 없습니다."}
        
        # 임시 파일 저장
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        try:
            # 엑셀 파일 처리 (pandas 사용)
            import pandas as pd
            
            # 엑셀 파일 읽기
            df = pd.read_excel(temp_path)
            
            # 기본 검증 - 규격 컬럼 포함
            required_columns = ['식자재명', '규격', '단위']  # 필수 컬럼
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return {
                    "success": False, 
                    "message": f"필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}"
                }
            
            processed_count = 0
            error_count = 0
            error_details = []
            
            for index, row in df.iterrows():
                try:
                    # 빈 행 건너뛰기
                    if pd.isna(row.get('식자재명')) or str(row.get('식자재명')).strip() == '':
                        continue
                    
                    # 규격 컬럼 포함하여 처리
                    ingredient_name = str(row['식자재명']).strip()
                    specification = str(row['규격']).strip() if not pd.isna(row.get('규격')) else ''
                    base_unit = str(row['단위']).strip()
                    
                    # 추가 정보들
                    ingredient_code = str(row.get('식자재코드', '')).strip() if not pd.isna(row.get('식자재코드')) else ''
                    category = str(row.get('분류(대분류)', '')).strip() if not pd.isna(row.get('분류(대분류)')) else ''
                    subcategory = str(row.get('기본식자재(소분류)', '')).strip() if not pd.isna(row.get('기본식자재(소분류)')) else ''
                    storage_method = str(row.get('저장방법', '')).strip() if not pd.isna(row.get('저장방법')) else ''
                    weight = str(row.get('중량', '')).strip() if not pd.isna(row.get('중량')) else ''
                    weight_unit = str(row.get('중량단위', '')).strip() if not pd.isna(row.get('중량단위')) else ''
                    notes = str(row.get('비고', '')).strip() if not pd.isna(row.get('비고')) else ''
                    
                    # 판매가 처리 (숫자가 아닌 경우 None)
                    try:
                        price = float(row.get('판매가', 0)) if not pd.isna(row.get('판매가')) else None
                    except:
                        price = None
                    
                    # 공급업체 처리
                    supplier_name = str(row.get('공급처명', '')).strip() if not pd.isna(row.get('공급처명')) else None
                    supplier_id = None
                    
                    if supplier_name:
                        # 기존 공급업체 찾기 또는 생성
                        supplier = db.query(Supplier).filter(Supplier.name == supplier_name).first()
                        if not supplier:
                            supplier = Supplier(name=supplier_name)
                            db.add(supplier)
                            db.flush()
                        supplier_id = supplier.id
                    
                    # 기존 식자재 확인
                    existing_ingredient = db.query(Ingredient).filter(Ingredient.name == ingredient_name).first()
                    
                    if existing_ingredient:
                        # 기존 식자재 업데이트
                        existing_ingredient.code = ingredient_code or existing_ingredient.code
                        existing_ingredient.specification = specification or existing_ingredient.specification
                        existing_ingredient.base_unit = base_unit
                        existing_ingredient.category = category or existing_ingredient.category
                        existing_ingredient.subcategory = subcategory or existing_ingredient.subcategory
                        existing_ingredient.storage_method = storage_method or existing_ingredient.storage_method
                        existing_ingredient.weight = weight or existing_ingredient.weight
                        existing_ingredient.weight_unit = weight_unit or existing_ingredient.weight_unit
                        existing_ingredient.notes = notes or existing_ingredient.notes
                        
                        if price is not None:
                            existing_ingredient.price = price
                        if supplier_id is not None:
                            existing_ingredient.supplier_id = supplier_id
                        existing_ingredient.updated_at = datetime.now()
                    else:
                        # 새 식자재 생성
                        new_ingredient = Ingredient(
                            name=ingredient_name,
                            code=ingredient_code,
                            specification=specification,
                            base_unit=base_unit,
                            price=price,
                            supplier_id=supplier_id,
                            category=category,
                            subcategory=subcategory,
                            storage_method=storage_method,
                            weight=weight,
                            weight_unit=weight_unit,
                            notes=notes
                        )
                        db.add(new_ingredient)
                    
                    processed_count += 1
                    
                except Exception as row_error:
                    error_count += 1
                    error_details.append(f"행 {index + 2}: {str(row_error)}")
                    continue
            
            # 변경사항 저장
            db.commit()
            
            return {
                "success": True,
                "message": "식자재 업로드 완료",
                "processed_count": processed_count,
                "error_count": error_count,
                "details": {
                    "errors": error_details[:10]  # 최대 10개 오류만 반환
                }
            }
            
        except Exception as process_error:
            db.rollback()
            return {
                "success": False,
                "message": f"파일 처리 중 오류 발생: {str(process_error)}"
            }
        
        finally:
            # 임시 파일 삭제
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        print(f"[ERROR] 식자재 업로드 실패: {e}")
        raise HTTPException(status_code=500, detail="식자재 업로드 실패")

@app.post("/api/admin/sites/{site_id}/move")
async def move_site(site_id: int, move_data: SiteMoveRequest, db: Session = Depends(get_db)):
    """사업장을 다른 부모 하위로 이동"""
    try:
        # 이동할 사업장 조회
        site = db.query(Customer).filter(Customer.id == site_id).first()
        if not site:
            return {"success": False, "message": "이동할 사업장을 찾을 수 없습니다"}
        
        # 새 부모 사업장 조회
        new_parent = db.query(Customer).filter(Customer.id == move_data.new_parent_id).first()
        if not new_parent:
            return {"success": False, "message": "새 부모 사업장을 찾을 수 없습니다"}
        
        # 이동 규칙 검증
        if site.site_type == 'head':
            return {"success": False, "message": "헤드 사업장은 이동할 수 없습니다"}
        
        if site.site_type == 'detail' and new_parent.site_type != 'head':
            return {"success": False, "message": "세부 사업장은 헤드 사업장 하위로만 이동 가능합니다"}
        
        if site.site_type == 'period' and new_parent.site_type != 'detail':
            return {"success": False, "message": "기간별 사업장은 세부 사업장 하위로만 이동 가능합니다"}
        
        # 순환 참조 검증 (자신의 하위로 이동하는 것 방지)
        def is_descendant(parent_id, target_id):
            """target_id가 parent_id의 하위에 있는지 확인"""
            children = db.query(Customer).filter(Customer.parent_id == parent_id).all()
            for child in children:
                if child.id == target_id:
                    return True
                if is_descendant(child.id, target_id):
                    return True
            return False
        
        if is_descendant(site.id, move_data.new_parent_id):
            return {"success": False, "message": "자신의 하위 사업장으로는 이동할 수 없습니다"}
        
        # 레벨 계산
        new_level = new_parent.level + 1
        
        # 사업장 이동
        old_parent_name = site.parent.name if site.parent else "없음"
        site.parent_id = move_data.new_parent_id
        site.level = new_level
        
        # 하위 사업장들의 레벨도 재조정
        def update_children_level(parent_id, base_level):
            """하위 사업장들의 레벨 재조정"""
            children = db.query(Customer).filter(Customer.parent_id == parent_id).all()
            for child in children:
                child.level = base_level + 1
                update_children_level(child.id, child.level)
        
        update_children_level(site.id, site.level)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"'{site.name}'이(가) '{old_parent_name}'에서 '{new_parent.name}' 하위로 성공적으로 이동되었습니다"
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"사업장 이동 중 오류가 발생했습니다: {str(e)}"}

def getSiteTypeDisplay(site_type: str) -> str:
    """사업장 유형 표시명 반환"""
    type_map = {
        'head': '헤드 사업장',
        'detail': '세부 사업장',
        'period': '기간별 사업장'
    }
    return type_map.get(site_type, site_type)

@app.get("/suppliers/{supplier_id}/ingredients")
async def get_supplier_ingredients(supplier_id: int, db: Session = Depends(get_db)):
    """특정 공급업체의 식재료 목록 조회"""
    try:
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="공급업체를 찾을 수 없습니다")
        
        result = db.execute(
            text("""
            SELECT i.name, si.unit_price, si.unit, si.ingredient_code, si.origin
            FROM supplier_ingredients si
            JOIN ingredients i ON si.ingredient_id = i.id
            WHERE si.supplier_id = :supplier_id AND si.unit_price > 0
            ORDER BY i.name
            LIMIT 100
            """),
            {"supplier_id": supplier_id}
        )
        
        ingredients = [
            {
                "name": row[0],
                "unit_price": float(row[1]),
                "unit": row[2],
                "code": row[3],
                "origin": row[4]
            } for row in result
        ]
        
        return {
            "success": True,
            "supplier": {"id": supplier.id, "name": supplier.name},
            "ingredients": ingredients,
            "total_count": len(ingredients)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== 식수 관리 API =====

@app.get("/api/admin/meal-counts")
async def get_meal_counts(request: Request, db: Session = Depends(get_db)):
    """식수 등록 목록 조회"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        meal_counts = db.query(MealCount).order_by(
            MealCount.registration_date.desc(),
            MealCount.delivery_site,
            MealCount.meal_type
        ).all()
        
        # 그룹화된 데이터 생성
        grouped_data = {}
        for mc in meal_counts:
            key = f"{mc.delivery_site}_{mc.meal_type}"
            if key not in grouped_data:
                grouped_data[key] = {
                    "delivery_site": mc.delivery_site,
                    "meal_type": mc.meal_type,
                    "target_material_cost": mc.target_material_cost,
                    "sites": []
                }
            
            grouped_data[key]["sites"].append({
                "id": mc.id,
                "site_name": mc.site_name,
                "meal_count": mc.meal_count,
                "registration_date": mc.registration_date.isoformat()
            })
        
        # 총합 계산
        total_meal_count = sum(mc.meal_count for mc in meal_counts)
        avg_cost = sum(float(mc.target_material_cost or 0) for mc in meal_counts) / len(meal_counts) if meal_counts else 0
        delivery_sites = len(set(mc.delivery_site for mc in meal_counts))
        
        return {
            "success": True,
            "data": list(grouped_data.values()),
            "summary": {
                "total_meal_count": total_meal_count,
                "average_cost": round(avg_cost, 2),
                "delivery_sites": delivery_sites
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/meal-counts")
async def create_meal_count(meal_count_data: MealCountCreate, request: Request, db: Session = Depends(get_db)):
    """새 식수 등록"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        # 날짜 파싱
        registration_date = datetime.strptime(meal_count_data.registration_date, "%Y-%m-%d").date()
        
        # 새 식수 등록 생성
        new_meal_count = MealCount(
            delivery_site=meal_count_data.delivery_site,
            meal_type=meal_count_data.meal_type,
            target_material_cost=meal_count_data.target_material_cost,
            site_name=meal_count_data.site_name,
            meal_count=meal_count_data.meal_count,
            registration_date=registration_date
        )
        
        db.add(new_meal_count)
        db.commit()
        db.refresh(new_meal_count)
        
        return {
            "success": True,
            "message": "식수가 성공적으로 등록되었습니다.",
            "data": {
                "id": new_meal_count.id,
                "delivery_site": new_meal_count.delivery_site,
                "meal_type": new_meal_count.meal_type,
                "target_material_cost": new_meal_count.target_material_cost,
                "site_name": new_meal_count.site_name,
                "meal_count": new_meal_count.meal_count,
                "registration_date": new_meal_count.registration_date.isoformat()
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="잘못된 날짜 형식입니다. YYYY-MM-DD 형식을 사용하세요.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/meal-counts/{meal_count_id}")
async def get_meal_count(meal_count_id: int, request: Request, db: Session = Depends(get_db)):
    """특정 식수 등록 조회"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    meal_count = db.query(MealCount).filter(MealCount.id == meal_count_id).first()
    if not meal_count:
        raise HTTPException(status_code=404, detail="식수 등록을 찾을 수 없습니다.")
    
    return {
        "success": True,
        "data": {
            "id": meal_count.id,
            "delivery_site": meal_count.delivery_site,
            "meal_type": meal_count.meal_type,
            "target_material_cost": meal_count.target_material_cost,
            "site_name": meal_count.site_name,
            "meal_count": meal_count.meal_count,
            "registration_date": meal_count.registration_date.isoformat()
        }
    }

@app.put("/api/admin/meal-counts/{meal_count_id}")
async def update_meal_count(meal_count_id: int, meal_count_data: MealCountUpdate, request: Request, db: Session = Depends(get_db)):
    """식수 등록 수정"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        meal_count = db.query(MealCount).filter(MealCount.id == meal_count_id).first()
        if not meal_count:
            raise HTTPException(status_code=404, detail="식수 등록을 찾을 수 없습니다.")
        
        # 월말 삭제 제한 확인 (현재 달의 마지막 3일)
        today = datetime.now().date()
        last_day_of_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        if today >= last_day_of_month - timedelta(days=2):  # 마지막 3일
            raise HTTPException(status_code=400, detail="월말 3일간은 식수 등록을 수정할 수 없습니다.")
        
        # 업데이트할 필드들
        if meal_count_data.delivery_site is not None:
            meal_count.delivery_site = meal_count_data.delivery_site
        if meal_count_data.meal_type is not None:
            meal_count.meal_type = meal_count_data.meal_type
        if meal_count_data.target_material_cost is not None:
            meal_count.target_material_cost = meal_count_data.target_material_cost
        if meal_count_data.site_name is not None:
            meal_count.site_name = meal_count_data.site_name
        if meal_count_data.meal_count is not None:
            meal_count.meal_count = meal_count_data.meal_count
        if meal_count_data.registration_date is not None:
            meal_count.registration_date = datetime.strptime(meal_count_data.registration_date, "%Y-%m-%d").date()
        
        db.commit()
        db.refresh(meal_count)
        
        return {
            "success": True,
            "message": "식수 등록이 성공적으로 수정되었습니다.",
            "data": {
                "id": meal_count.id,
                "delivery_site": meal_count.delivery_site,
                "meal_type": meal_count.meal_type,
                "target_material_cost": meal_count.target_material_cost,
                "site_name": meal_count.site_name,
                "meal_count": meal_count.meal_count,
                "registration_date": meal_count.registration_date.isoformat()
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="잘못된 날짜 형식입니다. YYYY-MM-DD 형식을 사용하세요.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/meal-counts/{meal_count_id}")
async def delete_meal_count(meal_count_id: int, request: Request, db: Session = Depends(get_db)):
    """식수 등록 삭제"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        meal_count = db.query(MealCount).filter(MealCount.id == meal_count_id).first()
        if not meal_count:
            raise HTTPException(status_code=404, detail="식수 등록을 찾을 수 없습니다.")
        
        # 월말 삭제 제한 확인 (현재 달의 마지막 3일)
        today = datetime.now().date()
        last_day_of_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        if today >= last_day_of_month - timedelta(days=2):  # 마지막 3일
            raise HTTPException(status_code=400, detail="월말 3일간은 식수 등록을 삭제할 수 없습니다.")
        
        db.delete(meal_count)
        db.commit()
        
        return {
            "success": True,
            "message": "식수 등록이 성공적으로 삭제되었습니다."
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ===== 15일 타임라인 식수 관리 API =====

@app.get("/api/meal-counts/timeline")
async def get_meal_counts_timeline(tab: str, start_date: str, end_date: str, db: Session = Depends(get_db)):
    """15일 타임라인 식수 데이터 조회 - 인증 불필요"""
    try:
        # 날짜 파싱
        start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # 타임라인 데이터 조회
        timeline_data = db.query(MealCountTimeline).filter(
            MealCountTimeline.tab_type == tab,
            MealCountTimeline.target_date >= start_dt,
            MealCountTimeline.target_date <= end_dt
        ).order_by(
            MealCountTimeline.meal_category,
            MealCountTimeline.site_name,
            MealCountTimeline.target_date
        ).all()
        
        # 데이터 구조화
        structured_data = {}
        for record in timeline_data:
            category = record.meal_category
            site = record.site_name
            date_str = record.target_date.strftime("%Y-%m-%d")
            
            if category not in structured_data:
                structured_data[category] = {}
            if site not in structured_data[category]:
                structured_data[category][site] = {}
            
            structured_data[category][site][date_str] = {
                'id': record.id,
                'meal_count': record.meal_count,
                'is_confirmed': record.is_confirmed,
                'target_material_cost': record.target_material_cost,
                'notes': record.notes
            }
        
        return {
            "success": True,
            "data": structured_data,
            "period": {
                "start_date": start_date,
                "end_date": end_date,
                "tab": tab
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="잘못된 날짜 형식입니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/meal-counts/templates/{tab_type}")
async def get_meal_count_templates(tab_type: str, db: Session = Depends(get_db)):
    """식수 템플릿 조회 - 인증 불필요"""
    try:
        templates = db.query(MealCountTemplate).filter(
            MealCountTemplate.tab_type == tab_type,
            MealCountTemplate.is_active == True
        ).order_by(
            MealCountTemplate.display_order,
            MealCountTemplate.meal_category,
            MealCountTemplate.site_name
        ).all()
        
        # 구조화
        structured_templates = {}
        for template in templates:
            category = template.meal_category
            if category not in structured_templates:
                structured_templates[category] = []
            
            structured_templates[category].append({
                'site_name': template.site_name,
                'default_count': template.default_count
            })
        
        return {
            "success": True,
            "data": structured_templates,
            "tab_type": tab_type
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/meal-counts/timeline/save")
async def save_meal_count_timeline(
    save_data: dict, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """타임라인 식수 데이터 저장 - 인증 필요"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    
    try:
        tab = save_data.get('tab')
        category = save_data.get('category')
        site = save_data.get('site')
        date_str = save_data.get('date')
        meal_count = save_data.get('meal_count', 0)
        
        # 날짜 파싱
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # 기존 데이터 확인
        existing = db.query(MealCountTimeline).filter(
            MealCountTimeline.tab_type == tab,
            MealCountTimeline.meal_category == category,
            MealCountTimeline.site_name == site,
            MealCountTimeline.target_date == target_date
        ).first()
        
        if existing:
            # 업데이트
            existing.meal_count = meal_count
            existing.updated_at = datetime.now()
        else:
            # 신규 생성
            new_record = MealCountTimeline(
                tab_type=tab,
                meal_category=category,
                site_name=site,
                meal_count=meal_count,
                target_date=target_date,
                is_confirmed=False
            )
            db.add(new_record)
        
        db.commit()
        
        return {
            "success": True,
            "message": "저장되었습니다."
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail="잘못된 데이터 형식입니다.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# 발주 관리 API
# ==============================================================================

class PurchaseOrderCreate(BaseModel):
    order_number: str
    order_date: str
    delivery_date: str
    lead_days: int = 3
    total_meals: Optional[int] = None
    reference_meal_plan: Optional[str] = None
    order_time: Optional[str] = None
    order_type: str = "manual"
    notes: Optional[str] = None
    items: List[dict]

@app.post("/api/purchase-orders")
async def create_purchase_order(order_data: PurchaseOrderCreate, db: Session = Depends(get_db)):
    """발주서 생성"""
    try:
        # 발주서 생성
        purchase_order = PurchaseOrder(
            order_number=order_data.order_number,
            order_date=datetime.strptime(order_data.order_date, '%Y-%m-%d').date(),
            delivery_date=datetime.strptime(order_data.delivery_date, '%Y-%m-%d').date(),
            lead_days=order_data.lead_days,
            total_meals=order_data.total_meals,
            reference_meal_plan=order_data.reference_meal_plan,
            order_time=order_data.order_time,
            order_type=OrderTypeEnum.manual if order_data.order_type == "manual" else OrderTypeEnum.auto,
            notes=order_data.notes,
            created_by=1  # 임시로 1번 사용자
        )
        
        db.add(purchase_order)
        db.flush()  # ID 생성을 위해 flush
        
        # 발주 품목들 생성
        total_amount = 0
        for item_data in order_data.items:
            amount = float(item_data.get('quantity', 0)) * float(item_data.get('unitPrice', 0))
            total_amount += amount
            
            order_item = PurchaseOrderItem(
                order_id=purchase_order.id,
                category=item_data.get('category'),
                code=item_data.get('code'),
                name=item_data.get('name'),
                supplier=item_data.get('supplier'),
                origin=item_data.get('origin'),
                unit=item_data.get('unit'),
                current_stock=float(item_data.get('currentStock', 0)) if item_data.get('currentStock') else 0,
                quantity=float(item_data.get('quantity', 0)),
                unit_price=float(item_data.get('unitPrice', 0)),
                amount=amount,
                lead_time=int(item_data.get('leadTime', 3)),
                meal_plan_ref=item_data.get('mealPlanRef'),
                notes=item_data.get('notes')
            )
            db.add(order_item)
        
        # 총 금액 업데이트
        purchase_order.total_amount = total_amount
        
        # 거래처별 입고 기록 생성
        suppliers = {}
        for item_data in order_data.items:
            supplier = item_data.get('supplier')
            if supplier and supplier not in suppliers:
                # 예상 입고일 계산 (발주일 + 선발주일)
                order_date = datetime.strptime(order_data.order_date, '%Y-%m-%d').date()
                expected_date = order_date + timedelta(days=order_data.lead_days)
                
                receiving_record = ReceivingRecord(
                    order_id=purchase_order.id,
                    supplier=supplier,
                    expected_date=expected_date,
                    status=ReceivingStatusEnum.pending
                )
                db.add(receiving_record)
                suppliers[supplier] = receiving_record
        
        db.flush()
        
        # 입고 품목들 생성
        for item_data in order_data.items:
            supplier = item_data.get('supplier')
            if supplier and supplier in suppliers:
                receiving_item = ReceivingItem(
                    receiving_record_id=suppliers[supplier].id,
                    order_item_id=0,  # 나중에 업데이트
                    name=item_data.get('name'),
                    ordered_quantity=float(item_data.get('quantity', 0)),
                    unit=item_data.get('unit'),
                    unit_price=float(item_data.get('unitPrice', 0)),
                    amount=float(item_data.get('quantity', 0)) * float(item_data.get('unitPrice', 0))
                )
                db.add(receiving_item)
        
        # 입고 기록 총계 업데이트
        for supplier, receiving_record in suppliers.items():
            supplier_items = [item for item in order_data.items if item.get('supplier') == supplier]
            receiving_record.total_items = len(supplier_items)
            receiving_record.total_amount = sum(
                float(item.get('quantity', 0)) * float(item.get('unitPrice', 0)) 
                for item in supplier_items
            )
        
        db.commit()
        
        return {
            "success": True,
            "message": "발주서가 성공적으로 저장되었습니다.",
            "order_id": purchase_order.id,
            "order_number": purchase_order.order_number
        }
        
    except Exception as e:
        db.rollback()
        print(f"발주서 저장 오류: {e}")
        raise HTTPException(status_code=500, detail=f"발주서 저장 중 오류가 발생했습니다: {str(e)}")

@app.get("/api/receiving-records")
async def get_receiving_records(
    expected_date: Optional[str] = None,
    supplier: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """입고 기록 조회"""
    try:
        query = """
            SELECT 
                rr.id, rr.order_id, rr.supplier, rr.expected_date, rr.actual_date,
                rr.status, rr.total_items, rr.received_items, rr.total_amount,
                po.order_date, po.order_number, po.lead_days
            FROM receiving_records rr
            JOIN purchase_orders po ON rr.order_id = po.id
            WHERE 1=1
        """
        
        params = {}
        if expected_date:
            query += " AND rr.expected_date = :expected_date"
            params['expected_date'] = expected_date
        
        if supplier:
            query += " AND rr.supplier = :supplier"
            params['supplier'] = supplier
            
        if status:
            query += " AND rr.status = :status"
            params['status'] = status
        
        query += " ORDER BY rr.expected_date DESC, rr.supplier"
        
        result = db.execute(text(query), params)
        
        receiving_records = []
        for row in result:
            # 해당 입고 기록의 품목들 조회
            items_query = """
                SELECT ri.id, ri.name, ri.ordered_quantity, ri.received_quantity, 
                       ri.unit, ri.unit_price, ri.amount, ri.received
                FROM receiving_items ri
                WHERE ri.receiving_record_id = :receiving_id
                ORDER BY ri.name
            """
            items_result = db.execute(text(items_query), {"receiving_id": row[0]})
            
            items = []
            for item_row in items_result:
                items.append({
                    "id": item_row[0],
                    "name": item_row[1],
                    "ordered_quantity": float(item_row[2]) if item_row[2] else 0,
                    "received_quantity": float(item_row[3]) if item_row[3] else 0,
                    "unit": item_row[4],
                    "unit_price": float(item_row[5]) if item_row[5] else 0,
                    "amount": float(item_row[6]) if item_row[6] else 0,
                    "received": bool(item_row[7])
                })
            
            receiving_records.append({
                "id": row[0],
                "order_id": row[1],
                "supplier": row[2],
                "expected_date": str(row[3]) if row[3] else None,
                "actual_date": str(row[4]) if row[4] else None,
                "status": row[5],
                "total_items": row[6] or 0,
                "received_items": row[7] or 0,
                "total_amount": float(row[8]) if row[8] else 0,
                "order_date": str(row[9]) if row[9] else None,
                "order_number": row[10],
                "lead_days": row[11] or 3,
                "items": items
            })
        
        return {
            "success": True,
            "data": receiving_records
        }
        
    except Exception as e:
        print(f"입고 기록 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/receiving-items/{item_id}/receive")
async def update_receiving_item(item_id: int, received: dict, db: Session = Depends(get_db)):
    """입고 품목 상태 업데이트"""
    try:
        is_received = received.get('received', False)
        
        # 입고 품목 업데이트
        update_query = """
            UPDATE receiving_items 
            SET received = :received, 
                received_at = :received_at,
                updated_at = :updated_at
            WHERE id = :item_id
        """
        
        received_at = datetime.now() if is_received else None
        db.execute(text(update_query), {
            "received": is_received,
            "received_at": received_at,
            "updated_at": datetime.now(),
            "item_id": item_id
        })
        
        # 입고 기록의 입고완료 품목수 업데이트
        update_record_query = """
            UPDATE receiving_records 
            SET received_items = (
                SELECT COUNT(*) 
                FROM receiving_items 
                WHERE receiving_record_id = receiving_records.id AND received = true
            ),
            updated_at = :updated_at
            WHERE id = (
                SELECT receiving_record_id 
                FROM receiving_items 
                WHERE id = :item_id
            )
        """
        
        db.execute(text(update_record_query), {
            "updated_at": datetime.now(),
            "item_id": item_id
        })
        
        db.commit()
        
        return {
            "success": True,
            "message": "입고 상태가 업데이트되었습니다."
        }
        
    except Exception as e:
        db.rollback()
        print(f"입고 상태 업데이트 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 전처리 지시서 API ====================

@app.get("/api/meal-plan-ingredients/{plan_date}")
async def get_meal_plan_ingredients(plan_date: str, meal_type: Optional[str] = None, db: Session = Depends(get_db)):
    """특정 날짜 식단표에서 모든 식자재 추출"""
    try:
        # 쿼리 작성: 식단표 -> 메뉴 -> 메뉴아이템 -> 레시피 -> 식자재
        query = """
            SELECT DISTINCT
                ri.ingredient_id,
                i.name as ingredient_name,
                SUM(ri.quantity * mi.portion_num_persons) as total_quantity,
                ri.unit,
                i.base_unit,
                m.menu_type,
                dp.date as plan_date
            FROM diet_plans dp
            JOIN menus m ON dp.id = m.diet_plan_id
            JOIN menu_items mi ON m.id = mi.menu_id
            JOIN recipes r ON mi.recipe_id = r.id
            JOIN recipe_ingredients ri ON r.id = ri.recipe_id
            JOIN ingredients i ON ri.ingredient_id = i.id
            WHERE DATE(dp.date) = :plan_date
        """
        
        params = {"plan_date": plan_date}
        
        if meal_type:
            query += " AND m.menu_type = :meal_type"
            params["meal_type"] = meal_type
            
        query += """
            GROUP BY ri.ingredient_id, i.name, ri.unit, i.base_unit, m.menu_type, dp.date
            ORDER BY m.menu_type, i.name
        """
        
        result = db.execute(text(query), params)
        rows = result.fetchall()
        
        # 끼니별로 그룹화
        ingredients_by_meal = {}
        for row in rows:
            meal_type = row[5]  # menu_type
            if meal_type not in ingredients_by_meal:
                ingredients_by_meal[meal_type] = []
                
            ingredients_by_meal[meal_type].append({
                "ingredient_id": row[0],
                "ingredient_name": row[1],
                "total_quantity": float(row[2]) if row[2] else 0,
                "unit": row[3],
                "base_unit": row[4],
                "meal_type": meal_type
            })
        
        return {
            "success": True,
            "date": plan_date,
            "ingredients_by_meal": ingredients_by_meal,
            "total_ingredients": sum(len(ingredients) for ingredients in ingredients_by_meal.values())
        }
        
    except Exception as e:
        print(f"식단표 식자재 추출 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/preprocessing-master")
async def get_preprocessing_master(db: Session = Depends(get_db)):
    """전처리 필요 식자재 마스터 목록"""
    try:
        query = """
            SELECT 
                id, ingredient_name, preprocessing_method, estimated_time,
                priority, safety_notes, storage_condition, tools_required,
                is_active
            FROM preprocessing_master
            WHERE is_active = true
            ORDER BY priority ASC, ingredient_name ASC
        """
        
        result = db.execute(text(query))
        rows = result.fetchall()
        
        preprocessing_master = []
        for row in rows:
            preprocessing_master.append({
                "id": row[0],
                "ingredient_name": row[1],
                "preprocessing_method": row[2],
                "estimated_time": row[3],
                "priority": row[4],
                "safety_notes": row[5],
                "storage_condition": row[6],
                "tools_required": row[7],
                "is_active": bool(row[8])
            })
        
        return {
            "success": True,
            "data": preprocessing_master
        }
        
    except Exception as e:
        print(f"전처리 마스터 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class PreprocessingInstructionCreate(BaseModel):
    instruction_date: date
    meal_type: str
    diet_plan_id: Optional[int] = None
    notes: Optional[str] = None
    items: List[dict]

@app.post("/api/preprocessing-instructions")
async def create_preprocessing_instruction(instruction: PreprocessingInstructionCreate, db: Session = Depends(get_db)):
    """전처리 지시서 생성"""
    try:
        # 전처리 지시서 생성
        insert_instruction_query = """
            INSERT INTO preprocessing_instructions 
            (instruction_date, meal_type, diet_plan_id, status, total_items, notes, created_by, created_at, updated_at)
            VALUES (:instruction_date, :meal_type, :diet_plan_id, 'pending', :total_items, :notes, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        
        result = db.execute(text(insert_instruction_query), {
            "instruction_date": instruction.instruction_date,
            "meal_type": instruction.meal_type,
            "diet_plan_id": instruction.diet_plan_id,
            "total_items": len(instruction.items),
            "notes": instruction.notes
        })
        
        # 생성된 지시서 ID 가져오기
        instruction_id = result.lastrowid
        
        # 지시서 항목들 생성
        for item in instruction.items:
            insert_item_query = """
                INSERT INTO preprocessing_instruction_items
                (instruction_id, ingredient_name, quantity, unit, preprocessing_method, 
                 estimated_time, priority, notes, created_at, updated_at)
                VALUES (:instruction_id, :ingredient_name, :quantity, :unit, :preprocessing_method,
                        :estimated_time, :priority, :notes, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            
            db.execute(text(insert_item_query), {
                "instruction_id": instruction_id,
                "ingredient_name": item.get("ingredient_name"),
                "quantity": item.get("quantity", 0),
                "unit": item.get("unit", ""),
                "preprocessing_method": item.get("preprocessing_method", ""),
                "estimated_time": item.get("estimated_time", 0),
                "priority": item.get("priority", 5),
                "notes": item.get("notes", "")
            })
        
        db.commit()
        
        return {
            "success": True,
            "instruction_id": instruction_id,
            "message": "전처리 지시서가 생성되었습니다."
        }
        
    except Exception as e:
        db.rollback()
        print(f"전처리 지시서 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/preprocessing-instructions")
async def get_preprocessing_instructions(
    instruction_date: Optional[str] = None,
    meal_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """전처리 지시서 목록 조회"""
    try:
        query = """
            SELECT 
                pi.id, pi.instruction_date, pi.meal_type, pi.status,
                pi.total_items, pi.completed_items, pi.notes,
                dp.description as diet_plan_description
            FROM preprocessing_instructions pi
            LEFT JOIN diet_plans dp ON pi.diet_plan_id = dp.id
            WHERE 1=1
        """
        
        params = {}
        
        if instruction_date:
            query += " AND DATE(pi.instruction_date) = :instruction_date"
            params["instruction_date"] = instruction_date
            
        if meal_type:
            query += " AND pi.meal_type = :meal_type"
            params["meal_type"] = meal_type
            
        query += " ORDER BY pi.instruction_date DESC, pi.meal_type"
        
        result = db.execute(text(query), params)
        rows = result.fetchall()
        
        instructions = []
        for row in rows:
            instructions.append({
                "id": row[0],
                "instruction_date": str(row[1]) if row[1] else None,
                "meal_type": row[2],
                "status": row[3],
                "total_items": row[4] or 0,
                "completed_items": row[5] or 0,
                "notes": row[6],
                "diet_plan_description": row[7]
            })
        
        return {
            "success": True,
            "data": instructions
        }
        
    except Exception as e:
        print(f"전처리 지시서 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/preprocessing-instructions/{instruction_id}")
async def get_preprocessing_instruction_detail(instruction_id: int, db: Session = Depends(get_db)):
    """전처리 지시서 상세 조회"""
    try:
        # 지시서 기본 정보
        instruction_query = """
            SELECT 
                pi.id, pi.instruction_date, pi.meal_type, pi.status,
                pi.total_items, pi.completed_items, pi.notes,
                dp.description as diet_plan_description
            FROM preprocessing_instructions pi
            LEFT JOIN diet_plans dp ON pi.diet_plan_id = dp.id
            WHERE pi.id = :instruction_id
        """
        
        instruction_result = db.execute(text(instruction_query), {"instruction_id": instruction_id})
        instruction_row = instruction_result.fetchone()
        
        if not instruction_row:
            raise HTTPException(status_code=404, detail="전처리 지시서를 찾을 수 없습니다.")
        
        # 지시서 항목들
        items_query = """
            SELECT 
                id, ingredient_name, quantity, unit, preprocessing_method,
                estimated_time, priority, is_completed, completed_at, notes
            FROM preprocessing_instruction_items
            WHERE instruction_id = :instruction_id
            ORDER BY priority ASC, ingredient_name ASC
        """
        
        items_result = db.execute(text(items_query), {"instruction_id": instruction_id})
        items_rows = items_result.fetchall()
        
        items = []
        for row in items_rows:
            items.append({
                "id": row[0],
                "ingredient_name": row[1],
                "quantity": float(row[2]) if row[2] else 0,
                "unit": row[3],
                "preprocessing_method": row[4],
                "estimated_time": row[5],
                "priority": row[6],
                "is_completed": bool(row[7]),
                "completed_at": str(row[8]) if row[8] else None,
                "notes": row[9]
            })
        
        instruction_detail = {
            "id": instruction_row[0],
            "instruction_date": str(instruction_row[1]) if instruction_row[1] else None,
            "meal_type": instruction_row[2],
            "status": instruction_row[3],
            "total_items": instruction_row[4] or 0,
            "completed_items": instruction_row[5] or 0,
            "notes": instruction_row[6],
            "diet_plan_description": instruction_row[7],
            "items": items
        }
        
        return {
            "success": True,
            "data": instruction_detail
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"전처리 지시서 상세 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create_preprocessing_master_data")
async def create_preprocessing_master_data(db: Session = Depends(get_db)):
    """전처리 마스터 데이터 샘플 생성"""
    try:
        # 기존 데이터 삭제
        db.execute(text("DELETE FROM preprocessing_master WHERE id > 0"))
        
        # 전처리 마스터 샘플 데이터
        preprocessing_samples = [
            {
                "ingredient_name": "감자",
                "preprocessing_method": "껍질 제거 후 적당한 크기로 썰기\n1. 흐르는 물에 깨끗이 세척\n2. 필러로 껍질 제거\n3. 요리법에 따라 크기 조절하여 썰기\n4. 찬물에 담가 전분 제거",
                "estimated_time": 15,
                "priority": 3,
                "safety_notes": "칼 사용 시 손가락 주의, 미끄러운 감자 조심",
                "storage_condition": "처리 후 찬물에 보관, 변색 방지",
                "tools_required": "칼, 도마, 필러, 볼"
            },
            {
                "ingredient_name": "양파",
                "preprocessing_method": "껍질 제거 후 용도에 맞게 썰기\n1. 겉껍질과 뿌리 부분 제거\n2. 반으로 자른 후 채썰기 또는 다이스컷\n3. 물에 담가 매운맛 제거 (선택사항)",
                "estimated_time": 10,
                "priority": 2,
                "safety_notes": "양파 자를 때 눈물 주의, 환기 필요",
                "storage_condition": "밀폐용기에 냉장보관",
                "tools_required": "칼, 도마, 볼"
            },
            {
                "ingredient_name": "당근",
                "preprocessing_method": "세척 후 껍질 제거하여 썰기\n1. 흐르는 물에 깨끗이 세척\n2. 필러로 껍질 제거\n3. 용도에 맞게 채썰기, 다이스컷, 또는 어슷썰기",
                "estimated_time": 12,
                "priority": 3,
                "safety_notes": "딱딱한 당근 썰 때 칼날 미끄러짐 주의",
                "storage_condition": "처리 후 밀폐용기에 냉장보관",
                "tools_required": "칼, 도마, 필러"
            },
            {
                "ingredient_name": "대파",
                "preprocessing_method": "뿌리와 시든 부분 제거 후 썰기\n1. 뿌리 부분과 시든 겉껍질 제거\n2. 흐르는 물에 깨끗이 세척\n3. 용도에 맞게 송송 썰기 또는 어슷썰기",
                "estimated_time": 8,
                "priority": 1,
                "safety_notes": "미끄러운 대파 썰 때 손가락 주의",
                "storage_condition": "키친타올로 물기 제거 후 보관",
                "tools_required": "칼, 도마"
            },
            {
                "ingredient_name": "마늘",
                "preprocessing_method": "껍질 제거 후 다지기 또는 썰기\n1. 마늘 껍질 제거\n2. 밑둥 부분 제거\n3. 용도에 맞게 편썰기, 다지기, 또는 통으로 사용",
                "estimated_time": 20,
                "priority": 2,
                "safety_notes": "작은 마늘 다질 때 손가락 주의",
                "storage_condition": "밀폐용기에 냉장보관, 기름에 절여 보관 가능",
                "tools_required": "칼, 도마, 마늘 압착기(선택)"
            },
            {
                "ingredient_name": "생강",
                "preprocessing_method": "껍질 제거 후 채썰기 또는 다지기\n1. 숟가락으로 껍질 제거\n2. 섬유질 방향과 수직으로 썰기\n3. 용도에 맞게 채썰기 또는 다지기",
                "estimated_time": 15,
                "priority": 4,
                "safety_notes": "딱딱한 생강 썰 때 칼날 미끄러짐 주의",
                "storage_condition": "밀폐용기에 냉장보관",
                "tools_required": "칼, 도마, 숟가락"
            },
            {
                "ingredient_name": "배추",
                "preprocessing_method": "세척 후 적당한 크기로 썰기\n1. 겉잎 제거 후 세척\n2. 밑동 부분 제거\n3. 용도에 맞게 썰기 (김치용, 국물용 등)",
                "estimated_time": 25,
                "priority": 3,
                "safety_notes": "큰 칼 사용 시 안전 주의",
                "storage_condition": "찬물에 담가 보관, 소금물 절임",
                "tools_required": "큰 칼, 도마, 큰 볼"
            },
            {
                "ingredient_name": "무",
                "preprocessing_method": "껍질 제거 후 용도에 맞게 썰기\n1. 껍질 제거 및 세척\n2. 용도에 맞게 채썰기, 깍둑썰기, 또는 큰 덩어리로 썰기",
                "estimated_time": 18,
                "priority": 3,
                "safety_notes": "딱딱한 무 썰 때 칼날 안전 주의",
                "storage_condition": "찬물에 담가 보관",
                "tools_required": "칼, 도마, 필러"
            },
            {
                "ingredient_name": "호박",
                "preprocessing_method": "세척 후 씨 제거하여 썰기\n1. 겉면 세척\n2. 반으로 자른 후 씨와 속 제거\n3. 껍질 제거 후 적당한 크기로 썰기",
                "estimated_time": 20,
                "priority": 3,
                "safety_notes": "딱딱한 호박 자를 때 칼날 안전 주의",
                "storage_condition": "처리 후 냉장보관",
                "tools_required": "큰 칼, 도마, 스푼"
            },
            {
                "ingredient_name": "버섯",
                "preprocessing_method": "밑동 제거 후 세척하여 썰기\n1. 밑동 부분 제거\n2. 키친타올로 이물질 제거 (물 세척 최소화)\n3. 용도에 맞게 썰기",
                "estimated_time": 10,
                "priority": 2,
                "safety_notes": "미끄러운 버섯 썰 때 주의",
                "storage_condition": "키친타올로 감싸 냉장보관",
                "tools_required": "칼, 도마, 키친타올"
            }
        ]
        
        for sample in preprocessing_samples:
            insert_query = """
                INSERT INTO preprocessing_master 
                (ingredient_name, preprocessing_method, estimated_time, priority, 
                 safety_notes, storage_condition, tools_required, is_active, created_at, updated_at)
                VALUES (:ingredient_name, :preprocessing_method, :estimated_time, :priority,
                        :safety_notes, :storage_condition, :tools_required, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
            
            db.execute(text(insert_query), sample)
        
        db.commit()
        return {
            "success": True,
            "message": f"{len(preprocessing_samples)}개의 전처리 마스터 데이터가 생성되었습니다."
        }
        
    except Exception as e:
        db.rollback()
        print(f"전처리 마스터 데이터 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/create_test_meal_data")
async def create_test_meal_data(db: Session = Depends(get_db)):
    """전처리 시스템 테스트용 식단표 및 메뉴 데이터 생성"""
    try:
        from datetime import date, timedelta
        
        # 1. 테스트 식자재 생성
        test_ingredients = [
            {"name": "돼지고기", "base_unit": "kg"},
            {"name": "양파", "base_unit": "kg"},
            {"name": "당근", "base_unit": "kg"},
            {"name": "감자", "base_unit": "kg"},
            {"name": "배추", "base_unit": "kg"},
            {"name": "대파", "base_unit": "kg"},
            {"name": "마늘", "base_unit": "kg"},
            {"name": "생강", "base_unit": "kg"},
            {"name": "토마토", "base_unit": "kg"},
            {"name": "브로콜리", "base_unit": "kg"}
        ]
        
        for ingredient_data in test_ingredients:
            existing = db.query(Ingredient).filter(Ingredient.name == ingredient_data["name"]).first()
            if not existing:
                ingredient = Ingredient(
                    name=ingredient_data["name"],
                    base_unit=ingredient_data["base_unit"],
                    code=f"I{len(db.query(Ingredient).all()) + 1:04d}",
                    category="테스트용"
                )
                db.add(ingredient)
        
        db.commit()
        
        # 2. 테스트 메뉴 및 레시피 생성
        test_menus = [
            {
                "name": "김치찌개",
                "category": "찌개류",
                "menu_type": "중식",
                "ingredients": [
                    {"name": "돼지고기", "quantity": 0.5, "unit": "kg"},
                    {"name": "배추", "quantity": 1.0, "unit": "kg"},
                    {"name": "양파", "quantity": 0.3, "unit": "kg"},
                    {"name": "대파", "quantity": 0.2, "unit": "kg"}
                ]
            },
            {
                "name": "돼지갈비찜",
                "category": "찜류", 
                "menu_type": "석식",
                "ingredients": [
                    {"name": "돼지고기", "quantity": 1.2, "unit": "kg"},
                    {"name": "당근", "quantity": 0.4, "unit": "kg"},
                    {"name": "양파", "quantity": 0.5, "unit": "kg"},
                    {"name": "마늘", "quantity": 0.1, "unit": "kg"}
                ]
            },
            {
                "name": "야채볶음",
                "category": "볶음류",
                "menu_type": "조식", 
                "ingredients": [
                    {"name": "브로콜리", "quantity": 0.8, "unit": "kg"},
                    {"name": "당근", "quantity": 0.3, "unit": "kg"},
                    {"name": "양파", "quantity": 0.2, "unit": "kg"},
                    {"name": "마늘", "quantity": 0.05, "unit": "kg"}
                ]
            }
        ]
        
        menu_ids = []
        for menu_data in test_menus:
            # 메뉴 생성
            menu = Menu(
                name=menu_data["name"],
                category=menu_data["category"],
                description=f"테스트용 {menu_data['name']}",
                version="1.0"
            )
            db.add(menu)
            db.flush()
            
            # 레시피 생성
            recipe = Recipe(
                menu_id=menu.id,
                name=f"{menu_data['name']} 레시피",
                description=f"{menu_data['name']} 조리법",
                cooking_time=30,
                portion_size=10
            )
            db.add(recipe)
            db.flush()
            
            # 레시피 재료 추가
            for ingredient_data in menu_data["ingredients"]:
                ingredient = db.query(Ingredient).filter(Ingredient.name == ingredient_data["name"]).first()
                if ingredient:
                    recipe_ingredient = RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient.id,
                        quantity=ingredient_data["quantity"],
                        unit=ingredient_data["unit"]
                    )
                    db.add(recipe_ingredient)
            
            menu_ids.append(menu.id)
        
        db.commit()
        
        # 3. 테스트 식단표 생성 (오늘 날짜)
        today = date.today()
        
        # 기존 식단표 확인
        existing_plan = db.query(DietPlan).filter(DietPlan.date == today).first()
        if existing_plan:
            db.delete(existing_plan)
            db.commit()
        
        # 새 식단표 생성
        diet_plan = DietPlan(
            date=today,
            meal_count_breakfast=50,
            meal_count_lunch=80,
            meal_count_dinner=60,
            meal_count_late_night=20,
            description="테스트용 식단표"
        )
        db.add(diet_plan)
        db.flush()
        
        # 식단표에 메뉴 배정
        for i, menu_id in enumerate(menu_ids):
            menu = db.query(Menu).filter(Menu.id == menu_id).first()
            if menu:
                diet_menu = Menu(
                    diet_plan_id=diet_plan.id,
                    name=menu.name,
                    category=menu.category,
                    menu_type=test_menus[i]["menu_type"],
                    description=menu.description
                )
                db.add(diet_menu)
                db.flush()
                
                # 메뉴 아이템 추가
                recipe = db.query(Recipe).filter(Recipe.menu_id == menu_id).first()
                if recipe:
                    menu_item = MenuItem(
                        menu_id=diet_menu.id,
                        recipe_id=recipe.id,
                        portion_num_persons=50  # 기본 50인분
                    )
                    db.add(menu_item)
        
        db.commit()
        
        return {
            "success": True,
            "message": f"테스트 데이터가 생성되었습니다 (날짜: {today})",
            "data": {
                "date": str(today),
                "menus_created": len(test_menus),
                "ingredients_created": len(test_ingredients)
            }
        }
        
    except Exception as e:
        db.rollback()
        print(f"테스트 데이터 생성 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 공급업체 관리 시스템 확장 API
# ==========================================

# init_supplier_extensions 함수 제거 - 테이블 스키마가 이미 완성됨


# 이전 중복된 API 제거됨 - 아래쪽의 더 간단한 버전 사용

@app.post("/api/admin/suppliers/create")
async def create_supplier(supplier_data: dict, request: Request, db: Session = Depends(get_db)):
    """새 공급업체 등록"""
    user = get_current_user(request)
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        query = """
            INSERT INTO suppliers 
            (name, parent_code, business_number, business_type, business_item, 
             representative, headquarters_address, headquarters_phone, headquarters_fax, 
             email, website, is_active, company_scale, notes, created_at, updated_at)
            VALUES 
            (:name, :parent_code, :business_number, :business_type, :business_item,
             :representative, :headquarters_address, :headquarters_phone, :headquarters_fax,
             :email, :website, :is_active, :company_scale, :notes,
             CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """
        
        params = {
            'name': supplier_data.get('name', ''),
            'parent_code': supplier_data.get('parent_code', ''),
            'business_number': supplier_data.get('business_number', ''),
            'business_type': supplier_data.get('business_type', ''),
            'business_item': supplier_data.get('business_item', ''),
            'representative': supplier_data.get('representative', ''),
            'headquarters_address': supplier_data.get('headquarters_address', ''),
            'headquarters_phone': supplier_data.get('headquarters_phone', ''),
            'headquarters_fax': supplier_data.get('headquarters_fax', ''),
            'email': supplier_data.get('email', ''),
            'website': supplier_data.get('website', ''),
            'is_active': supplier_data.get('is_active', True),
            'company_scale': supplier_data.get('company_scale', ''),
            'notes': supplier_data.get('notes', '')
        }
        
        db.execute(text(query), params)
        db.commit()
        
        return {"success": True, "message": "공급업체가 등록되었습니다."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"공급업체 등록 실패: {str(e)}")

@app.put("/api/admin/suppliers/{supplier_id}/update")
async def update_supplier(supplier_id: int, supplier_data: dict, request: Request, db: Session = Depends(get_db)):
    """공급업체 정보 수정"""
    user = get_current_user(request)
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        update_fields = []
        params = {"supplier_id": supplier_id}
        
        # 업데이트할 필드들 (실제 테이블 구조에 맞춤)
        updatable_fields = {
            'name': 'name',
            'parent_code': 'parent_code', 
            'business_number': 'business_number',
            'business_type': 'business_type',
            'business_item': 'business_item',
            'representative': 'representative',
            'headquarters_address': 'headquarters_address',
            'headquarters_phone': 'headquarters_phone', 
            'headquarters_fax': 'headquarters_fax',
            'email': 'email',
            'website': 'website',
            'is_active': 'is_active',
            'company_scale': 'company_scale',
            'notes': 'notes'
        }
        
        for key, db_field in updatable_fields.items():
            if key in supplier_data:
                update_fields.append(f"{db_field} = :{key}")
                params[key] = supplier_data[key]
        
# Debug logs removed
        
        if update_fields:
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f"""
                UPDATE suppliers 
                SET {', '.join(update_fields)}
                WHERE id = :supplier_id
            """
            
            db.execute(text(query), params)
            db.commit()
        
        return {"success": True, "message": "공급업체 정보가 업데이트되었습니다."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"공급업체 정보 수정 실패: {str(e)}")

@app.delete("/api/admin/suppliers/{supplier_id}/delete")
async def delete_supplier(supplier_id: int, request: Request, db: Session = Depends(get_db)):
    """공급업체 삭제"""
    user = get_current_user(request)
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        # 공급업체와 연관된 식자재가 있는지 확인
        ingredient_count = db.execute(text("""
            SELECT COUNT(*) FROM ingredients WHERE supplier_id = :supplier_id
        """), {"supplier_id": supplier_id}).scalar()
        
        if ingredient_count > 0:
            return {"success": False, "message": f"이 공급업체와 연관된 식자재가 {ingredient_count}개 있어 삭제할 수 없습니다."}
        
        db.execute(text("DELETE FROM suppliers WHERE id = :supplier_id"), {"supplier_id": supplier_id})
        db.commit()
        
        return {"success": True, "message": "공급업체가 삭제되었습니다."}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"공급업체 삭제 실패: {str(e)}")

@app.get("/api/admin/suppliers/enhanced")
async def get_suppliers_enhanced(
    request: Request, 
    page: int = 1, 
    limit: int = 20,
    search: str = '',
    status: str = '',
    db: Session = Depends(get_db)
):
    """공급업체 목록 조회 (페이지네이션 및 검색 지원)"""
    user = get_current_user(request)
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        # 기본 쿼리
        base_query = """
            SELECT id, parent_code, name, headquarters_phone, email, 
                   is_active, business_number, representative, notes, 
                   created_at, updated_at
            FROM suppliers
            WHERE 1=1
        """
        
        count_query = "SELECT COUNT(*) FROM suppliers WHERE 1=1"
        params = {}
        
        # 검색 조건 추가
        if search:
            search_condition = """
                AND (name LIKE :search OR headquarters_phone LIKE :search OR email LIKE :search 
                     OR representative LIKE :search OR business_number LIKE :search)
            """
            base_query += search_condition
            count_query += search_condition
            params['search'] = f'%{search}%'
        
        # 상태 필터
        if status:
            status_condition = " AND is_active = :status"
            base_query += status_condition
            count_query += status_condition
            params['status'] = int(status)
        
        # 총 개수 조회
        total_count = db.execute(text(count_query), params).scalar()
        total_pages = (total_count + limit - 1) // limit
        
        # 페이지네이션 적용
        offset = (page - 1) * limit
        base_query += " ORDER BY name, created_at DESC LIMIT :limit OFFSET :offset"
        params.update({'limit': limit, 'offset': offset})
        
        # 데이터 조회
        result = db.execute(text(base_query), params).fetchall()
        
        suppliers = []
        for row in result:
            supplier_dict = dict(row._mapping)
            suppliers.append(supplier_dict)
        
        return {
            "success": True,
            "suppliers": suppliers,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
                "limit": limit
            }
        }
        
    except Exception as e:
        print(f"[ERROR] 공급업체 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"공급업체 목록 조회 실패: {str(e)}")

@app.get("/api/admin/suppliers/{supplier_id}/detail")
async def get_supplier_detail(
    supplier_id: int, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """공급업체 상세정보 조회"""
    user = get_current_user(request)
    if not user or user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        query = """
            SELECT * FROM suppliers WHERE id = :supplier_id
        """
        result = db.execute(text(query), {"supplier_id": supplier_id}).fetchone()
        
        if not result:
            return {"success": False, "message": "공급업체를 찾을 수 없습니다."}
        
        supplier = dict(result._mapping)
        
        return {
            "success": True,
            "supplier": supplier
        }
        
    except Exception as e:
        print(f"[ERROR] 공급업체 상세정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=f"공급업체 상세정보 조회 실패: {str(e)}")

def create_default_meal_plans(db: Session, customer_id: int, customer_name: str) -> int:
    """사업장 생성 시 기본 식단표를 자동으로 생성하는 함수"""
    from datetime import date, timedelta
    
    try:
        created_count = 0
        today = date.today()
        
        # 향후 7일간의 기본 식단표 생성
        for i in range(7):
            target_date = today + timedelta(days=i)
            
            # 해당 날짜에 대한 DietPlan 생성 또는 기존 것 사용
            diet_plan = db.query(DietPlan).filter(
                DietPlan.date == target_date,
                DietPlan.category == "기본"
            ).first()
            
            if not diet_plan:
                diet_plan = DietPlan(
                    category="기본",
                    date=target_date,
                    description=f"{customer_name} - {target_date.strftime('%Y-%m-%d')} 기본 식단"
                )
                db.add(diet_plan)
                db.flush()  # ID 생성을 위해
            
            # 각 끼니별 메뉴 생성 (조식, 중식, 석식)
            meal_types = ["조식", "중식", "석식"]
            for meal_type in meal_types:
                # 기존 메뉴가 있는지 확인
                existing_menu = db.query(Menu).filter(
                    Menu.diet_plan_id == diet_plan.id,
                    Menu.menu_type == meal_type
                ).first()
                
                if not existing_menu:
                    new_menu = Menu(
                        diet_plan_id=diet_plan.id,
                        menu_type=meal_type,
                        target_num_persons=50,  # 기본값
                        target_food_cost=3000.00,  # 기본값
                        evaluation_score=80
                    )
                    db.add(new_menu)
                    db.flush()  # ID 생성을 위해
                    
                    # 사업장과 메뉴 연결 (CustomerMenu)
                    customer_menu = CustomerMenu(
                        customer_id=customer_id,
                        menu_id=new_menu.id,
                        customer_num_persons=50,
                        assigned_date=target_date
                    )
                    db.add(customer_menu)
                    created_count += 1
        
        db.commit()
        return created_count
        
    except Exception as e:
        db.rollback()
        print(f"기본 식단표 생성 중 오류: {e}")
        return 0

# ==============================================================================
# 단가관리 API 엔드포인트
# ==============================================================================

@app.get("/api/customers")
async def get_customers(db: Session = Depends(get_db)):
    """사업장 목록 조회 (단가관리용)"""
    try:
        customers = db.query(Customer).order_by(Customer.sort_order).all()
        
        customer_list = []
        for customer in customers:
            customer_list.append({
                "id": customer.id,
                "name": customer.name,
                "site_type": customer.site_type
            })
        
        return customer_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/diet-plans")
async def get_diet_plans(customer_id: int = None, db: Session = Depends(get_db)):
    """식단표 목록 조회 (단가관리용)"""
    try:
        query = db.query(DietPlan).join(Customer)
        
        if customer_id:
            query = query.filter(DietPlan.customer_id == customer_id)
        
        diet_plans = query.order_by(DietPlan.date).all()
        
        diet_plan_list = []
        for plan in diet_plans:
            # 식단 유형은 사업장의 site_type을 사용
            meal_type = plan.customer.site_type or "기타"
            
            diet_plan_list.append({
                "id": plan.id,
                "customer_id": plan.customer_id,
                "customer_name": plan.customer.name,
                "date": plan.date.isoformat(),
                "meal_type": meal_type,
                "breakfast_menu": plan.breakfast_menu,
                "lunch_menu": plan.lunch_menu,
                "dinner_menu": plan.dinner_menu
            })
        
        return diet_plan_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =============================
# Customer-Supplier Mapping API
# =============================

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

@app.get("/api/admin/customer-supplier-mappings")
async def get_customer_supplier_mappings(db: Session = Depends(get_db)):
    """사업장-협력업체 매핑 목록 조회"""
    try:
        mappings = db.query(CustomerSupplierMapping).all()
        
        mapping_list = []
        for mapping in mappings:
            mapping_list.append({
                "id": mapping.id,
                "customer_id": mapping.customer_id,
                "supplier_id": mapping.supplier_id,
                "delivery_code": mapping.delivery_code,
                "priority": mapping.priority_order,
                "is_primary": mapping.is_primary_supplier,
                "contract_start_date": mapping.contract_start_date.isoformat() if mapping.contract_start_date else None,
                "contract_end_date": mapping.contract_end_date.isoformat() if mapping.contract_end_date else None,
                "notes": mapping.notes,
                "is_active": mapping.is_active,
                "created_at": mapping.created_at.isoformat() if mapping.created_at else None,
                "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None
            })
        
        return {"success": True, "mappings": mapping_list}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.post("/api/admin/customer-supplier-mappings")  
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
            
            # 사업장과 협력업체 존재 확인
            customer_result = conn.execute(text("SELECT COUNT(*) FROM customers WHERE id = :customer_id"), {"customer_id": mapping_data.customer_id}).fetchone()
            if customer_result[0] == 0:
                return {"success": False, "message": "존재하지 않는 사업장입니다."}
            
            supplier_result = conn.execute(text("SELECT COUNT(*) FROM suppliers WHERE id = :supplier_id"), {"supplier_id": mapping_data.supplier_id}).fetchone()
            if supplier_result[0] == 0:
                return {"success": False, "message": "존재하지 않는 협력업체입니다."}
        
        # 직접 SQL INSERT 사용
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(
                text("""INSERT INTO customer_supplier_mappings 
                    (customer_id, supplier_id, delivery_code, priority_order, is_primary_supplier, 
                     contract_start_date, contract_end_date, notes, is_active, created_at, updated_at)
                    VALUES (:customer_id, :supplier_id, :delivery_code, :priority_order, :is_primary_supplier,
                            :contract_start_date, :contract_end_date, :notes, :is_active, :created_at, :updated_at)"""),
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

@app.put("/api/admin/customer-supplier-mappings/{mapping_id}")
async def update_customer_supplier_mapping(mapping_id: int, mapping_data: CustomerSupplierMappingUpdate, db: Session = Depends(get_db)):
    """사업장-협력업체 매핑 수정"""
    try:
        mapping = db.query(CustomerSupplierMapping).filter(CustomerSupplierMapping.id == mapping_id).first()
        if not mapping:
            return {"success": False, "message": "존재하지 않는 매핑입니다."}
        
        # 업데이트할 필드만 수정
        if mapping_data.customer_id is not None:
            # 사업장 존재 확인
            customer_result = db.execute(text("SELECT COUNT(*) FROM customers WHERE id = :customer_id"), {"customer_id": mapping_data.customer_id}).fetchone()
            if customer_result[0] == 0:
                return {"success": False, "message": "존재하지 않는 사업장입니다."}
            mapping.customer_id = mapping_data.customer_id
        
        if mapping_data.supplier_id is not None:
            # 협력업체 존재 확인
            supplier_result = db.execute(text("SELECT COUNT(*) FROM suppliers WHERE id = :supplier_id"), {"supplier_id": mapping_data.supplier_id}).fetchone()
            if supplier_result[0] == 0:
                return {"success": False, "message": "존재하지 않는 협력업체입니다."}
            mapping.supplier_id = mapping_data.supplier_id
        
        if mapping_data.delivery_code is not None:
            mapping.delivery_code = mapping_data.delivery_code
        if mapping_data.priority_order is not None:
            mapping.priority_order = mapping_data.priority_order
        if mapping_data.is_primary_supplier is not None:
            mapping.is_primary_supplier = mapping_data.is_primary_supplier
        if mapping_data.contract_start_date is not None:
            mapping.contract_start_date = mapping_data.contract_start_date
        if mapping_data.contract_end_date is not None:
            mapping.contract_end_date = mapping_data.contract_end_date
        if mapping_data.notes is not None:
            mapping.notes = mapping_data.notes
        if mapping_data.is_active is not None:
            mapping.is_active = mapping_data.is_active
        
        mapping.updated_at = datetime.now()
        
        db.commit()
        
        return {"success": True, "message": "매핑이 수정되었습니다."}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/customer-supplier-mappings/{mapping_id}")
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

@app.delete("/api/admin/customers/{customer_id}/supplier-mappings")
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
            
        return {"success": True, "message": f"고객 {customer_id}의 모든 매핑이 삭제되었습니다.", "deleted_count": result.rowcount}
    except Exception as e:
        return {"success": False, "message": str(e)}

@app.get("/api/admin/customer-supplier-mappings/{mapping_id}")
async def get_customer_supplier_mapping(mapping_id: int, db: Session = Depends(get_db)):
    """특정 사업장-협력업체 매핑 조회"""
    try:
        mapping = db.query(CustomerSupplierMapping).filter(CustomerSupplierMapping.id == mapping_id).first()
        if not mapping:
            return {"success": False, "message": "존재하지 않는 매핑입니다."}
        
        return {
            "success": True,
            "mapping": {
                "id": mapping.id,
                "customer_id": mapping.customer_id,
                "supplier_id": mapping.supplier_id,
                "delivery_code": mapping.delivery_code,
                "priority": mapping.priority_order,
                "is_primary": mapping.is_primary_supplier,
                "contract_start_date": mapping.contract_start_date.isoformat() if mapping.contract_start_date else None,
                "contract_end_date": mapping.contract_end_date.isoformat() if mapping.contract_end_date else None,
                "notes": mapping.notes,
                "is_active": mapping.is_active,
                "created_at": mapping.created_at.isoformat() if mapping.created_at else None,
                "updated_at": mapping.updated_at.isoformat() if mapping.updated_at else None
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

# ==============================================================================
# 사업장 관리 API 엔드포인트
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

@app.get("/api/admin/customers")
async def get_customers_admin(
    request: Request,
    page: int = 1, 
    limit: int = 20, 
    search: str = "", 
    db: Session = Depends(get_db)
):
    """사업장 목록 조회 (관리자용, 페이지네이션 포함)"""
    # 인증 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        query = db.query(Customer)
        
        if search:
            query = query.filter(Customer.name.contains(search))
        
        total = query.count()
        
        customers = query.order_by(Customer.sort_order, Customer.name).offset((page - 1) * limit).limit(limit).all()
        
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

@app.post("/api/admin/customers/create")
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
        print(f"[DEBUG] Creating customer with data: {customer_data.dict()}")
        
        # 중복 검사
        if customer_data.code:
            existing = db.query(Customer).filter(Customer.code == customer_data.code).first()
            if existing:
                print(f"[DEBUG] Duplicate code found: {customer_data.code}")
                return {"success": False, "message": "이미 존재하는 사업장 코드입니다."}
        
        customer = Customer(
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
        
        print(f"[DEBUG] Customer object created: {customer.name}")
        
        db.add(customer)
        print(f"[DEBUG] Customer added to session")
        db.commit()
        print(f"[DEBUG] Database commit completed")
        db.refresh(customer)
        print(f"[DEBUG] Customer refreshed, ID: {customer.id}")
        
        return {
            "success": True, 
            "message": "사업장이 성공적으로 등록되었습니다.",
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "code": customer.code,
                "site_type": customer.site_type
            }
        }
    except Exception as e:
        print(f"[DEBUG] Exception in create_customer: {str(e)}")
        print(f"[DEBUG] Exception type: {type(e)}")
        db.rollback()
        return {"success": False, "message": str(e)}

@app.get("/api/admin/customers/{customer_id}/detail")
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
            return {"success": False, "message": "사업장을 찾을 수 없습니다."}
        
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

@app.put("/api/admin/customers/{customer_id}/update")
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
            return {"success": False, "message": "사업장을 찾을 수 없습니다."}
        
        # 업데이트할 필드만 수정
        for field, value in customer_data.dict(exclude_unset=True).items():
            setattr(customer, field, value)
        
        db.commit()
        db.refresh(customer)
        
        return {"success": True, "message": "사업장 정보가 성공적으로 수정되었습니다."}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

@app.delete("/api/admin/customers/{customer_id}/delete")
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
            return {"success": False, "message": "사업장을 찾을 수 없습니다."}
        
        # 연관된 데이터 확인 (식단표, 매핑 등)
        related_data = db.query(DietPlan).filter(DietPlan.customer_id == customer_id).count()
        if related_data > 0:
            return {"success": False, "message": "연관된 데이터가 있어 삭제할 수 없습니다. 먼저 관련 데이터를 삭제해주세요."}
        
        db.delete(customer)
        db.commit()
        
        return {"success": True, "message": "사업장이 성공적으로 삭제되었습니다."}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

@app.post("/api/admin/meal-pricing")
async def save_meal_pricing(request: Request, meal_pricing_data: dict, db: Session = Depends(get_db)):
    """식단가 정보 저장"""
    # 인증 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        meal_plan_type = meal_pricing_data.get('meal_plan_type')
        pricing_data = meal_pricing_data.get('pricing_data', [])
        
        print(f"식단가 정보 저장 요청:")
        print(f"- 식단표 타입: {meal_plan_type}")
        print(f"- 세부식단표 개수: {len(pricing_data)}")
        
        saved_count = 0
        
        for plan in pricing_data:
            location_id = plan.get('location_id')
            location_name = plan.get('location_name', '')
            meal_type = plan.get('meal_type', '')
            plan_name = plan.get('plan_name', '')
            selling_price = float(plan.get('selling_price', 0))
            material_cost = float(plan.get('material_cost_guideline', 0))
            
            # 값이 0인 데이터는 스킵
            if selling_price == 0 and material_cost == 0:
                continue
            
            # 적용 날짜 처리
            apply_date_start = plan.get('apply_date_start')
            apply_date_end = plan.get('apply_date_end')
            
            if apply_date_start:
                try:
                    apply_date_start = datetime.strptime(apply_date_start, '%Y-%m-%d').date()
                except:
                    apply_date_start = date.today()
            else:
                apply_date_start = date.today()
                
            if apply_date_end:
                try:
                    apply_date_end = datetime.strptime(apply_date_end, '%Y-%m-%d').date()
                except:
                    apply_date_end = None
            else:
                apply_date_end = None
            
            # 재료비 비율 계산
            cost_ratio = round((material_cost / selling_price) * 100, 2) if selling_price > 0 else 0
            
            # 기존 데이터 확인 (같은 사업장, 식단표 타입, 끼니, 명칭, 적용일로)
            existing = db.query(MealPricing).filter(
                MealPricing.location_id == location_id,
                MealPricing.meal_plan_type == meal_plan_type,
                MealPricing.meal_type == meal_type,
                MealPricing.plan_name == plan_name,
                MealPricing.apply_date_start == apply_date_start
            ).first()
            
            if existing:
                # 기존 데이터 업데이트
                existing.selling_price = selling_price
                existing.material_cost_guideline = material_cost
                existing.cost_ratio = cost_ratio
                existing.apply_date_end = apply_date_end
                existing.updated_at = datetime.now()
                print(f"  업데이트: {meal_type} {plan_name} - 판매가: {selling_price}원, 재료비: {material_cost}원")
            else:
                # 새 데이터 생성
                try:
                    new_pricing = MealPricing(
                        location_id=location_id,
                        location_name=location_name,
                        meal_plan_type=meal_plan_type,
                        meal_type=meal_type,
                        plan_name=plan_name,
                        apply_date_start=apply_date_start,
                        apply_date_end=apply_date_end,
                        selling_price=selling_price,
                        material_cost_guideline=material_cost,
                        cost_ratio=cost_ratio
                    )
                    db.add(new_pricing)
                    db.flush()  # 즉시 DB에 반영하여 ID 확인
                    print(f"  생성: {meal_type} {plan_name} - 판매가: {selling_price}원, 재료비: {material_cost}원 (ID: {new_pricing.id})")
                except Exception as e:
                    print(f"  생성 오류: {e}")
                    continue
            
            saved_count += 1
        
        # 데이터베이스 커밋
        db.commit()
        
        return {
            "success": True, 
            "message": f"식단가 정보가 성공적으로 저장되었습니다. (총 {saved_count}개 항목)",
            "saved_data": {
                "meal_plan_type": meal_plan_type,
                "pricing_count": saved_count
            }
        }
        
    except Exception as e:
        db.rollback()
        print(f"식단가 저장 오류: {str(e)}")
        return {"success": False, "message": f"저장 중 오류가 발생했습니다: {str(e)}"}

@app.get("/api/admin/meal-pricing")
async def get_meal_pricing(request: Request, location_id: int = None, meal_plan_type: str = None, db: Session = Depends(get_db)):
    """식단가 정보 조회"""
    # 인증 확인
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        query = db.query(MealPricing).filter(MealPricing.is_active == True)
        
        if location_id:
            query = query.filter(MealPricing.location_id == location_id)
            
        if meal_plan_type:
            query = query.filter(MealPricing.meal_plan_type == meal_plan_type)
        
        # 적용일 순서로 정렬
        pricing_records = query.order_by(MealPricing.apply_date_start.desc()).all()
        
        # 결과 포맷팅
        result = []
        for record in pricing_records:
            result.append({
                "id": record.id,
                "location_id": record.location_id,
                "location_name": record.location_name,
                "meal_plan_type": record.meal_plan_type,
                "meal_type": record.meal_type,
                "plan_name": record.plan_name,
                "apply_date_start": record.apply_date_start.isoformat() if record.apply_date_start else None,
                "apply_date_end": record.apply_date_end.isoformat() if record.apply_date_end else None,
                "selling_price": float(record.selling_price),
                "material_cost_guideline": float(record.material_cost_guideline),
                "cost_ratio": float(record.cost_ratio),
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None
            })
        
        return {
            "success": True,
            "pricing_records": result,
            "total_count": len(result)
        }
        
    except Exception as e:
        print(f"식단가 조회 오류: {str(e)}")
        return {"success": False, "message": f"조회 중 오류가 발생했습니다: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
# Force reload
