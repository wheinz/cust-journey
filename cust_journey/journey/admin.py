from django.contrib import admin

from .models import Action, JourneyPhase, Phase, Step, Touchpoint


@admin.register(Phase)
class PhaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(JourneyPhase)
class JourneyPhaseAdmin(admin.ModelAdmin):
    list_display = ['name', 'phase', 'slug', 'order']
    list_filter = ['phase']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Step)
class StepAdmin(admin.ModelAdmin):
    list_display = ['name', 'journey_phase', 'slug', 'order']
    list_filter = ['journey_phase__phase', 'journey_phase']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ['name', 'step', 'is_drop_off', 'order']
    list_filter = ['step__journey_phase__phase', 'step', 'is_drop_off']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']


@admin.register(Touchpoint)
class TouchpointAdmin(admin.ModelAdmin):
    list_display = ['name', 'step', 'order']
    list_filter = ['step__journey_phase__phase', 'step']
