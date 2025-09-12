"""
대용량 업로드 최적화 API
- 청크 단위 업로드
- 배치 처리
- 트랜잭션 최적화
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional
import pandas as pd
import io
import os
import json
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.database import get_db
from models import Ingredient

router = APIRouter(prefix="/api/admin", tags=["bulk-upload"])

# 청크 임시 저장소
UPLOAD_CHUNKS = {}
executor = ThreadPoolExecutor(max_workers=4)

@router.post("/upload-chunk")
async def upload_chunk(
    chunk: UploadFile = File(...),
    chunkIndex: int = Form(...),
    totalChunks: int = Form(...),
    fileName: str = Form(...),
    db: Session = Depends(get_db)
):
    """청크 단위 업로드 처리"""
    
    # 고유 업로드 ID 생성
    upload_id = f"{fileName}_{datetime.now().timestamp()}"
    
    if upload_id not in UPLOAD_CHUNKS:
        UPLOAD_CHUNKS[upload_id] = {
            'chunks': {},
            'totalChunks': totalChunks,
            'fileName': fileName
        }
    
    # 청크 저장
    chunk_data = await chunk.read()
    UPLOAD_CHUNKS[upload_id]['chunks'][chunkIndex] = chunk_data
    
    # 모든 청크가 도착했는지 확인
    if len(UPLOAD_CHUNKS[upload_id]['chunks']) == totalChunks:
        # 파일 재조립
        complete_data = b''
        for i in range(totalChunks):
            complete_data += UPLOAD_CHUNKS[upload_id]['chunks'][i]
        
        # 비동기 처리
        result = await process_bulk_data(complete_data, fileName, db)
        
        # 임시 데이터 정리
        del UPLOAD_CHUNKS[upload_id]
        
        return result
    
    return {
        "status": "chunk_received",
        "chunkIndex": chunkIndex,
        "totalChunks": totalChunks
    }

async def process_bulk_data(file_data: bytes, file_name: str, db: Session):
    """대용량 데이터 배치 처리"""
    
    try:
        # 파일 확장자 확인
        if file_name.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_data), encoding='utf-8-sig')
        else:
            df = pd.read_excel(io.BytesIO(file_data))
        
        total_rows = len(df)
        batch_size = 1000  # 배치 크기
        processed = 0
        errors = []
        
        # 배치 단위로 처리
        for batch_start in range(0, total_rows, batch_size):
            batch_end = min(batch_start + batch_size, total_rows)
            batch_df = df.iloc[batch_start:batch_end]
            
            # 배치 데이터 준비
            batch_data = []
            for _, row in batch_df.iterrows():
                ingredient_data = {
                    '분류(대분류)': str(row.get('분류(대분류)', '')),
                    '기본식자재(세분류)': str(row.get('기본식자재(세분류)', '')),
                    '고유코드': str(row.get('고유코드', '')),
                    '식자재명': str(row.get('식자재명', '')),
                    '원산지': str(row.get('원산지', '')),
                    '게시유무': str(row.get('게시유무', '')),
                    '규격': str(row.get('규격', '')),
                    '단위': str(row.get('단위', '')),
                    '면세': str(row.get('면세', '')),
                    '선발주일': str(row.get('선발주일', '')),
                    '입고가': float(row.get('입고가', 0)) if pd.notna(row.get('입고가')) else 0,
                    '판매가': float(row.get('판매가', 0)) if pd.notna(row.get('판매가')) else 0,
                    '거래처명': str(row.get('거래처명', '')),
                    '비고': str(row.get('비고', '')),
                    '등록일': datetime.now()
                }
                batch_data.append(ingredient_data)
            
            # 배치 인서트 (BULK INSERT 최적화)
            try:
                # SQLAlchemy Core를 사용한 bulk_insert_mappings (더 빠름)
                db.bulk_insert_mappings(Ingredient, batch_data)
                
                # 주기적으로 커밋 (메모리 관리)
                if batch_end % 5000 == 0:
                    db.commit()
                    
                processed += len(batch_data)
                
            except Exception as e:
                errors.append(f"Batch {batch_start}-{batch_end}: {str(e)}")
                db.rollback()
        
        # 최종 커밋
        db.commit()
        
        return {
            "success": True,
            "processed": processed,
            "total": total_rows,
            "errors": errors if errors else None
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-upload-optimized")
async def bulk_upload_optimized(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """최적화된 대량 업로드 (단일 파일)"""
    
    # 파일 읽기
    contents = await file.read()
    
    # 백그라운드에서 처리
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        process_large_file,
        contents,
        file.filename,
        db
    )
    
    return result

def process_large_file(contents: bytes, filename: str, db: Session):
    """대용량 파일 처리 (스레드 풀에서 실행)"""
    
    try:
        # 파일 파싱
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents), encoding='utf-8-sig')
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # 데이터 전처리 (벡터화 연산으로 최적화)
        df = df.fillna('')
        df['등록일'] = datetime.now()
        
        # 숫자 컬럼 변환
        numeric_columns = ['입고가', '판매가']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # 딕셔너리 리스트로 변환
        records = df.to_dict('records')
        
        # 트랜잭션 최적화: 모든 데이터를 한 번에 처리
        batch_size = 5000
        total_processed = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            
            # Raw SQL 사용 (최고 성능)
            insert_query = text("""
                INSERT INTO ingredients (
                    "분류(대분류)", "기본식자재(세분류)", "고유코드", "식자재명",
                    "원산지", "게시유무", "규격", "단위", "면세", "선발주일",
                    "입고가", "판매가", "거래처명", "비고", "등록일"
                ) VALUES (
                    :category, :subcategory, :code, :name,
                    :origin, :published, :spec, :unit, :tax, :preorder,
                    :purchase_price, :selling_price, :supplier, :memo, :created_at
                )
            """)
            
            # 배치 실행
            for record in batch:
                db.execute(insert_query, {
                    'category': record.get('분류(대분류)', ''),
                    'subcategory': record.get('기본식자재(세분류)', ''),
                    'code': record.get('고유코드', ''),
                    'name': record.get('식자재명', ''),
                    'origin': record.get('원산지', ''),
                    'published': record.get('게시유무', ''),
                    'spec': record.get('규격', ''),
                    'unit': record.get('단위', ''),
                    'tax': record.get('면세', ''),
                    'preorder': record.get('선발주일', ''),
                    'purchase_price': record.get('입고가', 0),
                    'selling_price': record.get('판매가', 0),
                    'supplier': record.get('거래처명', ''),
                    'memo': record.get('비고', ''),
                    'created_at': datetime.now()
                })
            
            db.commit()
            total_processed += len(batch)
        
        return {
            "success": True,
            "processed": total_processed,
            "message": f"{total_processed:,}개 레코드 처리 완료"
        }
        
    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/ingredients-paginated")
async def get_ingredients_paginated(
    page: int = 1,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """페이지네이션 최적화 API"""
    
    try:
        # 전체 개수 (캐시 가능)
        total_query = text("SELECT COUNT(*) FROM ingredients")
        total = db.execute(total_query).scalar()
        
        # 오프셋 계산
        offset = (page - 1) * limit
        
        # 인덱스를 활용한 빠른 페이지네이션
        query = text("""
            SELECT * FROM ingredients
            ORDER BY id
            LIMIT :limit OFFSET :offset
        """)
        
        result = db.execute(query, {"limit": limit, "offset": offset})
        
        # 결과를 딕셔너리로 변환
        columns = result.keys()
        ingredients = [dict(zip(columns, row)) for row in result]
        
        return {
            "success": True,
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": (total + limit - 1) // limit,
            "ingredients": ingredients
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))