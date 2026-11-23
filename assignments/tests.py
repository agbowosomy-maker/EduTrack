
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from subjects.models import Subject
from submissions.models import Submission
from .models import Assignment

User = get_user_model()


class AssignmentManagementTests(TestCase):

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
            description='Mathematics subject.',
            teacher=self.teacher
        )

        self.subject.students.add(self.student)

        self.other_subject = Subject.objects.create(
            name='Physics',
            description='Physics subject.',
            teacher=self.other_teacher
        )

        self.assignment = Assignment.objects.create(
            title='Algebra Exercise',
            description='Complete the algebra exercises.',
            subject=self.subject,
            created_by=self.teacher,
            due_date=timezone.now() + timedelta(days=7),
            is_published=True
        )

        self.draft = Assignment.objects.create(
            title='Geometry Exercise',
            description='Complete the geometry exercises.',
            subject=self.subject,
            created_by=self.teacher,
            due_date=timezone.now() + timedelta(days=10),
            is_published=False
        )

        self.other_assignment = Assignment.objects.create(
            title='Physics Exercise',
            description='Complete the physics exercises.',
            subject=self.other_subject,
            created_by=self.other_teacher,
            due_date=timezone.now() + timedelta(days=7),
            is_published=True
        )

    def test_teacher_can_view_own_assignments(self):

        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse('assignments:assignment_list')
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Algebra Exercise')
        self.assertContains(response, 'Geometry Exercise')
        self.assertNotContains(response, 'Physics Exercise')

    def test_student_can_only_view_published_assignments(self):

        self.client.force_login(self.student)

        response = self.client.get(
            reverse('assignments:assignment_list')
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Algebra Exercise')
        self.assertNotContains(response, 'Geometry Exercise')
        self.assertNotContains(response, 'Physics Exercise')

    def test_teacher_can_create_assignment(self):

        self.client.force_login(self.teacher)

        due_date = timezone.localtime(
            timezone.now() + timedelta(days=14)
        ).strftime('%Y-%m-%dT%H:%M')

        response = self.client.post(
            reverse('assignments:assignment_create'),
            {
                'title': 'Computer Studies',
                'description': 'Introduction to computer systems.',
                'subject': self.subject.pk,
                'due_date': due_date,
                'is_published': 'on',
            }
        )

        self.assertRedirects(
            response,
            reverse('assignments:assignment_list')
        )

        assignment = Assignment.objects.get(
            title='Computer Studies'
        )

        self.assertEqual(
            assignment.created_by,
            self.teacher
        )

        self.assertTrue(assignment.is_published)

    def test_teacher_cannot_use_another_teachers_subject(self):

        self.client.force_login(self.teacher)

        due_date = timezone.localtime(
            timezone.now() + timedelta(days=14)
        ).strftime('%Y-%m-%dT%H:%M')

        response = self.client.post(
            reverse('assignments:assignment_create'),
            {
                'title': 'Invalid Assignment',
                'description': 'This should not be accepted.',
                'subject': self.other_subject.pk,
                'due_date': due_date,
                'is_published': 'on',
            }
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Assignment.objects.filter(
                title='Invalid Assignment'
            ).exists()
        )

    def test_student_cannot_create_assignment(self):

        self.client.force_login(self.student)

        response = self.client.get(
            reverse('assignments:assignment_create')
        )

        self.assertEqual(response.status_code, 403)

    def test_student_cannot_view_unpublished_assignment(self):

        self.client.force_login(self.student)

        response = self.client.get(
            reverse(
                'assignments:assignment_detail',
                kwargs={'pk': self.draft.pk}
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_teacher_cannot_edit_another_teachers_assignment(self):

        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse(
                'assignments:assignment_update',
                kwargs={'pk': self.other_assignment.pk}
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_teacher_can_update_own_assignment(self):

        self.client.force_login(self.teacher)

        due_date = timezone.localtime(
            timezone.now() + timedelta(days=20)
        ).strftime('%Y-%m-%dT%H:%M')

        response = self.client.post(
            reverse(
                'assignments:assignment_update',
                kwargs={'pk': self.assignment.pk}
            ),
            {
                'title': 'Updated Algebra Exercise',
                'description': 'Updated instructions.',
                'subject': self.subject.pk,
                'due_date': due_date,
                'is_published': 'on',
            }
        )

        self.assertRedirects(
            response,
            reverse(
                'assignments:assignment_detail',
                kwargs={'pk': self.assignment.pk}
            )
        )

        self.assignment.refresh_from_db()

        self.assertEqual(
            self.assignment.title,
            'Updated Algebra Exercise'
        )

    def test_teacher_can_delete_own_assignment(self):

        self.client.force_login(self.teacher)

        response = self.client.post(
            reverse(
                'assignments:assignment_delete',
                kwargs={'pk': self.assignment.pk}
            )
        )

        self.assertRedirects(
            response,
            reverse('assignments:assignment_list')
        )

        self.assertFalse(
            Assignment.objects.filter(
                pk=self.assignment.pk
            ).exists()
        )

    def test_assignment_with_submission_cannot_be_deleted(self):

        submission = Submission.objects.create(
            assignment=self.assignment,
            student=self.student,
            content='My completed assignment.'
        )

        self.client.force_login(self.teacher)

        response = self.client.post(
            reverse(
                'assignments:assignment_delete',
                kwargs={'pk': self.assignment.pk}
            )
        )

        self.assertRedirects(
            response,
            reverse(
                'assignments:assignment_detail',
                kwargs={'pk': self.assignment.pk}
            )
        )

        self.assertTrue(
            Assignment.objects.filter(
                pk=self.assignment.pk
            ).exists()
        )

        self.assertTrue(
            Submission.objects.filter(
                pk=submission.pk
            ).exists()
        )


class AssignmentSearchFilterPaginationTests(TestCase):

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

        self.subject = Subject.objects.create(
            name='Mathematics',
            teacher=self.teacher
        )

        self.subject.students.add(self.student)

        self.assignments = []

        for number in range(8):

            assignment = Assignment.objects.create(
                title=f'Exercise {number}',
                description=f'Assignment description {number}',
                subject=self.subject,
                created_by=self.teacher,
                due_date=timezone.now() + timedelta(days=number + 5),
                is_published=number % 2 == 0
            )

            self.assignments.append(assignment)

    def test_teacher_can_search_assignments(self):

        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse('assignments:assignment_list'),
            {'q': 'Exercise 0'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Exercise 0')
        self.assertNotContains(response, 'Exercise 1')

    def test_student_search_returns_only_published_assignments(self):

        self.client.force_login(self.student)

        response = self.client.get(
            reverse('assignments:assignment_list'),
            {'q': 'Exercise'}
        )

        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Exercise 0')
        self.assertNotContains(response, 'Exercise 1')

    def test_teacher_can_filter_by_publication_status(self):

        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse('assignments:assignment_list'),
            {'status': 'draft'}
        )

        self.assertEqual(response.status_code, 200)

        for assignment in self.assignments:
            if assignment.is_published:
                self.assertNotContains(
                    response,
                    assignment.title
                )
            else:
                self.assertContains(
                    response,
                    assignment.title
                )

    def test_assignments_can_be_filtered_by_subject(self):

        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse('assignments:assignment_list'),
            {'subject': str(self.subject.pk)}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['page_obj'].paginator.count,
            8
        )

    def test_assignments_are_paginated(self):

        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse('assignments:assignment_list')
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['assignments']), 6)

        self.assertTrue(
            response.context['page_obj'].has_next()
        )

    def test_search_parameters_are_preserved_on_next_page(self):

        self.client.force_login(self.teacher)

        response = self.client.get(
            reverse('assignments:assignment_list'),
            {'q': 'Exercise', 'page': '2'}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['page_obj'].number, 2)
