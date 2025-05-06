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
from django.urls import path
from django.conf import settings # Импорт для настроек
from django.conf.urls.static import static # Импорт для статики/медиа
from ninja import NinjaAPI # Импорт NinjaAPI

# Инициализация API для Django Ninja
# В будущем сюда будут добавляться роутеры из приложений apps.users и apps.blog
api = NinjaAPI(
    title="Blog API",
    version="1.0.0",
    description="API для управления блогом, статьями и комментариями.",
    # csrf=True # Раскомментируйте, если нужна CSRF защита для HTML форм в Ninja (обычно не для REST API)
)

# Пока оставим пустым, позже добавим роутеры приложений
# from apps.users.api import router as users_router
# from apps.blog.api import router as blog_router
# api.add_router("/users/", users_router, tags=["users"])
# api.add_router("/blog/", blog_router, tags=["blog"])

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', api.urls), # Подключаем URL-адреса Django Ninja к /api/
]

# Добавляем маршруты для статических и медиа файлов в режиме DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
