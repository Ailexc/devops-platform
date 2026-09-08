from datetime import date
from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    CostBill, CostItem, Budget, OptimizationSuggestion,
    OptimizationRule, OptimizationReport,
)
from .serializers import (
    CostBillSerializer, CostItemSerializer,
    BudgetSerializer, OptimizationSuggestionSerializer,
    OptimizationRuleSerializer, OptimizationReportSerializer,
)


class CostBillViewSet(viewsets.ModelViewSet):
    queryset = CostBill.objects.select_related('account').all()
    serializer_class = CostBillSerializer
    filterset_fields = ['account', 'bill_month']

    @action(detail=False, methods=['post'])
    def generate_mock(self, request):
        """生成模拟账单数据（按月份）"""
        from cmdb.models import CloudAccount, Resource
        month = request.data.get('month', date.today().strftime('%Y-%m'))
        accounts = CloudAccount.objects.all()

        for account in accounts:
            bill, _ = CostBill.objects.get_or_create(
                account=account, bill_month=month,
                defaults={'total_cost': 0}
            )
            # 为每个实例资源生成费用明细
            resources = Resource.objects.filter(
                account=account, resource_type='instance', is_deleted=False
            )
            total = Decimal('0')
            for r in resources:
                # 模拟费用：基于规格的基础价格 + 随机波动
                base_price = random.uniform(50, 800)
                cost = round(base_price * random.uniform(0.8, 1.2), 2)
                day = random.randint(1, 28)
                CostItem.objects.create(
                    bill=bill,
                    resource=r,
                    service_type='compute',
                    cost=cost,
                    cost_date=f'{month}-{day:02d}',
                    department=r.department,
                )
                total += Decimal(str(cost))

            bill.total_cost = total
            bill.save()

        return Response({'message': f'已为 {month} 生成模拟账单'})

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """成本汇总（按月趋势，支持部门/应用过滤 + 数据权限）"""
        months = int(request.query_params.get('months', 6))
        department = request.query_params.get('department', '')
        application = request.query_params.get('application', '')
        qs = self._scoped_items(request)
        if department:
            qs = qs.filter(department__name=department)
        if application:
            if application == '未归属':
                qs = qs.filter(application__isnull=True)
            else:
                qs = qs.filter(application__name=application)
        rows = list(qs.values('bill__bill_month').annotate(
            total=Sum('cost')).order_by('bill__bill_month'))
        recent = rows[-months:] if len(rows) > months else rows
        return Response([{'bill_month': r['bill__bill_month'],
                          'total': float(r['total'])} for r in recent])

    @action(detail=False, methods=['get'])
    def by_department(self, request):
        """按部门分摊（支持按应用过滤 + 数据权限）"""
        month = request.query_params.get('month', date.today().strftime('%Y-%m'))
        application = request.query_params.get('application', '')
        qs = self._scoped_items(request).filter(bill__bill_month=month)
        if application:
            if application == '未归属':
                qs = qs.filter(application__isnull=True)
            else:
                qs = qs.filter(application__name=application)
        items = qs.values('department__name').annotate(
            total=Sum('cost')
        ).order_by('-total')
        return Response(list(items))

    @action(detail=False, methods=['get'])
    def by_application(self, request):
        """按应用/服务分摊（含未归属，支持按部门过滤 + 数据权限）"""
        month = request.query_params.get('month', date.today().strftime('%Y-%m'))
        department = request.query_params.get('department', '')
        qs = self._scoped_items(request).filter(bill__bill_month=month)
        if department:
            qs = qs.filter(department__name=department)
        items = qs.values('application__name').annotate(
            total=Sum('cost')
        ).order_by('-total')
        return Response(list(items))

    @action(detail=False, methods=['get'])
    def share_filters(self, request):
        """成本分摊筛选选项：有成本数据的部门/应用列表（含数据权限）"""
        depts = list(self._scoped_items(request).filter(department__isnull=False)
                     .values_list('department__name', flat=True)
                     .distinct().order_by('department__name'))
        apps = list(self._scoped_items(request).filter(application__isnull=False)
                    .values_list('application__name', flat=True)
                    .distinct().order_by('application__name'))
        return Response({'departments': depts, 'applications': apps})

    @action(detail=False, methods=['get'])
    def global_filters(self, request):
        """全局筛选选项：云厂商/账号/区域/部门/应用（含数据权限）"""
        scoped = self._scoped_items(request)
        clouds = list(scoped.filter(bill__account__isnull=False)
                      .values_list('bill__account__provider_type', flat=True).distinct())
        accounts = list(scoped.filter(bill__account__isnull=False)
                        .values_list('bill__account__account_name', flat=True).distinct())
        regions = list(scoped.filter(resource__isnull=False)
                       .values_list('resource__region', flat=True).distinct())
        depts = list(scoped.filter(department__isnull=False)
                     .values_list('department__name', flat=True)
                     .distinct().order_by('department__name'))
        apps = list(scoped.filter(application__isnull=False)
                    .values_list('application__name', flat=True)
                    .distinct().order_by('application__name'))
        return Response({
            'clouds': [c for c in clouds if c],
            'accounts': [a for a in accounts if a],
            'regions': [r for r in regions if r],
            'departments': depts,
            'applications': apps,
        })

    # ---------- 成本分摊下钻（部门 / 应用 → 资源明细） ----------

    def _scoped_items(self, request):
        """基础费用查询集 + 数据权限（非超管仅本部门）+ 全局维度过滤（云/账号/区域）"""
        qs = CostItem.objects.all()
        user = request.user
        if user.is_authenticated and not user.is_superuser:
            dept = getattr(user, 'department', None)
            if dept:
                qs = qs.filter(department=dept)
            else:
                qs = qs.none()
        # 全局维度筛选（云厂商 / 云账号 / 区域）
        cloud = request.query_params.get('cloud', '')
        if cloud:
            qs = qs.filter(bill__account__provider_type=cloud)
        account = request.query_params.get('account', '')
        if account:
            qs = qs.filter(bill__account__account_name=account)
        region = request.query_params.get('region', '')
        if region:
            qs = qs.filter(resource__region=region)
        return qs

    def _share_qs(self, request):
        """按 type/name 构建 CostItem 查询集（部门或应用维度，name='未归属' 特殊处理）"""
        type_ = request.query_params.get('type', 'department')
        name = request.query_params.get('name', '')
        month = request.query_params.get('month', date.today().strftime('%Y-%m'))
        qs = self._scoped_items(request).filter(bill__bill_month=month).select_related(
            'resource', 'department', 'application')
        if name and name != '未归属':
            if type_ == 'application':
                qs = qs.filter(application__name=name)
            else:
                qs = qs.filter(department__name=name)
        elif name == '未归属':
            qs = qs.filter(application__isnull=True)
        return qs, type_, name, month

    @action(detail=False, methods=['get'])
    def share_summary(self, request):
        """成本分摊汇总：总额/资源数/类型分布/TOP资源（部门或应用维度）"""
        from django.db.models import Count
        qs, type_, name, month = self._share_qs(request)
        agg = qs.aggregate(total=Sum('cost'), cnt=Count('id'))
        total = float(agg['total'] or 0)
        count = agg['cnt'] or 0

        by_type = list(qs.values('service_type').annotate(
            total=Sum('cost'), cnt=Count('id')).order_by('-total'))

        top_resources = list(qs.values(
            'resource__resource_name', 'resource__cloud_resource_id',
            'resource__resource_type', 'resource__region', 'resource__spec',
        ).annotate(total=Sum('cost')).order_by('-total')[:10])

        month_total = float(self._scoped_items(request).filter(
            bill__bill_month=month).aggregate(t=Sum('cost'))['t'] or 0)
        pct = round(total / month_total * 100, 1) if month_total else 0

        return Response({
            'type': type_, 'name': name, 'month': month,
            'total': round(total, 2), 'count': count,
            'month_total': round(month_total, 2), 'pct': pct,
            'by_resource_type': [{'type': b['service_type'], 'total': float(b['total']),
                                  'cnt': b['cnt']} for b in by_type],
            'top_resources': [{
                'resource_name': r['resource__resource_name'] or '-',
                'resource_id': r['resource__cloud_resource_id'] or '-',
                'resource_type': r['resource__resource_type'] or '',
                'region': r['resource__region'] or '',
                'spec': r['resource__spec'] or '',
                'total': float(r['total']),
            } for r in top_resources],
        })

    @action(detail=False, methods=['get'])
    def share_items(self, request):
        """成本分摊明细（分页）"""
        qs, type_, name, month = self._share_qs(request)
        page = max(1, int(request.query_params.get('page', 1)))
        page_size = min(100, int(request.query_params.get('page_size', 20)))
        total = qs.count()
        items = qs.order_by('-cost')[(page - 1) * page_size: page * page_size]
        return Response({
            'count': total, 'page': page, 'page_size': page_size,
            'type': type_, 'name': name, 'month': month,
            'results': [{
                'id': it.id,
                'resource_name': it.resource.resource_name if it.resource else '-',
                'resource_id': it.resource.cloud_resource_id if it.resource else '-',
                'resource_type': it.resource.resource_type if it.resource else '',
                'region': it.resource.region if it.resource else '',
                'service_type': it.service_type,
                'cost': float(it.cost),
                'cost_date': str(it.cost_date),
                'department_name': it.department.name if it.department else '未分配',
                'application_name': it.application.name if it.application else '未归属',
            } for it in items],
        })

    @action(detail=False, methods=['get'])
    def share_export(self, request):
        """导出成本分摊明细 CSV（UTF-8 BOM，Excel 可打开）"""
        import csv
        from django.http import HttpResponse
        qs, type_, name, month = self._share_qs(request)
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        filename = f"cost_share_{type_}_{name or 'all'}_{month}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['资源名称', '资源ID', '资源类型', '区域', '规格',
                         '费用(元)', '费用日期', '分摊部门', '分摊应用'])
        for it in qs.order_by('-cost').select_related('resource', 'department', 'application'):
            writer.writerow([
                it.resource.resource_name if it.resource else '-',
                it.resource.cloud_resource_id if it.resource else '-',
                it.resource.resource_type if it.resource else '',
                it.resource.region if it.resource else '',
                it.resource.spec if it.resource else '',
                it.cost, it.cost_date,
                it.department.name if it.department else '未分配',
                it.application.name if it.application else '未归属',
            ])
        return response


class CostItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CostItem.objects.select_related('resource', 'department').all()
    serializer_class = CostItemSerializer
    filterset_fields = ['bill', 'service_type', 'department']


class BudgetViewSet(viewsets.ModelViewSet):
    queryset = Budget.objects.select_related('department').all()
    serializer_class = BudgetSerializer
    filterset_fields = ['department', 'month']

    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """预算告警"""
        month = request.query_params.get('month', date.today().strftime('%Y-%m'))
        budgets = Budget.objects.filter(month=month, used_amount__gte=0).select_related('department')
        alerts = [b for b in budgets if b.is_over_threshold]
        serializer = BudgetSerializer(alerts, many=True)
        return Response(serializer.data)


class OptimizationSuggestionViewSet(viewsets.ModelViewSet):
    queryset = OptimizationSuggestion.objects.select_related('resource', 'account', 'rule').all()
    serializer_class = OptimizationSuggestionSerializer
    filterset_fields = ['suggestion_type', 'severity', 'is_resolved', 'provider_type', 'region', 'report']

    def get_queryset(self):
        """数据权限：非超管仅可见本部门建议"""
        qs = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and not user.is_superuser:
            dept = getattr(user, 'department', None)
            qs = qs.filter(department=dept) if dept else qs.none()
        return qs

    @action(detail=False, methods=['post'])
    def generate(self, request):
        """执行规则引擎（全量检测），生成优化建议 + 分析报告（兼容旧前端按钮）"""
        from .engine import run_all
        report = run_all(trigger='manual', operator=request.user.username if request.user.is_authenticated else 'system')
        return Response({
            'message': f'已执行规则引擎，生成报告 {report.report_no or report.id}',
            'report_id': report.id,
            'report_no': report.report_no,
        })

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """标记建议为已处理"""
        suggestion = self.get_object()
        suggestion.is_resolved = True
        suggestion.save(update_fields=['is_resolved'])
        return Response({'message': '已标记为处理', 'id': suggestion.id})


class OptimizationRuleViewSet(viewsets.ModelViewSet):
    """可配置优化规则 CRUD + 执行"""
    queryset = OptimizationRule.objects.all()
    serializer_class = OptimizationRuleSerializer
    filterset_fields = ['rule_type', 'severity', 'is_enabled']

    @action(detail=True, methods=['post'])
    def run(self, request, pk=None):
        """单规则检测"""
        from .engine import execute_rule, _collect_items
        rule = self.get_object()
        result = execute_rule(rule, trigger='single',
                              operator=request.user.username if request.user.is_authenticated else 'system')
        items = _collect_items(rule)
        return Response({
            'message': f'规则「{rule.name}」执行完成',
            'matched': result['matched'],
            'created': result['created'],
            'items': items,
        })

    @action(detail=False, methods=['post'])
    def run_all(self, request):
        """全量检测所有启用规则，生成分析报告"""
        from .engine import run_all
        report = run_all(trigger='manual',
                         operator=request.user.username if request.user.is_authenticated else 'system')
        from .serializers import OptimizationReportSerializer
        return Response({
            'message': f'全量检测完成，生成报告 {report.report_no or f"#{report.id}"}',
            'report': OptimizationReportSerializer(report).data,
        })

    @action(detail=False, methods=['get'])
    def cloud_groups(self, request):
        """按云厂商分组统计规则（前端分组渲染）"""
        groups = {}
        for rule in self.queryset:
            cloud = (rule.scope or {}).get('cloud') or '全部云'
            groups.setdefault(cloud, []).append({
                'id': rule.id, 'name': rule.name, 'rule_type': rule.rule_type,
                'severity': rule.severity, 'is_enabled': rule.is_enabled,
                'description': rule.description,
                'scope': rule.scope,
            })
        ordered = {}
        for key in sorted(groups.keys(), key=lambda k: (k == '全部云', k)):
            ordered[key] = groups[key]
        return Response(ordered)


class OptimizationReportViewSet(viewsets.ReadOnlyModelViewSet):
    """分析报告列表 / 详情 / 导出"""
    queryset = OptimizationReport.objects.all()
    serializer_class = OptimizationReportSerializer
    filterset_fields = ['trigger', 'operator']
    pagination_class = None  # 报告数量少，直接返回数组

    @action(detail=True, methods=['get'])
    def export(self, request, pk=None):
        """导出 CSV（UTF-8 BOM，Excel 可打开）"""
        import csv
        from django.http import HttpResponse
        report = self.get_object()
        items = report.items_snapshot or []

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        filename = f"cost_report_{report.id}_{report.executed_at:%Y%m%d}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        # UTF-8 BOM，Excel 打开不乱码
        response.write('\ufeff')
        writer = csv.writer(response)
        writer.writerow(['云厂商', '云账号', '区域', '资源类型', '资源名称', '资源ID', '规格',
                         '建议类型', '优先级', '预估月节省(元)', '状态'])
        for it in items:
            writer.writerow([
                it.get('cloud', ''), it.get('account', ''), it.get('region', ''),
                it.get('resource_type', ''), it.get('resource_name', ''), it.get('resource_id', ''),
                it.get('spec', ''), it.get('suggestion_type', ''), it.get('severity', ''),
                it.get('estimated_saving', 0), '已处理' if it.get('is_resolved') else '待处理',
            ])
        return response


class OverviewView(APIView):
    """成本优化总览：统计卡 + 图表聚合（大屏）"""

    def get(self, request):
        from django.db.models import Count
        # 数据权限：非超管仅统计本部门建议
        base_qs = OptimizationSuggestion.objects.all()
        user = request.user
        if user.is_authenticated and not user.is_superuser:
            dept = getattr(user, 'department', None)
            base_qs = base_qs.filter(department=dept) if dept else base_qs.none()
        suggestions = base_qs.filter(is_resolved=False)
        total = suggestions.aggregate(s=Sum('estimated_saving'))['s'] or 0
        all_count = base_qs.count()

        # 按云节省分布
        by_cloud = suggestions.values('provider_type').annotate(
            total=Sum('estimated_saving'), cnt=Count('id')
        ).order_by('-total')

        # 按建议类型分布
        by_type = suggestions.values('suggestion_type').annotate(
            cnt=Count('id'), total=Sum('estimated_saving')
        ).order_by('-cnt')

        # 按区域成本分布
        by_region = suggestions.values('region').annotate(
            total=Sum('estimated_saving')
        ).order_by('-total')

        # 近6月报告（节省趋势）
        reports = list(OptimizationReport.objects.all()[:6])
        trend = [{'label': r.executed_at.strftime('%m月'),
                  'saving': r.summary.get('total_saving', 0)} for r in reversed(reports)]

        return Response({
            'stats': {
                'pending': suggestions.count(),
                'total': all_count,
                'total_saving': round(float(total), 2),
                'resolved': all_count - suggestions.count(),
                'cloud_count': suggestions.values('provider_type').distinct().count(),
            },
            'by_cloud': list(by_cloud),
            'by_type': list(by_type),
            'by_region': list(by_region),
            'trend': trend,
            'suggestions': OptimizationSuggestionSerializer(suggestions[:50], many=True).data,
        })


class ApplicationCostView(APIView):
    """应用成本管理：应用成本聚合 / 趋势 / 预算 + 申请加预算（Demo 闭环：创建工单 + 更新预算）"""

    def _month_cost(self, app_name, month):
        return float(CostItem.objects.filter(
            application__name=app_name, bill__bill_month=month
        ).aggregate(s=Sum('cost'))['s'] or 0)

    def _app_payload(self, app, month):
        from datetime import timedelta
        cur = self._month_cost(app.name, month)
        prev_month = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        prev = self._month_cost(app.name, prev_month)
        mom = round((cur - prev) / prev * 100, 1) if prev else 0.0
        budget = float(app.budget_amount or 0)
        usage = round(cur / budget * 100, 1) if budget else 0.0
        dept_cost = float(CostItem.objects.filter(
            department=app.department, bill__bill_month=month
        ).aggregate(s=Sum('cost'))['s'] or 0) if app.department else 0.0
        return {
            'id': app.id, 'name': app.name,
            'department': app.department.name if app.department else '-',
            'owner': app.owner or '-',
            'month': month,
            'month_cost': round(cur, 2),
            'prev_month_cost': round(prev, 2),
            'mom_pct': mom,
            'budget_amount': round(budget, 2),
            'usage_percent': usage,
            'dept_cost': round(dept_cost, 2),
        }

    def get(self, request):
        from cmdb.models import Application
        month = request.query_params.get('month', date.today().strftime('%Y-%m'))
        app_id = request.query_params.get('app_id')
        account = request.query_params.get('account', '')
        region = request.query_params.get('region', '')
        # 数据权限：非超管仅本部门应用
        qs = Application.objects.all()
        user = request.user
        if user.is_authenticated and not user.is_superuser and user.department:
            qs = qs.filter(department=user.department)

        if app_id:
            app = qs.filter(id=app_id).first()
            if not app:
                return Response({'error': '应用不存在或无权访问'}, status=status.HTTP_404_NOT_FOUND)
            # 环境维度：账号 + 区域（环境 = 账号+区域），限定该应用
            if account or region:
                if request.query_params.get('items'):
                    return self._env_items(app, account, region, month, request)
                return Response(self._env_payload(app, account, region, month))
            payload = self._app_payload(app, month)
            # 近 6 月趋势
            from datetime import timedelta
            months = []
            d = date.today().replace(day=1)
            for _ in range(6):
                months.append(d.strftime('%Y-%m'))
                d = (d.replace(day=1) - timedelta(days=1)).replace(day=1)
            payload['trend'] = [{'month': m, 'cost': round(self._month_cost(app.name, m), 2)}
                                for m in reversed(months)]
            # 资源类型分布
            by_type = list(CostItem.objects.filter(
                application__name=app.name, bill__bill_month=month
            ).values('service_type').annotate(total=Sum('cost')).order_by('-total'))
            payload['by_type'] = [{'type': t['service_type'], 'total': float(t['total'])}
                                  for t in by_type]
            return Response(payload)

        # 所有应用成本列表
        result = [self._app_payload(a, month) for a in qs]
        result.sort(key=lambda x: x['month_cost'], reverse=True)
        return Response(result)

    def _env_payload(self, app, account, region, month):
        """环境（账号+区域）成本聚合：该应用在该账号+区域下的资源费用 + 应用预算"""
        from datetime import timedelta

        def cost(m):
            q = CostItem.objects.filter(bill__bill_month=m, application__name=app.name)
            if account:
                q = q.filter(bill__account__account_name=account)
            if region:
                q = q.filter(resource__region=region)
            return float(q.aggregate(s=Sum('cost'))['s'] or 0)

        cur = cost(month)
        prev_month = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        prev = cost(prev_month)
        mom = round((cur - prev) / prev * 100, 1) if prev else 0.0
        budget = float(app.budget_amount or 0)
        usage = round(cur / budget * 100, 1) if budget else 0.0

        months = []
        d = date.today().replace(day=1)
        for _ in range(6):
            months.append(d.strftime('%Y-%m'))
            d = (d.replace(day=1) - timedelta(days=1)).replace(day=1)
        trend = [{'month': m, 'cost': round(cost(m), 2)} for m in reversed(months)]

        q = CostItem.objects.filter(bill__bill_month=month, application__name=app.name)
        if account:
            q = q.filter(bill__account__account_name=account)
        if region:
            q = q.filter(resource__region=region)
        by_type = list(q.values('service_type').annotate(total=Sum('cost')).order_by('-total'))

        dept_cost = float(CostItem.objects.filter(
            department=app.department, bill__bill_month=month
        ).aggregate(s=Sum('cost'))['s'] or 0) if app.department else 0.0

        return {
            'id': app.id, 'name': app.name,
            'department': app.department.name if app.department else '-',
            'account': account, 'region': region, 'month': month,
            'month_cost': round(cur, 2),
            'prev_month_cost': round(prev, 2),
            'mom_pct': mom,
            'budget_amount': round(budget, 2),
            'usage_percent': usage,
            'dept_cost': round(dept_cost, 2),
            'trend': trend,
            'by_type': [{'type': t['service_type'], 'total': float(t['total'])} for t in by_type],
        }

    def _env_items(self, app, account, region, month, request):
        """环境（账号+区域）成本资源级明细（分页，支持筛选）"""
        qs = CostItem.objects.filter(bill__bill_month=month, application__name=app.name)
        if account:
            qs = qs.filter(bill__account__account_name=account)
        if region:
            qs = qs.filter(resource__region=region)
        # 筛选：资源类型 / 区域 / 关键词
        rtype = request.query_params.get('resource_type', '')
        if rtype:
            qs = qs.filter(resource__resource_type=rtype)
        area = request.query_params.get('area', '')
        if area:
            qs = qs.filter(resource__region=area)
        keyword = request.query_params.get('keyword', '')
        if keyword:
            qs = qs.filter(resource__resource_name__icontains=keyword)
        page = max(1, int(request.query_params.get('page', 1)))
        page_size = min(100, int(request.query_params.get('page_size', 20)))
        total = qs.count()
        items = qs.order_by('-cost').select_related(
            'resource', 'department', 'application')[(page - 1) * page_size: page * page_size]
        return Response({
            'count': total, 'page': page, 'page_size': page_size,
            'results': [{
                'id': it.id,
                'resource_name': it.resource.resource_name if it.resource else '-',
                'resource_id': it.resource.cloud_resource_id if it.resource else '-',
                'resource_type': it.resource.resource_type if it.resource else it.service_type,
                'region': it.resource.region if it.resource else '',
                'spec': it.resource.spec if it.resource else '-',
                'cost': float(it.cost),
                'cost_date': str(it.cost_date),
                'department_name': it.department.name if it.department else '未分配',
                'application_name': it.application.name if it.application else '未归属',
            } for it in items],
        })

    def post(self, request):
        """申请加预算：创建 apply_quota 工单 + 更新应用预算（Demo 审批通过即生效）"""
        from decimal import Decimal
        from django.utils import timezone
        from cmdb.models import Application
        from ticket.models import TicketOrder

        app_id = request.data.get('app_id')
        amount = Decimal(str(request.data.get('amount') or 0))
        reason = (request.data.get('reason') or '').strip()
        app = Application.objects.filter(id=app_id).first()
        if not app:
            return Response({'error': '应用不存在'}, status=status.HTTP_404_NOT_FOUND)
        if amount <= 0:
            return Response({'error': '申请金额需大于 0'}, status=status.HTTP_400_BAD_REQUEST)

        before = float(app.budget_amount or 0)
        after = before + float(amount)
        app.budget_amount = Decimal(str(after))
        app.save(update_fields=['budget_amount'])

        # 工单号（复用 WO+日期+序列 规则）
        prefix = f'WO{timezone.now().strftime("%Y%m%d")}'
        last = TicketOrder.objects.filter(ticket_no__startswith=prefix).order_by('-ticket_no').first()
        seq = (int(last.ticket_no[-4:]) + 1) if last else 1
        ticket_no = f'{prefix}{seq:04d}'
        user = request.user
        TicketOrder.objects.create(
            ticket_no=ticket_no,
            ticket_type='apply_quota',
            title=f'预算申请：{app.name}',
            status='success',  # Demo 闭环：直接审批通过
            applicant=user.display_name or user.username,
            applicant_id=user.id,
            request_content={
                'app_id': app.id, 'app_name': app.name,
                'amount': str(amount), 'reason': reason,
                'budget_before': str(before), 'budget_after': str(after),
            },
        )
        return Response({
            'message': f'预算申请已提交并生效，新增 ¥{amount:,.0f}，当前预算 ¥{after:,.0f}',
            'ticket_no': ticket_no,
            'budget_amount': round(after, 2),
        })
