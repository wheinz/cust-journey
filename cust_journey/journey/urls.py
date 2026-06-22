from django.urls import path

from . import views

app_name = 'journey'

urlpatterns = [
    path('', views.JourneyHomeView.as_view(), name='home'),

    path('phase/<int:pk>/', views.PhaseDetailView.as_view(), name='phase_detail'),
    path('journey-phase/<int:pk>/', views.JourneyPhaseDetailView.as_view(), name='journey_phase_detail'),
    path('step/<int:pk>/', views.StepDetailView.as_view(), name='step_detail'),

    path('phase/create/', views.PhaseCreateView.as_view(), name='phase_create'),
    path('journey-phase/create/', views.JourneyPhaseCreateView.as_view(), name='journey_phase_create'),
    path('step/create/', views.StepCreateView.as_view(), name='step_create'),
    path('action/create/', views.ActionCreateView.as_view(), name='action_create'),

    path('phase/<int:pk>/edit/', views.PhaseUpdateView.as_view(), name='phase_edit'),
    path('journey-phase/<int:pk>/edit/', views.JourneyPhaseUpdateView.as_view(), name='journey_phase_edit'),
    path('step/<int:pk>/edit/', views.StepUpdateView.as_view(), name='step_edit'),
    path('action/<int:pk>/edit/', views.ActionUpdateView.as_view(), name='action_edit'),

    path('phase/<int:pk>/delete/', views.PhaseDeleteView.as_view(), name='phase_delete'),
    path('journey-phase/<int:pk>/delete/', views.JourneyPhaseDeleteView.as_view(), name='journey_phase_delete'),
    path('step/<int:pk>/delete/', views.StepDeleteView.as_view(), name='step_delete'),
    path('action/<int:pk>/delete/', views.ActionDeleteView.as_view(), name='action_delete'),
]
