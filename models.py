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

# Customers: 고객사
class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    portion_size = Column(Integer)  # 1인당 제공량 (g)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
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