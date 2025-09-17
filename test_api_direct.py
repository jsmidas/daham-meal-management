import requests
import json

# API 엔드포인트 URL
url = "http://127.0.0.1:8010/api/recipe/save"

# 테스트 데이터
data = {
    'recipe_name': '테스트 메뉴',
    'category': '국',
    'cooking_note': '테스트 조리법',
    'ingredients': json.dumps([
        {
            'ingredient_code': 'TEST001',
            'ingredient_name': '테스트 재료',
            'specification': '1kg',
            'unit': 'kg',
            'delivery_days': 1,
            'selling_price': 10000,
            'quantity': 0.5,
            'amount': 5000,
            'supplier_name': '테스트 업체'
        }
    ])
}

print("=" * 80)
print("레시피 저장 API 테스트")
print("=" * 80)
print(f"URL: {url}")
print(f"데이터: {json.dumps(data, ensure_ascii=False, indent=2)}")
print("-" * 80)

try:
    # POST 요청 전송
    response = requests.post(url, data=data)

    print(f"응답 상태 코드: {response.status_code}")
    print("-" * 80)

    # 응답 내용 출력
    if response.status_code == 200:
        result = response.json()
        print("응답 데이터:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        if result.get('success'):
            print("\n✅ 저장 성공!")
            print(f"레시피 ID: {result.get('recipe_id')}")
        else:
            print("\n❌ 저장 실패!")
            print(f"오류: {result.get('error') or result.get('detail')}")
    else:
        print(f"HTTP 오류: {response.status_code}")
        print("응답 내용:")
        print(response.text)

except Exception as e:
    print(f"요청 실패: {e}")

print("=" * 80)