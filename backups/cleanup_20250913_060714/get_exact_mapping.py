#!/usr/bin/env python3
"""
정확한 컬럼 매핑을 위한 Excel 컬럼명 추출
"""

import pandas as pd

def generate_correct_mapping():
    excel_file = "temp_upload_12순기 다함푸드 단가표 (0908-0927).xlsx"
    df = pd.read_excel(excel_file)
    
    print("# Correct column mapping based on actual Excel file:")
    print("column_mapping = {")
    
    # 현재 매핑에서 기대하는 컬럼들과 실제 Excel 컬럼들을 매치
    expected_mappings = {
        'category': ['분류', '대분류'],
        'sub_category': ['기본', '소분류'],
        'ingredient_code': ['식자재코드', '코드'],
        'ingredient_name': ['식자재명', '명'],
        'brand_name': ['브랜드명', '브랜드'],
        'extra_field1': ['게시여부', '게시'],
        'product_name': ['입고명', '입고'],
        'unit': ['단위'],
        'tax_type': ['과세'],
        'delivery_days': ['배송일수', '배송'],
        'purchase_price': ['입고가'],
        'selling_price': ['판매가'],
        'supplier_name': ['판매처', '처명'],
        'notes': ['비고']
    }
    
    excel_columns = list(df.columns)
    
    for db_field, keywords in expected_mappings.items():
        found_col = None
        for excel_col in excel_columns:
            if all(keyword in excel_col for keyword in keywords):
                found_col = excel_col
                break
        
        if found_col:
            print(f"    '{found_col}': '{db_field}',")
            # 샘플 데이터도 보여주기
            sample = df[found_col].dropna().iloc[0] if not df[found_col].dropna().empty else "NULL"
            print(f"    # Sample: '{sample}'")
        else:
            print(f"    # NOT FOUND for {db_field}: {keywords}")
    
    print("}")
    
    print("\nAll Excel columns:")
    for col in excel_columns:
        print(f"'{col}'")

if __name__ == "__main__":
    generate_correct_mapping()