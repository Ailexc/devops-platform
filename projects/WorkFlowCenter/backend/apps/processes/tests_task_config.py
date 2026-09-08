from unittest import mock

from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.capabilities.models import Capability
from apps.processes.models import NodeTask, ProcessDefinition, ProcessInstance
from apps.processes.services.definition_convert import normalized_definition
from apps.processes.services.engine import ProcessEngine

User = get_user_model()


def make_capability(code, name, input_schema=None, output_schema=None):
    return Capability.objects.create(
        code=code,
        name=name,
        input_schema=input_schema or {'type': 'object', 'properties': {}},
        output_schema=output_schema or {'type': 'object', 'properties': {}},
    )


def make_auto_definition(actions, execution_mode='sequential', transactor_users=None):
    transactors = [
        {'rid': i, 'transactorType': 4, 'assignees': [u.id]}
        for i, u in enumerate(transactor_users or [])
    ]
    return {
        'nodes': [
            {'key': 'start', 'type': 'start', 'name': '开始'},
            {
                'key': 'auto_handle',
                'type': 'handle',
                'name': '自动办理',
                'transactors': transactors,
                'taskConfig': {
                    'mode': 'auto',
                    'executionMode': execution_mode,
                    'actions': actions,
                },
            },
            {'key': 'end', 'type': 'end', 'name': '结束'},
        ],
        'edges': [
            {'from': 'start', 'to': 'auto_handle'},
            {'from': 'auto_handle', 'to': 'end'},
        ],
    }


class DefinitionConvertTest(TestCase):
    """设计器树形格式 → 引擎平铺格式"""

    def test_tree_to_flat(self):
        definition = {
            'nodeConfig': {
                'key': 'start', 'name': '开始', 'type': 0,
                'childNode': {
                    'key': 'approve', 'name': '审批', 'type': 1,
                    'childNode': {
                        'key': 'handle', 'name': '办理', 'type': 5,
                        'taskConfig': {'mode': 'auto'},
                        'childNode': {
                            'key': 'end', 'name': '结束', 'type': 9,
                        },
                    },
                },
            },
        }
        flow = normalized_definition(definition)
        self.assertEqual([n['key'] for n in flow['nodes']], ['start', 'approve', 'handle', 'end'])
        self.assertEqual([n['type'] for n in flow['nodes']], ['start', 'approve', 'handle', 'end'])
        self.assertEqual(
            {(e['from'], e['to']) for e in flow['edges']},
            {('start', 'approve'), ('approve', 'handle'), ('handle', 'end')},
        )
        self.assertEqual(flow['nodes'][2]['taskConfig']['mode'], 'auto')

    def test_tree_gateway(self):
        definition = {
            'nodeConfig': {
                'key': 'start', 'name': '开始', 'type': 0,
                'childNode': {
                    'key': 'gw', 'name': '条件', 'type': 4,
                    'conditionNodes': [
                        {
                            'key': 'b1', 'name': '金额大', 'type': 3,
                            'conditionGroups': [{
                                'conditions': [{'varName': 'amount', 'operator': 2, 'val': 10000}],
                            }],
                            'childNode': {'key': 'after', 'name': '汇合', 'type': 1, 'childNode': {'key': 'end', 'name': '结束', 'type': 9}},
                        },
                        {'key': 'b2', 'name': '默认', 'type': 3, 'conditionGroups': [], 'childNode': None},
                    ],
                    'childNode': {'key': 'after', 'name': '汇合', 'type': 1, 'childNode': {'key': 'end', 'name': '结束', 'type': 9}},
                },
            },
        }
        flow = normalized_definition(definition)
        edge_map = {(e['from'], e['to']): e.get('condition') for e in flow['edges']}
        self.assertEqual(edge_map[('gw', 'b1')], 'amount > 10000')
        self.assertIsNone(edge_map[('gw', 'b2')])
        # 分支汇入网关 childNode
        self.assertEqual(edge_map.get(('b2', 'after')), None)

    def test_flat_passthrough(self):
        flat = {'nodes': [{'key': 'a', 'type': 'approve'}], 'edges': []}
        self.assertIs(normalized_definition(flat), flat)


class TaskConfigEngineTest(TestCase):
    """任务配置自动执行：串行 / 并行 / 异常 / 重新执行"""

    def setUp(self):
        self.user = User.objects.create_user(username='initiator', password='pass')
        self.h1 = User.objects.create_user(username='h1', password='pass')
        self.h2 = User.objects.create_user(username='h2', password='pass')
        self.cmdb = make_capability(
            'cmdb.create_host', '创建主机',
            input_schema={
                'type': 'object',
                'required': ['hostname'],
                'properties': {
                    'hostname': {'type': 'string'},
                    'cpu': {'type': 'integer'},
                    'memory': {'type': 'integer'},
                    'os': {'type': 'string'},
                },
            },
            output_schema={'type': 'object', 'properties': {'host_id': {'type': 'string'}}},
        )
        self.mail = make_capability(
            'mail.send', '发送通知',
            input_schema={
                'type': 'object',
                'properties': {
                    'to': {'type': 'array', 'items': {'type': 'string'}},
                    'subject': {'type': 'string'},
                    'body': {'type': 'string'},
                },
            },
        )

    def _actions(self):
        return [
            {
                'key': 'act_create_host',
                'name': '创建主机',
                'capabilityId': self.cmdb.id,
                'capabilityCode': 'cmdb.create_host',
                'fieldBindings': [
                    {'capabilityField': 'hostname', 'source': 'form', 'formField': 'hostname'},
                    {'capabilityField': 'cpu', 'source': 'form', 'formField': 'cpu'},
                ],
            },
            {
                'key': 'act_send_mail',
                'name': '发送通知',
                'capabilityId': self.mail.id,
                'capabilityCode': 'mail.send',
                'fieldBindings': [
                    {'capabilityField': 'to', 'source': 'form', 'formField': 'email'},
                    {'capabilityField': 'subject', 'source': 'constant', 'constant': '开通通知'},
                    {'capabilityField': 'body', 'source': 'previous', 'previousActionKey': 'act_create_host', 'previousField': 'host_id'},
                ],
            },
        ]

    def _start(self, execution_mode):
        definition = ProcessDefinition.objects.create(
            key='auto_%s' % execution_mode,
            name='自动流程',
            status=ProcessDefinition.Status.PUBLISHED,
            definition_json=make_auto_definition(
                self._actions(), execution_mode, [self.h1, self.h2],
            ),
        )
        return ProcessEngine.start(
            definition=definition,
            form_data={'hostname': 'web-01', 'cpu': 4, 'email': 'ops@example.com'},
            started_by=self.user,
        )

    def test_sequential_success(self):
        instance = self._start('sequential')
        self.assertEqual(instance.status, ProcessInstance.Status.COMPLETED)
        node_task = NodeTask.objects.get(instance=instance, node_key='auto_handle')
        self.assertEqual(node_task.status, NodeTask.Status.COMPLETED)
        self.assertIn(node_task.assignee_id, [self.h1.id, self.h2.id])  # 代理随机从办理人中选
        jobs = list(instance.task_jobs.order_by('created_at'))
        self.assertEqual(len(jobs), 2)
        self.assertTrue(all(j.status == 'succeeded' for j in jobs))
        self.assertTrue(all(j.logs for j in jobs))  # 每个任务都有日志
        # 串行：第二个动作引用了前序输出
        mail_job = jobs[1]
        self.assertEqual(mail_job.input_data.get('body'), 'mock-host-001')
        # 节点输出已保存
        outputs = (instance.variables or {}).get('_node_outputs', {}).get('auto_handle', {})
        self.assertEqual(outputs.get('act_create_host', {}).get('host_id'), 'mock-host-001')

    def test_parallel_success(self):
        instance = self._start('parallel')
        self.assertEqual(instance.status, ProcessInstance.Status.COMPLETED)
        jobs = list(instance.task_jobs.all())
        self.assertEqual(len(jobs), 2)
        self.assertTrue(all(j.status == 'succeeded' for j in jobs))

    def test_parallel_partial_failure_abnormal(self):
        actions = self._actions()
        actions[1]['capabilityCode'] = 'mail.fail'
        definition = ProcessDefinition.objects.create(
            key='auto_fail',
            name='失败流程',
            status=ProcessDefinition.Status.PUBLISHED,
            definition_json=make_auto_definition(actions, 'parallel', [self.h1, self.h2]),
        )
        real_execute = None
        from apps.capabilities.services import executor as executor_module
        from apps.capabilities.models import TaskJob
        real_execute = executor_module.default_executor.execute_capability

        def fake_execute(job_id, capability_code='', input_data=None):
            job = TaskJob.objects.get(job_id=job_id)
            if job.action_key == 'act_send_mail':
                raise RuntimeError('模拟能力失败')
            return real_execute(job_id=job_id, capability_code=capability_code, input_data=input_data)

        with mock.patch.object(executor_module.default_executor, 'execute_capability', side_effect=fake_execute):
            instance = ProcessEngine.start(
                definition=definition,
                form_data={'hostname': 'web-01', 'cpu': 4, 'email': 'ops@example.com'},
                started_by=self.user,
            )

        # 并行：等待全部完成后统一判定，有失败则节点异常，流程暂停
        self.assertEqual(instance.status, ProcessInstance.Status.RUNNING)
        self.assertEqual(instance.current_node_key, 'auto_handle')
        node_task = NodeTask.objects.get(instance=instance, node_key='auto_handle')
        self.assertEqual(node_task.status, NodeTask.Status.ABNORMAL)
        self.assertIn(node_task.assignee_id, [self.h1.id, self.h2.id])
        self.assertIn('模拟能力失败', node_task.opinion)
        # 已成功的动作输出保留
        outputs = (instance.variables or {}).get('_node_outputs', {}).get('auto_handle', {})
        self.assertEqual(outputs.get('act_create_host', {}).get('host_id'), 'mock-host-001')

    def test_rerun_failed_action(self):
        actions = self._actions()
        actions[1]['capabilityCode'] = 'mail.fail'
        definition = ProcessDefinition.objects.create(
            key='auto_rerun',
            name='重跑流程',
            status=ProcessDefinition.Status.PUBLISHED,
            definition_json=make_auto_definition(actions, 'sequential', [self.h1, self.h2]),
        )
        from apps.capabilities.services import executor as executor_module
        from apps.capabilities.models import TaskJob
        real_execute = executor_module.default_executor.execute_capability
        fail_once = {'done': False}

        def fake_execute(job_id, capability_code='', input_data=None):
            job = TaskJob.objects.get(job_id=job_id)
            if job.action_key == 'act_send_mail' and not fail_once['done']:
                fail_once['done'] = True
                raise RuntimeError('第一次失败')
            return real_execute(job_id=job_id, capability_code=capability_code, input_data=input_data)

        with mock.patch.object(executor_module.default_executor, 'execute_capability', side_effect=fake_execute):
            instance = ProcessEngine.start(
                definition=definition,
                form_data={'hostname': 'web-01', 'cpu': 4, 'email': 'ops@example.com'},
                started_by=self.user,
            )
            node_task = NodeTask.objects.get(instance=instance, node_key='auto_handle')
            self.assertEqual(node_task.status, NodeTask.Status.ABNORMAL)
            # 代理重新执行
            from apps.processes.services.task_runner import rerun_node_actions
            rerun_node_actions(instance, node_task)

        node_task.refresh_from_db()
        instance = ProcessInstance.objects.get(pk=instance.pk)
        self.assertEqual(node_task.status, NodeTask.Status.COMPLETED)
        self.assertEqual(instance.status, ProcessInstance.Status.COMPLETED)

    def test_confirm_mode(self):
        """自动执行+人工确认：先生成确认待办，确认后执行动作"""
        definition = make_auto_definition(self._actions(), 'sequential', [self.h1, self.h2])
        definition['nodes'][1]['taskConfig']['mode'] = 'confirm'
        defn = ProcessDefinition.objects.create(
            key='auto_confirm',
            name='确认流程',
            status=ProcessDefinition.Status.PUBLISHED,
            definition_json=definition,
        )
        instance = ProcessEngine.start(
            definition=defn,
            form_data={'hostname': 'web-01', 'cpu': 4, 'email': 'ops@example.com'},
            started_by=self.user,
        )
        # 确认待办已生成，随机办理人，指针停在节点
        node_task = NodeTask.objects.get(instance=instance, node_key='auto_handle')
        self.assertEqual(node_task.status, NodeTask.Status.PENDING)
        self.assertIn(node_task.assignee_id, [self.h1.id, self.h2.id])
        instance = ProcessInstance.objects.get(pk=instance.pk)
        self.assertEqual(instance.current_node_key, 'auto_handle')

        # 办理人确认（填写办理说明）→ 执行动作 → 完成
        confirm_user = User.objects.get(pk=node_task.assignee_id)
        ProcessEngine.complete(
            node_task.id, confirm_user, result='approve', opinion='已核对，确认执行',
        )
        node_task = NodeTask.objects.get(pk=node_task.pk)
        instance = ProcessInstance.objects.get(pk=instance.pk)
        self.assertEqual(node_task.status, NodeTask.Status.COMPLETED)
        self.assertEqual(instance.status, ProcessInstance.Status.COMPLETED)
        self.assertEqual(instance.task_jobs.count(), 2)
        # 办理说明进入审批记录
        from apps.processes.models import ApprovalRecord
        record = ApprovalRecord.objects.filter(task=node_task, action='approve').first()
        self.assertEqual(record.opinion, '已核对，确认执行')

    def test_confirm_mode_failure(self):
        """确认后动作失败 → 节点异常，确认人接管"""
        actions = self._actions()
        definition = make_auto_definition(actions, 'sequential', [self.h1, self.h2])
        definition['nodes'][1]['taskConfig']['mode'] = 'confirm'
        defn = ProcessDefinition.objects.create(
            key='auto_confirm_fail',
            name='确认失败流程',
            status=ProcessDefinition.Status.PUBLISHED,
            definition_json=definition,
        )
        from apps.capabilities.services import executor as executor_module
        from apps.capabilities.models import TaskJob
        real_execute = executor_module.default_executor.execute_capability

        def fake_execute(job_id, capability_code='', input_data=None):
            job = TaskJob.objects.get(job_id=job_id)
            if job.action_key == 'act_send_mail':
                raise RuntimeError('确认后执行失败')
            return real_execute(job_id=job_id, capability_code=capability_code, input_data=input_data)

        with mock.patch.object(executor_module.default_executor, 'execute_capability', side_effect=fake_execute):
            instance = ProcessEngine.start(
                definition=defn,
                form_data={'hostname': 'web-01', 'cpu': 4, 'email': 'ops@example.com'},
                started_by=self.user,
            )
            node_task = NodeTask.objects.get(instance=instance, node_key='auto_handle')
            confirm_user = User.objects.get(pk=node_task.assignee_id)
            ProcessEngine.complete(node_task.id, confirm_user, result='approve', opinion='确认执行')

        node_task = NodeTask.objects.get(pk=node_task.pk)
        instance = ProcessInstance.objects.get(pk=instance.pk)
        self.assertEqual(node_task.status, NodeTask.Status.ABNORMAL)
        self.assertEqual(node_task.assignee_id, confirm_user.id)
        self.assertEqual(instance.status, ProcessInstance.Status.RUNNING)
        self.assertEqual(instance.current_node_key, 'auto_handle')
