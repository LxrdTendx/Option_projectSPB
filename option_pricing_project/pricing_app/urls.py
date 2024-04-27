from django.urls import path
from .views import index, get_option_data # Убедитесь, что имена совпадают с определенными в views.py
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', index, name='index'),  # обработка главной страницы
    path('get-option-data/<int:id>/', get_option_data, name='get-option-data')
    # path('result/', result, name='result'),  # обработка результатов формы
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)