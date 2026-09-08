"""
demo_session — 无 AWS 凭据环境下的模拟 AWS 会话。

真实生产走 boto3 AssumeRole；个人 demo 环境无法创建真实 AWS 账号，
这里提供确定性演示数据源，让「采集→对比→批量写」整条同步链路真实执行
（而非前端 stub），面试讲解时数据是真实落库的。

设计要点：
- 每个资源类型的演示数据固定（确定性），首次全量同步 → +N，再次同步 → 无变化
- CMDB 虚拟存储为共享内存，因此各区域返回同一份数据避免互相污染
"""

from __future__ import annotations


def _demo_ec2(count: int = 6) -> list[dict]:
    types = ["t3.micro", "t3.small", "t3.medium", "m5.large", "c5.large", "t3.micro"]
    states = ["running", "running", "stopped", "running", "running", "stopped"]
    items = []
    for i in range(1, count + 1):
        state_name = states[i - 1]
        # 注意：pydantic 把点分别名 "State.Name" 当作平铺字段名处理，
        # 因此同时提供嵌套 State（贴近真实 AWS 响应）与平铺 "State.Name"（pydantic 实际读取）。
        items.append({
            "InstanceId": f"i-demo-{i:03d}",
            "ImageId": f"ami-0demo{i:03d}",
            "InstanceType": types[i - 1],
            "State": {"Name": state_name, "Code": 16 if state_name == "running" else 80},
            "State.Name": state_name,
            "VpcId": "vpc-demo-001",
            "SubnetId": "subnet-demo-001",
            "PrivateIpAddress": f"10.0.{i}.10",
            "PublicIpAddress": f"54.240.{i}.10",
            "SecurityGroups": [{"GroupId": f"sg-demo-00{i % 3 + 1}", "GroupName": f"demo-sg-{i % 3 + 1}"}],
            "Tags": [{"Key": "Name", "Value": f"demo-ec2-{i:02d}"}, {"Key": "Env", "Value": "demo"}],
            "LaunchTime": "2026-06-01T00:00:00+00:00",
        })
    return items


def _demo_security_group(count: int = 4) -> list[dict]:
    return [
        {
            "GroupId": f"sg-demo-{i:03d}",
            "GroupName": f"demo-sg-{i:02d}",
            "Description": f"Demo security group {i}",
            "VpcId": "vpc-demo-001",
            "Tags": [{"Key": "Env", "Value": "demo"}],
        }
        for i in range(1, count + 1)
    ]


def _demo_network_interface(count: int = 5) -> list[dict]:
    return [
        {
            "NetworkInterfaceId": f"eni-demo-{i:03d}",
            "VpcId": "vpc-demo-001",
            "SubnetId": "subnet-demo-001",
            "Status": "in-use" if i % 2 else "available",
            "PrivateIpAddress": f"10.0.{i}.20",
            "Tags": [{"Key": "Env", "Value": "demo"}],
        }
        for i in range(1, count + 1)
    ]


def _demo_vpc(count: int = 3) -> list[dict]:
    cidrs = ["10.0.0.0/16", "172.16.0.0/16", "192.168.0.0/16"]
    return [
        {
            "VpcId": f"vpc-demo-{i:03d}",
            "CidrBlock": cidrs[i - 1],
            "State": "available",
            "IsDefault": i == 1,
            "Tags": [{"Key": "Name", "Value": f"demo-vpc-{i:02d}"}],
        }
        for i in range(1, count + 1)
    ]


def _demo_subnet(count: int = 4) -> list[dict]:
    return [
        {
            "SubnetId": f"subnet-demo-{i:03d}",
            "VpcId": "vpc-demo-001",
            "CidrBlock": f"10.0.{i}.0/24",
            "AvailabilityZone": "ap-northeast-1a",
            "State": "available",
            "Tags": [{"Key": "Name", "Value": f"demo-subnet-{i:02d}"}],
        }
        for i in range(1, count + 1)
    ]


def _demo_rds(count: int = 3) -> list[dict]:
    return [
        {
            "DBInstanceIdentifier": f"rds-demo-{i:03d}",
            "DBInstanceClass": "db.t3.micro",
            "Engine": "mysql",
            "EngineVersion": "8.0.35",
            "DBInstanceStatus": "available" if i % 3 else "stopped",
            "VpcId": "vpc-demo-001",
            "MultiAZ": i == 1,
            "StorageType": "gp3",
            "AllocatedStorage": 50 + i * 10,
            "Endpoint": {"Address": f"rds-demo-{i:03d}.cl-xxx.ap-northeast-1.rds.amazonaws.com", "Port": 3306},
        }
        for i in range(1, count + 1)
    ]


# 资源类型名 → 演示数据生成器（名称与 ResourceDef.name 对齐）
DEMO_DATA_GENERATORS = {
    "EC2": _demo_ec2,
    "SecurityGroup": _demo_security_group,
    "NetworkInterface": _demo_network_interface,
    "VPC": _demo_vpc,
    "Subnet": _demo_subnet,
    "RDS": _demo_rds,
}


class DemoPaginator:
    """模拟 boto3 Paginator：yield 一页数据。"""

    def __init__(self, resource_name: str):
        self.resource_name = resource_name

    def paginate(self, **kwargs):
        gen = DEMO_DATA_GENERATORS.get(self.resource_name)
        items = gen() if gen else []
        # 同时挂到多个 key 下，兼容各模块的响应键探测逻辑
        page = {self.resource_name: items}
        page[f"{self.resource_name}s"] = items
        page[self.resource_name.upper()] = items
        page[f"{self.resource_name.upper()}s"] = items
        yield page


class DemoClient:
    """模拟 boto3 Service client。"""

    def __init__(self, service: str, resource_name: str | None = None):
        self._service = service
        self._resource_name = resource_name

    def get_paginator(self, method: str):
        name = self._resource_name
        # 从方法名推断资源类型（describe_instances → EC2 等兜底）
        if not name:
            name = {
                "describe_instances": "EC2",
                "describe_security_groups": "SecurityGroup",
                "describe_network_interfaces": "NetworkInterface",
                "describe_vpcs": "VPC",
                "describe_subnets": "Subnet",
                "describe_db_instances": "RDS",
            }.get(method, "EC2")
        return DemoPaginator(name)

    def __getattr__(self, name: str):
        """管线会 getattr(client, 'describe_xxx') 探测方法是否存在，
        这里返回一个可调用桩函数即可（真正的数据走 get_paginator）。"""
        if name.startswith("_"):
            raise AttributeError(name)

        def _stub(*args, **kwargs):
            return None

        return _stub


class DemoSession:
    """模拟 boto3 Session：client(service) → DemoClient。"""

    def client(self, service: str, **kwargs):
        return DemoClient(service)
