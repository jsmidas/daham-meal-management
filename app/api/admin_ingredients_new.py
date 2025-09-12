"""
식자재 관리 API 모듈 (신규)
- 식자재 등록 (엑셀 업로드)
- 식자재 조회 (페이지네이션, 검색, 필터)
- 식자재 수정/삭제
- 통계 정보
"""

from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, func, or_, and_
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel
import pandas as pd
import io
import os

# 로컬 임포트
from app.database import get_db
from app.api.auth import get_current_user
from models import Ingredient, IngredientUploadHistory

router = APIRouter(prefix="/api/admin", tags=["ingredients"])

# ==============================================================================
# Pydantic 모델들
# ==============================================================================

class IngredientResponse(BaseModel):
    id: int
    분류_대분류: str = None
    기본식자재_세분류: str = None
    고유코드: str = None
    식자재명: str
    원산지: str = None
    게시여부: str = None
    입고명: str = None
    단위: str = None
    과세: str = None
    배송일수: str = None
    입고가: float = None
    판매가: float = None
    판매처명: str = None
    비고: str = None
    여유필드1: str = None
    여유필드2: str = None
    여유필드3: str = None
    is_active: bool = True
    created_at: str
    updated_at: str

class IngredientCreate(BaseModel):
    category: str
    sub_category: str
    ingredient_code: str
    ingredient_name: str
    origin: Optional[str] = None
    posting_status: Optional[str] = "유"
    specification: Optional[str] = None
    unit: str
    tax_type: Optional[str] = "과세"
    delivery_days: int
    purchase_price: float
    selling_price: float
    supplier_name: str
    notes: Optional[str] = None

class IngredientUpdate(BaseModel):
    category: Optional[str] = None
    sub_category: Optional[str] = None
    ingredient_code: Optional[str] = None
    ingredient_name: Optional[str] = None
    origin: Optional[str] = None
    posting_status: Optional[str] = None
    specification: Optional[str] = None
    unit: Optional[str] = None
    tax_type: Optional[str] = None
    delivery_days: Optional[int] = None
    purchase_price: Optional[float] = None
    selling_price: Optional[float] = None
    supplier_name: Optional[str] = None
    notes: Optional[str] = None

# ==============================================================================
# 인증 헬퍼
# ==============================================================================

def verify_admin_access(request: Request):
    """관리자 권한 확인"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    
    admin_roles = ['admin', 'manager', '관리자', '매니저']
    if user['role'] not in admin_roles:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    return user

# ==============================================================================
# 식자재 조회 API
# ==============================================================================

@router.get("/ingredients-new")
async def get_ingredients(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200000),
    search: str = Query("", description="식자재명 검색"),
    code_search: str = Query("", description="식자재 코드 검색"),
    supplier: str = Query("", description="공급업체 필터"),
    category: str = Query("", description="분류 필터"),
    active_only: bool = Query(True, description="활성 식자재만 조회"),
    db: Session = Depends(get_db)
):
    print("[GET DEBUG] ===== GET ingredients-new 호출됨 =====")
    """식자재 목록 조회 (페이지네이션, 검색, 필터 지원)"""
    try:
        # 기본 쿼리
        query = db.query(Ingredient)
        
        # 필터 적용
        if active_only:
            query = query.filter(Ingredient.is_active == True)
            
        if search:
            query = query.filter(
                or_(
                    Ingredient.ingredient_name.contains(search),
                    Ingredient.product_name.contains(search)
                )
            )
            
        if code_search:
            query = query.filter(Ingredient.ingredient_code.contains(code_search))
            
        if supplier:
            query = query.filter(Ingredient.supplier_name.contains(supplier))
            
        if category:
            query = query.filter(
                or_(
                    Ingredient.category.contains(category),
                    Ingredient.sub_category.contains(category)
                )
            )
        
        # 총 개수
        total = query.count()
        
        # 페이지네이션
        offset = (page - 1) * limit
        ingredients = query.order_by(Ingredient.created_at.desc()).offset(offset).limit(limit).all()
        
        # 응답 데이터 구성
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_list.append({
                "id": ingredient.id,
                "category": ingredient.category,
                "sub_category": ingredient.sub_category,
                "ingredient_code": ingredient.ingredient_code,
                "ingredient_name": ingredient.ingredient_name,
                "origin": ingredient.origin,
                "posting_status": ingredient.posting_status,
                "specification": ingredient.specification,
                "unit": ingredient.unit,
                "tax_type": ingredient.tax_type,
                "delivery_days": ingredient.delivery_days,
                "purchase_price": float(ingredient.purchase_price) if ingredient.purchase_price else 0,
                "selling_price": float(ingredient.selling_price) if ingredient.selling_price else 0,
                "supplier_name": ingredient.supplier_name,
                "notes": ingredient.notes,
                "is_active": ingredient.is_active,
                "created_at": str(ingredient.created_at),
                "updated_at": str(ingredient.updated_at)
            })
        
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        
        return {
            "success": True,
            "ingredients": ingredient_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages
            }
        }
        
    except Exception as e:
        print(f"[DEBUG] Exception in get_ingredients: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "message": f"식자재 조회 중 오류: {str(e)}"}

@router.get("/ingredients-new/stats/suppliers")
async def get_suppliers_stats(db: Session = Depends(get_db)):
    """업체별 식자재 통계"""
    try:
        # 업체별 식자재 수, 최근 업데이트 날짜 조회 (평균 가격 제거)
        suppliers_stats = db.query(
            Ingredient.supplier_name,
            func.count(Ingredient.id).label('ingredient_count'),
            func.max(Ingredient.updated_at).label('last_update')
        ).filter(
            Ingredient.is_active == True,
            Ingredient.supplier_name.isnot(None)
        ).group_by(Ingredient.supplier_name).all()
        
        # 결과 포맷팅
        result = []
        for stat in suppliers_stats:
            supplier_name = stat[0] if stat[0] else '미지정'
            ingredient_count = stat[1]
            last_update = stat[2]
            
            result.append({
                'supplier_name': supplier_name,
                'ingredient_count': ingredient_count,
                'last_update': str(last_update) if last_update else None
            })
        
        # 식자재 수 기준으로 내림차순 정렬
        result.sort(key=lambda x: x['ingredient_count'], reverse=True)
        
        return {
            "success": True,
            "suppliers_stats": result
        }
        
    except Exception as e:
        return {"success": False, "message": f"업체별 통계 조회 중 오류: {str(e)}"}


@router.get("/ingredients-stats")
async def get_ingredients_stats(db: Session = Depends(get_db)):
    """식자재 통계 정보"""
    try:
        # 기본 통계
        total_count = db.query(Ingredient).filter(Ingredient.is_active == True).count()
        total_suppliers = db.query(func.count(func.distinct(Ingredient.supplier_name))).filter(
            Ingredient.is_active == True,
            Ingredient.supplier_name.isnot(None)
        ).scalar() or 0
        
        # 평균 판매가
        avg_price_result = db.query(func.avg(Ingredient.selling_price)).filter(
            Ingredient.is_active == True,
            Ingredient.selling_price.isnot(None)
        ).scalar()
        avg_price = float(avg_price_result) if avg_price_result else 0
        
        # 최소/최대 판매가
        min_price_result = db.query(func.min(Ingredient.selling_price)).filter(
            Ingredient.is_active == True,
            Ingredient.selling_price.isnot(None),
            Ingredient.selling_price > 0
        ).scalar()
        max_price_result = db.query(func.max(Ingredient.selling_price)).filter(
            Ingredient.is_active == True,
            Ingredient.selling_price.isnot(None)
        ).scalar()
        
        min_price = float(min_price_result) if min_price_result else 0
        max_price = float(max_price_result) if max_price_result else 0
        
        # 최근 7일 내 등록된 식자재
        from datetime import timedelta
        recent_date = datetime.now() - timedelta(days=7)
        recent_uploads = db.query(Ingredient).filter(
            Ingredient.created_at >= recent_date,
            Ingredient.is_active == True
        ).count()
        
        # 대분류별 통계
        category_stats = db.query(
            Ingredient.category,
            func.count(Ingredient.id).label('count')
        ).filter(
            Ingredient.is_active == True,
            Ingredient.category.isnot(None)
        ).group_by(Ingredient.category).all()
        
        category_breakdown = [{"category": cat[0], "count": cat[1]} for cat in category_stats]
        
        # 필수 필드 누락 통계 (대분류, 세분류, 고유코드, 식자재명, 단위, 선발주일, 입고가, 판매가, 업체명)
        missing_stats = {}
        required_fields = {
            "category": "대분류",
            "sub_category": "세분류", 
            "ingredient_code": "고유코드",
            "ingredient_name": "식자재명",
            "unit": "단위",
            "delivery_days": "선발주일",
            "purchase_price": "입고가",
            "selling_price": "판매가",
            "supplier_name": "업체명"
        }
        
        for field, label in required_fields.items():
            missing_count = db.query(Ingredient).filter(
                Ingredient.is_active == True,
                or_(
                    getattr(Ingredient, field).is_(None),
                    getattr(Ingredient, field) == '',
                    getattr(Ingredient, field) == 0 if field in ['purchase_price', 'selling_price', 'delivery_days'] else False
                )
            ).count()
            missing_stats[label] = missing_count
        
        # 최근 업로드 정보
        latest_upload = db.query(IngredientUploadHistory).order_by(
            IngredientUploadHistory.upload_date.desc()
        ).first()
        
        latest_upload_info = None
        if latest_upload:
            latest_upload_info = {
                "upload_date": str(latest_upload.upload_date),
                "uploaded_by": latest_upload.uploaded_by,
                "total_rows": latest_upload.total_rows,
                "processed_count": latest_upload.processed_count,
                "error_count": latest_upload.error_count
            }
        
        return {
            "success": True,
            "stats": {
                "total_ingredients": total_count,
                "total_suppliers": total_suppliers,
                "avg_selling_price": avg_price,
                "min_selling_price": min_price,
                "max_selling_price": max_price,
                "recent_uploads": recent_uploads,
                "category_breakdown": category_breakdown,
                "missing_required_fields": missing_stats,
                "latest_upload": latest_upload_info
            }
        }
        
    except Exception as e:
        return {"success": False, "message": f"통계 조회 중 오류: {str(e)}"}

@router.get("/ingredients-new/suppliers")
async def get_suppliers_list(db: Session = Depends(get_db)):
    """공급업체 목록 조회"""
    try:
        suppliers = db.query(func.distinct(Ingredient.supplier_name)).filter(
            Ingredient.supplier_name.isnot(None),
            Ingredient.is_active == True
        ).all()
        
        supplier_list = [supplier[0] for supplier in suppliers if supplier[0]]
        
        return {
            "success": True,
            "suppliers": sorted(supplier_list)
        }
        
    except Exception as e:
        return {"success": False, "message": f"공급업체 목록 조회 중 오류: {str(e)}"}

# ==============================================================================
# 식자재 등록/수정/삭제 API
# ==============================================================================

@router.post("/ingredients-new")
async def create_ingredient(ingredient_data: IngredientCreate, request: Request, db: Session = Depends(get_db)):
    """식자재 개별 등록"""
    user = verify_admin_access(request)
    
    try:
        # 중복 코드 체크
        if ingredient_data.ingredient_code:
            existing = db.query(Ingredient).filter(
                Ingredient.ingredient_code == ingredient_data.ingredient_code
            ).first()
            if existing:
                return {"success": False, "message": "이미 존재하는 식자재 코드입니다."}
        
        # 새 식자재 생성
        new_ingredient = Ingredient(
            category=ingredient_data.category,
            sub_category=ingredient_data.sub_category,
            ingredient_code=ingredient_data.ingredient_code,
            ingredient_name=ingredient_data.ingredient_name,
            origin=ingredient_data.origin,
            posting_status=ingredient_data.posting_status,
            specification=ingredient_data.specification,
            unit=ingredient_data.unit,
            tax_type=ingredient_data.tax_type,
            delivery_days=ingredient_data.delivery_days,
            purchase_price=ingredient_data.purchase_price,
            selling_price=ingredient_data.selling_price,
            supplier_name=ingredient_data.supplier_name,
            notes=ingredient_data.notes,
            extra_field1=ingredient_data.extra_field1,
            extra_field2=ingredient_data.extra_field2,
            extra_field3=ingredient_data.extra_field3,
            created_by=user['username']
        )
        
        db.add(new_ingredient)
        db.commit()
        db.refresh(new_ingredient)
        
        return {
            "success": True,
            "message": "식자재가 등록되었습니다.",
            "ingredient_id": new_ingredient.id
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"식자재 등록 중 오류: {str(e)}"}

# ==============================================================================
# 엑셀 업로드 API
# ==============================================================================

@router.post("/ingredients-new/upload")
async def upload_ingredients_excel(
    file: UploadFile = File(...),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """식자재 엑셀 파일 업로드 (대용량 10만건 최적화)"""
    print(f"[UPLOAD DEBUG] ===== 업로드 함수 진입 =====")
    print(f"[UPLOAD DEBUG] 파일명: {file.filename}, 크기: {file.size}")
    print(f"[UPLOAD DEBUG] 인증 시작...")
    
    user = verify_admin_access(request)
    print(f"[UPLOAD DEBUG] 사용자 인증 완료: {user}")
    
    try:
        # 파일 확장자 확인
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            return {"success": False, "message": "엑셀 파일만 업로드 가능합니다."}
        
        # 파일 읽기
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # 업로드 히스토리 생성
        upload_history = IngredientUploadHistory(
            filename=file.filename,
            uploaded_by=user['username'],
            total_rows=len(df),
            status='processing'
        )
        db.add(upload_history)
        db.commit()
        db.refresh(upload_history)
        
        # 대용량 데이터 처리 최적화 (2만건 대응)
        processed_count = 0
        updated_count = 0
        error_count = 0
        error_details = []
        error_rows = []  # 오류 행 데이터 저장용
        
        # Excel 구조 정확히 일치하는 컬럼 매핑 (한글 컬럼명 -> 영문 프로퍼티명)
        column_mapping = {
            '분류(대분류)': 'category',
            '기본식자재(세분류)': 'sub_category',
            '고유코드': 'ingredient_code',
            '식자재명': 'ingredient_name',
            '원산지': 'origin',
            '게시유무': 'posting_status',
            '규격': 'specification',
            '단위': 'unit',
            '면세': 'tax_type',
            '선발주일': 'delivery_days',
            '입고가': 'purchase_price',
            '판매가': 'selling_price',
            '거래처명': 'supplier_name',
            '비고': 'notes'
        }
        
        # 대용량 데이터 최적화 (10만건 대응)
        batch_size = 2000  # 2000개씩 배치 처리 (더 큰 배치로 성능 향상)
        new_ingredients = []
        update_ingredients = []
        
        # 기존 식자재 코드들을 한 번에 조회 (성능 최적화)
        existing_codes = set()
        existing_ingredients_map = {}
        
        # 엑셀에서 코드가 있는 행들만 필터링해서 DB 조회
        codes_in_excel = []
        for index, row in df.iterrows():
            code = row.get('고유코드')
            if pd.notna(code) and str(code).strip():
                codes_in_excel.append(str(code).strip())
        
        if codes_in_excel:
            existing_query = db.query(Ingredient).filter(Ingredient.ingredient_code.in_(codes_in_excel)).all()
            for ingredient in existing_query:
                existing_codes.add(ingredient.ingredient_code)
                existing_ingredients_map[ingredient.ingredient_code] = ingredient
        
        print(f"[DEBUG] 기존 식자재 {len(existing_codes)}개 조회 완료")
        
        # 대용량 처리를 위한 진행률 추적
        total_rows = len(df)
        progress_step = max(1, total_rows // 10)  # 10% 단위로 진행률 출력
        
        # 데이터 처리 (행별 처리)
        for index, row in df.iterrows():
            # 진행률 출력 (10% 단위)
            if index % progress_step == 0:
                progress = (index / total_rows) * 100
                print(f"[DEBUG] 처리 진행률: {progress:.1f}% ({index}/{total_rows})")
                
                # 업로드 히스토리 상태 업데이트 (중간 저장)
                upload_history.processed_count = processed_count
                upload_history.updated_count = updated_count
                upload_history.error_count = error_count
                db.commit()
            try:
                # 행 디버깅 (처음 3행만)
                if index < 3:
                    print(f"[DEBUG] 행 {index + 1} 데이터:")
                    for col in df.columns:
                        value = row[col]
                        print(f"  {col}: '{value}' (type: {type(value)}, isna: {pd.isna(value)})")
                
                # 필수 필드 체크 (대분류, 세분류, 고유코드, 식자재명, 단위, 선발주일, 입고가, 판매가, 업체명)
                required_checks = [
                    ('분류(대분류)', '대분류'),
                    ('기본식자재(세분류)', '세분류'),
                    ('고유코드', '고유코드'),
                    ('식자재명', '식자재명'),
                    ('단위', '단위'),
                    ('선발주일', '선발주일'),
                    ('입고가', '입고가'),
                    ('판매가', '판매가'),
                    ('거래처명', '업체명')
                ]
                
                validation_failed = False
                for col_name, field_label in required_checks:
                    value = row.get(col_name)
                    if pd.isna(value) or str(value).strip() == '':
                        print(f"[DEBUG] 행 {index + 2}: {field_label}이(가) 없어서 오류 추가")
                        error_details.append(f"행 {index + 2}: {field_label}은(는) 필수입니다.")
                        validation_failed = True
                    elif col_name in ['입고가', '판매가', '선발주일']:
                        # 숫자 필드 추가 검증
                        try:
                            num_value = float(str(value).replace(',', ''))
                            if num_value <= 0:
                                print(f"[DEBUG] 행 {index + 2}: {field_label}이(가) 0 이하여서 오류 추가")
                                error_details.append(f"행 {index + 2}: {field_label}은(는) 0보다 큰 값이어야 합니다.")
                                validation_failed = True
                        except (ValueError, TypeError):
                            print(f"[DEBUG] 행 {index + 2}: {field_label}이(가) 숫자가 아니어서 오류 추가")
                            error_details.append(f"행 {index + 2}: {field_label}은(는) 유효한 숫자여야 합니다.")
                            validation_failed = True
                
                if validation_failed:
                    error_count += 1
                    # 오류 행 데이터 저장 (Excel 다운로드용)
                    error_row_dict = row.to_dict()
                    error_row_dict['행번호'] = index + 2
                    error_rows.append(error_row_dict)
                    continue
                
                # 데이터 변환 함수
                def convert_korean_values(property_name, value):
                    """영문 값들을 한국어로 변환"""
                    if pd.isna(value):
                        return None
                    
                    value_str = str(value).strip()
                    
                    # 게시유무 변환: 게시 = 유, 주문불가 = 무
                    if property_name == 'posting_status':
                        if value_str.lower() in ['게시', 'published', 'active', 'y', 'yes', '유']:
                            return '유'
                        elif value_str.lower() in ['주문불가', 'unavailable', 'inactive', 'n', 'no', '무']:
                            return '무'
                        return value_str  # 빈값이나 기타 값은 그대로
                    
                    # 면세 변환: Full tax = 과세, No tax = 면세
                    elif property_name == 'tax_type':
                        if value_str.lower() in ['full tax', 'tax', 'taxed', '과세']:
                            return '과세'
                        elif value_str.lower() in ['no tax', 'tax free', 'exempt', '면세']:
                            return '면세'
                        return value_str  # 빈값이나 기타 값은 그대로
                    
                    # 선발주일 변환: D-1,1,+1→'1', D-2,2,+2→'2', D-3,3,+3→'3'
                    elif property_name == 'delivery_days':
                        # 숫자 추출 (D-1, +1, 1 등에서 숫자만 추출)
                        import re
                        numbers = re.findall(r'\d+', value_str)
                        if numbers:
                            return numbers[0]  # 첫 번째 숫자만 사용
                        return value_str
                    
                    # 규격 정리: 업체명이 들어간 경우 쉼표, 띄어쓰기 포함해서 제거
                    elif property_name == 'specification':
                        import re
                        # 업체명 패턴들을 제거 (업체, 회사, (주), 합자회사, 유한회사 등)
                        company_patterns = [
                            r'[가-힣]+\s*업체\s*[,\s]*',
                            r'[가-힣]+\s*회사\s*[,\s]*',
                            r'\(주\)\s*[가-힣]+\s*[,\s]*',
                            r'[가-힣]+\s*\(주\)\s*[,\s]*',
                            r'유한회사\s*[가-힣]+\s*[,\s]*',
                            r'[가-힣]+\s*유한회사\s*[,\s]*',
                            r'합자회사\s*[가-힣]+\s*[,\s]*',
                            r'[가-힣]+\s*합자회사\s*[,\s]*',
                            r'[가-힣]*[상사]\s*[,\s]*',
                            r'[가-힣]*[푸드|식품]\s*[,\s]*'
                        ]
                        
                        cleaned_value = value_str
                        for pattern in company_patterns:
                            cleaned_value = re.sub(pattern, '', cleaned_value, flags=re.IGNORECASE)
                        
                        # 앞뒤 공백 및 쉼표 제거
                        cleaned_value = cleaned_value.strip(' ,')
                        return cleaned_value if cleaned_value else value_str
                    
                    return value_str
                
                # 데이터 매핑 (영문 프로퍼티명으로 + 한국어 변환)
                ingredient_data = {}
                for excel_col, property_name in column_mapping.items():
                    value = row.get(excel_col)
                    if pd.notna(value):
                        if property_name in ['purchase_price', 'selling_price']:
                            try:
                                ingredient_data[property_name] = float(value)
                            except:
                                ingredient_data[property_name] = None
                        else:
                            # 한국어 변환 적용
                            converted_value = convert_korean_values(property_name, value)
                            if converted_value is not None:
                                ingredient_data[property_name] = converted_value
                
                # 규격 필드는 Excel에서 직접 받아서 사용 (추출 로직 불필요)
                
                # 기존 식자재인지 확인
                ingredient_code = ingredient_data.get('ingredient_code')
                if index < 3:
                    print(f"[DEBUG] 행 {index + 1} ingredient_code: '{ingredient_code}'")
                    print(f"[DEBUG] existing_codes에서 찾기: {ingredient_code in existing_codes if ingredient_code else False}")
                
                if ingredient_code and ingredient_code in existing_codes:
                    # 기존 데이터 업데이트 대상
                    existing_ingredient = existing_ingredients_map[ingredient_code]
                    if index < 3:
                        print(f"[DEBUG] 행 {index + 1}: 기존 식자재 업데이트")
                    for field, value in ingredient_data.items():
                        setattr(existing_ingredient, field, value)
                    update_ingredients.append(existing_ingredient)
                    updated_count += 1
                else:
                    # 새 식자재 생성 대상
                    if index < 3:
                        print(f"[DEBUG] 행 {index + 1}: 신규 식자재 생성")
                        print(f"[DEBUG] ingredient_data 내용: {ingredient_data}")
                    
                    ingredient_data['created_by'] = user['username']
                    ingredient_data['upload_batch_id'] = upload_history.id
                    ingredient_data['created_at'] = datetime.now()
                    ingredient_data['updated_at'] = datetime.now()
                    ingredient_data['is_active'] = True
                    
                    new_ingredients.append(ingredient_data)
                    processed_count += 1
                
                # 배치 크기에 도달하면 일괄 처리 (메모리 관리)
                if len(new_ingredients) >= batch_size:
                    try:
                        print(f"[DEBUG] 배치 저장 시작: {len(new_ingredients)}개 아이템")
                        print(f"[DEBUG] 첫 번째 아이템 내용: {new_ingredients[0] if new_ingredients else 'None'}")
                        
                        # 벌크 인서트로 성능 최적화
                        db.bulk_insert_mappings(Ingredient, new_ingredients)
                        db.commit()
                        print(f"[DEBUG] {len(new_ingredients)}개 신규 식자재 배치 저장 완료 (총 진행: {processed_count + updated_count}개)")
                        new_ingredients.clear()  # 메모리 해제
                        
                        # 메모리 사용량 최적화를 위한 가비지 컬렉션
                        import gc
                        gc.collect()
                        
                    except Exception as batch_error:
                        db.rollback()
                        print(f"[DEBUG] 배치 저장 오류 발생: {str(batch_error)}")
                        print(f"[DEBUG] 오류 발생한 데이터 예시: {new_ingredients[0] if new_ingredients else 'None'}")
                        error_details.append(f"배치 저장 오류: {str(batch_error)}")
                        error_count += len(new_ingredients)
                        new_ingredients.clear()
                
            except Exception as e:
                error_details.append(f"행 {index + 2}: {str(e)}")
                error_count += 1
        
        # 남은 신규 식자재들 처리
        print(f"[DEBUG] 최종 처리: new_ingredients={len(new_ingredients)}개, update_ingredients={len(update_ingredients)}개")
        if new_ingredients:
            try:
                print(f"[DEBUG] 마지막 배치 저장 시작: {len(new_ingredients)}개")
                print(f"[DEBUG] 마지막 배치 첫 번째 아이템: {new_ingredients[0] if new_ingredients else 'None'}")
                
                db.bulk_insert_mappings(Ingredient, new_ingredients)
                db.commit()
                print(f"[DEBUG] 마지막 {len(new_ingredients)}개 신규 식자재 배치 저장 완료")
            except Exception as batch_error:
                db.rollback()
                print(f"[DEBUG] 마지막 배치 저장 오류: {str(batch_error)}")
                error_details.append(f"마지막 배치 저장 오류: {str(batch_error)}")
                error_count += len(new_ingredients)
        
        # 업데이트된 식자재들 일괄 커밋
        if update_ingredients:
            try:
                db.commit()
                print(f"[DEBUG] {len(update_ingredients)}개 식자재 업데이트 완료")
            except Exception as update_error:
                db.rollback()
                error_details.append(f"업데이트 저장 오류: {str(update_error)}")
                error_count += len(update_ingredients)
                updated_count = 0
        
        # 업로드 히스토리 업데이트
        upload_history.processed_count = processed_count
        upload_history.updated_count = updated_count
        upload_history.error_count = error_count
        upload_history.error_details = error_details
        
        # 오류 행 데이터를 JSON으로 저장 (임시 파일로)
        if error_rows:
            import json
            error_file_path = f"temp_error_rows_{upload_history.id}.json"
            with open(error_file_path, 'w', encoding='utf-8') as f:
                json.dump(error_rows, f, ensure_ascii=False, default=str)
        upload_history.status = 'completed'
        
        db.commit()
        
        print(f"[DEBUG] 최종 결과:")
        print(f"  - 총 행 수: {len(df)}")
        print(f"  - 신규 처리: {processed_count}")
        print(f"  - 업데이트: {updated_count}")
        print(f"  - 오류: {error_count}")
        print(f"  - 오류 내역: {error_details[:5] if error_details else 'None'}")
        
        # 당일 통계 계산
        today = datetime.now().date()
        today_stats = db.query(
            func.count(IngredientUploadHistory.id).label('today_uploads'),
            func.sum(IngredientUploadHistory.processed_count).label('today_created'),
            func.sum(IngredientUploadHistory.updated_count).label('today_updated'),
            func.sum(IngredientUploadHistory.error_count).label('today_errors')
        ).filter(
            func.date(IngredientUploadHistory.upload_date) == today
        ).first()
        
        # None 값 처리
        today_uploads = today_stats.today_uploads or 0
        today_created = today_stats.today_created or 0 
        today_updated = today_stats.today_updated or 0
        today_errors = today_stats.today_errors or 0
        
        return {
            "success": True,
            "message": "엑셀 업로드가 완료되었습니다.",
            "result": {
                "total_rows": len(df),
                "processed_count": processed_count,
                "updated_count": updated_count,
                "error_count": error_count,
                "upload_id": upload_history.id,
                "today_stats": {
                    "uploads": today_uploads,
                    "created": today_created, 
                    "updated": today_updated,
                    "errors": today_errors
                },
                "error_details": error_details[:10] if error_details else [],
                "has_error_file": len(error_rows) > 0
            }
        }
        
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"업로드 처리 중 오류: {str(e)}"}

@router.get("/ingredients-new/download-errors/{upload_id}")
async def download_error_file(
    upload_id: int,
    db: Session = Depends(get_db)
):
    """업로드 실패 데이터를 엑셀 파일로 다운로드"""
    try:
        # 업로드 히스토리 확인
        upload_history = db.query(IngredientUploadHistory).filter(
            IngredientUploadHistory.id == upload_id
        ).first()
        
        if not upload_history:
            raise HTTPException(status_code=404, detail="업로드 기록을 찾을 수 없습니다")
            
        if upload_history.error_count == 0:
            raise HTTPException(status_code=400, detail="오류 데이터가 없습니다")
        
        # 임시 오류 파일 확인
        error_file_path = f"temp_error_rows_{upload_id}.json"
        if not os.path.exists(error_file_path):
            # 오류 상세 내용을 텍스트로 생성
            error_data = {
                "업로드 파일명": upload_history.filename,
                "업로드 일시": str(upload_history.upload_date),
                "총 처리 행수": upload_history.total_rows,
                "성공": upload_history.processed_count + upload_history.updated_count,
                "실패": upload_history.error_count,
                "오류 상세": "\n".join(upload_history.error_details) if upload_history.error_details else "오류 상세 정보 없음"
            }
            
            # 간단한 오류 리포트 생성
            df_error = pd.DataFrame([error_data])
        else:
            # JSON 파일에서 오류 데이터 읽기
            import json
            with open(error_file_path, 'r', encoding='utf-8') as f:
                error_rows = json.load(f)
            df_error = pd.DataFrame(error_rows)
        
        # 엑셀 파일 생성
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_error.to_excel(writer, sheet_name='오류데이터', index=False)
            
            # 요약 시트 추가
            summary_data = {
                "항목": ["업로드 파일명", "업로드 일시", "총 행수", "성공(신규)", "성공(업데이트)", "실패"],
                "값": [
                    upload_history.filename,
                    str(upload_history.upload_date),
                    upload_history.total_rows,
                    upload_history.processed_count,
                    upload_history.updated_count,
                    upload_history.error_count
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='요약', index=False)
        
        excel_buffer.seek(0)
        
        # 파일명 생성
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"오류데이터_{upload_history.filename}_{timestamp}.xlsx"
        
        # 임시 파일 정리
        if os.path.exists(error_file_path):
            os.remove(error_file_path)
        
        return StreamingResponse(
            io.BytesIO(excel_buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename.encode('utf-8').decode('latin-1')}"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다운로드 처리 중 오류: {str(e)}")

@router.get("/ingredients-upload-history")
async def get_upload_history(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """업로드 히스토리 조회"""
    try:
        total = db.query(IngredientUploadHistory).count()
        offset = (page - 1) * limit
        
        histories = db.query(IngredientUploadHistory).order_by(
            IngredientUploadHistory.upload_date.desc()
        ).offset(offset).limit(limit).all()
        
        history_list = []
        for history in histories:
            history_list.append({
                "id": history.id,
                "filename": history.filename,
                "uploaded_by": history.uploaded_by,
                "upload_date": str(history.upload_date),
                "total_rows": history.total_rows,
                "processed_count": history.processed_count,
                "updated_count": history.updated_count,
                "error_count": history.error_count,
                "status": history.status
            })
        
        total_pages = (total + limit - 1) // limit if total > 0 else 1
        
        return {
            "success": True,
            "histories": history_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages
            }
        }
        
    except Exception as e:
        return {"success": False, "message": f"업로드 히스토리 조회 중 오류: {str(e)}"}

@router.get("/ingredients-upload/{upload_id}/download-errors")
async def download_error_records(
    upload_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """오류 발생 레코드를 Excel 파일로 다운로드"""
    try:
        # 업로드 히스토리 확인
        upload_history = db.query(IngredientUploadHistory).filter(
            IngredientUploadHistory.id == upload_id
        ).first()
        
        if not upload_history:
            raise HTTPException(status_code=404, detail="업로드 기록을 찾을 수 없습니다.")
        
        # 오류 파일 경로
        error_file_path = f"temp_error_rows_{upload_id}.json"
        
        if not os.path.exists(error_file_path):
            raise HTTPException(status_code=404, detail="오류 데이터를 찾을 수 없습니다.")
        
        # JSON 파일에서 오류 행 데이터 읽기
        import json
        with open(error_file_path, 'r', encoding='utf-8') as f:
            error_rows = json.load(f)
        
        if not error_rows:
            raise HTTPException(status_code=404, detail="다운로드할 오류 데이터가 없습니다.")
        
        # DataFrame으로 변환
        df = pd.DataFrame(error_rows)
        
        # 행번호 컬럼을 제거 (원본 Excel 형태로 복구)
        if '행번호' in df.columns:
            df = df.drop('행번호', axis=1)
        
        # Excel 파일로 변환
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='오류_데이터')
        
        excel_buffer.seek(0)
        
        # 파일명 생성
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"오류_데이터_{upload_id}_{current_time}.xlsx"
        
        # 파일 응답 반환
        return StreamingResponse(
            io.BytesIO(excel_buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"오류 데이터 다운로드 중 오류: {str(e)}")

# ==============================================================================
# 개별 식자재 CRUD API
# ==============================================================================

@router.get("/ingredients-new/{ingredient_id}")
async def get_ingredient_by_id(
    ingredient_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """개별 식자재 조회"""
    try:
        ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        
        if not ingredient:
            raise HTTPException(status_code=404, detail="식자재를 찾을 수 없습니다.")
        
        return {
            "success": True,
            "ingredient": {
                "id": ingredient.id,
                "category": ingredient.category,
                "sub_category": ingredient.sub_category,
                "ingredient_code": ingredient.ingredient_code,
                "ingredient_name": ingredient.ingredient_name,
                "origin": ingredient.origin,
                "posting_status": ingredient.posting_status,
                "specification": ingredient.specification,
                "unit": ingredient.unit,
                "tax_type": ingredient.tax_type,
                "delivery_days": ingredient.delivery_days,
                "purchase_price": float(ingredient.purchase_price) if ingredient.purchase_price else 0,
                "selling_price": float(ingredient.selling_price) if ingredient.selling_price else 0,
                "supplier_name": ingredient.supplier_name,
                "notes": ingredient.notes,
                "is_active": ingredient.is_active,
                "created_at": str(ingredient.created_at),
                "updated_at": str(ingredient.updated_at)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"식자재 조회 중 오류: {str(e)}")

@router.post("/ingredients-new")
async def create_ingredient(
    ingredient_data: IngredientCreate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """개별 식자재 생성"""
    try:
        # 고유코드 중복 체크
        existing = db.query(Ingredient).filter(
            Ingredient.ingredient_code == ingredient_data.ingredient_code
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="이미 존재하는 고유코드입니다.")
        
        # 새 식자재 생성
        new_ingredient = Ingredient(
            category=ingredient_data.category,
            sub_category=ingredient_data.sub_category,
            ingredient_code=ingredient_data.ingredient_code,
            ingredient_name=ingredient_data.ingredient_name,
            origin=ingredient_data.origin,
            posting_status=ingredient_data.posting_status,
            specification=ingredient_data.specification,
            unit=ingredient_data.unit,
            tax_type=ingredient_data.tax_type,
            delivery_days=ingredient_data.delivery_days,
            purchase_price=Decimal(str(ingredient_data.purchase_price)),
            selling_price=Decimal(str(ingredient_data.selling_price)),
            supplier_name=ingredient_data.supplier_name,
            notes=ingredient_data.notes,
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(new_ingredient)
        db.commit()
        db.refresh(new_ingredient)
        
        return {
            "success": True,
            "message": "식자재가 성공적으로 등록되었습니다.",
            "ingredient_id": new_ingredient.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"식자재 등록 중 오류: {str(e)}")

@router.put("/ingredients-new/{ingredient_id}")
async def update_ingredient(
    ingredient_id: int,
    ingredient_data: IngredientUpdate,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """개별 식자재 수정"""
    try:
        ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        
        if not ingredient:
            raise HTTPException(status_code=404, detail="식자재를 찾을 수 없습니다.")
        
        # 고유코드 중복 체크 (다른 식자재와의 중복)
        if ingredient_data.ingredient_code and ingredient_data.ingredient_code != ingredient.ingredient_code:
            existing = db.query(Ingredient).filter(
                Ingredient.ingredient_code == ingredient_data.ingredient_code,
                Ingredient.id != ingredient_id
            ).first()
            
            if existing:
                raise HTTPException(status_code=400, detail="이미 존재하는 고유코드입니다.")
        
        # 단위 필수 검증
        if hasattr(ingredient_data, 'unit') and ingredient_data.unit is not None:
            if not ingredient_data.unit.strip():
                raise HTTPException(status_code=400, detail="단위는 필수 항목입니다.")
        
        # 필드 업데이트 (None이 아닌 값들만)
        update_data = ingredient_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field in ['purchase_price', 'selling_price'] and value is not None:
                setattr(ingredient, field, Decimal(str(value)))
            else:
                setattr(ingredient, field, value)
        
        ingredient.updated_at = datetime.now()
        
        db.commit()
        db.refresh(ingredient)
        
        return {
            "success": True,
            "message": "식자재가 성공적으로 수정되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"식자재 수정 중 오류: {str(e)}")

@router.delete("/ingredients-new/{ingredient_id}")
async def delete_ingredient(
    ingredient_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """개별 식자재 삭제"""
    try:
        ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
        
        if not ingredient:
            raise HTTPException(status_code=404, detail="식자재를 찾을 수 없습니다.")
        
        # 소프트 삭제 (is_active를 False로 설정)
        ingredient.is_active = False
        ingredient.updated_at = datetime.now()
        
        db.commit()
        
        return {
            "success": True,
            "message": "식자재가 성공적으로 삭제되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"식자재 삭제 중 오류: {str(e)}")

@router.get("/ingredients-new/check-code")
async def check_ingredient_code(
    code: str = Query(..., description="확인할 고유코드"),
    exclude_id: Optional[int] = Query(None, description="제외할 식자재 ID (수정 시)"),
    db: Session = Depends(get_db)
):
    """고유코드 중복 체크"""
    try:
        query = db.query(Ingredient).filter(
            Ingredient.ingredient_code == code,
            Ingredient.is_active == True
        )
        
        # 수정 시 자기 자신은 제외
        if exclude_id:
            query = query.filter(Ingredient.id != exclude_id)
        
        existing = query.first()
        
        return {
            "success": True,
            "exists": existing is not None,
            "message": "이미 사용 중인 고유코드입니다." if existing else "사용 가능한 고유코드입니다."
        }
        
    except Exception as e:
        return {"success": False, "exists": False, "message": f"코드 확인 중 오류: {str(e)}"}