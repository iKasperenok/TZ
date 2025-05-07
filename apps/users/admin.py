from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

# Можно расширить стандартный UserAdmin, если потребуется кастомизация
# class UserAdmin(BaseUserAdmin):
#     pass # Добавьте здесь свои настройки list_display, list_filter, search_fields и т.д.

# Если стандартное отображение User в админке устраивает и django.contrib.auth уже в INSTALLED_APPS,
# то явная регистрация User здесь не строго обязательна, но может быть полезна для будущих кастомизаций.
# Если вы хотите использовать свой UserAdmin, раскомментируйте и зарегистрируйте его:
# admin.site.unregister(User) # Сначала отменить стандартную регистрацию
# admin.site.register(User, UserAdmin)

# На данном этапе, чтобы просто отметить шаг, оставим файл таким.
# Если стандартная регистрация User устраивает, этот файл может даже оставаться пустым
# или содержать только комментарии о возможной будущей кастомизации.
