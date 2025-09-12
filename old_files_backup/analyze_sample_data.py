import pandas as pd
import os
from pathlib import Path

def analyze_sample_data():
    """샘플 데이터 구조를 분석합니다."""
    
    sample_dir = Path("sample data")
    meal_plan_dir = sample_dir / "meal plan"
    upload_dir = sample_dir / "upload"
    
    print("=" * 60)
    print("다함식단관리 - 샘플 데이터 분석")
    print("=" * 60)
    
    # 1. 식단표 데이터 분석
    print("\n1. 식단표 데이터 분석")
    print("-" * 30)
    
    meal_plan_files = list(meal_plan_dir.glob("*.xlsx"))
    print(f"식단표 파일 개수: {len(meal_plan_files)}")
    
    for file_path in meal_plan_files:
        print(f"\n파일명: {file_path.name}")
        try:
            # Excel 파일의 모든 시트 확인
            xl_file = pd.ExcelFile(file_path)
            print(f"  시트명: {xl_file.sheet_names}")
            
            # 첫 번째 시트 분석
            if xl_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=xl_file.sheet_names[0])
                print(f"  행 수: {len(df)}")
                print(f"  열 수: {len(df.columns)}")
                print(f"  컬럼명: {list(df.columns)[:10]}")  # 처음 10개만
                
                # 데이터 샘플 출력
                print("  데이터 샘플:")
                for i, row in df.head(5).iterrows():
                    print(f"    행 {i+1}: {dict(list(row.items())[:3])}")
                    
        except Exception as e:
            print(f"  오류: {e}")
    
    # 2. 공급업체 단가표 데이터 분석
    print("\n\n2. 공급업체 단가표 데이터 분석")
    print("-" * 30)
    
    upload_files = list(upload_dir.glob("*.xls*"))
    print(f"단가표 파일 개수: {len(upload_files)}")
    
    for file_path in upload_files:
        print(f"\n파일명: {file_path.name}")
        try:
            xl_file = pd.ExcelFile(file_path)
            print(f"  시트명: {xl_file.sheet_names}")
            
            # 첫 번째 시트 분석
            if xl_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=xl_file.sheet_names[0])
                print(f"  행 수: {len(df)}")
                print(f"  열 수: {len(df.columns)}")
                print(f"  컬럼명: {list(df.columns)[:8]}")
                
                # 데이터 샘플 출력
                print("  데이터 샘플:")
                for i, row in df.head(3).iterrows():
                    print(f"    행 {i+1}: {dict(list(row.items())[:4])}")
                    
        except Exception as e:
            print(f"  오류: {e}")
    
    # 3. 데이터 구조 추천
    print("\n\n3. 데이터 구조 분석 결과")
    print("-" * 30)
    print("분석을 통해 다음 단계를 추천합니다:")
    print("1. 공급업체 단가표 → Suppliers, Ingredients, SupplierIngredients 테이블")
    print("2. 식단표 → DietPlans, Menus, MenuItems, Recipes 테이블")
    print("3. 레시피-식재료 매핑 → RecipeIngredients 테이블")
    print("4. 데이터 정규화 및 중복 제거 필요")

if __name__ == "__main__":
    analyze_sample_data()