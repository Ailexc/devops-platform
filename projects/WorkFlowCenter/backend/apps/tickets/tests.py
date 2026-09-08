from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status as http_status

from .models import TicketType, Ticket, Comment, Notification

User = get_user_model()


class TicketTypeTest(TestCase):
    def test_create_ticket_type(self):
        tt = TicketType.objects.create(
            code='incident',
            name='故障报修',
            priority_matrix={'severity': {'high': 4}},
        )
        self.assertEqual(tt.code, 'incident')


class TicketTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='pass')
        self.tt = TicketType.objects.create(code='incident', name='故障报修')

    def test_create_ticket(self):
        ticket = Ticket.objects.create(
            ticket_type=self.tt,
            title='服务器宕机',
            description='生产环境 web-01 无法访问',
            started_by=self.user,
        )
        self.assertEqual(ticket.status, Ticket.Status.NEW)

    def test_fsm_transitions(self):
        ticket = Ticket.objects.create(
            ticket_type=self.tt,
            title='测试工单',
            started_by=self.user,
        )
        ticket.assign()
        ticket.save(update_fields=['status'])
        self.assertEqual(ticket.status, Ticket.Status.ASSIGNED)

        ticket.start_progress()
        ticket.save(update_fields=['status'])
        self.assertEqual(ticket.status, Ticket.Status.IN_PROGRESS)


class TicketAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='api_user', password='pass', is_staff=True)
        self.client.force_authenticate(user=self.user)
        self.tt = TicketType.objects.create(code='incident', name='故障报修')

    def test_create_ticket(self):
        response = self.client.post('/api/v1/tickets/', {
            'ticket_type': self.tt.id,
            'title': '测试工单',
            'description': '描述',
            'priority': 2,
        })
        self.assertEqual(response.status_code, http_status.HTTP_201_CREATED)

    def test_list_tickets(self):
        Ticket.objects.create(
            ticket_type=self.tt,
            title='工单1',
            started_by=self.user,
        )
        response = self.client.get('/api/v1/tickets/')
        self.assertEqual(response.status_code, http_status.HTTP_200_OK)
