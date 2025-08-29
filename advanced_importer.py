import pandas as pd
import re
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from decimal import Decimal
from sqlalchemy.orm import Session
from models import Supplier, Ingredient, SupplierIngredient
from data_validator import DataValidator
from file_validator import FileUploadValidator

class AdvancedImporter:
    """고급 데이터 임포터 - 중복 처리 정책 지원"""
    
    def __init__(self, db: Session):
        self.db = db
        self.supplier_mapping = {
            "82_(사조푸디스트)": "사조푸디스트",
            "82_동원홈푸드": "동원홈푸드", 
            "82_영유통": "영유통",
            "82_현대그린푸드": "현대그린푸드",
            "82다함푸드": "CJ제일제당"
        }
        self.import_stats = {
            'total_processed': 0,
            'new_imports': 0,
            'updated': 0,
            'variants_created': 0,
            'skipped_duplicates': 0,
            'errors': 0
        }
    
    def import_with_policy(self, file_path: str, duplicate_policy: str = 'skip_duplicates', 
                          validate_first: bool = True) -> Dict:
        """정책에 따른 데이터 임포트"""
        
        # 사전 검증 실행
        if validate_first:
            validator = FileUploadValidator(self.db)
            validation_result = validator.validate_supplier_file(file_path)
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': '파일 검증 실패',
                    'validation_result': validation_result
                }
            
            print(f"검증 완료: 예상 임포트 {validation_result['expected_imports']:,}개")
        
        file_path = Path(file_path)
        supplier_name = self._extract_supplier_name(file_path.name)
        
        try:
            df = pd.read_excel(file_path)
            supplier = self._get_or_create_supplier(supplier_name)
            
            # 데이터 정리
            df = df.dropna(subset=['식자재명'])
            df = df.fillna('')
            
            self.import_stats = {
                'total_processed': len(df),
                'new_imports': 0,
                'updated': 0,
                'variants_created': 0,
                'skipped_duplicates': 0,
                'errors': 0
            }
            
            print(f"\\n{duplicate_policy} 정책으로 {len(df):,}개 행 처리 중...")
            
            # 배치 처리로 성능 향상
            batch_size = 1000
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                self._process_batch(batch, supplier.id, duplicate_policy)
                
                if (i + batch_size) % 5000 == 0 or i + batch_size >= len(df):
                    processed = min(i + batch_size, len(df))
                    print(f"  진행 상황: {processed:,}/{len(df):,} ({processed/len(df)*100:.1f}%)")
                    self.db.commit()  # 중간 커밋
            
            self.db.commit()
            
            return {
                'success': True,
                'supplier_name': supplier_name,
                'stats': self.import_stats,
                'message': self._generate_success_message()
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'message': f'임포트 실패: {str(e)}',
                'stats': self.import_stats
            }
    
    def _process_batch(self, batch: pd.DataFrame, supplier_id: int, policy: str):
        """배치 단위 처리"""
        for _, row in batch.iterrows():
            try:
                self._process_row(row, supplier_id, policy)
            except Exception as e:
                self.import_stats['errors'] += 1
                print(f"    행 처리 오류: {str(e)}")
    
    def _process_row(self, row, supplier_id: int, policy: str):
        """정책에 따른 행 처리"""
        ingredient_name = str(row.get('식자재명', '')).strip()
        if not ingredient_name or ingredient_name == 'nan':
            return
        
        base_unit = str(row.get('단위', 'kg')).strip() or 'kg'
        
        # 식재료 처리
        ingredient = self._get_or_create_ingredient(ingredient_name, base_unit, supplier_id)
        
        # 기존 공급업체-식재료 관계 확인
        existing = self.db.query(SupplierIngredient).filter(
            SupplierIngredient.supplier_id == supplier_id,
            SupplierIngredient.ingredient_id == ingredient.id
        ).first()
        
        # 정책에 따른 처리
        if policy == 'skip_duplicates':
            if existing:
                self.import_stats['skipped_duplicates'] += 1
                return
            else:
                self._create_new_supplier_ingredient(row, supplier_id, ingredient.id)
                self.import_stats['new_imports'] += 1
        
        elif policy == 'update_existing':
            if existing:
                self._update_supplier_ingredient(existing, row)
                self.import_stats['updated'] += 1
            else:
                self._create_new_supplier_ingredient(row, supplier_id, ingredient.id)
                self.import_stats['new_imports'] += 1
        
        elif policy == 'create_variants':
            # 같은 이름이라도 다른 속성이면 변형으로 생성
            if existing and self._is_different_variant(existing, row):
                variant_name = self._create_variant_name(ingredient_name, row)
                variant_ingredient = self._get_or_create_ingredient(variant_name, base_unit, supplier_id)
                self._create_new_supplier_ingredient(row, supplier_id, variant_ingredient.id)
                self.import_stats['variants_created'] += 1
            elif existing:
                self.import_stats['skipped_duplicates'] += 1
            else:
                self._create_new_supplier_ingredient(row, supplier_id, ingredient.id)
                self.import_stats['new_imports'] += 1
        
        elif policy == 'merge_data':
            if existing:
                self._merge_supplier_ingredient(existing, row)
                self.import_stats['updated'] += 1
            else:
                self._create_new_supplier_ingredient(row, supplier_id, ingredient.id)
                self.import_stats['new_imports'] += 1
    
    def _create_new_supplier_ingredient(self, row, supplier_id: int, ingredient_id: int):
        """새로운 공급업체-식재료 관계 생성"""
        supplier_ingredient = SupplierIngredient(
            supplier_id=supplier_id,
            ingredient_id=ingredient_id,
            ingredient_code=str(row.get('식자재코드', '')).strip(),
            origin=str(row.get('원산지', '')).strip(),
            is_published=self._parse_boolean(row.get('게시여부', True)),
            unit=str(row.get('단위', 'kg')).strip() or 'kg',
            is_tax_free=self._parse_boolean(row.get('면세여부', False)),
            unit_price=self._parse_decimal(row.get('입고단가', 0)),
            selling_price=self._parse_decimal(row.get('판매단가', 0)),
            note=str(row.get('비고', '')).strip()
        )
        self.db.add(supplier_ingredient)
    
    def _update_supplier_ingredient(self, existing: SupplierIngredient, row):
        """기존 공급업체-식재료 정보 업데이트"""
        existing.ingredient_code = str(row.get('식자재코드', existing.ingredient_code)).strip()
        existing.origin = str(row.get('원산지', existing.origin)).strip()
        existing.is_published = self._parse_boolean(row.get('게시여부', existing.is_published))
        existing.unit = str(row.get('단위', existing.unit)).strip() or existing.unit
        existing.is_tax_free = self._parse_boolean(row.get('면세여부', existing.is_tax_free))
        
        # 가격 정보는 0이 아닌 경우만 업데이트
        new_unit_price = self._parse_decimal(row.get('입고단가', 0))
        if new_unit_price > 0:
            existing.unit_price = new_unit_price
        
        new_selling_price = self._parse_decimal(row.get('판매단가', 0))
        if new_selling_price > 0:
            existing.selling_price = new_selling_price
        
        note = str(row.get('비고', '')).strip()
        if note:
            existing.note = note
    
    def _merge_supplier_ingredient(self, existing: SupplierIngredient, row):
        """데이터 병합 (기존 + 새로운 정보)"""
        # 비어있던 필드들을 새 정보로 채움
        if not existing.ingredient_code:
            existing.ingredient_code = str(row.get('식자재코드', '')).strip()
        
        if not existing.origin:
            existing.origin = str(row.get('원산지', '')).strip()
        
        # 가격 정보 업데이트 (더 나은 가격으로)
        new_unit_price = self._parse_decimal(row.get('입고단가', 0))
        if new_unit_price > 0 and (existing.unit_price == 0 or new_unit_price < existing.unit_price):
            existing.unit_price = new_unit_price
        
        new_selling_price = self._parse_decimal(row.get('판매단가', 0))
        if new_selling_price > 0 and (existing.selling_price == 0 or new_selling_price < existing.selling_price):
            existing.selling_price = new_selling_price
        
        # 비고란 병합
        new_note = str(row.get('비고', '')).strip()
        if new_note and new_note not in existing.note:
            existing.note = f"{existing.note}; {new_note}".strip('; ')
    
    def _is_different_variant(self, existing: SupplierIngredient, row) -> bool:
        """변형 상품인지 확인"""
        # 단위, 가격, 포장 정보가 다르면 변형으로 간주
        current_unit = str(row.get('단위', 'kg')).strip()
        current_price = self._parse_decimal(row.get('입고단가', 0))
        current_code = str(row.get('식자재코드', '')).strip()
        
        return (
            current_unit != existing.unit or 
            abs(current_price - existing.unit_price) > Decimal('0.01') or
            (current_code and current_code != existing.ingredient_code)
        )
    
    def _create_variant_name(self, base_name: str, row) -> str:
        """변형 상품명 생성"""
        unit = str(row.get('단위', 'kg')).strip()
        code = str(row.get('식자재코드', '')).strip()
        
        if code:
            return f"{base_name}({code})"
        elif unit != 'kg':
            return f"{base_name}({unit})"
        else:
            return f"{base_name}_변형"
    
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
    
    def _parse_decimal(self, value) -> Decimal:
        """숫자값을 Decimal로 파싱합니다."""
        try:
            if pd.isna(value) or value == '':
                return Decimal('0')
            return Decimal(str(float(value)))
        except:
            return Decimal('0')
    
    def _generate_success_message(self) -> str:
        """성공 메시지 생성"""
        stats = self.import_stats
        total = stats['total_processed']
        
        message = f"임포트 완료: 총 {total:,}개 행 처리\\n"
        message += f"  - 새로 추가: {stats['new_imports']:,}개\\n"
        message += f"  - 업데이트: {stats['updated']:,}개\\n"
        message += f"  - 변형 생성: {stats['variants_created']:,}개\\n"
        message += f"  - 중복 스킵: {stats['skipped_duplicates']:,}개\\n"
        message += f"  - 오류: {stats['errors']:,}개"
        
        return message

def import_all_supplier_files(db: Session, duplicate_policy: str = 'update_existing'):
    """모든 공급업체 파일 고급 임포트"""
    importer = AdvancedImporter(db)
    upload_dir = Path("sample data/upload")
    
    print(f"고급 임포트 시작 - 중복 정책: {duplicate_policy}")
    print("=" * 50)
    
    results = {}
    
    for file_path in upload_dir.glob("*.xls*"):
        if file_path.name != "food_sample.xls":
            print(f"\\n처리 중: {file_path.name}")
            result = importer.import_with_policy(str(file_path), duplicate_policy)
            results[file_path.name] = result
            
            if result['success']:
                print(result['message'])
            else:
                print(f"실패: {result['message']}")
    
    # 전체 요약
    total_new = sum(r['stats']['new_imports'] for r in results.values() if r['success'])
    total_updated = sum(r['stats']['updated'] for r in results.values() if r['success'])
    total_variants = sum(r['stats']['variants_created'] for r in results.values() if r['success'])
    total_skipped = sum(r['stats']['skipped_duplicates'] for r in results.values() if r['success'])
    
    print(f"\\n=== 전체 결과 ===")
    print(f"새로 추가: {total_new:,}개")
    print(f"업데이트: {total_updated:,}개")
    print(f"변형 생성: {total_variants:,}개")
    print(f"중복 스킵: {total_skipped:,}개")
    
    return results

if __name__ == "__main__":
    print("고급 임포터 준비 완료")
    print("사용법: from advanced_importer import import_all_supplier_files; import_all_supplier_files(db, 'update_existing')")