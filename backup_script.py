#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
데이터베이스 자동 백업 스크립트
매일 자동으로 데이터베이스를 백업합니다.
"""
import sqlite3
import shutil
import os
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def create_backup():
    """데이터베이스 백업 생성"""
    try:
        source_db = 'daham_meal.db'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_db = f'backups/daham_meal_backup_{timestamp}.db'
        
        # 백업 디렉토리 생성
        os.makedirs('backups', exist_ok=True)
        
        # 데이터베이스 백업
        shutil.copy2(source_db, backup_db)
        
        # 백업 검증
        conn = sqlite3.connect(backup_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        logging.info(f"백업 완료: {backup_db} ({len(tables)}개 테이블)")
        
        # 오래된 백업 정리 (30일 이상)
        cleanup_old_backups()
        
        return backup_db
        
    except Exception as e:
        logging.error(f"백업 실패: {e}")
        return None

def cleanup_old_backups(days_to_keep=30):
    """30일 이상 된 백업 파일 정리"""
    if not os.path.exists('backups'):
        return
        
    current_time = datetime.now()
    
    for filename in os.listdir('backups'):
        if filename.startswith('daham_meal_backup_'):
            file_path = os.path.join('backups', filename)
            file_time = datetime.fromtimestamp(os.path.getctime(file_path))
            
            if (current_time - file_time).days > days_to_keep:
                os.remove(file_path)
                logging.info(f"오래된 백업 삭제: {filename}")

def verify_critical_data():
    """중요 데이터 존재 여부 확인"""
    try:
        conn = sqlite3.connect('daham_meal.db')
        cursor = conn.cursor()
        
        # 각 테이블의 데이터 개수 확인
        critical_tables = [
            'users', 'business_locations', 'suppliers', 
            'customers', 'ingredients', 'recipes'
        ]
        
        for table in critical_tables:
            try:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                count = cursor.fetchone()[0]
                if count == 0:
                    logging.warning(f"⚠️ {table} 테이블이 비어있습니다!")
                else:
                    logging.info(f"✅ {table}: {count}개 데이터")
            except sqlite3.OperationalError:
                logging.error(f"❌ {table} 테이블이 존재하지 않습니다!")
        
        conn.close()
        
    except Exception as e:
        logging.error(f"데이터 검증 실패: {e}")

if __name__ == '__main__':
    print("=== 데이터베이스 백업 및 검증 ===")
    
    # 1. 데이터 검증
    verify_critical_data()
    
    # 2. 백업 생성
    backup_file = create_backup()
    
    if backup_file:
        print(f"✅ 백업 성공: {backup_file}")
    else:
        print("❌ 백업 실패")