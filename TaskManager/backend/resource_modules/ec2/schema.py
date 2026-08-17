"""
EC2 resource schemas — Pydantic models for AWS EC2 API responses.

Uses Field(alias=...) to handle AWS CamelCase → Python snake_case conversion.
"""

from pydantic import BaseModel, Field
from typing import Optional


class AWS_EC2Instance(BaseModel):
    """Maps to AWS EC2 describe_instances Response.Instances[0]."""
    instance_id: str = Field(alias="InstanceId")
    image_id: str = Field(alias="ImageId")
    instance_type: str = Field(alias="InstanceType")
    state: str = Field(alias="State.Name")
    vpc_id: Optional[str] = Field(alias="VpcId", default=None)
    subnet_id: Optional[str] = Field(alias="SubnetId", default=None)
    private_ip: Optional[str] = Field(alias="PrivateIpAddress", default=None)
    public_ip: Optional[str] = Field(alias="PublicIpAddress", default=None)
    security_groups: list[dict] = Field(alias="SecurityGroups", default=[])
    tags: dict[str, str] = Field(default={})
    launch_time: Optional[str] = Field(alias="LaunchTime", default=None)

    class Config:
        populate_by_name = True

    @classmethod
    def from_aws_dict(cls, raw: dict) -> "AWS_EC2Instance":
        """Convert raw boto3 response dict to Pydantic model (handles aliases)."""
        return cls.model_validate(raw)


class AWS_SecurityGroup(BaseModel):
    group_id: str = Field(alias="GroupId")
    group_name: str = Field(alias="GroupName")
    description: str = Field(alias="Description", default="")
    vpc_id: Optional[str] = Field(alias="VpcId", default=None)
    tags: dict[str, str] = Field(default={})

    class Config:
        populate_by_name = True


class AWS_NetworkInterface(BaseModel):
    network_interface_id: str = Field(alias="NetworkInterfaceId")
    vpc_id: str = Field(alias="VpcId")
    subnet_id: str = Field(alias="SubnetId")
    status: str = Field(alias="Status")
    private_ip: Optional[str] = Field(alias="PrivateIpAddress", default=None)
    tags: dict[str, str] = Field(default={})

    class Config:
        populate_by_name = True
