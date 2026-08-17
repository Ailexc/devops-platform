from django.db import models


class User(models.Model):
    """用户 - 无密码，Demo 通过选择用户登录"""
    username = models.CharField(max_length=32, unique=True, verbose_name="用户名")
    display_name = models.CharField(max_length=64, verbose_name="显示名称")
    email = models.EmailField(max_length=128, blank=True, verbose_name="邮箱")
    avatar_url = models.URLField(blank=True, verbose_name="头像")
    is_active = models.BooleanField(default=True, verbose_name="是否激活")

    # 专属角色关联
    role = models.ForeignKey("authz.Role", null=True, blank=True, on_delete=models.SET_NULL,
                             verbose_name="专属角色")
    # 身份属性
    is_group_leader = models.BooleanField(default=False, verbose_name="是否组长")
    is_audit_admin = models.BooleanField(default=False, verbose_name="是否审计管理员（仅手动SQL设置，全量可见不可操作）")

    # Django 对自定义 User 模型的要求
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['display_name']
    is_anonymous = False
    is_authenticated = True

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user"
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self):
        return f"{self.display_name}({self.username})"