"""
사업장 모델
- 계층구조 지원
- 완전한 데이터 검증
- 비즈니스 규칙 적용
"""
from sqlalchemy import Column, String, Integer, Boolean, Text, ForeignKey, Index, CheckConstraint
from sqlalchemy.orm import relationship, validates
from .base import BaseModel
import re


class Customer(BaseModel):
    """사업장 모델"""
    
    __tablename__ = "customers"
    
    # 기본 정보 (필수)
    name = Column(
        String(100), 
        nullable=False, 
        index=True,
        comment="사업장명"
    )
    
    # 코드 정보 (고유)
    code = Column(
        String(50), 
        unique=True,
        comment="사업장 일반코드"
    )
    site_code = Column(
        String(10), 
        unique=True, 
        nullable=False,
        comment="사업장 고유코드 (예: H001, S001)"
    )
    
    # 사업장 유형
    site_type = Column(
        String(20),
        default="detail",
        nullable=False,
        comment="사업장 유형 (head/detail/period)"
    )
    
    # 계층 구조
    parent_id = Column(
        Integer, 
        ForeignKey("customers.id", ondelete="SET NULL"),
        comment="상위 사업장 ID"
    )
    level = Column(
        Integer,
        default=0,
        nullable=False,
        comment="계층 레벨 (0:본사, 1:사업장, 2:세부)"
    )
    sort_order = Column(
        Integer,
        default=0,
        nullable=False,
        comment="정렬 순서"
    )
    
    # 운영 정보
    portion_size = Column(
        Integer,
        comment="1인당 제공량(g)"
    )
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="활성 상태"
    )
    
    # 담당자 정보
    contact_person = Column(
        String(100),
        comment="담당자명"
    )
    contact_phone = Column(
        String(50),
        comment="담당자 연락처"
    )
    
    # 주소 정보
    address = Column(
        Text,
        comment="사업장 주소"
    )
    
    # 비고
    description = Column(
        Text,
        comment="사업장 설명 및 특이사항"
    )
    
    # 관계 정의
    # 자기 참조 관계 (계층 구조)
    parent = relationship(
        "Customer", 
        remote_side="Customer.id",
        back_populates="children"
    )
    children = relationship(
        "Customer",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    
    # 협력업체 매핑
    supplier_mappings = relationship(
        "CustomerSupplierMapping",
        back_populates="customer",
        cascade="all, delete-orphan"
    )
    
    # 제약 조건
    __table_args__ = (
        CheckConstraint(
            "site_type IN ('head', 'detail', 'period')",
            name="check_site_type"
        ),
        CheckConstraint(
            "level >= 0 AND level <= 2",
            name="check_level_range"
        ),
        CheckConstraint(
            "portion_size IS NULL OR portion_size > 0",
            name="check_positive_portion_size"
        ),
        CheckConstraint(
            "LENGTH(site_code) >= 3 AND LENGTH(site_code) <= 10",
            name="check_site_code_length"
        ),
        Index('idx_customer_active_name', 'is_active', 'name'),
        Index('idx_customer_site_code', 'site_code'),
        Index('idx_customer_hierarchy', 'parent_id', 'level', 'sort_order'),
    )
    
    # 데이터 검증
    @validates('site_code')
    def validate_site_code(self, key, site_code):
        """사업장 코드 검증"""
        if site_code:
            # 대문자 영문자와 숫자만 허용
            pattern = r'^[A-Z0-9]+$'
            if not re.match(pattern, site_code):
                raise ValueError("사업장 코드는 대문자 영문자와 숫자만 허용됩니다")
        return site_code
    
    @validates('contact_phone')
    def validate_phone(self, key, phone):
        """전화번호 형식 검증"""
        if phone:
            # 다양한 전화번호 형식 허용
            pattern = r'^(\d{2,3}-\d{3,4}-\d{4}|\d{10,11})$'
            if not re.match(pattern, phone.replace('-', '').replace(' ', '')):
                raise ValueError("올바른 전화번호 형식이 아닙니다")
        return phone
    
    @validates('level', 'parent_id')
    def validate_hierarchy(self, key, value):
        """계층 구조 검증"""
        if key == 'level':
            if value == 0 and self.parent_id is not None:
                raise ValueError("최상위 레벨(0)은 상위 사업장을 가질 수 없습니다")
            elif value > 0 and self.parent_id is None:
                raise ValueError("하위 레벨은 반드시 상위 사업장이 필요합니다")
        return value
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', code='{self.site_code}')>"
    
    @property
    def display_name(self):
        """표시용 이름 (코드 포함)"""
        return f"{self.name} ({self.site_code})"
    
    @property
    def full_hierarchy_name(self):
        """전체 계층 이름"""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    def is_head_office(self):
        """본사 여부 확인"""
        return self.site_type == 'head' and self.level == 0
    
    def get_all_children(self):
        """모든 하위 사업장 조회 (재귀)"""
        all_children = []
        for child in self.children:
            all_children.append(child)
            all_children.extend(child.get_all_children())
        return all_children
    
    def get_primary_suppliers(self):
        """주 협력업체 목록 조회"""
        return [
            mapping.supplier 
            for mapping in self.supplier_mappings 
            if mapping.is_primary_supplier and mapping.is_active
        ]