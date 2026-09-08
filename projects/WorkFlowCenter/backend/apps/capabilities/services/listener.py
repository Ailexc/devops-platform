"""
Celery 任务：Redis Streams 消费者 & TaskJob 结果处理

在异步模式下，能力执行的结果通过 Redis Streams 传递，
由 Celery worker 消费并触发流程引擎推进。
"""
import json
import logging

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def process_job_result(self, job_id: str):
    """
    处理单个 TaskJob 执行结果。
    1. 查询 TaskJob
    2. 如果成功，推进流程引擎
    3. 如果失败，记录错误
    """
    from apps.capabilities.models import TaskJob
    from apps.processes.services.engine import ProcessEngine
    from apps.processes.models import NodeTask, ProcessInstance

    try:
        job = TaskJob.objects.select_related('instance', 'task', 'capability').get(job_id=job_id)
    except TaskJob.DoesNotExist:
        logger.error(f'process_job_result: TaskJob 不存在: {job_id}')
        return

    # 更新 NodeTask 状态
    node_task = job.task
    instance = job.instance

    if job.status == TaskJob.Status.SUCCEEDED:
        node_task.status = NodeTask.Status.COMPLETED
        node_task.result = 'success'
        node_task.save(update_fields=['status', 'result', 'updated_at'])

        # 推进到下一个节点
        next_node_key = ProcessEngine._resolve_next_node(
            instance, node_task.node_key, instance.variables
        )
        if next_node_key:
            instance.current_node_key = next_node_key
            instance.save(update_fields=['current_node_key', 'updated_at'])
            ProcessEngine._advance(instance, instance.variables)

        logger.info(f'Job 成功处理: {job_id}, instance={instance.instance_no}')

    elif job.status == TaskJob.Status.FAILED:
        node_task.status = NodeTask.Status.COMPLETED
        node_task.result = 'failed'
        node_task.opinion = job.error_message
        node_task.save(update_fields=['status', 'result', 'opinion', 'updated_at'])

        # 服务调用失败 → 终止实例
        instance.status = ProcessInstance.Status.TERMINATED
        instance.ended_at = timezone.now()
        instance.save(update_fields=['status', 'ended_at', 'updated_at'])

        logger.warning(f'Job 失败导致流程终止: {job_id}, instance={instance.instance_no}')


@shared_task(bind=True, max_retries=5, default_retry_delay=3)
def listen_job_results(self):
    """
    消费能力执行结果。
    Demo 模式下能力同步执行，无需 Redis Streams 消费。
    保留此任务定义以兼容真实异步场景。
    """
    logger.info('listen_job_results: Demo 模式下能力同步执行，跳过 Redis Streams 消费')


@shared_task
def execute_capability_task(job_id: str):
    """
    Celery 异步任务：执行能力。
    由流程引擎在创建 service 类型节点任务时触发。
    """
    from apps.capabilities.services.executor import default_executor
    from apps.capabilities.models import TaskJob

    try:
        job = TaskJob.objects.select_related('capability').get(job_id=job_id)
    except TaskJob.DoesNotExist:
        logger.error(f'execute_capability_task: TaskJob 不存在: {job_id}')
        return

    output = default_executor.execute_capability(
        job_id=job_id,
        capability_code=job.capability.code,
        input_data=job.input_data,
    )

    # 执行完成后触发结果处理
    process_job_result.delay(job_id)
