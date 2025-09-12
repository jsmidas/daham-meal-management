"""
협력업체 모델
- 완전한 데이터 검증
- 비즈니스 규칙 적용
- 확장 가능한 구조
"""
from sqlalchemy import Column, String, Boolean, Text, Index, CheckConstraint
from sqlalchemy.orm import relationship, validates
from .base import BaseModel
import re


class Supplier(BaseModel):
    """협력업체 모델"""
    
    __tablename__ = "suppliers"
    
    # 기본 정보 (필수)
    name = Column(
        String(100), 
        nullable=False, 
        index=True,
        comment="협력업체명"
    )
    
    # 코드 정보 (고유)
    parent_code = Column(
        String(10), 
        unique=True, 
        nullable=False,
        comment="협력업체 코드 (예: WEL, CJ)"
    )
    
    # 사업자 정보
    business_number = Column(
        String(12), 
        unique=True,
        comment="사업자등록번호 (XXX-XX-XXXXX)"
    )
    business_type = Column(
        String(50),
        comment="업태"
    )
    business_item = Column(
        String(100),
        comment="종목"
    )
    
    # 대표자 정보
    representative = Column(
        String(50),
        comment="대표자명"
    )
    
    # 연락처 정보
    headquarters_address = Column(
        Text,
        comment="본사 주소"
    )
    headquarters_phone = Column(
        String(20),
        comment="본사 전화번호"
    )
    headquarters_fax = Column(
        String(20),
        comment="본사 팩스번호"
    )
    email = Column(
        String(100),
        comment="이메일"
    )
    website = Column(
        String(200),
        comment="홈페이지 URL"
    )
    
    # 상태 정보
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="활성 상태"
    )
    company_scale = Column(
        String(10),
        comment="회사 규모 (대기업/중견기업/중소기업)"
    )
    
    # 비고
    notes = Column(
        Text,
        comment="비고 및 특이사항"
    )
    
    # 관계 정의
    customer_mappings = relationship(
        "CustomerSupplierMapping",
        back_populates="supplier",
        cascade="all, delete-orphan"
    )
    
    # 제약 조건
    __table_args__ = (
        CheckConstraint(
            "company_scale IN ('대기업', '중견기업', '중소기업') OR company_scale IS NULL",
            name="check_company_scale"
        ),
        CheckConstraint(
            "LENGTH(parent_code) >= 2 AND LENGTH(parent_code) <= 10",
            name="check_parent_code_length"
        ),
        Index('idx_supplier_active_name', 'is_active', 'name'),
        Index('idx_supplier_code', 'parent_code'),
    )
    
    # 데이터 검증
    @validates('business_number')
    def validate_business_number(self, key, business_number):
        """사업자등록번호 형식 검증"""
        if business_number:
            # XXX-XX-XXXXX 형식 검증
            pattern = r'^\d{3}-\d{2}-\d{5}$'
            if not re.match(pattern, business_number):
                raise ValueError("사업자등록번호는 XXX-XX-XXXXX 형식이어야 합니다")
        return business_number
    
    @validates('email')
    def validate_email(self, key, email):
        """이메일 형식 검증"""
        if email:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, email):
                raise ValueError("올바른 이메일 형식이 아닙니다")
        return email
    
    @validates('parent_code')
    def validate_parent_code(self, key, parent_code):
        """협력업체 코드 검증"""
        if parent_code:
            # 대문자 영문자와 숫자만 허용
            pattern = r'^[A-Z0-9]+$'
            if not re.match(pattern, parent_code):
                raise ValueError("협력업체 코드는 대문자 영문자와 숫자만 허용됩니다")
        return parent_code
    
    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', code='{self.parent_code}')>"
    
    @property
    def display_name(self):
        """표시용 이름 (코드 포함)"""
        return f"{self.name} ({self.parent_code})"
    
    def is_major_company(self):
        """대기업 여부 확인"""
        return self.company_scale == '대기업'