from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django import forms

from ..models import Group, Post

User = get_user_model()


class PostViewTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        cls.groups = [
            Group.objects.create(
                title='Тестовая группа',
                slug='first',
                description='Тестовая группа',
            ),
        ]
        cls.group = cls.groups[0]
        cls.posts = [
            Post.objects.create(
                text='Тестовый пост',
                author=cls.author,
                group=cls.group,
            ),
        ]
        cls.post = cls.posts[0]

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_correct_template(self):

        url_templates_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile', args={self.author.username}):
            'posts/profile.html',
            reverse('posts:post_edit', args={self.post.pk}):
            'posts/create_post.html',
            reverse('posts:post_detail', args={self.post.pk}):
            'posts/post_detail.html',
            reverse('posts:group_list', args={self.group.slug}):
            'posts/group_list.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in url_templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_list_context(self):

        urls_posts = {
            reverse('posts:index'): len(self.posts),
            reverse('posts:profile', args={self.author.username}):
                self.author.posts.count(),
        }
        for group in self.groups:
            arg = group.slug
            key = reverse('posts:group_list', args={arg})
            value = group.posts.count()
            urls_posts[key] = value
        for reverse_name, object in urls_posts.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                self.assertIn('posts', response.context)
                self.assertEqual(len(response.context['posts']), object)

    def test_post_context(self):

        urls = [
            reverse('posts:index'),
            reverse('posts:profile', args={self.author.username}),
            reverse('posts:group_list', args={self.group.slug}),
        ]
        for reverse_name in urls:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                first_object = response.context['posts'][0]
                post_text = first_object.text
                post_author = first_object.author.username
                post_group = first_object.group.id
                post_user = first_object.author.id
                post_group_title = first_object.group.title
                self.assertEqual(post_user, self.author.id)
                self.assertEqual(post_group_title, self.group.title)
                self.assertEqual(post_text, self.post.text)
                self.assertEqual(post_author, self.author.username)
                self.assertEqual(post_group, self.group.id)
                """Проверка ID поста."""
                response = self.authorized_author.get(
                    reverse('posts:post_detail', args={self.post.pk}))
                post = response.context['post']
                self.assertEqual(post.pk, self.post.pk)

    def test_group_context(self):

        response = self.authorized_author.get(
            reverse('posts:group_list', args={self.group.slug})
        )
        post = response.context['posts'][0]
        self.assertEqual(post.pk, self.post.pk)

    def test_form_context(self):

        urls = [
            reverse('posts:post_edit', args={self.post.pk}),
            reverse('posts:post_create'),
        ]
        for reverse_name in urls:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse_name)
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                }
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value)
                        self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Описание группы',
        )
        number_of_posts = 13
        cls.posts = []
        for post_id in range(number_of_posts):
            post = Post.objects.create(
                text=f'Тестовый пост {post_id}',
                author=cls.author,
                group=cls.group,
            )
            cls.posts.append(post)
        cls.urls_with_paginator = [
            reverse('posts:index'),
            reverse('posts:profile', args={cls.author.username}),
            reverse('posts:group_list', args={cls.group.slug}),
        ]

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_first_page_contains_ten_records(self):

        response = self.authorized_author.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), settings.PAGE_POST)

    def test_second_page_contains_three_records(self):

        response = self.authorized_author.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
