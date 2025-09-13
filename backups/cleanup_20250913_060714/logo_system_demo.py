#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로고 이미지 교체 시스템 데모
"""

import os
import shutil
from datetime import datetime

def setup_logo_system():
    """로고 시스템 폴더 구조 생성"""
    
    # 로고 저장 폴더 생성
    os.makedirs('assets/logos/customers', exist_ok=True)
    os.makedirs('assets/logos/templates', exist_ok=True)
    
    print("로고 시스템 폴더 구조:")
    print("assets/")
    print("├── logos/")
    print("│   ├── customers/          # 고객사별 로고 저장")
    print("│   │   ├── testfood/")
    print("│   │   │   ├── main_logo.png      (200x60)")
    print("│   │   │   ├── favicon.ico        (32x32)")
    print("│   │   │   └── login_logo.png     (300x100)")
    print("│   │   ├── company_a/")
    print("│   │   └── company_b/")
    print("│   └── templates/          # 로고 템플릿")
    print("│       ├── default_main.png")
    print("│       ├── default_favicon.ico")
    print("│       └── default_login.png")
    
    return True

def create_logo_config():
    """로고 설정 파일 생성"""
    
    logo_config = '''# 로고 교체 설정 파일
# customer_logos.json

{
    "testfood": {
        "company_name": "테스트푸드",
        "logos": {
            "main": "assets/logos/customers/testfood/main_logo.png",
            "favicon": "assets/logos/customers/testfood/favicon.ico", 
            "login": "assets/logos/customers/testfood/login_logo.png"
        },
        "fallback": {
            "main": "assets/logos/templates/default_main.png",
            "favicon": "assets/logos/templates/default_favicon.ico",
            "login": "assets/logos/templates/default_login.png"
        }
    },
    
    "premium_hotel": {
        "company_name": "프리미엄 호텔",
        "logos": {
            "main": "assets/logos/customers/premium_hotel/main_logo.png",
            "favicon": "assets/logos/customers/premium_hotel/favicon.ico",
            "login": "assets/logos/customers/premium_hotel/login_logo.png"
        }
    }
}'''
    
    with open('customer_logos_config.txt', 'w', encoding='utf-8') as f:
        f.write(logo_config)
    
    print("로고 설정 파일 생성 완료: customer_logos_config.txt")

def demo_logo_replacement():
    """로고 교체 데모 코드"""
    
    demo_code = '''
def replace_logos(customer_id):
    """고객사 로고로 교체"""
    
    logo_mapping = {
        # 현재 시스템의 로고 위치 → 고객사 로고 위치
        'static/images/logo.png': f'assets/logos/customers/{customer_id}/main_logo.png',
        'static/favicon.ico': f'assets/logos/customers/{customer_id}/favicon.ico',
        'assets/login_logo.png': f'assets/logos/customers/{customer_id}/login_logo.png'
    }
    
    for system_logo, customer_logo in logo_mapping.items():
        if os.path.exists(customer_logo):
            # 백업 생성
            if os.path.exists(system_logo):
                shutil.copy2(system_logo, f"{system_logo}.backup")
            
            # 로고 교체
            shutil.copy2(customer_logo, system_logo)
            print(f"[LOGO] {system_logo} ← {customer_logo}")
        else:
            print(f"[WARNING] 고객 로고 없음: {customer_logo}")
    
    print(f"고객사 '{customer_id}' 로고 적용 완료!")
'''
    
    with open('logo_replacement_demo.txt', 'w', encoding='utf-8') as f:
        f.write(demo_code)
    
    print("로고 교체 데모 코드 생성: logo_replacement_demo.txt")

def show_logo_integration():
    """HTML에서 로고 사용 방법"""
    
    html_examples = '''
<!-- HTML에서 로고 사용 예시 -->

1. 메인 대시보드 상단 로고:
<div class="header-logo">
    <img src="static/images/logo.png" alt="회사 로고" style="height: 40px;">
</div>

2. 사이드바 브랜드 로고:
<div class="sidebar-brand">
    <img src="static/images/logo.png" alt="브랜드" style="width: 200px;">
    <h3>{{COMPANY_NAME}}</h3>
</div>

3. 로그인 페이지 로고:
<div class="login-logo">
    <img src="assets/login_logo.png" alt="로그인" style="width: 300px;">
</div>

4. 파비콘 (HTML head):
<link rel="icon" type="image/x-icon" href="static/favicon.ico">

CSS에서 로고 스타일링:
.header-logo img {
    max-height: 50px;
    width: auto;
}

.sidebar-brand img {
    max-width: 100%;
    height: auto;
    margin-bottom: 10px;
}
'''
    
    with open('logo_html_examples.txt', 'w', encoding='utf-8') as f:
        f.write(html_examples)
    
    print("HTML 로고 사용 예시 생성: logo_html_examples.txt")

def main():
    print("=" * 50)
    print("로고 이미지 교체 시스템 데모")  
    print("=" * 50)
    
    # 1. 폴더 구조 생성
    setup_logo_system()
    print()
    
    # 2. 설정 파일 생성
    create_logo_config()
    print()
    
    # 3. 데모 코드 생성
    demo_logo_replacement()
    print()
    
    # 4. HTML 사용 예시
    show_logo_integration()
    print()
    
    print("=" * 50)
    print("로고 시스템 준비 완료!")
    print("=" * 50)
    print()
    print("다음 단계:")
    print("1. assets/logos/customers/testfood/ 폴더에 로고 이미지 넣기")
    print("   - main_logo.png (200x60px)")
    print("   - favicon.ico (32x32px)")  
    print("   - login_logo.png (300x100px)")
    print()
    print("2. 로고 교체 스크립트 실행")
    print("3. 브라우저에서 확인")

if __name__ == "__main__":
    main()