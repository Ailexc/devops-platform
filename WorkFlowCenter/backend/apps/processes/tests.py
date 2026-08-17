from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse
import json
from rest_framework.test import APIClient

from .models import ProcessDefinition, ProcessInstance, NodeTask, InitiatorApp, ApprovalRecord
from .services.engine import ProcessEngine
from .services.security import hash_api_key

User = get_user_model()


def make_definition(**kwargs):
    defaults = dict(
        key='simple_approve',
        name='简单审批',
        status=ProcessDefinition.Status.PUBLISHED,
        definition_json={
            'nodes': [
                {'key': 'start', 'type': 'start', 'name': '开始'},
                {'key': 'approve', 'type': 'approve', 'name': '主管审批'},
                {'key': 'end', 'type': 'end', 'name': '结束'},
            ],
            'edges': [
                {'from': 'start', 'to': 'approve'},
                {'from': 'approve', 'to': 'end'},
            ],
        },
    )
    defaults.update(kwargs)
    return ProcessDefinition.objects.create(**defaults)


class ProcessDefinitionTest(TestCase):
    """流程定义测试"""

    def test_create_definition(self):
        defn = ProcessDefinition.objects.create(
            key='leave_apply',
            name='请假申请',
            definition_json={
                'nodes': [
                    {'key': 'start', 'type': 'start', 'name': '开始'},
                    {'key': 'approve', 'type': 'approve', 'name': '审批'},
                    {'key': 'end', 'type': 'end', 'name': '结束'},
                ],
                'edges': [
                    {'from': 'start', 'to': 'approve'},
                    {'from': 'approve', 'to': 'end'},
                ],
            },
        )
        self.assertEqual(defn.key, 'leave_apply')


class ProcessEngineTest(TestCase):
    """流程引擎测试"""

    def setUp(self):
        self.user = User.objects.create_user(username='starter', password='pass')
        self.manager = User.objects.create_user(username='manager', password='pass')
        self.definition = ProcessDefinition.objects.create(
            key='simple_approve',
            name='简单审批',
            status=ProcessDefinition.Status.PUBLISHED,
            definition_json={
                'nodes': [
                    {'key': 'start', 'type': 'start', 'name': '开始'},
                    {
                        'key': 'approve', 'type': 'approve', 'name': '主管审批',
                        'approval_type': 'single',
                        'assignees': [{'type': 'user', 'id': self.manager.id}],
                    },
                    {'key': 'end', 'type': 'end', 'name': '结束'},
                ],
                'edges': [
                    {'from': 'start', 'to': 'approve'},
                    {'from': 'approve', 'to': 'end'},
                ],
            },
        )

    def test_start_process(self):
        instance = ProcessEngine.start(
            definition=self.definition,
            form_data={'days': 3, 'reason': '年假'},
            started_by=self.user,
        )
        self.assertEqual(instance.status, ProcessInstance.Status.RUNNING)
        self.assertTrue(instance.instance_no.startswith('WI-'))

    def test_complete_task(self):
        instance = ProcessEngine.start(
            definition=self.definition,
            form_data={},
            started_by=self.user,
        )
        task = NodeTask.objects.filter(instance=instance).first()
        if task:
            # Assign manager
            task.assignee = self.manager
            task.candidate_users = [self.manager.id]
            task.save()
            task = ProcessEngine.complete(task.id, self.manager, result='approve')
            # After approval with this simple flow, instance should be completed
            instance = ProcessInstance.objects.get(pk=instance.pk)
            self.assertEqual(instance.status, ProcessInstance.Status.COMPLETED)
            # 完成审批后不应重复创建同一节点的任务
            self.assertEqual(
                NodeTask.objects.filter(instance=instance, node_key='approve').count(),
                1,
            )


class SubmitScopeTest(TestCase):
    """提交范围运行时校验"""

    def setUp(self):
        from apps.accounts.models import Department
        self.parent_dept = Department.objects.create(name='技术部')
        self.dept_a = Department.objects.create(name='研发组', parent=self.parent_dept)
        self.dept_b = Department.objects.create(name='运营部')
        self.role = Group.objects.create(name='审批人')

        self.user_a = User.objects.create_user(username='ua', password='pass', department=self.dept_a)
        self.user_b = User.objects.create_user(username='ub', password='pass', department=self.dept_b)
        self.user_role = User.objects.create_user(username='ur', password='pass', department=self.dept_b)
        self.user_role.groups.add(self.role)

        self.client_a = APIClient()
        self.client_a.force_authenticate(self.user_a)
        self.client_b = APIClient()
        self.client_b.force_authenticate(self.user_b)
        self.client_role = APIClient()
        self.client_role.force_authenticate(self.user_role)

    def test_specific_dept_allows_member(self):
        definition = make_definition(
            key='dept_flow',
            submit_scope=ProcessDefinition.SubmitScope.SPECIFIC_DEPT,
            submit_scope_ids=[self.dept_a.id],
        )
        response = self.client_a.post(
            reverse('process-instance-start'),
            {'definition_id': definition.id, 'form_data': {}},
            format='json',
        )
        self.assertEqual(response.status_code, 201)

    def test_specific_dept_denies_other_dept(self):
        definition = make_definition(
            key='dept_flow',
            submit_scope=ProcessDefinition.SubmitScope.SPECIFIC_DEPT,
            submit_scope_ids=[self.dept_a.id],
        )
        response = self.client_b.post(
            reverse('process-instance-start'),
            {'definition_id': definition.id, 'form_data': {}},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_specific_dept_includes_child_dept(self):
        """指定上级部门时，下属部门成员也可发起"""
        definition = make_definition(
            key='dept_flow',
            submit_scope=ProcessDefinition.SubmitScope.SPECIFIC_DEPT,
            submit_scope_ids=[self.parent_dept.id],
        )
        response = self.client_a.post(
            reverse('process-instance-start'),
            {'definition_id': definition.id, 'form_data': {}},
            format='json',
        )
        self.assertEqual(response.status_code, 201)

    def test_specific_role_allows_member(self):
        definition = make_definition(
            key='role_flow',
            submit_scope=ProcessDefinition.SubmitScope.SPECIFIC_ROLE,
            submit_scope_ids=[self.role.id],
        )
        response = self.client_role.post(
            reverse('process-instance-start'),
            {'definition_id': definition.id, 'form_data': {}},
            format='json',
        )
        self.assertEqual(response.status_code, 201)

    def test_specific_role_denies_other(self):
        definition = make_definition(
            key='role_flow',
            submit_scope=ProcessDefinition.SubmitScope.SPECIFIC_ROLE,
            submit_scope_ids=[self.role.id],
        )
        response = self.client_a.post(
            reverse('process-instance-start'),
            {'definition_id': definition.id, 'form_data': {}},
            format='json',
        )
        self.assertEqual(response.status_code, 403)


class ProgramInitiateTest(TestCase):
    """程序发起路径：凭证认证 + 绑定 + 提单人 + 幂等"""

    API_KEY = 'demo_test_key_2026'

    def setUp(self):
        self.app = InitiatorApp.objects.create(
            name='测试程序',
            code='test_app',
            api_key_hash=hash_api_key(self.API_KEY),
        )
        self.initiator = User.objects.create_user(username='ticket_owner', password='pass')
        self.definition = make_definition(
            key='program_flow',
            allow_program_initiate=True,
            initiator_app_ids=[self.app.id],
        )

    def call(self, definition=None, initiator_user_id=None, business_key='bk-1', app_key=None, app_code=None):
        definition = definition or self.definition
        extra = {
            'HTTP_X_APP_CODE': app_code if app_code is not None else self.app.code,
            'HTTP_X_APP_KEY': app_key if app_key is not None else self.API_KEY,
        }
        payload = {'definition_id': definition.id, 'form_data': {'reason': 'test'}}
        if initiator_user_id is not None:
            payload['initiator_user_id'] = initiator_user_id
        if business_key is not None:
            payload['business_key'] = business_key
        return Client().post(
            reverse('process-instance-start'),
            data=json.dumps(payload),
            content_type='application/json',
            **extra,
        )

    def test_valid_program_start(self):
        response = self.call(initiator_user_id=self.initiator.id)
        self.assertEqual(response.status_code, 201)
        instance = ProcessInstance.objects.get(business_key='bk-1')
        self.assertEqual(instance.started_by, self.initiator)
        record = ApprovalRecord.objects.filter(instance=instance, action='comment').first()
        self.assertEqual(record.initiator_source, 'test_app')

    def test_invalid_key_rejected(self):
        response = self.call(
            initiator_user_id=self.initiator.id,
            app_key='wrong-key',
        )
        self.assertEqual(response.status_code, 401)

    def test_app_not_bound_rejected(self):
        other = make_definition(key='other_flow', allow_program_initiate=True, initiator_app_ids=[])
        response = self.call(definition=other, initiator_user_id=self.initiator.id)
        self.assertEqual(response.status_code, 403)

    def test_program_initiate_disabled_rejected(self):
        other = make_definition(key='person_flow', allow_program_initiate=False)
        response = self.call(definition=other, initiator_user_id=self.initiator.id)
        self.assertEqual(response.status_code, 403)

    def test_missing_initiator_user_rejected(self):
        response = self.call(initiator_user_id=None)
        self.assertEqual(response.status_code, 400)

    def test_missing_business_key_rejected(self):
        response = self.call(initiator_user_id=self.initiator.id, business_key=None)
        self.assertEqual(response.status_code, 400)

    def test_business_key_idempotent(self):
        first = self.call(initiator_user_id=self.initiator.id)
        self.assertEqual(first.status_code, 201)
        second = self.call(initiator_user_id=self.initiator.id)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data['id'], first.data['id'])
        self.assertEqual(ProcessInstance.objects.filter(business_key='bk-1').count(), 1)

    def test_anonymous_person_path_rejected(self):
        response = APIClient().post(
            reverse('process-instance-start'),
            {'definition_id': self.definition.id, 'form_data': {}},
            format='json',
        )
        self.assertEqual(response.status_code, 401)
