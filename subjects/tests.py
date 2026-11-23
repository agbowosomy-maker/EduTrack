from django.test import TestCase
from datetime import timedelta
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Subject
from assignments.models import Assignment

# Create your tests here.
User = get_user_model()


class SubjectManagementTests(TestCase):

    def setUp(self):

        self.teacher = User.objects.create_user(
            username='teacher_one',
            email='teacher@example.com',
            password='StrongPass123!',
            role=User.Role.TEACHER
        )

        self.other_teacher = User.objects.create_user(
            username='teacher_two',
            email='teacher2@example.com',
            password='StrongPass123!',
            role=User.Role.TEACHER
        )

        self.student = User.objects.create_user(
            username='student_one',
            email='student@example.com',
            password='StrongPass123!',
            role=User.Role.STUDENT
        )

        self.subject = Subject.objects.create(
            name='Mathematics',
            description='Study of numbers and calculations.',
            teacher=self.teacher
        )

        self.subject.students.add(self.student)

        self.other_subject = Subject.objects.create(
            name='Physics',
            description='Study of matter and energy.',
            teacher=self.other_teacher
        )

    def test_teacher_can_view_own_subjects(self):

        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse('subjects:subject_list')
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mathematics')
        self.assertNotContains(response, 'Physics')

    def test_student_can_view_enrolled_subjects(self):

        self.client.force_login(self.student)

        response = self.client.get(
            reverse('subjects:subject_list')
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mathematics')
        self.assertNotContains(response, 'Physics')

    def test_teacher_can_create_subject(self):

        self.client.force_login(self.teacher)

        response = self.client.post(
            reverse('subjects:subject_create'),
            {
                'name': 'Computer Science',
                'description': 'Introduction to computing.',
            }
        )

        self.assertRedirects(
            response,
            reverse('subjects:subject_list')
        )

        subject = Subject.objects.get(name='Computer Science')

        self.assertEqual(subject.teacher, self.teacher)

    def test_teacher_cannot_edit_another_teachers_subject(self):

        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse(
                'subjects:subject_update',
                kwargs={'pk': self.other_subject.pk}
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_student_cannot_create_subject(self):

        self.client.force_login(self.student)

        response = self.client.get(
            reverse('subjects:subject_create')
        )

        self.assertEqual(response.status_code, 403)

    def test_student_cannot_access_unenrolled_subject(self):

        self.client.force_login(self.student)

        response = self.client.get(
            reverse(
                'subjects:subject_detail',
                kwargs={'pk': self.other_subject.pk}
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_teacher_can_update_own_subject(self):

        self.client.force_login(self.teacher)

        response = self.client.post(
            reverse(
                'subjects:subject_update',
                kwargs={'pk': self.subject.pk}
            ),
            {
                'name': 'Advanced Mathematics',
                'description': 'An advanced mathematics subject.',
            }
        )

        self.assertRedirects(
            response,
            reverse(
                'subjects:subject_detail',
                kwargs={'pk': self.subject.pk}
            )
        )

        self.subject.refresh_from_db()

        self.assertEqual(
            self.subject.name,
            'Advanced Mathematics'
        )

    def test_teacher_can_delete_own_subject(self):

        self.client.force_login(self.teacher)

        response = self.client.post(
            reverse(
                'subjects:subject_delete',
                kwargs={'pk': self.subject.pk}
            )
        )

        self.assertRedirects(
            response,
            reverse('subjects:subject_list')
        )

        self.assertFalse(
            Subject.objects.filter(pk=self.subject.pk).exists()
        )

    def test_subject_with_assignments_cannot_be_deleted(self):

        assignment = Assignment.objects.create(
            title='Algebra Exercise',
            description='Complete the algebra exercises.',
            subject=self.subject,
            created_by=self.teacher,
            due_date=timezone.now() + timedelta(days=7)
        )

        self.client.force_login(self.teacher)

        response = self.client.post(
            reverse(
                'subjects:subject_delete',
                kwargs={'pk': self.subject.pk}
            )
        )

        self.assertRedirects(
            response,
            reverse(
                'subjects:subject_detail',
                kwargs={'pk': self.subject.pk}
            )
        )

        self.assertTrue(
            Subject.objects.filter(pk=self.subject.pk).exists()
        )

        self.assertTrue(
            Assignment.objects.filter(pk=assignment.pk).exists()
        )


class SubjectSearchPaginationTests(TestCase):

    def setUp(self):

        self.teacher = User.objects.create_user(
            username='search_teacher',
            password='StrongPass123!',
            role=User.Role.TEACHER
        )

        self.student = User.objects.create_user(
            username='search_student',
            password='StrongPass123!',
            role=User.Role.STUDENT
        )

        self.subjects = []

        for number in range(8):
            subject = Subject.objects.create(
                name=f'Subject {number}',
                description=f'Description for subject {number}',
                teacher=self.teacher
            )

            self.subjects.append(subject)

        self.subjects[0].students.add(self.student)

    def test_teacher_can_search_subjects(self):

        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse('subjects:subject_list'),
            {'q': 'Subject 0'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Subject 0')
        self.assertNotContains(response, 'Subject 1')

    def test_student_search_is_limited_to_enrolled_subjects(self):

        self.client.force_login(self.student)

        response = self.client.get(
            reverse('subjects:subject_list'),
            {'q': 'Subject'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Subject 0')
        self.assertNotContains(response, 'Subject 1')

    def test_subjects_are_paginated(self):

        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse('subjects:subject_list')
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['subjects']), 6)

        self.assertTrue(
            response.context['page_obj'].has_next()
        )

    def test_invalid_page_number_is_handled(self):

        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse('subjects:subject_list'),
            {'page': 'invalid'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['page_obj'].number,
            1
        )
