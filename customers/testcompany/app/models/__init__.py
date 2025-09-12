"""
견고한 데이터 모델 패키지
- 명확한 관계 정의
- 데이터 무결성 보장
- 확장 가능한 구조
"""
from .base import BaseModel
from .suppliers import Supplier
from .customers import Customer
from .mappings import CustomerSupplierMapping

__all__ = [
    "BaseModel",
    "Supplier", 
    "Customer",
    "CustomerSupplierMapping"
]