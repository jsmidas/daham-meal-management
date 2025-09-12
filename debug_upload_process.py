"""
업로드 과정 디버깅 스크립트
실제 Excel 파일을 읽어서 규격 필드가 어떻게 처리되는지 단계별로 확인
"""

import pandas as pd
import numpy as np

def debug_excel_processing():
    """Excel 파일 처리 과정 디버깅"""
    
    file_path = r'c:\Users\master\Downloads\92_new동원홈푸드(다함푸드-영남)-25년 9월 16~30일.xlsx'
    
    try:
        print("=" * 60)
        print("Excel 파일 처리 디버깅")
        print("=" * 60)
        
        # 1. Excel 파일 읽기
        df = pd.read_excel(file_path)
        print(f"1. 파일 읽기 완료: {len(df)}행")
        
        # 2. 컬럼 확인
        print(f"\n2. 컬럼 목록 ({len(df.columns)}개):")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i:2d}. '{col}'")
        
        # 3. column_mapping 적용
        column_mapping = {
            '분류(대분류)': 'category',
            '기본식자재(세분류)': 'sub_category',
            '고유코드': 'ingredient_code',
            '식자재명': 'ingredient_name',
            '원산지': 'origin',
            '게시유무': 'posting_status',
            '규격': 'specification',
            '단위': 'unit',
            '면세': 'tax_type',
            '선발주일': 'delivery_days',
            '입고가': 'purchase_price',
            '판매가': 'selling_price',
            '거래처명': 'supplier_name',
            '비고': 'notes'
        }
        
        print(f"\n3. 컬럼 매핑 확인:")
        for excel_col, db_col in column_mapping.items():
            if excel_col in df.columns:
                print(f"   ✓ '{excel_col}' -> '{db_col}' (존재)")
            else:
                print(f"   ✗ '{excel_col}' -> '{db_col}' (없음)")
        
        # 4. 첫 번째 행의 실제 데이터 처리 과정 시뮬레이션
        print(f"\n4. 첫 번째 행 데이터 처리 시뮬레이션:")
        if len(df) > 0:
            row = df.iloc[0]
            
            print("   원본 Excel 데이터:")
            for excel_col in column_mapping.keys():
                if excel_col in df.columns:
                    value = row[excel_col]
                    print(f"     {excel_col}: '{value}' (타입: {type(value).__name__})")
            
            # ingredient_data 생성 시뮬레이션
            ingredient_data = {}
            for excel_col, db_col in column_mapping.items():
                if excel_col in df.columns:
                    value = row[excel_col]
                    # NaN 처리
                    if pd.isna(value):
                        ingredient_data[db_col] = None
                    else:
                        ingredient_data[db_col] = str(value).strip() if isinstance(value, str) else value
                else:
                    ingredient_data[db_col] = None
            
            print("\\n   변환된 ingredient_data:")
            for db_col, value in ingredient_data.items():
                print(f"     {db_col}: '{value}' (타입: {type(value).__name__})")
            
            # convert_korean_values 함수 시뮬레이션 (규격만)
            spec_value = ingredient_data.get('specification')
            print(f"\\n   규격 필드 convert_korean_values 적용 전: '{spec_value}'")
            
            # convert_korean_values 로직 적용
            if spec_value is not None:
                import re
                # 업체명 패턴들을 제거
                company_patterns = [
                    r'[가-힣]+\\s*업체\\s*[,\\s]*',
                    r'[가-힣]+\\s*회사\\s*[,\\s]*',
                    r'\\(주\\)\\s*[가-힣]+\\s*[,\\s]*',
                    r'[가-힣]+\\s*\\(주\\)\\s*[,\\s]*',
                ]
                
                cleaned_value = str(spec_value)
                for pattern in company_patterns:
                    cleaned_value = re.sub(pattern, '', cleaned_value, flags=re.IGNORECASE)
                
                cleaned_value = cleaned_value.strip(' ,')
                final_spec = cleaned_value if cleaned_value else str(spec_value)
            else:
                final_spec = None
                
            print(f"   규격 필드 convert_korean_values 적용 후: '{final_spec}'")
        
        # 5. 규격 필드의 실제 데이터 분포 확인
        print(f"\\n5. 전체 규격 필드 데이터 분석:")
        if '규격' in df.columns:
            spec_column = df['규격']
            
            print(f"   총 데이터 수: {len(spec_column)}")
            print(f"   NULL 개수: {spec_column.isnull().sum()}")
            print(f"   빈 문자열 개수: {(spec_column == '').sum()}")
            print(f"   유효 데이터 개수: {(~spec_column.isnull() & (spec_column != '')).sum()}")
            
            # 고유값 10개 샘플
            unique_specs = spec_column.dropna().drop_duplicates().head(10)
            print("\\n   고유 규격 값 샘플:")
            for i, spec in enumerate(unique_specs, 1):
                print(f"     {i:2d}. '{spec}'")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_excel_processing()