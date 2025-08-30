import pandas as pd
import os

def analyze_supplier_data():
    """업체 단가표 파일 분석"""
    
    files = [
        "sample data/upload/82_(사조푸디스트) 08월 하반기 단가표 _ 다함푸드 귀하..xlsx",
        "sample data/upload/82_동원홈푸드(다함푸드-영남)-25년 8월 16-31일.xlsx",
        "sample data/upload/82_현대그린푸드8월2차수견적서(다함푸드.요청양식)-송부용.xlsx",
        "sample data/upload/82다함푸드 8월 하순 단가표 씨제이 0813.xlsx"
    ]
    
    for file_path in files:
        print(f"\n{'='*50}")
        print(f"분석 중: {file_path}")
        print('='*50)
        
        if not os.path.exists(file_path):
            print(f"파일을 찾을 수 없습니다: {file_path}")
            continue
        
        try:
            # 엑셀 파일 읽기
            df = pd.read_excel(file_path)
            
            print(f"총 행 수: {len(df)}")
            print(f"컬럼 수: {len(df.columns)}")
            print("\n컬럼명들:")
            for i, col in enumerate(df.columns):
                print(f"{i+1}. {col}")
            
            # 게시유무 컬럼 찾기
            posting_cols = [col for col in df.columns if '게시' in str(col) or '유무' in str(col)]
            print(f"\n게시유무 관련 컬럼: {posting_cols}")
            
            if posting_cols:
                posting_col = posting_cols[0]
                print(f"\n'{posting_col}' 컬럼의 고유값들:")
                print(df[posting_col].value_counts(dropna=False))
                
                # 발주 가능/불가능 품목 수 집계
                orderable = df[df[posting_col].isin(['유', '']) | df[posting_col].isna()]
                non_orderable = df[df[posting_col] == '무']
                
                print(f"\n발주 가능 품목: {len(orderable)}개")
                print(f"발주 불가능 품목: {len(non_orderable)}개")
                
                # 발주 불가능 품목 예시
                if len(non_orderable) > 0:
                    print("\n발주 불가능 품목 예시:")
                    item_name_col = '품목명' if '품목명' in df.columns else df.columns[1]
                    print(non_orderable[[item_name_col, posting_col]].head(10))
            else:
                print("\n게시유무 컬럼을 찾을 수 없습니다.")
            
        except Exception as e:
            print(f"파일 분석 중 오류 발생: {e}")

if __name__ == "__main__":
    analyze_supplier_data()