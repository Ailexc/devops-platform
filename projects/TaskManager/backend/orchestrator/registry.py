"""
Resource Registry — auto-discovers resource modules and their definitions.

Each resource module exposes `get_sync_resources()` which returns a list
of ResourceDef objects.  The registry aggregates them for the orchestrator.
"""

from typing import Type
from dataclasses import dataclass, field


@dataclass
class ResourceGroupDef:
    """A logical group of resources (e.g. "计算", "网络", "存储")."""
    name: str
    resources: list = field(default_factory=list)


@dataclass
class RelationDef:
    """A global association between two resource types (deduplicated).

    key: 源端绑定字段名（如 vpc_id）; cardinality: 如 n:1 / n:n / 1:n
    """
    source: str
    target: str
    cardinality: str
    key: str
    description: str = ""


class ResourceRegistry:
    """Central registry of all known resource types, groups and relations.

    — 能力层（代码注册）数据源：系统"支持什么资源/关系"由代码声明，
      不需要 DB 表承载，discover_modules() 收集的 dict 即元数据。
    """

    def __init__(self):
        self._groups: dict[str, ResourceGroupDef] = {}
        self._individual: dict[str, Type] = {}
        self._relations: list[RelationDef] = []
        self._relation_keys: set[str] = set()

    def register_group(self, group: ResourceGroupDef):
        self._groups[group.name] = group
        for res in group.resources:
            self._individual[res.name] = res
            # 收集该资源声明的关联关系（去重：source→target 唯一）
            for assoc in getattr(res, "associations", []):
                key = f"{res.name}:{assoc.target}"
                if key not in self._relation_keys:
                    self._relation_keys.add(key)
                    self._relations.append(
                        RelationDef(
                            source=res.name,
                            target=assoc.target,
                            cardinality=assoc.cardinality,
                            key=assoc.key,
                            description=assoc.description,
                        )
                    )

    def get_group(self, name: str) -> ResourceGroupDef | None:
        return self._groups.get(name)

    def get_resource(self, name: str):
        return self._individual.get(name)

    def list_groups(self) -> list[ResourceGroupDef]:
        return list(self._groups.values())

    def list_resources(self) -> list:
        return list(self._individual.values())

    def list_relations(self) -> list[RelationDef]:
        """Global unique relation list (能力层)."""
        return list(self._relations)

    def get_relation(self, source: str, target: str) -> RelationDef | None:
        for rel in self._relations:
            if rel.source == source and rel.target == target:
                return rel
        return None

    def group_relations(self, group_name: str) -> list[RelationDef]:
        """Relations whose source resource belongs to the given group."""
        group = self._groups.get(group_name)
        if not group:
            return []
        names = {res.name for res in group.resources}
        return [r for r in self._relations if r.source in names]


# ── Global registry instance ───────────────────────────────────────

registry = ResourceRegistry()


def discover_modules():
    """Import all resource modules so they register themselves.

    Called once at application startup (e.g. in AppConfig.ready()).
    """
    from resource_modules.ec2.resource import COMPUTE_GROUP as ec2_group
    from resource_modules.vpc.resource import NETWORK_GROUP as vpc_group
    from resource_modules.rds.resource import STORAGE_GROUP as rds_group

    registry.register_group(ResourceGroupDef(name="计算", resources=ec2_group))
    registry.register_group(ResourceGroupDef(name="网络", resources=vpc_group))
    registry.register_group(ResourceGroupDef(name="存储", resources=rds_group))

    # Future modules:
    # from resource_modules.iam.resource import SECURITY_GROUP as iam_group
    # registry.register_group(ResourceGroupDef(name="安全", resources=iam_group))
    # from resource_modules.ebs.resource import STORAGE_GROUP as ebs_group
    # registry.register_group(ResourceGroupDef(name="存储", resources=ebs_group))
