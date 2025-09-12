#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
식자재 업로드 템플릿 생성 스크립트
"""
import pandas as pd
import os

def create_ingredient_template():
    """식자재 업로드 템플릿 Excel 파일 생성"""
    
    # 템플릿 데이터 구조
    template_data = {
        '식자재명': ['쌀', '돼지고기(삼겹살)', '양파', '당근', '감자'],
        '단위': ['kg', 'kg', 'kg', 'kg', 'kg'],
        '단가': [3000, 15000, 2000, 2500, 1500],
        '공급업체': ['한국미곡', '정육점', '농협', '농협', '농협'],
        '최소주문량': [20, 5, 10, 10, 20],
        '비고': ['', '국산', '국산', '국산', '']
    }
    
    # DataFrame 생성
    df = pd.DataFrame(template_data)
    
    # templates 폴더 생성
    os.makedirs('templates', exist_ok=True)
    
    # Excel 파일로 저장
    template_path = 'templates/ingredient_template.xlsx'
    
    with pd.ExcelWriter(template_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='식자재목록', index=False)
        
        # 워크시트 가져오기
        workbook = writer.book
        worksheet = writer.sheets['식자재목록']
        
        # 컬럼 너비 조정
        column_widths = {
            'A': 20,  # 식자재명
            'B': 10,  # 단위
            'C': 12,  # 단가
            'D': 15,  # 공급업체
            'E': 12,  # 최소주문량
            'F': 15   # 비고
        }
        
        for column, width in column_widths.items():
            worksheet.column_dimensions[column].width = width
        
        # 헤더 스타일 적용
        from openpyxl.styles import Font, PatternFill, Alignment
        
        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center')
        
        for cell in worksheet[1]:  # 첫 번째 행 (헤더)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
    
    print(f"템플릿 파일이 생성되었습니다: {template_path}")
    return template_path

if __name__ == "__main__":
    create_ingredient_template()