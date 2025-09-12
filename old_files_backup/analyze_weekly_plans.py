"""
BOKSILI 시스템의 주간 식단표 데이터 구조 분석
sample data/ 폴더의 주간식단표 파일들을 분석
"""

import pandas as pd
import os
from pathlib import Path
import json
from datetime import datetime, timedelta

def analyze_weekly_meal_plans():
    """주간 식단표 파일들을 상세 분석"""
    
    base_path = Path("sample data")
    weekly_files = list(base_path.glob("주간식단표_*.xlsx"))
    
    print("="*80)
    print("BOKSILI 주간 식단표 시스템 데이터 분석")
    print("="*80)
    
    weekly_data = {}
    
    for file_path in weekly_files:
        print(f"\n분석 중: {file_path.name}")
        print("-" * 60)
        
        # 파일명에서 정보 추출
        filename = file_path.name
        date_info = parse_weekly_filename(filename)
        
        try:
            # Excel 파일의 모든 시트 확인
            excel_file = pd.ExcelFile(file_path)
            print(f"시트 수: {len(excel_file.sheet_names)}")
            print(f"시트명: {excel_file.sheet_names}")
            
            weekly_data[filename] = {
                'date_info': date_info,
                'sheets': {}
            }
            
            for sheet_name in excel_file.sheet_names:
                print(f"\n[시트: {sheet_name}]")
                
                # 시트 데이터 읽기
                df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
                print(f"크기: {df.shape[0]} 행 × {df.shape[1]} 열")
                
                # 식단표 구조 분석
                sheet_analysis = analyze_meal_plan_structure(df, sheet_name)
                weekly_data[filename]['sheets'][sheet_name] = sheet_analysis
                
                # 첫 20행 출력 (구조 파악용)
                print("첫 20행 데이터:")
                print(df.head(20).to_string(max_cols=10))
                
                # 식단표 패턴 분석
                analyze_meal_patterns(df)
                
                print("\n" + "="*40)
                
        except Exception as e:
            print(f"오류 발생: {e}")
            print("\n" + "="*40)
    
    # 분석 결과 저장
    save_weekly_analysis_result(weekly_data)
    
    # 전체 요약
    print_weekly_summary(weekly_data)

def parse_weekly_filename(filename):
    """파일명에서 날짜 정보 추출"""
    info = {
        'original_name': filename,
        'start_date': None,
        'end_date': None,
        'category': None,
        'week_period': None
    }
    
    # 파일명 패턴: 주간식단표_2025-07-28_2025-08-03_도시락.xlsx
    try:
        parts = filename.replace('.xlsx', '').split('_')
        if len(parts) >= 4:
            info['start_date'] = parts[1]
            info['end_date'] = parts[2]
            info['category'] = parts[3]
            
            # 주차 계산
            start_date = datetime.strptime(parts[1], '%Y-%m-%d')
            end_date = datetime.strptime(parts[2], '%Y-%m-%d')
            days_diff = (end_date - start_date).days
            info['week_period'] = f"{days_diff + 1}일간" if days_diff >= 0 else "날짜오류"
            
    except Exception as e:
        print(f"파일명 파싱 오류: {e}")
    
    return info

def analyze_meal_plan_structure(df, sheet_name):
    """식단표의 구조 분석"""
    analysis = {
        'shape': df.shape,
        'table_structure': 'unknown',
        'days_columns': [],
        'meal_types': [],
        'data_start_row': 0,
        'menu_items': []
    }
    
    # 요일 컬럼 찾기
    weekdays = ['월', '화', '수', '목', '금', '토', '일', '월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
    
    for row_idx in range(min(10, df.shape[0])):
        row_data = df.iloc[row_idx]
        
        for col_idx in range(df.shape[1]):
            cell_value = str(row_data.iloc[col_idx]).strip()
            
            # 요일 헤더 찾기
            for day in weekdays:
                if day in cell_value:
                    analysis['days_columns'].append({
                        'column': col_idx,
                        'day': day,
                        'row': row_idx
                    })
                    break
    
    # 식사 타입 찾기
    meal_types = ['아침', '점심', '저녁', '중식', '석식', '조식', '중식A', '중식B']
    
    for row_idx in range(df.shape[0]):
        row_data = df.iloc[row_idx]
        
        for col_idx in range(df.shape[1]):
            cell_value = str(row_data.iloc[col_idx]).strip()
            
            for meal in meal_types:
                if meal in cell_value and len(cell_value) <= 10:  # 짧은 텍스트만
                    analysis['meal_types'].append({
                        'column': col_idx,
                        'meal': meal,
                        'row': row_idx,
                        'full_text': cell_value
                    })
                    break
    
    # 테이블 구조 판단
    if len(analysis['days_columns']) >= 5:  # 주간 테이블
        analysis['table_structure'] = 'weekly_table'
    elif len(analysis['meal_types']) >= 2:  # 식사별 구조
        analysis['table_structure'] = 'meal_based'
    
    return analysis

def analyze_meal_patterns(df):
    """식단표 내 메뉴 패턴 분석"""
    print("\n메뉴 패턴 분석:")
    
    menu_items = []
    recipe_patterns = []
    
    # 요리명으로 보이는 패턴 찾기
    for row_idx in range(df.shape[0]):
        for col_idx in range(df.shape[1]):
            cell_value = str(df.iloc[row_idx, col_idx]).strip()
            
            # 한글이 포함되고 적당한 길이의 텍스트 (메뉴명 가능성)
            if (len(cell_value) > 2 and len(cell_value) < 50 and 
                any(ord(char) >= 0xAC00 and ord(char) <= 0xD7A3 for char in cell_value) and
                not any(skip in cell_value for skip in ['시트', '월', '화', '수', '목', '금', '토', '일', '아침', '점심', '저녁'])):
                
                # 요리명 패턴 체크
                if any(pattern in cell_value for pattern in ['찌개', '볶음', '구이', '튀김', '무침', '조림', '국', '밥', '면', '탕']):
                    menu_items.append({
                        'row': row_idx,
                        'col': col_idx,
                        'menu': cell_value,
                        'type': 'recipe'
                    })
    
    # 중복 제거 및 요약
    unique_menus = list({item['menu']: item for item in menu_items}.values())
    
    print(f"  발견된 메뉴 수: {len(unique_menus)}")
    if unique_menus:
        print("  메뉴 예시:")
        for i, menu in enumerate(unique_menus[:10]):
            print(f"    {i+1}. {menu['menu']} (위치: 행{menu['row']}, 열{menu['col']})")

def save_weekly_analysis_result(weekly_data):
    """분석 결과를 JSON 파일로 저장"""
    
    # JSON 직렬화를 위한 데이터 변환
    json_data = {}
    for filename, data in weekly_data.items():
        json_data[filename] = {
            'date_info': data['date_info'],
            'sheets': {}
        }
        
        for sheet_name, sheet_data in data['sheets'].items():
            json_data[filename]['sheets'][sheet_name] = {
                'shape': sheet_data['shape'],
                'table_structure': sheet_data['table_structure'],
                'days_columns': sheet_data['days_columns'],
                'meal_types': sheet_data['meal_types'],
                'data_start_row': sheet_data['data_start_row']
            }
    
    with open('weekly_meal_plan_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n분석 결과가 'weekly_meal_plan_analysis.json'에 저장되었습니다.")

def print_weekly_summary(weekly_data):
    """전체 분석 요약 출력"""
    print("\n" + "="*80)
    print("BOKSILI 주간 식단표 시스템 분석 요약")
    print("="*80)
    
    print(f"분석된 파일 수: {len(weekly_data)}")
    
    # 카테고리별 요약
    categories = {}
    date_ranges = []
    
    for filename, data in weekly_data.items():
        date_info = data['date_info']
        category = date_info['category']
        
        if category:
            if category not in categories:
                categories[category] = []
            categories[category].append(filename)
        
        if date_info['start_date'] and date_info['end_date']:
            date_ranges.append({
                'start': date_info['start_date'],
                'end': date_info['end_date'],
                'category': category
            })
    
    print(f"\n확인된 카테고리:")
    for category, files in categories.items():
        print(f"  - {category}: {len(files)}개 파일")
    
    print(f"\n날짜 범위:")
    for date_range in sorted(date_ranges, key=lambda x: x['start']):
        print(f"  - {date_range['start']} ~ {date_range['end']} ({date_range['category']})")
    
    print(f"\n식단표 구조 특징:")
    print(f"  - 주간 단위 (7일) 식단표 형태")
    print(f"  - 카테고리별 구분 (도시락 등)")
    print(f"  - Excel 기반 테이블 구조")
    print(f"  - 요일별 × 식사별 매트릭스 형태")

if __name__ == "__main__":
    analyze_weekly_meal_plans()