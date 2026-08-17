from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import TicketType, Ticket, Comment, Notification
from .serializers import (
    TicketTypeSerializer,
    TicketListSerializer,
    TicketDetailSerializer,
    CommentSerializer,
    NotificationSerializer,
)


class TicketTypeViewSet(viewsets.ModelViewSet):
    """工单类型视图集"""
    queryset = TicketType.objects.all()
    serializer_class = TicketTypeSerializer
    filterset_fields = ['is_active']
    search_fields = ['code', 'name']


class TicketViewSet(viewsets.ModelViewSet):
    """工单视图集"""
    queryset = Ticket.objects.select_related(
        'ticket_type', 'started_by', 'assigned_to', 'instance',
    ).all()
    filterset_fields = ['status', 'priority', 'ticket_type', 'started_by', 'assigned_to']
    search_fields = ['title', 'description']

    def get_serializer_class(self):
        if self.action == 'list':
            return TicketListSerializer
        return TicketDetailSerializer

    def perform_create(self, serializer):
        serializer.save(started_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='assign')
    def assign_ticket(self, request, pk=None):
        """分配工单"""
        ticket = self.get_object()
        to_user_id = request.data.get('assigned_to')
        if not to_user_id:
            return Response({'detail': '请指定处理人'}, status=status.HTTP_400_BAD_REQUEST)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            to_user = User.objects.get(pk=to_user_id)
        except User.DoesNotExist:
            return Response({'detail': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)

        ticket.assigned_to = to_user
        ticket.assign()
        ticket.save(update_fields=['assigned_to', 'status', 'updated_at'])

        # 通知
        Notification.objects.create(
            user=to_user,
            type=Notification.Type.TICKET,
            title='工单已分配',
            content=f'工单 {ticket.title} 已分配给您',
        )
        return Response(TicketDetailSerializer(ticket).data)

    @action(detail=True, methods=['post'], url_path='start-progress')
    def start_progress(self, request, pk=None):
        """开始处理"""
        ticket = self.get_object()
        ticket.start_progress()
        ticket.save(update_fields=['status', 'updated_at'])
        return Response(TicketDetailSerializer(ticket).data)

    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve_ticket(self, request, pk=None):
        """解决工单"""
        ticket = self.get_object()
        ticket.resolve()
        ticket.resolved_at = timezone.now()
        ticket.save(update_fields=['status', 'resolved_at', 'updated_at'])
        return Response(TicketDetailSerializer(ticket).data)

    @action(detail=True, methods=['post'], url_path='close')
    def close_ticket(self, request, pk=None):
        """关闭工单"""
        ticket = self.get_object()
        ticket.close()
        ticket.closed_at = timezone.now()
        ticket.save(update_fields=['status', 'closed_at', 'updated_at'])
        return Response(TicketDetailSerializer(ticket).data)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_ticket(self, request, pk=None):
        """取消工单"""
        ticket = self.get_object()
        ticket.cancel()
        ticket.save(update_fields=['status', 'updated_at'])
        return Response(TicketDetailSerializer(ticket).data)

    @action(detail=True, methods=['post'], url_path='reopen')
    def reopen_ticket(self, request, pk=None):
        """重开工单"""
        ticket = self.get_object()
        ticket.reopen()
        ticket.save(update_fields=['status', 'updated_at'])
        return Response(TicketDetailSerializer(ticket).data)

    @action(detail=True, methods=['get', 'post'], url_path='comments')
    def ticket_comments(self, request, pk=None):
        """工单评论"""
        ticket = self.get_object()
        if request.method == 'GET':
            comments = ticket.comments.select_related('user').all()
            return Response(CommentSerializer(comments, many=True).data)
        else:
            serializer = CommentSerializer(data=request.data, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save(ticket=ticket)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentViewSet(viewsets.ModelViewSet):
    """评论视图集"""
    queryset = Comment.objects.select_related('user', 'ticket').all()
    serializer_class = CommentSerializer
    filterset_fields = ['ticket', 'user', 'visibility']

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotificationViewSet(viewsets.ModelViewSet):
    """通知视图集"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filterset_fields = ['user', 'type', 'is_read']

    def get_queryset(self):
        """默认只返回当前用户的通知"""
        queryset = super().get_queryset()
        user = self.request.user
        if user and user.is_authenticated:
            queryset = queryset.filter(user=user)
        return queryset

    @action(detail=False, methods=['get'], url_path='my')
    def my_notifications(self, request):
        """我的通知（最新在前）"""
        notifications = Notification.objects.filter(user=request.user)
        unread = notifications.filter(is_read=False).count()
        serializer = NotificationSerializer(notifications, many=True)
        return Response({'results': serializer.data, 'unread_count': unread})

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """标记已读"""
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """标记所有通知已读"""
        count = Notification.objects.filter(
            user=request.user, is_read=False
        ).update(is_read=True)
        return Response({'marked_count': count})
