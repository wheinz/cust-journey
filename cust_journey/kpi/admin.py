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
            'fields': ('name', 'level', 'kpi_type', 'description'),
        }),
        ('Journey', {
            'fields': ('lifecycle_phase', 'journey_phase', 'step'),
        }),
        ('Ownership', {
            'fields': ('owner', 'why_important'),
        }),
        ('Measurement', {
            'fields': (
                'do_we_measure_it', 'measurement_current', 'measurement_target',
                'measurement_trigger', 'measurement_trigger_detail',
                'store_current', 'store_target', 'review_cadence',
            ),
        }),
        ('Prioritization', {
            'fields': ('impact', 'effort', 'implementation_phase', 'target_quarter'),
        }),
        ('Relationships', {
            'fields': ('contributes_to', 'initiatives', 'notes'),
        }),
    )
