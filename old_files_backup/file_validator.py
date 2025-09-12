import pandas as pd
import re
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from decimal import Decimal
from sqlalchemy.orm import Session
from models import Supplier, Ingredient, SupplierIngredient

class FileUploadValidator:
    """파일 업로드 사전 검증 클래스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.supplier_mapping = {
            "82_(사조푸디스트)": "사조푸디스트",
            "82_동원홈푸드": "동원홈푸드", 
            "82_영유통": "영유통",
            "82_현대그린푸드": "현대그린푸드",
            "82다함푸드": "CJ제일제당"
        }
    
    def validate_supplier_file(self, file_path: str) -> Dict:
        """공급업체 파일 사전 검증"""
        file_path = Path(file_path)
        
        validation_result = {
            'file_name': file_path.name,
            'file_size_mb': file_path.stat().st_size / (1024 * 1024),
            'valid': False,
            'supplier_name': '',
            'total_rows': 0,
            'valid_rows': 0,
            'duplicate_within_file': 0,
            'duplicate_in_db': 0,
            'expected_imports': 0,
            'warnings': [],
            'errors': [],
            'column_analysis': {},
            'data_quality_issues': [],
            'duplicate_analysis': {}
        }
        
        try:
            # 파일 읽기 시도
            df = pd.read_excel(file_path)
            validation_result['total_rows'] = len(df)
            
            # 공급업체 식별
            supplier_name = self._extract_supplier_name(file_path.name)
            validation_result['supplier_name'] = supplier_name
            
            # 기본 구조 검증
            structure_check = self._validate_file_structure(df)
            if not structure_check['valid']:
                validation_result['errors'].extend(structure_check['errors'])
                return validation_result
            
            # 컬럼 분석
            validation_result['column_analysis'] = self._analyze_columns(df)
            
            # 데이터 품질 분석
            validation_result['data_quality_issues'] = self._analyze_data_quality(df)
            
            # 중복 분석
            duplicate_analysis = self._analyze_duplicates(df, supplier_name)
            validation_result['duplicate_analysis'] = duplicate_analysis
            validation_result['duplicate_within_file'] = duplicate_analysis['within_file_duplicates']
            
            # 데이터베이스 중복 분석
            db_duplicate_analysis = self._analyze_db_duplicates(df, supplier_name)
            validation_result['duplicate_in_db'] = db_duplicate_analysis['existing_count']
            
            # 유효한 데이터 행 수 계산
            valid_df = df.dropna(subset=['식자재명'])
            valid_df = valid_df[valid_df['식자재명'].apply(lambda x: str(x).strip() != '' and str(x).strip() != 'nan')]
            validation_result['valid_rows'] = len(valid_df)
            
            # 예상 임포트 수 계산
            validation_result['expected_imports'] = (
                validation_result['valid_rows'] - 
                validation_result['duplicate_within_file'] - 
                validation_result['duplicate_in_db']
            )
            
            # 경고 및 권장사항 생성
            validation_result['warnings'] = self._generate_warnings(validation_result)
            
            validation_result['valid'] = True
            
        except Exception as e:
            validation_result['errors'].append(f'파일 처리 오류: {str(e)}')
        
        return validation_result
    
    def _validate_file_structure(self, df: pd.DataFrame) -> Dict:
        """파일 구조 검증"""
        errors = []
        
        # 필수 컬럼 확인
        required_columns = ['식자재명']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            errors.append(f"필수 컬럼 누락: {', '.join(missing_columns)}")
        
        # 권장 컬럼 확인
        recommended_columns = ['고유코드', '단위', '입고단가', '판매단가', '원산지']
        missing_recommended = [col for col in recommended_columns if col not in df.columns]
        
        if missing_recommended:
            errors.append(f"권장 컬럼 누락 (데이터 품질에 영향): {', '.join(missing_recommended)}")
        
        # 데이터 행 수 확인
        if len(df) == 0:
            errors.append("데이터가 없습니다")
        elif len(df) > 50000:
            errors.append("파일이 너무 큽니다 (50,000행 초과). 성능에 영향을 줄 수 있습니다.")
        
        return {
            'valid': len([e for e in errors if '누락' in e and '필수' in e]) == 0,
            'errors': errors
        }
    
    def _analyze_columns(self, df: pd.DataFrame) -> Dict:
        """컬럼별 데이터 분석"""
        analysis = {}
        
        for column in df.columns:
            col_analysis = {
                'total_values': len(df),
                'non_null_values': df[column].count(),
                'null_values': df[column].isnull().sum(),
                'unique_values': df[column].nunique(),
                'data_types': str(df[column].dtype)
            }
            
            # 숫자 컬럼 추가 분석
            if column in ['입고단가', '판매단가']:
                numeric_col = pd.to_numeric(df[column], errors='coerce')
                col_analysis.update({
                    'min_value': float(numeric_col.min()) if not numeric_col.isna().all() else None,
                    'max_value': float(numeric_col.max()) if not numeric_col.isna().all() else None,
                    'mean_value': float(numeric_col.mean()) if not numeric_col.isna().all() else None,
                    'zero_values': (numeric_col == 0).sum()
                })
            
            analysis[column] = col_analysis
        
        return analysis
    
    def _analyze_data_quality(self, df: pd.DataFrame) -> List[Dict]:
        """데이터 품질 이슈 분석"""
        issues = []
        
        # 식자재명 품질 검사
        if '식자재명' in df.columns:
            empty_names = df['식자재명'].isnull().sum()
            if empty_names > 0:
                issues.append({
                    'type': 'missing_data',
                    'column': '식자재명',
                    'count': empty_names,
                    'description': f'{empty_names}개 행에 식자재명이 없습니다'
                })
            
            # 이상한 식자재명 패턴 검사
            weird_names = df[df['식자재명'].astype(str).str.len() < 2]
            if len(weird_names) > 0:
                issues.append({
                    'type': 'suspicious_data',
                    'column': '식자재명',
                    'count': len(weird_names),
                    'description': f'{len(weird_names)}개 행에 너무 짧은 식자재명이 있습니다'
                })
        
        # 가격 데이터 품질 검사
        for price_col in ['입고단가', '판매단가']:
            if price_col in df.columns:
                numeric_prices = pd.to_numeric(df[price_col], errors='coerce')
                zero_prices = (numeric_prices == 0).sum()
                negative_prices = (numeric_prices < 0).sum()
                
                if zero_prices > len(df) * 0.5:  # 50% 이상이 0
                    issues.append({
                        'type': 'data_quality',
                        'column': price_col,
                        'count': zero_prices,
                        'description': f'{price_col}의 {zero_prices}개 값이 0입니다'
                    })
                
                if negative_prices > 0:
                    issues.append({
                        'type': 'invalid_data',
                        'column': price_col,
                        'count': negative_prices,
                        'description': f'{price_col}에 {negative_prices}개 음수 값이 있습니다'
                    })
        
        return issues
    
    def _analyze_duplicates(self, df: pd.DataFrame, supplier_name: str) -> Dict:
        """중복 데이터 분석"""
        analysis = {
            'within_file_duplicates': 0,
            'duplicate_ingredients': [],
            'total_duplicate_rows': 0
        }
        
        if '식자재명' not in df.columns:
            return analysis
        
        # 식자재명 기준 중복 분석
        ingredient_counts = df['식자재명'].value_counts()
        duplicated_ingredients = ingredient_counts[ingredient_counts > 1]
        
        analysis['within_file_duplicates'] = len(duplicated_ingredients)
        analysis['total_duplicate_rows'] = (ingredient_counts - 1).sum()
        
        # 중복이 많은 상위 10개
        top_duplicates = []
        for name, count in duplicated_ingredients.head(10).items():
            top_duplicates.append({
                'ingredient_name': name,
                'count': count,
                'duplicate_rows': count - 1
            })
        
        analysis['duplicate_ingredients'] = top_duplicates
        
        # 고유코드 기준 중복도 확인
        if '고유코드' in df.columns:
            code_counts = df['고유코드'].value_counts()
            duplicated_codes = code_counts[code_counts > 1]
            analysis['code_duplicates'] = len(duplicated_codes)
            analysis['code_duplicate_rows'] = (code_counts - 1).sum()
        
        return analysis
    
    def _analyze_db_duplicates(self, df: pd.DataFrame, supplier_name: str) -> Dict:
        """데이터베이스 내 기존 데이터와 중복 분석"""
        analysis = {
            'existing_count': 0,
            'existing_ingredients': []
        }
        
        try:
            # 공급업체 확인
            supplier = self.db.query(Supplier).filter(Supplier.name == supplier_name).first()
            if not supplier:
                return analysis
            
            # 파일의 식자재명들과 DB의 기존 데이터 비교
            file_ingredients = set(df['식자재명'].dropna().astype(str))
            
            existing_ingredients = self.db.query(Ingredient.name).join(
                SupplierIngredient, Ingredient.id == SupplierIngredient.ingredient_id
            ).filter(
                SupplierIngredient.supplier_id == supplier.id
            ).all()
            
            existing_names = set([ing[0] for ing in existing_ingredients])
            
            # 겹치는 식자재명들
            overlapping = file_ingredients.intersection(existing_names)
            analysis['existing_count'] = len(overlapping)
            analysis['existing_ingredients'] = list(overlapping)[:10]  # 상위 10개만
            
        except Exception as e:
            analysis['error'] = str(e)
        
        return analysis
    
    def _generate_warnings(self, validation_result: Dict) -> List[str]:
        """경고 및 권장사항 생성"""
        warnings = []
        
        # 중복 데이터 경고
        if validation_result['duplicate_within_file'] > 0:
            warnings.append(
                f"파일 내에 {validation_result['duplicate_within_file']}개의 중복 식자재명이 "
                f"있습니다. 총 {validation_result['duplicate_analysis']['total_duplicate_rows']}개 행이 "
                f"중복으로 스킵될 예정입니다."
            )
        
        # 데이터베이스 중복 경고
        if validation_result['duplicate_in_db'] > 0:
            warnings.append(
                f"데이터베이스에 이미 {validation_result['duplicate_in_db']}개의 동일한 식자재가 "
                f"등록되어 있습니다. 이들은 업데이트되지 않고 스킵될 예정입니다."
            )
        
        # 임포트 효율성 경고
        import_rate = (validation_result['expected_imports'] / validation_result['valid_rows'] * 100 
                      if validation_result['valid_rows'] > 0 else 0)
        
        if import_rate < 50:
            warnings.append(
                f"예상 임포트율이 {import_rate:.1f}%로 낮습니다. "
                f"중복 데이터를 확인하시기 바랍니다."
            )
        
        # 데이터 품질 경고
        for issue in validation_result['data_quality_issues']:
            if issue['type'] == 'invalid_data':
                warnings.append(f"{issue['description']} - 데이터를 검토하시기 바랍니다.")
        
        return warnings
    
    def _extract_supplier_name(self, filename: str) -> str:
        """파일명에서 공급업체 이름을 추출합니다."""
        for key, supplier_name in self.supplier_mapping.items():
            if key in filename:
                return supplier_name
        return filename.split('.')[0]
    
    def generate_validation_report(self, validation_result: Dict) -> str:
        """검증 리포트 생성"""
        report = []
        report.append("=== 파일 업로드 사전 검증 리포트 ===")
        report.append(f"파일명: {validation_result['file_name']}")
        report.append(f"파일 크기: {validation_result['file_size_mb']:.2f} MB")
        report.append(f"공급업체: {validation_result['supplier_name']}")
        
        if not validation_result['valid']:
            report.append("\n[검증 실패]")
            for error in validation_result['errors']:
                report.append(f"  - {error}")
            return '\n'.join(report)
        
        report.append(f"\n[기본 검증 통과]")
        report.append(f"전체 행수: {validation_result['total_rows']:,}개")
        report.append(f"유효 행수: {validation_result['valid_rows']:,}개")
        report.append(f"예상 임포트: {validation_result['expected_imports']:,}개")
        
        import_rate = (validation_result['expected_imports'] / validation_result['valid_rows'] * 100 
                      if validation_result['valid_rows'] > 0 else 0)
        report.append(f"예상 임포트율: {import_rate:.1f}%")
        
        # 중복 분석 결과
        if validation_result['duplicate_within_file'] > 0:
            report.append(f"\n[파일 내 중복]")
            report.append(f"  중복 식자재명: {validation_result['duplicate_within_file']}개")
            report.append(f"  중복으로 스킵될 행: {validation_result['duplicate_analysis']['total_duplicate_rows']}개")
            
            if validation_result['duplicate_analysis']['duplicate_ingredients']:
                report.append("  중복이 많은 식자재 (상위 5개):")
                for dup in validation_result['duplicate_analysis']['duplicate_ingredients'][:5]:
                    report.append(f"    - {dup['ingredient_name']}: {dup['count']}번")
        
        if validation_result['duplicate_in_db'] > 0:
            report.append(f"\n[데이터베이스 중복]")
            report.append(f"  기존 등록 식자재: {validation_result['duplicate_in_db']}개")
        
        # 경고사항
        if validation_result['warnings']:
            report.append(f"\n[경고사항]")
            for warning in validation_result['warnings']:
                report.append(f"  - {warning}")
        
        # 데이터 품질 이슈
        if validation_result['data_quality_issues']:
            report.append(f"\n[데이터 품질 이슈]")
            for issue in validation_result['data_quality_issues']:
                report.append(f"  - {issue['description']}")
        
        return '\n'.join(report)

def validate_upload_file(db: Session, file_path: str) -> Dict:
    """파일 업로드 검증 실행"""
    validator = FileUploadValidator(db)
    result = validator.validate_supplier_file(file_path)
    return result

if __name__ == "__main__":
    print("파일 업로드 검증 유틸리티 준비 완료")
    print("사용법: from file_validator import validate_upload_file; validate_upload_file(db, 'file_path')")