from django.urls import path
from .views import index # Убедитесь, что имена совпадают с определенными в views.py

urlpatterns = [
    path('', index, name='index'),  # обработка главной страницы
    # path('result/', result, name='result'),  # обработка результатов формы
]