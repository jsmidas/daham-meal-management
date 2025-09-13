#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def remove_inline_css():
    with open('admin_dashboard.html', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # CSS 시작과 끝 찾기
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if '.admin-container {' in line:
            start_idx = i
        elif line.strip() == '</style>':
            end_idx = i
            break
    
    if start_idx != -1 and end_idx != -1:
        # CSS 부분 제거
        new_lines = lines[:start_idx] + lines[end_idx+1:]
        
        with open('admin_dashboard.html', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        print(f"CSS 제거 완료: 줄 {start_idx+1}부터 {end_idx+1}까지 제거됨")
        print(f"제거된 줄 수: {end_idx - start_idx + 1}")
        print(f"새 파일 크기: {len(new_lines)}줄")
    else:
        print("CSS 영역을 찾을 수 없습니다.")

if __name__ == "__main__":
    remove_inline_css()