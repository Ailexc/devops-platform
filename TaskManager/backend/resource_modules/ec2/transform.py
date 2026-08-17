"""
EC2 transforms — convert AWS Pydantic schemas to CMDB-ready dicts.

Each transform class inherits from BaseTransform and declares fields
using the class-style descriptor syntax.
"""

from core.base_transform import BaseTransform, ToString, ToDict


def state_to_cmdb(raw: str) -> str:
    """Map AWS instance state to CMDB status."""
    mapping = {
        "running": "running",
        "stopped": "stopped",
        "pending": "provisioning",
        "stopping": "stopping",
        "terminated": "deleted",
    }
    return mapping.get(raw, "unknown")


class EC2InstanceTransform(BaseTransform):
    cloud_id = ToString(source="instance_id", required=True)
    name = ToString(source="tags", required=False, default="")
    instance_type = ToString(source="instance_type", required=True)
    status = ToString(source="state", tf_func=state_to_cmdb)
    vpc_id = ToString(source="vpc_id", default="")
    subnet_id = ToString(source="subnet_id", default="")
    private_ip = ToString(source="private_ip", default="")
    public_ip = ToString(source="public_ip", default="")
    image_id = ToString(source="image_id", required=True)
    tags = ToDict(source="tags", default={})

    def to_cmdb(self, aws_obj) -> dict:
        """Produce a flat CMDB-ready dict from an AWS_EC2Instance."""
        result = {}
        for field_name in self._declared_fields:
            try:
                result[field_name] = self.transform_field(aws_obj, field_name)
            except (KeyError, ValueError) as e:
                if self._declared_fields[field_name].required:
                    raise
                result[field_name] = self._declared_fields[field_name].default
        return result


class SecurityGroupTransform(BaseTransform):
    cloud_id = ToString(source="group_id", required=True)
    name = ToString(source="group_name", required=True)
    description = ToString(source="description", default="")
    vpc_id = ToString(source="vpc_id", default="")
    tags = ToDict(source="tags", default={})

    def to_cmdb(self, aws_obj) -> dict:
        result = {}
        for field_name in self._declared_fields:
            try:
                result[field_name] = self.transform_field(aws_obj, field_name)
            except (KeyError, ValueError):
                if self._declared_fields[field_name].required:
                    raise
                result[field_name] = self._declared_fields[field_name].default
        return result


class NetworkInterfaceTransform(BaseTransform):
    cloud_id = ToString(source="network_interface_id", required=True)
    vpc_id = ToString(source="vpc_id", required=True)
    subnet_id = ToString(source="subnet_id", required=True)
    status = ToString(source="status", required=True)
    private_ip = ToString(source="private_ip", default="")
    tags = ToDict(source="tags", default={})

    def to_cmdb(self, aws_obj) -> dict:
        result = {}
        for field_name in self._declared_fields:
            try:
                result[field_name] = self.transform_field(aws_obj, field_name)
            except (KeyError, ValueError):
                if self._declared_fields[field_name].required:
                    raise
                result[field_name] = self._declared_fields[field_name].default
        return result
