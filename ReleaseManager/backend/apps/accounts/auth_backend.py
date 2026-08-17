from django.contrib.auth.backends import BaseBackend
from apps.accounts.models import User


class DemoAuthBackend(BaseBackend):
    """Demo 认证后端 - 仅通过用户名认证，无密码"""

    def authenticate(self, request, username=None, **kwargs):
        try:
            return User.objects.get(username=username, is_active=True)
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None