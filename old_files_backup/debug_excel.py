#!/usr/bin/env python3
"""
Excel 파일 구조 및 데이터 디버깅 스크립트
"""

import pandas as pd
import numpy as np

def debug_excel_file():
    """Excel 파일의 구조와 데이터를 자세히 분석"""
    
    excel_file = "temp_upload_12순기 다함푸드 단가표 (0908-0927).xlsx"
    
    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(excel_file)
        
        print("=" * 60)
        print("EXCEL FILE ANALYSIS")
        print("=" * 60)
        
        print(f"파일: {excel_file}")
        print(f"총 행 수: {len(df)}")
        print(f"총 컬럼 수: {len(df.columns)}")
        print()
        
        # 컬럼 이름들 출력
        print("실제 컬럼 이름들:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1:2d}. '{col}'")
        print()
        
        # 첫 5행 데이터 출력
        print("첫 5행 데이터:")
        print(df.head().to_string())
        print()
        
        # 각 컬럼별 null 값 개수 확인
        print("각 컬럼별 Null 값 개수:")
        null_counts = df.isnull().sum()
        for col in df.columns:
            null_count = null_counts[col]
            non_null_count = len(df) - null_count
            print(f"  {col:<25}: {null_count:5d} null, {non_null_count:5d} 값 있음")
        print()
        
        # 핵심 컬럼들 샘플 데이터 확인
        key_columns = [
            '분류(대분류)', 
            '기본식자재(소분류)', 
            '식자재코드', 
            '식자재명', 
            '브랜드명',
            '판매처명'
        ]
        
        print("핵심 컬럼들의 샘플 데이터:")
        for col in key_columns:
            if col in df.columns:
                sample_values = df[col].dropna().head(5).tolist()
                print(f"  {col}:")
                for val in sample_values:
                    print(f"    '{val}'")
                print()
            else:
                print(f"  {col}: 컬럼이 존재하지 않음")
                print()
        
        # 현재 사용 중인 컬럼 매핑과 실제 컬럼명 비교
        current_mapping = {
            '분류(대분류)': 'category',
            '기본식자재(소분류)': 'sub_category',
            '식자재코드': 'ingredient_code',
            '식자재명': 'ingredient_name',
            '브랜드명': 'brand_name',
            '게시여부': 'extra_field1',
            '입고명': 'product_name',
            '단위': 'unit',
            '과세': 'tax_type',
            '배송일수': 'delivery_days',
            '입고가': 'purchase_price',
            '판매가': 'selling_price',
            '판매처명': 'supplier_name',
            '비고': 'notes'
        }
        
        print("현재 매핑과 실제 컬럼 존재 여부:")
        for excel_col, db_field in current_mapping.items():
            exists = excel_col in df.columns
            status = "✓ 존재" if exists else "✗ 없음"
            print(f"  {excel_col:<20} -> {db_field:<15} {status}")
            
            if exists:
                # 해당 컬럼의 첫 번째 non-null 값 출력
                first_val = df[excel_col].dropna().iloc[0] if not df[excel_col].dropna().empty else "모든 값이 null"
                print(f"    첫 번째 값: '{first_val}'")
        print()
        
        # 실제 엑셀 컬럼 중에서 매핑되지 않은 컬럼들
        mapped_cols = set(current_mapping.keys())
        excel_cols = set(df.columns)
        unmapped_cols = excel_cols - mapped_cols
        
        if unmapped_cols:
            print("매핑되지 않은 Excel 컬럼들:")
            for col in sorted(unmapped_cols):
                print(f"  '{col}'")
        
    except Exception as e:
        print(f"오류 발생: {e}")

if __name__ == "__main__":
    debug_excel_file()