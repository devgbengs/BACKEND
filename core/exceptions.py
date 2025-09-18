class BaseError(Exception):
    """Base exception for all custom exceptions"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class NotFoundException(BaseError):
    """Raised when a resource is not found"""
    pass

class ValidationError(BaseError):
    """Raised when validation fails"""
    pass

class InsufficientStockError(BaseError):
    """Raised when there is insufficient stock for an operation"""
    pass

class AuthenticationError(BaseError):
    """Raised when authentication fails"""
    pass

class AuthorizationError(BaseError):
    """Raised when user doesn't have required permissions"""
    pass

class TenantError(BaseError):
    """Raised when there are tenant-related issues"""
    pass

class BusinessRuleError(BaseError):
    """Raised when a business rule is violated"""
    pass

class DuplicateError(BaseError):
    """Raised when attempting to create a duplicate resource"""
    pass