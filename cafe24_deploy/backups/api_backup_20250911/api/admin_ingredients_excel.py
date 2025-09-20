"""
Excel 구조 그대로 식자재 관리 API 모듈
- Excel 컬럼명 그대로 한글 필드 사용
- 여유 컬럼 3개 포함
"""

from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, Query
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

router = APIRouter(prefix="/api/admin", tags=["ingredients-excel"])

# ==============================================================================
# 데이터 변환 유틸리티 함수
# ==============================================================================

def convert_korean_values(property_name, value):
    """영문 값들을 한국어로 변환 및 데이터 정리"""
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

# ==============================================================================
# Pydantic 모델들 (Excel 구조)
# ==============================================================================

class IngredientExcelResponse(BaseModel):
    id: int
    분류_대분류: str = None
    기본식자재_세분류: str = None
    고유코드: str = None
    식자재명: str
    원산지: str = None
    게시유무: str = None
    규격: str = None
    단위: str = None
    면세: str = None
    선발주일: str = None
    입고가: float = None
    판매가: float = None
    거래처명: str = None
    비고: str = None
    여유필드1: str = None
    여유필드2: str = None
    여유필드3: str = None
    is_active: bool = True
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True

# ==============================================================================
# 식자재 조회 API
# ==============================================================================

@router.get("/ingredients-excel", response_model=dict)
async def get_ingredients_excel(
    request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=1000),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None)
):
    """Excel 구조 식자재 목록 조회"""
    
    try:
        # 기본 쿼리
        query = db.query(Ingredient).filter(Ingredient.is_active == True)
        
        # 검색 조건
        if search:
            search_filter = or_(
                Ingredient.ingredient_name.ilike(f"%{search}%"),
                Ingredient.ingredient_code.ilike(f"%{search}%"),
                Ingredient.supplier_name.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        if category:
            query = query.filter(Ingredient.category == category)
        
        # 전체 카운트
        total_count = query.count()
        
        # 페이지네이션
        offset = (page - 1) * size
        ingredients = query.offset(offset).limit(size).all()
        
        # 응답 데이터 변환
        ingredient_list = []
        for ingredient in ingredients:
            ingredient_dict = {
                "id": ingredient.id,
                "분류_대분류": ingredient.category,
                "기본식자재_세분류": ingredient.sub_category,
                "고유코드": ingredient.ingredient_code,
                "식자재명": ingredient.ingredient_name,
                "게시여부": ingredient.posting_status,
                "단위": ingredient.unit,
                "과세": ingredient.tax_type,
                "배송일수": ingredient.delivery_days,
                "입고가": float(ingredient.purchase_price) if ingredient.purchase_price else None,
                "판매가": float(ingredient.selling_price) if ingredient.selling_price else None,
                "판매처명": ingredient.supplier_name,
                "비고": ingredient.notes,
                "여유필드1": ingredient.extra_field1,
                "여유필드2": ingredient.extra_field2,
                "여유필드3": ingredient.extra_field3,
                "is_active": ingredient.is_active,
                "created_at": ingredient.created_at.isoformat() if ingredient.created_at else None,
                "updated_at": ingredient.updated_at.isoformat() if ingredient.updated_at else None
            }
            ingredient_list.append(ingredient_dict)
        
        return {
            "success": True,
            "data": {
                "ingredients": ingredient_list,
                "pagination": {
                    "total_count": total_count,
                    "current_page": page,
                    "page_size": size,
                    "total_pages": (total_count + size - 1) // size
                }
            }
        }
        
    except Exception as e:
        print(f"식자재 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"식자재 조회 중 오류가 발생했습니다: {str(e)}")

# ==============================================================================
# Excel 업로드 API
# ==============================================================================

@router.post("/ingredients-excel-upload")
async def upload_ingredients_excel(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Excel 구조 그대로 식자재 업로드"""
    
    try:
        # 파일 확장자 체크
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Excel 파일만 업로드 가능합니다.")
        
        # 파일 내용 읽기
        content = await file.read()
        
        # pandas로 Excel 읽기
        try:
            df = pd.read_excel(io.BytesIO(content))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Excel 파일 읽기 오류: {str(e)}")
        
        if df.empty:
            raise HTTPException(status_code=400, detail="Excel 파일이 비어있습니다.")
        
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
        
        # 대용량 데이터 배치 처리
        batch_size = 2000
        new_ingredients = []
        
        # 데이터 처리
        for index, row in df.iterrows():
            try:
                # Excel 데이터에서 값 추출
                ingredient_data = {}
                for excel_col, db_col in column_mapping.items():
                    if excel_col in df.columns:
                        value = row[excel_col]
                        # NaN 처리
                        if pd.isna(value):
                            ingredient_data[db_col] = None
                        else:
                            ingredient_data[db_col] = str(value).strip() if isinstance(value, str) else value
                    else:
                        ingredient_data[db_col] = None
                
                # 필수 필드 체크 (사용자 요구사항에 따른 필수 필드들)
                required_fields = [
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
                
                validation_failed = False
                for field_key, field_name in required_fields:
                    field_value = ingredient_data.get(field_key)
                    if pd.isna(field_value) or str(field_value).strip() == '':
                        error_count += 1
                        error_details.append(f"행 {index+2}: {field_name}은(는) 필수입니다.")
                        validation_failed = True
                    elif field_key in ['입고가', '판매가', '선발주일']:
                        # 숫자 필드 추가 검증
                        try:
                            num_value = float(str(field_value).replace(',', ''))
                            if num_value <= 0:
                                error_count += 1
                                error_details.append(f"행 {index+2}: {field_name}은(는) 0보다 큰 값이어야 합니다.")
                                validation_failed = True
                        except (ValueError, TypeError):
                            error_count += 1
                            error_details.append(f"행 {index+2}: {field_name}은(는) 유효한 숫자여야 합니다.")
                            validation_failed = True
                
                if validation_failed:
                    # 오류 행 데이터 저장 (Excel 다운로드용)
                    error_row_dict = row.to_dict()
                    error_row_dict['행번호'] = index + 2
                    error_rows.append(error_row_dict)
                    continue
                
                # 고유코드 중복 체크 (업데이트 vs 신규)
                ingredient_code_value = ingredient_data.get('고유코드')
                existing_ingredient = None
                
                if ingredient_code_value:
                    existing_ingredient = db.query(Ingredient).filter(
                        Ingredient.ingredient_code == ingredient_code_value
                    ).first()
                
                if existing_ingredient:
                    # 기존 데이터 업데이트 - 컬럼 매핑 적용
                    field_mapping = {
                        '분류(대분류)': 'category',
                        '기본식자재(세분류)': 'sub_category',
                        '고유코드': 'ingredient_code',
                        '식자재명': 'ingredient_name',
                        '게시여부': 'posting_status',
                        '단위': 'unit',
                        '과세': 'tax_type',
                        '배송일수': 'delivery_days',
                        '입고가': 'purchase_price',
                        '판매가': 'selling_price',
                        '판매처명': 'supplier_name',
                        '비고': 'notes'
                    }
                    
                    for excel_col, value in ingredient_data.items():
                        if excel_col in field_mapping:
                            model_field = field_mapping[excel_col]
                            if excel_col == '입고가' or excel_col == '판매가':
                                if value is not None:
                                    try:
                                        setattr(existing_ingredient, model_field, Decimal(str(value)))
                                    except:
                                        setattr(existing_ingredient, model_field, None)
                                else:
                                    setattr(existing_ingredient, model_field, None)
                            else:
                                # 데이터 변환 적용
                                converted_value = convert_korean_values(model_field, value)
                                setattr(existing_ingredient, model_field, converted_value)
                    
                    existing_ingredient.updated_at = func.now()
                    updated_count += 1
                else:
                    # 신규 데이터 생성
                    new_ingredient_data = {
                        'category': ingredient_data.get('분류(대분류)'),
                        'sub_category': ingredient_data.get('기본식자재(세분류)'),
                        'ingredient_code': ingredient_data.get('고유코드'),
                        'ingredient_name': ingredient_data.get('식자재명'),
                        'posting_status': convert_korean_values('posting_status', ingredient_data.get('게시여부')),
                        'unit': ingredient_data.get('단위'),
                        'tax_type': convert_korean_values('tax_type', ingredient_data.get('과세')),
                        'delivery_days': convert_korean_values('delivery_days', ingredient_data.get('배송일수')),
                        'supplier_name': ingredient_data.get('판매처명'),
                        'notes': ingredient_data.get('비고'),
                        'specification': convert_korean_values('specification', ingredient_data.get('규격')),
                        'origin': ingredient_data.get('원산지'),
                        'created_by': user['username'],
                        'upload_batch_id': upload_history.id
                    }
                    
                    # 가격 데이터 처리
                    if ingredient_data.get('입고가') is not None:
                        try:
                            new_ingredient_data['purchase_price'] = Decimal(str(ingredient_data.get('입고가')))
                        except:
                            new_ingredient_data['purchase_price'] = None
                    
                    if ingredient_data.get('판매가') is not None:
                        try:
                            new_ingredient_data['selling_price'] = Decimal(str(ingredient_data.get('판매가')))
                        except:
                            new_ingredient_data['selling_price'] = None
                    
                    new_ingredient = Ingredient(**new_ingredient_data)
                    new_ingredients.append(new_ingredient)
                
                processed_count += 1
                
                # 배치 처리
                if len(new_ingredients) >= batch_size:
                    db.add_all(new_ingredients)
                    db.commit()
                    new_ingredients = []
                    
            except Exception as e:
                error_count += 1
                error_details.append(f"행 {index+2}: {str(e)}")
                continue
        
        # 남은 데이터 처리
        if new_ingredients:
            db.add_all(new_ingredients)
            db.commit()
        
        # 오류 행 데이터 임시 파일로 저장 (다운로드용)
        if error_rows:
            import json
            error_file_path = f"temp_error_rows_{upload_history.id}.json"
            with open(error_file_path, 'w', encoding='utf-8') as f:
                json.dump(error_rows, f, ensure_ascii=False, default=str)
        
        # 업로드 히스토리 업데이트
        upload_history.processed_count = processed_count
        upload_history.updated_count = updated_count
        upload_history.error_count = error_count
        upload_history.error_details = error_details[:100]  # 최대 100개 오류만 저장
        upload_history.status = 'completed'
        db.commit()
        
        return {
            "success": True,
            "message": "식자재 업로드가 완료되었습니다.",
            "data": {
                "total_rows": len(df),
                "processed_count": processed_count,
                "new_count": processed_count - updated_count,
                "updated_count": updated_count,
                "error_count": error_count,
                "error_details": error_details[:10] if error_details else [],
                "has_error_file": len(error_rows) > 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"업로드 오류: {e}")
        raise HTTPException(status_code=500, detail=f"업로드 중 오류가 발생했습니다: {str(e)}")

# ==============================================================================
# 업로드 히스토리 조회
# ==============================================================================

@router.get("/ingredients-excel-upload-history")
async def get_excel_upload_history(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100)
):
    """Excel 업로드 히스토리 조회"""
    
    try:
        # 페이지네이션
        offset = (page - 1) * size
        
        histories = db.query(IngredientUploadHistory)\
            .order_by(IngredientUploadHistory.upload_date.desc())\
            .offset(offset)\
            .limit(size)\
            .all()
        
        total_count = db.query(IngredientUploadHistory).count()
        
        history_list = []
        for history in histories:
            history_dict = {
                "id": history.id,
                "filename": history.filename,
                "uploaded_by": history.uploaded_by,
                "upload_date": history.upload_date.isoformat(),
                "total_rows": history.total_rows,
                "processed_count": history.processed_count,
                "updated_count": history.updated_count,
                "error_count": history.error_count,
                "status": history.status
            }
            history_list.append(history_dict)
        
        return {
            "success": True,
            "data": {
                "history": history_list,
                "pagination": {
                    "total_count": total_count,
                    "current_page": page,
                    "page_size": size,
                    "total_pages": (total_count + size - 1) // size
                }
            }
        }
        
    except Exception as e:
        print(f"히스토리 조회 오류: {e}")
        raise HTTPException(status_code=500, detail=f"히스토리 조회 중 오류가 발생했습니다: {str(e)}")

# ==============================================================================
# 오류 파일 다운로드 API
# ==============================================================================

@router.get("/ingredients-excel/download-errors/{upload_id}")
async def download_excel_error_file(
    upload_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user)
):
    """Excel 업로드 실패 데이터를 엑셀 파일로 다운로드"""
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
        filename = f"식자재_업로드_오류_{timestamp}.xlsx"
        
        return StreamingResponse(
            io.BytesIO(excel_buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"오류 파일 다운로드 오류: {e}")
        raise HTTPException(status_code=500, detail=f"오류 파일 다운로드 중 문제가 발생했습니다: {str(e)}")