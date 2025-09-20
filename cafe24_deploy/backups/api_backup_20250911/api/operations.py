"""
운영 관리 API 라우터
- 발주 관리 (Purchase Orders)
- 입고 관리 (Receiving)
- 전처리 지시서 (Preprocessing)
- 급식수 타임라인 관리
- 식단별 식재료 관리
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text, func
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from pydantic import BaseModel
from enum import Enum

# 로컬 임포트
from app.database import get_db, DATABASE_URL
from app.api.auth import get_current_user
from models import (
    PurchaseOrder, PurchaseOrderItem, ReceivingRecord, ReceivingItem,
    PreprocessingMaster, PreprocessingInstruction, PreprocessingInstructionItem,
    MealCount, MealCountTimeline, MealCountTemplate,
    DietPlan, Menu, MenuItem, Ingredient, Supplier, Customer,
    OrderTypeEnum, ReceivingStatusEnum
)

router = APIRouter()

# ==============================================================================
# Enum 정의
# ==============================================================================

class OrderStatus(str, Enum):
    draft = "draft"
    confirmed = "confirmed"
    sent = "sent"
    delivered = "delivered"
    completed = "completed"

class ReceivingStatus(str, Enum):
    pending = "pending"
    partial = "partial"
    completed = "completed"

# ==============================================================================
# Pydantic 모델 정의
# ==============================================================================

class PurchaseOrderCreate(BaseModel):
    order_number: str
    order_date: str  # YYYY-MM-DD 형식
    delivery_date: str  # YYYY-MM-DD 형식
    lead_days: int
    total_meals: int
    reference_meal_plan: Optional[str] = None
    order_time: Optional[str] = None
    order_type: str  # "manual" or "auto"
    notes: Optional[str] = None
    items: List[Dict[str, Any]]

class ReceivingItemUpdate(BaseModel):
    received_quantity: Decimal
    received_date: Optional[date] = None
    notes: Optional[str] = None

class PreprocessingInstructionCreate(BaseModel):
    instruction_date: date
    meal_type: str
    total_servings: int
    reference_menu: Optional[str] = None
    notes: Optional[str] = None
    items: List[Dict[str, Any]]

class MealCountTimelineSave(BaseModel):
    timeline_data: List[Dict[str, Any]]
    template_name: Optional[str] = None

# ==============================================================================
# 페이지 서빙
# ==============================================================================

@router.get("/ordering")
async def serve_ordering():
    """발주 페이지"""
    return FileResponse("ordering_management.html")

@router.get("/receiving")
async def serve_receiving():
    """입고 페이지"""
    return FileResponse("receiving_management.html")

@router.get("/preprocessing")
async def serve_preprocessing():
    """전처리 페이지"""
    return FileResponse("preprocessing.html")

@router.get("/preprocessing-demo")
async def serve_preprocessing_demo():
    """전처리 데모 페이지"""
    return FileResponse("preprocessing_management.html")

# ==============================================================================
# 발주 관리 API
# ==============================================================================

@router.post("/api/purchase-orders")
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
        
        # 발주 아이템들 생성
        total_amount = Decimal('0')
        
        for item_data in order_data.items:
            order_item = PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                ingredient_id=item_data["ingredient_id"],
                ordered_quantity=Decimal(str(item_data["ordered_quantity"])),
                unit_price=Decimal(str(item_data.get("unit_price", 0))),
                total_price=Decimal(str(item_data.get("total_price", 0))),
                unit=item_data.get("unit", "kg"),
                supplier_id=item_data.get("supplier_id"),
                delivery_code=item_data.get("delivery_code", ""),
                notes=item_data.get("notes", "")
            )
            db.add(order_item)
            total_amount += order_item.total_price
        
        purchase_order.total_amount = total_amount
        db.commit()
        
        return {
            "success": True,
            "message": "발주서가 성공적으로 생성되었습니다.",
            "purchase_order_id": purchase_order.id,
            "order_number": purchase_order.order_number
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"발주서 생성 중 오류가 발생했습니다: {str(e)}"}

@router.get("/api/purchase-orders")
async def get_purchase_orders(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """발주서 목록 조회"""
    try:
        query = db.query(PurchaseOrder)
        
        # 필터링
        if start_date:
            query = query.filter(PurchaseOrder.order_date >= start_date)
        if end_date:
            query = query.filter(PurchaseOrder.order_date <= end_date)
        if status:
            query = query.filter(PurchaseOrder.status == status)
        
        total = query.count()
        
        # 페이징
        offset = (page - 1) * limit
        orders = query.order_by(PurchaseOrder.order_date.desc()).offset(offset).limit(limit).all()
        
        order_list = []
        for order in orders:
            order_list.append({
                "id": order.id,
                "order_number": order.order_number,
                "order_date": order.order_date.isoformat(),
                "delivery_date": order.delivery_date.isoformat(),
                "total_meals": order.total_meals,
                "total_amount": float(order.total_amount) if order.total_amount else 0,
                "status": order.status,
                "order_type": order.order_type.value if order.order_type else "manual",
                "created_at": order.created_at.isoformat() if order.created_at else None
            })
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "success": True,
            "orders": order_list,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

# ==============================================================================
# 입고 관리 API
# ==============================================================================

@router.get("/api/receiving-records")
async def get_receiving_records(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """입고 기록 목록 조회"""
    try:
        query = db.query(ReceivingRecord)
        
        # 필터링
        if start_date:
            query = query.filter(ReceivingRecord.received_date >= start_date)
        if end_date:
            query = query.filter(ReceivingRecord.received_date <= end_date)
        if status:
            query = query.filter(ReceivingRecord.status == status)
        if supplier_id:
            query = query.filter(ReceivingRecord.supplier_id == supplier_id)
        
        total = query.count()
        
        # 페이징
        offset = (page - 1) * limit
        records = query.order_by(ReceivingRecord.received_date.desc()).offset(offset).limit(limit).all()
        
        record_list = []
        for record in records:
            # 공급업체 정보 조회
            supplier = db.query(Supplier).filter(Supplier.id == record.supplier_id).first()
            
            record_list.append({
                "id": record.id,
                "purchase_order_id": record.purchase_order_id,
                "supplier_id": record.supplier_id,
                "supplier_name": supplier.name if supplier else "알 수 없음",
                "received_date": record.received_date.isoformat(),
                "delivery_note_number": record.delivery_note_number,
                "status": record.status.value if record.status else "pending",
                "total_amount": float(record.total_amount) if record.total_amount else 0,
                "notes": record.notes,
                "created_at": record.created_at.isoformat() if record.created_at else None
            })
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "success": True,
            "records": record_list,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.put("/api/receiving-items/{item_id}/receive")
async def receive_item(
    item_id: int, 
    receive_data: ReceivingItemUpdate, 
    request: Request,
    db: Session = Depends(get_db)
):
    """입고 처리"""
    try:
        # 입고 아이템 조회
        receiving_item = db.query(ReceivingItem).filter(ReceivingItem.id == item_id).first()
        if not receiving_item:
            return {"success": False, "message": "입고 아이템을 찾을 수 없습니다."}
        
        # 입고 정보 업데이트
        receiving_item.received_quantity = receive_data.received_quantity
        if receive_data.received_date:
            receiving_item.received_date = receive_data.received_date
        receiving_item.notes = receive_data.notes
        receiving_item.updated_at = datetime.now()
        
        # 입고 상태 업데이트 (주문량과 입고량 비교)
        if receiving_item.received_quantity >= receiving_item.ordered_quantity:
            receiving_item.status = ReceivingStatusEnum.completed
        elif receiving_item.received_quantity > 0:
            receiving_item.status = ReceivingStatusEnum.partial
        else:
            receiving_item.status = ReceivingStatusEnum.pending
        
        db.commit()
        
        return {
            "success": True,
            "message": "입고 처리가 완료되었습니다.",
            "item_id": receiving_item.id,
            "status": receiving_item.status.value
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"입고 처리 중 오류가 발생했습니다: {str(e)}"}

# ==============================================================================
# 전처리 지시서 API
# ==============================================================================

@router.get("/api/preprocessing-master")
async def get_preprocessing_master(db: Session = Depends(get_db)):
    """전처리 마스터 데이터 조회"""
    try:
        masters = db.query(PreprocessingMaster).all()
        
        master_list = []
        for master in masters:
            master_list.append({
                "id": master.id,
                "ingredient_id": master.ingredient_id,
                "ingredient_name": master.ingredient_name,
                "preprocessing_method": master.preprocessing_method,
                "unit_conversion": float(master.unit_conversion) if master.unit_conversion else 1.0,
                "loss_rate": float(master.loss_rate) if master.loss_rate else 0.0,
                "processing_time": master.processing_time,
                "temperature": master.temperature,
                "humidity": master.humidity,
                "storage_method": master.storage_method,
                "shelf_life_hours": master.shelf_life_hours,
                "notes": master.notes,
                "created_at": master.created_at.isoformat() if master.created_at else None
            })
        
        return {"success": True, "masters": master_list}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/preprocessing-instructions")
async def create_preprocessing_instruction(
    instruction_data: PreprocessingInstructionCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """전처리 지시서 생성"""
    try:
        # 전처리 지시서 생성
        instruction = PreprocessingInstruction(
            instruction_date=instruction_data.instruction_date,
            meal_type=instruction_data.meal_type,
            total_servings=instruction_data.total_servings,
            reference_menu=instruction_data.reference_menu,
            notes=instruction_data.notes,
            created_by=1,  # 임시로 1번 사용자
            created_at=datetime.now()
        )
        
        db.add(instruction)
        db.flush()  # ID 생성을 위해 flush
        
        # 전처리 지시서 아이템들 생성
        for item_data in instruction_data.items:
            instruction_item = PreprocessingInstructionItem(
                preprocessing_instruction_id=instruction.id,
                ingredient_id=item_data["ingredient_id"],
                raw_quantity=Decimal(str(item_data["raw_quantity"])),
                processed_quantity=Decimal(str(item_data.get("processed_quantity", 0))),
                preprocessing_method=item_data.get("preprocessing_method", ""),
                start_time=item_data.get("start_time"),
                estimated_duration=item_data.get("estimated_duration", 0),
                notes=item_data.get("notes", "")
            )
            db.add(instruction_item)
        
        db.commit()
        
        return {
            "success": True,
            "message": "전처리 지시서가 성공적으로 생성되었습니다.",
            "instruction_id": instruction.id
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"전처리 지시서 생성 중 오류가 발생했습니다: {str(e)}"}

@router.get("/api/preprocessing-instructions")
async def get_preprocessing_instructions(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    meal_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """전처리 지시서 목록 조회"""
    try:
        query = db.query(PreprocessingInstruction)
        
        # 필터링
        if start_date:
            query = query.filter(PreprocessingInstruction.instruction_date >= start_date)
        if end_date:
            query = query.filter(PreprocessingInstruction.instruction_date <= end_date)
        if meal_type:
            query = query.filter(PreprocessingInstruction.meal_type == meal_type)
        
        total = query.count()
        
        # 페이징
        offset = (page - 1) * limit
        instructions = query.order_by(PreprocessingInstruction.instruction_date.desc()).offset(offset).limit(limit).all()
        
        instruction_list = []
        for instruction in instructions:
            instruction_list.append({
                "id": instruction.id,
                "instruction_date": instruction.instruction_date.isoformat(),
                "meal_type": instruction.meal_type,
                "total_servings": instruction.total_servings,
                "reference_menu": instruction.reference_menu,
                "status": instruction.status,
                "notes": instruction.notes,
                "created_at": instruction.created_at.isoformat() if instruction.created_at else None
            })
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "success": True,
            "instructions": instruction_list,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/api/preprocessing-instructions/{instruction_id}")
async def get_preprocessing_instruction_detail(instruction_id: int, db: Session = Depends(get_db)):
    """전처리 지시서 상세 조회"""
    try:
        instruction = db.query(PreprocessingInstruction).filter(PreprocessingInstruction.id == instruction_id).first()
        if not instruction:
            return {"success": False, "message": "전처리 지시서를 찾을 수 없습니다."}
        
        # 지시서 아이템들 조회
        items = db.query(PreprocessingInstructionItem).filter(
            PreprocessingInstructionItem.preprocessing_instruction_id == instruction_id
        ).all()
        
        item_list = []
        for item in items:
            ingredient = db.query(Ingredient).filter(Ingredient.id == item.ingredient_id).first()
            item_list.append({
                "id": item.id,
                "ingredient_id": item.ingredient_id,
                "ingredient_name": ingredient.name if ingredient else "알 수 없음",
                "raw_quantity": float(item.raw_quantity),
                "processed_quantity": float(item.processed_quantity),
                "preprocessing_method": item.preprocessing_method,
                "start_time": item.start_time,
                "estimated_duration": item.estimated_duration,
                "actual_duration": item.actual_duration,
                "status": item.status,
                "notes": item.notes
            })
        
        instruction_data = {
            "id": instruction.id,
            "instruction_date": instruction.instruction_date.isoformat(),
            "meal_type": instruction.meal_type,
            "total_servings": instruction.total_servings,
            "reference_menu": instruction.reference_menu,
            "status": instruction.status,
            "notes": instruction.notes,
            "created_at": instruction.created_at.isoformat() if instruction.created_at else None,
            "items": item_list
        }
        
        return {"success": True, "instruction": instruction_data}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/create_preprocessing_master_data")
async def create_preprocessing_master_data(db: Session = Depends(get_db)):
    """전처리 마스터 데이터 생성 (샘플 데이터)"""
    try:
        # 샘플 전처리 마스터 데이터
        sample_masters = [
            {
                "ingredient_name": "양파",
                "preprocessing_method": "깍둑썰기",
                "unit_conversion": Decimal('0.95'),  # 95% (껍질 제거)
                "loss_rate": Decimal('0.05'),  # 5% 손실
                "processing_time": 15,  # 15분
                "storage_method": "냉장보관",
                "shelf_life_hours": 24,
                "notes": "균등한 크기로 썰기"
            },
            {
                "ingredient_name": "당근",
                "preprocessing_method": "채썰기",
                "unit_conversion": Decimal('0.90'),  # 90%
                "loss_rate": Decimal('0.10'),  # 10% 손실
                "processing_time": 20,  # 20분
                "storage_method": "냉장보관",
                "shelf_life_hours": 48,
                "notes": "2-3mm 두께로 썰기"
            },
            {
                "ingredient_name": "감자",
                "preprocessing_method": "깍둑썰기",
                "unit_conversion": Decimal('0.85'),  # 85%
                "loss_rate": Decimal('0.15'),  # 15% 손실
                "processing_time": 25,  # 25분
                "storage_method": "찬물보관",
                "shelf_life_hours": 12,
                "notes": "물에 담가 갈변 방지"
            }
        ]
        
        created_count = 0
        for master_data in sample_masters:
            # 중복 체크
            existing = db.query(PreprocessingMaster).filter(
                PreprocessingMaster.ingredient_name == master_data["ingredient_name"]
            ).first()
            
            if not existing:
                new_master = PreprocessingMaster(
                    ingredient_name=master_data["ingredient_name"],
                    preprocessing_method=master_data["preprocessing_method"],
                    unit_conversion=master_data["unit_conversion"],
                    loss_rate=master_data["loss_rate"],
                    processing_time=master_data["processing_time"],
                    storage_method=master_data["storage_method"],
                    shelf_life_hours=master_data["shelf_life_hours"],
                    notes=master_data["notes"],
                    created_at=datetime.now()
                )
                db.add(new_master)
                created_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"전처리 마스터 데이터 {created_count}개가 생성되었습니다.",
            "created_count": created_count
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "message": str(e)}

# ==============================================================================
# 급식수 타임라인 API
# ==============================================================================

@router.get("/api/meal-counts/timeline")
async def get_meal_counts_timeline(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    site_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """급식수 타임라인 조회"""
    try:
        # 기본 날짜 범위 설정 (지정되지 않은 경우)
        if not start_date:
            start_date = date.today() - timedelta(days=30)
        if not end_date:
            end_date = date.today() + timedelta(days=30)
        
        query = db.query(MealCountTimeline)
        
        # 필터링
        query = query.filter(MealCountTimeline.date >= start_date)
        query = query.filter(MealCountTimeline.date <= end_date)
        if site_id:
            query = query.filter(MealCountTimeline.site_id == site_id)
        
        timelines = query.order_by(MealCountTimeline.date).all()
        
        timeline_list = []
        for timeline in timelines:
            site = db.query(Customer).filter(Customer.id == timeline.site_id).first()
            timeline_list.append({
                "id": timeline.id,
                "site_id": timeline.site_id,
                "site_name": site.name if site else "알 수 없음",
                "date": timeline.date.isoformat(),
                "breakfast_count": timeline.breakfast_count or 0,
                "lunch_count": timeline.lunch_count or 0,
                "dinner_count": timeline.dinner_count or 0,
                "snack_count": timeline.snack_count or 0,
                "total_count": (timeline.breakfast_count or 0) + (timeline.lunch_count or 0) + (timeline.dinner_count or 0) + (timeline.snack_count or 0),
                "is_holiday": timeline.is_holiday,
                "notes": timeline.notes,
                "created_at": timeline.created_at.isoformat() if timeline.created_at else None
            })
        
        return {"success": True, "timeline": timeline_list}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/api/meal-counts/templates/{tab_type}")
async def get_meal_count_templates(tab_type: str, db: Session = Depends(get_db)):
    """급식수 템플릿 조회"""
    try:
        templates = db.query(MealCountTemplate).filter(
            MealCountTemplate.template_type == tab_type
        ).all()
        
        template_list = []
        for template in templates:
            template_list.append({
                "id": template.id,
                "name": template.name,
                "template_type": template.template_type,
                "breakfast_count": template.breakfast_count or 0,
                "lunch_count": template.lunch_count or 0,
                "dinner_count": template.dinner_count or 0,
                "snack_count": template.snack_count or 0,
                "description": template.description,
                "is_default": template.is_default,
                "created_at": template.created_at.isoformat() if template.created_at else None
            })
        
        return {"success": True, "templates": template_list}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/api/meal-counts/timeline/save")
async def save_meal_counts_timeline(
    timeline_data: MealCountTimelineSave,
    request: Request,
    db: Session = Depends(get_db)
):
    """급식수 타임라인 저장"""
    try:
        saved_count = 0
        
        for timeline_item in timeline_data.timeline_data:
            timeline_date = datetime.strptime(timeline_item["date"], '%Y-%m-%d').date()
            site_id = timeline_item["site_id"]
            
            # 기존 데이터 확인
            existing = db.query(MealCountTimeline).filter(
                MealCountTimeline.date == timeline_date,
                MealCountTimeline.site_id == site_id
            ).first()
            
            if existing:
                # 업데이트
                existing.breakfast_count = timeline_item.get("breakfast_count", 0)
                existing.lunch_count = timeline_item.get("lunch_count", 0)
                existing.dinner_count = timeline_item.get("dinner_count", 0)
                existing.snack_count = timeline_item.get("snack_count", 0)
                existing.is_holiday = timeline_item.get("is_holiday", False)
                existing.notes = timeline_item.get("notes", "")
                existing.updated_at = datetime.now()
            else:
                # 새로 생성
                new_timeline = MealCountTimeline(
                    site_id=site_id,
                    date=timeline_date,
                    breakfast_count=timeline_item.get("breakfast_count", 0),
                    lunch_count=timeline_item.get("lunch_count", 0),
                    dinner_count=timeline_item.get("dinner_count", 0),
                    snack_count=timeline_item.get("snack_count", 0),
                    is_holiday=timeline_item.get("is_holiday", False),
                    notes=timeline_item.get("notes", ""),
                    created_at=datetime.now()
                )
                db.add(new_timeline)
            
            saved_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"급식수 타임라인 {saved_count}개가 저장되었습니다.",
            "saved_count": saved_count
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"타임라인 저장 중 오류가 발생했습니다: {str(e)}"}

# ==============================================================================
# 식단별 식재료 API
# ==============================================================================

@router.get("/api/meal-plan-ingredients/{plan_date}")
async def get_meal_plan_ingredients(plan_date: str, db: Session = Depends(get_db)):
    """특정 날짜의 식단별 식재료 목록 조회"""
    try:
        # 날짜 파싱
        target_date = datetime.strptime(plan_date, '%Y-%m-%d').date()
        
        # 해당 날짜의 식단표들 조회
        diet_plans = db.query(DietPlan).filter(DietPlan.date == target_date).all()
        
        if not diet_plans:
            return {"success": True, "ingredients": [], "message": "해당 날짜에 등록된 식단이 없습니다."}
        
        # 모든 식단의 식재료 집계
        ingredient_summary = {}
        
        for diet_plan in diet_plans:
            # 식단에 연결된 메뉴들 조회
            customer_menus = db.query(CustomerMenu).filter(
                CustomerMenu.customer_id == diet_plan.customer_id,
                CustomerMenu.diet_plan_id == diet_plan.id
            ).all()
            
            for customer_menu in customer_menus:
                # 메뉴의 식재료들 조회
                menu_items = db.query(MenuItem).filter(MenuItem.menu_id == customer_menu.menu_id).all()
                
                for menu_item in menu_items:
                    ingredient = db.query(Ingredient).filter(Ingredient.id == menu_item.ingredient_id).first()
                    if not ingredient:
                        continue
                    
                    # 식재료별 집계
                    ingredient_key = f"{ingredient.id}_{ingredient.name}"
                    
                    if ingredient_key in ingredient_summary:
                        ingredient_summary[ingredient_key]["total_quantity"] += menu_item.quantity
                        ingredient_summary[ingredient_key]["menus"].append({
                            "menu_id": customer_menu.menu_id,
                            "menu_name": customer_menu.menu.name if customer_menu.menu else "알 수 없음",
                            "customer_name": diet_plan.customer.name,
                            "quantity": float(menu_item.quantity)
                        })
                    else:
                        ingredient_summary[ingredient_key] = {
                            "ingredient_id": ingredient.id,
                            "ingredient_name": ingredient.name,
                            "category": ingredient.category,
                            "unit": menu_item.unit,
                            "cost_per_unit": float(ingredient.cost_per_unit) if ingredient.cost_per_unit else 0,
                            "total_quantity": menu_item.quantity,
                            "menus": [{
                                "menu_id": customer_menu.menu_id,
                                "menu_name": customer_menu.menu.name if customer_menu.menu else "알 수 없음",
                                "customer_name": diet_plan.customer.name,
                                "quantity": float(menu_item.quantity)
                            }]
                        }
        
        # 결과 포맷팅
        ingredient_list = []
        for ingredient_data in ingredient_summary.values():
            total_cost = ingredient_data["total_quantity"] * Decimal(str(ingredient_data["cost_per_unit"]))
            
            ingredient_list.append({
                "ingredient_id": ingredient_data["ingredient_id"],
                "ingredient_name": ingredient_data["ingredient_name"],
                "category": ingredient_data["category"],
                "unit": ingredient_data["unit"],
                "total_quantity": float(ingredient_data["total_quantity"]),
                "cost_per_unit": ingredient_data["cost_per_unit"],
                "total_cost": float(total_cost),
                "menus": ingredient_data["menus"]
            })
        
        # 카테고리별로 정렬
        ingredient_list.sort(key=lambda x: (x["category"], x["ingredient_name"]))
        
        return {"success": True, "ingredients": ingredient_list, "date": plan_date}
    except Exception as e:
        return {"success": False, "message": str(e)}

# ==============================================================================
# 테스트 데이터 생성 API
# ==============================================================================

@router.post("/api/create_test_meal_data")
async def create_test_meal_data(db: Session = Depends(get_db)):
    """테스트 급식 데이터 생성"""
    try:
        # 샘플 고객 조회 (Customer 테이블)
        customers = db.query(Customer).limit(3).all()
        if not customers:
            return {"success": False, "message": "고객 데이터가 필요합니다. 먼저 고객을 생성해주세요."}
        
        created_plans = 0
        created_timelines = 0
        
        # 향후 7일간의 식단표 생성
        for i in range(7):
            target_date = date.today() + timedelta(days=i)
            
            for customer in customers:
                # 식단표 생성 (중복 체크)
                existing_plan = db.query(DietPlan).filter(
                    DietPlan.customer_id == customer.id,
                    DietPlan.date == target_date
                ).first()
                
                if not existing_plan:
                    diet_plan = DietPlan(
                        customer_id=customer.id,
                        date=target_date,
                        meal_type="중식",
                        description=f"{customer.name} {target_date.isoformat()} 식단",
                        created_at=datetime.now()
                    )
                    db.add(diet_plan)
                    created_plans += 1
                
                # 급식수 타임라인 생성 (중복 체크)
                existing_timeline = db.query(MealCountTimeline).filter(
                    MealCountTimeline.site_id == customer.id,
                    MealCountTimeline.date == target_date
                ).first()
                
                if not existing_timeline:
                    timeline = MealCountTimeline(
                        site_id=customer.id,
                        date=target_date,
                        breakfast_count=50 + (i * 5),
                        lunch_count=100 + (i * 10),
                        dinner_count=80 + (i * 8),
                        snack_count=30 + (i * 3),
                        is_holiday=target_date.weekday() >= 5,  # 주말은 휴일
                        notes=f"테스트 데이터 - {target_date.isoformat()}",
                        created_at=datetime.now()
                    )
                    db.add(timeline)
                    created_timelines += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": f"테스트 데이터가 생성되었습니다. (식단표: {created_plans}개, 타임라인: {created_timelines}개)",
            "created_plans": created_plans,
            "created_timelines": created_timelines
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"테스트 데이터 생성 중 오류가 발생했습니다: {str(e)}"}