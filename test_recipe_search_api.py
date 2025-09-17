"""
데이터베이스 기반 레시피 검색 API
"""
import sqlite3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class RecipeSearchHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/api/db_search_recipes':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                keyword = data.get('keyword', '')
                limit = data.get('limit', 100)

                # 데이터베이스 검색
                conn = sqlite3.connect('daham_meal.db')
                cursor = conn.cursor()

                query = """
                    SELECT id, recipe_code, recipe_name, category, total_cost,
                           cooking_note, image_path, image_thumbnail, created_at
                    FROM menu_recipes
                    WHERE recipe_name LIKE ? AND is_active = 1
                    ORDER BY id DESC
                    LIMIT ?
                """

                cursor.execute(query, (f'%{keyword}%', limit))
                rows = cursor.fetchall()

                recipes = []
                for row in rows:
                    recipe = {
                        'id': row[0],
                        'recipe_code': row[1],
                        'name': row[2],
                        'category': row[3],
                        'total_cost': row[4],
                        'cooking_note': row[5],
                        'image_path': row[6],
                        'thumbnail': row[7],
                        'created_at': row[8]
                    }

                    # 재료 정보 가져오기
                    cursor.execute("""
                        SELECT ingredient_name, specification, quantity, amount
                        FROM menu_recipe_ingredients
                        WHERE recipe_id = ?
                    """, (row[0],))

                    ingredients = cursor.fetchall()
                    recipe['ingredients'] = [
                        {
                            'name': ing[0],
                            'specification': ing[1],
                            'quantity': ing[2],
                            'amount': ing[3]
                        } for ing in ingredients
                    ]

                    recipes.append(recipe)

                conn.close()

                # 응답 보내기
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
    port = 8011
    server = HTTPServer(('127.0.0.1', port), RecipeSearchHandler)
    print(f"Recipe search API running on port {port}")
    print(f"Test with: http://127.0.0.1:{port}/api/db_search_recipes")
    server.serve_forever()