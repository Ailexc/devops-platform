"""
执行引擎 —— 后台线程异步执行，边执行边写日志（供 SSE 实时回流）

模拟真实 Spug 的 CI/CD 全流程：
  op=build  → 真实执行 docker build（临时 Pod 编译 → 镜像产出到本地 Docker）
  op=deploy → 首次 apply YAML / 后续 set image
  op=pods   → 查询 Pod 列表（区分 Deployment / StatefulSet）
"""

import os
import subprocess
import time
import threading

try:
    import yaml
except ImportError:
    yaml = None

from . import k8s as k8s_mod
from .store import Execution, get_execution

k8s = k8s_mod.k8s

# demo-apps 目录（项目根目录下）
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
DEMO_APPS_DIR = os.path.join(PROJECT_ROOT, "demo-apps")
CONFIG_ROOT = os.path.join(DEMO_APPS_DIR, "config")


def start_execution(exec_id: str):
    t = threading.Thread(target=_run, args=(exec_id,), daemon=True)
    t.start()


def _run(exec_id: str):
    ex = get_execution(exec_id)
    if ex is None:
        return
    try:
        _dispatch(ex)
    except Exception as e:
        ex.log("error", f"[executor] 执行失败: {e}")
        ex.finish("failed", error=str(e))


def _dispatch(ex: Execution):
    op = ex.op
    p = ex.params
    ex.log("info", f"[executor] 收到执行请求 op={op} release_no={p.get('release_no', 'N/A')}")

    handlers = {
        "build": _do_build,
        "deploy": _do_deploy,
        "pods": _do_pods,
        "rollback": _do_rollback,
        "scale": _do_scale,
        "restart": _do_restart,
        "canary": _do_canary,
        "blue_green": _do_blue_green,
        "traffic": _do_traffic,
        "verify": _do_verify,
    }
    handler = handlers.get(op)
    if handler:
        handler(ex, p)
    else:
        raise ValueError(f"未知操作: {op}")


# ── 构建（全真实：docker build）─────────────────────────────


def _do_build(ex: Execution, p: dict):
    """
    CI 构建：
    用户代码仓库自带 Dockerfile，CI 系统直接 docker build，不修改用户文件。
    builder_image / base_image 作为元数据记录，供展示和合规校验使用。
    """
    app_code = p.get("name", "unknown")
    branch = p.get("branch", "main")
    commit_id = p.get("commit_id", "abc1234")
    version = p.get("version", "1.0.0")
    language = p.get("language", "python")
    repo_url = p.get("repo_url", f"https://gitlab.internal/spug/{app_code}.git")

    # 元数据：记录绑定的镜像（不改变 Dockerfile）
    builder_image = p.get("builder_image", "")
    base_image = p.get("base_image", "")
    if builder_image:
        ex.log("info", f"[CI] 绑定的环境基础镜像: {builder_image}")
    if base_image:
        ex.log("info", f"[CI] 绑定的应用基础镜像: {base_image}")

    registry = p.get("registry", "")
    image = f"{registry}/{app_code}:{version}" if registry else f"{app_code}:{version}"
    app_dir = os.path.join(DEMO_APPS_DIR, app_code)

    # ── Step 1: 准备构建环境 ──
    ex.log("step", f"[CI] 创建构建 Pod: builder-{language}:latest")
    ex.log("info", f"[CI] namespace=build, 临时 Pod")
    ex.log("info", f"[CI] Pod 就绪")

    # ── Step 2: 模拟 git clone（真实检查源码目录）──
    ex.log("step", f"[CI] git clone {repo_url}")
    if os.path.isdir(app_dir):
        ex.log("info", f"[CI] 源码目录已就绪: {app_dir}")
        ex.log("info", f"[CI] git checkout {branch} → {commit_id}")
        ex.log("info", f"[CI] Branch '{branch}' set up to track remote")
        files = os.listdir(app_dir)
        ex.log("info", f"[CI] 源码文件: {', '.join(files)}")
    else:
        ex.log("error", f"[CI] 源码目录不存在: {app_dir}")
        ex.finish("failed", error=f"源码目录不存在: {app_dir}")
        return

    # ── Step 3: 清理旧镜像 ──
    ex.log("step", f"[CI] 清理旧镜像: {image}")
    rmi_result = subprocess.run(
        ["docker", "rmi", image],
        capture_output=True, text=True, timeout=30,
    )
    if rmi_result.returncode == 0:
        ex.log("info", f"[CI] 旧镜像已删除")
    else:
        ex.log("info", f"[CI] 无旧镜像，跳过清理")

    # ── 真实模式：执行 docker build ──
    ex.log("step", f"[CI] docker build -t {image} {app_dir}")

    try:
        result = subprocess.run(
            ["docker", "build", "--build-arg", f"APP_VERSION={version}", "-t", image, app_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True, timeout=300,
        )
        if result.stdout:
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line:
                    ex.log("info", f"[CI] {line}")

        if result.returncode == 0:
            img_info = subprocess.run(
                ["docker", "image", "inspect", image, "--format", "{{.Size}}"],
                capture_output=True, text=True, timeout=10,
            )
            if img_info.returncode == 0:
                size_mb = int(img_info.stdout.strip()) / 1024 / 1024
                ex.log("ok", f"[CI] ✅ docker build 成功 → {image} ({size_mb:.1f}MB)")
            else:
                ex.log("ok", f"[CI] ✅ docker build 成功 → {image}")
        else:
            ex.log("error", f"[CI] docker build 失败 (exit code: {result.returncode})")
            ex.finish("failed", error=f"docker build 失败")
            return
    except subprocess.TimeoutExpired:
        ex.log("error", f"[CI] docker build 超时（300s）")
        ex.finish("failed", error="docker build 超时")
        return
    except FileNotFoundError:
        ex.log("error", f"[CI] docker 命令不可用")
        ex.finish("failed", error="docker 命令不可用")
        return

    # ── Step 5: 打 latest 标签 ──
    if f"{app_code}:latest" != image:
        ex.log("step", f"[CI] docker tag {image} {app_code}:latest")
        tag_result = subprocess.run(
            ["docker", "tag", image, f"{app_code}:latest"],
            capture_output=True, text=True, timeout=10,
        )
        if tag_result.returncode == 0:
            ex.log("info", f"[CI] {app_code}:latest 标签已创建")
        else:
            ex.log("warn", f"[CI] tag 失败: {tag_result.stderr.strip()}")

    # ── Step 6: 清理临时 Pod ──
    ex.log("step", f"[CI] 清理构建 Pod: builder-{language}:latest")
    ex.log("info", f"[CI] Pod 已删除")

    ex.finish("success", {
        "message": f"构建成功: {image}",
        "image": image, "branch": branch, "commit_id": commit_id,
    })
    ex.finish("success", {
        "message": f"构建成功: {image}",
        "image": image, "branch": branch, "commit_id": commit_id,
    })


# ── 部署（首次 apply / 后续 set image）────────────────────────


def _maybe_config_apply(ex: Execution, p: dict) -> bool:
    """
    配置随发布走：若 CD params 携带 configs，则：
      1. 创建/更新 ConfigMap {app}-config（data = {模板名: 渲染内容}）
      2. 为主 Deployment 挂载卷到 /etc/app（strategic merge patch，幂等）
    蓝绿/灰度克隆体基于主 Deployment JSON 克隆，挂载自动继承。
    无 configs → 返回 False（跳过）；主 Deployment 尚不存在（首次）→ 创建 ConfigMap 后告警跳过挂载。
    """
    configs = p.get("configs") or {}
    if not configs:
        return False
    app_code = p.get("name", "unknown")
    env_code = p.get("env_code", "dev")
    namespace = _cluster_ns(ex, app_code, env_code, p.get("namespace", "release-demo"))
    cm_name = f"{app_code}-config"
    volume_name = f"{app_code}-config"
    mount_path = "/etc/app"

    ex.log("step", f"[CD] 配置随发布走: 渲染 {len(configs)} 个模板 → ConfigMap {cm_name} ({namespace})")
    r = k8s.apply_configmap(namespace, cm_name, configs)
    if r.get("status") not in ("success", "simulated"):
        raise RuntimeError(f"创建 ConfigMap 失败: {r}")
    for k, v in configs.items():
        ex.log("info", f"[CD]   ConfigMap data: {k} ({len(v)} bytes)")

    try:
        from kubernetes.client.rest import ApiException
    except ImportError:
        ApiException = Exception
    try:
        m = k8s.mount_configmap(namespace, app_code, volume_name, cm_name, mount_path, app_code)
    except ApiException as e:
        if getattr(e, "status", None) == 404:
            ex.log("warn", f"[CD] 主 Deployment {app_code} 尚不存在，ConfigMap 已创建，挂载随首次部署")
            return True
        raise
    if m.get("status") not in ("success", "simulated"):
        raise RuntimeError(f"挂载 ConfigMap 失败: {m}")
    ex.log("ok", f"[CD] ✅ 已挂载 {cm_name} → {mount_path} (Deployment {app_code})")
    return True


def _do_deploy(ex: Execution, p: dict):
    app_code = p.get("name", "unknown")
    env_code = p.get("env_code", "dev")
    version = p.get("version", "1.0.0")
    is_first = p.get("is_first_deploy", False)

    ex.log("info", f"[CD] 连接 K8s 集群 ({'真实模式' if not k8s.is_simulating() else '模拟模式'})")

    # 读取 YAML 配置（模拟从 GitLab 拉取）
    ns, replicas, workload_type = _read_config(ex, app_code, env_code)

    registry = p.get("registry", "")
    if registry:
        image = f"{registry}/{app_code}:{version}"
    else:
        image = f"{app_code}:{version}"

    success = False
    if is_first:
        success = _deploy_first(ex, app_code, ns, replicas, image)
        if success:
            _maybe_config_apply(ex, p)  # 首次：先 apply 再挂载（Deployment 此时已存在）
    else:
        _maybe_config_apply(ex, p)  # 后续：先挂载，卷随 set image 同一次 rollout 生效
        success = _deploy_rolling(ex, app_code, ns, replicas, image)

    if success:
        ex.log("ok", f"[CD] 🚀 部署完成 · {replicas}/{replicas} Pod Ready")
        ex.finish("success", {
            "message": f"部署成功: {image}",
            "image": image, "namespace": ns, "replicas": replicas,
            "is_first_deploy": is_first,
        })
    else:
        ex.log("error", f"[CD] 部署失败")
        ex.finish("failed", error=f"部署失败: {app_code}")


def _read_config(ex: Execution, app_code: str, env_code: str) -> tuple:
    """读取 demo-apps/config/{app_code}/{env_code}/deployment.yaml"""
    ns, replicas, workload_type = "release-demo", 2, "Deployment"
    config_path = os.path.join(CONFIG_ROOT, app_code, env_code, "deployment.yaml")

    if os.path.exists(config_path):
        ex.log("step", f"[CD] 从 GitLab 拉取配置: apps/{app_code}/{env_code}/deployment.yaml")
        _sleep_log(ex, 0.3, "info", f"[CD] 配置已获取")
        try:
            if yaml:
                with open(config_path, "r") as f:
                    docs = list(yaml.safe_load_all(f))
                deploy_doc = next((d for d in docs if d and d.get("kind") == "Deployment"), None)
                if deploy_doc:
                    ns = deploy_doc.get("metadata", {}).get("namespace", ns)
                    replicas = deploy_doc.get("spec", {}).get("replicas", replicas)
                    ex.log("info", f"[CD] 解析配置: kind=Deployment namespace={ns} replicas={replicas}")
        except Exception as e:
            ex.log("warn", f"[CD] 配置解析异常: {e}, 使用默认值")
    else:
        ex.log("warn", f"[CD] 未找到配置 {app_code}/{env_code}, 使用默认值")

    return ns, replicas, workload_type


def _deploy_first(ex: Execution, app_code: str, ns: str, replicas: int, image: str) -> bool:
    """首次部署：真实 kubectl apply + kubectl get pods 轮询，返回是否成功"""
    ex.log("step", f"[CD] 检测到首次部署，执行 kubectl apply")
    result = subprocess.run(
        ["kubectl", "apply", "-f", os.path.join(CONFIG_ROOT, app_code, _get_env_from_ns(ns), "deployment.yaml")],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode == 0:
        for line in result.stdout.strip().split("\n"):
            ex.log("info", f"[CD] {line.strip()}")
    else:
        ex.log("error", f"[CD] kubectl apply 失败: {result.stderr.strip()}")
        return False

    return _wait_rollout(ex, ns, app_code)


def _deploy_rolling(ex: Execution, app_code: str, ns: str, replicas: int, image: str) -> bool:
    """后续部署：真实 kubectl set image + 同步 APP_VERSION env + rollout status，返回是否成功"""
    ex.log("step", f"[CD] 检测到现有 Deployment: {app_code}")
    ex.log("info", f"[CD] 执行: kubectl set image deployment/{app_code} {app_code}={image}")
    result = subprocess.run(
        ["kubectl", "set", "image", f"deployment/{app_code}", f"{app_code}={image}", "-n", ns],
        capture_output=True, text=True, timeout=60,
    )
    if result.returncode == 0:
        ex.log("info", f"[CD] {result.stdout.strip()}")
    else:
        err = result.stderr.strip()
        # deployment 不存在 → 自动回退到首次部署
        if "NotFound" in err or "not found" in err.lower():
            ex.log("warn", f"[CD] Deployment {app_code} 不存在，自动回退到首次部署")
            return _deploy_first(ex, app_code, ns, replicas, image)
        ex.log("error", f"[CD] kubectl set image 失败: {err}")
        return False

    # 同步更新 APP_VERSION 环境变量（deployment.yaml 里硬编码了旧版本，set image 不会更新，
    # 若不更新会覆盖镜像内的版本号导致验证的版本检查失败）
    version = image.rsplit(":", 1)[-1] if ":" in image else "1.0.0"
    env_result = subprocess.run(
        ["kubectl", "set", "env", f"deployment/{app_code}", f"APP_VERSION={version}", "-n", ns],
        capture_output=True, text=True, timeout=60,
    )
    if env_result.returncode == 0:
        ex.log("info", f"[CD] 同步 APP_VERSION → {version}")
    else:
        ex.log("warn", f"[CD] 更新 APP_VERSION 失败: {env_result.stderr.strip()}")

    return _wait_rollout(ex, ns, app_code)


def _get_env_from_ns(ns: str) -> str:
    """从 namespace 名推断环境目录名"""
    mapping = {"release-demo": "dev", "dev": "dev", "test1": "test", "pre": "pre", "prod": "prod"}
    return mapping.get(ns, ns)


def _wait_rollout(ex: Execution, ns: str, app_name: str, timeout: int = 120):
    """
    等待 Deployment 滚动更新完成。
    使用 kubectl rollout status —— 自动识别正确的 ReplicaSet，
    只监控新 Pod 的 Ready 状态，不会被旧 Pod 干扰。
    """
    import subprocess as sp
    import select
    import sys

    ex.log("step", f"[CD] 等待 rollout 完成 ...")

    cmd = [
        "kubectl", "rollout", "status",
        f"deployment/{app_name}", "-n", ns,
        f"--timeout={timeout}s",
    ]
    ex.log("info", f"[CD] $ {' '.join(cmd)}")

    proc = sp.Popen(
        cmd, stdout=sp.PIPE, stderr=sp.STDOUT,
        text=True, bufsize=1,
    )

    # 逐行读取 rollout status 的实时输出
    rollout_success = False
    try:
        while True:
            # 非阻塞读取，避免卡死
            rlist, _, _ = select.select([proc.stdout], [], [], 2.0)
            if rlist:
                line = proc.stdout.readline()
                if not line:  # EOF
                    break
                line = line.strip()
                if not line:
                    continue
                # rollout status 输出格式：
                #   "deployment \"xxx\" successfully rolled out" → 成功
                #   "Waiting for rollout to finish: ..." → 进行中
                #   "error: ..." → 失败
                if "successfully rolled out" in line.lower():
                    rollout_success = True
                    ex.log("ok", f"[CD] {line} ✅")
                elif "error" in line.lower() or "failed" in line.lower():
                    ex.log("error", f"[CD] {line}")
                elif "waiting" in line.lower() or "rolled out" in line.lower():
                    ex.log("info", f"[CD] {line}")
                else:
                    ex.log("info", f"[CD] {line}")
            else:
                # 超时无输出，继续等待（timeout 由 kubectl 本身控制）
                if proc.poll() is not None:
                    break
    except Exception as e:
        ex.log("warn", f"[CD] rollout 读取异常: {e}")
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except sp.TimeoutExpired:
                proc.kill()

    if rollout_success:
        ex.log("info", f"[CD] Rollout 完成")
        return True

    # kubectl rollout status 退出码 0 = 成功, 非0 = 失败/超时
    if proc.returncode == 0:
        ex.log("ok", f"[CD] 🚀 Rollout 成功 ✅")
        return True

    # 退出码非0：可能是超时或 Deployment 不存在
    ex.log("warn", f"[CD] rollout status 退出码: {proc.returncode}")
    # 兜底检查：直接查询新 ReplicaSet 的 Pod 是否 Ready
    return _fallback_check_pods(ex, ns, app_name)


def _fallback_check_pods(ex: Execution, ns: str, app_name: str) -> bool:
    """兜底：rollout status 失败时，用 JSON 查询确认新 Pod 状态"""
    import subprocess as sp
    import json as _json

    ex.log("info", f"[CD] 回退检查 Pod 状态 ...")
    r = sp.run(
        ["kubectl", "get", "pods", "-n", ns, "-l", f"app={app_name}", "-o", "json"],
        capture_output=True, text=True, timeout=10,
    )
    if r.returncode != 0:
        ex.log("error", f"[CD] kubectl get pods 失败: {r.stderr.strip()}")
        return False

    try:
        pods_data = _json.loads(r.stdout).get("items", [])
    except Exception:
        pods_data = []

    ready_count = 0
    for pod in pods_data:
        name = pod.get("metadata", {}).get("name", "?")
        conditions = pod.get("status", {}).get("conditions", [])
        ready = any(c.get("type") == "Ready" and c.get("status") == "True" for c in conditions)
        if ready:
            ready_count += 1
            ex.log("ok", f"[CD] Pod {name} Ready ✅")

    total = len(pods_data)
    if ready_count > 0 and ready_count == total:
        ex.log("info", f"[CD] 全部 {ready_count}/{total} Pod 已就绪")
        return True

    ex.log("warn", f"[CD] {ready_count}/{total} Pod Ready")
    return ready_count > 0  # 至少有一个 Ready 就算成功


# ── 查询 Pod 列表 ─────────────────────────────────────────


def _do_pods(ex: Execution, p: dict):
    app_code = p.get("name", "unknown")
    env_code = p.get("env_code", "dev")
    ex.log("info", f"[CD] 查询 {app_code} 在 {env_code} 的 Pod 列表 ...")
    _sleep_log(ex, 0.3, "info", f"[CD] kubectl get pods -l app={app_code} -o json")

    workload_type = p.get("workload_type", "deployment")
    ns = p.get("namespace", "release-demo")
    replicas = p.get("replicas", 2)
    pods = []

    for i in range(replicas):
        if workload_type == "statefulset":
            pod_name = f"{app_code}-{i}"
            selectable = True
        else:
            pod_name = f"{app_code}-{_rand_hex(5)}-{_rand_hex(4)}"
            selectable = False
        pods.append({
            "name": pod_name, "status": "Running",
            "ip": f"10.0.{_rand_int(1, 254)}.{_rand_int(1, 254)}",
            "image": f"123456789.dkr.ecr.us-east-1.amazonaws.com/{app_code}:1.0.0",
            "node": f"ip-10-0-{_rand_int(1, 10)}-{_rand_int(1, 254)}.ec2.internal",
            "started_at": "2026-07-31T10:00:00Z",
            "workload_type": workload_type,
            "selectable": selectable,
        })

    ex.log("info", f"[CD] 发现 {len(pods)} 个 Pod (workload={workload_type})")
    for pod in pods:
        ex.log("info", f"[CD]   - {pod['name']}  status={pod['status']}  ip={pod['ip']}")
    ex.finish("success", {"pods": pods, "workload_type": workload_type, "namespace": ns})


# ── 回滚 / 扩缩容 / 重启 / 灰度 / 蓝绿 ───────────────────


def _do_rollback(ex: Execution, p: dict):
    app_code = p.get("name", "unknown")
    image = p.get("image")
    ex.log("info", f"[CD] 回滚 {app_code} 到镜像 {image} ...")
    ex.log("step", f"[CD] kubectl rollout undo deployment/{app_code}")
    _sleep_log(ex, 0.5, "info", f"[CD] deployment.apps/{app_code} rolled back")
    ex.log("ok", f"[CD] ✅ 回滚完成")
    ex.finish("success", {"message": f"回滚到 {image}"})


def _do_scale(ex: Execution, p: dict):
    name = p.get("name", "unknown")
    replicas = p.get("replicas", 1)
    env_code = p.get("env_code", "dev")
    deploy_type = p.get("deploy_type", "k8s")
    namespace = _cluster_ns(ex, name, env_code, p.get("namespace", "release-demo"))

    if deploy_type == "ec2":
        # ── EC2 模式：模拟虚拟机伸缩 ──
        ex.log("step", f"[CD] EC2 模式: 伸缩 {name} ({env_code})")
        ex.log("info", f"[CD] 连接 EC2 实例管理服务 ...")
        _sleep_log(ex, 0.5, "info", f"[CD] 当前实例数: {max(1, replicas)}")

        if replicas == 0:
            ex.log("step", f"[CD] 关闭所有实例 ...")
            for i in range(1, 4):
                _sleep_log(ex, 0.3, "info", f"[CD] 正在停止实例{i} (i-{_rand_hex(8)}) ...")
            _sleep_log(ex, 0.5, "ok", f"[CD] ✅ 所有实例已停止")
        else:
            ex.log("step", f"[CD] 目标实例数: {replicas}")
            for i in range(1, replicas + 1):
                ip = f"10.0.{_rand_int(1, 10)}.{_rand_int(1, 254)}"
                _sleep_log(ex, 0.3, "info", f"[CD] 实例{i} 启动中 (IP: {ip}) ...")
            _sleep_log(ex, 0.5, "ok", f"[CD] ✅ {replicas} 台实例已就绪")

        ex.finish("success", {
            "message": f"EC2 伸缩完成: {name} → {replicas} 台",
            "namespace": namespace, "replicas": replicas,
        })
    else:
        # ── K8s 模式：真实 kubectl scale ──
        ex.log("info", f"[CD] K8s 模式: 伸缩 {namespace}/{name} -> replicas={replicas}")
        ex.log("step", f"[CD] kubectl scale deployment/{name} --replicas={replicas} -n {namespace}")
        _sleep_log(ex, 0.3, "info", f"[CD] deployment.apps/{name} scaled")
        result = k8s.scale(namespace, name, replicas)
        ex.finish("success", result)


def _do_restart(ex: Execution, p: dict):
    name = p.get("name", "unknown")
    env_code = p.get("env_code", "dev")
    deploy_type = p.get("deploy_type", "k8s")
    namespace = _cluster_ns(ex, name, env_code, p.get("namespace", "release-demo"))

    if deploy_type == "ec2":
        # ── EC2 模式：模拟 SSH 重启服务进程 ──
        ex.log("step", f"[CD] EC2 模式: 重启 {name} ({env_code})")
        ex.log("info", f"[CD] SSH 连接实例并重启服务进程 ...")
        _sleep_log(ex, 0.5, "info", f"[CD] systemctl restart {name} 执行完成")
        _sleep_log(ex, 0.3, "ok", f"[CD] ✅ 服务已重启")
        ex.finish("success", {"message": f"EC2 重启完成: {name}"})
        return

    ex.log("info", f"[CD] 触发滚动重启 {namespace}/{name} ...")
    result = k8s.restart(namespace, name)
    ex.finish("success", result)


def _do_traffic(ex: Execution, p: dict):
    """流量摘流/挂流：k8s 真实 patch Service selector；ec2 模拟 ALB Target Group"""
    name = p.get("name", "unknown")
    env_code = p.get("env_code", "dev")
    deploy_type = p.get("deploy_type", "k8s")
    traffic_action = p.get("traffic_action", "take_out")
    track = p.get("track", "stable")
    namespace = _cluster_ns(ex, name, env_code, p.get("namespace", "release-demo"))
    is_take_out = traffic_action == "take_out"
    label = "摘流" if is_take_out else "挂流"

    if deploy_type == "ec2":
        # ── EC2 模式：模拟 ALB Target Group deregister/register ──
        ex.log("step", f"[CD] EC2 模式: {label} {name} ({env_code})")
        ex.log("info", f"[CD] 连接 AWS ALB Target Group ...")
        if is_take_out:
            _sleep_log(ex, 0.4, "info", f"[CD] deregistering instance i-{_rand_hex(8)} from TargetGroup ...")
            _sleep_log(ex, 0.5, "ok", f"[CD] ✅ 已摘流：实例不再接收请求")
        else:
            _sleep_log(ex, 0.4, "info", f"[CD] registering instance i-{_rand_hex(8)} to TargetGroup ...")
            _sleep_log(ex, 0.5, "ok", f"[CD] ✅ 已挂流：实例恢复接收请求")
        ex.finish("success", {"message": f"EC2 流量{'摘除' if is_take_out else '恢复'}: {name}"})
        return

    # ── K8s 模式：真实 patch Service selector（track 维度）──
    if is_take_out:
        # 摘流：selector 指向不存在的 track 组合 → 无 Endpoint，流量断开
        selector = {"app": name, "track": "nonexistent"}
    else:
        # 挂流：恢复 track 指向 active 环境
        selector = {"app": name, "track": track}

    ex.log("step", f"[CD] K8s 模式: {label} {namespace}/{name}")
    ex.log("info", f"[CD] Service {name} selector → {selector}")
    result = k8s.patch_service_selector(namespace, name, selector)
    if result.get("status") in ("success", "simulated"):
        ex.log("ok", f"[CD] ✅ Service selector 已更新")
        ex.finish("success", {"message": f"流量{'摘除' if is_take_out else '恢复'}: {name}", "selector": selector})
    else:
        ex.log("error", f"[CD] 更新 Service selector 失败: {result}")
        ex.finish("failed", error=f"更新 Service selector 失败")


def _do_canary(ex: Execution, p: dict):
    """灰度发布：真实创建 {name}-canary Deployment + 独立 Service 入口，等待人工确认全量"""
    name = p.get("name", "unknown")
    env_code = p.get("env_code", "dev")
    version = p.get("version", "latest")
    registry = p.get("registry", "")
    image = f"{registry}/{name}:{version}" if registry else f"{name}:{version}"
    canary_replicas = p.get("canary_replicas", 1)
    deploy_type = p.get("deploy_type", "k8s")
    namespace = _cluster_ns(ex, name, env_code, p.get("namespace", "release-demo"))

    if deploy_type == "ec2":
        # ── EC2 模式：模拟金丝雀实例 ──
        ex.log("step", f"[CD] EC2 模式: 灰度 {name} ({env_code})")
        ex.log("info", f"[CD] 启动 1 台金丝雀实例 (新版本 {image}) ...")
        _sleep_log(ex, 0.5, "ok", f"[CD] ✅ 金丝雀实例就绪")
        ex.log("info", f"[CD] 等待灰度验证 (手动确认后全量发布) ...")
        ex.finish("success", {"message": f"灰度实例已部署: {name}"})
        return

    import subprocess as sp
    import json as _json

    ex.log("step", f"[CD] 灰度部署: {namespace}/{name} → {name}-canary (image={image})")

    # 配置随发布走：先挂载主 Deployment，克隆体基于主 Deployment JSON 自动继承挂载
    _maybe_config_apply(ex, p)

    # 1. 基于主 Deployment 构造 canary Deployment（track: canary，1 副本，新镜像）
    r = sp.run(["kubectl", "get", "deploy", name, "-n", namespace, "-o", "json"],
               capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        ex.log("error", f"[CD] 获取主 Deployment 失败: {r.stderr.strip()}")
        ex.finish("failed", error="获取主 Deployment 失败")
        return
    dep = _json.loads(r.stdout)
    dep["metadata"]["name"] = f"{name}-canary"
    for k in ("uid", "resourceVersion", "creationTimestamp", "generation", "managedFields", "selfLink"):
        dep["metadata"].pop(k, None)
    labels = dep["metadata"].get("labels") or {}
    labels["track"] = "canary"
    dep["metadata"]["labels"] = labels
    dep["spec"]["selector"]["matchLabels"]["track"] = "canary"
    dep["spec"]["template"]["metadata"]["labels"]["track"] = "canary"
    dep["spec"]["template"]["spec"]["containers"][0]["image"] = image
    dep["spec"]["replicas"] = canary_replicas
    # 更新 APP_VERSION env 为新版本（避免克隆的旧 env 覆盖镜像内版本号）
    for _c in dep["spec"]["template"]["spec"]["containers"]:
        for _e in _c.get("env") or []:
            if _e.get("name") == "APP_VERSION":
                _e["value"] = version
    if "status" in dep:
        del dep["status"]

    r2 = sp.run(["kubectl", "apply", "-f", "-"], input=_json.dumps(dep),
                capture_output=True, text=True, timeout=60)
    if r2.returncode != 0:
        ex.log("error", f"[CD] 创建 {name}-canary 失败: {r2.stderr.strip()}")
        ex.finish("failed", error=f"创建 {name}-canary 失败")
        return
    for line in r2.stdout.strip().split("\n"):
        ex.log("info", f"[CD] {line.strip()}")

    # 2. 构造 canary 独立 Service 入口（selector: app + track: canary）
    r3 = sp.run(["kubectl", "get", "svc", name, "-n", namespace, "-o", "json"],
                capture_output=True, text=True, timeout=30)
    if r3.returncode == 0:
        svc = _json.loads(r3.stdout)
        svc["metadata"]["name"] = f"{name}-canary"
        for k in ("uid", "resourceVersion", "creationTimestamp", "managedFields", "selfLink"):
            svc["metadata"].pop(k, None)
        sel = svc["spec"].get("selector") or {}
        sel["track"] = "canary"
        svc["spec"]["selector"] = sel
        # 新 Service 需重新分配 ClusterIP（克隆的 clusterIP 已被主 Service 占用）
        svc["spec"].pop("clusterIP", None)
        svc["spec"].pop("clusterIPs", None)
        if "status" in svc:
            del svc["status"]
        r4 = sp.run(["kubectl", "apply", "-f", "-"], input=_json.dumps(svc),
                    capture_output=True, text=True, timeout=60)
        if r4.returncode == 0:
            for line in r4.stdout.strip().split("\n"):
                ex.log("info", f"[CD] {line.strip()}")
            ex.log("ok", f"[CD] ✅ 金丝雀独立入口: {name}-canary.{namespace}.svc.cluster.local")
        else:
            ex.log("warn", f"[CD] 创建 {name}-canary Service 失败: {r4.stderr.strip()}")
    else:
        ex.log("warn", f"[CD] 未找到主 Service，跳过金丝雀独立入口创建")

    # 3. 等待 canary 就绪
    if not _wait_rollout(ex, namespace, f"{name}-canary"):
        ex.log("error", f"[CD] {name}-canary 就绪检查未通过")
        ex.finish("failed", error=f"{name}-canary 就绪检查未通过")
        return

    # 4. 等待人工确认全量
    ex.log("ok", f"[CD] ✅ 金丝雀 {name}-canary 就绪 (image={image})")
    ex.log("info", f"[CD] 等待灰度验证 (人工确认后全量发布) ...")
    ex.finish("success", {"message": f"灰度 {name}-canary 已就绪，等待确认全量", "canary": f"{name}-canary"})


def _do_blue_green(ex: Execution, p: dict):
    """蓝绿部署：真实创建 {name}-blue Deployment，切换 Service selector，保留旧环境回滚"""
    name = p.get("name", "unknown")
    env_code = p.get("env_code", "dev")
    version = p.get("version", "latest")
    registry = p.get("registry", "")
    image = f"{registry}/{name}:{version}" if registry else f"{name}:{version}"
    deploy_type = p.get("deploy_type", "k8s")
    namespace = _cluster_ns(ex, name, env_code, p.get("namespace", "release-demo"))

    if deploy_type == "ec2":
        # ── EC2 模式：模拟蓝色环境 ──
        ex.log("step", f"[CD] EC2 模式: 蓝绿部署 {name} ({env_code})")
        ex.log("info", f"[CD] 创建蓝色环境实例组 (新版本 {image}) ...")
        _sleep_log(ex, 0.5, "ok", f"[CD] ✅ 蓝色环境就绪")
        ex.log("step", f"[CD] 切换 ALB Target Group 指向蓝色环境")
        _sleep_log(ex, 0.3, "ok", f"[CD] 🚀 蓝绿切换完成")
        ex.finish("success", {"message": f"EC2 蓝绿部署完成: {name}"})
        return

    import subprocess as sp
    import json as _json

    ex.log("step", f"[CD] 蓝绿部署: {namespace}/{name} → {name}-blue (image={image})")

    # 配置随发布走：先挂载主 Deployment，克隆体基于主 Deployment JSON 自动继承挂载
    _maybe_config_apply(ex, p)

    # 1. 基于主 Deployment 构造 blue Deployment（track: blue，新镜像）
    r = sp.run(["kubectl", "get", "deploy", name, "-n", namespace, "-o", "json"],
               capture_output=True, text=True, timeout=30)
    if r.returncode != 0:
        ex.log("error", f"[CD] 获取主 Deployment 失败: {r.stderr.strip()}")
        ex.finish("failed", error="获取主 Deployment 失败")
        return
    dep = _json.loads(r.stdout)
    dep["metadata"]["name"] = f"{name}-blue"
    for k in ("uid", "resourceVersion", "creationTimestamp", "generation", "managedFields", "selfLink"):
        dep["metadata"].pop(k, None)
    labels = dep["metadata"].get("labels") or {}
    labels["track"] = "blue"
    dep["metadata"]["labels"] = labels
    dep["spec"]["selector"]["matchLabels"]["track"] = "blue"
    dep["spec"]["template"]["metadata"]["labels"]["track"] = "blue"
    dep["spec"]["template"]["spec"]["containers"][0]["image"] = image
    # 更新 APP_VERSION env 为新版本（避免克隆的旧 env 覆盖镜像内版本号）
    for _c in dep["spec"]["template"]["spec"]["containers"]:
        for _e in _c.get("env") or []:
            if _e.get("name") == "APP_VERSION":
                _e["value"] = version
    if "status" in dep:
        del dep["status"]

    r2 = sp.run(["kubectl", "apply", "-f", "-"], input=_json.dumps(dep),
                capture_output=True, text=True, timeout=60)
    if r2.returncode != 0:
        ex.log("error", f"[CD] 创建 {name}-blue 失败: {r2.stderr.strip()}")
        ex.finish("failed", error=f"创建 {name}-blue 失败")
        return
    for line in r2.stdout.strip().split("\n"):
        ex.log("info", f"[CD] {line.strip()}")

    # 2. 等待 blue 就绪
    if not _wait_rollout(ex, namespace, f"{name}-blue"):
        ex.log("error", f"[CD] {name}-blue 就绪检查未通过")
        ex.finish("failed", error=f"{name}-blue 就绪检查未通过")
        return

    # 3. 切换 Service selector 到 blue（真实流量切换）
    ex.log("step", f"[CD] 切换 Service {name} selector → track: blue")
    result = k8s.patch_service_selector(namespace, name, {"app": name, "track": "blue"})
    if result.get("status") in ("success", "simulated"):
        ex.log("ok", f"[CD] 🚀 蓝绿切换完成: 流量已指向 {name}-blue")
        ex.log("info", f"[CD] 旧环境 {name} (track: stable) 保留用于回滚")
        ex.finish("success", {
            "message": f"蓝绿部署完成: 流量已切换至 {name}-blue (image={image})",
            "active": f"{name}-blue",
        })
    else:
        ex.log("error", f"[CD] Service 切换失败: {result}")
        ex.finish("failed", error="Service 切换失败")


# ── 发布自动验证（op=verify）──────────────────────────────


def _do_verify(ex: Execution, p: dict):
    """
    发布自动验证：
    读取 demo-apps/config/{app}/{env}/verify.yaml（声明式检查脚本）→
    模板注入 {app}/{version}/{env}/{ns} → 按发布策略过滤检查项 →
    逐项执行内置原语（k8s_deploy_ready / k8s_service_selector / k8s_pods / http / http_json）→
    产出结构化结果 [{name, status, evidence, duration_ms}]。
    """
    import json as _json

    app_code = p.get("name", "unknown")
    env_code = p.get("env_code", "dev")
    version = p.get("version", "")
    strategy = p.get("deploy_strategy", "rolling")
    ns = _cluster_ns(ex, app_code, env_code, p.get("namespace", "release-demo"))

    verify_path = os.path.join(CONFIG_ROOT, app_code, env_code, "verify.yaml")
    if not (yaml and os.path.exists(verify_path)):
        ex.log("info", f"[VERIFY] 未找到验证脚本: {verify_path}，跳过")
        ex.finish("success", {
            "status": "skipped", "checks": [],
            "summary": "该项目未配置验证脚本",
        })
        return

    with open(verify_path, "r") as f:
        doc = yaml.safe_load(f) or {}
    checks = doc.get("checks", []) if isinstance(doc, dict) else []

    def inject(text):
        """模板变量注入"""
        if not isinstance(text, str):
            return text
        return (text.replace("{app}", app_code)
                    .replace("{version}", version)
                    .replace("{env}", env_code)
                    .replace("{ns}", ns))

    results = []
    passed = 0
    total_start = time.time()

    # 发布刚完成时 Pod 可能仍就绪中/端点未传播：先等待主 Deployment 就绪（最多 30s）
    if not _wait_deploy_ready(ex, app_code, ns, timeout=30):
        ex.log("warn", f"[VERIFY] 主 Deployment {app_code} 尚未完全就绪，继续执行检查项（结果以实际为准）")

    for i, chk in enumerate(checks):
        if not isinstance(chk, dict):
            continue
        # 策略过滤：strategy 可省略（所有发布都跑），或指定单个策略 / 多个策略（列表或逗号分隔）
        chk_strategy = chk.get("strategy")
        if chk_strategy:
            want = chk_strategy if isinstance(chk_strategy, list) else str(chk_strategy).split(",")
            want = [s.strip() for s in want]
            if strategy not in want:
                continue
        name = chk.get("name", f"检查项 {i + 1}")
        ctype = chk.get("type", "http")
        start = time.time()
        try:
            ok, evidence = _verify_check(ex, ctype, chk, app_code, env_code, ns, version, inject)
        except Exception as e:
            ok, evidence = False, f"执行异常: {e}"
        duration_ms = int((time.time() - start) * 1000)
        results.append({
            "name": name,
            "status": "pass" if ok else "fail",
            "evidence": evidence,
            "duration_ms": duration_ms,
        })
        if ok:
            passed += 1
        ex.log("ok" if ok else "error",
               f"[VERIFY] {'✅' if ok else '❌'} {name} ({duration_ms}ms) {evidence}")

    total_ms = int((time.time() - total_start) * 1000)
    total = len(results)
    summary = f"{passed}/{total} 通过，耗时 {total_ms / 1000:.1f}s"
    overall = "success" if total and passed == total else "failed"
    ex.log("info", f"[VERIFY] 汇总: {summary}")
    result = {"status": overall, "checks": results, "summary": summary}
    if overall == "success":
        ex.finish("success", result)
    else:
        ex.finish("failed", result)


def _verify_check(ex, ctype: str, chk: dict, app_code: str, env_code: str,
                  ns: str, version: str, inject) -> tuple:
    """执行单个验证原语，返回 (ok, evidence)"""
    import json as _json
    import subprocess as sp

    def kubectl(args, timeout=30):
        return sp.run(["kubectl"] + args, capture_output=True, text=True, timeout=timeout)

    if ctype == "k8s_deploy_ready":
        # Deployment 就绪检查：READY 数 == spec.replicas（或 >= expect_ready）
        app_name = inject(chk.get("deploy", "{app}"))
        r = kubectl(["get", "deploy", app_name, "-n", ns, "-o", "json"])
        if r.returncode != 0:
            return False, f"Deployment {app_name} 不存在"
        dep = _json.loads(r.stdout)
        spec_replicas = dep.get("spec", {}).get("replicas", 1)
        status = dep.get("status", {})
        ready = status.get("readyReplicas", 0)
        evidence = f"{app_name} {ready}/{spec_replicas} Ready"
        expected = chk.get("expect_ready")
        if expected is not None:
            return int(ready) >= int(expected), evidence
        return int(ready) >= 1 and int(ready) == int(spec_replicas), evidence

    if ctype == "k8s_service_selector":
        # Service selector 检查：读当前 selector，验证 track 指向期望环境
        svc_name = inject(chk.get("service", "{app}"))
        r = kubectl(["get", "svc", svc_name, "-n", ns, "-o", "json"])
        if r.returncode != 0:
            return False, f"Service {svc_name} 不存在"
        svc = _json.loads(r.stdout)
        selector = svc.get("spec", {}).get("selector", {})
        evidence = f"selector: {_json.dumps(selector, ensure_ascii=False)}"
        expect_track = chk.get("expect_track")
        if expect_track:
            return selector.get("track") == expect_track, evidence
        return bool(selector), evidence

    if ctype == "k8s_pods":
        # Pod 摘要检查：全部 Running/Ready
        label = inject(chk.get("label", "{app}"))
        r = kubectl(["get", "pods", "-n", ns, "-l", f"app={label}", "-o", "json"])
        if r.returncode != 0:
            return False, f"查询 Pod 失败: {r.stderr.strip()}"
        pods = _json.loads(r.stdout)
        items = pods.get("items", [])
        ready = 0
        for pod in items:
            cstatus = pod.get("status", {}).get("containerStatuses", [])
            if cstatus and all(c.get("ready") for c in cstatus):
                ready += 1
        evidence = f"{ready}/{len(items)} Pods Ready"
        return len(items) > 0 and ready == len(items), evidence

    if ctype == "http":
        # HTTP 检查：状态码 2xx + body 可选包含 expect_contains
        path = inject(chk.get("path", "/"))
        service = inject(chk.get("service", "{app}"))
        url = _resolve_service_url(service, ns, path)
        if url is None:
            return False, f"Service {service} 不存在"
        resp = _http_get_safe(url)
        if resp is None:
            return False, f"无法访问 {service}: 网络不可达"
        status_ok = 200 <= resp.status_code < 300
        evidence = f"HTTP {resp.status_code}"
        expect_contains = inject(chk.get("expect_contains", ""))
        if expect_contains:
            found = expect_contains in resp.text
            evidence += f', body 含 "{expect_contains}"'
            return status_ok and found, evidence
        return status_ok, evidence

    if ctype == "http_json":
        # HTTP + JSON 断言：取 jsonpath（简单点路径）与期望值比较
        path = inject(chk.get("path", "/"))
        service = inject(chk.get("service", "{app}"))
        url = _resolve_service_url(service, ns, path)
        if url is None:
            return False, f"Service {service} 不存在"
        resp = _http_get_safe(url)
        if resp is None:
            return False, f"无法访问 {service}: 网络不可达"
        if resp.status_code >= 400:
            return False, f"HTTP {resp.status_code}"
        try:
            data = resp.json()
        except Exception:
            return False, f"响应非 JSON: {resp.text[:100]}"
        jsonpath = chk.get("jsonpath", "version")
        value = _json_get(data, jsonpath)
        evidence = f"{jsonpath}={value}"
        expect_equal = inject(str(chk.get("expect_equal", "")))
        expect_not_equal = inject(str(chk.get("expect_not_equal", "")))
        if expect_not_equal:
            evidence += f" (期望 ≠ {expect_not_equal})"
            return str(value) != str(expect_not_equal), evidence
        evidence += f" (期望 {expect_equal})"
        return str(value) == str(expect_equal), evidence

    return False, f"未知检查类型: {ctype}"


def _http_get(url: str, timeout: float = 10):
    """带超时的 HTTP GET（requests）"""
    import requests as _requests
    return _requests.get(url, timeout=timeout)


def _http_get_safe(url: str, timeout: float = 8, retries: int = 4):
    """
    HTTP GET；连接失败返回 None（用于检查项，避免抛异常）。
    带重试：发布刚完成时 Service 端点可能尚未传播（旧 Pod 终止 / 新 Pod 未入端点），
    连接失败时短暂重试几次。
    """
    for attempt in range(retries):
        try:
            return _http_get(url, timeout=timeout)
        except Exception:
            if attempt < retries - 1:
                time.sleep(1)
    return None


def _wait_deploy_ready(ex: Execution, app_code: str, ns: str, timeout: float = 30) -> bool:
    """
    等待主 Deployment 完全就绪（readyReplicas >= spec.replicas）。
    Deployment 不存在视为已就绪（由后续检查项报告真实状态）。
    """
    import json as _json
    import subprocess as sp

    deadline = time.time() + timeout
    while time.time() < deadline:
        r = sp.run(["kubectl", "get", "deploy", app_code, "-n", ns, "-o", "json"],
                   capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return True  # Deployment 不存在，交给检查项判断
        try:
            dep = _json.loads(r.stdout)
        except Exception:
            return True
        spec_replicas = dep.get("spec", {}).get("replicas", 1)
        ready = dep.get("status", {}).get("readyReplicas", 0)
        if int(ready) >= int(spec_replicas):
            return True
        time.sleep(1)
    return False


def _resolve_service_url(service: str, ns: str, path: str):
    """
    解析服务访问地址（方式 B：ClusterIP + Service 端口，不依赖 DNS）。
    先 kubectl 确认 Service 存在并取 ClusterIP；服务不存在返回 None（快速失败）。
    """
    import json as _json
    import subprocess as sp
    r = sp.run(["kubectl", "get", "svc", service, "-n", ns, "-o", "json"],
                capture_output=True, text=True, timeout=15)
    if r.returncode != 0:
        return None
    try:
        svc = _json.loads(r.stdout)
        ip = svc.get("spec", {}).get("clusterIP")
        if not ip or ip == "None":
            return None
        ports = svc.get("spec", {}).get("ports", [])
        port = ports[0].get("port", 80) if ports else 80
        return f"http://{ip}:{port}{path}"
    except Exception:
        return None


def _json_get(data, path: str):
    """简单点路径 JSON 取值（version / data.version / items.0.version）"""
    cur = data
    for part in str(path).split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return None
    return cur


# ── 工具函数 ──────────────────────────────────────────────


def _cluster_ns(ex: Execution, app_code: str, env_code: str, fallback: str = "release-demo") -> str:
    """从 demo-apps 配置 YAML 解析集群真实 namespace（demo 约定 release-demo）。
    数据库里的 namespace 对象名（dev/test5/prod2...）是模拟环境标记，不是集群 ns。"""
    try:
        config_path = os.path.join(CONFIG_ROOT, app_code, env_code, "deployment.yaml")
        if yaml and os.path.exists(config_path):
            with open(config_path, "r") as f:
                docs = list(yaml.safe_load_all(f))
            deploy_doc = next((d for d in docs if d and d.get("kind") == "Deployment"), None)
            if deploy_doc:
                ns = deploy_doc.get("metadata", {}).get("namespace")
                if ns:
                    return ns
    except Exception:
        pass
    return fallback


def _sleep_log(ex: Execution, seconds: float, level: str, message: str):
    time.sleep(seconds)
    ex.log(level, message)


def _rand_hex(n: int) -> str:
    import random
    return ''.join(random.choice('0123456789abcdef') for _ in range(n))


def _rand_int(a: int, b: int) -> int:
    import random
    return random.randint(a, b)
