"""
RDS resource schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional


class AWS_RDSInstance(BaseModel):
    db_instance_identifier: str = Field(alias="DBInstanceIdentifier")
    db_instance_class: str = Field(alias="DBInstanceClass", default="")
    engine: str = Field(alias="Engine", default="")
    engine_version: str = Field(alias="EngineVersion", default="")
    db_instance_status: str = Field(alias="DBInstanceStatus", default="available")
    endpoint: Optional[dict] = Field(alias="Endpoint", default=None)
    vpc_id: Optional[str] = Field(alias="VpcId", default=None)
    subnet_group: Optional[dict] = Field(alias="DBSubnetGroup", default=None)
    multi_az: bool = Field(alias="MultiAZ", default=False)
    storage_type: str = Field(alias="StorageType", default="")
    allocated_storage: int = Field(alias="AllocatedStorage", default=0)
    tags: list[dict] = Field(default=[])

    class Config:
        populate_by_name = True

    @classmethod
    def from_aws_dict(cls, raw: dict) -> "AWS_RDSInstance":
        return cls.model_validate(raw)
