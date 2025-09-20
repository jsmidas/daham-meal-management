"""
세부식단표 관리 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from models import Menu, DietPlan, BusinessLocation
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()

class DetailedMenuCreate(BaseModel):
    site_id: int
    name: str
    description: str = ""
    is_active: bool = True

class DetailedMenuUpdate(BaseModel):
    name: str
    description: str = ""
    is_active: bool = True

class DetailedMenuResponse(BaseModel):
    id: int
    name: str
    description: str
    is_active: bool
    created_at: datetime
    site_id: int
    site_name: str

    class Config:
        from_attributes = True

@router.get("/sites/{site_id}/detailed-menus")
async def get_detailed_menus_for_site(site_id: int, db: Session = Depends(get_db)):
    """사업장의 세부식단표 목록 조회"""
    try:
        # 사업장 존재 확인
        site = db.query(BusinessLocation).filter(BusinessLocation.id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="사업장을 찾을 수 없습니다")
        
        # 해당 사업장의 세부식단표 조회 (Menu 테이블에서)
        # 임시로 Menu 테이블을 사용하되, 실제로는 site_id와 연결된 구조가 필요함
        # 현재는 기본 Menu 데이터를 반환
        menus = db.query(Menu).limit(10).all()  # 임시 데이터
        
        # 응답 데이터 구성
        menu_list = []
        for menu in menus:
            menu_data = {
                "id": menu.id,
                "name": f"세부식단표 {menu.id}",
                "description": f"세부식단표 설명 {menu.id}",
                "is_active": True,
                "created_at": menu.created_at or datetime.now(),
                "site_id": site_id,
                "site_name": site.site_name
            }
            menu_list.append(menu_data)
        
        return {
            "success": True,
            "menus": menu_list,
            "message": f"{site.site_name}의 세부식단표 목록"
        }
        
    except Exception as e:
        print(f"세부식단표 조회 오류: {e}")
        return {
            "success": False,
            "menus": [],
            "message": f"조회 중 오류가 발생했습니다: {str(e)}"
        }

@router.post("/detailed-menus")
async def create_detailed_menu(menu_data: DetailedMenuCreate, db: Session = Depends(get_db)):
    """새 세부식단표 생성"""
    try:
        # 사업장 존재 확인
        site = db.query(BusinessLocation).filter(BusinessLocation.id == menu_data.site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="사업장을 찾을 수 없습니다")
        
        # 기본 DietPlan 생성 또는 조회
        diet_plan = db.query(DietPlan).first()
        if not diet_plan:
            # 기본 DietPlan 생성
            diet_plan = DietPlan(
                category="기본",
                date=datetime.now().date(),
                description="기본 식단계획"
            )
            db.add(diet_plan)
            db.commit()
            db.refresh(diet_plan)
        
        # 새 Menu(세부식단표) 생성
        new_menu = Menu(
            diet_plan_id=diet_plan.id,
            menu_type=menu_data.name,
            target_num_persons=50,  # 기본값
            target_food_cost=10000,  # 기본값
            evaluation_score=5,
            created_at=datetime.now()
        )
        
        db.add(new_menu)
        db.commit()
        db.refresh(new_menu)
        
        return {
            "success": True,
            "menu": {
                "id": new_menu.id,
                "name": menu_data.name,
                "description": menu_data.description,
                "site_id": menu_data.site_id
            },
            "message": "세부식단표가 생성되었습니다"
        }
        
    except Exception as e:
        db.rollback()
        print(f"세부식단표 생성 오류: {e}")
        return {
            "success": False,
            "message": f"생성 중 오류가 발생했습니다: {str(e)}"
        }

@router.put("/detailed-menus/{menu_id}")
async def update_detailed_menu(menu_id: int, menu_data: DetailedMenuUpdate, db: Session = Depends(get_db)):
    """세부식단표 수정"""
    try:
        menu = db.query(Menu).filter(Menu.id == menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail="세부식단표를 찾을 수 없습니다")
        
        # 필드 업데이트
        menu.menu_type = menu_data.name
        menu.updated_at = datetime.now()
        
        db.commit()
        db.refresh(menu)
        
        return {
            "success": True,
            "menu": {
                "id": menu.id,
                "name": menu_data.name,
                "description": menu_data.description
            },
            "message": "세부식단표가 수정되었습니다"
        }
        
    except Exception as e:
        db.rollback()
        print(f"세부식단표 수정 오류: {e}")
        return {
            "success": False,
            "message": f"수정 중 오류가 발생했습니다: {str(e)}"
        }

@router.delete("/detailed-menus/{menu_id}")
async def delete_detailed_menu(menu_id: int, db: Session = Depends(get_db)):
    """세부식단표 삭제"""
    try:
        menu = db.query(Menu).filter(Menu.id == menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail="세부식단표를 찾을 수 없습니다")
        
        # 관련 데이터 확인 (실제로는 더 복잡한 체크가 필요)
        db.delete(menu)
        db.commit()
        
        return {
            "success": True,
            "message": "세부식단표가 삭제되었습니다"
        }
        
    except Exception as e:
        db.rollback()
        print(f"세부식단표 삭제 오류: {e}")
        return {
            "success": False,
            "message": f"삭제 중 오류가 발생했습니다: {str(e)}"
        }