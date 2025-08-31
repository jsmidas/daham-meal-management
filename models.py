from sqlalchemy import Column, Integer, String, Float, Date, Text, Boolean, ForeignKey, JSON, Enum, DECIMAL, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class ColorEnum(enum.Enum):
    red = "red"
    blue = "blue" 
    green = "green"
    yellow = "yellow"
    white = "white"
    black = "black"
    orange = "#F34C2B"
    brown = "brown"
    lite_brown = "lite brown"

class RoleEnum(enum.Enum):
    nutritionist = "영양사"
    admin = "관리자"

class InstructionTypeEnum(enum.Enum):
    preprocessing = "전처리"
    cooking = "조리"
    portioning = "소분"

class OrderStatusEnum(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"

class OrderTypeEnum(enum.Enum):
    manual = "수동발주"
    auto = "자동발주"
    regular = "정기발주"
    additional = "추가발주"
    urgent = "긴급발주"

class ReceivingStatusEnum(enum.Enum):
    pending = "입고대기"
    partial = "일부입고"
    completed = "입고완료"
    overdue = "입고지연"

# Users: 사용자 정보
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    contact_info = Column(String(100))
    department = Column(String(50))
    position = Column(String(50))
    managed_site = Column(String(100))
    operator = Column(Boolean, default=False)
    semi_operator = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# DietPlans: 최상위 식단표
class DietPlan(Base):
    __tablename__ = "diet_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    menus = relationship("Menu", back_populates="diet_plan")

# Menus: 세부식단표
class Menu(Base):
    __tablename__ = "menus"
    
    id = Column(Integer, primary_key=True, index=True)
    diet_plan_id = Column(Integer, ForeignKey("diet_plans.id"), nullable=False)
    menu_type = Column(String(15), nullable=False)
    target_num_persons = Column(Integer, nullable=False)
    target_food_cost = Column(DECIMAL(10, 2))
    evaluation_score = Column(Integer)
    color = Column(Enum(ColorEnum))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    diet_plan = relationship("DietPlan", back_populates="menus")
    menu_items = relationship("MenuItem", back_populates="menu")
    customer_menus = relationship("CustomerMenu", back_populates="menu")
    orders = relationship("Order", back_populates="menu")

# MenuItems: 단일 식단표
class MenuItem(Base):
    __tablename__ = "menu_items"
    
    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    name = Column(String(100), nullable=False)
    portion_num_persons = Column(Integer)
    yield_rate = Column(DECIMAL(3, 2), default=1.0)
    recipe_id = Column(Integer, ForeignKey("recipes.id"))
    photo_url = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    menu = relationship("Menu", back_populates="menu_items")
    recipe = relationship("Recipe", back_populates="menu_items")

# Recipe: 레시피
class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    version = Column(String(10))
    effective_date = Column(Date)
    notes = Column(Text)
    nutrition_data = Column(JSON)
    evaluation_score = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    recipe_ingredients = relationship("RecipeIngredient", back_populates="recipe")
    menu_items = relationship("MenuItem", back_populates="recipe")

# Ingredients: 식재료
class Ingredient(Base):
    __tablename__ = "ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    base_unit = Column(String(10), nullable=False)
    price = Column(DECIMAL(10, 2))
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    moq = Column(DECIMAL(10, 3), default=1.0)  # Minimum Order Quantity
    allergy_codes = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="ingredients")
    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient")
    supplier_ingredients = relationship("SupplierIngredient", back_populates="ingredient")
    inventories = relationship("Inventory", back_populates="ingredient")

# Suppliers: 공급업체
class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    contact = Column(String(100))
    update_frequency = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    ingredients = relationship("Ingredient", back_populates="supplier")
    supplier_ingredients = relationship("SupplierIngredient", back_populates="supplier")

# RecipeIngredients: 레시피-식재료 관계
class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    
    recipe_id = Column(Integer, ForeignKey("recipes.id"), primary_key=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), primary_key=True)
    quantity = Column(DECIMAL(10, 3), nullable=False)  # 1인량
    unit = Column(String(10), nullable=False)
    unit_in_kg = Column(DECIMAL(10, 3))  # kg 환산
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    recipe = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")

# SupplierIngredients: 공급업체-식재료 관계
class SupplierIngredient(Base):
    __tablename__ = "supplier_ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    ingredient_code = Column(String(20))
    origin = Column(String(50))
    is_published = Column(Boolean, default=True)
    unit = Column(String(10))
    is_tax_free = Column(Boolean, default=False)
    preorder_date = Column(Date)
    unit_price = Column(DECIMAL(10, 2))
    selling_price = Column(DECIMAL(10, 2))
    note = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="supplier_ingredients")
    ingredient = relationship("Ingredient", back_populates="supplier_ingredients")

# Orders: 발주
class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    quantity = Column(DECIMAL(10, 3))
    adjusted_quantity = Column(DECIMAL(10, 3))
    total_price = Column(DECIMAL(10, 2))
    status = Column(Enum(OrderStatusEnum), default=OrderStatusEnum.pending)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    menu = relationship("Menu", back_populates="orders")

# Customers: 고객사 (사업장) - 계층 구조 지원
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    site_type = Column(String(20), default="detail")  # head, detail, period
    parent_id = Column(Integer, ForeignKey("customers.id"), nullable=True)  # 상위 사업장
    level = Column(Integer, default=0)  # 0: 헤드, 1: 세부, 2: 기간별
    sort_order = Column(Integer, default=0)  # 정렬 순서
    portion_size = Column(Integer)  # 1인당 제공량 (g)
    is_active = Column(Boolean, default=True)
    contact_person = Column(String(100))  # 담당자
    contact_phone = Column(String(50))   # 연락처
    address = Column(Text)               # 주소
    description = Column(Text)           # 설명
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Self-referential relationship for hierarchy
    children = relationship("Customer", backref="parent", remote_side=[id])
    
    # Relationships
    customer_menus = relationship("CustomerMenu", back_populates="customer")

# CustomerMenus: 고객사-메뉴 연결
class CustomerMenu(Base):
    __tablename__ = "customer_menus"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    customer_num_persons = Column(Integer)
    assigned_date = Column(Date)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="customer_menus")
    menu = relationship("Menu", back_populates="customer_menus")

# Inventories: 재고
class Inventory(Base):
    __tablename__ = "inventories"
    
    id = Column(Integer, primary_key=True, index=True)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    quantity = Column(DECIMAL(10, 3))
    last_updated = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    ingredient = relationship("Ingredient", back_populates="inventories")

# PreprocessingMaster: 전처리 필요 식자재 마스터
class PreprocessingMaster(Base):
    __tablename__ = "preprocessing_master"
    
    id = Column(Integer, primary_key=True, index=True)
    ingredient_name = Column(String(200), nullable=False, index=True)  # 식자재명
    preprocessing_method = Column(Text, nullable=False)  # 전처리 방법
    estimated_time = Column(Integer)  # 예상 소요시간(분)
    priority = Column(Integer, default=5)  # 우선순위 (1=높음, 5=보통, 10=낮음)
    safety_notes = Column(Text)  # 안전사항
    storage_condition = Column(String(100))  # 보관조건
    tools_required = Column(Text)  # 필요 도구
    is_active = Column(Boolean, default=True)  # 활성화 여부
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# PreprocessingInstructions: 전처리 지시서
class PreprocessingInstruction(Base):
    __tablename__ = "preprocessing_instructions"
    
    id = Column(Integer, primary_key=True, index=True)
    instruction_date = Column(Date, nullable=False, index=True)  # 지시서 날짜
    meal_type = Column(String(20), nullable=False)  # 조식/중식/석식/야식
    diet_plan_id = Column(Integer, ForeignKey("diet_plans.id"))  # 참조 식단표
    status = Column(String(20), default="pending")  # pending, completed
    total_items = Column(Integer, default=0)  # 총 전처리 항목수
    completed_items = Column(Integer, default=0)  # 완료된 항목수
    notes = Column(Text)  # 특별 지시사항
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    diet_plan = relationship("DietPlan")
    creator = relationship("User")
    items = relationship("PreprocessingInstructionItem", back_populates="instruction", cascade="all, delete-orphan")

# PreprocessingInstructionItems: 전처리 지시서 항목
class PreprocessingInstructionItem(Base):
    __tablename__ = "preprocessing_instruction_items"
    
    id = Column(Integer, primary_key=True, index=True)
    instruction_id = Column(Integer, ForeignKey("preprocessing_instructions.id"), nullable=False)
    ingredient_name = Column(String(200), nullable=False)  # 식자재명
    quantity = Column(DECIMAL(10, 3), nullable=False)  # 수량
    unit = Column(String(20), nullable=False)  # 단위
    preprocessing_method = Column(Text, nullable=False)  # 전처리 방법
    estimated_time = Column(Integer)  # 예상 소요시간
    priority = Column(Integer, default=5)  # 우선순위
    is_completed = Column(Boolean, default=False)  # 완료 여부
    completed_at = Column(DateTime)  # 완료 시간
    notes = Column(Text)  # 비고
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    instruction = relationship("PreprocessingInstruction", back_populates="items")

# Instructions: 지시서
class Instruction(Base):
    __tablename__ = "instructions"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(InstructionTypeEnum), nullable=False)
    content = Column(JSON)
    details = Column(Text)  # 영양사 입력 지시사항
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    diet_plan_instructions = relationship("DietPlanInstruction", back_populates="instruction")

# DietPlanInstructions: 식단표-지시서 M:N
class DietPlanInstruction(Base):
    __tablename__ = "diet_plan_instructions"
    
    diet_plan_id = Column(Integer, ForeignKey("diet_plans.id"), primary_key=True)
    instruction_id = Column(Integer, ForeignKey("instructions.id"), primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    instruction = relationship("Instruction", back_populates="diet_plan_instructions")

# MealCount: 식수 등록 관리
class MealCount(Base):
    __tablename__ = "meal_counts"
    
    id = Column(Integer, primary_key=True, index=True)
    delivery_site = Column(String(100), nullable=False)  # 운반처
    meal_type = Column(String(20), nullable=False)  # 식사유형 (조식/중식)
    target_material_cost = Column(DECIMAL(10, 2))  # 목표 재료비
    site_name = Column(String(100), nullable=False)  # 사업장명
    meal_count = Column(Integer, nullable=False)  # 식수
    registration_date = Column(Date, nullable=False)  # 등록 날짜
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# MealCountTimeline: 15일 타임라인 식수 관리
class MealCountTimeline(Base):
    __tablename__ = "meal_count_timeline"
    
    id = Column(Integer, primary_key=True, index=True)
    tab_type = Column(String(50), nullable=False)  # 탭 구분 (도시락/운반/학교/요양원/확장1/확장2)
    meal_category = Column(String(50), nullable=False)  # 세부식단 (조식A/중식A/중식B/석식A/야식A 등)
    site_name = Column(String(100), nullable=False)  # 사업장명
    meal_count = Column(Integer, nullable=False)  # 식수
    target_date = Column(Date, nullable=False)  # 대상 날짜
    is_confirmed = Column(Boolean, default=False)  # 확정 여부 (과거 데이터)
    target_material_cost = Column(DECIMAL(10, 2))  # 목표재료비 (선택사항)
    notes = Column(Text)  # 비고
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# MealCountTemplate: 식수 템플릿 관리 (기본 구성 정보)
class MealCountTemplate(Base):
    __tablename__ = "meal_count_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    tab_type = Column(String(50), nullable=False)  # 탭 구분
    meal_category = Column(String(50), nullable=False)  # 세부식단
    site_name = Column(String(100), nullable=False)  # 사업장명
    display_order = Column(Integer, default=0)  # 표시 순서
    is_active = Column(Boolean, default=True)  # 활성화 여부
    default_count = Column(Integer, default=0)  # 기본 식수 (예상값 계산용)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Purchase Orders: 발주서
class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)  # 발주번호
    order_date = Column(Date, nullable=False)  # 발주일
    delivery_date = Column(Date, nullable=False)  # 납기일
    lead_days = Column(Integer, default=3)  # 선발주일
    total_meals = Column(Integer)  # 총 식수
    reference_meal_plan = Column(String(100))  # 참조 식단표
    order_time = Column(String(10))  # 발주 시간
    order_type = Column(Enum(OrderTypeEnum), nullable=False)  # 발주 유형
    status = Column(Enum(OrderStatusEnum), default=OrderStatusEnum.pending)  # 발주 상태
    total_amount = Column(DECIMAL(12, 2), default=0)  # 총 발주 금액
    notes = Column(Text)  # 비고
    created_by = Column(Integer, ForeignKey("users.id"))  # 발주자
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 관계 설정
    creator = relationship("User", backref="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="order", cascade="all, delete-orphan")

# Purchase Order Items: 발주 품목
class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    category = Column(String(50))  # 분류
    code = Column(String(50))  # 코드
    name = Column(String(200), nullable=False)  # 식자재명
    supplier = Column(String(100))  # 거래처
    origin = Column(String(50))  # 원산지
    unit = Column(String(20))  # 단위
    current_stock = Column(DECIMAL(10, 2), default=0)  # 현재재고
    quantity = Column(DECIMAL(10, 2), nullable=False)  # 발주수량
    unit_price = Column(DECIMAL(10, 2), nullable=False)  # 단가
    amount = Column(DECIMAL(12, 2), nullable=False)  # 금액
    lead_time = Column(Integer, default=3)  # 선발주일
    meal_plan_ref = Column(String(100))  # 참조식단표
    notes = Column(Text)  # 비고
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 관계 설정
    order = relationship("PurchaseOrder", back_populates="items")

# Receiving Records: 입고 기록
class ReceivingRecord(Base):
    __tablename__ = "receiving_records"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=False)
    supplier = Column(String(100), nullable=False)  # 거래처
    expected_date = Column(Date, nullable=False)  # 예상 입고일
    actual_date = Column(Date)  # 실제 입고일
    status = Column(Enum(ReceivingStatusEnum), default=ReceivingStatusEnum.pending)  # 입고 상태
    total_items = Column(Integer, default=0)  # 총 품목수
    received_items = Column(Integer, default=0)  # 입고완료 품목수
    total_amount = Column(DECIMAL(12, 2), default=0)  # 총 금액
    notes = Column(Text)  # 비고
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 관계 설정
    order = relationship("PurchaseOrder", backref="receiving_records")
    items = relationship("ReceivingItem", back_populates="receiving_record", cascade="all, delete-orphan")

# Receiving Items: 입고 품목
class ReceivingItem(Base):
    __tablename__ = "receiving_items"
    
    id = Column(Integer, primary_key=True, index=True)
    receiving_record_id = Column(Integer, ForeignKey("receiving_records.id"), nullable=False)
    order_item_id = Column(Integer, ForeignKey("purchase_order_items.id"), nullable=False)
    name = Column(String(200), nullable=False)  # 식자재명
    ordered_quantity = Column(DECIMAL(10, 2), nullable=False)  # 주문수량
    received_quantity = Column(DECIMAL(10, 2), default=0)  # 입고수량
    unit = Column(String(20))  # 단위
    unit_price = Column(DECIMAL(10, 2), nullable=False)  # 단가
    amount = Column(DECIMAL(12, 2), nullable=False)  # 금액
    received = Column(Boolean, default=False)  # 입고완료 여부
    received_at = Column(DateTime)  # 입고 시간
    notes = Column(Text)  # 비고
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 관계 설정
    receiving_record = relationship("ReceivingRecord", back_populates="items")
    order_item = relationship("PurchaseOrderItem", backref="receiving_items")