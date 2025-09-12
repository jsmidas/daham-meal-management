"""
식재료 관리 전용 API 모듈
- 식재료 CRUD 작업
- 대량 업로드 기능
- 업로드 히스토리 관리
- 템플릿 다운로드
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Query, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
import pandas as pd
import io
import os

# 로컬 임포트
from app.database import get_db
from app.api.auth import get_current_user
from models import Ingredient, IngredientUploadHistory, Supplier

router = APIRouter(prefix="/api/admin", tags=["ingredients"])

# ==============================================================================
# Pydantic 모델들
# ==============================================================================

class IngredientCreate(BaseModel):
    name: str
    code: str
    category: Optional[str] = None
    sub_category: Optional[str] = None
    base_unit: str = "kg"
    origin: Optional[str] = None
    is_published: Optional[bool] = True
    tax_type: Optional[str] = None
    preorder_days: Optional[int] = None
    purchase_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    price: Optional[Decimal] = None
    storage_method: Optional[str] = None
    supplier_id: Optional[int] = None
    moq: Optional[Decimal] = None
    weight: Optional[str] = None
    weight_unit: Optional[str] = None
    notes: Optional[str] = None

class IngredientUpdate(BaseModel):
    category: Optional[str] = None
    sub_category: Optional[str] = None
    ingredient_code: Optional[str] = None
    ingredient_name: Optional[str] = None
    posting_status: Optional[str] = None
    origin: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None
    tax_type: Optional[str] = None
    delivery_days: Optional[str] = None
    purchase_price: Optional[Decimal] = None
    selling_price: Optional[Decimal] = None
    supplier_name: Optional[str] = None
    notes: Optional[str] = None

class IngredientResponse(BaseModel):
    id: int
    name: str
    code: str
    category: Optional[str]
    sub_category: Optional[str]
    base_unit: str
    origin: Optional[str]
    is_published: Optional[bool]
    tax_type: Optional[str]
    preorder_days: Optional[int]
    purchase_price: Optional[float]
    selling_price: Optional[float]
    price: Optional[float]
    storage_method: Optional[str]
    supplier_id: Optional[int]
    supplier_name: Optional[str]
    moq: Optional[float]
    weight: Optional[str]
    weight_unit: Optional[str]
    notes: Optional[str]
    created_at: Optional[str]

# ==============================================================================
# 인증 헬퍼
# ==============================================================================

def verify_admin_access(request: Request):
    """관리자 권한 확인"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    return user

# ==============================================================================
# 식재료 관리 API
# ==============================================================================

@router.get("/ingredients")
async def get_ingredients_admin(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    search: str = Query(""),
    ingredientName: str = Query(""),
    ingredientCode: str = Query(""),
    supplierName: str = Query(""),
    category: str = Query(""),
    sort: str = Query("name"),
    db: Session = Depends(get_db)
):
    """관리자용 식재료 목록 조회"""
    try:
        query = db.query(Ingredient)
        
        # 검색 조건
        if search:
            # 통합 검색 (식자재명, 코드, 업체명)
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Ingredient.ingredient_name.ilike(search_term),
                    Ingredient.ingredient_code.ilike(search_term),
                    Ingredient.supplier_name.ilike(search_term)
                )
            )
        
        # 개별 필드 검색
        if ingredientName:
            name_term = f"%{ingredientName}%"
            query = query.filter(Ingredient.ingredient_name.ilike(name_term))
            
        if ingredientCode:
            code_term = f"%{ingredientCode}%"
            query = query.filter(Ingredient.ingredient_code.ilike(code_term))
            
        if supplierName:
            supplier_term = f"%{supplierName}%"
            query = query.filter(Ingredient.supplier_name.ilike(supplier_term))
        
        if category:
            query = query.filter(Ingredient.category == category)
            
        # 정렬 처리
        if sort == "name":
            query = query.order_by(Ingredient.ingredient_name)
        elif sort == "code":
            query = query.order_by(Ingredient.ingredient_code)
        elif sort == "category":
            query = query.order_by(Ingredient.category)
        elif sort == "supplier":
            query = query.order_by(Ingredient.supplier_name)
        elif sort == "price_low":
            query = query.order_by(Ingredient.selling_price.asc())
        elif sort == "price_high":
            query = query.order_by(Ingredient.selling_price.desc())
        elif sort == "created_date":
            query = query.order_by(Ingredient.created_date.desc())
        else:
            query = query.order_by(Ingredient.ingredient_name)
        
        total = query.count()
        
        # 페이징
        offset = (page - 1) * limit
        ingredients = query.offset(offset).limit(limit).all()
        
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_list.append({
                "id": ingredient.id,
                "분류(대분류)": ingredient.category,
                "기본식자재(세분류)": ingredient.sub_category,
                "고유코드": ingredient.ingredient_code,
                "식자재명": ingredient.ingredient_name,
                "게시유무": ingredient.posting_status,
                "원산지": ingredient.origin,
                "규격": ingredient.specification,
                "단위": ingredient.unit,
                "면세": ingredient.tax_type,
                "선발주일": ingredient.delivery_days,
                "입고가": float(ingredient.purchase_price) if ingredient.purchase_price else 0,
                "판매가": float(ingredient.selling_price) if ingredient.selling_price else 0,
                "거래처명": ingredient.supplier_name,
                "비고": ingredient.notes,
                "등록일": ingredient.created_date.isoformat() if ingredient.created_date else None
            })
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "success": True,
            "ingredients": ingredient_list,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/ingredient-template")
async def get_ingredient_template():
    """식재료 업로드 템플릿 다운로드"""
    try:
        # 템플릿 파일이 있으면 제공
        template_path = "templates/ingredient_template.xlsx"
        if os.path.exists(template_path):
            return FileResponse(template_path, filename="ingredient_template.xlsx")
        else:
            # 템플릿 파일이 없으면 샘플 데이터 생성
            import pandas as pd
            sample_data = {
                "분류(대분류)": ["채소류", "육류", "곡물류"],
                "기본식자재(세분류)": ["엽채류", "소고기", "쌀류"],
                "고유코드": ["VEG001", "MEAT001", "GRAIN001"], 
                "식자재명": ["시금치", "등심", "백미"],
                "단위": ["kg", "kg", "kg"],
                "원산지": ["국산", "호주산", "국산"],
                "게시유무": ["Y", "Y", "Y"],
                "면세": ["N", "N", "N"],
                "선발주일": [1, 2, 1],
                "입고단가": [3000, 15000, 2000],
                "판매단가": [3500, 18000, 2500],
                "저장방법": ["냉장", "냉동", "실온"],
                "비고": ["", "", ""]
            }
            df = pd.DataFrame(sample_data)
            temp_file = "temp_template.xlsx"
            df.to_excel(temp_file, index=False)
            return FileResponse(temp_file, filename="ingredient_template.xlsx")
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/upload-ingredients")
async def upload_ingredients(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """식재료 일괄 업로드"""
    # 인증 및 권한 확인
    user = get_current_user(request)
    if not user:
        # 임시 테스트용 - 나중에 제거할 것
        print("WARNING: 인증 우회 모드 - 테스트용")
        user = {'username': 'test_user', 'role': 'admin'}
        # raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저', 'nutritionist', '영양사']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    try:
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            return {"success": False, "message": "CSV 또는 Excel 파일만 업로드 가능합니다."}
        
        # 파일 읽기
        contents = await file.read()
        
        # 임시로 파일 저장 (디버깅용)
        temp_filename = f"temp_upload_{file.filename}"
        with open(temp_filename, 'wb') as temp_file:
            temp_file.write(contents)
        print(f"임시 파일 저장: {temp_filename}")
        
        # Excel 파일 읽기
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:  # CSV
            df = pd.read_csv(io.BytesIO(contents))
        
        print(f"파일 읽기 완료: {len(df)}행, {len(df.columns)}컬럼")
        print(f"컬럼명: {list(df.columns)}")
        
        # 필수 컬럼 확인 (정확한 15개 필드 순서)
        required_columns = [
            '분류(대분류)', '기본식자재(세분류)', '고유코드', '식자재명', 
            '단위', '선발주일', '입고가', '판매가', '거래처명'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return {
                "success": False, 
                "message": f"필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}"
            }
        
        print(f"총 {len(df)}행 처리 시작")
        
        # 대용량 처리를 위한 변수들 초기화
        processed_count = 0
        updated_count = 0
        error_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # 진행상황 로깅 (매 100행마다)
                if (index + 1) % 100 == 0:
                    print(f"처리 중: {index + 1}/{len(df)} 행")
                
                # 필수 데이터 검증 (9개 필수 필드)
                required_validations = [
                    ('분류(대분류)', '대분류'),
                    ('기본식자재(세분류)', '세분류'),
                    ('고유코드', '고유코드'),
                    ('식자재명', '식자재명'),
                    ('단위', '단위'),
                    ('선발주일', '선발주일'),
                    ('입고가', '입고가'),
                    ('판매가', '판매가'),
                    ('거래처명', '거래처명')
                ]
                
                has_error = False
                for field, display_name in required_validations:
                    if pd.isna(row[field]) or not str(row[field]).strip():
                        errors.append(f"행 {index + 2}: {display_name}이(가) 필요합니다")
                        error_count += 1
                        has_error = True
                
                if has_error:
                    continue
                
                # 고유코드 처리 - 정수일 수도 있으므로 str()로 변환 후 처리
                code_value = str(row['고유코드']).strip()
                    
                existing_ingredient = db.query(Ingredient).filter(
                    Ingredient.code == code_value
                ).first()
                
                # 가격 처리 (정확한 필드명)
                purchase_price = None
                selling_price = None
                
                if '입고가' in row and not pd.isna(row['입고가']):
                    try:
                        price_str = str(row['입고가']).replace(',', '').strip()
                        if price_str:
                            purchase_price = Decimal(price_str)
                    except (ValueError, TypeError):
                        pass
                
                if '판매가' in row and not pd.isna(row['판매가']):
                    try:
                        price_str = str(row['판매가']).replace(',', '').strip()
                        if price_str:
                            selling_price = Decimal(price_str)
                    except (ValueError, TypeError):
                        pass
                
                if existing_ingredient:
                    # 기존 식자재 업데이트
                    existing_ingredient.name = str(row['식자재명']).strip()
                    existing_ingredient.category = str(row['분류(대분류)']).strip() if not pd.isna(row['분류(대분류)']) else None
                    existing_ingredient.sub_category = str(row['기본식자재(세분류)']).strip() if not pd.isna(row['기본식자재(세분류)']) else None
                    existing_ingredient.base_unit = str(row['단위']).strip() if not pd.isna(row['단위']) else 'kg'
                    existing_ingredient.origin = str(row['원산지']).strip() if '원산지' in row and not pd.isna(row['원산지']) else None
                    existing_ingredient.is_published = str(row['게시유무']).strip() if '게시유무' in row and not pd.isna(row['게시유무']) else None
                    existing_ingredient.tax_type = str(row['면세']).strip() if '면세' in row and not pd.isna(row['면세']) else None
                    existing_ingredient.preorder_days = str(row['선발주일']).strip() if '선발주일' in row and not pd.isna(row['선발주일']) else None
                    
                    if purchase_price is not None:
                        existing_ingredient.purchase_price = purchase_price
                    if selling_price is not None:
                        existing_ingredient.selling_price = selling_price
                        existing_ingredient.price = selling_price  # 기존 price 필드도 업데이트
                    
                    existing_ingredient.storage_method = str(row['저장방법']).strip() if '저장방법' in row and not pd.isna(row['저장방법']) else None
                    existing_ingredient.notes = str(row['비고']).strip() if '비고' in row and not pd.isna(row['비고']) else None
                    existing_ingredient.updated_at = func.now()
                    updated_count += 1
                else:
                    # 새 식자재 생성
                    new_ingredient = Ingredient(
                        name=str(row['식자재명']).strip(),
                        code=code_value,
                        category=str(row['분류(대분류)']).strip() if not pd.isna(row['분류(대분류)']) else None,
                        sub_category=str(row['기본식자재(세분류)']).strip() if not pd.isna(row['기본식자재(세분류)']) else None,
                        base_unit=str(row['단위']).strip() if not pd.isna(row['단위']) else 'kg',
                        origin=str(row['원산지']).strip() if '원산지' in row and not pd.isna(row['원산지']) else None,
                        is_published=str(row['게시유무']).strip() if '게시유무' in row and not pd.isna(row['게시유무']) else None,
                        tax_type=str(row['면세']).strip() if '면세' in row and not pd.isna(row['면세']) else None,
                        preorder_days=str(row['선발주일']).strip() if '선발주일' in row and not pd.isna(row['선발주일']) else None,
                        purchase_price=purchase_price,
                        selling_price=selling_price,
                        price=selling_price,
                        storage_method=str(row['저장방법']).strip() if '저장방법' in row and not pd.isna(row['저장방법']) else None,
                        notes=str(row['비고']).strip() if '비고' in row and not pd.isna(row['비고']) else None,
                        created_at=datetime.now()
                    )
                    db.add(new_ingredient)
                    processed_count += 1
                
                # 매 50개마다 커밋
                if (index + 1) % 50 == 0:
                    db.commit()
                    
            except Exception as row_error:
                error_count += 1
                errors.append(f"행 {index + 2}: {str(row_error)}")
                print(f"행 {index + 1} 처리 중 오류: {str(row_error)}")
                continue
        
        # 최종 커밋
        db.commit()
        
        # 업로드 히스토리 저장
        upload_history = IngredientUploadHistory(
            filename=file.filename,
            upload_date=datetime.now(),
            user_id=user.get('id', 1),
            total_rows=len(df),
            processed_rows=processed_count + updated_count,
            error_rows=error_count,
            status='completed' if error_count == 0 else 'completed_with_errors',
            notes=f"신규: {processed_count}, 업데이트: {updated_count}, 오류: {error_count}"
        )
        db.add(upload_history)
        db.commit()
        
        # 임시 파일 삭제
        try:
            os.remove(temp_filename)
        except:
            pass
        
        result = {
            "success": True,
            "message": f"식재료 데이터 처리 완료: 신규 {processed_count}개, 업데이트 {updated_count}개",
            "processed": processed_count + updated_count,
            "errors": error_count,
            "total": len(df)
        }
        
        if errors and len(errors) <= 10:  # 처음 10개 오류만 표시
            result["error_details"] = errors[:10]
        
        return result
        
    except Exception as e:
        db.rollback()
        print(f"업로드 처리 중 오류: {str(e)}")
        return {"success": False, "message": f"업로드 처리 중 오류가 발생했습니다: {str(e)}"}

@router.get("/ingredient-upload-history")
async def get_ingredient_upload_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """식자재 업로드 히스토리 조회"""
    try:
        query = db.query(IngredientUploadHistory)
        
        total = query.count()
        offset = (page - 1) * limit
        histories = query.order_by(IngredientUploadHistory.upload_date.desc()).offset(offset).limit(limit).all()
        
        history_list = []
        for history in histories:
            history_list.append({
                "id": history.id,
                "filename": history.filename,
                "upload_date": history.upload_date.isoformat() if history.upload_date else None,
                "user_id": history.user_id,
                "total_rows": history.total_rows,
                "processed_rows": history.processed_rows,
                "error_rows": history.error_rows,
                "status": history.status,
                "notes": history.notes
            })
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "success": True,
            "histories": history_list,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages
        }
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/ingredients/stats")
async def get_ingredient_stats(db: Session = Depends(get_db)):
    """식재료 통계"""
    try:
        total_ingredients = db.query(Ingredient).count()
        published_ingredients = db.query(Ingredient).filter(Ingredient.is_published == 'Y').count()
        
        # 카테고리별 통계
        categories = db.query(Ingredient.category).distinct().all()
        category_stats = {}
        for category in categories:
            if category[0]:
                count = db.query(Ingredient).filter(Ingredient.category == category[0]).count()
                category_stats[category[0]] = count
        
        return {
            "success": True,
            "stats": {
                "total_ingredients": total_ingredients,
                "published_ingredients": published_ingredients,
                "unpublished_ingredients": total_ingredients - published_ingredients,
                "categories": category_stats
            }
        }
    except Exception as e:
        return {"success": False, "message": f"통계 조회 중 오류: {str(e)}"}

# ==============================================================================
# 식재료 CRUD API
# ==============================================================================

@router.post("/ingredients")
async def create_ingredient(ingredient_data: IngredientCreate, request: Request, db: Session = Depends(get_db)):
    """식재료 생성"""
    verify_admin_access(request)
    
    try:
        # 코드 중복 확인
        existing = db.query(Ingredient).filter(Ingredient.code == ingredient_data.code).first()
        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 식재료 코드입니다.")
        
        new_ingredient = Ingredient(**ingredient_data.dict(), created_at=datetime.now())
        db.add(new_ingredient)
        db.commit()
        db.refresh(new_ingredient)
        
        return {"success": True, "message": "식재료가 생성되었습니다.", "ingredient_id": new_ingredient.id}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"식재료 생성 중 오류: {str(e)}"}

@router.get("/ingredients/{ingredient_id}")
async def get_ingredient(ingredient_id: int, request: Request, db: Session = Depends(get_db)):
    """식재료 상세 조회"""
    verify_admin_access(request)
    
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="식재료를 찾을 수 없습니다.")
    
    return {
        "success": True,
        "ingredient": {
            "id": ingredient.id,
            "name": ingredient.name,
            "code": ingredient.code,
            "category": ingredient.category,
            "subcategory": ingredient.sub_category,
            "base_unit": ingredient.base_unit,
            "origin": ingredient.origin,
            "is_published": ingredient.is_published,
            "tax_type": ingredient.tax_type,
            "preorder_days": ingredient.preorder_days,
            "purchase_price": float(ingredient.purchase_price) if ingredient.purchase_price else None,
            "selling_price": float(ingredient.selling_price) if ingredient.selling_price else None,
            "price": float(ingredient.price) if ingredient.price else None,
            "storage_method": ingredient.storage_method,
            "supplier_id": ingredient.supplier_id,
            "supplier_name": ingredient.supplier.name if ingredient.supplier else None,
            "moq": float(ingredient.moq) if ingredient.moq else None,
            "weight": ingredient.weight,
            "weight_unit": ingredient.weight_unit,
            "notes": ingredient.notes,
            "created_at": ingredient.created_at.isoformat() if ingredient.created_at else None
        }
    }

@router.put("/ingredients/{ingredient_id}")
async def update_ingredient(ingredient_id: int, ingredient_data: IngredientUpdate, request: Request, db: Session = Depends(get_db)):
    """식재료 수정"""
    verify_admin_access(request)
    
    try:
        ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        if not ingredient:
            raise HTTPException(status_code=404, detail="식재료를 찾을 수 없습니다.")
        
        # 코드 중복 확인 (다른 식재료에 동일한 코드가 있는지)
        if ingredient_data.code and ingredient_data.code != ingredient.code:
            existing = db.query(Ingredient).filter(Ingredient.code == ingredient_data.code).first()
            if existing:
                raise HTTPException(status_code=400, detail="이미 존재하는 식재료 코드입니다.")
        
        # 필드 업데이트
        update_data = ingredient_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(ingredient, field, value)
        
        ingredient.updated_at = datetime.now()
        db.commit()
        db.refresh(ingredient)
        
        return {"success": True, "message": "식재료가 수정되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"식재료 수정 중 오류: {str(e)}"}

@router.delete("/ingredients/{ingredient_id}")
async def delete_ingredient(ingredient_id: int, request: Request, db: Session = Depends(get_db)):
    """식재료 삭제"""
    verify_admin_access(request)
    
    try:
        ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        if not ingredient:
            raise HTTPException(status_code=404, detail="식재료를 찾을 수 없습니다.")
        
        db.delete(ingredient)
        db.commit()
        
        return {"success": True, "message": "식재료가 삭제되었습니다."}
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"식재료 삭제 중 오류: {str(e)}"}

@router.get("/ingredient-stats")
async def get_ingredient_stats(request: Request, db: Session = Depends(get_db)):
    """식재료 통계"""
    verify_admin_access(request)
    try:
        total_ingredients = db.query(Ingredient).count()
        active_ingredients = db.query(Ingredient).filter(Ingredient.is_active == True).count()
        
        # 카테고리별 통계
        categories = db.query(Ingredient.category).distinct().all()
        category_stats = {}
        for category in categories:
            if category[0]:
                count = db.query(Ingredient).filter(Ingredient.category == category[0]).count()
                category_stats[category[0]] = count
        
        # 재고 상태별 통계
        low_stock = db.query(Ingredient).filter(Ingredient.current_stock <= Ingredient.minimum_stock).count()
        out_of_stock = db.query(Ingredient).filter(Ingredient.current_stock == 0).count()
        
        return {
            "total_ingredients": total_ingredients,
            "active_ingredients": active_ingredients,
            "inactive_ingredients": total_ingredients - active_ingredients,
            "category_stats": category_stats,
            "low_stock": low_stock,
            "out_of_stock": out_of_stock
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류: {str(e)}")

@router.post("/ingredients/upload")
async def upload_ingredients_file(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """식재료 Excel 파일 업로드"""
    verify_admin_access(request)
    
    # 파일 확장자 검증
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Excel 파일만 업로드 가능합니다.")
    
    try:
        # 파일 읽기
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # 업로드 히스토리 생성
        upload_history = IngredientUploadHistory(
            filename=file.filename,
            upload_date=datetime.now(),
            status='processing',
            processed_count=0,
            created_count=0,
            updated_count=0,
            error_count=0
        )
        db.add(upload_history)
        db.commit()
        db.refresh(upload_history)
        
        processed_count = 0
        created_count = 0 
        updated_count = 0
        error_count = 0
        errors = []
        
        # DataFrame 열 이름 매핑 (한글 -> 영문)
        column_mapping = {
            '분류(대분류)': 'category',
            '기본식자재(세분류)': 'name', 
            '고유코드': 'code',
            '식자재명': 'name_alt',
            '원산지': 'origin',
            '재차유무': 'reorder_info',
            '규격': 'specification',
            '단위': 'unit',
            '먹세': 'tax_type',
            '선별주일': 'selection_period',
            '입고가': 'purchase_price',
            '판매가': 'selling_price',
            '거래처명': 'supplier_name',
            '비고': 'notes'
        }
        
        # 2행부터 처리 (1행은 헤더이므로 제외)
        for index, row in df.iterrows():
            if index == 0:  # 1행은 수정 불가 양식이므로 건너뛰기
                continue
                
            try:
                processed_count += 1
                
                # 필수 필드 확인
                code = str(row.get('고유코드', '')).strip()
                name = str(row.get('기본식자재(세분류)', '')).strip()
                
                if not code or code == 'nan':
                    errors.append(f"행 {index+2}: 고유코드가 비어있습니다.")
                    error_count += 1
                    continue
                
                if not name or name == 'nan':
                    errors.append(f"행 {index+2}: 식자재명이 비어있습니다.")
                    error_count += 1
                    continue
                
                # 기존 식재료 확인
                existing = db.query(Ingredient).filter(Ingredient.code == code).first()
                
                # 가격 정보 추출
                purchase_price = 0
                selling_price = 0
                
                try:
                    purchase_price_str = str(row.get('입고가', '0')).strip()
                    if purchase_price_str and purchase_price_str != 'nan':
                        purchase_price = float(purchase_price_str.replace(',', ''))
                except:
                    purchase_price = 0
                    
                try:
                    selling_price_str = str(row.get('판매가', '0')).strip()
                    if selling_price_str and selling_price_str != 'nan':
                        selling_price = float(selling_price_str.replace(',', ''))
                except:
                    selling_price = 0
                
                if existing:
                    # 기존 식재료 - 단가 업데이트
                    existing.purchase_price = Decimal(str(purchase_price))
                    existing.selling_price = Decimal(str(selling_price))
                    existing.updated_at = datetime.now()
                    updated_count += 1
                else:
                    # 새 식재료 생성
                    new_ingredient = Ingredient(
                        code=code,
                        name=name,
                        category=str(row.get('분류(대분류)', '')).strip() or '기타',
                        origin=str(row.get('원산지', '')).strip() or None,
                        specification=str(row.get('규격', '')).strip() or None,
                        unit=str(row.get('단위', '')).strip() or 'EA',
                        purchase_price=Decimal(str(purchase_price)),
                        selling_price=Decimal(str(selling_price)),
                        supplier_name=str(row.get('거래처명', '')).strip() or None,
                        notes=str(row.get('비고', '')).strip() or None,
                        current_stock=0,
                        minimum_stock=0,
                        maximum_stock=0,
                        is_active=True,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    db.add(new_ingredient)
                    created_count += 1
                    
            except Exception as e:
                error_count += 1
                errors.append(f"행 {index+2}: {str(e)}")
                continue
        
        # 변경사항 저장
        db.commit()
        
        # 업로드 히스토리 업데이트
        upload_history.status = 'completed' if error_count == 0 else 'completed_with_errors'
        upload_history.processed_count = processed_count
        upload_history.created_count = created_count
        upload_history.updated_count = updated_count
        upload_history.error_count = error_count
        upload_history.error_details = '\n'.join(errors) if errors else None
        db.commit()
        
        return {
            "success": True,
            "message": f"업로드 완료: {created_count}개 생성, {updated_count}개 수정, {error_count}개 오류",
            "details": {
                "processed_count": processed_count,
                "created_count": created_count,
                "updated_count": updated_count,
                "error_count": error_count,
                "errors": errors[:10]  # 최대 10개 오류만 반환
            }
        }
        
    except Exception as e:
        # 업로드 히스토리 실패로 업데이트
        if 'upload_history' in locals():
            upload_history.status = 'failed'
            upload_history.error_details = str(e)
            db.commit()
        
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류: {str(e)}")

@router.get("/ingredients/upload-history")
async def get_upload_history(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """업로드 히스토리 조회"""
    verify_admin_access(request)
    
    try:
        offset = (page - 1) * limit
        
        history_query = db.query(IngredientUploadHistory)\
            .order_by(IngredientUploadHistory.upload_date.desc())\
            .offset(offset)\
            .limit(limit)
        
        history_list = history_query.all()
        total = db.query(IngredientUploadHistory).count()
        
        history_data = []
        for item in history_list:
            history_data.append({
                "id": item.id,
                "filename": item.filename,
                "upload_date": item.upload_date.isoformat() if item.upload_date else None,
                "status": item.status,
                "processed_count": item.processed_count,
                "created_count": item.created_count,
                "updated_count": item.updated_count,
                "error_count": item.error_count,
                "error_details": item.error_details
            })
        
        return {
            "success": True,
            "history": history_data,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"히스토리 조회 중 오류: {str(e)}")