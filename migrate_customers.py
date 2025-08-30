#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Customer 테이블을 계층 구조를 지원하도록 마이그레이션하는 스크립트
"""
import sqlite3
import os
from datetime import datetime

DATABASE_PATH = "meal_management.db"

def check_table_exists(cursor, table_name):
    """테이블 존재 여부 확인"""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cursor.fetchone() is not None

def check_column_exists(cursor, table_name, column_name):
    """컬럼 존재 여부 확인"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    return any(column[1] == column_name for column in columns)

def migrate_customers_table():
    """customers 테이블 마이그레이션"""
    if not os.path.exists(DATABASE_PATH):
        print(f"[ERROR] 데이터베이스 파일을 찾을 수 없습니다: {DATABASE_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        print(f"[INFO] 데이터베이스 연결 성공: {DATABASE_PATH}")
        
        # customers 테이블 존재 확인
        if not check_table_exists(cursor, 'customers'):
            print("[ERROR] customers 테이블이 존재하지 않습니다.")
            return False
        
        print("[OK] customers 테이블 존재 확인")
        
        # 현재 테이블 구조 확인
        cursor.execute("PRAGMA table_info(customers)")
        current_columns = cursor.fetchall()
        print(f"[INFO] 현재 customers 테이블 컬럼: {[col[1] for col in current_columns]}")
        
        # 추가할 컬럼들 정의
        new_columns = [
            ("site_type", "VARCHAR(20) DEFAULT 'detail'"),
            ("parent_id", "INTEGER REFERENCES customers(id)"),
            ("level", "INTEGER DEFAULT 0"),
            ("sort_order", "INTEGER DEFAULT 0"),
            ("portion_size", "INTEGER"),
            ("is_active", "BOOLEAN DEFAULT TRUE"),
            ("contact_person", "VARCHAR(100)"),
            ("contact_phone", "VARCHAR(50)"),
            ("address", "TEXT"),
            ("description", "TEXT"),
            ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
            ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP")
        ]
        
        # 필요한 컬럼들 추가
        added_columns = []
        for column_name, column_def in new_columns:
            if not check_column_exists(cursor, 'customers', column_name):
                try:
                    alter_query = f"ALTER TABLE customers ADD COLUMN {column_name} {column_def}"
                    cursor.execute(alter_query)
                    added_columns.append(column_name)
                    print(f"[OK] 컬럼 추가: {column_name}")
                except Exception as e:
                    print(f"[ERROR] 컬럼 추가 실패 ({column_name}): {e}")
            else:
                print(f"[SKIP] 이미 존재하는 컬럼: {column_name}")
        
        if added_columns:
            print(f"[SUCCESS] 총 {len(added_columns)}개 컬럼이 추가되었습니다: {added_columns}")
        else:
            print("[INFO] 추가할 컬럼이 없습니다. 모든 컬럼이 이미 존재합니다.")
        
        # 변경사항 커밋
        conn.commit()
        
        # 마이그레이션 후 테이블 구조 재확인
        cursor.execute("PRAGMA table_info(customers)")
        updated_columns = cursor.fetchall()
        print(f"[INFO] 마이그레이션 후 customers 테이블 컬럼: {[col[1] for col in updated_columns]}")
        
        # 샘플 계층 데이터 삽입
        print("[INFO] 샘플 계층 데이터 삽입 중...")
        
        # 기존 데이터 확인
        cursor.execute("SELECT COUNT(*) FROM customers")
        existing_count = cursor.fetchone()[0]
        
        if existing_count == 0:
            # 계층 구조 샘플 데이터
            sample_data = [
                # 헤드 오피스 (level 0)
                (1, "웰스토리 본사", "head", None, 0, 1, True, "김본부", "02-123-4567", "서울시 강남구", "웰스토리 본사"),
                
                # 세부 사업장 (level 1) - 헤드 오피스 하위
                (2, "삼성전자 본사", "detail", 1, 1, 2, True, "박영양", "031-200-1234", "수원시 영통구", "삼성전자 본사 구내식당"),
                (3, "LG전자 본사", "detail", 1, 1, 3, True, "이영양", "02-3777-1234", "서울시 영등포구", "LG전자 본사 구내식당"),
                (4, "현대자동차 본사", "detail", 1, 1, 4, True, "최영양", "02-3464-1234", "서울시 서초구", "현대자동차 본사 구내식당"),
                
                # 기간별 사업장 (level 2) - 삼성전자 하위
                (5, "삼성전자 1공장", "period", 2, 2, 5, True, "김조리", "031-200-5678", "수원시 영통구", "삼성전자 1공장 구내식당"),
                (6, "삼성전자 2공장", "period", 2, 2, 6, True, "이조리", "031-200-5679", "수원시 영통구", "삼성전자 2공장 구내식당"),
                
                # 기간별 사업장 (level 2) - LG전자 하위  
                (7, "LG전자 평택공장", "period", 3, 2, 7, True, "박조리", "031-8080-1234", "평택시 청북면", "LG전자 평택공장 구내식당"),
            ]
            
            insert_query = """
            INSERT INTO customers (id, name, site_type, parent_id, level, sort_order, is_active, 
                                 contact_person, contact_phone, address, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            for data in sample_data:
                try:
                    cursor.execute(insert_query, data)
                    print(f"[OK] 샘플 데이터 삽입: {data[1]} ({data[2]}, level {data[4]})")
                except Exception as e:
                    print(f"[ERROR] 샘플 데이터 삽입 실패 ({data[1]}): {e}")
            
            conn.commit()
            print("[SUCCESS] 샘플 계층 데이터 삽입 완료")
            
        else:
            print(f"[INFO] 기존 데이터가 {existing_count}개 있으므로 샘플 데이터를 삽입하지 않습니다.")
        
        cursor.close()
        conn.close()
        
        print("[SUCCESS] customers 테이블 마이그레이션이 완료되었습니다!")
        return True
        
    except Exception as e:
        print(f"[ERROR] 마이그레이션 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Customer 테이블 계층구조 마이그레이션 시작")
    print("=" * 60)
    
    success = migrate_customers_table()
    
    print("=" * 60)
    if success:
        print("마이그레이션 성공!")
    else:
        print("마이그레이션 실패!")
    print("=" * 60)