"""
식단표 작성 API 서버
웹 인터페이스와 연동되는 Flask API
"""

from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
from meal_plan_builder import MealPlanBuilder
from datetime import datetime, date
import json
import os
from enhanced_file_upload import file_processor

app = Flask(__name__)
CORS(app)

# 식단표 빌더 인스턴스
builder = MealPlanBuilder()

@app.route('/')
def index():
    """메인 마스터 레이아웃 페이지"""
    try:
        with open('master_layout.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "마스터 레이아웃 파일을 찾을 수 없습니다.", 404

@app.route('/dashboard')
def dashboard():
    """대시보드 페이지"""
    try:
        with open('dashboard.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "대시보드 파일을 찾을 수 없습니다.", 404

@app.route('/meal-plan')
def meal_plan():
    """식단관리 페이지"""
    try:
        with open('meal_plan_simple.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "식단관리 인터페이스 파일을 찾을 수 없습니다.", 404

@app.route('/weekly')
def weekly_index():
    """주간 식단표 인터페이스 페이지"""
    try:
        with open('weekly_content.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "주간 식단표 인터페이스 파일을 찾을 수 없습니다.", 404

@app.route('/meal-counts')
def meal_counts_index():
    """식수입력 관리 인터페이스 페이지"""
    try:
        with open('meal_counts_content.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "식수입력 관리 인터페이스 파일을 찾을 수 없습니다.", 404

@app.route('/meal-input')
def meal_input_index():
    """BOKSILI 스타일 식수입력 인터페이스"""
    try:
        with open('meal_count_input.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "식수입력 인터페이스 파일을 찾을 수 없습니다.", 404

@app.route('/preprocessing')
def preprocessing_index():
    """전처리지시서 인터페이스"""
    try:
        preprocessing_path = r'C:\Users\master\Documents\카카오톡 받은 파일\본사메뉴관리\preprocessing-instruction.html'
        with open(preprocessing_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "전처리지시서 인터페이스 파일을 찾을 수 없습니다.", 404

@app.route('/cooking')
def cooking_index():
    """조리지시서 인터페이스"""
    try:
        cooking_path = r'C:\Users\master\Documents\카카오톡 받은 파일\본사메뉴관리\cooking-instruction-viewer.html'
        with open(cooking_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "조리지시서 인터페이스 파일을 찾을 수 없습니다.", 404

@app.route('/distribution')
def distribution_index():
    """소분지시서 인터페이스"""
    try:
        distribution_path = r'C:\Users\master\Documents\카카오톡 받은 파일\본사메뉴관리\distribution-instruction-v3.html'
        with open(distribution_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "소분지시서 인터페이스 파일을 찾을 수 없습니다.", 404

@app.route('/supplier-management')
def supplier_management_index():
    """식자재업체관리 인터페이스"""
    try:
        with open('supplier_management.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "식자재업체관리 인터페이스 파일을 찾을 수 없습니다.", 404

@app.route('/business-management')
def business_management_index():
    """업장관리 인터페이스"""
    try:
        with open('business_location_management.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "업장관리 인터페이스 파일을 찾을 수 없습니다.", 404

@app.route('/ordering-system')
def ordering_system_index():
    """발주서 시스템 인터페이스"""
    try:
        with open('ordering_system.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "발주서 시스템 인터페이스 파일을 찾을 수 없습니다.", 404

@app.route('/user-management')
def user_management_index():
    """사원관리 인터페이스"""
    try:
        with open('user_management.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "사원관리 인터페이스 파일을 찾을 수 없습니다.", 404

@app.route('/ingredient-file-upload')
def ingredient_file_upload_index():
    """식자재 파일 등록 인터페이스"""
    try:
        with open('ingredient_upload_content.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "식자재 파일 등록 인터페이스 파일을 찾을 수 없습니다.", 404

@app.route('/ingredient-file-viewer')
def ingredient_file_viewer_index():
    """식자재 파일 내용 조회 인터페이스"""
    try:
        with open('ingredient_file_viewer.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "식자재 파일 내용 조회 인터페이스 파일을 찾을 수 없습니다.", 404

@app.route('/ingredient-selection')
def ingredient_selection_popup():
    """식자재 선택 팝업 인터페이스"""
    try:
        with open('ingredient_selection_popup.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "식자재 선택 팝업 인터페이스 파일을 찾을 수 없습니다.", 404

@app.route('/enhanced_upload_client.js')
def enhanced_upload_client_js():
    """Enhanced Upload Client JavaScript 파일"""
    try:
        with open('enhanced_upload_client.js', 'r', encoding='utf-8') as f:
            content = f.read()
        
        from flask import Response
        return Response(content, mimetype='application/javascript')
    except FileNotFoundError:
        return "JavaScript 파일을 찾을 수 없습니다.", 404

# =================== 개선된 파일 업로드 API ===================

@app.route('/api/upload/start', methods=['POST'])
def api_start_chunked_upload():
    """청크 업로드 시작 API"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        file_size = data.get('file_size')
        total_chunks = data.get('total_chunks')
        
        if not all([filename, file_size, total_chunks]):
            return jsonify({
                'success': False,
                'error': '필수 매개변수가 누락되었습니다: filename, file_size, total_chunks'
            }), 400
        
        result = file_processor.start_chunked_upload(filename, file_size, total_chunks)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'업로드 시작 오류: {str(e)}'
        }), 500

@app.route('/api/upload/chunk', methods=['POST'])
def api_upload_chunk():
    """청크 데이터 업로드 API"""
    try:
        upload_id = request.form.get('upload_id')
        chunk_index = int(request.form.get('chunk_index'))
        
        if 'chunk' not in request.files:
            return jsonify({'success': False, 'error': '청크 데이터가 없습니다'}), 400
        
        chunk_file = request.files['chunk']
        chunk_data = chunk_file.read()
        
        result = file_processor.receive_chunk(upload_id, chunk_index, chunk_data)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'청크 업로드 오류: {str(e)}'
        }), 500

@app.route('/api/upload/complete', methods=['POST'])
def api_complete_upload():
    """업로드 완료 API"""
    try:
        data = request.get_json()
        upload_id = data.get('upload_id')
        
        if not upload_id:
            return jsonify({'success': False, 'error': 'upload_id가 필요합니다'}), 400
        
        result = file_processor.complete_upload(upload_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'업로드 완료 처리 오류: {str(e)}'
        }), 500

@app.route('/api/upload/status/<upload_id>', methods=['GET'])
def api_upload_status(upload_id):
    """업로드 상태 조회 API"""
    try:
        result = file_processor.get_upload_status(upload_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'상태 조회 오류: {str(e)}'
        }), 500

@app.route('/api/upload/validate', methods=['POST'])
def api_validate_file():
    """파일 유효성 검사 API"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        file_size = data.get('file_size')
        
        if not all([filename, file_size]):
            return jsonify({
                'success': False,
                'error': '필수 매개변수가 누락되었습니다: filename, file_size'
            }), 400
        
        validation = file_processor.validate_file(filename, file_size)
        return jsonify(validation)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'검증 오류: {str(e)}'
        }), 500

@app.route('/api/ingredients/list', methods=['GET'])
def api_ingredients_list():
    """등록된 식자재 파일 목록 API"""
    try:
        import sqlite3
        conn = sqlite3.connect('meal_management.db')
        cursor = conn.cursor()
        
        # 업로드별 요약 정보 조회
        cursor.execute('''
            SELECT 
                upload_id,
                COUNT(*) as ingredient_count,
                supplier,
                MIN(created_at) as upload_date,
                MAX(name) as sample_name
            FROM ingredients 
            WHERE upload_id IS NOT NULL
            GROUP BY upload_id, supplier
            ORDER BY MIN(created_at) DESC
            LIMIT 50
        ''')
        
        files = []
        for row in cursor.fetchall():
            upload_id, count, supplier, upload_date, sample_name = row
            files.append({
                'upload_id': upload_id,
                'supplier': supplier or '미지정',
                'ingredient_count': count,
                'upload_date': upload_date,
                'sample_name': sample_name,
                'status': 'completed'  # DB에 있으면 완료된 것
            })
        
        conn.close()
        return jsonify({'success': True, 'files': files})
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'파일 목록 조회 오류: {str(e)}'
        }), 500

@app.route('/api/cleanup', methods=['POST'])
def api_cleanup_uploads():
    """오래된 업로드 정리 API"""
    try:
        removed_count = file_processor.cleanup_old_uploads()
        return jsonify({
            'success': True,
            'message': f'{removed_count}개의 오래된 업로드 세션이 정리되었습니다.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'정리 작업 오류: {str(e)}'
        }), 500

@app.route('/recipes-data')
def get_recipes_data():
    """레시피 데이터 제공 API"""
    try:
        with open('recipes_clean.json', 'r', encoding='utf-8') as f:
            recipes = json.load(f)
        return jsonify(recipes)
    except FileNotFoundError:
        return jsonify({'error': '레시피 데이터를 찾을 수 없습니다.'}), 404
    except Exception as e:
        return jsonify({'error': f'레시피 데이터 로드 오류: {str(e)}'}), 500

@app.route('/api/search_recipes', methods=['POST'])
def api_search_recipes():
    """레시피 검색 API"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '')
        limit = data.get('limit', 20)
        
        recipes = builder.search_recipes(keyword, limit)
        return jsonify(recipes)
        
    except Exception as e:
        print(f"검색 오류: {e}")
        return jsonify([]), 500

@app.route('/api/get_recipe_ingredients/<int:recipe_id>', methods=['GET'])
def api_get_recipe_ingredients(recipe_id):
    """레시피 식재료 정보 API"""
    try:
        ingredients = builder.get_recipe_ingredients(recipe_id)
        return jsonify(ingredients)
        
    except Exception as e:
        print(f"식재료 조회 오류: {e}")
        return jsonify([]), 500

@app.route('/api/create_diet_plan', methods=['POST'])
def api_create_diet_plan():
    """식단표 생성 API"""
    try:
        data = request.get_json()
        
        # 기본 식단표 생성
        category = data.get('category')
        plan_date = datetime.strptime(data.get('date'), '%Y-%m-%d').date()
        description = data.get('description', '')
        persons = data.get('persons', 100)
        menus_data = data.get('menus', {})
        
        # 1. 식단표 생성
        diet_plan_id = builder.create_diet_plan(category, plan_date, description)
        
        # 2. 각 메뉴 타입별로 메뉴와 아이템 추가
        created_menus = {}
        
        for menu_type, recipes in menus_data.items():
            if recipes:  # 레시피가 있는 메뉴만 처리
                # 메뉴 생성
                menu_id = builder.add_menu_to_plan(
                    diet_plan_id, menu_type, persons, target_cost=50000
                )
                created_menus[menu_type] = menu_id
                
                # 각 레시피를 메뉴 아이템으로 추가
                for recipe in recipes:
                    builder.add_menu_item(
                        menu_id, recipe['id'], persons, yield_rate=0.8
                    )
        
        # 3. 생성된 식단표 요약 정보 반환
        summary = builder.get_diet_plan_summary(diet_plan_id)
        
        return jsonify({
            'success': True,
            'diet_plan_id': diet_plan_id,
            'created_menus': created_menus,
            'summary': summary
        })
        
    except Exception as e:
        print(f"식단표 생성 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/calculate_menu_cost/<int:menu_id>', methods=['GET'])
def api_calculate_menu_cost(menu_id):
    """메뉴 비용 계산 API"""
    try:
        cost_info = builder.calculate_menu_cost(menu_id)
        return jsonify(cost_info)
        
    except Exception as e:
        print(f"비용 계산 오류: {e}")
        return jsonify({'total_cost': 0, 'cost_per_person': 0, 'items': []}), 500

@app.route('/api/get_diet_plan_summary/<int:diet_plan_id>', methods=['GET'])
def api_get_diet_plan_summary(diet_plan_id):
    """식단표 요약 정보 API"""
    try:
        summary = builder.get_diet_plan_summary(diet_plan_id)
        return jsonify(summary)
        
    except Exception as e:
        print(f"요약 조회 오류: {e}")
        return jsonify(None), 500

@app.route('/api/recent_diet_plans', methods=['GET'])
def api_recent_diet_plans():
    """최근 식단표 목록 API"""
    try:
        import sqlite3
        
        conn = sqlite3.connect(builder.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                dp.id,
                dp.category,
                dp.date,
                dp.description,
                COUNT(DISTINCT m.id) as menu_count,
                COUNT(mi.id) as item_count
            FROM diet_plans dp
            LEFT JOIN menus m ON dp.id = m.diet_plan_id
            LEFT JOIN menu_items mi ON m.id = mi.menu_id
            GROUP BY dp.id, dp.category, dp.date, dp.description
            ORDER BY dp.created_at DESC
            LIMIT 10
        """)
        
        plans = []
        for row in cursor.fetchall():
            plans.append({
                'id': row[0],
                'category': row[1],
                'date': row[2],
                'description': row[3],
                'menu_count': row[4],
                'item_count': row[5]
            })
        
        conn.close()
        return jsonify(plans)
        
    except Exception as e:
        print(f"최근 식단표 조회 오류: {e}")
        return jsonify([]), 500

@app.route('/api/popular_recipes', methods=['GET'])
def api_popular_recipes():
    """인기 레시피 목록 API (평점 기준)"""
    try:
        recipes = builder.search_recipes("", 50)  # 상위 50개
        return jsonify(recipes)
        
    except Exception as e:
        print(f"인기 레시피 조회 오류: {e}")
        return jsonify([]), 500

@app.route('/api/save_weekly_plan', methods=['POST'])
def api_save_weekly_plan():
    """주간 식단표 저장 API"""
    try:
        data = request.get_json()
        
        category = data.get('category')
        week = data.get('week')  # 예: "2025-W35"
        persons = data.get('persons', 100)
        target_cost = data.get('targetCost', 3000)
        weekly_plan = data.get('weeklyPlan', {})
        
        # 주차에서 날짜 계산 (간단 버전)
        year, week_num = week.split('-W')
        year = int(year)
        week_num = int(week_num)
        
        # 각 날짜별로 식단표 생성
        created_plans = []
        
        for day in range(7):  # 월~일
            # 해당 날짜의 메뉴들 수집
            day_menus = {}
            for meal in ['아침', '점심', '저녁']:
                key = f"{day}-{meal}"
                if key in weekly_plan and weekly_plan[key]:
                    day_menus[meal] = weekly_plan[key]
            
            if day_menus:  # 메뉴가 있는 날만 저장
                # 날짜 계산 (실제로는 더 정확한 계산 필요)
                from datetime import datetime, timedelta
                jan_1 = datetime(year, 1, 1)
                start_of_week = jan_1 + timedelta(weeks=week_num-1, days=-jan_1.weekday())
                plan_date = start_of_week + timedelta(days=day)
                
                # 식단표 생성
                description = f"{category} {plan_date.strftime('%Y-%m-%d')} 식단표"
                diet_plan_id = builder.create_diet_plan(category, plan_date.date(), description)
                
                # 각 식사별 메뉴 추가
                for meal_type, recipes in day_menus.items():
                    menu_id = builder.add_menu_to_plan(diet_plan_id, meal_type, persons, target_cost)
                    
                    for recipe in recipes:
                        builder.add_menu_item(menu_id, recipe['id'], persons, 0.8)
                
                created_plans.append({
                    'date': plan_date.strftime('%Y-%m-%d'),
                    'diet_plan_id': diet_plan_id,
                    'meals': list(day_menus.keys())
                })
        
        return jsonify({
            'success': True,
            'created_plans': created_plans,
            'message': f"{len(created_plans)}일 식단표가 저장되었습니다."
        })
        
    except Exception as e:
        print(f"주간 식단표 저장 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/meal-counts/<year>/<month>', methods=['GET'])
def api_get_meal_counts(year, month):
    """월별 식수 데이터 조회 API"""
    try:
        import sqlite3
        
        conn = sqlite3.connect(builder.db_path)
        cursor = conn.cursor()
        
        # 식수 테이블이 없으면 생성
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meal_counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                time_slot TEXT NOT NULL,
                customer TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 해당 월의 데이터 조회
        cursor.execute('''
            SELECT time_slot, customer, count
            FROM meal_counts
            WHERE year = ? AND month = ?
        ''', (year, month))
        
        data = {}
        for row in cursor.fetchall():
            time_slot, customer, count = row
            if time_slot not in data:
                data[time_slot] = {}
            data[time_slot][customer] = count
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': data,
            'year': year,
            'month': month
        })
        
    except Exception as e:
        print(f"식수 데이터 조회 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/meal-counts/save', methods=['POST'])
def api_save_meal_counts():
    """식수 데이터 저장 API"""
    try:
        import sqlite3
        
        data = request.get_json()
        year = data.get('year')
        month = data.get('month')
        meal_count_data = data.get('data', {})
        
        conn = sqlite3.connect(builder.db_path)
        cursor = conn.cursor()
        
        # 식수 테이블 생성 (존재하지 않을 경우)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meal_counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER NOT NULL,
                month INTEGER NOT NULL,
                time_slot TEXT NOT NULL,
                customer TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 기존 데이터 삭제
        cursor.execute('''
            DELETE FROM meal_counts WHERE year = ? AND month = ?
        ''', (year, month))
        
        # 새 데이터 삽입
        insert_count = 0
        for time_slot, customers in meal_count_data.items():
            for customer, count in customers.items():
                if count and count > 0:  # 0보다 큰 값만 저장
                    cursor.execute('''
                        INSERT INTO meal_counts (year, month, time_slot, customer, count, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                    ''', (year, month, time_slot, customer, count))
                    insert_count += 1
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'{insert_count}개 데이터가 저장되었습니다.',
            'year': year,
            'month': month
        })
        
    except Exception as e:
        print(f"식수 데이터 저장 오류: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# 개발용 라우트
@app.route('/test')
def test():
    """시스템 테스트 페이지"""
    return """
    <h1>식단표 시스템 테스트</h1>
    <ul>
        <li><a href="/api/popular_recipes">인기 레시피 조회</a></li>
        <li><a href="/api/recent_diet_plans">최근 식단표 목록</a></li>
        <li>POST /api/search_recipes - 레시피 검색</li>
        <li>POST /api/create_diet_plan - 식단표 생성</li>
    </ul>
    <hr>
    <h2>레시피 검색 테스트</h2>
    <form action="/api/search_recipes" method="post">
        <input type="text" name="keyword" placeholder="검색어">
        <input type="submit" value="검색">
    </form>
    """

if __name__ == '__main__':
    print("\n" + "="*60)
    print("다함 식단표 작성 시스템 API 서버 시작")
    print("="*60)
    print("[식단표 관리]")
    print(f"   - 메인 식단표: http://localhost:5000")
    print(f"   - 주간 식단표: http://localhost:5000/weekly")
    print(f"   - 식수입력 관리: http://localhost:5000/meal-counts")
    print(f"   - BOKSILI 식수입력: http://localhost:5000/meal-input")
    print()
    print("[작업지시서]")
    print(f"   - 전처리지시서: http://localhost:5000/preprocessing")
    print(f"   - 조리지시서: http://localhost:5000/cooking")
    print(f"   - 소분지시서: http://localhost:5000/distribution")
    print()
    print("[관리 시스템]")
    print(f"   - 식자재업체관리: http://localhost:5000/supplier-management")
    print(f"   - 업장관리: http://localhost:5000/business-management")
    print(f"   - 발주서시스템: http://localhost:5000/ordering-system")
    print(f"   - 사원관리: http://localhost:5000/user-management")
    print()
    print("[식자재 관리]")
    print(f"   - 식자재 파일등록: http://localhost:5000/ingredient-file-upload")
    print(f"   - 식자재 파일조회: http://localhost:5000/ingredient-file-viewer")
    print(f"   - 식자재 선택팝업: http://localhost:5000/ingredient-selection")
    print()
    print(f"[개발 도구] http://localhost:5000/test")
    print("="*60 + "\n")
    
    # DB 연결 테스트
    try:
        recipes = builder.search_recipes("", 1)
        print(f"DB 연결 성공 - 총 레시피 수: {len(recipes) if recipes else '연결 실패'}")
    except Exception as e:
        print(f"DB 연결 오류: {e}")
    
    print()
    app.run(host='0.0.0.0', port=5000, debug=True)