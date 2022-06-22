from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()

symbols_text: int = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост для проверки моделей',
        )

    def test_model_post_have_correct_str(self):
        """Проверяем, что у модели post корректно работает __str__."""
        post = PostModelTest.post
        expected_post_str = post.text[:symbols_text]
        self.assertEqual(expected_post_str, str(post))

    def test_model_group_have_correct_str(self):
        """Проверяем, что у модели group корректно работает __str__."""
        group = PostModelTest.group
        expected_group_str = group.title
        self.assertEqual(expected_group_str, str(group))
