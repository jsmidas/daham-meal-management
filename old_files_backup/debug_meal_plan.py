import pandas as pd
from pathlib import Path

def debug_meal_plan():
    """식단표의 실제 데이터를 행별로 확인합니다."""
    
    file_path = Path("sample data/meal plan/0811_도시락.xlsx")
    
    print("=== 도시락 식단표 행별 데이터 확인 ===\n")
    
    try:
        excel_file = pd.ExcelFile(file_path)
        sheet_name = excel_file.sheet_names[0]
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        print(f"총 {df.shape[0]}행 확인 중...\n")
        
        for idx in range(min(20, df.shape[0])):  # 처음 20행만 확인
            row = df.iloc[idx]
            print(f"행 {idx}: ", end="")
            for col_idx, value in enumerate(row):
                if pd.notna(value) and str(value).strip():
                    print(f"[{col_idx}] {repr(str(value).strip())}", end=" | ")
            print()
            
        print("\n" + "="*50)
        
        # 특정 패턴 찾기
        print("메뉴 패턴 찾기...")
        for idx in range(df.shape[0]):
            row = df.iloc[idx]
            first_col = str(row[0]).strip() if pd.notna(row[0]) else ""
            
            if any(pattern in first_col for pattern in ['자)', '중)', '석)', '간)']):
                print(f"행 {idx}: {first_col}")
                
                # 이후 몇 행의 식재료 데이터도 확인
                for next_idx in range(idx+1, min(idx+5, df.shape[0])):
                    next_row = df.iloc[next_idx]
                    if pd.notna(next_row[1]) and str(next_row[1]).strip():
                        print(f"  -> 식재료: {str(next_row[1]).strip()} | {next_row[2]} | {next_row[3]} | {str(next_row[4]).strip()}")
                    else:
                        break
                print()
                
    except Exception as e:
        print(f"오류: {e}")

if __name__ == "__main__":
    debug_meal_plan()