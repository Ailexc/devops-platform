from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import Department

User = get_user_model()


class UserModelTest(TestCase):
    """用户模型测试"""

    def test_create_user(self):
        dept = Department.objects.create(name='技术部')
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            department=dept,
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.department.name, '技术部')

    def test_get_manager(self):
        manager = User.objects.create_user(username='manager', password='pass')
        dept = Department.objects.create(name='技术部', manager=manager)
        user = User.objects.create_user(username='dev', password='pass', department=dept)
        self.assertEqual(user.get_manager(level=1), manager)


class DepartmentAPITest(TestCase):
    """部门 API 测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='admin', password='pass', is_staff=True)
        self.client.force_authenticate(user=self.user)

    def test_create_department(self):
        response = self.client.post('/api/v1/departments/', {'name': '技术部'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_departments(self):
        Department.objects.create(name='技术部')
        response = self.client.get('/api/v1/departments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
