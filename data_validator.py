import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from decimal import Decimal
from sqlalchemy.orm import Session
from models import Supplier, Ingredient, SupplierIngredient

class DataValidator:
    """데이터 임포트 검증 및 오류 리포팅 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.validation_report = {
            'files_processed': 0,
            'total_rows_processed': 0,
            'successful_imports': 0,
            'failed_imports': 0,
            'duplicate_skips': 0,
            'validation_errors': [],
            'file_reports': {}
        }
    
    def validate_and_import_supplier_data(self, file_path: str) -> Dict:
        """공급업체 데이터 검증 및 임포트"""
        file_path = Path(file_path)
        file_report = {
            'file_name': file_path.name,
            'total_rows': 0,
            'valid_rows': 0,
            'imported_rows': 0,
            'duplicate_rows': 0,
            'error_rows': 0,
            'errors': []
        }
        
        try:
            df = pd.read_excel(file_path)
            file_report['total_rows'] = len(df)
            
            # 기본 검증
            validation_result = self._validate_file_structure(df, file_path.name)
            if not validation_result['valid']:
                file_report['errors'].extend(validation_result['errors'])
                return file_report
            
            # 공급업체 확인
            supplier_name = self._extract_supplier_name(file_path.name)
            supplier = self._get_or_create_supplier(supplier_name)
            
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
            
            # 데이터 정리
            df = df.dropna(subset=['식자재명'])
            df = df.fillna('')
            file_report['valid_rows'] = len(df)
            
            # 각 행 처리
            for idx, row in df.iterrows():
                row_result = self._process_supplier_row(row, supplier.id, idx + 1)
                
                if row_result['success']:
                    if row_result['imported']:
                        file_report['imported_rows'] += 1
                    else:
                        file_report['duplicate_rows'] += 1
                else:
                    file_report['error_rows'] += 1
                    file_report['errors'].append({
                        'row': idx + 1,
                        'ingredient_name': str(row.get('식자재명', '')),
                        'error': row_result['error']
                    })
            
            self.db.commit()
            print(f"  완료: {supplier_name}에서 {file_report['imported_rows']}개 항목 임포트")
            print(f"  중복: {file_report['duplicate_rows']}개, 오류: {file_report['error_rows']}개")
            
        except Exception as e:
            file_report['errors'].append({
                'row': 0,
                'ingredient_name': '',
                'error': f'파일 처리 오류: {str(e)}'
            })
            self.db.rollback()
        
        self.validation_report['file_reports'][file_path.name] = file_report
        self.validation_report['files_processed'] += 1
        self.validation_report['total_rows_processed'] += file_report['total_rows']
        self.validation_report['successful_imports'] += file_report['imported_rows']
        self.validation_report['failed_imports'] += file_report['error_rows']
        self.validation_report['duplicate_skips'] += file_report['duplicate_rows']
        
        return file_report
    
    def _validate_file_structure(self, df: pd.DataFrame, filename: str) -> Dict:
        """파일 구조 검증"""
        errors = []
        
        # 필수 컬럼 확인
        required_columns = ['식자재명']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            errors.append(f"필수 컬럼 누락: {', '.join(missing_columns)}")
        
        # 데이터 행 수 확인
        if len(df) == 0:
            errors.append("데이터가 없습니다")
        
        # 식자재명 컬럼의 유효성 확인
        if '식자재명' in df.columns:
            valid_names = df['식자재명'].dropna()
            if len(valid_names) == 0:
                errors.append("유효한 식자재명이 없습니다")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _process_supplier_row(self, row, supplier_id: int, row_num: int) -> Dict:
        """공급업체 데이터 행 처리"""
        try:
            ingredient_name = str(row.get('식자재명', '')).strip()
            if not ingredient_name or ingredient_name == 'nan':
                return {
                    'success': False,
                    'imported': False,
                    'error': '식자재명이 비어있음'
                }
            
            # 식재료 생성 또는 조회
            ingredient = self._get_or_create_ingredient(
                name=ingredient_name,
                base_unit=str(row.get('단위', 'kg')).strip() or 'kg',
                supplier_id=supplier_id
            )
            
            # 중복 체크
            existing = self.db.query(SupplierIngredient).filter(
                SupplierIngredient.supplier_id == supplier_id,
                SupplierIngredient.ingredient_id == ingredient.id
            ).first()
            
            if existing:
                return {
                    'success': True,
                    'imported': False,
                    'error': None
                }
            
            # 공급업체-식재료 관계 생성
            supplier_ingredient = SupplierIngredient(
                supplier_id=supplier_id,
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
            
            self.db.add(supplier_ingredient)
            
            return {
                'success': True,
                'imported': True,
                'error': None
            }
            
        except Exception as e:
            return {
                'success': False,
                'imported': False,
                'error': f'처리 오류: {str(e)}'
            }
    
    def _extract_supplier_name(self, filename: str) -> str:
        """파일명에서 공급업체 이름을 추출합니다."""
        supplier_mapping = {
            "82_(사조푸디스트)": "사조푸디스트",
            "82_동원홈푸드": "동원홈푸드", 
            "82_영유통": "영유통",
            "82_현대그린푸드": "현대그린푸드",
            "82다함푸드": "CJ제일제당"
        }
        
        for key, supplier_name in supplier_mapping.items():
            if key in filename:
                return supplier_name
        return filename.split('.')[0]
    
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
    
    def generate_report(self) -> str:
        """검증 리포트 생성"""
        report = []
        report.append("=== 데이터 검증 리포트 ===")
        report.append(f"처리된 파일: {self.validation_report['files_processed']}개")
        report.append(f"전체 행수: {self.validation_report['total_rows_processed']:,}개")
        report.append(f"성공 임포트: {self.validation_report['successful_imports']:,}개")
        report.append(f"중복 건너뜀: {self.validation_report['duplicate_skips']:,}개")
        report.append(f"오류 발생: {self.validation_report['failed_imports']:,}개")
        
        success_rate = (self.validation_report['successful_imports'] / 
                       self.validation_report['total_rows_processed'] * 100 
                       if self.validation_report['total_rows_processed'] > 0 else 0)
        report.append(f"성공률: {success_rate:.1f}%")
        
        report.append("\n=== 파일별 상세 ===")
        for filename, file_report in self.validation_report['file_reports'].items():
            report.append(f"\n파일: {filename}")
            report.append(f"  전체: {file_report['total_rows']:,}개")
            report.append(f"  유효: {file_report['valid_rows']:,}개")
            report.append(f"  임포트: {file_report['imported_rows']:,}개")
            report.append(f"  중복: {file_report['duplicate_rows']:,}개")
            report.append(f"  오류: {file_report['error_rows']:,}개")
            
            if file_report['errors']:
                report.append("  오류 내용:")
                for error in file_report['errors'][:5]:  # 처음 5개만 표시
                    if error['row'] == 0:
                        report.append(f"    {error['error']}")
                    else:
                        report.append(f"    행 {error['row']}: {error['ingredient_name']} - {error['error']}")
                
                if len(file_report['errors']) > 5:
                    report.append(f"    ... 및 {len(file_report['errors']) - 5}개 추가 오류")
        
        return '\n'.join(report)

def run_validated_import(db: Session):
    """검증 기능이 있는 임포트 실행"""
    validator = DataValidator(db)
    
    print("다함식단관리 - 검증 기능 포함 데이터 임포트 시작")
    print("=" * 50)
    
    upload_dir = Path("sample data/upload")
    
    for file_path in upload_dir.glob("*.xls*"):
        if file_path.name != "food_sample.xls":
            print(f"\n처리 중: {file_path.name}")
            file_report = validator.validate_and_import_supplier_data(str(file_path))
    
    print("\n" + validator.generate_report())
    print("\n전체 임포트 프로세스 완료!")

if __name__ == "__main__":
    print("데이터 검증 유틸리티 준비 완료")
    print("사용법: from data_validator import run_validated_import; run_validated_import(db)")