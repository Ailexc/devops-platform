from django.contrib.auth.models import AbstractUser
from django.db import models


class Department(models.Model):
    """部门模型，支持树形结构"""
    name = models.CharField('部门名称', max_length=100)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='children',
        verbose_name='上级部门',
    )
    manager = models.ForeignKey(
        'User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='managed_departments',
        verbose_name='部门主管',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name_plural = 'departments'
        ordering = ['id']

    def __str__(self):
        return self.name

    @property
    def ancestor_chain(self):
        """返回从当前部门到根部门的链"""
        chain = []
        current = self
        while current:
            chain.append(current)
            current = current.parent
        return chain


class User(AbstractUser):
    """扩展用户模型"""
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='members',
        verbose_name='所属部门',
    )

    class Meta:
        verbose_name = 'user'

    def __str__(self):
        return self.get_full_name() or self.username

    def get_manager(self, level=1):
        """
        获取第 N 级主管。
        level=1 表示直属主管，level=2 表示隔级主管，以此类推。
        """
        current_dept = self.department
        for _ in range(level):
            if current_dept and current_dept.manager:
                return current_dept.manager
            if current_dept and current_dept.parent:
                current_dept = current_dept.parent
            else:
                return None
        return current_dept.manager if current_dept else None
