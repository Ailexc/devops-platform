"""
EC2 resource registration — binds schema, transform, model, and sync logic.

This is the primary entry point that the orchestrator uses to discover
and invoke EC2-related sync operations.
"""

from dataclasses import dataclass, field
from typing import Callable

from .schema import AWS_EC2Instance, AWS_SecurityGroup, AWS_NetworkInterface
from .transform import EC2InstanceTransform, SecurityGroupTransform, NetworkInterfaceTransform
from .models import CmdbEC2, CmdbSecurityGroup, CmdbNetworkInterface


@dataclass
class Association:
    """Defines a relationship between two resource types."""
    target: str          # Target model name (e.g., "VPC", "Subnet")
    cardinality: str     # "1:1", "n:1", "n:n"
    key: str             # Foreign key expression (e.g., "vpc_id")
    description: str = ""


@dataclass
class ResourceDef:
    """Registration record for a single resource type."""
    name: str
    aws_api: str                       # boto3 method name, e.g. "ec2.describe_instances"
    schema_cls: type
    transform_cls: type
    model_cls: type
    bind_key: str                      # unique identifier field
    associations: list[Association] = field(default_factory=list)
    sync_fn: Callable | None = None    # optional custom sync function


# ── Resource definitions ────────────────────────────────────────────

EC2 = ResourceDef(
    name="EC2",
    aws_api="ec2.describe_instances",
    schema_cls=AWS_EC2Instance,
    transform_cls=EC2InstanceTransform,
    model_cls=CmdbEC2,
    bind_key="instance_id",
    associations=[
        Association(target="VPC", cardinality="n:1", key="vpc_id", description="EC2所在的VPC"),
        Association(target="Subnet", cardinality="n:1", key="subnet_id", description="EC2所在的子网"),
        Association(target="SecurityGroup", cardinality="n:n", key="security_groups", description="EC2关联的安全组"),
    ],
)

SecurityGroup = ResourceDef(
    name="SecurityGroup",
    aws_api="ec2.describe_security_groups",
    schema_cls=AWS_SecurityGroup,
    transform_cls=SecurityGroupTransform,
    model_cls=CmdbSecurityGroup,
    bind_key="group_id",
    associations=[
        Association(target="VPC", cardinality="n:1", key="vpc_id", description="安全组所属VPC"),
    ],
)

NetworkInterface = ResourceDef(
    name="NetworkInterface",
    aws_api="ec2.describe_network_interfaces",
    schema_cls=AWS_NetworkInterface,
    transform_cls=NetworkInterfaceTransform,
    model_cls=CmdbNetworkInterface,
    bind_key="network_interface_id",
    associations=[
        Association(target="VPC", cardinality="n:1", key="vpc_id", description="网卡所属VPC"),
        Association(target="Subnet", cardinality="n:1", key="subnet_id", description="网卡所属子网"),
    ],
)

# Grouped for the orchestrator — "计算" group
COMPUTE_GROUP = [EC2, SecurityGroup, NetworkInterface]


def get_sync_resources() -> list[ResourceDef]:
    """Return all EC2 module resources (for discovery by the registry)."""
    return COMPUTE_GROUP
