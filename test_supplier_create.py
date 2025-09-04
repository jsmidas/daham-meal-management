#!/usr/bin/env python3
"""
협력업체 생성 API 테스트용 스크립트
근본 문제를 파악하고 해결하기 위한 간단한 버전
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from models import Supplier
import json

app = FastAPI()

@app.post("/test/supplier/create")
async def test_create_supplier(request: Request):
    """테스트용 간단한 협력업체 생성 API"""
    db = next(get_db())
    
    try:
        # 1단계: Request body 읽기 (여러 방법 시도)
        print("=== Step 1: Reading request body ===")
        
        try:
            # 방법 1: 일반적인 방법
            supplier_data = await request.json()
            print(f"Method 1 - Success: {type(supplier_data)}")
        except Exception as e:
            print(f"Method 1 - Failed: {e}")
            
            try:
                # 방법 2: 바이트로 읽기
                body_bytes = await request.body()
                print(f"Raw bytes: {body_bytes[:100]}...")
                
                body_str = body_bytes.decode('utf-8', errors='replace')
                supplier_data = json.loads(body_str)
                print(f"Method 2 - Success: {type(supplier_data)}")
            except Exception as e2:
                print(f"Method 2 - Failed: {e2}")
                return {"error": f"Cannot parse request: {e2}"}
        
        # 2단계: 데이터 확인
        print("=== Step 2: Data validation ===")
        print(f"Received data keys: {list(supplier_data.keys())}")
        print(f"Name: {supplier_data.get('name', 'NOT_PROVIDED')}")
        print(f"Parent code: {supplier_data.get('parent_code', 'NOT_PROVIDED')}")
        
        # 3단계: 안전한 값 변환
        print("=== Step 3: Safe value conversion ===")
        
        def safe_clean(value):
            """안전한 값 정리"""
            if value is None or value == '':
                return None
            if isinstance(value, str):
                cleaned = value.strip()
                return None if cleaned == '' else cleaned
            return value
        
        clean_name = safe_clean(supplier_data.get('name'))
        clean_parent_code = safe_clean(supplier_data.get('parent_code'))
        
        print(f"Clean name: {clean_name}")
        print(f"Clean parent_code: {clean_parent_code}")
        
        # 4단계: UNIQUE 체크
        print("=== Step 4: UNIQUE constraint check ===")
        
        if clean_parent_code:
            existing = db.query(Supplier).filter(Supplier.parent_code == clean_parent_code).first()
            if existing:
                print(f"DUPLICATE parent_code found: {existing.id}")
                return {"error": f"모코드 '{clean_parent_code}'가 이미 존재합니다"}
        
        # 5단계: 객체 생성
        print("=== Step 5: Creating supplier object ===")
        
        new_supplier = Supplier(
            name=clean_name or "테스트업체",
            parent_code=clean_parent_code,
            business_number=safe_clean(supplier_data.get('business_number')),
            business_type=safe_clean(supplier_data.get('business_type')),
            representative=safe_clean(supplier_data.get('representative')),
            headquarters_address=safe_clean(supplier_data.get('address')),
            headquarters_phone=safe_clean(supplier_data.get('phone')),
            is_active=True
        )
        
        print("Supplier object created successfully")
        
        # 6단계: 데이터베이스 저장
        print("=== Step 6: Database save ===")
        
        db.add(new_supplier)
        db.commit()
        db.refresh(new_supplier)
        
        print(f"Saved to database with ID: {new_supplier.id}")
        
        return {
            "success": True,
            "message": "협력업체 생성 성공",
            "id": new_supplier.id,
            "name": new_supplier.name,
            "parent_code": new_supplier.parent_code
        }
        
    except Exception as e:
        print(f"=== ERROR: {e} ===")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)