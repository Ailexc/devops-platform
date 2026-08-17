"""
通用工具函数
"""
import uuid
import hashlib
import time


def generate_instance_no(prefix='WI'):
    """
    生成唯一的流程实例编号。
    格式: {prefix}-{YYYYMMDD}-{6位随机字符}
    """
    from django.utils import timezone
    now = timezone.now()
    date_part = now.strftime('%Y%m%d')
    rand_part = uuid.uuid4().hex[:6].upper()
    return f'{prefix}-{date_part}-{rand_part}'


def generate_job_id():
    """生成唯一 Job ID"""
    return uuid.uuid4().hex


def md5_hash(text: str) -> str:
    """计算字符串的 MD5 哈希"""
    return hashlib.md5(text.encode()).hexdigest()
