"""
自定义模型字段
"""
import json

from django.core.exceptions import ValidationError
from django.db import models
from jsonschema import validate, ValidationError as SchemaValidationError


class JSONSchemaField(models.JSONField):
    """
    带 JSON Schema 校验的 JSONField。
    通过 schema 参数传入 JSON Schema 字典。
    """

    def __init__(self, *args, schema=None, **kwargs):
        self.schema = schema
        super().__init__(*args, **kwargs)

    def validate(self, value, model_instance):
        super().validate(value, model_instance)
        if self.schema and value is not None:
            try:
                validate(instance=value, schema=self.schema)
            except SchemaValidationError as e:
                raise ValidationError(f'JSON schema validation failed: {e.message}')

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.schema is not None:
            kwargs['schema'] = self.schema
        return name, path, args, kwargs
