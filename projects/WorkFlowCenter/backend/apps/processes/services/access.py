"""
提交范围与程序发起权限校验
"""
from apps.processes.models import ProcessDefinition


def user_allowed_to_submit(definition, user):
    """
    校验用户是否在流程的提交范围内。

    返回 (allowed: bool, reason: str)。
    - all：全员可提交
    - specific_dept：用户所属部门（含上级部门链）命中指定部门
    - specific_role：用户角色命中指定角色
    """
    scope = definition.submit_scope
    if scope == ProcessDefinition.SubmitScope.NONE:
        return False, '该流程不允许人员提交，请通过程序接口发起'
    if scope == ProcessDefinition.SubmitScope.ALL:
        return True, ''
    ids = set(definition.submit_scope_ids or [])
    if scope == ProcessDefinition.SubmitScope.SPECIFIC_DEPT:
        dept_ids = set()
        dept = getattr(user, 'department', None)
        while dept:
            dept_ids.add(dept.id)
            dept = dept.parent
        if dept_ids & ids:
            return True, ''
        return False, '当前用户所属部门不在该流程的提交范围内'
    if scope == ProcessDefinition.SubmitScope.SPECIFIC_ROLE:
        role_ids = set(user.groups.values_list('id', flat=True))
        if role_ids & ids:
            return True, ''
        return False, '当前用户所属角色不在该流程的提交范围内'
    return True, ''
