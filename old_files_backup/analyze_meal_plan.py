import pandas as pd
import os
from pathlib import Path

def analyze_meal_plan_files():
    """샘플 식단표 파일들을 분석하여 구조를 파악합니다."""
    
    base_path = Path("sample data/meal plan")
    files = list(base_path.glob("*.xlsx"))
    
    print("=== 샘플 식단표 파일 분석 ===\n")
    
    for file_path in files:
        print(f"파일: {file_path.name}")
        print("-" * 50)
        
        try:
            # Excel 파일의 모든 시트 확인
            excel_file = pd.ExcelFile(file_path)
            print(f"시트 목록: {excel_file.sheet_names}")
            
            for sheet_name in excel_file.sheet_names:
                print(f"\n[시트: {sheet_name}]")
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                print(f"크기: {df.shape[0]} 행 × {df.shape[1]} 열")
                
                # 첫 몇 행 출력 (데이터 구조 파악)
                print("첫 5행:")
                print(df.head().to_string())
                
                # 비어있지 않은 셀이 있는 영역 확인
                non_empty_rows = df.dropna(how='all').shape[0]
                non_empty_cols = df.dropna(how='all', axis=1).shape[1]
                print(f"실제 데이터 영역: {non_empty_rows} 행 × {non_empty_cols} 열")
                
                print("\n" + "="*30 + "\n")
                
        except Exception as e:
            print(f"오류 발생: {e}")
            print("\n" + "="*30 + "\n")

if __name__ == "__main__":
    analyze_meal_plan_files()