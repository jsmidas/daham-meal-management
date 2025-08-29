import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from decimal import Decimal
from sqlalchemy.orm import Session
from models import Supplier, Ingredient, SupplierIngredient, DietPlan, Menu, MenuItem, Recipe, RecipeIngredient
from datetime import datetime, date

class DataImporter:
    """실제 Excel 데이터를 데이터베이스로 임포트하는 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.supplier_mapping = {
            "82_(사조푸디스트)": "사조푸디스트",
            "82_동원홈푸드": "동원홈푸드", 
            "82_영유통": "영유통",
            "82_현대그린푸드": "현대그린푸드",
            "82다함푸드": "CJ제일제당"
        }
    
    def import_supplier_data(self, file_path: str) -> int:
        """공급업체 단가표를 임포트합니다."""
        file_path = Path(file_path)
        
        # 파일명에서 공급업체 이름 추출
        supplier_name = self._extract_supplier_name(file_path.name)
        
        # 공급업체 생성 또는 조회
        supplier = self._get_or_create_supplier(supplier_name)
        
        try:
            df = pd.read_excel(file_path)
            
            # 컬럼명 정규화
            column_mapping = {
                '분류(대분류)': 'category_major',
                '기본소분류(중분류)': 'category_minor', 
                '식자재코드': 'ingredient_code',
                '식자재명': 'ingredient_name',
                '원산지': 'origin',
                '게시여부': 'is_published',
                '단위': 'unit',
                '면세여부': 'is_tax_free',
                '선발주날짜': 'preorder_date',
                '입고단가': 'unit_price',
                '판매단가': 'selling_price',
                '비고': 'note'
            }
            
            # DataFrame 정리
            df = df.dropna(subset=['식자재명'])  # 식자재명이 없는 행 제거
            df = df.fillna('')  # NaN을 빈 문자열로 변경
            
            imported_count = 0
            
            for _, row in df.iterrows():
                try:
                    ingredient_name = str(row.get('식자재명', '')).strip()
                    if not ingredient_name or ingredient_name == 'nan':
                        continue
                    
                    # 식재료 생성 또는 조회
                    ingredient = self._get_or_create_ingredient(
                        name=ingredient_name,
                        base_unit=str(row.get('단위', 'kg')).strip() or 'kg',
                        supplier_id=supplier.id
                    )
                    
                    # 공급업체-식재료 관계 생성
                    supplier_ingredient = SupplierIngredient(
                        supplier_id=supplier.id,
                        ingredient_id=ingredient.id,
                        ingredient_code=str(row.get('식자재코드', '')).strip(),
                        origin=str(row.get('원산지', '')).strip(),
                        is_published=self._parse_boolean(row.get('게시여부', True)),
                        unit=str(row.get('단위', 'kg')).strip() or 'kg',
                        is_tax_free=self._parse_boolean(row.get('면세여부', False)),
                        unit_price=self._parse_decimal(row.get('입고단가', 0)),
                        selling_price=self._parse_decimal(row.get('판매단가', 0)),
                        note=str(row.get('비고', '')).strip()
                    )
                    
                    # 중복 체크
                    existing = self.db.query(SupplierIngredient).filter(
                        SupplierIngredient.supplier_id == supplier.id,
                        SupplierIngredient.ingredient_id == ingredient.id
                    ).first()
                    
                    if not existing:
                        self.db.add(supplier_ingredient)
                        imported_count += 1
                        
                        if imported_count % 1000 == 0:
                            print(f"  진행 상황: {imported_count}개 항목 처리됨...")
                            self.db.commit()  # 중간 커밋
                    
                except Exception as e:
                    print(f"  행 처리 오류: {e}")
                    continue
            
            self.db.commit()
            print(f"  완료: {supplier_name}에서 {imported_count}개 항목 임포트")
            return imported_count
            
        except Exception as e:
            print(f"  파일 처리 오류: {e}")
            self.db.rollback()
            return 0
    
    def import_meal_plan_data(self, file_path: str) -> Dict:
        """식단표 데이터를 임포트합니다."""
        file_path = Path(file_path)
        
        # 파일명에서 정보 추출 (0811_학교.xlsx -> 학교, 2025-08-11)
        date_str, category = self._extract_meal_plan_info(file_path.name)
        plan_date = self._parse_date(date_str)
        
        try:
            df = pd.read_excel(file_path)
            
            # 식단표 생성
            diet_plan = self._get_or_create_diet_plan(category, plan_date)
            
            imported_data = {
                'diet_plan_id': diet_plan.id,
                'menus': [],
                'menu_items': []
            }
            
            # 데이터 파싱 (각 식단표 형식에 맞게 조정)
            current_menu = None
            menu_items_count = 0
            
            for _, row in df.iterrows():
                try:
                    # 첫 번째 컬럼에서 메뉴 타입과 식수 추출
                    first_col = str(row.iloc[0]).strip()
                    
                    if '식수:' in first_col or '(' in first_col:
                        # 메뉴 정보 행 (예: "중식A (식수: 100)")
                        menu_info = self._parse_menu_info(first_col)
                        if menu_info:
                            current_menu = self._create_menu(
                                diet_plan.id, 
                                menu_info['menu_type'], 
                                menu_info['target_num_persons']
                            )
                            imported_data['menus'].append(current_menu.id)
                    
                    elif current_menu and len(row) >= 3:
                        # 메뉴 아이템 행 (메뉴명, 식재료명, 1인량)
                        menu_name = str(row.iloc[0]).strip()
                        ingredient_name = str(row.iloc[1]).strip()
                        quantity_str = str(row.iloc[2]).strip()
                        
                        if menu_name and menu_name != 'nan' and ingredient_name and ingredient_name != 'nan':
                            quantity = self._parse_quantity(quantity_str)
                            if quantity > 0:
                                menu_item = self._create_menu_item_with_ingredient(
                                    current_menu.id,
                                    menu_name,
                                    ingredient_name,
                                    quantity
                                )
                                if menu_item:
                                    imported_data['menu_items'].append(menu_item.id)
                                    menu_items_count += 1
                
                except Exception as e:
                    print(f"  행 처리 오류: {e}")
                    continue
            
            self.db.commit()
            print(f"  완료: {category} 식단표에서 메뉴 {len(imported_data['menus'])}개, 항목 {menu_items_count}개 임포트")
            return imported_data
            
        except Exception as e:
            print(f"  파일 처리 오류: {e}")
            self.db.rollback()
            return {}
    
    def _extract_supplier_name(self, filename: str) -> str:
        """파일명에서 공급업체 이름을 추출합니다."""
        for key, supplier_name in self.supplier_mapping.items():
            if key in filename:
                return supplier_name
        return filename.split('.')[0]  # 확장자 제거
    
    def _get_or_create_supplier(self, name: str) -> Supplier:
        """공급업체를 생성하거나 조회합니다."""
        supplier = self.db.query(Supplier).filter(Supplier.name == name).first()
        if not supplier:
            supplier = Supplier(
                name=name,
                update_frequency="2주"
            )
            self.db.add(supplier)
            self.db.commit()
            self.db.refresh(supplier)
        return supplier
    
    def _get_or_create_ingredient(self, name: str, base_unit: str, supplier_id: int) -> Ingredient:
        """식재료를 생성하거나 조회합니다."""
        ingredient = self.db.query(Ingredient).filter(Ingredient.name == name).first()
        if not ingredient:
            ingredient = Ingredient(
                name=name,
                base_unit=base_unit,
                supplier_id=supplier_id
            )
            self.db.add(ingredient)
            self.db.commit()
            self.db.refresh(ingredient)
        return ingredient
    
    def _parse_boolean(self, value) -> bool:
        """다양한 형태의 불린값을 파싱합니다."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'y', 'yes', '예', '참']
        return bool(value)
    
    def _parse_decimal(self, value) -> Decimal:
        """숫자값을 Decimal로 파싱합니다."""
        try:
            if pd.isna(value) or value == '':
                return Decimal('0')
            return Decimal(str(float(value)))
        except:
            return Decimal('0')
    
    def _extract_meal_plan_info(self, filename: str) -> Tuple[str, str]:
        """파일명에서 날짜와 카테고리를 추출합니다."""
        # 예: "0811_학교.xlsx" -> ("0811", "학교")
        parts = filename.replace('.xlsx', '').split('_')
        if len(parts) >= 2:
            return parts[0], parts[1]
        return "0811", "기타"
    
    def _parse_date(self, date_str: str) -> date:
        """날짜 문자열을 파싱합니다."""
        try:
            # "0811" -> 2025-08-11
            if len(date_str) == 4 and date_str.isdigit():
                month = int(date_str[:2])
                day = int(date_str[2:])
                return date(2025, month, day)
        except:
            pass
        return date(2025, 8, 11)  # 기본값
    
    def _get_or_create_diet_plan(self, category: str, plan_date: date) -> DietPlan:
        """식단표를 생성하거나 조회합니다."""
        diet_plan = self.db.query(DietPlan).filter(
            DietPlan.category == category,
            DietPlan.date == plan_date
        ).first()
        
        if not diet_plan:
            diet_plan = DietPlan(
                category=category,
                date=plan_date,
                description=f"{plan_date} {category} 급식 계획"
            )
            self.db.add(diet_plan)
            self.db.commit()
            self.db.refresh(diet_plan)
        
        return diet_plan
    
    def _parse_menu_info(self, text: str) -> Optional[Dict]:
        """메뉴 정보를 파싱합니다."""
        # "중식A (식수: 100)" 또는 "중식A (식수: 100)" 패턴
        match = re.search(r'([^(]+)\s*\([^:]*:\s*(\d+)\)', text)
        if match:
            return {
                'menu_type': match.group(1).strip(),
                'target_num_persons': int(match.group(2))
            }
        return None
    
    def _create_menu(self, diet_plan_id: int, menu_type: str, target_num_persons: int) -> Menu:
        """메뉴를 생성합니다."""
        menu = Menu(
            diet_plan_id=diet_plan_id,
            menu_type=menu_type,
            target_num_persons=target_num_persons
        )
        self.db.add(menu)
        self.db.commit()
        self.db.refresh(menu)
        return menu
    
    def _parse_quantity(self, quantity_str: str) -> float:
        """수량 문자열을 파싱합니다."""
        try:
            return float(str(quantity_str).replace(',', ''))
        except:
            return 0.0
    
    def _create_menu_item_with_ingredient(self, menu_id: int, menu_name: str, 
                                        ingredient_name: str, quantity: float) -> Optional[MenuItem]:
        """메뉴 아이템과 레시피를 생성합니다."""
        try:
            # 레시피 생성 또는 조회
            recipe = self.db.query(Recipe).filter(Recipe.name == menu_name).first()
            if not recipe:
                recipe = Recipe(name=menu_name)
                self.db.add(recipe)
                self.db.commit()
                self.db.refresh(recipe)
            
            # 메뉴 아이템 생성
            menu_item = MenuItem(
                menu_id=menu_id,
                name=menu_name,
                recipe_id=recipe.id
            )
            self.db.add(menu_item)
            self.db.commit()
            self.db.refresh(menu_item)
            
            # 식재료 찾기
            ingredient = self.db.query(Ingredient).filter(Ingredient.name == ingredient_name).first()
            if ingredient:
                # 중복 확인
                existing_recipe_ingredient = self.db.query(RecipeIngredient).filter(
                    RecipeIngredient.recipe_id == recipe.id,
                    RecipeIngredient.ingredient_id == ingredient.id
                ).first()
                
                if not existing_recipe_ingredient:
                    # 레시피-식재료 관계 생성
                    recipe_ingredient = RecipeIngredient(
                        recipe_id=recipe.id,
                        ingredient_id=ingredient.id,
                        quantity=Decimal(str(quantity)),
                        unit=ingredient.base_unit
                    )
                    self.db.add(recipe_ingredient)
                    self.db.commit()
            
            return menu_item
            
        except Exception as e:
            print(f"  메뉴 아이템 생성 오류: {e}")
            return None

def run_full_import(db: Session):
    """전체 데이터 임포트를 실행합니다."""
    importer = DataImporter(db)
    
    print("다함식단관리 - 실제 데이터 임포트 시작")
    print("=" * 50)
    
    # 1. 공급업체 데이터 임포트
    print("\n공급업체 단가표 데이터 임포트 중...")
    upload_dir = Path("sample data/upload")
    total_imported = 0
    
    for file_path in upload_dir.glob("*.xls*"):
        if file_path.name != "food_sample.xls":  # 샘플 파일 제외
            print(f"처리 중: {file_path.name}")
            count = importer.import_supplier_data(str(file_path))
            total_imported += count
    
    print(f"공급업체 데이터 임포트 완료: 총 {total_imported:,}개 항목")
    
    # 2. 식단표 데이터 임포트  
    print("\n식단표 데이터 임포트 중...")
    meal_plan_dir = Path("sample data/meal plan")
    
    for file_path in meal_plan_dir.glob("*.xlsx"):
        print(f"처리 중: {file_path.name}")
        result = importer.import_meal_plan_data(str(file_path))
    
    print("식단표 데이터 임포트 완료")
    print("\n전체 임포트 프로세스 완료!")

if __name__ == "__main__":
    # 테스트용 - 실제로는 main.py에서 호출
    print("데이터 임포트 유틸리티 준비 완료")
    print("사용법: from data_import import run_full_import; run_full_import(db)")