from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


class UserProfileTests(TestCase):
    """Tests for the users app focusing on Profile creation and views."""
    def setUp(self):
        # Create a reusable test user for the profile-related tests
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='pass'
        )

    def test_profile_created_on_user_creation(self):
        # Creating a User should also created a related profile via signal
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_profile_view_requires_login(self):
        # The  profile view should redirect anonymous users to login
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_profile_view_logged_in(self):
        # Logged-in users should be able to view their profile page
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # the response should contain the username to confirm correct context
        self.assertContains(response, self.user.username)

    def test_profile_edit(self):
        # Authenticated users should be able to edit their profile via POST
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Submit valid data and expect a redirect on success
        response = self.client.post(url, {
            'bio': 'Updated bio',
            'fitness_goal': 'Get stronger'
        })
        self.assertEqual(response.status_code, 302)
        # Refresh and assert that changes persisted to the DB
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.bio, 'Updated bio')
        self.assertEqual(self.user.profile.fitness_goal, 'Get stronger')

    def test_profile_edit_requires_login(self):
        # The edit page should redirect anonymous users to login
        url = reverse('users:profile_edit')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_profile_edit_invalid_data(self):
        # Submitting invalid data (too long fitness_goal) should
        # re-render the form with errors
        self.client.login(username='testuser', password='pass')
        url = reverse('users:profile_edit')
        response = self.client.post(url, {
            'bio': 'Bio',
            'fitness_goal': 'x' * 101  # Exceeds max_length
        })
        # Expect the form to be shown again (status 200) with validation errors
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertTrue(form.errors)
        self.assertIn('fitness_goal', form.errors)
        self.assertIn(
            'Ensure this value has at most 100 characters',
            form.errors['fitness_goal'][0]
        )

    def test_profile_str_method(self):
        # The Profile model's __str__ should include the username
        # for readability
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(str(profile), f"{self.user.username}'s Profile")

    def test_profile_avatar_field_blank(self):
        # Newly created profiles should have an empty avatar by default
        profile = Profile.objects.get(user=self.user)
        self.assertTrue(profile.avatar.name == '' or profile.avatar is None)
