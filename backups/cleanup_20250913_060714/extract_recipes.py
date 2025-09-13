"""
Extract and parse recipes from the fetched data
"""
import json
import re
from decimal import Decimal

def extract_json_from_file(file_path):
    """Extract JSON from file containing PHP errors"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the JSON part (starts with {"result":)
    json_start = content.find('{"result":')
    if json_start == -1:
        print("JSON data not found")
        return None
    
    json_str = content[json_start:]
    
    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return None

def parse_recipe_ingredients(recipe_text):
    """Parse recipe ingredients from text format"""
    ingredients = []
    
    if not recipe_text:
        return ingredients
    
    # Clean HTML tags
    recipe_text = re.sub(r'<br>', '\n', recipe_text)
    recipe_text = re.sub(r'<[^>]+>', '', recipe_text)
    
    # Split by comma for individual ingredients
    parts = recipe_text.split(',')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # Try to extract ingredient name, quantity and unit
        # Format: "ingredient_name(details) UNIT quantity UNIT"
        # Example: "세척당근(중국산/상급/200~300g/포베이)KG 0.01KG"
        
        # Find the last occurrence of a number followed by unit
        match = re.search(r'(.+?)([A-Z]+)\s*([\d.]+)\s*([A-Z]+)?', part)
        if match:
            name_with_details = match.group(1).strip()
            first_unit = match.group(2)
            quantity = match.group(3)
            second_unit = match.group(4) if match.group(4) else first_unit
            
            # Extract name without parentheses content
            name_match = re.match(r'^([^(]+)', name_with_details)
            ingredient_name = name_match.group(1).strip() if name_match else name_with_details
            
            try:
                qty = float(quantity)
            except ValueError:
                # Handle malformed quantities
                qty = 0.0
            
            ingredients.append({
                'name': ingredient_name,
                'quantity': qty,
                'unit': second_unit,
                'full_text': part
            })
    
    return ingredients

def main():
    """Extract and process recipes"""
    print("=" * 50)
    print("레시피 데이터 추출 및 분석")
    print("=" * 50)
    
    # Extract JSON from raw file
    data = extract_json_from_file('all_recipes_raw.txt')
    
    if not data or not data.get('result'):
        print("[ERROR] 데이터 추출 실패")
        return
    
    result = data.get('result', {})
    recipes = result.get('recipeList', [])
    total_count = result.get('totalCount', 0)
    
    print(f"\n[정보] 전체 레시피: {total_count}개")
    print(f"[정보] 추출된 레시피: {len(recipes)}개")
    
    # Save clean JSON
    with open('recipes_clean.json', 'w', encoding='utf-8') as f:
        json.dump(recipes, f, ensure_ascii=False, indent=2)
    print("\n[OK] recipes_clean.json 파일 저장 완료")
    
    # Analyze first few recipes
    print("\n[샘플 레시피 분석]")
    for i, recipe in enumerate(recipes[:5], 1):
        print(f"\n{i}. {recipe.get('ri_name', 'N/A')}")
        print(f"   - 카테고리: {recipe.get('ctg_name', 'N/A')}")
        print(f"   - 업장수: {recipe.get('bp_cnt', 0)}")
        
        # Parse ingredients
        ingredients = parse_recipe_ingredients(recipe.get('ri_standard_cooking_method', ''))
        if ingredients:
            print(f"   - 식재료: {len(ingredients)}개")
            for ing in ingredients[:3]:  # Show first 3
                print(f"     * {ing['name']}: {ing['quantity']}{ing['unit']}")
    
    # Category statistics
    print("\n[카테고리별 통계]")
    categories = {}
    for recipe in recipes:
        ctg = recipe.get('ctg_name', 'Unknown')
        categories[ctg] = categories.get(ctg, 0) + 1
    
    for ctg, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {ctg}: {count}개")
    
    # Prepare for database import
    print("\n[데이터베이스 임포트 준비]")
    
    import_data = []
    for recipe in recipes:
        ingredients = parse_recipe_ingredients(recipe.get('ri_standard_cooking_method', ''))
        
        import_data.append({
            'id': recipe.get('ri_seq'),
            'name': recipe.get('ri_name'),
            'category': recipe.get('ctg_name'),
            'business_count': int(recipe.get('bp_cnt', 0)),
            'ingredients': ingredients,
            'raw_text': recipe.get('ri_standard_cooking_method', '')
        })
    
    # Save import-ready data
    with open('recipes_for_import.json', 'w', encoding='utf-8') as f:
        json.dump(import_data, f, ensure_ascii=False, indent=2)
    
    print(f"[OK] recipes_for_import.json 파일 생성 완료")
    print(f"     - 임포트 가능 레시피: {len(import_data)}개")
    
    return import_data

if __name__ == "__main__":
    main()