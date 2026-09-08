from rest_framework import serializers
from .models import (
    CostBill, CostItem, Budget, OptimizationRule,
    RuleExecutionLog, OptimizationReport, OptimizationSuggestion,
)


class CostBillSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source='account.account_name', read_only=True)

    class Meta:
        model = CostBill
        fields = ['id', 'account', 'account_name', 'bill_month', 'total_cost',
                  'currency', 'created_at']


class CostItemSerializer(serializers.ModelSerializer):
    resource_name = serializers.CharField(source='resource.resource_name', read_only=True, default='')
    department_name = serializers.CharField(source='department.name', read_only=True, default='')
    application_name = serializers.CharField(source='application.name', read_only=True, default='')

    class Meta:
        model = CostItem
        fields = ['id', 'bill', 'resource', 'resource_name', 'service_type',
                  'cost', 'cost_date', 'department', 'department_name',
                  'application', 'application_name']


class BudgetSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    usage_percent = serializers.FloatField(read_only=True)
    is_over_threshold = serializers.BooleanField(read_only=True)

    class Meta:
        model = Budget
        fields = ['id', 'department', 'department_name', 'month', 'budget_amount',
                  'used_amount', 'alert_threshold', 'usage_percent', 'is_over_threshold']


class OptimizationSuggestionSerializer(serializers.ModelSerializer):
    resource_name = serializers.CharField(source='resource.resource_name', read_only=True, default='')
    resource_id = serializers.CharField(source='resource.cloud_resource_id', read_only=True, default='')
    account_name = serializers.CharField(source='account.account_name', read_only=True, default='')
    rule_name = serializers.CharField(source='rule.name', read_only=True, default='')
    suggestion_type_display = serializers.CharField(source='get_suggestion_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)

    class Meta:
        model = OptimizationSuggestion
        fields = ['id', 'report', 'rule', 'rule_name', 'resource', 'resource_name', 'resource_id',
                  'account', 'account_name', 'provider_type', 'region', 'resource_type',
                  'suggestion_type', 'suggestion_type_display', 'severity', 'severity_display',
                  'title', 'description', 'estimated_saving', 'is_resolved', 'created_at']


class OptimizationRuleSerializer(serializers.ModelSerializer):
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)

    class Meta:
        model = OptimizationRule
        fields = ['id', 'name', 'rule_type', 'rule_type_display', 'severity', 'severity_display',
                  'description', 'scope', 'conditions', 'title_template', 'description_template',
                  'saving_config', 'is_enabled', 'priority', 'created_at', 'updated_at']


class RuleExecutionLogSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source='rule.name', read_only=True, default='')

    class Meta:
        model = RuleExecutionLog
        fields = ['id', 'rule', 'rule_name', 'scope_snapshot', 'matched_count',
                  'created_count', 'execution_time_ms', 'executed_at']


class OptimizationReportSerializer(serializers.ModelSerializer):
    trigger_display = serializers.CharField(source='get_trigger_display', read_only=True)
    cloud_count = serializers.SerializerMethodField()
    total_rules = serializers.SerializerMethodField()
    total_matched = serializers.SerializerMethodField()
    total_saving = serializers.SerializerMethodField()

    class Meta:
        model = OptimizationReport
        fields = ['id', 'report_no', 'title', 'operator', 'trigger', 'trigger_display', 'summary',
                  'tree_snapshot', 'items_snapshot', 'executed_at',
                  'cloud_count', 'total_rules', 'total_matched', 'total_saving']

    def get_cloud_count(self, obj):
        return obj.summary.get('cloud_count', 0)

    def get_total_rules(self, obj):
        return obj.summary.get('total_rules', 0)

    def get_total_matched(self, obj):
        return obj.summary.get('total_matched', 0)

    def get_total_saving(self, obj):
        return obj.summary.get('total_saving', 0)
