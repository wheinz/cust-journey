from django.urls import path

from . import views

app_name = 'kpi'

urlpatterns = [
    path('', views.KPITableView.as_view(), name='table'),
    path('hierarchy/', views.KPIHierarchyView.as_view(), name='hierarchy'),
    path('hierarchy/<int:pk>/', views.KPIHierarchyDetailView.as_view(), name='hierarchy_detail'),
    path('prioritize/', views.PrioritizeView.as_view(), name='prioritize'),
    path('roadmap/', views.RoadmapView.as_view(), name='roadmap'),
    path('<int:pk>/', views.KPIDetailView.as_view(), name='kpi_detail'),
    path('create/', views.KPICreateView.as_view(), name='kpi_create'),
    path('<int:pk>/edit/', views.KPIUpdateView.as_view(), name='kpi_edit'),
    path('<int:pk>/delete/', views.KPIDeleteView.as_view(), name='kpi_delete'),
    path('filter/', views.KPIFilterView.as_view(), name='kpi_filter'),
]
