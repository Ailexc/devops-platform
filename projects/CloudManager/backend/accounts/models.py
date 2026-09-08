from django.db import models
from django.contrib.auth.models import AbstractUser


class Department(models.Model):
    """部门"""
    name = models.CharField('部门名称', max_length=64)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='children', verbose_name='上级部门')
    sort_order = models.IntegerField('排序', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'sys_department'
        verbose_name = '部门'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class User(AbstractUser):
    """用户模型"""
    display_name = models.CharField('显示名', max_length=64, blank=True, default='')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name='所属部门')
    phone = models.CharField('手机号', max_length=20, blank=True, default='')
    avatar = models.CharField('头像URL', max_length=255, blank=True, default='')

    class Meta:
        db_table = 'sys_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        # 解决与 Django auth.User 的 groups/user_permissions 字段冲突
        abstract = False

    def __str__(self):
        return self.display_name or self.username


class Role(models.Model):
    """角色"""
    ROLE_CHOICES = [
        ('super_admin', '超级管理员'),
        ('cloud_admin', '云管理员'),
        ('ops', '运维'),
        ('readonly', '只读'),
    ]

    name = models.CharField('角色名称', max_length=64, unique=True)
    code = models.CharField('角色编码', max_length=32, unique=True, choices=ROLE_CHOICES)
    description = models.CharField('描述', max_length=255, blank=True, default='')
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'sys_role'
        verbose_name = '角色'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Permission(models.Model):
    """权限点"""
    MODULE_CHOICES = [
        ('cmdb', '资源管理'),
        ('ticket', '工单管理'),
        ('account', '账号管理'),
        ('cost', '成本管理'),
        ('system', '系统管理'),
    ]

    name = models.CharField('权限名称', max_length=64)
    code = models.CharField('权限编码', max_length=128, unique=True,
                            help_text='格式: module:resource:action')
    module = models.CharField('所属模块', max_length=32, choices=MODULE_CHOICES)
    description = models.CharField('描述', max_length=255, blank=True, default='')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'sys_permission'
        verbose_name = '权限'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class UserRole(models.Model):
    """用户-角色关联"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles', verbose_name='用户')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_users', verbose_name='角色')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'sys_user_role'
        verbose_name = '用户角色'
        verbose_name_plural = verbose_name
        unique_together = ('user', 'role')


class RolePermission(models.Model):
    """角色-权限关联"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions', verbose_name='角色')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE,
                                   related_name='permission_roles', verbose_name='权限')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'sys_role_permission'
        verbose_name = '角色权限'
        verbose_name_plural = verbose_name
        unique_together = ('role', 'permission')


class OperationLog(models.Model):
    """操作审计日志"""
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name='操作人')
    username = models.CharField('用户名', max_length=64, blank=True, default='')
    module = models.CharField('模块', max_length=32, help_text='cmdb/ticket/account/cost/auth')
    action = models.CharField('操作标识', max_length=64)
    resource_id = models.CharField('目标资源ID', max_length=64, blank=True, default='')
    detail = models.JSONField('操作详情', default=dict, blank=True)
    ip = models.CharField('来源IP', max_length=64, blank=True, default='')
    created_at = models.DateTimeField('操作时间', auto_now_add=True)

    class Meta:
        db_table = 'sys_operation_log'
        verbose_name = '操作日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.username} - {self.module}:{self.action}'
