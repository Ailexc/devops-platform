"""
transform_utils — 转换辅助。

CMDB 存储使用 bind_key（AWS 字段名，如 instance_id / vpc_id）做索引，
而 transform.to_cmdb() 产物用 cloud_id 作唯一标识。此处统一在转换产物中
补齐 bind_key 字段，保证 diff/删除/关系绑定都能按 bind_key 定位。
"""


def to_cmdb_with_bind(transform, resource_def, aws_obj) -> dict:
    """转换 AWS schema 对象为 CMDB dict，并补齐 resource_def.bind_key 字段。"""
    d = transform.to_cmdb(aws_obj)
    bind_val = getattr(aws_obj, resource_def.bind_key, None)
    if bind_val is not None:
        d[resource_def.bind_key] = bind_val
    return d
