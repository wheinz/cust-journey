from django.contrib import admin

from .models import KPI


@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'level', 'kpi_type', 'owner', 'lifecycle_phase',
        'implementation_phase', 'target_quarter', 'impact', 'effort',
        'review_cadence', 'do_we_measure_it',
    ]
    list_filter = [
        'level', 'kpi_type', 'review_cadence', 'do_we_measure_it',
        'implementation_phase', 'target_quarter', 'lifecycle_phase',
    ]
    search_fields = ['name', 'description', 'owner']
    fieldsets = (
        (None, {
            'fields': ('name', 'level', 'kpi_type', 'owner', 'review_cadence'),
        }),
        ('Journey link', {
            'fields': ('lifecycle_phase', 'journey_phase', 'step'),
        }),
        ('Details', {
            'fields': (
                'description', 'why_important', 'do_we_measure_it',
                'how_measure_it', 'where_store',
            ),
        }),
        ('Prioritization & roadmap', {
            'fields': ('impact', 'effort', 'implementation_phase', 'target_quarter'),
        }),
        ('Impact & tracking', {
            'fields': ('influences', 'initiatives', 'notes'),
        }),
    )
