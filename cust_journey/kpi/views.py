from django.db.models import Prefetch, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from .models import KPI


class KPIHierarchyView(TemplateView):
    template_name = 'kpi/kpi_hierarchy.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        kpi_prefetch = Prefetch(
            'supported_by',
            queryset=KPI.objects.filter(level=KPI.Level.KPI)
            .prefetch_related(Prefetch(
                'supported_by',
                queryset=KPI.objects.filter(level=KPI.Level.METRIC),
                to_attr='contributing_metrics',
            ))
            .order_by('name'),
            to_attr='contributing_kpis',
        )
        metric_prefetch = Prefetch(
            'supported_by',
            queryset=KPI.objects.filter(level=KPI.Level.METRIC).order_by('name'),
            to_attr='direct_metrics',
        )
        ctx['roots'] = (
            KPI.objects.filter(level=KPI.Level.BUSINESS_KPI)
            .prefetch_related(kpi_prefetch, metric_prefetch)
            .order_by('name')
        )
        return ctx


class KPIHierarchyDetailView(DetailView):
    model = KPI
    template_name = 'kpi/partials/hierarchy_detail.html'
    context_object_name = 'kpi'

    def get_queryset(self):
        return KPI.objects.prefetch_related('contributes_to', 'supported_by')


class KPITableView(ListView):
    model = KPI
    template_name = 'kpi/kpi_table.html'
    context_object_name = 'kpis'
    paginate_by = 50

    def get_queryset(self):
        qs = KPI.objects.select_related('lifecycle_phase', 'step')
        q = self.request.GET.get('q', '')
        level = self.request.GET.get('level', '')
        kpi_type = self.request.GET.get('kpi_type', '')
        lifecycle = self.request.GET.get('lifecycle_phase', '')
        measure = self.request.GET.get('do_we_measure_it', '')
        impl_phase = self.request.GET.get('implementation_phase', '')
        target_q = self.request.GET.get('target_quarter', '')

        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(description__icontains=q) |
                Q(owner__icontains=q)
            )
        if level:
            qs = qs.filter(level=level)
        if kpi_type:
            qs = qs.filter(kpi_type=kpi_type)
        if lifecycle:
            qs = qs.filter(lifecycle_phase_id=lifecycle)
        if measure:
            qs = qs.filter(do_we_measure_it=measure)
        if impl_phase:
            qs = qs.filter(implementation_phase=impl_phase)
        if target_q:
            qs = qs.filter(target_quarter=target_q)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['level_choices'] = KPI.Level.choices
        ctx['kpi_type_choices'] = KPI.KPIType.choices
        ctx['measure_choices'] = KPI.MeasureStatus.choices
        ctx['phase_choices'] = KPI.ImplementationPhase.choices
        from journey.models import Phase
        ctx['lifecycle_choices'] = Phase.objects.all()
        ctx['quarter_choices'] = KPI.objects.exclude(target_quarter='').values_list('target_quarter', flat=True).distinct().order_by('target_quarter')
        ctx['active_filters'] = {
            'q': self.request.GET.get('q', ''),
            'level': self.request.GET.get('level', ''),
            'kpi_type': self.request.GET.get('kpi_type', ''),
            'lifecycle_phase': self.request.GET.get('lifecycle_phase', ''),
            'do_we_measure_it': self.request.GET.get('do_we_measure_it', ''),
            'implementation_phase': self.request.GET.get('implementation_phase', ''),
            'target_quarter': self.request.GET.get('target_quarter', ''),
        }
        return ctx


class KPIFilterView(KPITableView):
    """Handles HTMX filter requests, returns just the table section."""
    template_name = 'kpi/partials/table_section.html'


class KPIDetailView(DetailView):
    model = KPI
    template_name = 'kpi/partials/kpi_detail.html'
    context_object_name = 'kpi'

    def get_queryset(self):
        return KPI.objects.prefetch_related('contributes_to', 'supported_by')


class KPICreateView(CreateView):
    model = KPI
    template_name = 'kpi/partials/form_modal.html'
    fields = [
        'name', 'level', 'kpi_type', 'description', 'owner',
        'why_important', 'do_we_measure_it', 'how_measure_it',
        'where_store', 'review_cadence', 'influences', 'initiatives',
        'notes', 'lifecycle_phase', 'journey_phase', 'step',
        'impact', 'effort', 'implementation_phase', 'target_quarter',
        'contributes_to',
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        level = self.request.GET.get('level', '')
        if not level and self.request.POST:
            level = self.request.POST.get('level', '')
        if level:
            allowed_levels = {
                'business_kpi': ['business_kpi'],
                'kpi': ['business_kpi'],
                'metric': ['business_kpi', 'kpi'],
            }
            target_levels = allowed_levels.get(level, [])
            form.fields['contributes_to'].queryset = KPI.objects.filter(
                level__in=target_levels
            ).order_by('name')
        else:
            form.fields['contributes_to'].queryset = KPI.objects.filter(
                level__in=['business_kpi', 'kpi']
            ).order_by('name')
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add KPI'
        return ctx

    def get_success_url(self):
        referer = self.request.META.get('HTTP_REFERER', '')
        if '/journey/' in referer:
            return referer
        return reverse_lazy('kpi:table')


class KPIUpdateView(UpdateView):
    model = KPI
    template_name = 'kpi/partials/form_modal.html'
    fields = [
        'name', 'level', 'kpi_type', 'description', 'owner',
        'why_important', 'do_we_measure_it', 'how_measure_it',
        'where_store', 'review_cadence', 'influences', 'initiatives',
        'notes', 'lifecycle_phase', 'journey_phase', 'step',
        'impact', 'effort', 'implementation_phase', 'target_quarter',
        'contributes_to',
    ]

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        obj = self.get_object()
        allowed_levels = {
            'business_kpi': ['business_kpi'],
            'kpi': ['business_kpi'],
            'metric': ['business_kpi', 'kpi'],
        }
        target_levels = allowed_levels.get(obj.level, [])
        form.fields['contributes_to'].queryset = KPI.objects.filter(
            level__in=target_levels
        ).exclude(pk=obj.pk).order_by('name')
        return form

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Edit KPI'
        return ctx

    def get_success_url(self):
        referer = self.request.META.get('HTTP_REFERER', '')
        if '/journey/' in referer:
            return referer
        return reverse_lazy('kpi:table')


class KPIDeleteView(DeleteView):
    model = KPI
    template_name = 'kpi/partials/delete_confirm.html'

    def get_success_url(self):
        referer = self.request.META.get('HTTP_REFERER', '')
        if '/journey/' in referer:
            return referer
        return reverse_lazy('kpi:table')


class PrioritizeView(TemplateView):
    template_name = 'kpi/prioritize.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        kpis = KPI.objects.select_related(
            'lifecycle_phase', 'journey_phase'
        ).filter(impact__isnull=False, effort__isnull=False)

        lc_filter = self.request.GET.get('lifecycle_phase', '')
        owner_filter = self.request.GET.get('owner', '')

        if lc_filter:
            kpis = kpis.filter(lifecycle_phase_id=lc_filter)
        if owner_filter:
            kpis = kpis.filter(owner__icontains=owner_filter)

        kpis = list(kpis)

        ctx['quick_wins'] = [k for k in kpis if k.impact >= 4 and k.effort <= 2]
        ctx['strategic'] = [k for k in kpis if k.impact >= 4 and k.effort >= 3]
        ctx['fill_ins'] = [k for k in kpis if k.impact <= 3 and k.effort <= 2]
        ctx['avoid'] = [k for k in kpis if k.impact <= 3 and k.effort >= 3]

        unscored_qs = KPI.objects.filter(Q(impact__isnull=True) | Q(effort__isnull=True))
        if lc_filter:
            unscored_qs = unscored_qs.filter(lifecycle_phase_id=lc_filter)
        if owner_filter:
            unscored_qs = unscored_qs.filter(owner__icontains=owner_filter)
        ctx['unscored'] = unscored_qs.count()
        ctx['total_scored'] = len(kpis)
        ctx['show_filtered'] = bool(lc_filter or owner_filter)

        from journey.models import Phase
        ctx['lifecycle_phase_choices'] = Phase.objects.order_by('order')
        ctx['active_owner'] = owner_filter
        ctx['active_lifecycle_phase'] = lc_filter
        return ctx

    def get_template_names(self):
        if self.request.htmx:
            return ['kpi/partials/prioritize_grid.html']
        return [self.template_name]


class RoadmapView(TemplateView):
    template_name = 'kpi/roadmap.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        kpis = KPI.objects.select_related(
            'lifecycle_phase', 'journey_phase'
        ).exclude(target_quarter='').order_by(
            'target_quarter', 'lifecycle_phase__order'
        )

        lc_filter = self.request.GET.get('lifecycle_phase', '')
        owner_filter = self.request.GET.get('owner', '')

        if lc_filter:
            kpis = kpis.filter(lifecycle_phase_id=lc_filter)
        if owner_filter:
            kpis = kpis.filter(owner__icontains=owner_filter)

        from journey.models import Phase

        # Always show all quarters from the full dataset
        all_q_kpis = KPI.objects.exclude(target_quarter='').order_by('target_quarter')
        quarters = list(dict.fromkeys(k.target_quarter for k in all_q_kpis))

        ctx['lifecycle_phase_choices'] = Phase.objects.order_by('order')
        ctx['owner_choices'] = KPI.objects.exclude(owner='').values_list('owner', flat=True).distinct().order_by('owner')
        ctx['active_owner'] = owner_filter
        ctx['active_lifecycle_phase'] = lc_filter
        ctx['quarters'] = quarters
        ctx['all_kpis'] = list(kpis)
        ctx['show_filtered'] = bool(lc_filter or owner_filter)
        return ctx

    def get_template_names(self):
        if self.request.htmx:
            return ['kpi/partials/roadmap_grid.html']
        return [self.template_name]
