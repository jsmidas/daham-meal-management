#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

def convert_inline_styles():
    with open('admin_dashboard.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 변환 규칙들
    conversions = [
        # Button background colors
        (r'style="[^"]*background:\s*#17a2b8[^"]*"', 'class="btn-info"'),
        (r'style="[^"]*background:\s*#28a745[^"]*"', 'class="btn-success"'),
        (r'style="[^"]*background:\s*#6c757d[^"]*"', 'class="btn-secondary-gray"'),
        (r'style="[^"]*background:\s*#f39c12[^"]*"', 'class="btn-warning"'),
        (r'style="[^"]*background:\s*#e74c3c[^"]*"', 'class="btn-danger"'),
        (r'style="[^"]*background:\s*#007bff[^"]*"', 'class="btn-primary-blue"'),
        (r'style="[^"]*background:\s*#667eea[^"]*"', 'class="btn-purple"'),
        (r'style="[^"]*background:\s*#27ae60[^"]*"', 'class="btn-success"'),
        
        # Margins
        (r'style="[^"]*margin-left:\s*10px[^"]*"', 'class="ml-10"'),
        (r'style="[^"]*margin-bottom:\s*15px[^"]*"', 'class="mb-15"'),
        (r'style="[^"]*margin-bottom:\s*20px[^"]*"', 'class="mb-20"'),
        (r'style="[^"]*margin-bottom:\s*30px[^"]*"', 'class="mb-30"'),
        
        # Padding
        (r'style="[^"]*padding:\s*8px\s+12px[^"]*"', 'class="px-12 py-8"'),
        (r'style="[^"]*padding:\s*8px\s+16px[^"]*"', 'class="px-16 py-8"'),
        (r'style="[^"]*padding:\s*10px\s+20px[^"]*"', 'class="px-20 py-10"'),
        
        # Border radius
        (r'style="[^"]*border-radius:\s*4px[^"]*"', 'class="border-radius-4"'),
        (r'style="[^"]*border-radius:\s*5px[^"]*"', 'class="border-radius-5"'),
        (r'style="[^"]*border-radius:\s*8px[^"]*"', 'class="border-radius-8"'),
        
        # Background colors
        (r'style="[^"]*background:\s*#f8f9fa[^"]*"', 'class="bg-light-gray"'),
        (r'style="[^"]*background:\s*white[^"]*"', 'class="bg-white"'),
        (r'style="[^"]*background:\s*#e8f5e8[^"]*"', 'class="bg-light-green"'),
        
        # Display flex
        (r'style="[^"]*display:\s*flex[^"]*"', 'class="flex-row"'),
        
        # Cursor pointer
        (r'style="[^"]*cursor:\s*pointer[^"]*"', 'class="cursor-pointer"'),
    ]
    
    # 변환 적용
    for pattern, replacement in conversions:
        content = re.sub(pattern, replacement, content)
    
    # 복합 스타일 패턴들 (더 복잡한 경우)
    complex_patterns = [
        # 표준 버튼 스타일
        (r'style="padding:\s*8px\s+16px;\s*background:\s*(#[0-9a-fA-F]{6});\s*color:\s*white;\s*border:\s*none;\s*border-radius:\s*4px;\s*cursor:\s*pointer[^"]*"',
         lambda m: f'class="btn-standard {get_bg_class(m.group(1))}"'),
         
        # 대형 버튼 스타일
        (r'style="padding:\s*10px\s+20px;\s*background:\s*(#[0-9a-fA-F]{6});\s*color:\s*white;\s*border:\s*none;\s*border-radius:\s*5px;\s*cursor:\s*pointer[^"]*"',
         lambda m: f'class="btn-large {get_bg_class(m.group(1))}"'),
    ]
    
    for pattern, replacement in complex_patterns:
        content = re.sub(pattern, replacement, content)
    
    # 파일 저장
    with open('admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("인라인 스타일 변환 완료")

def get_bg_class(hex_color):
    color_map = {
        '#17a2b8': 'btn-info',
        '#28a745': 'btn-success', 
        '#6c757d': 'btn-secondary-gray',
        '#f39c12': 'btn-warning',
        '#e74c3c': 'btn-danger',
        '#007bff': 'btn-primary-blue',
        '#667eea': 'btn-purple',
        '#27ae60': 'btn-success'
    }
    return color_map.get(hex_color, 'btn-default')

if __name__ == "__main__":
    convert_inline_styles()