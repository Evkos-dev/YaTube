from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from django.core.cache import cache

from ..models import Group, Post, Comment

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Vasya')
        cls.user_2 = User.objects.create_user(username='Petya')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый коммент',
        )

    def test_urls_for_guest(self):
        """Страницы доступны любому пользователю."""
        url_names = {
            '/': 200,
            '/group/test-slug/': 200,
            '/profile/Vasya/': 200,
            f'/posts/{PostURLTests.post.id}/': 200,
        }
        for address, code in url_names.items():
            with self.subTest(code=code):
                response = self.guest_client.get(address)
                self.assertEqual(
                    response.status_code,
                    code,
                    f'Ошибка в {address}'
                )

    def test_urls_for_authorized(self):
        """Страницы доступны авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_client.get('/follow/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_anonymous(self):
        """Страницы перенаправляют анонимного пользователя."""
        url_names = {
            '/create/': 302,
            f'/posts/{PostURLTests.post.id}/edit/': 302,
            f'/posts/{PostURLTests.post.id}/comment/': 302,
            '/profile/Vasya/follow/': 302,
            '/profile/Vasya/unfollow/': 302,
            '/follow/': 302,
        }
        for address, code in url_names.items():
            with self.subTest(code=code):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, code)

    def test_edit_post_url(self):
        response = self.authorized_client.get(
            f'/posts/{PostURLTests.post.id}/edit/'
        )
        self.assertEqual(response.status_code, 200)

    def test_url_for_404(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)

    def test_urls_uses_correct_template_authorized(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/Vasya/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html',
        }
        for address, template in templates_url_names.items():
            cache.clear()
            with self.subTest(template=template):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_guest(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/Vasya/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
        }
        for address, template in templates_url_names.items():
            cache.clear()
            with self.subTest(template=template):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_redirect_urls_authorized_client(self):
        url_names = [
            f'/posts/{PostURLTests.post.id}/comment/',
            '/profile/Vasya/follow/',
            '/profile/Vasya/unfollow/',
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)
