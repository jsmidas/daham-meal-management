"""
다함식단관리 시스템 테스트 스크립트
직접 실행: python test_system.py
"""

import json
from urllib.request import urlopen, Request
from urllib.error import URLError

BASE_URL = "http://127.0.0.1:8000"

def test_api_connection():
    """API 연결 테스트"""
    try:
        response = urlopen(f"{BASE_URL}/")
        data = json.loads(response.read().decode())
        print("[OK] API 연결 성공!")
        print(f"   메시지: {data.get('message', '')}")
        return True
    except URLError:
        print("[ERROR] API 서버가 실행되지 않았습니다.")
        print("   먼저 다음 명령을 실행하세요:")
        print("   python -m uvicorn main:app --host 127.0.0.1 --port 8000")
        return False

def test_suppliers():
    """공급업체 조회 테스트"""
    try:
        response = urlopen(f"{BASE_URL}/suppliers")
        suppliers = json.loads(response.read().decode())
        print(f"\n[공급업체] 등록된 공급업체: {len(suppliers)}개")
        for supplier in suppliers[:3]:  # 처음 3개만 표시
            print(f"   - {supplier['name']}")
        return True
    except Exception as e:
        print(f"[ERROR] 공급업체 조회 실패: {e}")
        return False

def test_calculation():
    """수량 계산 테스트"""
    try:
        # 테스트 데이터
        data = {
            "menu_item_id": 1,
            "target_num_persons": 120,
            "yield_rate": 0.75
        }
        
        # POST 요청 생성
        req = Request(
            f"{BASE_URL}/calculate-requirements",
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        
        response = urlopen(req)
        result = json.loads(response.read().decode())
        
        print(f"\n[수량계산] 수량 계산 테스트:")
        print(f"   메뉴: {result.get('menu_item_name', 'N/A')}")
        print(f"   대상 인원: {result.get('portion_num_persons', 0)}명")
        print(f"   수율: {float(result.get('yield_rate', 0))*100:.0f}%")
        
        if 'ingredients' in result and result['ingredients']:
            ing = result['ingredients'][0]
            print(f"\n   필요 식재료:")
            print(f"   - {ing['ingredient_name']}: {ing['required_quantity']}{ing['unit']}")
            print(f"   - 주문량: {ing['order_quantity']}{ing['unit']}")
            print(f"   - 비용: {ing['total_cost']:,.0f}원")
        
        print(f"\n   총 비용: {float(result.get('total_cost', 0)):,.0f}원")
        print(f"   1인당: {float(result.get('cost_per_person', 0)):,.0f}원")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 수량 계산 테스트 실패: {e}")
        return False

def test_database_stats():
    """데이터베이스 통계 확인"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from models import Base, Supplier, SupplierIngredient, DietPlan, Menu, MenuItem, Recipe
    
    engine = create_engine('sqlite:///daham_meal.db', echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        suppliers = db.query(Supplier).count()
        products = db.query(SupplierIngredient).count()
        priced_products = db.query(SupplierIngredient).filter(
            SupplierIngredient.unit_price > 0
        ).count()
        diet_plans = db.query(DietPlan).count()
        menus = db.query(Menu).count()
        menu_items = db.query(MenuItem).count()
        recipes = db.query(Recipe).count()
        
        print("\n[데이터베이스] 현황:")
        print(f"   공급업체: {suppliers}개")
        print(f"   상품: {products:,}개")
        print(f"   가격정보: {priced_products:,}개 ({priced_products/products*100:.1f}%)")
        print(f"   식단표: {diet_plans}개")
        print(f"   메뉴: {menus}개")
        print(f"   메뉴항목: {menu_items}개")
        print(f"   레시피: {recipes}개")
        
    finally:
        db.close()

def main():
    """전체 시스템 테스트"""
    print("=" * 50)
    print("다함식단관리 시스템 테스트")
    print("=" * 50)
    
    # API 연결 테스트
    if not test_api_connection():
        return
    
    # 각 기능 테스트
    test_suppliers()
    test_calculation()
    test_database_stats()
    
    print("\n" + "=" * 50)
    print("[완료] 모든 테스트 완료!")
    print("\nSwagger UI 접속:")
    print("   http://127.0.0.1:8000/docs")
    print("=" * 50)

if __name__ == "__main__":
    main()