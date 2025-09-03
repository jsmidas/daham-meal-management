"""
협력업체 서비스
- 비즈니스 로직 구현
- 트랜잭션 관리
- 복잡한 조회 및 처리
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError

from app.models import Supplier, CustomerSupplierMapping
from app.core.exceptions import BusinessLogicError, NotFoundError, DuplicateError


class SupplierService:
    """협력업체 서비스 클래스"""
    
    def __init__(self, db: Session):
        """서비스 초기화"""
        self.db = db
    
    def create_supplier(self, supplier_data: Dict[str, Any]) -> Supplier:
        """
        협력업체 생성
        
        Args:
            supplier_data: 협력업체 데이터
            
        Returns:
            생성된 협력업체 객체
            
        Raises:
            DuplicateError: 중복 데이터 존재
            BusinessLogicError: 비즈니스 규칙 위반
        """
        try:
            # 중복 확인
            self._check_duplicate_supplier(
                parent_code=supplier_data.get('parent_code'),
                business_number=supplier_data.get('business_number')
            )
            
            # 객체 생성
            supplier = Supplier(**supplier_data)
            
            # 데이터베이스 저장
            self.db.add(supplier)
            self.db.commit()
            self.db.refresh(supplier)
            
            return supplier
            
        except IntegrityError as e:
            self.db.rollback()
            raise DuplicateError(f"협력업체 생성 실패: 중복 데이터 ({str(e)})")
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicError(f"협력업체 생성 중 오류 발생: {str(e)}")
    
    def get_supplier_by_id(self, supplier_id: int) -> Supplier:
        """
        ID로 협력업체 조회
        
        Args:
            supplier_id: 협력업체 ID
            
        Returns:
            협력업체 객체
            
        Raises:
            NotFoundError: 협력업체 없음
        """
        supplier = self.db.query(Supplier).filter(
            and_(
                Supplier.id == supplier_id,
                Supplier.is_deleted == False
            )
        ).first()
        
        if not supplier:
            raise NotFoundError(f"협력업체를 찾을 수 없습니다 (ID: {supplier_id})")
            
        return supplier
    
    def get_suppliers_list(
        self, 
        page: int = 1, 
        limit: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        company_scale: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        협력업체 목록 조회 (페이지네이션)
        
        Args:
            page: 페이지 번호
            limit: 페이지당 항목 수
            search: 검색어
            is_active: 활성 상태 필터
            company_scale: 회사 규모 필터
            
        Returns:
            페이지네이션된 협력업체 목록
        """
        # 기본 쿼리
        query = self.db.query(Supplier).filter(
            Supplier.is_deleted == False
        )
        
        # 필터 적용
        if search:
            query = query.filter(
                or_(
                    Supplier.name.like(f"%{search}%"),
                    Supplier.parent_code.like(f"%{search}%"),
                    Supplier.business_number.like(f"%{search}%"),
                    Supplier.representative.like(f"%{search}%")
                )
            )
        
        if is_active is not None:
            query = query.filter(Supplier.is_active == is_active)
            
        if company_scale:
            query = query.filter(Supplier.company_scale == company_scale)
        
        # 총 개수 조회
        total_count = query.count()
        total_pages = (total_count + limit - 1) // limit
        
        # 페이지네이션 적용
        offset = (page - 1) * limit
        suppliers = query.order_by(
            Supplier.name,
            Supplier.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return {
            "suppliers": suppliers,
            "pagination": {
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
                "limit": limit,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    
    def update_supplier(
        self, 
        supplier_id: int, 
        update_data: Dict[str, Any]
    ) -> Supplier:
        """
        협력업체 정보 수정
        
        Args:
            supplier_id: 협력업체 ID
            update_data: 수정할 데이터
            
        Returns:
            수정된 협력업체 객체
        """
        try:
            supplier = self.get_supplier_by_id(supplier_id)
            
            # 중복 확인 (다른 협력업체와)
            if 'parent_code' in update_data or 'business_number' in update_data:
                self._check_duplicate_supplier(
                    parent_code=update_data.get('parent_code', supplier.parent_code),
                    business_number=update_data.get('business_number', supplier.business_number),
                    exclude_id=supplier_id
                )
            
            # 데이터 업데이트
            for key, value in update_data.items():
                if hasattr(supplier, key):
                    setattr(supplier, key, value)
            
            self.db.commit()
            self.db.refresh(supplier)
            
            return supplier
            
        except IntegrityError as e:
            self.db.rollback()
            raise DuplicateError(f"협력업체 수정 실패: 중복 데이터 ({str(e)})")
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicError(f"협력업체 수정 중 오류 발생: {str(e)}")
    
    def delete_supplier(self, supplier_id: int) -> bool:
        """
        협력업체 삭제 (소프트 삭제)
        
        Args:
            supplier_id: 협력업체 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            supplier = self.get_supplier_by_id(supplier_id)
            
            # 매핑 관계 확인
            active_mappings_count = self.db.query(CustomerSupplierMapping).filter(
                and_(
                    CustomerSupplierMapping.supplier_id == supplier_id,
                    CustomerSupplierMapping.is_active == True
                )
            ).count()
            
            if active_mappings_count > 0:
                raise BusinessLogicError(
                    f"활성 상태인 사업장 매핑이 {active_mappings_count}개 있어 삭제할 수 없습니다"
                )
            
            # 소프트 삭제
            supplier.is_deleted = True
            supplier.is_active = False
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise BusinessLogicError(f"협력업체 삭제 중 오류 발생: {str(e)}")
    
    def get_supplier_statistics(self) -> Dict[str, Any]:
        """
        협력업체 통계 조회
        
        Returns:
            협력업체 관련 통계
        """
        # 기본 통계
        total_suppliers = self.db.query(func.count(Supplier.id)).filter(
            Supplier.is_deleted == False
        ).scalar()
        
        active_suppliers = self.db.query(func.count(Supplier.id)).filter(
            and_(
                Supplier.is_deleted == False,
                Supplier.is_active == True
            )
        ).scalar()
        
        # 회사 규모별 통계
        scale_stats = self.db.query(
            Supplier.company_scale,
            func.count(Supplier.id).label('count')
        ).filter(
            and_(
                Supplier.is_deleted == False,
                Supplier.is_active == True
            )
        ).group_by(Supplier.company_scale).all()
        
        # 매핑 관계 통계
        mapping_stats = self.db.query(
            func.count(CustomerSupplierMapping.id).label('total_mappings'),
            func.count(
                func.distinct(CustomerSupplierMapping.customer_id)
            ).label('connected_customers')
        ).filter(
            CustomerSupplierMapping.is_active == True
        ).first()
        
        return {
            "total_suppliers": total_suppliers,
            "active_suppliers": active_suppliers,
            "inactive_suppliers": total_suppliers - active_suppliers,
            "scale_distribution": {
                scale or "미분류": count for scale, count in scale_stats
            },
            "mapping_statistics": {
                "total_mappings": mapping_stats.total_mappings or 0,
                "connected_customers": mapping_stats.connected_customers or 0
            }
        }
    
    def _check_duplicate_supplier(
        self, 
        parent_code: Optional[str] = None,
        business_number: Optional[str] = None,
        exclude_id: Optional[int] = None
    ):
        """중복 협력업체 확인"""
        query = self.db.query(Supplier).filter(
            Supplier.is_deleted == False
        )
        
        if exclude_id:
            query = query.filter(Supplier.id != exclude_id)
        
        conditions = []
        if parent_code:
            conditions.append(Supplier.parent_code == parent_code)
        if business_number:
            conditions.append(Supplier.business_number == business_number)
        
        if conditions:
            duplicate = query.filter(or_(*conditions)).first()
            if duplicate:
                if duplicate.parent_code == parent_code:
                    raise DuplicateError(f"협력업체 코드 '{parent_code}'는 이미 사용중입니다")
                if duplicate.business_number == business_number:
                    raise DuplicateError(f"사업자등록번호 '{business_number}'는 이미 사용중입니다")