"""
bok2.boksili.kr 사이트에서 레시피 데이터를 가져오는 스크립트
"""
import json
import ssl
import urllib.request
import urllib.parse
from http.cookiejar import CookieJar

# SSL 인증서 무시 설정
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

class RecipeFetcher:
    def __init__(self):
        self.base_url = "http://bok2.boksili.kr"
        self.cookie_jar = CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar),
            urllib.request.HTTPSHandler(context=ssl_context)
        )
        self.session_id = None
        
    def login(self, username="admin", password="1234"):
        """로그인"""
        login_data = {
            "userid": username,
            "password": password
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        try:
            # JSON 데이터로 로그인 시도
            req = urllib.request.Request(
                f"{self.base_url}/api/authorize/signIn",
                data=json.dumps(login_data).encode('utf-8'),
                headers=headers
            )
            
            response = self.opener.open(req)
            result = json.loads(response.read().decode('utf-8'))
            
            if result.get('result'):
                self.session_id = result.get('session_id')
                print(f"로그인 성공! 세션 ID: {self.session_id}")
                return True
            else:
                print(f"로그인 실패: {result.get('message', 'Unknown error')}")
                
                # 다른 로그인 방법 시도 - 폼 데이터
                return self.login_form(username, password)
                
        except Exception as e:
            print(f"로그인 오류: {str(e)}")
            return False
    
    def login_form(self, username, password):
        """폼 데이터로 로그인 시도"""
        try:
            # 먼저 로그인 페이지 방문 (쿠키 받기)
            login_page = self.opener.open(f"{self.base_url}/member/signin")
            
            # 폼 데이터로 로그인
            form_data = urllib.parse.urlencode({
                'id': username,
                'password': password
            }).encode('utf-8')
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            req = urllib.request.Request(
                f"{self.base_url}/member/signin_proc",
                data=form_data,
                headers=headers
            )
            
            response = self.opener.open(req)
            result_text = response.read().decode('utf-8')
            
            # 로그인 성공 확인 (리다이렉트나 성공 메시지 확인)
            if 'logout' in result_text.lower() or 'main' in response.geturl():
                print("폼 로그인 성공!")
                return True
            else:
                print("폼 로그인 실패")
                return False
                
        except Exception as e:
            print(f"폼 로그인 오류: {str(e)}")
            return False
    
    def fetch_recipes(self):
        """레시피 목록 가져오기"""
        try:
            # 레시피 관리 페이지 접근
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            # API 엔드포인트 추측
            endpoints = [
                "/api/recipe/list",
                "/api/recipes",
                "/recipe/list",
                "/shop/recipe",
                "/shop/recipe/list"
            ]
            
            for endpoint in endpoints:
                try:
                    req = urllib.request.Request(
                        f"{self.base_url}{endpoint}",
                        headers=headers
                    )
                    
                    response = self.opener.open(req, timeout=5)
                    content = response.read().decode('utf-8')
                    
                    # JSON 응답인지 확인
                    try:
                        data = json.loads(content)
                        print(f"레시피 데이터 발견: {endpoint}")
                        return data
                    except json.JSONDecodeError:
                        # HTML 응답인 경우
                        if 'recipe' in content.lower():
                            print(f"레시피 페이지 발견 (HTML): {endpoint}")
                            return self.parse_html_recipes(content)
                        
                except Exception as e:
                    continue
            
            # 직접 페이지 접근
            print("직접 레시피 페이지 접근 시도...")
            return self.fetch_recipe_page()
            
        except Exception as e:
            print(f"레시피 가져오기 오류: {str(e)}")
            return None
    
    def fetch_recipe_page(self):
        """레시피 관리 페이지 직접 접근"""
        try:
            # 업장 > 레시피 관리 페이지
            req = urllib.request.Request(
                f"{self.base_url}/shop/recipe",
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            response = self.opener.open(req)
            content = response.read().decode('utf-8')
            
            # 간단한 HTML 파싱
            if '레시피' in content:
                print("레시피 페이지 HTML 내용 확인됨")
                
                # JavaScript에서 데이터 추출 시도
                import re
                
                # JSON 데이터 패턴 찾기
                json_pattern = r'var\s+recipes?\s*=\s*(\[.*?\]);'
                matches = re.findall(json_pattern, content, re.DOTALL)
                
                if matches:
                    try:
                        recipes = json.loads(matches[0])
                        print(f"레시피 {len(recipes)}개 발견")
                        return recipes
                    except:
                        pass
                
                # 테이블 데이터 추출
                return self.extract_table_data(content)
            
            return None
            
        except Exception as e:
            print(f"페이지 접근 오류: {str(e)}")
            return None
    
    def extract_table_data(self, html_content):
        """HTML 테이블에서 레시피 데이터 추출"""
        try:
            import re
            
            recipes = []
            
            # 테이블 행 패턴
            row_pattern = r'<tr[^>]*>(.*?)</tr>'
            cell_pattern = r'<td[^>]*>(.*?)</td>'
            
            rows = re.findall(row_pattern, html_content, re.DOTALL)
            
            for row in rows:
                cells = re.findall(cell_pattern, row, re.DOTALL)
                if len(cells) >= 3:  # 최소 3개 컬럼 (번호, 레시피명, 재료 등)
                    # HTML 태그 제거
                    clean_cells = []
                    for cell in cells:
                        clean_text = re.sub(r'<[^>]+>', '', cell).strip()
                        clean_cells.append(clean_text)
                    
                    if clean_cells[1] and not clean_cells[1].isdigit():  # 레시피명이 있는 경우
                        recipe = {
                            'name': clean_cells[1],
                            'ingredients': clean_cells[2] if len(clean_cells) > 2 else '',
                            'raw_data': clean_cells
                        }
                        recipes.append(recipe)
            
            if recipes:
                print(f"테이블에서 {len(recipes)}개 레시피 추출")
                return recipes
            
        except Exception as e:
            print(f"테이블 데이터 추출 오류: {str(e)}")
        
        return None
    
    def parse_html_recipes(self, html_content):
        """HTML에서 레시피 정보 파싱"""
        # 간단한 파싱 로직
        recipes = []
        
        # 여기에 실제 HTML 구조에 맞는 파싱 로직 추가
        
        return recipes

def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("bok2.boksili.kr 레시피 가져오기")
    print("=" * 50)
    
    fetcher = RecipeFetcher()
    
    # 로그인
    print("\n1. 로그인 시도...")
    if fetcher.login():
        # 레시피 가져오기
        print("\n2. 레시피 데이터 가져오기...")
        recipes = fetcher.fetch_recipes()
        
        if recipes:
            print(f"\n3. 결과: {len(recipes)}개 레시피 발견")
            
            # 처음 5개 출력
            for i, recipe in enumerate(recipes[:5], 1):
                if isinstance(recipe, dict):
                    print(f"\n레시피 {i}:")
                    print(f"  이름: {recipe.get('name', 'N/A')}")
                    print(f"  재료: {recipe.get('ingredients', 'N/A')}")
                else:
                    print(f"\n레시피 {i}: {recipe}")
            
            # 파일로 저장
            with open('fetched_recipes.json', 'w', encoding='utf-8') as f:
                json.dump(recipes, f, ensure_ascii=False, indent=2)
            print(f"\n레시피 데이터가 'fetched_recipes.json'에 저장되었습니다.")
            
            return recipes
        else:
            print("\n레시피를 찾을 수 없습니다.")
    else:
        print("\n로그인에 실패했습니다.")
    
    return None

if __name__ == "__main__":
    main()