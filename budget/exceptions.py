from rest_framework.exceptions import APIException

class BusinessException(APIException):
    status_code = 400
    default_detail = "Business rule violated."

class ObjectNotFound(BusinessException):
    status_code = 404
    default_detail = "Requested object not found."

class BudgetExceeded(BusinessException):
    default_detail = "Budget exceeded."

class ApprovalError(BusinessException):
    default_detail = "Approval failed."
