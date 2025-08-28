from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


class UserProfileTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='pass')

    def test_profile_created_on_user_creation(self):
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_profile_view_requires_login(self):
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_profile_view_logged_in(self):
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_profile_edit(self):
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, {
            'bio': 'Updated bio',
            'fitness_goal': 'Get stronger'
        })
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Updated bio')
        self.assertEqual(self.user.profile.fitness_goal, 'Get stronger')

    def test_profile_edit_requires_login(self):
        url = reverse('users:profile_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_profile_edit_invalid_data(self):
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.post(url, {
            'bio': 'Bio',
            'fitness_goal': 'x' * 101  # Exceeds max_length
        })
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('fitness_goal', form.errors)
        self.assertIn('Ensure this value has at most 100 characters', form.errors['fitness_goal'][0])

    def test_profile_str_method(self):
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(str(profile), f"{self.user.username}'s Profile")

    def test_profile_avatar_field_blank(self):
        profile = Profile.objects.get(user=self.user)
        self.assertTrue(profile.avatar.name == '' or profile.avatar is None)
