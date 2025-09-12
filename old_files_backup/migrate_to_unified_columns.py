"""
통일된 컬럼명으로 식자재 테이블 마이그레이션
- 기존 데이터 백업 후 새로운 정확한 컬럼명으로 테이블 재생성
"""

import sqlite3
import os
from datetime import datetime

def migrate_to_unified_columns():
    """기존 데이터를 새로운 통일된 컬럼명으로 마이그레이션"""
    
    db_path = "daham_meal.db"
    backup_path = f"daham_meal_backup_before_unified_{datetime.now().strftime('%Y%m%d_%H%M')}.db"
    
    print(f"데이터베이스 마이그레이션 시작...")
    
    # 백업 생성
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"백업 완료: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 기존 데이터 조회
        cursor.execute("SELECT COUNT(*) FROM ingredients WHERE is_active = 1")
        existing_count = cursor.fetchone()[0]
        print(f"기존 활성 식자재: {existing_count}개")
        
        # 기존 데이터 백업 테이블로 이동
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ingredients_old AS 
        SELECT * FROM ingredients
        """)
        
        # 기존 테이블 삭제
        cursor.execute("DROP TABLE ingredients")
        
        # 새로운 정확한 컬럼명으로 테이블 생성
        cursor.execute("""
        CREATE TABLE ingredients (
            id INTEGER PRIMARY KEY,
            "분류(대분류)" TEXT,
            "식자재(세분류)" TEXT,  
            "고유코드" TEXT UNIQUE,
            "식자재명" TEXT NOT NULL,
            "원산지" TEXT,
            "게시유무" TEXT,
            "규격" TEXT,
            "단위" TEXT,
            "면세" TEXT,
            "선발주일" TEXT,
            "입고가" DECIMAL(10,2),
            "판매가" DECIMAL(10,2),
            "거래처명" TEXT,
            "비고" TEXT,
            "여유필드1" TEXT,
            "여유필드2" TEXT,
            "여유필드3" TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_by TEXT,
            upload_batch_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # 인덱스 생성
        cursor.execute('CREATE INDEX idx_ingredients_category ON ingredients("분류(대분류)")')
        cursor.execute('CREATE INDEX idx_ingredients_subcategory ON ingredients("식자재(세분류)")')  
        cursor.execute('CREATE INDEX idx_ingredients_code ON ingredients("고유코드")')
        cursor.execute('CREATE INDEX idx_ingredients_name ON ingredients("식자재명")')
        cursor.execute('CREATE INDEX idx_ingredients_supplier ON ingredients("거래처명")')
        cursor.execute('CREATE INDEX idx_ingredients_active ON ingredients(is_active)')
        
        # 기존 데이터를 새로운 컬럼명으로 매핑하여 삽입 (중복 제거)
        cursor.execute("""
        INSERT INTO ingredients (
            "분류(대분류)", "식자재(세분류)", "고유코드", "식자재명", 
            "원산지", "게시유무", "규격", "단위", "면세", "선발주일",
            "입고가", "판매가", "거래처명", "비고",
            "여유필드1", "여유필드2", "여유필드3",
            is_active, created_by, upload_batch_id, created_at, updated_at
        )
        SELECT 
            "분류(대분류)", 
            COALESCE("기본식자재(소분류)", "식자재(세분류)") as "식자재(세분류)",
            COALESCE("식자재코드", "고유코드") as "고유코드",
            "식자재명",
            COALESCE("브랜드명", "원산지") as "원산지",  -- 브랜드명을 원산지로 매핑
            COALESCE("게시여부", "게시유무") as "게시유무",
            COALESCE("입고명", "규격") as "규격",  -- 입고명을 규격으로 매핑
            "단위",
            COALESCE("과세", "면세") as "면세",
            COALESCE("배송일수", "선발주일") as "선발주일",
            "입고가", "판매가",
            COALESCE("판매처명", "거래처명") as "거래처명",
            "비고",
            "여유필드1", "여유필드2", "여유필드3",
            is_active, created_by, upload_batch_id, created_at, updated_at
        FROM (
            SELECT *, 
                   ROW_NUMBER() OVER (PARTITION BY COALESCE("식자재코드", "고유코드") ORDER BY id) as rn
            FROM ingredients_old 
            WHERE COALESCE("식자재코드", "고유코드") IS NOT NULL 
            AND TRIM(COALESCE("식자재코드", "고유코드")) != ''
        ) ranked
        WHERE rn = 1
        
        UNION ALL
        
        SELECT 
            "분류(대분류)", 
            COALESCE("기본식자재(소분류)", "식자재(세분류)") as "식자재(세분류)",
            NULL as "고유코드",  -- 코드가 없는 경우
            "식자재명",
            COALESCE("브랜드명", "원산지") as "원산지",
            COALESCE("게시여부", "게시유무") as "게시유무", 
            COALESCE("입고명", "규격") as "규격",
            "단위",
            COALESCE("과세", "면세") as "면세",
            COALESCE("배송일수", "선발주일") as "선발주일",
            "입고가", "판매가",
            COALESCE("판매처명", "거래처명") as "거래처명",
            "비고",
            "여유필드1", "여유필드2", "여유필드3",
            is_active, created_by, upload_batch_id, created_at, updated_at
        FROM ingredients_old
        WHERE (COALESCE("식자재코드", "고유코드") IS NULL OR TRIM(COALESCE("식자재코드", "고유코드")) = '')
        """)
        
        # 결과 확인
        cursor.execute("SELECT COUNT(*) FROM ingredients WHERE is_active = 1")
        new_count = cursor.fetchone()[0]
        
        conn.commit()
        
        print(f"마이그레이션 완료!")
        print(f"- 이전 데이터: {existing_count}개")
        print(f"- 마이그레이션된 데이터: {new_count}개")
        print(f"- 백업 테이블: ingredients_old")
        
        # 새로운 테이블 구조 확인
        cursor.execute("PRAGMA table_info(ingredients)")
        columns = cursor.fetchall()
        print("\n새로운 테이블 구조:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"마이그레이션 오류: {e}")
        conn.rollback()
        raise
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_to_unified_columns()