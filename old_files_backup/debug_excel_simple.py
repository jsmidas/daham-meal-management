#!/usr/bin/env python3
"""
Excel 파일 컬럼 매핑 문제 확인
"""

import pandas as pd

def check_column_mapping():
    """컬럼 매핑 문제 확인"""
    
    excel_file = "temp_upload_12순기 다함푸드 단가표 (0908-0927).xlsx"
    df = pd.read_excel(excel_file)
    
    print("="*50)
    print("COLUMN MAPPING ISSUE FOUND!")
    print("="*50)
    
    print("Current mapping expects:")
    print("  '기본식자재(소분류)' -> sub_category")
    print()
    
    print("But Excel file has:")
    for col in df.columns:
        if '기본' in col or '소분류' in col:
            print(f"  '{col}'")
    print()
    
    # 실제로는 '기본식자재(소분류)'가 아니라 다른 이름일 가능성
    print("All columns containing '분류' or similar:")
    for col in df.columns:
        if '분류' in col:
            print(f"  '{col}'")
    print()
    
    print("Sample data from key columns:")
    key_cols = ['분류(대분류)', '기본식자재(소분류)', '식자재명', '판매처명']
    for col in key_cols:
        if col in df.columns:
            sample = df[col].dropna().iloc[0] if not df[col].dropna().empty else "ALL NULL"
            print(f"  {col}: '{sample}'")
        else:
            print(f"  {col}: COLUMN NOT FOUND")

if __name__ == "__main__":
    check_column_mapping()