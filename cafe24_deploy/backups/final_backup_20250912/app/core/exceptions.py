"""
사용자 정의 예외 클래스들
- 명확한 예외 분류
- 일관된 에러 메시지
- HTTP 상태 코드 매핑
"""
from typing import Optional, Dict, Any


class BaseCustomException(Exception):
    """사용자 정의 예외의 기본 클래스"""
    
    def __init__(
        self, 
        message: str, 
        status_code: int = 500,
        detail: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)


class BusinessLogicError(BaseCustomException):
    """비즈니스 로직 오류"""
    
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, detail=detail)


class NotFoundError(BaseCustomException):
    """리소스 없음 오류"""
    
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, detail=detail)


class DuplicateError(BaseCustomException):
    """중복 데이터 오류"""
    
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=409, detail=detail)


class ValidationError(BaseCustomException):
    """데이터 검증 오류"""
    
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=422, detail=detail)


class AuthenticationError(BaseCustomException):
    """인증 오류"""
    
    def __init__(self, message: str = "인증이 필요합니다", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=401, detail=detail)


class AuthorizationError(BaseCustomException):
    """권한 부족 오류"""
    
    def __init__(self, message: str = "권한이 부족합니다", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=403, detail=detail)


class DatabaseError(BaseCustomException):
    """데이터베이스 오류"""
    
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, detail=detail)


class ExternalServiceError(BaseCustomException):
    """외부 서비스 연동 오류"""
    
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=502, detail=detail)


# HTTP 예외 응답 생성 유틸리티
def create_error_response(exception: BaseCustomException) -> Dict[str, Any]:
    """
    사용자 정의 예외를 HTTP 응답 형태로 변환
    
    Args:
        exception: 사용자 정의 예외
        
    Returns:
        HTTP 응답용 딕셔너리
    """
    return {
        "success": False,
        "error": {
            "type": exception.__class__.__name__,
            "message": exception.message,
            "status_code": exception.status_code,
            "detail": exception.detail
        }
    }