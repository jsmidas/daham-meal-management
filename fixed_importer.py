import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from decimal import Decimal
from sqlalchemy.orm import Session
from models import Supplier, Ingredient, SupplierIngredient

class FixedImporter:
    """가격 데이터 문제를 수정한 임포터"""
    
    def __init__(self, db: Session):
        self.db = db
        self.supplier_mapping = {
            "82_(사조푸디스트)": "사조푸디스트",
            "82_동원홈푸드": "동원홈푸드", 
            "82_영유통": "영유통",
            "82_현대그린푸드": "현대그린푸드",
            "82다함푸드": "CJ제일제당"
        }
        self.stats = {
            'total_processed': 0,
            'successful_imports': 0,
            'price_fixes': 0,
            'errors': 0
        }
    
    def clean_import_supplier_data(self, file_path: str) -> Dict:
        """가격 정보를 올바르게 파싱하는 임포트"""
        file_path = Path(file_path)
        
        try:
            # 올바른 헤더로 파일 읽기
            df = pd.read_excel(file_path, header=0)
            
            supplier_name = self._extract_supplier_name(file_path.name)
            supplier = self._get_or_create_supplier(supplier_name)
            
            print(f"\\n처리 중: {supplier_name} ({len(df):,}개 행)")
            
            # 기존 데이터 삭제 (중복 방지)
            existing_count = self.db.query(SupplierIngredient).filter(
                SupplierIngredient.supplier_id == supplier.id
            ).count()
            
            if existing_count > 0:
                print(f"  기존 데이터 {existing_count:,}개 삭제 중...")
                self.db.query(SupplierIngredient).filter(
                    SupplierIngredient.supplier_id == supplier.id
                ).delete()
                self.db.commit()
            
            # 데이터 정리
            df = df.dropna(subset=['식자재명'])
            df = df.fillna('')
            
            self.stats = {
                'total_processed': len(df),
                'successful_imports': 0,
                'price_fixes': 0,
                'errors': 0
            }
            
            # 배치 처리
            batch_size = 1000
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                self._process_batch_clean(batch, supplier.id)
                
                if (i + batch_size) % 5000 == 0 or i + batch_size >= len(df):
                    processed = min(i + batch_size, len(df))
                    print(f"    진행: {processed:,}/{len(df):,} ({processed/len(df)*100:.1f}%)")
                    self.db.commit()
            
            self.db.commit()
            
            print(f"  완료: {self.stats['successful_imports']:,}개 임포트")
            print(f"  가격 수정: {self.stats['price_fixes']:,}개")
            print(f"  오류: {self.stats['errors']:,}개")
            
            return {
                'success': True,
                'supplier_name': supplier_name,
                'stats': self.stats
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': str(e),
                'stats': self.stats
            }
    
    def _process_batch_clean(self, batch: pd.DataFrame, supplier_id: int):
        """배치를 올바른 가격 파싱으로 처리"""
        for _, row in batch.iterrows():
            try:
                ingredient_name = str(row.get('식자재명', '')).strip()
                if not ingredient_name or ingredient_name == 'nan':
                    continue
                
                # 식재료 생성/조회
                base_unit = str(row.get('단위', 'kg')).strip() or 'kg'
                ingredient = self._get_or_create_ingredient(ingredient_name, base_unit, supplier_id)
                
                # 가격 정보 올바른 파싱
                unit_price = self._parse_price(row.get('입고단가', 0))
                selling_price = self._parse_price(row.get('판매단가', 0))
                
                # 공급업체-식재료 관계 생성
                supplier_ingredient = SupplierIngredient(
                    supplier_id=supplier_id,
                    ingredient_id=ingredient.id,
                    ingredient_code=str(row.get('식자재코드', '')).strip(),
                    origin=str(row.get('원산지', '')).strip(),
                    is_published=self._parse_boolean(row.get('게시여부', True)),
                    unit=base_unit,
                    is_tax_free=self._parse_boolean(row.get('면세여부', False)),
                    unit_price=unit_price,
                    selling_price=selling_price,
                    note=str(row.get('비고', '')).strip()
                )
                
                self.db.add(supplier_ingredient)
                self.stats['successful_imports'] += 1
                
                if unit_price > 0 or selling_price > 0:
                    self.stats['price_fixes'] += 1
                
            except Exception as e:
                self.stats['errors'] += 1
                print(f"      행 처리 오류: {str(e)}")
    
    def _parse_price(self, value) -> Decimal:
        """가격 데이터를 올바르게 파싱"""
        try:
            if pd.isna(value):
                return Decimal('0')
            
            # 문자열로 변환 후 숫자 추출
            price_str = str(value).strip()
            if not price_str or price_str == 'nan' or price_str == '':
                return Decimal('0')
            
            # 숫자가 아닌 문자 제거 (콤마, 원 등)
            clean_price = re.sub(r'[^\d.]', '', price_str)
            
            if clean_price:
                return Decimal(clean_price)
            else:
                return Decimal('0')
                
        except Exception as e:
            print(f"    가격 파싱 오류: {value} -> {str(e)}")
            return Decimal('0')
    
    def _extract_supplier_name(self, filename: str) -> str:
        """파일명에서 공급업체 이름을 추출합니다."""
        for key, supplier_name in self.supplier_mapping.items():
            if key in filename:
                return supplier_name
        return filename.split('.')[0]
    
    def _get_or_create_supplier(self, name: str) -> Supplier:
        """공급업체를 생성하거나 조회합니다."""
        supplier = self.db.query(Supplier).filter(Supplier.name == name).first()
        if not supplier:
            supplier = Supplier(name=name, update_frequency="2주")
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

def clean_import_all_files(db: Session):
    """모든 공급업체 파일을 중복 제거하고 가격 수정하여 재임포트"""
    importer = FixedImporter(db)
    
    print("=== 중복 제거 및 가격 수정 임포트 ===")
    print()
    
    upload_dir = Path("sample data/upload")
    results = {}
    total_items = 0
    total_priced = 0
    
    for file_path in upload_dir.glob("*.xls*"):
        if file_path.name != "food_sample.xls":
            result = importer.clean_import_supplier_data(str(file_path))
            results[file_path.name] = result
            
            if result['success']:
                total_items += result['stats']['successful_imports']
                total_priced += result['stats']['price_fixes']
    
    print(f"\\n=== 최종 결과 ===")
    print(f"총 임포트: {total_items:,}개")
    print(f"가격 정보 복구: {total_priced:,}개")
    print(f"가격 복구율: {total_priced/total_items*100:.1f}%" if total_items > 0 else "N/A")
    
    return results

if __name__ == "__main__":
    print("수정된 임포터 준비 완료")
    print("사용법: from fixed_importer import clean_import_all_files; clean_import_all_files(db)")