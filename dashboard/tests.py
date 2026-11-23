from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from subjects.models import Subject
from assignments.models import Assignment
from submissions.models import Submission


class StudentDashboardTests(TestCase):

    def setUp(self):
        # Teachers
        self.teacher = User.objects.create_user(
            username='teacher1',
            password='pass12345',
            role='TEACHER'
        )
        self.other_teacher = User.objects.create_user(
            username='teacher2',
            password='pass12345',
            role='TEACHER'
        )

        # Students
        self.student = User.objects.create_user(
            username='student1',
            password='pass12345',
            role='STUDENT'
        )
        self.other_student = User.objects.create_user(
            username='student2',
            password='pass12345',
            role='STUDENT'
        )

        # Subject with self.student enrolled
        self.subject = Subject.objects.create(
            name='Math',
            description='Math subject',
            teacher=self.teacher
        )
        self.subject.students.add(self.student)

        # Subject with only other_student enrolled
        self.other_subject = Subject.objects.create(
            name='Science',
            description='Science subject',
            teacher=self.other_teacher
        )
        self.other_subject.students.add(self.other_student)

        # Published assignment in self.student's subject
        self.assignment = Assignment.objects.create(
            title='Algebra HW',
            description='Do algebra',
            subject=self.subject,
            created_by=self.teacher,
            due_date=timezone.now() + timedelta(days=7),
            is_published=True,
        )

        # Unpublished assignment (should never appear)
        self.draft_assignment = Assignment.objects.create(
            title='Draft HW',
            description='Not yet',
            subject=self.subject,
            created_by=self.teacher,
            due_date=timezone.now() + timedelta(days=10),
            is_published=False,
        )

        # Published assignment in a subject the student isn't in
        self.foreign_assignment = Assignment.objects.create(
            title='Foreign HW',
            description='Not yours',
            subject=self.other_subject,
            created_by=self.other_teacher,
            due_date=timezone.now() + timedelta(days=5),
            is_published=True,
        )

        self.url = reverse('dashboard:student_dashboard')

    def test_student_can_access_dashboard(self):
        self.client.login(username='student1', password='pass12345')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_teacher_cannot_access_student_dashboard(self):
        self.client.login(username='teacher1', password='pass12345')
        response = self.client.get(self.url)
        # role_required decorator should reject — exact code depends on
        # your decorator (403 or redirect). Adjust if needed.
        self.assertIn(response.status_code, (403, 302))

    def test_counts_are_zero_with_no_enrollment(self):
        # other_student is enrolled in other_subject only, with a published
        # assignment, so use a fresh student with no enrollment.
        lonely = User.objects.create_user(
            username='lonely', password='pass12345', role='STUDENT'
        )
        self.client.login(username='lonely', password='pass12345')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['subject_count'], 0)
        self.assertEqual(response.context['total_assignments'], 0)
        self.assertEqual(response.context['progress_percentage'], 0)

    def test_progress_zero_when_no_assignments(self):
        self.client.login(username='student2', password='pass12345')
        # student2 is in other_subject which has 1 published assignment,
        # so make a truly empty student instead
        empty = User.objects.create_user(
            username='empty', password='pass12345', role='STUDENT'
        )
        empty_subject = Subject.objects.create(
            name='Empty', description='Empty', teacher=self.teacher
        )
        empty_subject.students.add(empty)

        self.client.login(username='empty', password='pass12345')
        response = self.client.get(self.url)
        self.assertEqual(response.context['progress_percentage'], 0)

    def test_submitted_count_increases(self):
        Submission.objects.create(
            assignment=self.assignment,
            student=self.student,
            content='done',
        )
        self.client.login(username='student1', password='pass12345')
        response = self.client.get(self.url)
        self.assertEqual(response.context['submitted_count'], 1)
        self.assertEqual(response.context['pending_count'], 0)

    def test_reviewed_count_increases(self):
        Submission.objects.create(
            assignment=self.assignment,
            student=self.student,
            content='done',
            status=Submission.Status.REVIEWED,
            grade=90,
        )
        self.client.login(username='student1', password='pass12345')
        response = self.client.get(self.url)
        self.assertEqual(response.context['reviewed_count'], 1)

    def test_other_students_submissions_not_visible(self):
        # other_student submits on their own assignment
        Submission.objects.create(
            assignment=self.foreign_assignment,
            student=self.other_student,
            content='theirs',
            status=Submission.Status.REVIEWED,
            grade=80,
        )
        # self.student views their dashboard — must show 0 submitted/reviewed
        self.client.login(username='student1', password='pass12345')
        response = self.client.get(self.url)
        self.assertEqual(response.context['submitted_count'], 0)
        self.assertEqual(response.context['reviewed_count'], 0)