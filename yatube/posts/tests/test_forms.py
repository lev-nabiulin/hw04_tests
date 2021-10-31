from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()

class PostFormFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug',
            description='Описание группы',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )
        cls.post_after_edit = {
            'text': 'Текст поста после изменения',
            'group': cls.group.id,
        }
        cls.post_guest_create = {
            'text': 'Текст поста',
            'group': cls.group.id,
        }

    def setUp(self):
        self.authorized_user = Client()
        self.authorized_user.force_login(self.user)
        
    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост',
            'author': self.user,
            'group': self.group.id,
        }
        response = self.authorized_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', args={self.user.username})
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post_prev = Post.objects.order_by('id')
        post = post_prev.last()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, form_data['author'])
        self.assertEqual(post.group.id, form_data['group'])

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        posts_count = Post.objects.count()
        response = self.authorized_user.post(
            reverse('posts:post_edit', args={self.post.pk}),
            data=self.post_after_edit,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', args={self.post.pk})
        )
        self.assertEqual(Post.objects.count(), posts_count)

        post_edit = Post.objects.filter(
            text=self.post_after_edit['text'],
            author=self.user,
            group=self.group,
        )
        self.assertTrue(post_edit.exists())
       

    def test_guest_cant_create_post(self):
        posts_count = Post.objects.count()
        response = self.client.post(
            reverse('posts:post_create'),
            data=self.post_guest_create,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse('posts:post_create')
        )
        self.assertFalse(
            Post.objects.filter(
                text=self.post_guest_create['text'],
                group=self.post_guest_create['group'],
                author=self.user,
            ).exists()
        )

    def test_guest_cant_edit_post(self):
        posts_count = Post.objects.count()
        response = self.client.post(
            reverse('posts:post_edit', args={self.post.pk}),
            data=self.post_after_edit,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse('users:login') + '?next=' + reverse('posts:post_edit', args={self.post.pk})
        )
        self.assertFalse(
            Post.objects.filter(
                text=self.post_after_edit['text'],
                group=self.post_after_edit['group'],
                author=self.user,
            ).exists()
        )