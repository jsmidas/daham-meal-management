"""
BOKSILI 시스템의 식자재 발주 데이터 구조 분석
sample data/upload/ 폴더의 공급업체 단가표들을 분석
"""

import pandas as pd
import os
from pathlib import Path
import json

def analyze_supplier_files():
    """공급업체 단가표 파일들을 상세 분석"""
    
    base_path = Path("sample data/upload")
    files = list(base_path.glob("*.xls*"))
    
    print("="*80)
    print("BOKSILI 식자재 발주 시스템 데이터 분석")
    print("="*80)
    
    supplier_data = {}
    
    for file_path in files:
        print(f"\n분석 중: {file_path.name}")
        print("-" * 60)
        
        # 파일명에서 정보 추출
        filename = file_path.name
        supplier_info = parse_filename(filename)
        
        try:
            # Excel 파일의 모든 시트 확인
            excel_file = pd.ExcelFile(file_path)
            print(f"시트 수: {len(excel_file.sheet_names)}")
            print(f"시트명: {excel_file.sheet_names}")
            
            supplier_data[filename] = {
                'filename_info': supplier_info,
                'sheets': {}
            }
            
            for sheet_name in excel_file.sheet_names:
                print(f"\n[시트: {sheet_name}]")
                
                # 시트 데이터 읽기 (헤더 없이)
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                print(f"크기: {df.shape[0]} 행 × {df.shape[1]} 열")
                
                # 데이터 구조 분석
                sheet_analysis = analyze_sheet_structure(df, sheet_name)
                supplier_data[filename]['sheets'][sheet_name] = sheet_analysis
                
                # 첫 10행 출력
                print("첫 10행 데이터:")
                print(df.head(10).to_string(max_cols=8))
                
                # 데이터 패턴 분석
                analyze_data_patterns(df)
                
                print("\n" + "="*40)
                
        except Exception as e:
            print(f"오류 발생: {e}")
            print("\n" + "="*40)
    
    # 분석 결과 저장
    save_analysis_result(supplier_data)
    
    # 전체 요약
    print_summary(supplier_data)

def parse_filename(filename):
    """파일명에서 정보 추출"""
    info = {
        'original_name': filename,
        'supplier': None,
        'period': None,
        'type': None
    }
    
    # 파일명 패턴 분석
    if '사조푸디스트' in filename:
        info['supplier'] = '사조푸디스트'
        info['period'] = '8월 하반기'
    elif '동원홈푸드' in filename:
        info['supplier'] = '동원홈푸드'  
        info['period'] = '25년 8월 16-31일'
    elif '영유통' in filename:
        info['supplier'] = '영유통'
        info['period'] = '8월18~24'
    elif '현대그린푸드' in filename:
        info['supplier'] = '현대그린푸드'
        info['period'] = '8월2차'
    elif '씨제이' in filename:
        info['supplier'] = 'CJ'
        info['period'] = '8월 하순'
    elif 'food_sample' in filename:
        info['supplier'] = 'Sample'
        info['type'] = 'template'
    
    return info

def analyze_sheet_structure(df, sheet_name):
    """시트의 데이터 구조 분석"""
    analysis = {
        'shape': df.shape,
        'has_header': False,
        'data_start_row': 0,
        'columns_info': [],
        'data_types': [],
        'key_patterns': []
    }
    
    # 헤더 행 찾기
    for i in range(min(10, df.shape[0])):
        row_data = df.iloc[i].dropna()
        if len(row_data) >= 3:  # 최소 3개 컬럼
            row_str = ' '.join([str(x) for x in row_data])
            
            # 헤더로 보이는 패턴
            if any(keyword in row_str for keyword in ['품명', '단가', '규격', '단위', '원산지', '업체', '코드']):
                analysis['has_header'] = True
                analysis['data_start_row'] = i + 1
                analysis['columns_info'] = row_data.tolist()
                break
    
    # 데이터 타입 분석
    if analysis['data_start_row'] < df.shape[0]:
        data_rows = df.iloc[analysis['data_start_row']:]
        for col in range(df.shape[1]):
            col_data = data_rows.iloc[:, col].dropna()
            if len(col_data) > 0:
                # 숫자형 데이터 비율
                numeric_ratio = sum(pd.to_numeric(col_data, errors='coerce').notna()) / len(col_data)
                
                if numeric_ratio > 0.8:
                    analysis['data_types'].append('numeric')
                elif any(keyword in str(col_data.iloc[0]) for keyword in ['kg', 'g', '개', '팩', 'EA']):
                    analysis['data_types'].append('unit')
                else:
                    analysis['data_types'].append('text')
    
    return analysis

def analyze_data_patterns(df):
    """데이터 패턴 분석"""
    print("\n데이터 패턴 분석:")
    
    # 가격으로 보이는 컬럼 찾기
    price_columns = []
    for col in range(df.shape[1]):
        col_data = df.iloc[:, col].dropna()
        if len(col_data) > 5:
            # 숫자 데이터이면서 큰 값들 (가격)
            try:
                numeric_data = pd.to_numeric(col_data, errors='coerce').dropna()
                if len(numeric_data) > 0 and numeric_data.mean() > 100:
                    price_columns.append(col)
                    print(f"  가격 컬럼 {col}: 평균 {numeric_data.mean():.0f}원")
            except:
                pass
    
    # 품목명으로 보이는 컬럼 찾기
    product_columns = []
    for col in range(df.shape[1]):
        col_data = df.iloc[:, col].dropna().astype(str)
        if len(col_data) > 5:
            # 한글이 많고 다양한 값들 (품목명)
            korean_ratio = sum(any(ord(char) >= 0xAC00 and ord(char) <= 0xD7A3 for char in str(val)) for val in col_data) / len(col_data)
            if korean_ratio > 0.7 and len(col_data.unique()) > len(col_data) * 0.8:
                product_columns.append(col)
                print(f"  품목명 컬럼 {col}: {col_data.iloc[0][:20]}... 등 {len(col_data.unique())}개 품목")

def save_analysis_result(supplier_data):
    """분석 결과를 JSON 파일로 저장"""
    
    # JSON 직렬화를 위해 데이터 변환
    json_data = {}
    for filename, data in supplier_data.items():
        json_data[filename] = {
            'filename_info': data['filename_info'],
            'sheets': {}
        }
        
        for sheet_name, sheet_data in data['sheets'].items():
            json_data[filename]['sheets'][sheet_name] = {
                'shape': sheet_data['shape'],
                'has_header': sheet_data['has_header'],
                'data_start_row': sheet_data['data_start_row'],
                'columns_info': [str(x) for x in sheet_data['columns_info']],
                'data_types': sheet_data['data_types']
            }
    
    with open('supplier_data_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n분석 결과가 'supplier_data_analysis.json'에 저장되었습니다.")

def print_summary(supplier_data):
    """전체 분석 요약 출력"""
    print("\n" + "="*80)
    print("BOKSILI 시스템 데이터 구조 분석 요약")
    print("="*80)
    
    print(f"분석된 파일 수: {len(supplier_data)}")
    
    # 공급업체별 요약
    suppliers = {}
    for filename, data in supplier_data.items():
        supplier = data['filename_info']['supplier']
        if supplier:
            if supplier not in suppliers:
                suppliers[supplier] = []
            suppliers[supplier].append(filename)
    
    print(f"\n확인된 공급업체:")
    for supplier, files in suppliers.items():
        print(f"  - {supplier}: {len(files)}개 파일")
    
    print(f"\n데이터 구조 특징:")
    print(f"  - 대부분 Excel 형태의 단가표")
    print(f"  - 품목명, 단가, 규격, 단위 등의 표준 컬럼 구조")
    print(f"  - 공급업체별 고유한 코드 체계")
    print(f"  - 기간별 단가 업데이트 방식")

if __name__ == "__main__":
    analyze_supplier_files()