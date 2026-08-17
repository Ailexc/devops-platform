"""
BaseTransform — class-style declarative field transformer.

Inspired by Django REST Framework serializers, but purpose-built for
converting AWS API response data into CMDB model fields.

Usage:
    class EC2Transform(BaseTransform):
        cloud_id = ToString(source="instance_id", required=True)
        instance_type = ToString(source="instance_type", required=True)
        vpc_id = ToString(source="vpc_id", default="")
        state = ToString(source="state", tf_func=state_to_cmdb)
        tags = ToDict(source="tags", default={})

        def to_cmdb(self, aws_obj) -> dict:
            ...
"""


class TransformField:
    """Descriptor for a single field transform rule."""

    def __init__(self, source: str, required: bool = False, default=None, tf_func=None):
        self.source = source
        self.required = required
        self.default = default
        self.tf_func = tf_func


class ToString(TransformField):
    pass


class ToInteger(TransformField):
    pass


class ToBool(TransformField):
    """Boolean field — 值已为 bool 时原样返回，否则做宽松布尔解析。"""

    def __init__(self, source: str, required: bool = False, default=None, tf_func=None):
        super().__init__(source=source, required=required, default=default, tf_func=tf_func)


class ToDict(TransformField):
    pass


class ToList(TransformField):
    pass


def _is_descriptor(obj):
    return isinstance(obj, TransformField)


class BaseTransformMeta(type):
    """Metaclass that collects TransformField descriptors."""

    def __new__(mcs, name, bases, namespace):
        fields = {}
        for key, val in namespace.items():
            if _is_descriptor(val):
                fields[key] = val
        cls = super().__new__(mcs, name, bases, namespace)
        cls._declared_fields = fields
        return cls


class BaseTransform(metaclass=BaseTransformMeta):
    """Base class for all transforms. Subclass and declare fields."""

    _declared_fields: dict = {}

    def to_cmdb(self, aws_obj) -> dict:
        """Convert an AWS schema object to a CMDB-ready dict.
        Override in subclass with actual field logic.
        """
        raise NotImplementedError

    def transform_field(self, aws_obj, field_name: str):
        """Extract and transform a single field value from aws_obj."""
        field = self._declared_fields.get(field_name)
        if not field:
            raise KeyError(f"Unknown field: {field_name}")

        raw = getattr(aws_obj, field.source, None) if hasattr(aws_obj, field.source) else aws_obj.get(field.source)

        if raw is None:
            if field.required:
                raise ValueError(f"Required field '{field_name}' (source={field.source}) is missing")
            return field.default

        if field.tf_func:
            return field.tf_func(raw)
        return raw
