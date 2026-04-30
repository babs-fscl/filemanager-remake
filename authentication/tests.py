from django.test import TestCase, Client
from .models import CustomUser
from django.urls import reverse
from .forms import UserRegisterForm


class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpassword',
            first_name='Test',
            last_name='User',
            company_name='Test Co',
            personal_telephone='N/A',
            office_telephone='N/A',
            address='N/A',
        )

    def test_login_view(self):
        response = self.client.post(reverse('login'), {'email': 'test@example.com', 'password': 'testpassword'})
        self.assertEqual(response.status_code, 302)  # Redirects after successful login
        self.assertRedirects(response, reverse('upload'))  # Check if redirects to upload page

    def test_invalid_login_view(self):
        response = self.client.post(reverse('login'), {'email': 'test@example.com', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 302)  # Redirects after unsuccessful login
        self.assertRedirects(response, reverse('login'))  # Check if redirects back to login page

    def test_logout_view(self):
        self.client.login(email='test@example.com', password='testpassword')
        response = self.client.get(reverse('logout_user'))
        self.assertEqual(response.status_code, 302)  # Redirects after logout
        self.assertRedirects(response, reverse('login'))  # Check if redirects to login page

    def test_register_user_view(self):
        response = self.client.post(reverse('register'),
                                    {'first_name': 'Temitope', 'last_name': 'Shols', 'company_name': 'Welz',
                                     'personal_telephone': '+2348167847286', 'office_telephone': '+2348167847286',
                                     'address': 'Mayflower School', 'email': 'newuser@example.com',
                                     'password1': 'newpassword',
                                     'password2': 'newpassword', })
        self.assertEqual(response.status_code, 302)  # Redirects after successful registration
        self.assertRedirects(response, reverse('upload'))  # Check if redirects to upload page

    def test_register_user_form(self):
        form = UserRegisterForm(
            data={'first_name': 'Temitope', 'last_name': 'Shols', 'company_name': 'Welz',
                  'personal_telephone': '+2348167847286', 'office_telephone': '+2348167847286',
                  'address': 'Mayflower School', 'email': 'newuser1@example.com', 'password1': 'newpassword',
                  'password2': 'newpassword'})

        self.assertTrue(form.is_valid())

    #   def test_change_password_view(self):
    #       self.client.login(email='test@example.com', password='testpassword')
    #       response = self.client.post(reverse('change_password'),
    #                                   {'old_password': 'testpassword', 'new_password1': 'newpassword',
    #                                    'new_password2': 'newpassword'})
    #       self.assertEqual(response.status_code, 302)  # Redirects after successful password change
    #       self.assertRedirects(response, reverse('dashboard'))  # Check if redirects to dashboard

    #   def test_invalid_change_password_view(self):
    #       self.client.login(email='test@example.com', password='testpassword')
    #       response = self.client.post(reverse('change_password'),
    #                                   {'old_password': 'wrongpassword', 'new_password1': 'newpassword',
    #                                    'new_password2': 'newpassword'})
    #       self.assertEqual(response.status_code, 200)  # Renders the same page on invalid password change
    #       self.assertContains(response, 'Password changed successfully',
    #                           count=0)  # Check if success message is not present

    # def test_change_password_view_unauthorized_user(self): self.user.is_shopper = False self.user.save()
    # self.client.login(email='test@example.com', password='testpassword') response = self.client.get(reverse(
    # 'change_password')) self.assertEqual(response.status_code, 200)  # Renders the same page for unauthorized user
    # self.assertContains(response, 'You do not have access to do this')  # Check if unauthorized message is present
