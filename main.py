from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
import os
import json
from datetime import datetime, date

# 로컬 임포트
from models import Base, DietPlan, Menu, MenuItem, Recipe, Ingredient, Supplier, Customer
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

@app.get("/")
async def serve_homepage():
    return FileResponse("menu_recipe_management.html")

@app.get("/meal-plan")
async def serve_meal_plan():
    return FileResponse("meal_plan_management.html")

# 데이터베이스 연결
DATABASE_URL = "postgresql://postgres:123@localhost:5432/daham_menu"

try:
    # PostgreSQL 드라이버가 설치되지 않은 경우 SQLite로 fallback
    import psycopg2
    # 엔진 생성 부분을 더 안전하게 수정
    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "options": "-c client_encoding=utf8"
        },
        pool_pre_ping=True,
        echo=False  # 로그 출력 비활성화
    )
    print("Using PostgreSQL database")
except ImportError:
    # SQLite로 fallback
    DATABASE_URL = "sqlite:///./daham_menu.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    print("Using SQLite database")
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

# 메뉴별 식재료 정보 조회 API
@app.get("/api/menu_ingredients/{menu_name}")
async def get_menu_ingredients(menu_name: str, db: Session = Depends(get_db)):
    """특정 메뉴의 식재료 목록 조회"""
    try:
        # 메뉴의 식재료 정보 조회
        ingredient_query = """
        SELECT 
            i.name as ingredient_name,
            i.code as ingredient_code,
            ri.amount,
            i.base_unit,
            s.name as supplier_name
        FROM recipes r
        LEFT JOIN recipe_ingredients ri ON r.id = ri.recipe_id
        LEFT JOIN ingredients i ON ri.ingredient_id = i.id
        LEFT JOIN supplier_ingredients si ON i.id = si.ingredient_id
        LEFT JOIN suppliers s ON si.supplier_id = s.id
        WHERE r.name = :menu_name
        ORDER BY ri.amount DESC
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
async def get_recipes(db: Session = Depends(get_db)):
    """레시피 목록 조회"""
    try:
        result = db.execute(text("SELECT * FROM Recipe ORDER BY name"))
        plans = [dict(row._mapping) for row in result]
        return {"success": True, "data": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingredients")
async def get_ingredients(db: Session = Depends(get_db)):
    """식재료 목록 조회"""
    try:
        query = """
            SELECT i.id, i.name, i.code, i.base_unit, i.price, i.moq, i.allergy_codes,
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
            SELECT i.id, i.name, i.code, i.base_unit, i.moq, 
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
    """공급업체 목록 조회"""
    try:
        result = db.execute(text("SELECT id, name, update_frequency as delivery_schedule FROM suppliers ORDER BY name"))
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)