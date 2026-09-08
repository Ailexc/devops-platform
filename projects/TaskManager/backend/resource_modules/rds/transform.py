"""
RDS transforms.
"""

from core.base_transform import BaseTransform, ToString, ToInteger, ToBool


def status_to_cmdb(raw: str) -> str:
    mapping = {
        "available": "running",
        "creating": "provisioning",
        "deleting": "deleting",
        "stopped": "stopped",
        "failed": "failed",
    }
    return mapping.get(raw, "unknown")


class RDSInstanceTransform(BaseTransform):
    cloud_id = ToString(source="db_instance_identifier", required=True)
    instance_class = ToString(source="db_instance_class", required=True)
    engine = ToString(source="engine", required=True)
    engine_version = ToString(source="engine_version", default="")
    status = ToString(source="db_instance_status", tf_func=status_to_cmdb)
    vpc_id = ToString(source="vpc_id", default="")
    multi_az = ToBool(source="multi_az", default=False)
    storage_type = ToString(source="storage_type", default="")
    allocated_storage = ToInteger(source="allocated_storage", default=0)

    def to_cmdb(self, aws_obj) -> dict:
        result = {}
        for fn in self._declared_fields:
            try:
                result[fn] = self.transform_field(aws_obj, fn)
            except (KeyError, ValueError):
                if self._declared_fields[fn].required:
                    raise
                result[fn] = self._declared_fields[fn].default
        return result
