from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Category, Test, Question, AnswerOption, TestAttempt


class QuizPlatformTests(APITestCase):

    def setUp(self):
        # Полномочия пользователей
        self.user = User.objects.create_user(username='john', email='john@ex.com', password='password123')
        self.admin = User.objects.create_superuser(username='admin', email='admin@ex.com', password='adminpassword')

        # Данные
        self.category = Category.objects.create(name='Python', description='Python tests')
        self.test = Test.objects.create(
            title='Python Basics', category=self.category,
            time_limit=30, passing_score=70, is_active=True
        )
        self.question = Question.objects.create(
            test=self.test, text='What is DRF?', question_type='single_choice', points=1
        )
        self.opt1 = AnswerOption.objects.create(question=self.question, text='Framework', is_correct=True)
        self.opt2 = AnswerOption.objects.create(question=self.question, text='DB', is_correct=False)

    def test_user_flow_passing_test(self):
        # 1. Авторизация
        response = self.client.post(reverse('token_obtain_pair'), {'username': 'john', 'password': 'password123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # 2. Старт теста
        url = reverse('test-start', kwargs={'pk': self.test.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        attempt_id = response.data['attempt_id']

        # 3. Получение вопросов (проверка, что скрыт is_correct)
        url = reverse('attempt-questions', kwargs={'pk': attempt_id})
        response = self.client.get(url)
        self.assertNotIn('is_correct', str(response.data))

        # 4. Отправка правильного ответа
        url = reverse('attempt-answer', kwargs={'pk': attempt_id})
        response = self.client.post(url, {"question_id": self.question.id, "selected_options": [self.opt1.id]},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 5. Завершение теста
        url = reverse('attempt-finish', kwargs={'pk': attempt_id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['score'], 100)
        self.assertTrue(response.data['is_passed'])