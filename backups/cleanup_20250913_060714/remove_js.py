#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def remove_inline_js():
    with open('admin_dashboard.html', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # JavaScript 블록들 찾기 및 제거
    new_lines = []
    skip = False
    js_scripts_added = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 첫 번째 <script> 태그 시작
        if line.strip() == '<script>' and not js_scripts_added:
            # 외부 JavaScript 파일들 추가
            new_lines.append('    <script src="/static/js/admin-dashboard-main.js"></script>\n')
            new_lines.append('    <script src="/static/js/admin-dashboard-additional.js"></script>\n')
            new_lines.append('    <script src="/static/js/admin-dashboard-final.js"></script>\n')
            js_scripts_added = True
            skip = True
        elif line.strip() == '</script>' and skip:
            skip = False
        elif line.strip().startswith('<script>') and skip == False and 'src=' not in line:
            skip = True
        elif line.strip() == '</script>' and skip:
            skip = False
        elif not skip:
            new_lines.append(line)
        
        i += 1
    
    # 파일 쓰기
    with open('admin_dashboard.html', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"JavaScript 제거 및 외부화 완료")
    print(f"새 파일 크기: {len(new_lines)}줄")

if __name__ == "__main__":
    remove_inline_js()