#!/usr/bin/env python3
"""
식자재 테이블 마이그레이션 스크립트
- 기존 ingredients 테이블을 새로운 스키마로 업데이트
- 기존 데이터 보존 및 새 필드 추가
"""

import sqlite3
from datetime import datetime

def migrate_ingredients_table():
    """식자재 테이블을 새로운 스키마로 마이그레이션"""
    
    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()
    
    print("Starting ingredients table migration...")
    
    try:
        # 1. 백업 테이블 생성
        print("1. Creating backup table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingredients_backup AS
            SELECT * FROM ingredients;
        """)
        
        # 2. 기존 테이블 삭제
        print("2. Dropping existing ingredients table...")
        cursor.execute("DROP TABLE IF EXISTS ingredients;")
        
        # 3. 새로운 스키마로 테이블 생성
        print("3. Creating new ingredients table with updated schema...")
        cursor.execute("""
            CREATE TABLE ingredients (
                id INTEGER PRIMARY KEY,
                
                -- 기본 식자재 정보 (엑셀 파일 기준)
                category VARCHAR(100),  -- 분류(대분류)
                sub_category VARCHAR(100),  -- 기본분류(소분류)
                ingredient_code VARCHAR(50) UNIQUE,  -- 식자재코드
                ingredient_name VARCHAR(255) NOT NULL,  -- 식자재명
                brand_name VARCHAR(255),  -- 브랜드명
                manufacture_info VARCHAR(255),  -- 제조업체
                
                -- 제품 상세 정보
                product_name VARCHAR(255),  -- 입고명
                unit VARCHAR(20),  -- 단위 (PAC, EA, KG 등)
                tax_type VARCHAR(20),  -- 과세 (Full tax, 면세 등)
                delivery_days VARCHAR(20),  -- 배송일수 (D-1, 2 등)
                
                -- 가격 정보
                purchase_price DECIMAL(10, 2),  -- 입고가
                selling_price DECIMAL(10, 2),  -- 판매가
                
                -- 공급업체 정보
                supplier_name VARCHAR(255),  -- 판매처명
                supplier_id INTEGER REFERENCES suppliers(id),  -- 공급업체 ID (선택사항)
                
                -- 기타 정보
                notes TEXT,  -- 비고
                
                -- 업체별 추가 정보 (유연한 구조)
                specification VARCHAR(500),  -- 규격 정보 (업체별로 다른 형태)
                extra_field1 VARCHAR(255),  -- 여유 필드 1 (업체 특화 정보)
                extra_field2 VARCHAR(255),  -- 여유 필드 2 (추가 분류 등)
                extra_field3 TEXT,  -- 여유 필드 3 (기타 메모)
                
                -- 시스템 정보
                is_active BOOLEAN DEFAULT 1,  -- 활성 상태
                created_by VARCHAR(50),  -- 등록자
                upload_batch_id INTEGER REFERENCES ingredient_upload_history(id),  -- 업로드 배치 ID
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 4. 인덱스 생성
        print("4. Creating indexes...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ingredients_code ON ingredients(ingredient_code);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ingredients_name ON ingredients(ingredient_name);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ingredients_supplier ON ingredients(supplier_id);")
        
        # 5. 기존 데이터 마이그레이션
        print("5. Migrating existing data...")
        cursor.execute("""
            INSERT INTO ingredients (
                id, category, sub_category, ingredient_code, ingredient_name,
                unit, tax_type, purchase_price, selling_price,
                specification, notes, is_active, created_at, updated_at, supplier_id
            )
            SELECT 
                id,
                category,
                subcategory as sub_category,  -- 필드명 변경
                code as ingredient_code,      -- 필드명 변경  
                name as ingredient_name,      -- 필드명 변경
                base_unit as unit,           -- 필드명 변경
                tax_type,
                purchase_price,
                selling_price,
                specification,
                notes,
                1 as is_active,             -- 기본값
                created_at,
                updated_at,
                supplier_id
            FROM ingredients_backup
            WHERE name IS NOT NULL;  -- NULL 이름 제외
        """)
        
        migrated_count = cursor.rowcount
        print(f"   Migrated {migrated_count} ingredients")
        
        # 6. 변경사항 커밋
        conn.commit()
        
        # 7. 결과 확인
        cursor.execute("SELECT count(*) FROM ingredients;")
        final_count = cursor.fetchone()[0]
        
        print(f"Migration completed successfully!")
        print(f"Final ingredients count: {final_count}")
        
        # 8. 새로운 스키마 확인
        print("\\nNew table schema:")
        cursor.execute("PRAGMA table_info(ingredients);")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]:<20} {col[2]}")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_ingredients_table()