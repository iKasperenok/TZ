from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase # Используем APITestCase из DRF, он удобен
from rest_framework import status

# Create your tests here.

# Если SimpleTokenAuth не устанавливает request.user, а просто возвращает токен,
# то для тестов защищенных эндпоинтов нам нужно будет как-то этот токен передавать.
# Пока что для регистрации это не нужно.

class UserRegistrationLoginTests(APITestCase):
    def setUp(self):
        # Используем хардкод URL, так как reverse() с Ninja вызывает проблемы
        self.register_url = '/api/users/register'
        self.login_url = '/api/users/login'

        # Данные для тестов регистрации
        self.user_data = { # Оставляем эти имена
            'username': f'testuser_reg_{User.objects.count() + 8}', # Увеличим счетчик для уникальности
            'password': 'testpassword123'
        }
        # Создаем пользователя для теста конфликта имен при регистрации
        conflict_reg_username = f'testuser_conflict_reg_{User.objects.count() + 800}' # Увеличим счетчик
        User.objects.create_user(username=conflict_reg_username, password='somepassword')
        self.user_data_conflict = { # Оставляем это имя
            'username': conflict_reg_username, 
            'password': 'testpassword123'
        }
        # Удалены дублирующиеся self.reg_user_data и self.reg_user_data_conflict

        # Данные и пользователь для тестов логина
        self.login_test_username = f'testuser_login_{User.objects.count() + 80}' # Увеличим счетчик
        self.login_test_password = 'login_password_123'
        User.objects.create_user(username=self.login_test_username, password=self.login_test_password)


    def test_successful_registration(self):
        """
        Тест успешной регистрации нового пользователя.
        Ожидаем HTTP 201 Created.
        """
        # Использует self.user_data
        response = self.client.post(self.register_url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertTrue(User.objects.filter(username=self.user_data['username']).exists())
        
        response_data = response.json()
        self.assertIn('token', response_data)
        self.assertIsNotNone(response_data['token'])
        self.assertEqual(len(response_data['token']), 256)

    def test_registration_username_conflict(self):
        """
        Тест регистрации с уже существующим именем пользователя.
        Ожидаем HTTP 409 Conflict.
        """
        # Использует self.user_data_conflict
        response = self.client.post(self.register_url, self.user_data_conflict, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT, response.content)
        
        response_data = response.json()
        self.assertIn('detail', response_data)
        expected_error_message = f"Пользователь с именем '{self.user_data_conflict['username']}' уже существует."
        self.assertEqual(response_data['detail'], expected_error_message)

    # --- Тесты для эндпоинта входа --- 

    def test_successful_login(self):
        """ Тест успешного входа пользователя с корректными данными. """
        login_data = {
            'username': self.login_test_username,
            'password': self.login_test_password
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
        response_data = response.json()
        self.assertIn('token', response_data)
        self.assertIsNotNone(response_data['token'])
        self.assertEqual(len(response_data['token']), 256)

    def test_login_wrong_password(self):
        """ Тест входа пользователя с неверным паролем. """
        login_data = {
            'username': self.login_test_username,
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, response.content)
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertEqual(response_data['detail'], "Неверные учетные данные.")

    def test_login_nonexistent_user(self):
        """ Тест входа с несуществующим именем пользователя. """
        login_data = {
            'username': 'nonexistentuser',
            'password': 'anypassword'
        }
        response = self.client.post(self.login_url, login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, response.content)
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertEqual(response_data['detail'], "Неверные учетные данные.")

    # --- Тесты валидации данных при регистрации --- 

    def test_registration_invalid_data_empty(self):
        """ Тест регистрации с пустыми полями (ошибка валидации). """
        invalid_data = {
            'username': '',
            'password': ''
        }
        response = self.client.post(self.register_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY, response.content)
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertIsInstance(response_data['detail'], list)
        
        # Проверяем наличие ошибок для username и password в списке деталей
        has_username_error = any(err.get('loc') == ['body', 'payload', 'username'] for err in response_data['detail'])
        has_password_error = any(err.get('loc') == ['body', 'payload', 'password'] for err in response_data['detail'])
        
        self.assertTrue(has_username_error, "Ошибка для 'username' не найдена в деталях.")
        # Пароль также должен иметь ошибку (пустая строка короче 8 символов)
        self.assertTrue(has_password_error, "Ошибка для 'password' не найдена в деталях.")

    def test_registration_invalid_data_short_password(self):
        """ Тест регистрации со слишком коротким паролем. """
        # Валидация min_length=8 в UserRegisterSchema должна вернуть 422
        invalid_data = {
            'username': f'testuser_shortpass_{User.objects.count() + 9}',
            'password': '123'
        }
        response = self.client.post(self.register_url, invalid_data, format='json')
        # Ожидаем 422 из-за короткого пароля
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY, response.content)
        response_data = response.json()
        self.assertIn('detail', response_data)
        self.assertIsInstance(response_data['detail'], list)

        # Ищем конкретную ошибку для пароля
        password_error_found = False
        for error in response_data['detail']:
            if error.get('loc') == ['body', 'payload', 'password']:
                password_error_found = True
                self.assertIn("String should have at least 8 characters", error.get('msg', ''))
                break
        self.assertTrue(password_error_found, "Ошибка валидации длины пароля не найдена.")

    # TODO: Добавить еще тесты валидации, если необходимо
