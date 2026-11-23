from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from assignments.models import Assignment
from subjects.models import Subject
from .models import Submission

User = get_user_model()


class StudentSubmissionTests(TestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            username='student_one',
            password='TestPassword123!',
            role='STUDENT'
        )

        self.other_student = User.objects.create_user(
            username='student_two',
            password='TestPassword123!',
            role='STUDENT'
        )

        self.teacher = User.objects.create_user(
            username='teacher_one',
            password='TestPassword123!',
            role='TEACHER'
        )

        self.subject = Subject.objects.create(
            name='Mathematics',
            description='Mathematics subject',
            teacher=self.teacher
        )

        self.subject.students.add(
            self.student,
            self.other_student
        )

        self.assignment = Assignment.objects.create(
            title='Algebra Exercise',
            description='Complete the algebra questions.',
            subject=self.subject,
            created_by=self.teacher,
            due_date=timezone.now() + timedelta(days=3),
            is_published=True
        )

        self.submit_url = reverse(
            'submissions:submission_create',
            args=[self.assignment.pk]
        )

    def test_student_can_submit_written_answer(self):
        self.client.login(
            username='student_one',
            password='TestPassword123!'
        )

        response = self.client.post(
            self.submit_url,
            {'content': 'My completed algebra answers.'}
        )

        self.assertEqual(response.status_code, 302)

        submission = Submission.objects.get(
            assignment=self.assignment,
            student=self.student
        )

        self.assertEqual(
            submission.content,
            'My completed algebra answers.'
        )

    def test_student_can_upload_valid_pdf(self):
        self.client.login(
            username='student_one',
            password='TestPassword123!'
        )

        uploaded_file = SimpleUploadedFile(
            'answers.pdf',
            b'%PDF-1.4 test document content',
            content_type='application/pdf'
        )

        response = self.client.post(
            self.submit_url,
            {
                'content': '',
                'file': uploaded_file
            }
        )

        self.assertEqual(response.status_code, 302)

        submission = Submission.objects.get(
            assignment=self.assignment,
            student=self.student
        )

        self.assertTrue(submission.file)

    def test_student_cannot_submit_empty_work(self):
        self.client.login(
            username='student_one',
            password='TestPassword123!'
        )

        response = self.client.post(
            self.submit_url,
            {'content': ''}
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Submission.objects.filter(
                assignment=self.assignment,
                student=self.student
            ).exists()
        )

    def test_student_cannot_upload_unsupported_file(self):
        self.client.login(
            username='student_one',
            password='TestPassword123!'
        )

        uploaded_file = SimpleUploadedFile(
            'answers.exe',
            b'test content',
            content_type='application/octet-stream'
        )

        response = self.client.post(
            self.submit_url,
            {
                'content': '',
                'file': uploaded_file
            }
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            Submission.objects.filter(
                assignment=self.assignment,
                student=self.student
            ).exists()
        )

    def test_student_cannot_submit_after_deadline(self):
        self.assignment.due_date = timezone.now() - timedelta(hours=1)
        self.assignment.save()

        self.client.login(
            username='student_one',
            password='TestPassword123!'
        )

        response = self.client.post(
            self.submit_url,
            {'content': 'Late submission'}
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Submission.objects.filter(
                assignment=self.assignment,
                student=self.student
            ).exists()
        )

    def test_student_cannot_submit_twice(self):
        Submission.objects.create(
            assignment=self.assignment,
            student=self.student,
            content='First submission'
        )

        self.client.login(
            username='student_one',
            password='TestPassword123!'
        )

        response = self.client.get(self.submit_url)

        self.assertRedirects(
            response,
            reverse(
                'submissions:submission_detail',
                args=[
                    Submission.objects.get(
                        assignment=self.assignment,
                        student=self.student
                    ).pk
                ]
            )
        )

    def test_student_cannot_view_another_students_submission(self):
        other_submission = Submission.objects.create(
            assignment=self.assignment,
            student=self.other_student,
            content='Private student work'
        )

        self.client.login(
            username='student_one',
            password='TestPassword123!'
        )

        response = self.client.get(
            reverse(
                'submissions:submission_detail',
                args=[other_submission.pk]
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_teacher_can_view_submission_for_own_subject(self):
        submission = Submission.objects.create(
            assignment=self.assignment,
            student=self.student,
            content='Completed work'
        )

        self.client.login(
            username='teacher_one',
            password='TestPassword123!'
        )

        response = self.client.get(
            reverse(
                'submissions:submission_detail',
                args=[submission.pk]
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_student_can_update_unreviewed_submission(self):
        submission = Submission.objects.create(
            assignment=self.assignment,
            student=self.student,
            content='Original answer'
        )

        self.client.login(
            username='student_one',
            password='TestPassword123!'
        )

        response = self.client.post(
            reverse(
                'submissions:submission_update',
                args=[submission.pk]
            ),
            {'content': 'Updated answer'}
        )

        self.assertEqual(response.status_code, 302)

        submission.refresh_from_db()

        self.assertEqual(submission.content, 'Updated answer')

    def test_student_cannot_update_reviewed_submission(self):
        submission = Submission.objects.create(
            assignment=self.assignment,
            student=self.student,
            content='Reviewed answer',
            status=Submission.Status.REVIEWED,
            grade=85
        )

        self.client.login(
            username='student_one',
            password='TestPassword123!'
        )

        response = self.client.post(
            reverse(
                'submissions:submission_update',
                args=[submission.pk]
            ),
            {'content': 'Attempted change'}
        )

        self.assertEqual(response.status_code, 302)

        submission.refresh_from_db()

        self.assertEqual(submission.content, 'Reviewed answer')
        self.assertEqual(submission.grade, 85)


class TeacherGradingTests(TestCase):

    def setUp(self):
        self.student = User.objects.create_user(
            username='grading_student',
            password='TestPassword123!',
            role='STUDENT'
        )

        self.teacher = User.objects.create_user(
            username='grading_teacher',
            password='TestPassword123!',
            role='TEACHER'
        )

        self.other_teacher = User.objects.create_user(
            username='other_teacher',
            password='TestPassword123!',
            role='TEACHER'
        )

        self.subject = Subject.objects.create(
            name='Physics',
            description='Physics subject',
            teacher=self.teacher
        )

        self.subject.students.add(self.student)

        self.assignment = Assignment.objects.create(
            title='Physics Exercise',
            description='Complete the physics exercise.',
            subject=self.subject,
            created_by=self.teacher,
            due_date=timezone.now() + timedelta(days=3),
            is_published=True
        )

        self.submission = Submission.objects.create(
            assignment=self.assignment,
            student=self.student,
            content='My completed physics work.'
        )

        self.grade_url = reverse(
            'submissions:submission_grade',
            args=[self.submission.pk]
        )

    def test_teacher_can_grade_submission(self):
        self.client.login(
            username='grading_teacher',
            password='TestPassword123!'
        )

        response = self.client.post(
            self.grade_url,
            {
                'status': Submission.Status.REVIEWED,
                'grade': '85',
                'feedback': 'Good work. Well explained.',
            }
        )

        self.assertEqual(response.status_code, 302)

        self.submission.refresh_from_db()

        self.assertEqual(
            self.submission.status,
            Submission.Status.REVIEWED
        )

        self.assertEqual(
            self.submission.grade,
            85
        )

        self.assertEqual(
            self.submission.feedback,
            'Good work. Well explained.'
        )

        self.assertIsNotNone(self.submission.reviewed_at)

    def test_teacher_cannot_review_another_teachers_submission(self):
        self.client.login(
            username='other_teacher',
            password='TestPassword123!'
        )

        response = self.client.get(self.grade_url)

        self.assertEqual(response.status_code, 404)

    def test_student_cannot_access_grading_page(self):
        self.client.login(
            username='grading_student',
            password='TestPassword123!'
        )

        response = self.client.get(self.grade_url)

        self.assertEqual(response.status_code, 403)

    def test_reviewed_submission_requires_grade(self):
        self.client.login(
            username='grading_teacher',
            password='TestPassword123!'
        )

        response = self.client.post(
            self.grade_url,
            {
                'status': Submission.Status.REVIEWED,
                'grade': '',
                'feedback': 'Good work.',
            }
        )

        self.assertEqual(response.status_code, 200)

        self.submission.refresh_from_db()

        self.assertEqual(
            self.submission.status,
            Submission.Status.SUBMITTED
        )

    def test_revision_request_requires_feedback(self):
        self.client.login(
            username='grading_teacher',
            password='TestPassword123!'
        )

        response = self.client.post(
            self.grade_url,
            {
                'status': Submission.Status.REVISION_REQUIRED,
                'grade': '',
                'feedback': '',
            }
        )

        self.assertEqual(response.status_code, 200)

        self.submission.refresh_from_db()

        self.assertEqual(
            self.submission.status,
            Submission.Status.SUBMITTED
        )

    def test_teacher_can_request_revision(self):
        self.client.login(
            username='grading_teacher',
            password='TestPassword123!'
        )

        response = self.client.post(
            self.grade_url,
            {
                'status': Submission.Status.REVISION_REQUIRED,
                'grade': '',
                'feedback': 'Please improve your explanation.',
            }
        )

        self.assertEqual(response.status_code, 302)

        self.submission.refresh_from_db()

        self.assertEqual(
            self.submission.status,
            Submission.Status.REVISION_REQUIRED
        )

        self.assertEqual(
            self.submission.feedback,
            'Please improve your explanation.'
        )

        self.assertIsNotNone(self.submission.reviewed_at)

    def test_teacher_dashboard_only_counts_own_submissions(self):
        other_subject = Subject.objects.create(
            name='Chemistry',
            description='Chemistry subject',
            teacher=self.other_teacher
        )

        other_assignment = Assignment.objects.create(
            title='Chemistry Exercise',
            description='Chemistry work.',
            subject=other_subject,
            created_by=self.other_teacher,
            due_date=timezone.now() + timedelta(days=4),
            is_published=True
        )

        Submission.objects.create(
            assignment=other_assignment,
            student=self.student,
            content='Chemistry work.'
        )

        self.client.login(
            username='grading_teacher',
            password='TestPassword123!'
        )

        response = self.client.get(
            reverse('dashboard:teacher_dashboard')
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['submission_count'], 1)
        self.assertEqual(response.context['pending_review_count'], 1)