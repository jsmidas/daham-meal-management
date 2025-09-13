#!/usr/bin/env python3
"""
다함푸드 브랜드 컬러 일괄 업데이트 스크립트
- 기존 파란색 계열을 오렌지색으로 변경
- 로고 텍스트를 "복실이"에서 "다함"으로 변경
"""

import os
import re

# 파일 목록
html_files = [
    'meal_plan_interface.html',
    'weekly_meal_plan_interface.html', 
    'meal_count_management.html',
    'meal_count_input.html',
    'supplier_management.html',
    'business_location_management.html',
    'ordering_system.html',
    'user_management.html',
    'ingredient_file_upload.html',
    'ingredient_file_viewer.html',
    'ingredient_selection_popup.html'
]

# 색상 매핑 (구 색상 -> 새 색상)
color_mappings = {
    # 기본 파란색 팔레트
    '#2c5aa0': '#F5881F',
    '#1e3a5f': '#E67309', 
    '#007bff': '#F5881F',
    '#0056b3': '#E67309',
    
    # 그라데이션
    'linear-gradient(135deg, #2c5aa0 0%, #1e3a5f 100%)': 'linear-gradient(135deg, #F5881F 0%, #E67309 100%)',
    'linear-gradient(135deg, #667eea 0%, #764ba2 100%)': 'linear-gradient(135deg, #F5881F 0%, #E67309 100%)',
    
    # 배경색
    '#f8f9ff': '#fff8f0',
    '#e3f2fd': '#ffeee6',
    '#bbdefb': '#ffcc9a',
    
    # 기타 파란색 계열
    '#1976d2': '#F5881F',
    '#1565c0': '#E67309',
    '#2196f3': '#F5881F'
}

# 로고 텍스트 매핑
logo_mappings = {
    '복실이': '다함',
    'BOKSILI': '다함',
    '복실이 시스템': '다함 시스템'
}

def update_file_colors(file_path):
    """단일 파일의 색상을 업데이트"""
    if not os.path.exists(file_path):
        print(f"파일을 찾을 수 없음: {file_path}")
        return False
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 색상 변경
        for old_color, new_color in color_mappings.items():
            content = content.replace(old_color, new_color)
        
        # 로고 텍스트 변경 (HTML 태그 내에서만)
        for old_logo, new_logo in logo_mappings.items():
            # div class="logo" 내부의 텍스트만 변경
            content = re.sub(
                r'(<div class="logo"[^>]*>)' + re.escape(old_logo) + r'(</div>)',
                r'\1' + new_logo + r'\2',
                content
            )
            # 타이틀에서도 변경
            content = re.sub(
                r'(<title>[^<]*?)' + re.escape(old_logo),
                r'\1' + new_logo,
                content
            )
        
        # 파일이 변경되었다면 저장
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] 업데이트 완료: {file_path}")
            return True
        else:
            print(f"[SKIP] 변경사항 없음: {file_path}")
            return False
            
    except Exception as e:
        print(f"[ERROR] 오류 발생 {file_path}: {e}")
        return False

def main():
    """메인 실행 함수"""
    print("="*60)
    print("다함푸드 브랜드 컬러 업데이트 시작")
    print("="*60)
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    updated_count = 0
    
    for html_file in html_files:
        file_path = os.path.join(base_dir, html_file)
        if update_file_colors(file_path):
            updated_count += 1
    
    print("="*60)
    print(f"업데이트 완료: {updated_count}/{len(html_files)} 파일")
    print("주요 변경사항:")
    print("  - 파란색 계열 -> 다함푸드 오렌지 (#F5881F)")
    print("  - 로고 텍스트: '복실이' -> '다함'")
    print("  - 그라데이션 및 배경색 모두 업데이트")
    print("="*60)

if __name__ == '__main__':
    main()