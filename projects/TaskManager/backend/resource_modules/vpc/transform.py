"""
VPC transforms.
"""

from core.base_transform import BaseTransform, ToString, ToBool, ToDict


class VPCTransform(BaseTransform):
    cloud_id = ToString(source="vpc_id", required=True)
    cidr_block = ToString(source="cidr_block", default="")
    state = ToString(source="state", default="available")
    is_default = ToBool(source="is_default", default=False)
    tags = ToDict(source="tags", default={})

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


class SubnetTransform(BaseTransform):
    cloud_id = ToString(source="subnet_id", required=True)
    vpc_id = ToString(source="vpc_id", required=True)
    cidr_block = ToString(source="cidr_block", default="")
    availability_zone = ToString(source="availability_zone", default="")
    state = ToString(source="state", default="available")
    tags = ToDict(source="tags", default={})

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
