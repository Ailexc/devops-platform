"""
自定义异常与 DRF 异常处理器
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import APIException
from rest_framework import status


class WorkflowError(APIException):
    """流程引擎业务异常"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '流程操作失败'


class TaskNotFoundError(APIException):
    """任务不存在"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = '任务不存在'


class TaskAlreadyCompletedError(APIException):
    """任务已完成"""
    status_code = status.HTTP_409_CONFLICT
    default_detail = '任务已完成或已关闭'


class PermissionDeniedError(APIException):
    """权限不足"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = '权限不足，无法执行此操作'


def custom_exception_handler(exc, context):
    """
    自定义 DRF 异常处理器，统一错误响应格式。
    """
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'code': response.status_code,
            'message': response.data.get('detail', str(response.data))
                      if isinstance(response.data, dict) else str(response.data),
            'data': None,
        }
    return response
