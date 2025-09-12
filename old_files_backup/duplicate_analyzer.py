import pandas as pd
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from models import Supplier, Ingredient, SupplierIngredient

class DuplicateAnalyzer:
    """중복 데이터 분석 도구"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_database_duplicates(self) -> Dict:
        """데이터베이스 내 중복 분석"""
        print("=== 데이터베이스 중복 분석 ===")
        
        # 1. 식재료명 기준 중복 분석
        ingredient_duplicates = self.db.query(
            Ingredient.name, 
            func.count(Ingredient.id).label('count')
        ).group_by(Ingredient.name).having(func.count(Ingredient.id) > 1).all()
        
        # 2. 공급업체별 동일 식재료 중복
        supplier_duplicates = self.db.query(
            SupplierIngredient.supplier_id,
            SupplierIngredient.ingredient_id,
            func.count(SupplierIngredient.id).label('count')
        ).group_by(
            SupplierIngredient.supplier_id, 
            SupplierIngredient.ingredient_id
        ).having(func.count(SupplierIngredient.id) > 1).all()
        
        # 3. 고유코드 중복
        code_duplicates = self.db.query(
            SupplierIngredient.ingredient_code,
            func.count(SupplierIngredient.id).label('count')
        ).filter(
            SupplierIngredient.ingredient_code != '',
            SupplierIngredient.ingredient_code.isnot(None)
        ).group_by(SupplierIngredient.ingredient_code).having(
            func.count(SupplierIngredient.id) > 1
        ).all()
        
        result = {
            'ingredient_name_duplicates': len(ingredient_duplicates),
            'supplier_ingredient_duplicates': len(supplier_duplicates),
            'ingredient_code_duplicates': len(code_duplicates),
            'details': {
                'ingredient_names': ingredient_duplicates,
                'supplier_relations': supplier_duplicates,
                'ingredient_codes': code_duplicates
            }
        }
        
        print(f"식재료명 중복: {len(ingredient_duplicates)}개")
        print(f"공급업체-식재료 관계 중복: {len(supplier_duplicates)}개") 
        print(f"고유코드 중복: {len(code_duplicates)}개")
        
        return result
    
    def show_ingredient_name_duplicates(self, limit: int = 10) -> List[Dict]:
        """식재료명 중복 상세 보기"""
        duplicates = self.db.query(
            Ingredient.name,
            func.count(Ingredient.id).label('count')
        ).group_by(Ingredient.name).having(
            func.count(Ingredient.id) > 1
        ).order_by(func.count(Ingredient.id).desc()).limit(limit).all()
        
        print(f"\n=== 식재료명 중복 TOP {limit} ===")
        
        duplicate_details = []
        for name, count in duplicates:
            print(f"\n[식재료] {name} ({count}개)")
            
            # 해당 이름의 모든 식재료 조회
            ingredients = self.db.query(Ingredient).filter(Ingredient.name == name).all()
            
            detail = {
                'name': name,
                'count': count,
                'variations': []
            }
            
            for ing in ingredients:
                # 각 식재료의 공급업체 정보
                supplier_info = self.db.query(SupplierIngredient).join(
                    Supplier, SupplierIngredient.supplier_id == Supplier.id
                ).filter(SupplierIngredient.ingredient_id == ing.id).all()
                
                variation = {
                    'ingredient_id': ing.id,
                    'base_unit': ing.base_unit,
                    'suppliers': []
                }
                
                for si in supplier_info:
                    supplier = self.db.query(Supplier).filter(Supplier.id == si.supplier_id).first()
                    variation['suppliers'].append({
                        'supplier_name': supplier.name,
                        'ingredient_code': si.ingredient_code,
                        'unit': si.unit,
                        'unit_price': float(si.unit_price),
                        'selling_price': float(si.selling_price),
                        'origin': si.origin
                    })
                    
                    print(f"  - ID {ing.id}: {supplier.name} | 코드: {si.ingredient_code} | 단위: {si.unit} | 입고가: {si.unit_price}원")
                
                detail['variations'].append(variation)
            
            duplicate_details.append(detail)
        
        return duplicate_details
    
    def show_supplier_duplicates(self, supplier_name: str = None) -> List[Dict]:
        """특정 공급업체의 중복 분석"""
        query = self.db.query(
            SupplierIngredient.supplier_id,
            SupplierIngredient.ingredient_id,
            func.count(SupplierIngredient.id).label('count')
        ).group_by(
            SupplierIngredient.supplier_id, 
            SupplierIngredient.ingredient_id
        ).having(func.count(SupplierIngredient.id) > 1)
        
        if supplier_name:
            supplier = self.db.query(Supplier).filter(Supplier.name == supplier_name).first()
            if supplier:
                query = query.filter(SupplierIngredient.supplier_id == supplier.id)
                print(f"\n=== {supplier_name} 중복 분석 ===")
            else:
                print(f"공급업체 '{supplier_name}'를 찾을 수 없습니다.")
                return []
        else:
            print(f"\n=== 전체 공급업체 중복 분석 ===")
        
        duplicates = query.all()
        
        duplicate_details = []
        for supplier_id, ingredient_id, count in duplicates:
            supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
            ingredient = self.db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
            
            print(f"\n[{supplier.name}] {ingredient.name} ({count}개 중복)")
            
            # 중복된 항목들 조회
            items = self.db.query(SupplierIngredient).filter(
                SupplierIngredient.supplier_id == supplier_id,
                SupplierIngredient.ingredient_id == ingredient_id
            ).all()
            
            detail = {
                'supplier_name': supplier.name,
                'ingredient_name': ingredient.name,
                'count': count,
                'duplicates': []
            }
            
            for i, item in enumerate(items, 1):
                print(f"  {i}. 코드: {item.ingredient_code} | 단위: {item.unit} | 입고가: {item.unit_price}원 | 원산지: {item.origin}")
                detail['duplicates'].append({
                    'id': item.id,
                    'ingredient_code': item.ingredient_code,
                    'unit': item.unit,
                    'unit_price': float(item.unit_price),
                    'selling_price': float(item.selling_price),
                    'origin': item.origin,
                    'note': item.note
                })
            
            duplicate_details.append(detail)
        
        print(f"\n총 {len(duplicates)}개 중복 발견")
        return duplicate_details
    
    def show_price_analysis(self) -> Dict:
        """가격 정보 분석"""
        print("\n=== 가격 정보 분석 ===")
        
        total_items = self.db.query(SupplierIngredient).count()
        
        # 가격이 있는 상품
        priced_items = self.db.query(SupplierIngredient).filter(
            SupplierIngredient.unit_price > 0
        ).count()
        
        # 판매가만 있는 상품
        selling_only = self.db.query(SupplierIngredient).filter(
            SupplierIngredient.unit_price == 0,
            SupplierIngredient.selling_price > 0
        ).count()
        
        # 가격 정보 없는 상품
        no_price = self.db.query(SupplierIngredient).filter(
            SupplierIngredient.unit_price == 0,
            SupplierIngredient.selling_price == 0
        ).count()
        
        result = {
            'total_items': total_items,
            'with_unit_price': priced_items,
            'selling_price_only': selling_only,
            'no_price': no_price
        }
        
        print(f"전체 상품: {total_items:,}개")
        print(f"입고단가 있음: {priced_items:,}개 ({priced_items/total_items*100:.1f}%)")
        print(f"판매단가만: {selling_only:,}개 ({selling_only/total_items*100:.1f}%)")
        print(f"가격정보 없음: {no_price:,}개 ({no_price/total_items*100:.1f}%)")
        
        return result
    
    def analyze_file_duplicates(self, file_path: str) -> Dict:
        """파일 내 중복 분석"""
        file_path = Path(file_path)
        
        try:
            df = pd.read_excel(file_path)
            
            print(f"\n=== 파일 내 중복 분석: {file_path.name} ===")
            print(f"전체 행수: {len(df):,}개")
            
            if '식자재명' not in df.columns:
                print("식자재명 컬럼을 찾을 수 없습니다.")
                return {}
            
            # 식자재명 중복 분석
            ingredient_counts = df['식자재명'].value_counts()
            duplicated = ingredient_counts[ingredient_counts > 1]
            
            print(f"유니크한 식자재명: {len(ingredient_counts):,}개")
            print(f"중복된 식자재명: {len(duplicated):,}개")
            print(f"중복으로 인한 추가 행: {(ingredient_counts - 1).sum():,}개")
            
            print(f"\n중복이 많은 식재료 TOP 10:")
            for name, count in duplicated.head(10).items():
                print(f"  {name}: {count}번")
                
                # 해당 식재료의 다른 정보들 확인
                samples = df[df['식자재명'] == name]
                if len(samples) > 1:
                    print("    변형 정보:")
                    for idx, row in samples.head(3).iterrows():  # 처음 3개만
                        code = str(row.get('고유코드', ''))
                        unit = str(row.get('단위', ''))
                        price = str(row.get('입고단가', ''))
                        print(f"      코드:{code} | 단위:{unit} | 가격:{price}")
                    if len(samples) > 3:
                        print(f"      ... 및 {len(samples)-3}개 더")
            
            return {
                'total_rows': len(df),
                'unique_ingredients': len(ingredient_counts),
                'duplicated_ingredients': len(duplicated),
                'duplicate_rows': (ingredient_counts - 1).sum(),
                'top_duplicates': duplicated.head(10).to_dict()
            }
            
        except Exception as e:
            print(f"파일 분석 오류: {str(e)}")
            return {}
    
    def compare_suppliers(self, ingredient_name: str) -> List[Dict]:
        """특정 식재료의 공급업체별 비교"""
        print(f"\n=== '{ingredient_name}' 공급업체 비교 ===")
        
        # 해당 이름의 식재료들 찾기
        ingredients = self.db.query(Ingredient).filter(
            Ingredient.name.like(f"%{ingredient_name}%")
        ).all()
        
        if not ingredients:
            print(f"'{ingredient_name}'를 포함한 식재료를 찾을 수 없습니다.")
            return []
        
        comparisons = []
        for ingredient in ingredients:
            print(f"\n[식재료] {ingredient.name}")
            
            supplier_items = self.db.query(SupplierIngredient).join(
                Supplier, SupplierIngredient.supplier_id == Supplier.id
            ).filter(SupplierIngredient.ingredient_id == ingredient.id).all()
            
            comparison = {
                'ingredient_name': ingredient.name,
                'suppliers': []
            }
            
            for item in supplier_items:
                supplier = self.db.query(Supplier).filter(Supplier.id == item.supplier_id).first()
                
                supplier_info = {
                    'supplier_name': supplier.name,
                    'ingredient_code': item.ingredient_code,
                    'unit': item.unit,
                    'unit_price': float(item.unit_price),
                    'selling_price': float(item.selling_price),
                    'origin': item.origin
                }
                
                comparison['suppliers'].append(supplier_info)
                
                print(f"  [{supplier.name}]")
                print(f"     코드: {item.ingredient_code}")
                print(f"     단위: {item.unit}")
                print(f"     입고가: {item.unit_price:,}원")
                print(f"     판매가: {item.selling_price:,}원")
                print(f"     원산지: {item.origin}")
            
            comparisons.append(comparison)
        
        return comparisons

def analyze_all_duplicates(db: Session):
    """전체 중복 분석 실행"""
    analyzer = DuplicateAnalyzer(db)
    
    # 1. 데이터베이스 전체 중복 분석
    db_duplicates = analyzer.analyze_database_duplicates()
    
    # 2. 식재료명 중복 상세 보기
    analyzer.show_ingredient_name_duplicates(limit=5)
    
    # 3. 가격 정보 분석
    analyzer.show_price_analysis()
    
    return analyzer

if __name__ == "__main__":
    print("중복 데이터 분석 도구 준비 완료")
    print("사용법: from duplicate_analyzer import analyze_all_duplicates; analyze_all_duplicates(db)")