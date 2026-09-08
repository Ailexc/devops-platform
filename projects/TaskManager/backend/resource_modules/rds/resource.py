"""
RDS resource registration.
"""

from resource_modules.ec2.resource import ResourceDef, Association
from .schema import AWS_RDSInstance
from .transform import RDSInstanceTransform
from .models import CmdbRDS


RDS = ResourceDef(
    name="RDS",
    aws_api="rds.describe_db_instances",
    schema_cls=AWS_RDSInstance,
    transform_cls=RDSInstanceTransform,
    model_cls=CmdbRDS,
    bind_key="db_instance_identifier",
    associations=[
        Association(target="VPC", cardinality="n:1", key="vpc_id", description="RDS实例所属VPC"),
        Association(target="EC2", cardinality="n:n", key="vpc_id", description="同VPC内的EC2"),
    ],
)

STORAGE_GROUP = [RDS]


def get_sync_resources() -> list[ResourceDef]:
    return STORAGE_GROUP
