from django.urls import path
from . import views

app_name = 'automation'

urlpatterns = [
    path('', views.rule_list_view, name='list'),
    path('create/', views.rule_create_view, name='create'),
    path('<uuid:pk>/edit/', views.rule_edit_view, name='edit'),
    path('<uuid:pk>/delete/', views.rule_delete_view, name='delete'),
    path('logs/', views.rule_logs_view, name='logs'),
]
