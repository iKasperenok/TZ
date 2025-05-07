from django.db import models
from django.conf import settings # Для ссылки на AUTH_USER_MODEL
import secrets
import string

# Create your models here.

class AuthToken(models.Model):
    key = models.CharField(max_length=256, primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name='auth_token_custom', # Изменено с auth_token, чтобы не конфликтовать с DRF, если он когда-либо будет добавлен
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            # Генерация ключа вынесена в сервисы, но на всякий случай,
            # если объект будет создан напрямую без использования сервиса,
            # хотя в данном проекте предполагается использование сервисов.
            # В контексте этого проекта, ключ должен генерироваться и присваиваться до вызова save()
            # из сервиса generate_auth_token_for_user.
            # Оставим здесь генерацию как запасной вариант, но основной поток - через сервисы.
            alphabet = string.ascii_letters + string.digits
            self.key = ''.join(secrets.choice(alphabet) for _ in range(256))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Token for {self.user.username}"
