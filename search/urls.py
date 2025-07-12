"""
URLs نظام البحث المتقدم
"""

from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    # Main search page
    path('', views.SearchView.as_view(), name='search'),
    
    # Search API
    path('api/', views.SearchAPIView.as_view(), name='api'),
    path('suggestions/', views.SearchSuggestionsAPIView.as_view(), name='suggestions'),
    path('click/', views.SearchClickAPIView.as_view(), name='click'),
    
    # Popular searches
    path('popular/', views.PopularSearchesView.as_view(), name='popular'),
    
    # Saved filters
    path('filters/', views.SearchFiltersView.as_view(), name='filters'),
    path('filters/save/', views.SaveFilterAPIView.as_view(), name='save_filter'),
    path('filters/<uuid:filter_id>/delete/', views.delete_filter, name='delete_filter'),
    
    # Quick search redirect
    path('quick/', views.search_redirect, name='quick'),
]
