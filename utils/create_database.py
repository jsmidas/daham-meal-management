#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터베이스 및 테이블 생성 스크립트
"""
import os
from sqlalchemy import create_engine
from models import Base, Customer, User, DietPlan, Menu, MenuItem, Recipe, Ingredient, Supplier
from models import RecipeIngredient, SupplierIngredient, Order, CustomerMenu, Inventory, Instruction, DietPlanInstruction
from datetime import datetime

DATABASE_PATH = "meal_management.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

def create_database_and_tables():
    """데이터베이스 및 모든 테이블 생성"""
    try:
        # 엔진 생성
        engine = create_engine(DATABASE_URL, echo=True)
        print(f"[INFO] 데이터베이스 엔진 생성: {DATABASE_URL}")
        
        # 모든 테이블 생성
        Base.metadata.create_all(bind=engine)
        print("[SUCCESS] 모든 테이블이 생성되었습니다!")
        
        # 생성된 테이블 목록 확인
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"[INFO] 생성된 테이블 목록: {tables}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 데이터베이스 생성 중 오류 발생: {e}")
        return False

def insert_sample_data():
    """샘플 데이터 삽입"""
    try:
        from sqlalchemy.orm import sessionmaker
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("[INFO] 샘플 데이터 삽입 중...")
        
        # 계층 구조 샘플 사업장 데이터
        sample_customers = [
            # 헤드 오피스 (level 0)
            Customer(
                id=1, name="웰스토리 본사", site_type="head", parent_id=None, level=0, sort_order=1,
                is_active=True, contact_person="김본부", contact_phone="02-123-4567", 
                address="서울시 강남구", description="웰스토리 본사"
            ),
            
            # 세부 사업장 (level 1) - 헤드 오피스 하위
            Customer(
                id=2, name="삼성전자 본사", site_type="detail", parent_id=1, level=1, sort_order=2,
                is_active=True, contact_person="박영양", contact_phone="031-200-1234",
                address="수원시 영통구", description="삼성전자 본사 구내식당"
            ),
            Customer(
                id=3, name="LG전자 본사", site_type="detail", parent_id=1, level=1, sort_order=3,
                is_active=True, contact_person="이영양", contact_phone="02-3777-1234",
                address="서울시 영등포구", description="LG전자 본사 구내식당"
            ),
            Customer(
                id=4, name="현대자동차 본사", site_type="detail", parent_id=1, level=1, sort_order=4,
                is_active=True, contact_person="최영양", contact_phone="02-3464-1234",
                address="서울시 서초구", description="현대자동차 본사 구내식당"
            ),
            
            # 기간별 사업장 (level 2) - 삼성전자 하위
            Customer(
                id=5, name="삼성전자 1공장", site_type="period", parent_id=2, level=2, sort_order=5,
                is_active=True, contact_person="김조리", contact_phone="031-200-5678",
                address="수원시 영통구", description="삼성전자 1공장 구내식당"
            ),
            Customer(
                id=6, name="삼성전자 2공장", site_type="period", parent_id=2, level=2, sort_order=6,
                is_active=True, contact_person="이조리", contact_phone="031-200-5679",
                address="수원시 영통구", description="삼성전자 2공장 구내식당"
            ),
            
            # 기간별 사업장 (level 2) - LG전자 하위  
            Customer(
                id=7, name="LG전자 평택공장", site_type="period", parent_id=3, level=2, sort_order=7,
                is_active=True, contact_person="박조리", contact_phone="031-8080-1234",
                address="평택시 청북면", description="LG전자 평택공장 구내식당"
            ),
        ]
        
        for customer in sample_customers:
            session.add(customer)
            print(f"[OK] 사업장 추가: {customer.name} ({customer.site_type}, level {customer.level})")
        
        session.commit()
        session.close()
        
        print("[SUCCESS] 샘플 데이터 삽입 완료")
        return True
        
    except Exception as e:
        print(f"[ERROR] 샘플 데이터 삽입 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("데이터베이스 및 테이블 생성 시작")
    print("=" * 60)
    
    # 기존 데이터베이스 파일이 있으면 백업
    if os.path.exists(DATABASE_PATH):
        backup_path = f"{DATABASE_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(DATABASE_PATH, backup_path)
        print(f"[INFO] 기존 데이터베이스를 백업했습니다: {backup_path}")
    
    # 데이터베이스 및 테이블 생성
    if create_database_and_tables():
        print("[SUCCESS] 데이터베이스 생성 완료")
        
        # 샘플 데이터 삽입
        if insert_sample_data():
            print("[SUCCESS] 전체 설정 완료!")
        else:
            print("[WARNING] 샘플 데이터 삽입 실패")
    else:
        print("[ERROR] 데이터베이스 생성 실패!")
    
    print("=" * 60)