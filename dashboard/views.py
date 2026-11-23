from django.shortcuts import render
from django.utils import timezone
from django.core.exceptions import PermissionDenied

from accounts.decorators import role_required
from assignments.models import Assignment
from submissions.models import Submission
from subjects.models import Subject


@role_required('STUDENT')
def student_dashboard(request):

    # Subjects belonging to the logged-in student.
    enrolled_subjects = Subject.objects.filter(
        students=request.user
    )

    # Published assignments from the student's enrolled subjects.
    available_assignments = Assignment.objects.filter(
        subject__students=request.user,
        is_published=True
    ).select_related('subject').distinct()

    # The student's own submissions for those assignments.
    student_submissions = Submission.objects.filter(
        student=request.user,
        assignment__in=available_assignments
    ).select_related('assignment', 'assignment__subject')

    # IDs of assignments already submitted.
    submitted_assignment_ids = student_submissions.values_list(
        'assignment_id',
        flat=True
    )

    # Assignments the student has not submitted.
    pending_assignments = available_assignments.exclude(
        id__in=submitted_assignment_ids
    )

    # Submissions that have received a teacher's review.
    # ASSUMPTION: Submission has a `status` field with REVIEWED and
    # REVISION_REQUIRED choices. Adjust the field/choice names to match
    # your model.
    reviewed_submissions = student_submissions.filter(
        status__in=['REVIEWED', 'REVISION_REQUIRED']
    )

    # Counts
    subject_count = enrolled_subjects.count()
    total_assignments = available_assignments.count()
    submitted_count = student_submissions.count()
    pending_count = pending_assignments.count()
    reviewed_count = reviewed_submissions.count()

    # Progress percentage (guard against division by zero).
    if total_assignments > 0:
        progress_percentage = round(
            (submitted_count / total_assignments) * 100
        )
    else:
        progress_percentage = 0

    # Upcoming deadlines: pending assignments ordered by due date.
    upcoming_assignments = pending_assignments.order_by(
        'due_date'
    )[:5]

    # Recently published assignments.
    recent_assignments = available_assignments.order_by(
        '-created_at'
    )[:5]

    context = {
        'subject_count': subject_count,
        'total_assignments': total_assignments,
        'submitted_count': submitted_count,
        'pending_count': pending_count,
        'reviewed_count': reviewed_count,
        'progress_percentage': progress_percentage,
        'upcoming_assignments': upcoming_assignments,
        'recent_assignments': recent_assignments,
    }

    return render(
        request,
        'dashboard/student_dashboard.html',
        context
    )


@role_required('TEACHER')
def teacher_dashboard(request):
    if request.user.role != 'TEACHER':
        raise PermissionDenied

    # Subjects managed by this teacher.
    teacher_subjects = Subject.objects.filter(
        teacher=request.user
    )

    # Assignments created by this teacher.
    teacher_assignments = Assignment.objects.filter(
        created_by=request.user
    ).select_related('subject')

    # Submissions for assignments belonging to this teacher.
    teacher_submissions = Submission.objects.filter(
        assignment__created_by=request.user
    ).select_related(
        'student',
        'assignment',
        'assignment__subject'
    )

    pending_reviews = teacher_submissions.filter(
        status=Submission.Status.SUBMITTED
    )

    reviewed_submissions = teacher_submissions.filter(
        status=Submission.Status.REVIEWED
    )

    revision_requests = teacher_submissions.filter(
        status=Submission.Status.REVISION_REQUIRED
    )

    recent_submissions = teacher_submissions.order_by(
        '-submitted_at'
    )[:6]

    context = {
        'subject_count': teacher_subjects.count(),
        'assignment_count': teacher_assignments.count(),
        'submission_count': teacher_submissions.count(),
        'pending_review_count': pending_reviews.count(),
        'reviewed_count': reviewed_submissions.count(),
        'revision_count': revision_requests.count(),
        'recent_submissions': recent_submissions,
        'teacher_subjects': teacher_subjects,
        'teacher_assignments': teacher_assignments,
    }

    return render(
        request,
        'dashboard/teacher_dashboard.html',
        context
    )