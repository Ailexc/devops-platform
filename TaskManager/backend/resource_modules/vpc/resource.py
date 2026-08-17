"""
VPC resource registration.
"""

from dataclasses import dataclass, field

from .schema import AWS_VPC, AWS_Subnet
from .transform import VPCTransform, SubnetTransform
from .models import CmdbVPC, CmdbSubnet

from resource_modules.ec2.resource import ResourceDef, Association


VPC = ResourceDef(
    name="VPC",
    aws_api="ec2.describe_vpcs",
    schema_cls=AWS_VPC,
    transform_cls=VPCTransform,
    model_cls=CmdbVPC,
    bind_key="vpc_id",
    associations=[
        Association(target="EC2", cardinality="1:n", key="vpc_id", description="VPC内的EC2实例"),
        Association(target="Subnet", cardinality="1:n", key="vpc_id", description="VPC内的子网"),
    ],
)

Subnet = ResourceDef(
    name="Subnet",
    aws_api="ec2.describe_subnets",
    schema_cls=AWS_Subnet,
    transform_cls=SubnetTransform,
    model_cls=CmdbSubnet,
    bind_key="subnet_id",
    associations=[
        Association(target="VPC", cardinality="n:1", key="vpc_id", description="子网所属VPC"),
    ],
)

NETWORK_GROUP = [VPC, Subnet]


def get_sync_resources() -> list[ResourceDef]:
    return NETWORK_GROUP
