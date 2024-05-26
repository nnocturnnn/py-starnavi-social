from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Like, Post

User = get_user_model()


class UserTests(APITestCase):
    def setUp(self):
        self.signup_url = reverse('user-signup')
        self.login_url = reverse('user-login')
        self.activity_url = reverse('user-activity')
        self.user_data = {
            'username': 'testuser99',
            'email': 'testuser@example.com',
            'password': 'Testpass123'
        }

    def test_user_signup(self):
        response = self.client.post(self.signup_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], self.user_data['username'])

    def test_user_login(self):
        self.client.post(self.signup_url, self.user_data)
        response = self.client.post(self.login_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_user_activity(self):
        self.client.post(self.signup_url, self.user_data)
        login_response = self.client.post(self.login_url, {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        })
        token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(self.activity_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('last_login', response.data)
        self.assertIn('last_request', response.data)


class PostTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.post_url = reverse('post-list')
        self.like_url = lambda pk: reverse('post-like', kwargs={'pk': pk})
        self.unlike_url = lambda pk: reverse('post-unlike', kwargs={'pk': pk})
        self.analytics_url = reverse('post-analytics')

    def test_post_creation(self):
        response = self.client.post(
            self.post_url, {'title': 'Test Post', 'body': 'This is a test post.'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['post']['title'], 'Test Post')

    def test_post_like(self):
        post = Post.objects.create(
            user=self.user, title='Test Post', body='This is a test post.')
        response = self.client.post(self.like_url(post.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'Post liked successfully')

    def test_post_unlike(self):
        post = Post.objects.create(
            user=self.user, title='Test Post', body='This is a test post.')
        self.client.post(self.like_url(post.pk))
        response = self.client.post(self.unlike_url(post.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status', response.data)
        self.assertEqual(response.data['status'], 'Post unliked successfully')

    def test_analytics(self):
        post1 = Post.objects.create(
            user=self.user, title='Test Post 1', body='This is a test post 1.')
        post2 = Post.objects.create(
            user=self.user, title='Test Post 2', body='This is a test post 2.')
        like1 = Like.objects.create(user=self.user, post=post1)
        like2 = Like.objects.create(user=self.user, post=post2)
        date_from = (like1.date - timezone.timedelta(days=1)).strftime('%Y-%m-%d')
        date_to = (like2.date + timezone.timedelta(days=1)).strftime('%Y-%m-%d')
        response = self.client.get(
            self.analytics_url, {'date_from': date_from, 'date_to': date_to})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertTrue(len(response.data['data']) > 0)
