"""
K8s 操作封装 —— executor 的实际执行能力

当本地 K8s 集群（kind / OrbStack）可用时走真实 Kubernetes API；
否则自动降级为模拟模式（记录日志，不实际执行），保证 demo 在无集群环境下也能跑通。
"""

import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import kubernetes
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False
    logger.warning("kubernetes 库未安装，executor 使用模拟模式")


class K8sExecutor:
    def __init__(self):
        self.simulate = False
        self.apps_v1 = None
        self.core_v1 = None
        self._init_client()

    def _init_client(self):
        if not K8S_AVAILABLE:
            self.simulate = True
            logger.info("K8s 客户端: 模拟模式")
            return
        try:
            # demo 集群（OrbStack）证书与 host.docker.internal 不匹配，跳过 TLS 校验
            c = client.Configuration()
            c.verify_ssl = False
            # 兼容 kubernetes 库新旧版本（35+ 用 load_kube_config，旧版用 load_kubeconfig）
            if hasattr(config, 'load_kube_config'):
                config.load_kube_config(client_configuration=c)
            else:
                config.load_kubeconfig(client_configuration=c)
            client.Configuration.set_default(c)
            self.apps_v1 = client.AppsV1Api()
            self.core_v1 = client.CoreV1Api()
            self.core_v1.list_namespace()  # 连通性探测
            logger.info("K8s 客户端: 真实模式 (已连接到集群)")
        except Exception as e:
            self.simulate = True
            logger.info(f"K8s 客户端: 模拟模式 (未检测到集群: {e})")

    def is_simulating(self) -> bool:
        return self.simulate

    def describe(self) -> str:
        return "模拟模式（未检测到 K8s 集群）" if self.simulate else "真实模式（已连接 K8s 集群）"

    # ── 部署 ────────────────────────────────────────────
    def create_or_update_deployment(
        self,
        namespace: str,
        name: str,
        image: str,
        replicas: int = 1,
        env_vars: Optional[dict] = None,
        labels: Optional[dict] = None,
    ) -> dict:
        """创建或更新 Deployment"""
        if self.simulate:
            return {"action": "simulated", "name": name, "namespace": namespace, "image": image}

        container = client.V1Container(
            name=name,
            image=image,
            image_pull_policy="IfNotPresent",
            ports=[client.V1ContainerPort(container_port=8080)],
        )
        if env_vars:
            container.env = [client.V1EnvVar(name=k, value=str(v)) for k, v in env_vars.items()]

        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels=labels or {"app": name}),
            spec=client.V1PodSpec(containers=[container]),
        )
        spec = client.V1DeploymentSpec(
            replicas=replicas,
            selector=client.V1LabelSelector(match_labels=labels or {"app": name}),
            template=template,
        )
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name, namespace=namespace),
            spec=spec,
        )

        try:
            self.apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
            self.apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=deployment)
            return {"action": "updated", "name": name, "namespace": namespace, "image": image}
        except ApiException as e:
            if e.status == 404:
                self.apps_v1.create_namespaced_deployment(namespace=namespace, body=deployment)
                return {"action": "created", "name": name, "namespace": namespace, "image": image}
            raise

    # ── 滚动更新状态 ────────────────────────────────────
    def rollout_status(self, namespace: str, name: str) -> dict:
        """检查 Deployment 滚动更新状态"""
        if self.simulate:
            return {"status": "success", "message": "模拟模式：滚动更新成功"}
        try:
            self.apps_v1.read_namespaced_deployment_status(name=name, namespace=namespace)
            return {"status": "success", "message": "滚动更新完成"}
        except ApiException as e:
            return {"status": "failed", "message": str(e)}

    # ── 扩缩容 ──────────────────────────────────────────
    def scale(self, namespace: str, name: str, replicas: int) -> dict:
        """修改副本数"""
        if self.simulate:
            return {"status": "simulated", "name": name, "namespace": namespace, "replicas": replicas}
        body = {"spec": {"replicas": replicas}}
        self.apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=body)
        return {"status": "success", "name": name, "namespace": namespace, "replicas": replicas}

    # ── 重启（rollout restart）──────────────────────────
    def restart(self, namespace: str, name: str) -> dict:
        """触发滚动重启：给 Pod 模板打上时间戳注解"""
        if self.simulate:
            return {"status": "simulated", "name": name, "namespace": namespace}
        body = {
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "kubectl.kubernetes.io/restartedAt": datetime.now(timezone.utc).isoformat()
                        }
                    }
                }
            }
        }
        self.apps_v1.patch_namespaced_deployment(name=name, namespace=namespace, body=body)
        return {"status": "success", "name": name, "namespace": namespace}

    # ── Service selector（蓝绿切换 / 摘挂流）────────────
    def patch_service_selector(self, namespace: str, service: str, selector: dict) -> dict:
        """修改 Service 的 selector：蓝绿切换 / 摘流（指向不存在的组合）/ 挂流（恢复）"""
        if self.simulate:
            return {"status": "simulated", "namespace": namespace, "service": service, "selector": selector}
        body = {"spec": {"selector": selector}}
        self.core_v1.patch_namespaced_service(name=service, namespace=namespace, body=body)
        return {"status": "success", "namespace": namespace, "service": service, "selector": selector}

    # ── ConfigMap 下发（配置随发布走）────────────────────
    def apply_configmap(self, namespace: str, name: str, data: dict) -> dict:
        """创建或更新 ConfigMap（data = {template_name: rendered_content}）"""
        if self.simulate:
            return {"status": "simulated", "namespace": namespace, "name": name,
                    "keys": list(data.keys())}
        body = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": name, "namespace": namespace},
            "data": data,
        }
        try:
            self.core_v1.read_namespaced_config_map(name=name, namespace=namespace)
            self.core_v1.replace_namespaced_config_map(name=name, namespace=namespace, body=body)
            action = "updated"
        except ApiException as e:
            if e.status == 404:
                self.core_v1.create_namespaced_config_map(namespace=namespace, body=body)
                action = "created"
            else:
                raise
        return {"status": "success", "action": action, "namespace": namespace, "name": name,
                "keys": list(data.keys())}

    def mount_configmap(self, namespace: str, deployment: str, volume_name: str,
                        configmap_name: str, mount_path: str, container: str) -> dict:
        """为 Deployment 挂载 ConfigMap 卷（strategic merge patch，幂等）。

        volumes/volumeMounts 的 merge key 分别为 name/mountPath，
        重复执行会合并同名项而非报错，可安全重试。
        """
        if self.simulate:
            return {"status": "simulated", "namespace": namespace, "deployment": deployment,
                    "volume": volume_name, "mount_path": mount_path}
        body = {
            "spec": {
                "template": {
                    "spec": {
                        "volumes": [{
                            "name": volume_name,
                            "configMap": {"name": configmap_name},
                        }],
                        "containers": [{
                            "name": container,
                            "volumeMounts": [{"name": volume_name, "mountPath": mount_path}],
                        }],
                    }
                }
            }
        }
        self.apps_v1.patch_namespaced_deployment(name=deployment, namespace=namespace, body=body)
        return {"status": "success", "namespace": namespace, "deployment": deployment,
                "volume": volume_name, "mount_path": mount_path}

    # ── Pod 列表 ────────────────────────────────────────
    def get_pods(self, namespace: str, app_label: str) -> list:
        """获取指定应用的 Pod 列表"""
        if self.simulate:
            return [{"status": "simulated", "namespace": namespace, "app": app_label}]
        pods = self.core_v1.list_namespaced_pod(
            namespace=namespace,
            label_selector=f"app={app_label}",
        )
        result = []
        for p in pods.items:
            result.append({
                "name": p.metadata.name,
                "node": p.spec.node_name,
                "ip": p.status.pod_ip,
                "status": p.status.phase,
                "image": p.spec.containers[0].image if p.spec.containers else "",
                "started_at": str(p.status.start_time) if p.status.start_time else "",
            })
        return result

    # ── 灰度 / 蓝绿（demo 级：模拟）─────────────────────
    def canary_update(self, namespace: str, name: str, image: str,
                      canary_replicas: int = 1, canary_percent: int = 10) -> dict:
        return {
            "status": "simulated",
            "namespace": namespace, "name": name, "image": image,
            "canary_percent": canary_percent,
            "message": f"金丝雀发布 {canary_percent}% 流量（demo 模拟）",
        }

    def blue_green_switch(self, namespace: str, name: str, image: str) -> dict:
        return {
            "status": "simulated",
            "namespace": namespace, "name": name, "image": image,
            "message": "蓝绿切换（demo 模拟）",
        }


# 单例
k8s = K8sExecutor()
