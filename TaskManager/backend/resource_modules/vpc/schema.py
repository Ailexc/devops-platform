"""
VPC resource schemas — Pydantic models for AWS VPC API responses.
"""

from pydantic import BaseModel, Field
from typing import Optional


class AWS_VPC(BaseModel):
    vpc_id: str = Field(alias="VpcId")
    cidr_block: str = Field(alias="CidrBlock", default="")
    state: str = Field(alias="State", default="available")
    is_default: bool = Field(alias="IsDefault", default=False)
    tags: dict[str, str] = Field(default={})

    class Config:
        populate_by_name = True

    @classmethod
    def from_aws_dict(cls, raw: dict) -> "AWS_VPC":
        return cls.model_validate(raw)


class AWS_Subnet(BaseModel):
    subnet_id: str = Field(alias="SubnetId")
    vpc_id: str = Field(alias="VpcId")
    cidr_block: str = Field(alias="CidrBlock", default="")
    availability_zone: str = Field(alias="AvailabilityZone", default="")
    state: str = Field(alias="State", default="available")
    tags: dict[str, str] = Field(default={})

    class Config:
        populate_by_name = True

    @classmethod
    def from_aws_dict(cls, raw: dict) -> "AWS_Subnet":
        return cls.model_validate(raw)
