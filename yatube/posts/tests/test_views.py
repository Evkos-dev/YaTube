import tempfile
import shutil
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.template.defaultfilters import truncatechars
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.MEDIA_ROOT)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Vasya')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый коммент',
            author=cls.user,
            post_id=cls.post.id
        )

    def SetUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_uses_correct_template_for_authorized(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'Vasya'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.id}'}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            cache.clear()
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_uses_correct_template_for_guest(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'Vasya'}
            ): 'posts/profile.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.guest_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_group_0, self.post.group)
        self.assertTrue(post_image_0, 'posts/small.gif')

    def test_group_posts_page_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_posts',
                kwargs={'slug': 'test-slug'}
            ))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        group_title_0 = first_object.group.title
        group_slug_0 = first_object.group.slug
        group_description_0 = first_object.group.description
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_group_0, self.post.group)
        self.assertTrue(post_image_0, 'posts/small.gif')
        self.assertEqual(group_title_0, self.post.group.title)
        self.assertEqual(group_slug_0, self.post.group.slug)
        self.assertEqual(group_description_0, self.post.group.description)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{self.post.id}'}
            ))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').author, self.post.author)
        self.assertEqual(response.context.get('post').group, self.post.group)
        self.assertEqual(
            response.context.get('title'),
            f'Пост: {truncatechars(self.post.text, 30)}'
        )
        self.assertTrue(response.context.get('post').image, 'posts/small.gif')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'Vasya'}
            ))
        self.assertEqual(
            response.context['page_obj'][0].text,
            self.post.text
        )
        self.assertEqual(
            response.context['page_obj'][0].author,
            self.post.author
        )
        self.assertEqual(
            response.context['page_obj'][0].group,
            self.post.group
        )
        self.assertEqual(
            response.context.get('title'),
            'Профиль пользователя Vasya'
        )
        self.assertTrue(
            response.context['page_obj'][0].image,
            'posts/small.gif'
        )

    def test_post_create_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{self.post.id}'}
            ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertEqual(
            response.context.get('post_id'),
            self.post.id
        )
        self.assertEqual(response.context.get('is_edit'), True)

    def test_first_pages_contains_ten_records(self):
        number_of_posts: int = 12
        for post_num in range(number_of_posts):
            Post.objects.create(
                author=self.user,
                text='Тестовый текст %s' % post_num,
                group=self.group,
            )
        page_names = {
            'index': reverse('posts:index'),
            'group_posts': reverse(
                'posts:group_posts',
                kwargs={'slug': 'test-slug'}
            ),
            'profile': reverse('posts:profile', kwargs={'username': 'Vasya'}),
        }
        for value in page_names.values():
            cache.clear()
            with self.subTest(value=value):
                response = self.client.get(value)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_pages_contains_three_records(self):
        number_of_posts: int = 12
        for post_num in range(number_of_posts):
            Post.objects.create(
                author=self.user,
                text='Тестовый текст %s' % post_num,
                group=self.group,
            )
        page_names = {
            'index': reverse('posts:index'),
            'group_posts': reverse(
                'posts:group_posts',
                kwargs={'slug': 'test-slug'}
            ),
            'profile': reverse('posts:profile', kwargs={'username': 'Vasya'}),
        }
        for value in page_names.values():
            with self.subTest(value=value):
                response = self.client.get(value + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_posts_slug2_post_is_not_here(self):
        self.group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание',
        )
        response = (
            self.authorized_client.
            get(reverse('posts:group_posts', kwargs={'slug': 'test-slug2'}))
        )
        self.assertNotEqual(
            response.context.get('group').title,
            self.post.group.title
        )

    def test_added_comment_in_page(self):
        response = (
            self.authorized_client.
            get(reverse('posts:post_detail', args=(self.post.id,)))
        )
        self.assertEqual(
            response.context['comments'][0].text,
            self.comment.text
        )


class CachePagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Sasha')
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Тестовая группа 5',
            slug='test-slug5',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст 5',
            group=cls.group,
        )

    def test_cache_index_page(self):
        """Проверка кеширования главной старницы"""
        response = self.authorized_client.get(reverse('posts:index'))
        reference_content = response.content
        self.post.delete()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(reference_content, response.content)
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(reference_content, response.content)


class TestFollowViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Zhenya')
        cls.user_2 = User.objects.create_user(username='Q')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user_2)
        cls.group = Group.objects.create(
            title='Тестовая группа 6',
            slug='test-slug6',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст 6',
            group=cls.group,
        )

    def test_follow_for_authorized(self):
        response = self.authorized_client.get(
            reverse('posts:profile_follow', args=(self.user,))
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_2, author=self.user
            ).exists()
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            args=(self.user,)
        ))

    def test_unfollow_for_authorized(self):
        response = self.authorized_client.get(
            reverse('posts:profile_unfollow', args=(self.user,))
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_2, author=self.user
            ).exists()
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            args=(self.user,)
        ))

    def test_new_content_for_follower_and_unfollower(self):
        self.follower = Follow.objects.create(
            user=self.user_2, author=self.user
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        reference_content = response.content
        self.assertEqual(
            response.context['page_obj'][0].text,
            'Тестовый текст 6'
        )
        self.follower.delete()
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotEqual(response.content, reference_content)
