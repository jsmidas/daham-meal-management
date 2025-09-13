"""
오늘 업로드된 식자재의 규격 필드 누락 문제 해결 스크립트
삼성웰스토리를 제외한 모든 업체의 규격 필드가 누락된 문제를 수정
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

def fix_specification_fields():
    """규격 필드 누락 문제 해결"""
    
    # 데이터베이스 연결
    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()
    
    try:
        # 오늘 날짜
        today = datetime.now().strftime('%Y-%m-%d')
        print(f"처리 대상 날짜: {today}")
        
        # 오늘 업로드된 식자재 중 규격이 누락된 항목 확인
        cursor.execute('''
            SELECT id, supplier_name, ingredient_name, ingredient_code, specification
            FROM ingredients 
            WHERE DATE(created_at) = ? 
            AND supplier_name != '삼성웰스토리'
            AND (specification IS NULL OR specification = '')
        ''', (today,))
        
        missing_items = cursor.fetchall()
        print(f"규격 필드가 누락된 항목: {len(missing_items):,}개")
        
        if not missing_items:
            print("누락된 규격 필드가 없습니다.")
            return
        
        # 공급업체별 현황 확인
        supplier_counts = {}
        for item in missing_items:
            supplier = item[1]
            if supplier not in supplier_counts:
                supplier_counts[supplier] = 0
            supplier_counts[supplier] += 1
        
        print("\n공급업체별 누락 현황:")
        for supplier, count in supplier_counts.items():
            print(f"  {supplier}: {count:,}개")
        
        # 사용자 확인
        print(f"\n총 {len(missing_items):,}개 항목의 규격 필드를 수정하시겠습니까?")
        print("규격 필드에 기본값 '규격정보없음'이 설정됩니다.")
        
        response = input("계속하시겠습니까? (y/N): ").strip().lower()
        if response != 'y':
            print("작업이 취소되었습니다.")
            return
        
        # 백업 생성
        backup_filename = f"daham_meal_backup_before_specification_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        os.system(f'copy daham_meal.db "{backup_filename}"')
        print(f"백업 파일 생성: {backup_filename}")
        
        # 배치로 업데이트 실행
        print("\n규격 필드 업데이트 중...")
        batch_size = 1000
        updated_count = 0
        
        for i in range(0, len(missing_items), batch_size):
            batch = missing_items[i:i+batch_size]
            ids = [str(item[0]) for item in batch]
            
            # 배치 업데이트
            placeholders = ','.join(['?' for _ in ids])
            cursor.execute(f'''
                UPDATE ingredients 
                SET specification = '규격정보없음', updated_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
            ''', ids)
            
            updated_count += cursor.rowcount
            print(f"  진행률: {min(i + batch_size, len(missing_items)):,} / {len(missing_items):,} ({(min(i + batch_size, len(missing_items)) / len(missing_items) * 100):.1f}%)")
        
        # 커밋
        conn.commit()
        print(f"\n✅ 업데이트 완료: {updated_count:,}개 항목")
        
        # 결과 확인
        cursor.execute('''
            SELECT supplier_name, COUNT(*) as count
            FROM ingredients 
            WHERE DATE(created_at) = ? 
            AND supplier_name != '삼성웰스토리'
            AND specification = '규격정보없음'
            GROUP BY supplier_name
        ''', (today,))
        
        updated_results = cursor.fetchall()
        if updated_results:
            print("\n업데이트된 항목 현황:")
            for supplier, count in updated_results:
                print(f"  {supplier}: {count:,}개")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 오류 발생: {e}")
        raise
    finally:
        conn.close()

def verify_specification_fix():
    """규격 필드 수정 결과 확인"""
    
    conn = sqlite3.connect('daham_meal.db')
    cursor = conn.cursor()
    
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 전체 현황 확인
        cursor.execute('''
            SELECT 
                supplier_name,
                COUNT(*) as total,
                SUM(CASE WHEN specification IS NULL OR specification = '' THEN 1 ELSE 0 END) as missing,
                SUM(CASE WHEN specification = '규격정보없음' THEN 1 ELSE 0 END) as fixed
            FROM ingredients 
            WHERE DATE(created_at) = ? 
            AND supplier_name != '삼성웰스토리'
            GROUP BY supplier_name
        ''', (today,))
        
        results = cursor.fetchall()
        
        print(f"오늘({today}) 업로드된 식자재 규격 현황:")
        print("=" * 60)
        print(f"{'공급업체':<15} {'전체':<8} {'누락':<8} {'수정':<8} {'상태'}")
        print("-" * 60)
        
        total_items = 0
        total_missing = 0
        total_fixed = 0
        
        for supplier, total, missing, fixed in results:
            status = "✅ 완료" if missing == 0 else f"⚠️  {missing}개 누락"
            print(f"{supplier:<15} {total:<8} {missing:<8} {fixed:<8} {status}")
            
            total_items += total
            total_missing += missing
            total_fixed += fixed
        
        print("-" * 60)
        print(f"{'합계':<15} {total_items:<8} {total_missing:<8} {total_fixed:<8}")
        
        if total_missing == 0:
            print("\n✅ 모든 규격 필드가 정상적으로 처리되었습니다!")
        else:
            print(f"\n⚠️  아직 {total_missing}개 항목에 규격이 누락되어 있습니다.")
            
    except Exception as e:
        print(f"❌ 확인 중 오류 발생: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("="*60)
    print("식자재 규격 필드 누락 문제 해결 도구")
    print("="*60)
    
    while True:
        print("\n메뉴:")
        print("1. 규격 필드 수정 실행")
        print("2. 현재 상태 확인")
        print("3. 종료")
        
        choice = input("\n선택 (1-3): ").strip()
        
        if choice == '1':
            fix_specification_fields()
        elif choice == '2':
            verify_specification_fix()
        elif choice == '3':
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 선택입니다. 1-3 중에서 선택해주세요.")