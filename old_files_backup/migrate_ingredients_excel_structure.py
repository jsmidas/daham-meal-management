#!/usr/bin/env python3
"""
Excel 파일 구조에 맞게 ingredients 테이블 재구성
- Excel 컬럼 그대로 DB 필드명으로 사용 (한글 컬럼명)
- 여유 컬럼 3개 추가
"""

import sqlite3
from datetime import datetime

def migrate_ingredients_to_excel_structure():
    """Excel 파일 구조에 맞게 ingredients 테이블 재구성"""
    
    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()
    
    print("Excel 구조에 맞게 ingredients 테이블 재구성 시작...")
    
    try:
        # 1. 기존 데이터 백업
        print("1. 기존 데이터 백업...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ingredients_backup_old AS
            SELECT * FROM ingredients;
        """)
        
        # 2. 기존 테이블 삭제
        print("2. 기존 ingredients 테이블 삭제...")
        cursor.execute("DROP TABLE IF EXISTS ingredients;")
        
        # 3. Excel 구조 그대로 새 테이블 생성
        print("3. Excel 구조에 맞는 새 ingredients 테이블 생성...")
        cursor.execute("""
            CREATE TABLE ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- Excel 파일 컬럼 구조 그대로 (한글 컬럼명)
                "분류(대분류)" VARCHAR(100),
                "기본식자재(소분류)" VARCHAR(100),
                "식자재코드" VARCHAR(50) UNIQUE,
                "식자재명" VARCHAR(255) NOT NULL,
                "브랜드명" VARCHAR(255),
                "게시여부" VARCHAR(20),
                "입고명" VARCHAR(255),
                "단위" VARCHAR(20),
                "과세" VARCHAR(20),
                "배송일수" VARCHAR(20),
                "입고가" DECIMAL(10, 2),
                "판매가" DECIMAL(10, 2),
                "판매처명" VARCHAR(255),
                "비고" TEXT,
                
                -- 여유 컬럼 3개
                "여유필드1" VARCHAR(255),
                "여유필드2" VARCHAR(255),
                "여유필드3" TEXT,
                
                -- 시스템 정보
                is_active BOOLEAN DEFAULT 1,
                created_by VARCHAR(50),
                upload_batch_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 4. 인덱스 생성
        print("4. 인덱스 생성...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingredients_code ON ingredients("식자재코드");')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingredients_name ON ingredients("식자재명");')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingredients_supplier ON ingredients("판매처명");')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingredients_category ON ingredients("분류(대분류)");')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ingredients_subcategory ON ingredients("기본식자재(소분류)");')
        
        # 5. 기존 데이터 마이그레이션 (가능한 것들만)
        print("5. 기존 데이터 마이그레이션...")
        cursor.execute("""
            INSERT INTO ingredients (
                "분류(대분류)", "기본식자재(소분류)", "식자재코드", "식자재명",
                "브랜드명", "입고명", "단위", "과세", "배송일수",
                "입고가", "판매가", "판매처명", "비고",
                is_active, created_at, updated_at
            )
            SELECT 
                category as "분류(대분류)",
                sub_category as "기본식자재(소분류)",
                ingredient_code as "식자재코드",
                ingredient_name as "식자재명",
                brand_name as "브랜드명",
                product_name as "입고명",
                unit as "단위",
                tax_type as "과세",
                delivery_days as "배송일수",
                purchase_price as "입고가",
                selling_price as "판매가",
                supplier_name as "판매처명",
                notes as "비고",
                is_active,
                created_at,
                updated_at
            FROM ingredients_backup_old
            WHERE ingredient_name IS NOT NULL;
        """)
        
        migrated_count = cursor.rowcount
        print(f"   마이그레이션된 레코드: {migrated_count}개")
        
        # 6. 변경사항 커밋
        conn.commit()
        
        # 7. 결과 확인
        cursor.execute("SELECT count(*) FROM ingredients;")
        final_count = cursor.fetchone()[0]
        
        print(f"\n마이그레이션 완료!")
        print(f"최종 ingredients 레코드 수: {final_count}개")
        
        # 8. 새로운 스키마 확인
        print("\n새로운 테이블 스키마:")
        cursor.execute("PRAGMA table_info(ingredients);")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]:<25} {col[2]}")
            
    except Exception as e:
        print(f"마이그레이션 중 오류 발생: {e}")
        conn.rollback()
        raise
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_ingredients_to_excel_structure()