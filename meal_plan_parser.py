import pandas as pd
import os
from pathlib import Path

def parse_meal_plan_structure():
    """식단표의 정확한 구조를 파악하고 파싱합니다."""
    
    base_path = Path("sample data/meal plan")
    files = list(base_path.glob("*.xlsx"))
    
    print("=== 식단표 데이터 구조 상세 분석 ===\n")
    
    for file_path in files:
        print(f"분석 중: {file_path.name}")
        print("="*60)
        
        try:
            excel_file = pd.ExcelFile(file_path)
            sheet_name = excel_file.sheet_names[0]  # 첫 번째 시트만 분석
            
            # 헤더 없이 모든 데이터 읽기
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
            
            print(f"시트명: {sheet_name}")
            print(f"전체 크기: {df.shape}")
            
            # 첫 번째 행 (제목)
            title_row = df.iloc[0]
            print(f"제목: {title_row[0]}")
            
            # 세 번째 행 (식사 종류와 인분)  
            meal_info = df.iloc[2]
            print(f"식사 정보: {meal_info[0]}")
            
            # 네 번째 행 (컬럼 헤더)
            headers = df.iloc[3].tolist()
            print(f"헤더: {headers}")
            
            # 실제 식재료 데이터 시작 (5행부터)
            data_start = 4
            food_data = df.iloc[data_start:]
            
            # 메뉴별 데이터 분석
            menu_sections = []
            current_section = None
            
            for idx, row in food_data.iterrows():
                first_col = str(row[0]).strip()
                
                # 메뉴 섹션 시작인지 확인 (예: "자)보쌈김치찌개-중식")
                if first_col.startswith(('자)', '중)', '석)', '간)')):
                    if current_section:
                        menu_sections.append(current_section)
                    current_section = {
                        'menu_name': first_col,
                        'items': [],
                        'start_row': idx
                    }
                elif current_section and pd.notna(row[1]) and str(row[1]).strip():
                    # 식재료 항목
                    item = {
                        'ingredient': str(row[1]).strip(),
                        'unit_amount': row[2] if pd.notna(row[2]) else 0,
                        'total_amount': row[3] if pd.notna(row[3]) else 0,
                        'unit': str(row[4]).strip() if pd.notna(row[4]) else '',
                        'note': str(row[5]).strip() if pd.notna(row[5]) else ''
                    }
                    current_section['items'].append(item)
            
            # 마지막 섹션 추가
            if current_section:
                menu_sections.append(current_section)
            
            print(f"\n발견된 메뉴 수: {len(menu_sections)}")
            
            # 첫 번째 메뉴의 상세 정보 출력
            if menu_sections:
                first_menu = menu_sections[0]
                print(f"\n[첫 번째 메뉴 예시]")
                print(f"메뉴명: {first_menu['menu_name']}")
                print(f"식재료 수: {len(first_menu['items'])}")
                
                if first_menu['items']:
                    print("식재료 목록 (처음 3개):")
                    for i, item in enumerate(first_menu['items'][:3]):
                        print(f"  {i+1}. {item['ingredient']}")
                        print(f"     - 단위량: {item['unit_amount']}")
                        print(f"     - 총량: {item['total_amount']}")  
                        print(f"     - 단위: {item['unit']}")
                        if item['note']:
                            print(f"     - 비고: {item['note']}")
                        print()
            
            print("\n" + "="*60 + "\n")
                
        except Exception as e:
            print(f"오류: {e}")
            print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    parse_meal_plan_structure()