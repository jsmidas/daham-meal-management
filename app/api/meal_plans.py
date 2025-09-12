"""
식단 관리 API 라우터
- 식단표(diet plans) CRUD
- 메뉴 관리
- 메뉴 항목 관리
- 레시피 관리
- 메뉴 원가 계산
- 식단 관련 계산 기능
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
import json

# 로컬 임포트
from app.database import get_db, DATABASE_URL
from app.api.auth import get_current_user
from models import (
    DietPlan, Menu, MenuItem, Recipe, Ingredient, Customer, 
    CustomerMenu, Supplier
)
from business_logic import MenuCalculator, NutritionCalculator, CostAnalyzer

router = APIRouter()

# ==============================================================================
# Pydantic 모델 정의
# ==============================================================================

class DietPlanCreate(BaseModel):
    customer_id: int
    date: date
    meal_type: str
    menu_ids: List[int]
    notes: Optional[str] = None

class DietPlanResponse(BaseModel):
    success: bool
    diet_plan_id: int
    message: str

class MenuCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    recipe_ids: List[int]

class MenuResponse(BaseModel):
    success: bool
    menu_id: int
    message: str

class MenuItemCreate(BaseModel):
    menu_id: int
    ingredient_id: int
    quantity: Decimal
    unit: str
    notes: Optional[str] = None

class MenuItemResponse(BaseModel):
    success: bool
    menu_item_id: int
    message: str

class RecipeCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    ingredients: List[Dict[str, Any]]
    instructions: Optional[str] = None
    servings: int
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None

class MenuCostRequest(BaseModel):
    menu_ids: List[int]
    servings: int

class RequirementCalculationRequest(BaseModel):
    menu_ids: List[int]
    servings: int
    date: date

class RequirementCalculationResponse(BaseModel):
    success: bool
    requirements: List[Dict[str, Any]]
    total_cost: Decimal
    message: str

class BulkReplaceRequest(BaseModel):
    old_ingredient_id: int
    new_ingredient_id: int
    menu_ids: List[int]

# ==============================================================================
# 페이지 서빙
# ==============================================================================

@router.get("/diet-plans")
async def serve_diet_plans():
    """식단표 페이지"""
    return FileResponse("diet_plans.html")

@router.get("/recipes")
async def serve_recipes():
    """레시피 페이지"""
    return FileResponse("recipes.html")

@router.get("/cooking")
async def serve_cooking():
    """조리 페이지"""
    return FileResponse("cooking_instruction_management.html")

@router.get("/portion")
async def serve_portion():
    """분할 페이지"""
    return FileResponse("portion_instruction_management.html")

# ==============================================================================
# 식단표 API
# ==============================================================================

@router.get("/api/diet-plans")
async def get_diet_plans(customer_id: int = Query(None), db: Session = Depends(get_db)):
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
                "description": plan.description
            })
        
        return {"success": True, "diet_plans": diet_plan_list}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/diet-plans", response_model=DietPlanResponse)
async def create_diet_plan(diet_plan_data: DietPlanCreate, db: Session = Depends(get_db)):
    """식단표 생성"""
    try:
        # 새 식단표 생성
        new_diet_plan = DietPlan(
            customer_id=diet_plan_data.customer_id,
            date=diet_plan_data.date,
            meal_type=diet_plan_data.meal_type,
            notes=diet_plan_data.notes,
            created_at=datetime.now()
        )
        
        db.add(new_diet_plan)
        db.commit()
        db.refresh(new_diet_plan)
        
        # 메뉴 연결 (CustomerMenu 테이블 사용)
        for menu_id in diet_plan_data.menu_ids:
            customer_menu = CustomerMenu(
                customer_id=diet_plan_data.customer_id,
                menu_id=menu_id,
                diet_plan_id=new_diet_plan.id,
                created_at=datetime.now()
            )
            db.add(customer_menu)
        
        db.commit()
        
        return DietPlanResponse(
            success=True,
            diet_plan_id=new_diet_plan.id,
            message="식단표가 성공적으로 생성되었습니다."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/menus/{diet_plan_id}")
async def get_menus_by_diet_plan(diet_plan_id: int, db: Session = Depends(get_db)):
    """특정 식단표의 메뉴 목록 조회"""
    try:
        # 식단표 확인
        diet_plan = db.query(DietPlan).filter(DietPlan.id == diet_plan_id).first()
        if not diet_plan:
            raise HTTPException(status_code=404, detail="식단표를 찾을 수 없습니다.")
        
        # 식단표에 연결된 메뉴들 조회
        menus = db.query(Menu).join(CustomerMenu).filter(
            CustomerMenu.diet_plan_id == diet_plan_id
        ).all()
        
        menu_list = []
        for menu in menus:
            menu_list.append({
                "id": menu.id,
                "name": menu.name,
                "category": menu.category,
                "description": menu.description,
                "created_at": menu.created_at.isoformat() if menu.created_at else None
            })
        
        return {"success": True, "menus": menu_list}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ==============================================================================
# 메뉴 API
# ==============================================================================

@router.post("/menus", response_model=MenuResponse)
async def create_menu(menu_data: MenuCreate, db: Session = Depends(get_db)):
    """메뉴 생성"""
    try:
        new_menu = Menu(
            name=menu_data.name,
            category=menu_data.category,
            description=menu_data.description,
            created_at=datetime.now()
        )
        
        db.add(new_menu)
        db.commit()
        db.refresh(new_menu)
        
        # 레시피 연결 (Menu-Recipe 관계 테이블이 있다면)
        # TODO: Menu-Recipe 관계 처리
        
        return MenuResponse(
            success=True,
            menu_id=new_menu.id,
            message="메뉴가 성공적으로 생성되었습니다."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/menu_ingredients/{menu_name}")
async def get_menu_ingredients(menu_name: str, db: Session = Depends(get_db)):
    """메뉴별 식재료 목록 조회"""
    try:
        # 메뉴 조회
        menu = db.query(Menu).filter(Menu.name == menu_name).first()
        if not menu:
            return {"success": False, "message": "메뉴를 찾을 수 없습니다."}
        
        # 메뉴 아이템들 조회
        menu_items = db.query(MenuItem).filter(MenuItem.menu_id == menu.id).all()
        
        ingredient_list = []
        for item in menu_items:
            ingredient = db.query(Ingredient).filter(Ingredient.id == item.ingredient_id).first()
            if ingredient:
                ingredient_list.append({
                    "id": ingredient.id,
                    "name": ingredient.name,
                    "category": ingredient.category,
                    "quantity": float(item.quantity),
                    "unit": item.unit,
                    "cost_per_unit": float(ingredient.cost_per_unit) if ingredient.cost_per_unit else 0,
                    "total_cost": float(item.quantity * (ingredient.cost_per_unit or 0))
                })
        
        return {"success": True, "ingredients": ingredient_list}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/menus_ingredients")
async def save_menu_ingredients(request_data: dict, db: Session = Depends(get_db)):
    """메뉴 식재료 정보 저장"""
    try:
        menu_name = request_data.get("menu_name")
        ingredients = request_data.get("ingredients", [])
        
        # 메뉴 조회 또는 생성
        menu = db.query(Menu).filter(Menu.name == menu_name).first()
        if not menu:
            menu = Menu(
                name=menu_name,
                category="기타",
                created_at=datetime.now()
            )
            db.add(menu)
            db.commit()
            db.refresh(menu)
        
        # 기존 메뉴 아이템 삭제
        db.query(MenuItem).filter(MenuItem.menu_id == menu.id).delete()
        
        # 새로운 메뉴 아이템 추가
        for ingredient_data in ingredients:
            menu_item = MenuItem(
                menu_id=menu.id,
                ingredient_id=ingredient_data["id"],
                quantity=Decimal(str(ingredient_data["quantity"])),
                unit=ingredient_data["unit"],
                created_at=datetime.now()
            )
            db.add(menu_item)
        
        db.commit()
        
        return {"success": True, "message": "메뉴 식재료가 저장되었습니다."}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

# ==============================================================================
# 메뉴 아이템 API
# ==============================================================================

@router.post("/menu-items", response_model=MenuItemResponse)
async def create_menu_item(menu_item_data: MenuItemCreate, db: Session = Depends(get_db)):
    """메뉴 아이템 생성"""
    try:
        new_menu_item = MenuItem(
            menu_id=menu_item_data.menu_id,
            ingredient_id=menu_item_data.ingredient_id,
            quantity=menu_item_data.quantity,
            unit=menu_item_data.unit,
            notes=menu_item_data.notes,
            created_at=datetime.now()
        )
        
        db.add(new_menu_item)
        db.commit()
        db.refresh(new_menu_item)
        
        return MenuItemResponse(
            success=True,
            menu_item_id=new_menu_item.id,
            message="메뉴 아이템이 성공적으로 생성되었습니다."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/menu-items/{menu_id}")
async def get_menu_items(menu_id: int, db: Session = Depends(get_db)):
    """메뉴의 아이템 목록 조회"""
    try:
        menu = db.query(Menu).filter(Menu.id == menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail="메뉴를 찾을 수 없습니다.")
        
        menu_items = db.query(MenuItem).filter(MenuItem.menu_id == menu_id).all()
        
        item_list = []
        for item in menu_items:
            ingredient = db.query(Ingredient).filter(Ingredient.id == item.ingredient_id).first()
            item_list.append({
                "id": item.id,
                "ingredient_id": item.ingredient_id,
                "ingredient_name": ingredient.name if ingredient else "알 수 없음",
                "quantity": float(item.quantity),
                "unit": item.unit,
                "notes": item.notes,
                "created_at": item.created_at.isoformat() if item.created_at else None
            })
        
        return {"success": True, "menu_items": item_list}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ==============================================================================
# 레시피 API
# ==============================================================================

@router.get("/api/recipes")
async def get_recipes(
    category: str = Query(""),
    search: str = Query(""),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """레시피 목록 조회"""
    try:
        query = db.query(Recipe)
        
        if category:
            query = query.filter(Recipe.category == category)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(Recipe.name.ilike(search_term))
        
        recipes = query.limit(limit).all()
        
        recipe_list = []
        for recipe in recipes:
            recipe_list.append({
                "id": recipe.id,
                "name": recipe.name,
                "category": recipe.category,
                "description": recipe.description,
                "servings": recipe.servings,
                "prep_time": recipe.prep_time,
                "cook_time": recipe.cook_time,
                "created_at": recipe.created_at.isoformat() if recipe.created_at else None
            })
        
        return {"success": True, "recipes": recipe_list}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/api/recipe/{recipe_id}")
async def get_recipe_detail(recipe_id: int, db: Session = Depends(get_db)):
    """레시피 상세 정보 조회"""
    try:
        recipe = db.query(Recipe).filter(Recipe.id == recipe_id).first()
        if not recipe:
            return {"success": False, "message": "레시피를 찾을 수 없습니다."}
        
        recipe_data = {
            "id": recipe.id,
            "name": recipe.name,
            "category": recipe.category,
            "description": recipe.description,
            "servings": recipe.servings,
            "prep_time": recipe.prep_time,
            "cook_time": recipe.cook_time,
            "instructions": recipe.instructions,
            "created_at": recipe.created_at.isoformat() if recipe.created_at else None
        }
        
        return {"success": True, "recipe": recipe_data}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/search_recipes")
async def search_recipes(search_data: dict, db: Session = Depends(get_db)):
    """레시피 검색"""
    try:
        search_term = search_data.get("search_term", "")
        category = search_data.get("category", "")
        
        query = db.query(Recipe)
        
        if search_term:
            term = f"%{search_term}%"
            query = query.filter(Recipe.name.ilike(term))
        
        if category:
            query = query.filter(Recipe.category == category)
        
        recipes = query.limit(50).all()
        
        recipe_list = []
        for recipe in recipes:
            recipe_list.append({
                "id": recipe.id,
                "name": recipe.name,
                "category": recipe.category,
                "description": recipe.description,
                "servings": recipe.servings
            })
        
        return {"success": True, "recipes": recipe_list}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/init_sample_recipes")
async def init_sample_recipes(db: Session = Depends(get_db)):
    """샘플 레시피 데이터 초기화"""
    try:
        # 샘플 레시피 데이터
        sample_recipes = [
            {
                "name": "김치찌개",
                "category": "찌개류",
                "description": "한국 전통 김치찌개",
                "servings": 4,
                "prep_time": 10,
                "cook_time": 30,
                "instructions": "1. 김치를 볶는다\n2. 물을 넣고 끓인다\n3. 두부와 고기를 넣는다"
            },
            {
                "name": "된장찌개",
                "category": "찌개류",
                "description": "구수한 된장찌개",
                "servings": 4,
                "prep_time": 15,
                "cook_time": 25,
                "instructions": "1. 멸치육수를 만든다\n2. 된장을 풀어넣는다\n3. 채소를 넣고 끓인다"
            }
        ]
        
        created_count = 0
        for recipe_data in sample_recipes:
            # 중복 체크
            existing = db.query(Recipe).filter(Recipe.name == recipe_data["name"]).first()
            if not existing:
                new_recipe = Recipe(
                    name=recipe_data["name"],
                    category=recipe_data["category"],
                    description=recipe_data["description"],
                    servings=recipe_data["servings"],
                    prep_time=recipe_data["prep_time"],
                    cook_time=recipe_data["cook_time"],
                    instructions=recipe_data["instructions"],
                    created_at=datetime.now()
                )
                db.add(new_recipe)
                created_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"샘플 레시피 {created_count}개가 생성되었습니다.",
            "created_count": created_count
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

@router.post("/api/import_recipes_from_json")
async def import_recipes_from_json(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """JSON 파일에서 레시피 데이터 가져오기"""
    try:
        if not file.filename.endswith('.json'):
            return {"success": False, "message": "JSON 파일만 업로드 가능합니다."}
        
        content = await file.read()
        recipes_data = json.loads(content.decode('utf-8'))
        
        created_count = 0
        for recipe_data in recipes_data:
            # 중복 체크
            existing = db.query(Recipe).filter(Recipe.name == recipe_data["name"]).first()
            if not existing:
                new_recipe = Recipe(
                    name=recipe_data["name"],
                    category=recipe_data.get("category", "기타"),
                    description=recipe_data.get("description", ""),
                    servings=recipe_data.get("servings", 1),
                    prep_time=recipe_data.get("prep_time", 0),
                    cook_time=recipe_data.get("cook_time", 0),
                    instructions=recipe_data.get("instructions", ""),
                    created_at=datetime.now()
                )
                db.add(new_recipe)
                created_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"레시피 {created_count}개가 가져와졌습니다.",
            "created_count": created_count
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"파일 처리 중 오류가 발생했습니다: {str(e)}"}

# ==============================================================================
# 메뉴 계산 API
# ==============================================================================

@router.post("/api/calculate_menu_costs")
async def calculate_menu_costs(cost_request: MenuCostRequest, db: Session = Depends(get_db)):
    """메뉴 원가 계산"""
    try:
        calculator = CostAnalyzer(db)
        results = []
        
        for menu_id in cost_request.menu_ids:
            menu = db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                continue
            
            # 메뉴 아이템들 조회
            menu_items = db.query(MenuItem).filter(MenuItem.menu_id == menu_id).all()
            
            total_cost = Decimal('0')
            ingredients_detail = []
            
            for item in menu_items:
                ingredient = db.query(Ingredient).filter(Ingredient.id == item.ingredient_id).first()
                if ingredient and ingredient.cost_per_unit:
                    item_cost = item.quantity * ingredient.cost_per_unit
                    total_cost += item_cost
                    
                    ingredients_detail.append({
                        "ingredient_name": ingredient.name,
                        "quantity": float(item.quantity),
                        "unit": item.unit,
                        "cost_per_unit": float(ingredient.cost_per_unit),
                        "item_cost": float(item_cost)
                    })
            
            # 인분당 원가 계산
            cost_per_serving = total_cost / cost_request.servings if cost_request.servings > 0 else total_cost
            
            results.append({
                "menu_id": menu_id,
                "menu_name": menu.name,
                "total_cost": float(total_cost),
                "cost_per_serving": float(cost_per_serving),
                "servings": cost_request.servings,
                "ingredients": ingredients_detail
            })
        
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/check_menu_orderability")
async def check_menu_orderability(menu_data: dict, db: Session = Depends(get_db)):
    """메뉴 주문 가능성 체크"""
    try:
        menu_ids = menu_data.get("menu_ids", [])
        required_date = menu_data.get("date")
        
        results = []
        
        for menu_id in menu_ids:
            menu = db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                continue
            
            # 메뉴의 식재료 확인
            menu_items = db.query(MenuItem).filter(MenuItem.menu_id == menu_id).all()
            
            can_order = True
            missing_ingredients = []
            supplier_info = []
            
            for item in menu_items:
                ingredient = db.query(Ingredient).filter(Ingredient.id == item.ingredient_id).first()
                if not ingredient:
                    can_order = False
                    missing_ingredients.append(f"식재료 ID {item.ingredient_id} (정보 없음)")
                    continue
                
                # 공급업체 확인
                if ingredient.supplier_name:
                    supplier = db.query(Supplier).filter(Supplier.name == ingredient.supplier_name).first()
                    if supplier:
                        supplier_info.append({
                            "ingredient_name": ingredient.name,
                            "supplier_name": supplier.name,
                            "supplier_contact": supplier.contact_phone
                        })
                    else:
                        can_order = False
                        missing_ingredients.append(f"{ingredient.name} (공급업체 없음)")
                else:
                    can_order = False
                    missing_ingredients.append(f"{ingredient.name} (공급업체 미지정)")
            
            results.append({
                "menu_id": menu_id,
                "menu_name": menu.name,
                "can_order": can_order,
                "missing_ingredients": missing_ingredients,
                "suppliers": supplier_info
            })
        
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/calculate-requirements", response_model=RequirementCalculationResponse)
async def calculate_requirements(
    calc_request: RequirementCalculationRequest, 
    db: Session = Depends(get_db)
):
    """식재료 소요량 계산"""
    try:
        calculator = MenuCalculator(db)
        
        # 각 메뉴별 식재료 소요량 계산
        total_requirements = {}
        total_cost = Decimal('0')
        
        for menu_id in calc_request.menu_ids:
            menu = db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                continue
            
            menu_items = db.query(MenuItem).filter(MenuItem.menu_id == menu_id).all()
            
            for item in menu_items:
                ingredient = db.query(Ingredient).filter(Ingredient.id == item.ingredient_id).first()
                if not ingredient:
                    continue
                
                # 인분수에 맞춘 필요량 계산
                required_quantity = item.quantity * calc_request.servings
                
                if ingredient.id in total_requirements:
                    total_requirements[ingredient.id]["quantity"] += required_quantity
                else:
                    total_requirements[ingredient.id] = {
                        "ingredient_id": ingredient.id,
                        "ingredient_name": ingredient.name,
                        "unit": item.unit,
                        "quantity": required_quantity,
                        "cost_per_unit": ingredient.cost_per_unit or Decimal('0')
                    }
                
                # 총 비용 계산
                if ingredient.cost_per_unit:
                    total_cost += required_quantity * ingredient.cost_per_unit
        
        # 결과 포맷팅
        requirements_list = []
        for req_data in total_requirements.values():
            total_item_cost = req_data["quantity"] * req_data["cost_per_unit"]
            requirements_list.append({
                "ingredient_id": req_data["ingredient_id"],
                "ingredient_name": req_data["ingredient_name"],
                "unit": req_data["unit"],
                "quantity": float(req_data["quantity"]),
                "cost_per_unit": float(req_data["cost_per_unit"]),
                "total_cost": float(total_item_cost)
            })
        
        return RequirementCalculationResponse(
            success=True,
            requirements=requirements_list,
            total_cost=total_cost,
            message="식재료 소요량 계산이 완료되었습니다."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==============================================================================
# 식재료 대체 기능
# ==============================================================================

@router.post("/api/preview_bulk_replace")
async def preview_bulk_replace(replace_request: BulkReplaceRequest, db: Session = Depends(get_db)):
    """식재료 일괄 대체 미리보기"""
    try:
        old_ingredient = db.query(Ingredient).filter(Ingredient.id == replace_request.old_ingredient_id).first()
        new_ingredient = db.query(Ingredient).filter(Ingredient.id == replace_request.new_ingredient_id).first()
        
        if not old_ingredient or not new_ingredient:
            return {"success": False, "message": "존재하지 않는 식재료입니다."}
        
        affected_items = []
        
        for menu_id in replace_request.menu_ids:
            menu = db.query(Menu).filter(Menu.id == menu_id).first()
            if not menu:
                continue
            
            # 해당 메뉴에서 old_ingredient를 사용하는 아이템들 찾기
            menu_items = db.query(MenuItem).filter(
                MenuItem.menu_id == menu_id,
                MenuItem.ingredient_id == replace_request.old_ingredient_id
            ).all()
            
            for item in menu_items:
                affected_items.append({
                    "menu_id": menu_id,
                    "menu_name": menu.name,
                    "item_id": item.id,
                    "old_ingredient": old_ingredient.name,
                    "new_ingredient": new_ingredient.name,
                    "quantity": float(item.quantity),
                    "unit": item.unit,
                    "old_cost": float(item.quantity * (old_ingredient.cost_per_unit or 0)),
                    "new_cost": float(item.quantity * (new_ingredient.cost_per_unit or 0))
                })
        
        return {
            "success": True,
            "affected_items": affected_items,
            "old_ingredient": old_ingredient.name,
            "new_ingredient": new_ingredient.name,
            "total_affected": len(affected_items)
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/bulk_replace_ingredient")
async def bulk_replace_ingredient(replace_request: BulkReplaceRequest, db: Session = Depends(get_db)):
    """식재료 일괄 대체 실행"""
    try:
        old_ingredient = db.query(Ingredient).filter(Ingredient.id == replace_request.old_ingredient_id).first()
        new_ingredient = db.query(Ingredient).filter(Ingredient.id == replace_request.new_ingredient_id).first()
        
        if not old_ingredient or not new_ingredient:
            return {"success": False, "message": "존재하지 않는 식재료입니다."}
        
        updated_count = 0
        
        for menu_id in replace_request.menu_ids:
            # 해당 메뉴에서 old_ingredient를 사용하는 아이템들 업데이트
            menu_items = db.query(MenuItem).filter(
                MenuItem.menu_id == menu_id,
                MenuItem.ingredient_id == replace_request.old_ingredient_id
            ).all()
            
            for item in menu_items:
                item.ingredient_id = replace_request.new_ingredient_id
                item.updated_at = datetime.now()
                updated_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"식재료가 성공적으로 대체되었습니다. ({updated_count}개 아이템 업데이트)",
            "updated_count": updated_count,
            "old_ingredient": old_ingredient.name,
            "new_ingredient": new_ingredient.name
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

# ==============================================================================
# 추가 식단 관리 엔드포인트
# ==============================================================================

@router.post("/api/create_diet_plan")
async def create_diet_plan(diet_plan_data: dict, db: Session = Depends(get_db)):
    """식단 생성"""
    try:
        # 식단 생성 로직
        customer_id = diet_plan_data.get('customer_id')
        menu_date = diet_plan_data.get('date')
        menu_items = diet_plan_data.get('menu_items', [])
        
        # 기존 식단 확인
        existing_plan = db.query(DietPlan).filter(
            DietPlan.customer_id == customer_id,
            DietPlan.date == menu_date
        ).first()
        
        if existing_plan:
            return {"success": False, "message": "해당 날짜에 이미 식단이 존재합니다."}
        
        # 새 식단 생성
        new_plan = DietPlan(
            customer_id=customer_id,
            date=datetime.strptime(menu_date, '%Y-%m-%d').date(),
            meal_type=diet_plan_data.get('meal_type', 'lunch'),
            notes=diet_plan_data.get('notes', ''),
            created_at=datetime.now()
        )
        
        db.add(new_plan)
        db.flush()  # ID를 얻기 위해
        
        # 메뉴 아이템들 추가
        for item in menu_items:
            menu_item = MenuItem(
                diet_plan_id=new_plan.id,
                recipe_id=item.get('recipe_id'),
                quantity=item.get('quantity', 1),
                notes=item.get('notes', '')
            )
            db.add(menu_item)
        
        db.commit()
        
        return {
            "success": True,
            "diet_plan_id": new_plan.id,
            "message": "식단이 성공적으로 생성되었습니다."
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

@router.post("/api/save_weekly_plan")
async def save_weekly_plan(plan_data: dict, db: Session = Depends(get_db)):
    """주간 식단 저장"""
    try:
        customer_id = plan_data.get('customer_id')
        week_start = plan_data.get('week_start')
        daily_plans = plan_data.get('daily_plans', {})
        
        saved_plans = []
        
        for day, plan_info in daily_plans.items():
            if not plan_info.get('menu_items'):
                continue
                
            # 날짜 계산
            day_date = datetime.strptime(f"{week_start} {day}", '%Y-%m-%d %A').date()
            
            # 기존 식단 확인 및 삭제
            existing = db.query(DietPlan).filter(
                DietPlan.customer_id == customer_id,
                DietPlan.date == day_date
            ).first()
            
            if existing:
                db.delete(existing)
            
            # 새 식단 생성
            new_plan = DietPlan(
                customer_id=customer_id,
                date=day_date,
                meal_type=plan_info.get('meal_type', 'lunch'),
                notes=plan_info.get('notes', ''),
                created_at=datetime.now()
            )
            
            db.add(new_plan)
            db.flush()
            
            # 메뉴 아이템 추가
            for item in plan_info.get('menu_items', []):
                menu_item = MenuItem(
                    diet_plan_id=new_plan.id,
                    recipe_id=item.get('recipe_id'),
                    quantity=item.get('quantity', 1),
                    notes=item.get('notes', '')
                )
                db.add(menu_item)
            
            saved_plans.append(new_plan.id)
        
        db.commit()
        
        return {
            "success": True,
            "saved_plans": saved_plans,
            "message": f"{len(saved_plans)}일의 식단이 저장되었습니다."
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}