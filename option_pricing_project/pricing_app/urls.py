from django.urls import path
from .views import index, get_option_data # Убедитесь, что имена совпадают с определенными в views.py

urlpatterns = [
    path('', index, name='index'),  # обработка главной страницы
    path('get-option-data/<int:id>/', get_option_data, name='get-option-data')
    # path('result/', result, name='result'),  # обработка результатов формы
]