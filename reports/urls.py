from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_index_view, name='index'),
    path('ticket-summary/', views.ticket_summary_report, name='ticket_summary'),
    path('agent-performance/', views.agent_performance_report, name='agent_performance'),
    path('sla-compliance/', views.sla_compliance_report, name='sla_compliance'),
]
