#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고객사별 맞춤 기능 추가 데모
테스트 고객사에 "고급 식자재 검색" 기능 추가
"""

import os

def add_custom_menu_to_sidebar(customer_dir):
    """사이드바에 맞춤 메뉴 추가"""
    
    admin_dashboard_path = os.path.join(customer_dir, 'admin_dashboard.html')
    
    with open(admin_dashboard_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 기존 메뉴 다음에 맞춤 메뉴 추가
    custom_menu_html = '''
                <div class="menu-section">
                    <div class="menu-section-title">🎯 테스트회사 전용</div>
                    
                    <div class="menu-item">
                        <a href="advanced_search.html" class="menu-link">
                            <span class="menu-icon">🔍</span>
                            <span class="menu-text">고급 식자재 검색</span>
                            <span class="menu-badge" style="background: #ff6b6b;">맞춤</span>
                        </a>
                    </div>
                    
                    <div class="menu-item">
                        <a href="#" class="menu-link">
                            <span class="menu-icon">🚨</span>
                            <span class="menu-text">알레르기 관리</span>
                            <span class="menu-badge" style="background: #45b7d1;">전용</span>
                        </a>
                    </div>
                </div>

'''
    
    # 기존 메뉴 섹션들 뒤에 추가
    insertion_point = content.find('</div>\n            </div>')
    
    if insertion_point != -1:
        content = content[:insertion_point] + custom_menu_html + content[insertion_point:]
        
        with open(admin_dashboard_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("[OK] 사이드바에 맞춤 메뉴 추가 완료!")
        return True
    
    return False

def create_custom_feature_page(customer_dir):
    """맞춤 기능 페이지 생성"""
    
    custom_page_content = '''<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>고급 식자재 검색 - 테스트 급식회사 전용시스템</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Malgun Gothic', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        .search-section {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .search-filters {
            display: grid;
            grid-template-columns: 2fr 1fr 1fr 1fr;
            gap: 15px;
            align-items: center;
        }
        input[type="text"] {
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
        }
        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .search-btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
        }
        .results-section {
            background: white;
            border: 2px solid #eee;
            border-radius: 10px;
            min-height: 400px;
            padding: 20px;
        }
        .feature-badge {
            display: inline-block;
            background: #ff6b6b;
            color: white;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }
        .back-btn {
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(255,255,255,0.9);
            border: none;
            padding: 10px 15px;
            border-radius: 8px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <button class="back-btn" onclick="history.back()">← 돌아가기</button>
    
    <div class="container">
        <div class="header">
            <h1>🔍 고급 식자재 검색</h1>
            <p>테스트 급식회사 전용 맞춤 검색 시스템</p>
            <span class="feature-badge">CUSTOM FEATURE</span>
        </div>
        
        <div class="search-section">
            <h3>🎯 맞춤 검색 옵션</h3>
            <div class="search-filters">
                <input type="text" id="keyword" placeholder="식자재명을 입력하세요...">
                
                <div class="checkbox-group">
                    <input type="checkbox" id="allergy-filter">
                    <label for="allergy-filter">알레르기 제외</label>
                </div>
                
                <div class="checkbox-group">
                    <input type="checkbox" id="seasonal-filter">
                    <label for="seasonal-filter">제철 우선</label>
                </div>
                
                <button class="search-btn" onclick="performAdvancedSearch()">
                    🔍 맞춤 검색
                </button>
            </div>
        </div>
        
        <div class="results-section">
            <h3>🎯 검색 결과 (테스트 급식회사 전용 알고리즘)</h3>
            <div id="search-results">
                <p style="text-align: center; color: #666; padding: 50px;">
                    검색어를 입력하고 맞춤 검색을 실행해보세요!<br>
                    <small>이 기능은 테스트 급식회사만을 위한 특별 개발 기능입니다.</small>
                </p>
            </div>
        </div>
    </div>
    
    <script>
        function performAdvancedSearch() {
            const keyword = document.getElementById('keyword').value;
            const allergyFilter = document.getElementById('allergy-filter').checked;
            const seasonalFilter = document.getElementById('seasonal-filter').checked;
            
            const resultsDiv = document.getElementById('search-results');
            resultsDiv.innerHTML = '<p style="text-align: center;">검색 중...</p>';
            
            // 시뮬레이션된 검색 결과
            setTimeout(() => {
                resultsDiv.innerHTML = `
                    <div style="background: #e8f5e8; padding: 15px; border-radius: 8px;">
                        <h4>🎯 "${keyword}" 맞춤 검색 결과</h4>
                        <p><strong>알레르기 필터:</strong> ${allergyFilter ? '적용됨' : '비활성'}</p>
                        <p><strong>제철 필터:</strong> ${seasonalFilter ? '적용됨' : '비활성'}</p>
                        <hr style="margin: 10px 0;">
                        <p>📊 테스트 급식회사 맞춤 추천:</p>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>🥬 유기농 양배추 (A급 공급업체, 15% 할인 가능)</li>
                            <li>🥕 제철 당근 (지역 우선 공급, 신선도 최고)</li>
                            <li>🐟 고등어 (알레르기 주의, 대체재: 연어 추천)</li>
                        </ul>
                        <p style="color: #666; font-size: 12px; margin-top: 10px;">
                            * 이 결과는 테스트 급식회사의 과거 주문 패턴과 선호도를 분석한 맞춤 추천입니다.
                        </p>
                    </div>
                `;
            }, 1000);
        }
    </script>
</body>
</html>'''
    
    custom_page_path = os.path.join(customer_dir, 'advanced_search.html')
    
    with open(custom_page_path, 'w', encoding='utf-8') as f:
        f.write(custom_page_content)
    
    print("[OK] 맞춤 기능 페이지 생성 완료!")

def main():
    """테스트 고객사에 맞춤 기능 추가"""
    
    customer_dir = 'customers/testcompany'
    
    if not os.path.exists(customer_dir):
        print("❌ 테스트 고객사 디렉토리가 없습니다.")
        return
    
    print("테스트 급식회사에 맞춤 기능 추가")
    print("=" * 50)
    
    # 1. 사이드바 메뉴 추가
    if add_custom_menu_to_sidebar(customer_dir):
        print("1. 사이드바 맞춤 메뉴 추가 완료")
    
    # 2. 맞춤 기능 페이지 생성  
    create_custom_feature_page(customer_dir)
    print("2. 맞춤 기능 페이지 생성 완료")
    
    print("=" * 50)
    print("맞춤 기능 추가 완료!")
    print()
    print("확인 방법:")
    print("1. http://127.0.0.1:8001/admin 접속")
    print("2. 사이드바에 '🎯 테스트회사 전용' 섹션 확인")
    print("3. '고급 식자재 검색' 클릭하여 맞춤 페이지 확인")

if __name__ == "__main__":
    main()