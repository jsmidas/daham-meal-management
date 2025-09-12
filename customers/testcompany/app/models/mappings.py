"""
사업장-협력업체 매핑 모델
- N:N 관계 관리
- 비즈니스 규칙 강화
- 데이터 무결성 보장
"""
from sqlalchemy import Column, Integer, String, Boolean, Date, Text, ForeignKey, Index, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from .base import BaseModel
import re


class CustomerSupplierMapping(BaseModel):
    """사업장-협력업체 매핑 모델"""
    
    __tablename__ = "customer_supplier_mappings"
    
    # 외래키 관계 (필수)
    customer_id = Column(
        Integer, 
        ForeignKey("customers.id", ondelete="CASCADE"), 
        nullable=False,
        comment="사업장 ID"
    )
    supplier_id = Column(
        Integer, 
        ForeignKey("suppliers.id", ondelete="CASCADE"), 
        nullable=False,
        comment="협력업체 ID"
    )
    
    # 매핑 정보
    delivery_code = Column(
        String(20),
        comment="사업장별 배송코드 (예: WEL-SCH-001)"
    )
    priority_order = Column(
        Integer,
        default=0,
        nullable=False,
        comment="우선순위 (낮을수록 높은 우선순위)"
    )
    is_primary_supplier = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="주 협력업체 여부"
    )
    
    # 계약 정보
    contract_start_date = Column(
        Date,
        comment="계약 시작일"
    )
    contract_end_date = Column(
        Date,
        comment="계약 종료일"
    )
    
    # 상태 정보
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="활성 상태"
    )
    
    # 비고
    notes = Column(
        Text,
        comment="매핑 관련 특이사항"
    )
    
    # 관계 정의
    customer = relationship(
        "Customer", 
        back_populates="supplier_mappings"
    )
    supplier = relationship(
        "Supplier", 
        back_populates="customer_mappings"
    )
    
    # 제약 조건
    __table_args__ = (
        # 중복 방지: 동일 사업장-협력업체 조합은 하나만
        UniqueConstraint(
            'customer_id', 'supplier_id',
            name='uq_customer_supplier'
        ),
        # 배송코드 고유성 (활성 매핑에 한해)
        UniqueConstraint(
            'delivery_code',
            name='uq_delivery_code'
        ),
        # 우선순위는 양수
        CheckConstraint(
            'priority_order >= 0',
            name='check_positive_priority'
        ),
        # 계약 기간 유효성
        CheckConstraint(
            'contract_end_date IS NULL OR contract_start_date IS NULL OR contract_end_date >= contract_start_date',
            name='check_contract_period'
        ),
        # 배송코드 형식
        CheckConstraint(
            "delivery_code IS NULL OR LENGTH(delivery_code) >= 3",
            name='check_delivery_code_length'
        ),
        # 인덱스
        Index('idx_mapping_customer', 'customer_id'),
        Index('idx_mapping_supplier', 'supplier_id'),
        Index('idx_mapping_active', 'is_active'),
        Index('idx_mapping_primary', 'is_primary_supplier', 'is_active'),
        Index('idx_mapping_priority', 'customer_id', 'priority_order'),
    )
    
    # 데이터 검증
    @validates('delivery_code')
    def validate_delivery_code(self, key, delivery_code):
        """배송코드 형식 검증"""
        if delivery_code:
            # 대문자 영문자, 숫자, 하이픈만 허용
            pattern = r'^[A-Z0-9-]+$'
            if not re.match(pattern, delivery_code):
                raise ValueError("배송코드는 대문자 영문자, 숫자, 하이픈만 허용됩니다")
            
            # 기본 형식: XXX-XXX-XXX
            if len(delivery_code.split('-')) != 3:
                raise ValueError("배송코드는 XXX-XXX-XXX 형식이어야 합니다")
                
        return delivery_code
    
    @validates('priority_order')
    def validate_priority(self, key, priority_order):
        """우선순위 검증"""
        if priority_order < 0:
            raise ValueError("우선순위는 0 이상이어야 합니다")
        return priority_order
    
    @validates('contract_start_date', 'contract_end_date')
    def validate_contract_dates(self, key, date_value):
        """계약 기간 검증"""
        if key == 'contract_end_date' and date_value:
            if self.contract_start_date and date_value < self.contract_start_date:
                raise ValueError("계약 종료일은 시작일보다 늦어야 합니다")
        return date_value
    
    def __repr__(self):
        return f"<CustomerSupplierMapping(customer_id={self.customer_id}, supplier_id={self.supplier_id}, code='{self.delivery_code}')>"
    
    @property
    def display_name(self):
        """표시용 이름"""
        if self.customer and self.supplier:
            return f"{self.customer.name} ↔ {self.supplier.name}"
        return f"매핑 ID: {self.id}"
    
    @property
    def status_text(self):
        """상태 텍스트"""
        if not self.is_active:
            return "비활성"
        elif self.is_primary_supplier:
            return "주 협력업체"
        else:
            return "보조 협력업체"
    
    def is_contract_active(self):
        """계약 활성 상태 확인"""
        from datetime import date
        today = date.today()
        
        if not self.is_active:
            return False
            
        if self.contract_start_date and today < self.contract_start_date:
            return False
            
        if self.contract_end_date and today > self.contract_end_date:
            return False
            
        return True
    
    def get_contract_status(self):
        """계약 상태 조회"""
        if not self.contract_start_date:
            return "계약정보 없음"
            
        from datetime import date
        today = date.today()
        
        if today < self.contract_start_date:
            return "계약 대기중"
        elif self.contract_end_date and today > self.contract_end_date:
            return "계약 만료"
        else:
            return "계약 진행중"