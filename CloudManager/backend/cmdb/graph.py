"""
图谱服务：基于云管元数据整合视图构建"应用 -> 服务 -> 资源 -> 端点"分层图谱。

定位：云管只做整合与展示，不负责数据采集；数据准确性由采集系统 + CMDB 保证。
本模块提供：应用全景、邻居展开、影响面分析、路径查询、连通性推导。
"""
from collections import deque

from django.db.models import Count
from django.db.models import Q

from .models import (
    Application, Resource, ResourceRelation, ServiceInstance, ServiceEndpoint, SecurityRule,
    Environment,
)


CATEGORY_META = {
    'application': {'label': '应用', 'color': '#7C3AED'},
    'environment': {'label': '环境', 'color': '#EC4899'},
    'service': {'label': '服务', 'color': '#3B82F6'},
    'resource': {'label': '资源', 'color': '#10B981'},
    'endpoint': {'label': '端点', 'color': '#F59E0B'},
}


def _node(nid, name, category, **meta):
    return {'id': nid, 'name': name, 'category': category, 'meta': meta}


def _app_node(app: Application):
    return _node(f'app:{app.id}', app.name, 'application',
                 department=app.department.name if app.department else '-',
                 owner=app.owner or '-')


def _env_node(env: Environment):
    return _node(f'env:{env.id}', env.name, 'environment',
                 env_type=env.get_env_type_display(),
                 account=env.account.account_name if env.account else '-',
                 region=env.region or '-')


def _service_node(svc: ServiceInstance):
    return _node(f'svc:{svc.id}', svc.name, 'service',
                 service_type=svc.get_service_type_display(),
                 deploy_type=svc.get_deploy_type_display(),
                 status=svc.status, region=svc.region or '-',
                 environment=svc.environment.name if svc.environment else '-')


def _service_deployed(svc: ServiceInstance):
    """服务部署的实例/集群资源（多实例优先，回退主资源）"""
    deployed = list(svc.resources.all()) if svc.resources.exists() else []
    if not deployed and svc.resource_id:
        deployed = [svc.resource]
    return deployed


def _service_edges(svc: ServiceInstance, parent_id: str, nodes: list, core_resource_ids: set):
    """服务节点 + 部署资源节点/边 + 端点节点/边，返回生成的边"""
    edges = []
    deployed = _service_deployed(svc)
    nodes.append(_service_node(svc))
    edges.append(_edge(parent_id, f'svc:{svc.id}', 'contains', 'hard'))
    svc_node = nodes[-1]
    svc_node['meta']['instance_count'] = len(deployed)
    svc_node['meta']['instances'] = [
        {'id': r.id, 'name': r.resource_name, 'spec': r.spec, 'status': r.status}
        for r in deployed
    ]
    for res in deployed:
        core_resource_ids.add(res.id)
        edges.append(_edge(f'svc:{svc.id}', f'res:{res.id}', 'deployed_on', 'hard'))
    for ep in svc.endpoints.all():
        nodes.append(_endpoint_node(ep))
        edges.append(_edge(f'svc:{svc.id}', f'ep:{ep.id}', 'exposes', 'hard'))
    return edges


def _resource_node(res: Resource):
    return _node(f'res:{res.id}', res.resource_name, 'resource',
                 resource_type=res.resource_type, status=res.status,
                 region=res.region, spec=res.spec or '-',
                 provider=res.provider_type, cloud_id=res.cloud_resource_id,
                 managed_by=res.managed_by or 'cloud')


def _endpoint_node(ep: ServiceEndpoint):
    return _node(f'ep:{ep.id}', ep.domain or f'{ep.protocol}:{ep.port}', 'endpoint',
                 protocol=ep.protocol, port=ep.port, is_public=ep.is_public)


def _edge(source, target, relation_type, strength='hard', label=''):
    return {'source': source, 'target': target, 'relation_type': relation_type,
            'strength': strength, 'label': label or relation_type}


def _resource_edges(resource_ids):
    """返回两端都在给定资源集合内的资源关系边"""
    edges = []
    relations = ResourceRelation.objects.filter(
        source_id__in=resource_ids, target_id__in=resource_ids
    ).select_related('source', 'target')
    for rel in relations:
        edges.append(_edge(
            f'res:{rel.source_id}', f'res:{rel.target_id}',
            rel.relation_type, rel.strength,
        ))
    return edges


def list_applications():
    """应用列表（含服务数/资源数/关系数统计）"""
    result = []
    for app in Application.objects.prefetch_related('services', 'environments').all():
        services = list(app.services.all())
        resource_ids = set()
        for svc in services:
            if svc.resource_id:
                resource_ids.add(svc.resource_id)
        resource_ids.update(
            Resource.objects.filter(application=app).values_list('id', flat=True)
        )
        relations_count = ResourceRelation.objects.filter(
            Q(source_id__in=resource_ids) | Q(target_id__in=resource_ids)
        ).count() if resource_ids else 0
        result.append({
            'id': app.id,
            'name': app.name,
            'department': app.department.name if app.department else '-',
            'owner': app.owner or '-',
            'description': app.description or '',
            'services_count': len(services),
            'environments_count': app.environments.count(),
            'resources_count': len(resource_ids),
            'relations_count': relations_count,
        })
    return result


def organization_tree():
    """组织架构树：部门 -> 应用（含环境数）"""
    from accounts.models import Department

    dept_map = {
        d.id: {'id': d.id, 'name': d.name, 'parent_id': d.parent_id,
               'children': [], 'applications': []}
        for d in Department.objects.all()
    }
    apps = Application.objects.filter(department_id__isnull=False).annotate(
        env_count=Count('environments')
    )
    for app in apps:
        node = dept_map.get(app.department_id)
        if node:
            node['applications'].append({
                'id': app.id,
                'name': app.name,
                'owner': app.owner or '-',
                'environments_count': app.env_count,
            })

    roots = []
    for dept in dept_map.values():
        node = {
            'id': dept['id'],
            'name': dept['name'],
            'applications': dept['applications'],
            'children': dept['children'],
        }
        parent = dept_map.get(dept['parent_id'])
        if parent:
            parent['children'].append(node)
        else:
            roots.append(node)
    return roots


def application_graph(app_id, environment_id=None):
    """应用全景图：应用 -> 环境 -> 服务 -> 资源（含一跳依赖）-> 端点"""
    app = Application.objects.prefetch_related(
        'environments', 'services__resource', 'services__endpoints'
    ).get(id=app_id)
    nodes = [_app_node(app)]
    edges = []
    core_resource_ids = set()
    services = app.services.all()
    if environment_id:
        services = services.filter(environment_id=environment_id)

    for svc in services:
        if svc.environment_id:
            env = app.environments.filter(id=svc.environment_id).first()
            if env:
                nodes.append(_env_node(env))
                edges.append(_edge(f'app:{app.id}', f'env:{env.id}', 'contains', 'hard'))
        env_id = svc.environment_id
        parent = f'env:{env_id}' if env_id else f'app:{app.id}'
        edges.extend(_service_edges(svc, parent, nodes, core_resource_ids))

    core_resource_ids.update(
        Resource.objects.filter(application=app).values_list('id', flat=True)
    )

    # 一跳邻居：把服务依赖的上下游资源（s3/kafka/nginx 等）纳入视图
    neighbor_ids = set()
    for rel in ResourceRelation.objects.filter(
        Q(source_id__in=core_resource_ids) | Q(target_id__in=core_resource_ids)
    ):
        if rel.source_id in core_resource_ids:
            neighbor_ids.add(rel.target_id)
        if rel.target_id in core_resource_ids:
            neighbor_ids.add(rel.source_id)

    all_ids = core_resource_ids | neighbor_ids
    for res in Resource.objects.filter(id__in=all_ids):
        nodes.append(_resource_node(res))
    edges.extend(_resource_edges(all_ids))

    return {'nodes': nodes, 'edges': edges}


def environment_graph(env_id):
    """环境详情图：环境 -> 服务 -> 资源（含一跳依赖）-> 端点"""
    env = Environment.objects.prefetch_related(
        'services__resource', 'services__endpoints'
    ).get(id=env_id)
    nodes = [_env_node(env), _app_node(env.application)]
    edges = [_edge(f'app:{env.application_id}', f'env:{env.id}', 'contains', 'hard')]
    core_resource_ids = set()

    for svc in env.services.all():
        edges.extend(_service_edges(svc, f'env:{env.id}', nodes, core_resource_ids))

    core_resource_ids.update(
        Resource.objects.filter(environment_id=env.id).values_list('id', flat=True)
    )
    neighbor_ids = set()
    for rel in ResourceRelation.objects.filter(
        Q(source_id__in=core_resource_ids) | Q(target_id__in=core_resource_ids)
    ):
        if rel.source_id in core_resource_ids:
            neighbor_ids.add(rel.target_id)
        if rel.target_id in core_resource_ids:
            neighbor_ids.add(rel.source_id)

    all_ids = core_resource_ids | neighbor_ids
    for res in Resource.objects.filter(id__in=all_ids):
        nodes.append(_resource_node(res))
    edges.extend(_resource_edges(all_ids))
    return {'nodes': nodes, 'edges': edges}


def resource_neighbors(resource_id, depth=1):
    """以资源为中心按需展开邻居（BFS）"""
    resource_ids = {resource_id}
    frontier = {resource_id}
    for _ in range(max(1, depth)):
        nxt = set()
        for rel in ResourceRelation.objects.filter(
            Q(source_id__in=frontier) | Q(target_id__in=frontier)
        ):
            if rel.source_id in frontier:
                nxt.add(rel.target_id)
            if rel.target_id in frontier:
                nxt.add(rel.source_id)
        resource_ids |= nxt
        frontier = nxt - resource_ids
        if not frontier:
            break

    nodes = [_resource_node(r) for r in Resource.objects.filter(id__in=resource_ids)]
    edges = _resource_edges(resource_ids)

    # 附带关联的服务/应用/端点（上层视图）
    svc_ids = set(ServiceInstance.objects.filter(resource_id__in=resource_ids).values_list('id', flat=True))
    for svc in ServiceInstance.objects.filter(id__in=svc_ids).select_related('application'):
        nodes.append(_service_node(svc))
        nodes.append(_app_node(svc.application))
        edges.append(_edge(f'app:{svc.application_id}', f'svc:{svc.id}', 'contains', 'hard'))
        edges.append(_edge(f'svc:{svc.id}', f'res:{svc.resource_id}', 'deployed_on', 'hard'))
        for ep in svc.endpoints.all():
            nodes.append(_endpoint_node(ep))
            edges.append(_edge(f'svc:{svc.id}', f'ep:{ep.id}', 'exposes', 'hard'))

    return {'nodes': nodes, 'edges': edges}


def _impact_adjacency():
    """
    构建影响方向邻接表。
    规则：
    - depends_on / hosted_on / deployed_on（A 依赖 B）：操作 B 影响 A（反向）
    - belongs_to_vpc / belongs_to_subnet（A 属于 B）：操作 B 影响 A（反向）
    - attach_sg（A 绑定 SG）：双向
    - communicates_with / bind_application / contains / belongs_to：双向
    """
    adj = {}
    for rel in ResourceRelation.objects.all():
        src, tgt = rel.source_id, rel.target_id
        rev_types = {'depends_on', 'hosted_on', 'deployed_on',
                     'belongs_to_vpc', 'belongs_to_subnet'}
        if rel.relation_type in rev_types:
            adj.setdefault(tgt, []).append((src, rel.relation_type, rel.strength))
        else:
            adj.setdefault(src, []).append((tgt, rel.relation_type, rel.strength))
            adj.setdefault(tgt, []).append((src, rel.relation_type, rel.strength))
    return adj


def impact_analysis(resource_id, max_depth=3):
    """影响面分析：BFS 沿影响方向遍历，输出影响链 + 严重度 + 单点依赖"""
    adj = _impact_adjacency()
    root = Resource.objects.get(id=resource_id)
    visited = {}
    queue = deque([(resource_id, 0, [], '')])

    while queue:
        cur, depth, path, rel_info = queue.popleft()
        if cur in visited or depth > max_depth:
            continue
        visited[cur] = {
            'depth': depth,
            'path': path,
            'relation_type': rel_info[0] if rel_info else '',
            'strength': rel_info[1] if rel_info else 'hard',
        }
        for nxt, rel_type, strength in adj.get(cur, []):
            if nxt not in visited:
                queue.append((nxt, depth + 1, path + [cur], (rel_type, strength)))

    nodes = []
    for res in Resource.objects.filter(id__in=visited.keys()).exclude(id=resource_id):
        info = visited[res.id]
        severity = 'high' if info['depth'] == 1 and info['strength'] == 'hard' \
            else 'medium' if info['depth'] == 1 else 'low'
        nodes.append({
            'id': f'res:{res.id}',
            'resource_id': res.id,
            'name': res.resource_name,
            'category': 'resource',
            'resource_type': res.resource_type,
            'status': res.status,
            'relation_type': info['relation_type'],
            'strength': info['strength'],
            'severity': severity,
            'depth': info['depth'],
            'path': info['path'],
        })

    # 单点依赖（SPOF）：被影响集合中仅被一个硬依赖引用的节点
    incoming = {}
    for rel in ResourceRelation.objects.filter(
        source_id__in=visited.keys(), target_id__in=visited.keys(), strength='hard'
    ):
        incoming.setdefault(rel.target_id, []).append(rel.source_id)
    spof = [
        n['name'] for n in nodes
        if n['resource_id'] in incoming and len(incoming[n['resource_id']]) == 1
    ]

    summary = {
        'high': len([n for n in nodes if n['severity'] == 'high']),
        'medium': len([n for n in nodes if n['severity'] == 'medium']),
        'low': len([n for n in nodes if n['severity'] == 'low']),
        'spof': spof,
    }
    return {
        'root': {'id': f'res:{root.id}', 'name': root.resource_name, 'resource_type': root.resource_type},
        'summary': summary,
        'nodes': nodes,
    }


def path_between(source_id, target_id):
    """最短路径查询（资源关系图 BFS）"""
    adj = {}
    for rel in ResourceRelation.objects.all():
        adj.setdefault(rel.source_id, []).append((rel.target_id, rel))
        adj.setdefault(rel.target_id, []).append((rel.source_id, rel))

    parent = {source_id: None}
    queue = deque([source_id])
    while queue:
        cur = queue.popleft()
        if cur == target_id:
            break
        for nxt, _rel in adj.get(cur, []):
            if nxt not in parent:
                parent[nxt] = cur
                queue.append(nxt)

    if target_id not in parent:
        return {'nodes': [], 'edges': [], 'reachable': False}

    path_ids = []
    cur = target_id
    while cur is not None:
        path_ids.append(cur)
        cur = parent[cur]
    path_ids.reverse()

    nodes = [_resource_node(r) for r in Resource.objects.filter(id__in=path_ids)]
    edges = []
    for a, b in zip(path_ids, path_ids[1:]):
        rel = ResourceRelation.objects.filter(
            Q(source_id=a, target_id=b) | Q(source_id=b, target_id=a)
        ).first()
        edges.append(_edge(f'res:{a}', f'res:{b}',
                           rel.relation_type if rel else 'connected',
                           rel.strength if rel else 'soft'))
    return {'nodes': nodes, 'edges': edges, 'reachable': True}


def connectivity(source_id, target_id):
    """网络连通性推导（规则级）：共享网络 + 安全组规则检查"""
    def ancestors(res_id):
        result = set()
        frontier = {res_id}
        while frontier:
            nxt = set()
            for rel in ResourceRelation.objects.filter(
                source_id__in=frontier, relation_type__in=('belongs_to_vpc', 'belongs_to_subnet')
            ):
                result.add(rel.target_id)
                nxt.add(rel.target_id)
            frontier = nxt - result
        return result

    src_anc, tgt_anc = ancestors(source_id), ancestors(target_id)
    shared = src_anc & tgt_anc
    if not shared:
        return {'reachable': False, 'verdict': 'isolated',
                'reason': '两个资源不在同一 VPC/子网网络内'}

    # 目标侧安全组是否有放行规则（含源 0.0.0.0/0 或同网段）
    sg_ids = set(ResourceRelation.objects.filter(
        source_id=target_id, relation_type='attach_sg'
    ).values_list('target_id', flat=True))
    rules = SecurityRule.objects.filter(
        security_group_id__in=sg_ids, direction='inbound', enabled=True,
        action='allow', port_range__in=('1-65535', '0-65535', '80', '443', '8080'),
    )
    if rules.exists():
        return {'reachable': True, 'verdict': 'reachable',
                'reason': '共享网络且安全组存在放行规则'}
    return {'reachable': False, 'verdict': 'blocked',
            'reason': '共享网络，但安全组无匹配放行规则'}
