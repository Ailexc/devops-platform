from django.contrib import admin

from .models import Scenario, ScenarioStep


class ScenarioStepInline(admin.TabularInline):
    model = ScenarioStep
    extra = 0


@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'need_approval', 'enabled', 'version']
    inlines = [ScenarioStepInline]
