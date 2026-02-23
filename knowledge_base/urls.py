from django.urls import path
from . import views

app_name = 'knowledge_base'

urlpatterns = [
    # Public KB
    path('', views.kb_home_view, name='home'),
    path('search/', views.kb_search_view, name='search'),
    path('category/<slug:slug>/', views.kb_category_view, name='category'),
    path('article/<slug:slug>/', views.kb_article_view, name='article'),
    path('article/<slug:slug>/feedback/', views.kb_article_feedback, name='article_feedback'),

    # Staff management
    path('manage/', views.kb_manage_list_view, name='manage'),
    path('manage/create/', views.kb_article_create_view, name='article_create'),
    path('manage/<slug:slug>/edit/', views.kb_article_edit_view, name='article_edit'),
]
