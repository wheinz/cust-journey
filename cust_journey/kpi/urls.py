from django.urls import path

from . import views

app_name = 'kpi'

urlpatterns = [
    path('', views.KPITableView.as_view(), name='table'),
    path('hierarchy/', views.KPIHierarchyView.as_view(), name='hierarchy'),
    path('hierarchy/<int:pk>/', views.KPIHierarchyDetailView.as_view(), name='hierarchy_detail'),
    path('prioritize/', views.PrioritizeView.as_view(), name='prioritize'),
    path('prioritize/<int:pk>/move/', views.kpi_move, name='kpi_move'),
    path('roadmap/', views.RoadmapView.as_view(), name='roadmap'),
    path('roadmap/<int:pk>/move/', views.kpi_roadmap_move, name='kpi_roadmap_move'),
    path('create/', views.KPICreateView.as_view(), name='kpi_create'),
    path('<int:pk>/edit/', views.KPIUpdateView.as_view(), name='kpi_edit'),
    path('<int:pk>/delete/', views.KPIDeleteView.as_view(), name='kpi_delete'),
    path('filter/', views.KPIFilterView.as_view(), name='kpi_filter'),
]
