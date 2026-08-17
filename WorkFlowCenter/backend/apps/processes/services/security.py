"""
发起程序 API Key 工具
"""
import hashlib
import hmac
import secrets


def generate_api_key() -> str:
    """生成 API Key（仅创建/重置时返回明文）"""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """计算 API Key 摘要（只存摘要，不存明文）"""
    return hashlib.sha256(api_key.encode('utf-8')).hexdigest()


def verify_api_key(app, api_key: str) -> bool:
    """校验 API Key 是否与存储的摘要匹配"""
    if not app.api_key_hash or not api_key:
        return False
    return hmac.compare_digest(app.api_key_hash, hash_api_key(api_key))
