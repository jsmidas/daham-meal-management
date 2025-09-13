#!/usr/bin/env python3
"""
실제 사용자가 입력한 식단가 데이터 추출
sample data/meal plan/ 폴더의 Excel 파일들에서 진짜 데이터 추출
"""
import pandas as pd
import os
import sqlite3
from datetime import datetime

def extract_meal_pricing_from_excel():
    """Excel 파일들에서 식단가 데이터 추출"""
    try:
        meal_plan_dir = "sample data/meal plan"
        
        if not os.path.exists(meal_plan_dir):
            print(f"디렉토리가 존재하지 않습니다: {meal_plan_dir}")
            return
        
        excel_files = [f for f in os.listdir(meal_plan_dir) if f.endswith('.xlsx')]
        print(f"발견된 Excel 파일들: {excel_files}")
        
        all_meal_data = []
        
        for file in excel_files:
            file_path = os.path.join(meal_plan_dir, file)
            print(f"\n=== {file} 분석 중 ===")
            
            # 파일명에서 사업장명 추출 (학교, 도시락, 운반, 요양원)
            location_name = None
            if '학교' in file:
                location_name = '학교'
            elif '도시락' in file:
                location_name = '도시락'
            elif '운반' in file:
                location_name = '운반'
            elif '요양원' in file:
                location_name = '요양원'
            
            try:
                # Excel 파일 읽기
                df = pd.read_excel(file_path, sheet_name=None)  # 모든 시트 읽기
                
                print(f"시트 목록: {list(df.keys())}")
                
                for sheet_name, sheet_data in df.items():
                    print(f"\n시트: {sheet_name}")
                    print(f"컬럼들: {list(sheet_data.columns)}")
                    print(f"행 수: {len(sheet_data)}")
                    
                    # 처음 5행 출력
                    if len(sheet_data) > 0:
                        print("처음 5행:")
                        print(sheet_data.head().to_string())
                        
                        # 식단가나 가격 관련 컬럼 찾기
                        price_columns = [col for col in sheet_data.columns 
                                       if any(keyword in str(col).lower() for keyword in ['price', '가격', '단가', '금액', '원가'])]
                        
                        if price_columns:
                            print(f"가격 관련 컬럼들: {price_columns}")
                            
                        # 데이터를 딕셔너리로 저장
                        meal_data = {
                            'file_name': file,
                            'location_name': location_name,
                            'sheet_name': sheet_name,
                            'data': sheet_data,
                            'columns': list(sheet_data.columns),
                            'row_count': len(sheet_data)
                        }
                        all_meal_data.append(meal_data)
                    
            except Exception as e:
                print(f"파일 {file} 읽기 오류: {e}")
        
        return all_meal_data
        
    except Exception as e:
        print(f"오류 발생: {e}")
        return []

def check_existing_database_tables():
    """기존 데이터베이스에서 식단가 관련 테이블들 확인"""
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        # 식단가 관련 테이블들 찾기
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND (name LIKE '%meal%' OR name LIKE '%menu%' OR name LIKE '%pricing%')
        """)
        tables = cursor.fetchall()
        
        print("=== 식단가/메뉴 관련 테이블들 ===")
        for table in tables:
            table_name = table[0]
            print(f"\n테이블: {table_name}")
            
            # 테이블 구조 확인
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print("컬럼들:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # 데이터 개수 확인
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"데이터 개수: {count}")
            
            # 샘플 데이터 (최대 3개)
            if count > 0 and count <= 10:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                samples = cursor.fetchall()
                print("샘플 데이터:")
                for i, sample in enumerate(samples, 1):
                    print(f"  {i}: {sample}")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"데이터베이스 오류: {e}")

if __name__ == "__main__":
    print("=== 실제 식단가 데이터 분석 시작 ===")
    
    # Excel 파일에서 데이터 추출
    meal_data = extract_meal_pricing_from_excel()
    
    print(f"\n총 {len(meal_data)}개의 데이터셋 발견")
    
    # 기존 데이터베이스 테이블도 확인
    print("\n" + "="*50)
    check_existing_database_tables()