"""
데이터베이스 최적화 스크립트
- 인덱스 생성
- 쿼리 최적화
- 캐싱 전략
"""

import sqlite3
import time

def optimize_database():
    """데이터베이스 성능 최적화"""
    
    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()
    
    print("데이터베이스 최적화 시작...")
    
    # 1. 기존 인덱스 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    existing_indexes = [row[0] for row in cursor.fetchall()]
    print(f"기존 인덱스: {existing_indexes}")
    
    # 2. 필수 인덱스 생성
    indexes = [
        # 검색 성능 최적화
        ('idx_ingredients_name', 'ingredients', '"식자재명"'),
        ('idx_ingredients_code', 'ingredients', '"고유코드"'),
        ('idx_ingredients_supplier', 'ingredients', '"거래처명"'),
        
        # 복합 인덱스 (자주 함께 검색되는 필드)
        ('idx_ingredients_supplier_name', 'ingredients', '"거래처명", "식자재명"'),
        
        # 정렬 최적화
        ('idx_ingredients_created', 'ingredients', '"등록일"'),
        ('idx_ingredients_price', 'ingredients', '"판매가"'),
        
        # 필터링 최적화
        ('idx_ingredients_category', 'ingredients', '"분류(대분류)"'),
        ('idx_ingredients_subcategory', 'ingredients', '"기본식자재(세분류)"'),
    ]
    
    for idx_name, table, columns in indexes:
        if idx_name not in existing_indexes:
            try:
                start = time.time()
                cursor.execute(f'CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({columns})')
                elapsed = time.time() - start
                print(f"✓ 인덱스 생성: {idx_name} ({elapsed:.2f}초)")
            except Exception as e:
                print(f"✗ 인덱스 생성 실패 {idx_name}: {e}")
    
    # 3. 데이터베이스 최적화 명령어
    print("\n데이터베이스 최적화 중...")
    
    # VACUUM: 불필요한 공간 정리
    cursor.execute("VACUUM")
    print("✓ VACUUM 완료")
    
    # ANALYZE: 쿼리 최적화를 위한 통계 정보 업데이트
    cursor.execute("ANALYZE")
    print("✓ ANALYZE 완료")
    
    # 4. 데이터베이스 설정 최적화
    optimizations = [
        # 캐시 크기 증가 (기본 2MB -> 64MB)
        ("PRAGMA cache_size = -64000", "캐시 크기: 64MB"),
        
        # 페이지 크기 (새 DB에만 적용)
        # ("PRAGMA page_size = 4096", "페이지 크기: 4KB"),
        
        # WAL 모드 활성화 (동시 읽기/쓰기 성능 향상)
        ("PRAGMA journal_mode = WAL", "WAL 모드 활성화"),
        
        # 동기화 모드 (성능 우선)
        ("PRAGMA synchronous = NORMAL", "동기화 모드: NORMAL"),
        
        # 임시 저장소를 메모리에
        ("PRAGMA temp_store = MEMORY", "임시 저장소: 메모리"),
        
        # 멀티스레드 활성화
        ("PRAGMA threads = 4", "멀티스레드: 4"),
    ]
    
    print("\n데이터베이스 설정 최적화...")
    for pragma, description in optimizations:
        try:
            cursor.execute(pragma)
            print(f"✓ {description}")
        except Exception as e:
            print(f"✗ {description} 실패: {e}")
    
    # 5. 통계 정보
    cursor.execute("SELECT COUNT(*) FROM ingredients")
    total_records = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT \"거래처명\") FROM ingredients")
    total_suppliers = cursor.fetchone()[0]
    
    # 데이터베이스 크기
    cursor.execute("SELECT page_count * page_size FROM pragma_page_count(), pragma_page_size()")
    db_size_bytes = cursor.fetchone()[0]
    db_size_mb = db_size_bytes / (1024 * 1024)
    
    print(f"\n=== 데이터베이스 통계 ===")
    print(f"총 레코드: {total_records:,}개")
    print(f"거래처 수: {total_suppliers}개")
    print(f"DB 크기: {db_size_mb:.2f}MB")
    
    # 6. 쿼리 성능 테스트
    print(f"\n=== 쿼리 성능 테스트 ===")
    
    test_queries = [
        ("전체 조회", "SELECT COUNT(*) FROM ingredients"),
        ("거래처 검색", 'SELECT COUNT(*) FROM ingredients WHERE "거래처명" LIKE "%웰스토리%"'),
        ("식자재명 검색", 'SELECT COUNT(*) FROM ingredients WHERE "식자재명" LIKE "%김치%"'),
        ("가격 범위", 'SELECT COUNT(*) FROM ingredients WHERE "판매가" BETWEEN 1000 AND 5000'),
        ("복합 검색", 'SELECT COUNT(*) FROM ingredients WHERE "거래처명" = "거래처명" AND "판매가" > 1000'),
    ]
    
    for name, query in test_queries:
        start = time.time()
        cursor.execute(query)
        result = cursor.fetchone()[0]
        elapsed = (time.time() - start) * 1000  # ms
        print(f"{name}: {result:,}개 ({elapsed:.2f}ms)")
    
    conn.commit()
    conn.close()
    
    print("\n✅ 데이터베이스 최적화 완료!")
    
    return {
        "total_records": total_records,
        "total_suppliers": total_suppliers,
        "db_size_mb": db_size_mb
    }

if __name__ == "__main__":
    optimize_database()