from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, TemplateView, UpdateView

from .models import Action, JourneyPhase, Phase, Step
from kpi.models import KPI


class JourneyHomeView(TemplateView):
    template_name = 'journey/journey_home.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['phases'] = Phase.objects.prefetch_related(
            'journey_phases__steps__actions',
            'journey_phases__steps__touchpoints',
        )
        return ctx


class PhaseDetailView(DetailView):
    model = Phase
    template_name = 'journey/partials/detail_panel.html'
    context_object_name = 'node'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['node_type'] = 'phase'
        ctx['children'] = self.object.journey_phases.prefetch_related('steps__actions')
        ctx['kpis'] = self.object.kpis.all()
        return ctx


class JourneyPhaseDetailView(DetailView):
    model = JourneyPhase
    template_name = 'journey/partials/detail_panel.html'
    context_object_name = 'node'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['node_type'] = 'journey_phase'
        ctx['steps'] = self.object.steps.prefetch_related('actions', 'touchpoints', 'kpis')
        ctx['kpis'] = self.object.kpis.all()
        return ctx


class StepDetailView(DetailView):
    model = Step
    template_name = 'journey/partials/detail_panel.html'
    context_object_name = 'node'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['node_type'] = 'step'
        ctx['step'] = self.object
        ctx['actions'] = self.object.actions.all()
        ctx['touchpoints'] = self.object.touchpoints.all()
        ctx['kpis'] = self.object.kpis.all()
        return ctx


# --- CRUD views (admin only, not shown in frontend) ---

class PhaseCreateView(CreateView):
    model = Phase
    template_name = 'journey/partials/form_modal.html'
    fields = ['name', 'slug', 'order', 'description']
    success_url = reverse_lazy('journey:home')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add Lifecycle Phase'
        return ctx


class PhaseUpdateView(UpdateView):
    model = Phase
    template_name = 'journey/partials/form_modal.html'
    fields = ['name', 'slug', 'order', 'description']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Edit Lifecycle Phase'
        return ctx

    def get_success_url(self):
        return reverse_lazy('journey:phase_detail', kwargs={'pk': self.object.pk})


class PhaseDeleteView(DeleteView):
    model = Phase
    template_name = 'journey/partials/delete_confirm.html'
    success_url = reverse_lazy('journey:home')


class JourneyPhaseCreateView(CreateView):
    model = JourneyPhase
    template_name = 'journey/partials/form_modal.html'
    fields = ['phase', 'name', 'slug', 'order', 'description']
    success_url = reverse_lazy('journey:home')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add Journey Phase'
        return ctx


class JourneyPhaseUpdateView(UpdateView):
    model = JourneyPhase
    template_name = 'journey/partials/form_modal.html'
    fields = ['phase', 'name', 'slug', 'order', 'description']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Edit Journey Phase'
        return ctx

    def get_success_url(self):
        return reverse_lazy('journey:journey_phase_detail', kwargs={'pk': self.object.pk})


class JourneyPhaseDeleteView(DeleteView):
    model = JourneyPhase
    template_name = 'journey/partials/delete_confirm.html'
    success_url = reverse_lazy('journey:home')


class StepCreateView(CreateView):
    model = Step
    template_name = 'journey/partials/form_modal.html'
    fields = ['journey_phase', 'name', 'slug', 'order', 'description']
    success_url = reverse_lazy('journey:home')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add Step'
        return ctx


class StepUpdateView(UpdateView):
    model = Step
    template_name = 'journey/partials/form_modal.html'
    fields = ['journey_phase', 'name', 'slug', 'order', 'description']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Edit Step'
        return ctx

    def get_success_url(self):
        return reverse_lazy('journey:step_detail', kwargs={'pk': self.object.pk})


class StepDeleteView(DeleteView):
    model = Step
    template_name = 'journey/partials/delete_confirm.html'
    success_url = reverse_lazy('journey:home')


class ActionCreateView(CreateView):
    model = Action
    template_name = 'journey/partials/form_modal.html'
    fields = ['step', 'name', 'slug', 'order', 'is_drop_off']
    success_url = reverse_lazy('journey:home')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Add Action'
        return ctx


class ActionUpdateView(UpdateView):
    model = Action
    template_name = 'journey/partials/form_modal.html'
    fields = ['step', 'name', 'slug', 'order', 'is_drop_off']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Edit Action'
        return ctx

    def get_success_url(self):
        return reverse_lazy('journey:step_detail', kwargs={'pk': self.object.step.pk})


class ActionDeleteView(DeleteView):
    model = Action
    template_name = 'journey/partials/delete_confirm.html'
    success_url = reverse_lazy('journey:home')
