from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

# Create your tests here.
User=get_user_model()

class AuthenticationTests(TestCase):
    def setUp(self):
        self.student=User.objects.create_user(
            username='student_test',
            email='student@example.com',
            password='StrongPass123!',
            role=User.Role.STUDENT
        )
        self.teacher=User.objects.create_user(
            username='teacher_test',
            email='teacher@example.com',
            password='StrongPass123!',
            role=User.Role.TEACHER
        )

    def test_student_registration(self):
        response=self.client.post(reverse('accounts:register'),{
            'username':'new_student',
            'first_name': 'New',
            'last_name':'Student',
            'email': 'newstudent@example.com',
            'password1':'StrongPass123!',
            'password2':'StrongPass123!'
        }
        )

        self.assertRedirects(response, reverse('accounts:login'))
        user=User.objects.get(username='new_student')
        self.assertEqual(user.role, User.Role.STUDENT)

    def test_student_login_redirects_to_student_dashboard(self):
        response=self.client.post(reverse('accounts:login'),{
            'username':'student_test',
            'password':'StrongPass123!',
        },
        follow=True
        )
        self.assertRedirects(response, reverse('dashboard:student_dashboard'))

    def test_teacher_login_redirects_to_teacher_dashboard(self):
        response=self.client.post(reverse('accounts:login'),{
            'username':'teacher_test',
            'password': 'StrongPass123!'
        },
        follow=True
        )
        self.assertRedirects(response, reverse('dashboard:teacher_dashboard'))

    def test_student_cannot_access_teacher_dashboard(self):
        self.client.force_login(self.student)
        response=self.client.get(reverse('dashboard:teacher_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_teacher_cannot_access_student_dashboard(self):
        self.client.force_login(self.teacher)
        response=self.client.get(reverse('dashboard:student_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_logout(self):
        self.client.force_login(self.student)
        response=self.client.post(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('accounts:login'))
        response=self.client.get(reverse('dashboard:student_dashboard'))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('dashboard:student_dashboard')}")
