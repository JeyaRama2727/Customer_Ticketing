from django.urls import path
from . import views

app_name = 'sla'

urlpatterns = [
    path('', views.sla_list_view, name='list'),
    path('create/', views.sla_create_view, name='create'),
    path('<int:pk>/edit/', views.sla_edit_view, name='edit'),
]
