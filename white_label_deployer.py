#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
화이트라벨 브랜딩 자동 배포 시스템
로고와 회사명을 고객사 맞춤으로 자동 변경
"""

import os
import re
import json
from datetime import datetime
import shutil

class WhiteLabelDeployer:
    def __init__(self, config_file=None):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config = self.load_config(config_file)
        self.backup_dir = None
        
    def load_config(self, config_file):
        """브랜딩 설정 로드"""
        if config_file and os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 기본 설정 (테스트용)
        return {
            'company_name': '테스트푸드',
            'system_name': '테스트 급식관리 시스템',
            'short_name': '테스트',
            'colors': {
                'primary': '#007bff',
                'secondary': '#6c757d',
                'gradient': 'linear-gradient(135deg, #007bff 0%, #6c757d 100%)'
            },
            'contact': {
                'support_email': 'support@testfood.co.kr',
                'phone': '02-1234-5678'
            }
        }
    
    def create_backup(self):
        """현재 상태 백업"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_dir = f"backups/white_label_backup_{timestamp}"
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # HTML 파일들 백업
        html_files = [f for f in os.listdir(self.base_dir) if f.endswith('.html')]
        for file in html_files:
            if os.path.exists(file):
                shutil.copy2(file, self.backup_dir)
        
        print(f"[BACKUP] 백업 완료: {self.backup_dir}")
        return self.backup_dir
    
    def get_replacement_rules(self):
        """텍스트 치환 규칙 정의"""
        return {
            # 기본 시스템명
            '다함식단관리': self.config['system_name'],
            '다함 급식관리': f"{self.config['company_name']} 급식관리",
            '다함 식자재 관리': f"{self.config['company_name']} 식자재 관리",
            '다함식단관리시스템': self.config['system_name'],
            f"🍽️ 다함식단관리시스템": f"🍽️ {self.config['system_name']}",
            
            # 단축형
            '다함': self.config['company_name'],
            
            # 타이틀 태그들
            '다함식단관리 - 관리자 대시보드': f"{self.config['system_name']} - 관리자 대시보드",
            '📈 대시보드 - 다함식단관리시스템': f"📈 대시보드 - {self.config['system_name']}",
            '다함 조리지시서 관리': f"{self.config['company_name']} 조리지시서 관리",
            '다함 식자재 등록': f"{self.config['company_name']} 식자재 등록",
            
            # 추가 발견된 패턴들
            '15일 식수 관리 - 다함식단관리시스템': f"15일 식수 관리 - {self.config['system_name']}",
            '식수 등록 관리 - 다함식단관리시스템': f"식수 등록 관리 - {self.config['system_name']}",
            '메뉴/레시피 관리 - 다함식단관리시스템': f"메뉴/레시피 관리 - {self.config['system_name']}"
        }
    
    def process_html_file(self, file_path):
        """HTML 파일 처리"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            replacement_rules = self.get_replacement_rules()
            changes_made = []
            
            # 텍스트 치환 수행
            for old_text, new_text in replacement_rules.items():
                if old_text in content:
                    content = content.replace(old_text, new_text)
                    changes_made.append(f"'{old_text}' → '{new_text}'")
            
            # 변경사항이 있으면 파일 저장
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"[OK] {file_path} 업데이트 완료:")
                for change in changes_made:
                    print(f"   - {change}")
                return len(changes_made)
            else:
                print(f"[INFO] {file_path}: 변경사항 없음")
                return 0
                
        except Exception as e:
            print(f"[ERROR] {file_path} 처리 중 오류: {str(e)}")
            return 0
    
    def find_html_files(self):
        """HTML 파일 목록 조회"""
        html_files = []
        for file in os.listdir(self.base_dir):
            if file.endswith('.html') and os.path.isfile(file):
                html_files.append(file)
        return sorted(html_files)
    
    def deploy_branding(self, create_backup=True):
        """브랜딩 배포 실행"""
        print("화이트라벨 브랜딩 배포 시작")
        print("=" * 50)
        print(f"회사명: {self.config['company_name']}")
        print(f"시스템명: {self.config['system_name']}")
        print("=" * 50)
        
        # 백업 생성
        if create_backup:
            self.create_backup()
        
        # HTML 파일 처리
        html_files = self.find_html_files()
        print(f"\n📁 처리할 HTML 파일: {len(html_files)}개")
        
        total_changes = 0
        processed_files = 0
        
        for html_file in html_files:
            if os.path.exists(html_file):
                changes = self.process_html_file(html_file)
                if changes > 0:
                    total_changes += changes
                    processed_files += 1
        
        print("\n🎉 브랜딩 배포 완료!")
        print(f"📊 처리된 파일: {processed_files}개")
        print(f"📝 총 변경사항: {total_changes}개")
        
        if create_backup and self.backup_dir:
            print(f"💾 백업 위치: {self.backup_dir}")
        
        return {
            'processed_files': processed_files,
            'total_changes': total_changes,
            'backup_dir': self.backup_dir
        }
    
    def rollback(self, backup_dir=None):
        """백업에서 복원"""
        backup_path = backup_dir or self.backup_dir
        if not backup_path or not os.path.exists(backup_path):
            print("❌ 백업 디렉토리를 찾을 수 없습니다.")
            return False
        
        print(f"🔄 백업에서 복원 중: {backup_path}")
        
        restored_files = 0
        for file in os.listdir(backup_path):
            if file.endswith('.html'):
                source = os.path.join(backup_path, file)
                target = os.path.join(self.base_dir, file)
                try:
                    shutil.copy2(source, target)
                    restored_files += 1
                    print(f"✅ {file} 복원 완료")
                except Exception as e:
                    print(f"❌ {file} 복원 실패: {str(e)}")
        
        print(f"🎉 복원 완료: {restored_files}개 파일")
        return True

def main():
    """테스트 실행"""
    print("화이트라벨 브랜딩 시스템 테스트")
    
    # 배포기 초기화
    deployer = WhiteLabelDeployer()
    
    # 현재 설정 출력
    print("\n📋 현재 브랜딩 설정:")
    print(f"  - 회사명: {deployer.config['company_name']}")
    print(f"  - 시스템명: {deployer.config['system_name']}")
    
    # 사용자 확인
    response = input("\n브랜딩을 적용하시겠습니까? (y/n): ")
    if response.lower() == 'y':
        result = deployer.deploy_branding()
        
        print("\n테스트 완료! 브라우저에서 확인해보세요:")
        print("http://127.0.0.1:8003/admin")
        
        rollback_response = input("\n원상복구 하시겠습니까? (y/n): ")
        if rollback_response.lower() == 'y':
            deployer.rollback()
    else:
        print("브랜딩 적용을 취소했습니다.")

if __name__ == "__main__":
    main()