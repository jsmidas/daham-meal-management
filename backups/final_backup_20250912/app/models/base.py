"""
기본 모델 클래스
- 공통 필드 정의
- 타임스탬프 자동 관리
- 소프트 삭제 지원
"""
from sqlalchemy import Column, Integer, DateTime, Boolean
from sqlalchemy.sql import func
from app.database import Base


class BaseModel(Base):
    """모든 모델의 기본 클래스"""
    
    __abstract__ = True
    
    # 기본 필드
    id = Column(Integer, primary_key=True, index=True, comment="고유 ID")
    
    # 타임스탬프 (자동 관리)
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False,
        comment="생성일시"
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정일시"
    )
    
    # 소프트 삭제 지원
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="삭제 여부"
    )
    
    def __repr__(self):
        """객체 표현"""
        return f"<{self.__class__.__name__}(id={self.id})>"
    
    def to_dict(self):
        """딕셔너리 변환"""
        return {
            column.key: getattr(self, column.key)
            for column in self.__table__.columns
        }