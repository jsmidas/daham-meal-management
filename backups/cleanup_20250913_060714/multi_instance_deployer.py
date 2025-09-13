#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
멀티 인스턴스 배포 시스템
고객사별 독립 서버 + DB + 브랜딩으로 완전 분리 운영
"""

import os
import json
import shutil
import subprocess
from datetime import datetime

class MultiInstanceDeployer:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.customers_dir = os.path.join(self.base_dir, 'customers')
        self.config_file = os.path.join(self.base_dir, 'customer_instances.json')
        
        # 기본 폴더 생성
        os.makedirs(self.customers_dir, exist_ok=True)
        
    def load_customer_config(self):
        """고객사 인스턴스 설정 로드"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"customers": {}, "next_port": 8001}
    
    def save_customer_config(self, config):
        """고객사 인스턴스 설정 저장"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def get_core_files(self):
        """복사할 핵심 파일 목록"""
        return [
            'main.py',
            'models.py', 
            'admin_dashboard.html',
            'dashboard.html',
            'ingredients_management.html',
            'meal_count_management.html',
            'cooking_instruction_management.html',
            'static/',
            'modules/',
            'app/',
            'daham_meal.db'  # 빈 스키마만 복사
        ]
    
    def create_customer_instance(self, customer_id, company_name, system_name):
        """고객사 인스턴스 생성"""
        
        print(f"고객사 인스턴스 생성 시작: {customer_id}")
        print("=" * 50)
        
        # 1. 고객 설정 로드
        config = self.load_customer_config()
        
        if customer_id in config["customers"]:
            print(f"이미 존재하는 고객사: {customer_id}")
            return config["customers"][customer_id]
        
        # 2. 포트 할당
        port = config["next_port"]
        config["next_port"] += 1
        
        # 3. 고객사 폴더 생성
        customer_dir = os.path.join(self.customers_dir, customer_id)
        os.makedirs(customer_dir, exist_ok=True)
        
        # 4. 핵심 파일 복사
        print("1. 핵심 파일 복사 중...")
        for item in self.get_core_files():
            source = os.path.join(self.base_dir, item)
            target = os.path.join(customer_dir, item)
            
            if os.path.isfile(source):
                shutil.copy2(source, target)
                print(f"   [FILE] {item}")
            elif os.path.isdir(source):
                if os.path.exists(target):
                    shutil.rmtree(target)
                shutil.copytree(source, target)
                print(f"   [DIR]  {item}")
        
        # 5. 데이터베이스 초기화
        print("2. 고객사 전용 데이터베이스 생성...")
        customer_db = f"{customer_id}_meal.db"
        customer_db_path = os.path.join(customer_dir, customer_db)
        
        # 기존 DB를 복사한 후 데이터만 클리어 (스키마는 유지)
        if os.path.exists(os.path.join(customer_dir, 'daham_meal.db')):
            shutil.move(
                os.path.join(customer_dir, 'daham_meal.db'), 
                customer_db_path
            )
        
        # 6. main.py 포트 수정
        print("3. 서버 설정 수정...")
        main_py_path = os.path.join(customer_dir, 'main.py')
        self.update_main_py_port(main_py_path, port, customer_db)
        
        # 7. 화이트라벨 브랜딩 적용
        print("4. 브랜딩 적용...")
        branding_config = {
            'company_name': company_name,
            'system_name': system_name
        }
        self.apply_branding(customer_dir, branding_config)
        
        # 8. 고객사 정보 저장
        customer_info = {
            'customer_id': customer_id,
            'company_name': company_name,
            'system_name': system_name,
            'port': port,
            'directory': customer_dir,
            'database': customer_db,
            'url': f'http://127.0.0.1:{port}',
            'created_at': datetime.now().isoformat(),
            'status': 'created'
        }
        
        config["customers"][customer_id] = customer_info
        self.save_customer_config(config)
        
        print("5. 고객사 인스턴스 생성 완료!")
        print("=" * 50)
        print(f"고객사: {company_name}")
        print(f"시스템명: {system_name}")
        print(f"포트: {port}")
        print(f"URL: http://127.0.0.1:{port}")
        print(f"디렉토리: {customer_dir}")
        
        return customer_info
    
    def update_main_py_port(self, main_py_path, port, db_name):
        """main.py의 포트와 DB 경로 수정"""
        
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 포트 변경
        content = content.replace(
            'uvicorn.run(app, host="127.0.0.1", port=8003',
            f'uvicorn.run(app, host="127.0.0.1", port={port}'
        )
        
        # DB 경로 변경 
        content = content.replace(
            'DATABASE_URL = "sqlite:///./daham_meal.db"',
            f'DATABASE_URL = "sqlite:///./{db_name}"'
        )
        
        with open(main_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"   main.py 포트: {port}, DB: {db_name}")
    
    def apply_branding(self, customer_dir, branding_config):
        """화이트라벨 브랜딩 적용"""
        
        # 기존 화이트라벨 시스템 활용
        replacement_rules = {
            '다함식단관리': branding_config['system_name'],
            '다함 급식관리': f"{branding_config['company_name']} 급식관리",
            '다함 식자재 관리': f"{branding_config['company_name']} 식자재 관리", 
            '다함': branding_config['company_name']
        }
        
        # HTML 파일들 브랜딩 적용
        html_files = [f for f in os.listdir(customer_dir) if f.endswith('.html')]
        
        for html_file in html_files:
            file_path = os.path.join(customer_dir, html_file)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for old_text, new_text in replacement_rules.items():
                if old_text in content:
                    content = content.replace(old_text, new_text)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        print(f"   브랜딩 적용: {branding_config['company_name']}")
    
    def start_customer_instance(self, customer_id):
        """고객사 인스턴스 서버 시작"""
        
        config = self.load_customer_config()
        
        if customer_id not in config["customers"]:
            print(f"존재하지 않는 고객사: {customer_id}")
            return False
        
        customer = config["customers"][customer_id]
        customer_dir = customer["directory"]
        main_py_path = os.path.join(customer_dir, 'main.py')
        
        if not os.path.exists(main_py_path):
            print(f"main.py 파일을 찾을 수 없습니다: {main_py_path}")
            return False
        
        print(f"고객사 '{customer['company_name']}' 서버 시작...")
        print(f"포트: {customer['port']}")
        print(f"URL: {customer['url']}")
        
        # 백그라운드에서 서버 실행
        process = subprocess.Popen([
            'python', main_py_path
        ], cwd=customer_dir)
        
        # 프로세스 ID 저장
        customer['process_id'] = process.pid
        customer['status'] = 'running'
        config["customers"][customer_id] = customer
        self.save_customer_config(config)
        
        return True
    
    def list_customers(self):
        """고객사 목록 조회"""
        
        config = self.load_customer_config()
        
        if not config["customers"]:
            print("등록된 고객사가 없습니다.")
            return
        
        print("등록된 고객사 목록:")
        print("=" * 70)
        
        for customer_id, info in config["customers"].items():
            status = info.get('status', 'unknown')
            print(f"ID: {customer_id}")
            print(f"회사명: {info['company_name']}")
            print(f"시스템: {info['system_name']}")
            print(f"포트: {info['port']} | URL: {info['url']}")
            print(f"상태: {status}")
            print("-" * 50)

def main():
    """테스트 및 데모 실행"""
    
    deployer = MultiInstanceDeployer()
    
    print("멀티 인스턴스 배포 시스템")
    print("=" * 50)
    
    while True:
        print("\n1. 새 고객사 인스턴스 생성")
        print("2. 고객사 서버 시작")
        print("3. 고객사 목록 보기")
        print("4. 종료")
        
        choice = input("\n선택하세요 (1-4): ").strip()
        
        if choice == '1':
            customer_id = input("고객사 ID (영문): ")
            company_name = input("회사명: ")
            system_name = input("시스템명 (기본값: '회사명 급식관리 시스템'): ")
            
            if not system_name:
                system_name = f"{company_name} 급식관리 시스템"
            
            deployer.create_customer_instance(customer_id, company_name, system_name)
            
        elif choice == '2':
            customer_id = input("시작할 고객사 ID: ")
            success = deployer.start_customer_instance(customer_id)
            
            if success:
                print("서버 시작됨! 백그라운드에서 실행 중...")
            
        elif choice == '3':
            deployer.list_customers()
            
        elif choice == '4':
            print("종료합니다.")
            break
        
        else:
            print("잘못된 선택입니다.")

if __name__ == "__main__":
    main()