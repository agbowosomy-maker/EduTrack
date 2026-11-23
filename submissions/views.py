from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from assignments.models import Assignment

from .forms import GradingForm, SubmissionForm
from .models import Submission


# ==========================================
# CREATE SUBMISSION
# ==========================================

@login_required
def submission_create(request, assignment_id):

    if request.user.role != 'STUDENT':
        raise PermissionDenied

    assignment = get_object_or_404(
        Assignment.objects.select_related('subject'),
        pk=assignment_id,
        is_published=True,
        subject__students=request.user,
    )

    if assignment.due_date <= timezone.now():
        messages.error(
            request,
            'The deadline has passed. This assignment is no longer accepting submissions.'
        )
        return redirect(
            'assignments:assignment_detail',
            pk=assignment.pk
        )

    existing_submission = Submission.objects.filter(
        assignment=assignment,
        student=request.user
    ).first()

    if existing_submission:
        return redirect(
            'submissions:submission_detail',
            pk=existing_submission.pk
        )

    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)

        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.student = request.user
            submission.save()

            messages.success(
                request,
                'Assignment submitted successfully.'
            )

            return redirect(
                'submissions:submission_detail',
                pk=submission.pk
            )

    else:
        form = SubmissionForm()

    return render(
        request,
        'submissions/submission_form.html',
        {
            'form': form,
            'assignment': assignment,
            'page_title': 'Submit Assignment',
        }
    )


# ==========================================
# SUBMISSION DETAIL
# ==========================================

@login_required
def submission_detail(request, pk):

    submission = get_object_or_404(
        Submission.objects.select_related(
            'assignment',
            'assignment__subject',
            'student',
        ),
        pk=pk
    )

    is_student_owner = (
        request.user.role == 'STUDENT'
        and submission.student_id == request.user.id
    )

    is_subject_teacher = (
        request.user.role == 'TEACHER'
        and submission.assignment.subject.teacher_id == request.user.id
    )

    if not (is_student_owner or is_subject_teacher):
        raise PermissionDenied

    return render(
        request,
        'submissions/submission_detail.html',
        {
            'submission': submission,
            'now': timezone.now(),
        }
    )


# ==========================================
# UPDATE SUBMISSION
# ==========================================

@login_required
def submission_update(request, pk):

    if request.user.role != 'STUDENT':
        raise PermissionDenied

    submission = get_object_or_404(
        Submission.objects.select_related('assignment'),
        pk=pk,
        student=request.user
    )

    if submission.status == Submission.Status.REVIEWED:
        messages.error(
            request,
            'This submission has already been reviewed and cannot be edited.'
        )
        return redirect(
            'submissions:submission_detail',
            pk=submission.pk
        )

    if submission.assignment.due_date <= timezone.now():
        messages.error(
            request,
            'The deadline has passed. This submission can no longer be edited.'
        )
        return redirect(
            'submissions:submission_detail',
            pk=submission.pk
        )

    if request.method == 'POST':
        form = SubmissionForm(
            request.POST,
            request.FILES,
            instance=submission
        )

        if form.is_valid():
            updated = form.save(commit=False)

            # A student updating after a revision request moves back
            # to SUBMITTED so the teacher knows it needs re-reviewing.
            if updated.status == Submission.Status.REVISION_REQUIRED:
                updated.status = Submission.Status.SUBMITTED

            updated.save()

            messages.success(
                request,
                'Submission updated successfully.'
            )

            return redirect(
                'submissions:submission_detail',
                pk=submission.pk
            )

    else:
        form = SubmissionForm(instance=submission)

    return render(
        request,
        'submissions/submission_form.html',
        {
            'form': form,
            'assignment': submission.assignment,
            'submission': submission,
            'page_title': 'Update Submission',
        }
    )


# ==========================================
# SECURE FILE DOWNLOAD
# ==========================================

@login_required
def submission_download(request, pk):

    submission = get_object_or_404(
        Submission.objects.select_related(
            'assignment__subject'
        ),
        pk=pk
    )

    is_student_owner = (
        request.user.role == 'STUDENT'
        and submission.student_id == request.user.id
    )

    is_subject_teacher = (
        request.user.role == 'TEACHER'
        and submission.assignment.subject.teacher_id == request.user.id
    )

    if not (is_student_owner or is_subject_teacher):
        raise PermissionDenied

    if not submission.file:
        messages.error(request, 'No file is attached to this submission.')
        return redirect(
            'submissions:submission_detail',
            pk=submission.pk
        )

    return FileResponse(
        submission.file.open('rb'),
        as_attachment=True,
        filename=submission.file.name.split('/')[-1]
    )


# ==========================================
# MY SUBMISSIONS (STUDENT HISTORY)
# ==========================================

@login_required
def my_submissions(request):

    if request.user.role != 'STUDENT':
        raise PermissionDenied

    submissions = Submission.objects.filter(
        student=request.user
    ).select_related(
        'assignment',
        'assignment__subject'
    )

    return render(
        request,
        'submissions/my_submissions.html',
        {'submissions': submissions}
    )


# ==========================================
# ASSIGNMENT SUBMISSIONS (TEACHER LIST)
# ==========================================

@login_required
def assignment_submissions(request, assignment_id):

    if request.user.role != 'TEACHER':
        raise PermissionDenied

    assignment = get_object_or_404(
        Assignment.objects.select_related('subject'),
        pk=assignment_id,
        created_by=request.user
    )

    submissions = Submission.objects.filter(
        assignment=assignment
    ).select_related('student').order_by('-submitted_at')

    return render(
        request,
        'submissions/assignment_submissions.html',
        {
            'assignment': assignment,
            'submissions': submissions,
        }
    )


# ==========================================
# GRADE SUBMISSION (TEACHER)
# ==========================================

@login_required
def submission_grade(request, pk):

    if request.user.role != 'TEACHER':
        raise PermissionDenied

    submission = get_object_or_404(
        Submission.objects.select_related(
            'assignment',
            'assignment__subject',
            'student'
        ),
        pk=pk,
        assignment__created_by=request.user
    )

    if request.method == 'POST':
        form = GradingForm(request.POST, instance=submission)

        if form.is_valid():
            reviewed_submission = form.save(commit=False)

            if reviewed_submission.status == Submission.Status.REVIEWED:
                reviewed_submission.reviewed_at = timezone.now()

            elif reviewed_submission.status == Submission.Status.REVISION_REQUIRED:
                reviewed_submission.reviewed_at = timezone.now()
                reviewed_submission.grade = None

            else:
                reviewed_submission.reviewed_at = None
                reviewed_submission.grade = None
                reviewed_submission.feedback = ''

            reviewed_submission.full_clean()
            reviewed_submission.save()

            messages.success(
                request,
                'The student submission has been updated successfully.'
            )

            return redirect(
                'submissions:submission_detail',
                pk=submission.pk
            )

    else:
        form = GradingForm(instance=submission)

    return render(
        request,
        'submissions/grading_form.html',
        {
            'form': form,
            'submission': submission,
        }
    )