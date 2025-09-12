#!/usr/bin/env python3
"""
Excel 컬럼 이름 정확히 출력하기
"""

import pandas as pd
import sys

def print_columns():
    excel_file = "temp_upload_12순기 다함푸드 단가표 (0908-0927).xlsx"
    df = pd.read_excel(excel_file)
    
    print("EXACT COLUMN NAMES:")
    for i, col in enumerate(df.columns):
        print(f"{i+1:2d}. '{col}'")
    
    print("\nCURRENT MAPPING ISSUES:")
    current_mapping = [
        '분류(대분류)',
        '기본식자재(소분류)',
        '식자재코드', 
        '식자재명',
        '브랜드명',
        '게시여부',
        '입고명',
        '단위',
        '과세',
        '배송일수',
        '입고가',
        '판매가',
        '판매처명',
        '비고'
    ]
    
    excel_cols = list(df.columns)
    for mapping_col in current_mapping:
        if mapping_col in excel_cols:
            print(f"OK: '{mapping_col}' exists")
        else:
            print(f"MISSING: '{mapping_col}' not found")
            # 비슷한 컬럼 찾기
            similar = [col for col in excel_cols if any(word in col for word in mapping_col.split())]
            if similar:
                print(f"  Similar: {similar}")

if __name__ == "__main__":
    print_columns()