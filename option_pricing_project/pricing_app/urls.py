from django.urls import path
from . import views

urlpatterns = [
    path('', views.option_series_view, name='option_series_view'),
]