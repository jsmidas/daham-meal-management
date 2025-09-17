"""
데이터베이스 레시피 직접 검색 API - 재료 포함 버전
"""
import sqlite3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class DBRecipeHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/db_recipes':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                # 데이터베이스에서 모든 레시피 가져오기
                conn = sqlite3.connect('daham_meal.db')
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT id, recipe_code, recipe_name, category, total_cost,
                           cooking_note, image_path, image_thumbnail, created_at
                    FROM menu_recipes
                    WHERE is_active = 1
                    ORDER BY id DESC
                """)

                recipes = []
                for row in cursor.fetchall():
                    recipe_id = row[0]

                    # 재료 정보 가져오기
                    cursor.execute("""
                        SELECT ingredient_name, specification, quantity, amount,
                               ingredient_code, unit, delivery_days, selling_price, supplier_name
                        FROM menu_recipe_ingredients
                        WHERE recipe_id = ?
                    """, (recipe_id,))

                    ingredients = []
                    for ing in cursor.fetchall():
                        ingredients.append({
                            'name': ing[0],
                            'specification': ing[1],
                            'quantity': ing[2],
                            'amount': ing[3],
                            'code': ing[4] if len(ing) > 4 else '',
                            'unit': ing[5] if len(ing) > 5 else '',
                            'delivery_days': ing[6] if len(ing) > 6 else 0,
                            'price': ing[7] if len(ing) > 7 else 0,
                            'supplier': ing[8] if len(ing) > 8 else ''
                        })

                    recipes.append({
                        'id': recipe_id + 100000,  # DB ID 구분을 위해
                        'recipe_code': row[1],
                        'name': row[2],
                        'category': row[3] or '기타',
                        'total_cost': row[4] or 0,
                        'cooking_note': row[5],
                        'image_path': row[6],
                        'thumbnail': row[7],
                        'created_at': row[8],
                        'ingredients': ingredients,  # 재료 정보 추가
                        'is_new': True,  # DB 레시피 표시
                        'source': 'DB'
                    })

                conn.close()

                # 응답
                response = {
                    'success': True,
                    'data': recipes,
                    'count': len(recipes)
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))

                print(f"DB 레시피 {len(recipes)}개 반환")
                for recipe in recipes:
                    print(f"  - {recipe['name']}: 재료 {len(recipe['ingredients'])}개")

            except Exception as e:
                print(f"Error: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {'success': False, 'error': str(e)}
                self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))

        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        # 로그 간소화
        return

if __name__ == '__main__':
    port = 8012
    server = HTTPServer(('127.0.0.1', port), DBRecipeHandler)
    print(f"DB Recipe API (재료 포함 버전) running on port {port}")
    print(f"Test with: http://127.0.0.1:{port}/api/db_recipes")
    server.serve_forever()