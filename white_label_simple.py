#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 화이트라벨 브랜딩 테스트 스크립트
"""

import os
import shutil
from datetime import datetime

def create_backup():
    """현재 상태 백업"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"backups/white_label_test_{timestamp}"
    os.makedirs(backup_dir, exist_ok=True)
    
    # 주요 HTML 파일들 백업
    files_to_backup = ['admin_dashboard.html', 'dashboard.html', 'ingredients_management.html']
    
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
            print(f"[BACKUP] {file}")
    
    print(f"백업 완료: {backup_dir}")
    return backup_dir

def apply_branding():
    """브랜딩 적용"""
    print("=" * 50)
    print("화이트라벨 브랜딩 테스트 시작")
    print("다함 -> 테스트푸드 로 변경")
    print("=" * 50)
    
    # 치환 규칙
    replacements = {
        '다함식단관리': '테스트 급식관리 시스템',
        '다함 급식관리': '테스트푸드 급식관리',
        '다함 식자재 관리': '테스트푸드 식자재 관리',
        '다함': '테스트푸드'
    }
    
    # 처리할 파일들
    html_files = [f for f in os.listdir('.') if f.endswith('.html')]
    
    total_changes = 0
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 텍스트 치환
            for old_text, new_text in replacements.items():
                if old_text in content:
                    content = content.replace(old_text, new_text)
                    print(f"[{html_file}] {old_text} -> {new_text}")
                    total_changes += 1
            
            # 변경사항이 있으면 저장
            if content != original_content:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"[OK] {html_file} 업데이트 완료")
                
        except Exception as e:
            print(f"[ERROR] {html_file}: {str(e)}")
    
    print("=" * 50)
    print(f"총 {total_changes}개 항목이 변경되었습니다")
    print("브라우저에서 http://127.0.0.1:8003/admin 확인해보세요!")
    print("=" * 50)
    
    return total_changes

def main():
    print("화이트라벨 브랜딩 테스트 도구")
    print("")
    
    # 백업 생성
    backup_dir = create_backup()
    
    # 브랜딩 적용
    changes = apply_branding()
    
    if changes > 0:
        print("")
        print("테스트가 완료되었습니다!")
        print("변경 사항을 확인하신 후, 원래대로 되돌리려면")
        print(f"백업 폴더에서 파일들을 복사해오세요: {backup_dir}")
    else:
        print("변경된 항목이 없습니다.")

if __name__ == "__main__":
    main()