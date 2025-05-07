"""
URL configuration for blog_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path # Убедимся, что include не используется, если не нужен
from django.conf import settings # Импорт для настроек
from django.conf.urls.static import static # Импорт для статики/медиа
from ninja import NinjaAPI # Импорт NinjaAPI
from django.views.generic import RedirectView # Для поддержки /api без слэша

# Инициализация API для Django Ninja
# В будущем сюда будут добавляться роутеры из приложений apps.users и apps.blog
api = NinjaAPI(
    version="1.0.0",
    title="Blog API",
    description="API для управления блогом, статьями и комментариями.",
    # csrf=True # Раскомментируйте, если нужна CSRF защита для HTML форм в Ninja (обычно не для REST API)
)

@api.get("", auth=None, summary="Health check", operation_id="api_root")
def api_root(request):
    """
    Простой health-check эндпоинт, проверка доступности API.
    """
    return {"message": "Blog API is running. See /api/docs for docs."}

# Подключаем роутеры приложений
from apps.users.api import router as users_router
from apps.blog.api import router as blog_router # Добавляем импорт

api.add_router("/users", users_router) # Без trailing slash, если в users_router пути начинаются с /
api.add_router("/blog", blog_router) # Добавляем роутер блога к /api/blog/

urlpatterns = [
    path('admin/', admin.site.urls),
    # Редирект /api на /api/ для корректного отображения API
    path('api', RedirectView.as_view(url='/api/', permanent=False)),
    path('api/', api.urls), # основной маршрут API
]

# Добавляем маршруты для статических и медиа файлов в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
