from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.deletion import ProtectedError
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.core.paginator import Paginator

from accounts.decorators import role_required
from subjects.models import Subject
from submissions.models import Submission
from .models import Assignment
from .forms import AssignmentForm


# ==========================================
# ASSIGNMENT LIST
# ==========================================

@login_required
def assignment_list(request):

    if request.user.role == 'TEACHER':

        assignments = Assignment.objects.filter(
            created_by=request.user
        )

        subjects = Subject.objects.filter(
            teacher=request.user
        )

    elif request.user.role == 'STUDENT':

        assignments = Assignment.objects.filter(
            subject__students=request.user,
            is_published=True
        )

        subjects = Subject.objects.filter(
            students=request.user
        )

    else:

        assignments = Assignment.objects.none()
        subjects = Subject.objects.none()

    assignments = assignments.select_related(
        'subject',
        'created_by'
    ).distinct()

    # SEARCH
    search_query = request.GET.get('q', '').strip()

    if search_query:
        assignments = assignments.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(subject__name__icontains=search_query)
        )

    # SUBJECT FILTER
    subject_id = request.GET.get('subject', '').strip()

    if subject_id.isdigit():
        assignments = assignments.filter(
            subject_id=int(subject_id)
        )

    # PUBLICATION FILTER - TEACHERS ONLY
    publication_status = ''

    if request.user.role == 'TEACHER':

        publication_status = request.GET.get(
            'status',
            ''
        )

        if publication_status == 'published':
            assignments = assignments.filter(
                is_published=True
            )

        elif publication_status == 'draft':
            assignments = assignments.filter(
                is_published=False
            )

    # PAGINATION
    paginator = Paginator(assignments, 6)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'assignments/assignment_list.html',
        {
            'assignments': page_obj,
            'page_obj': page_obj,
            'subjects': subjects,
            'search_query': search_query,
            'selected_subject': subject_id,
            'publication_status': publication_status,
        }
    )


# ==========================================
# ASSIGNMENT DETAILS
# ==========================================

@login_required
def assignment_detail(request, pk):

    assignment = get_object_or_404(
        Assignment.objects.select_related('subject', 'created_by'),
        pk=pk
    )

    if request.user.role == 'TEACHER':
        if assignment.created_by_id != request.user.id:
            raise PermissionDenied

    elif request.user.role == 'STUDENT':
        is_enrolled = assignment.subject.students.filter(
            pk=request.user.pk
        ).exists()

        if not assignment.is_published or not is_enrolled:
            raise PermissionDenied

    else:
        raise PermissionDenied

    student_submission = None

    if request.user.role == 'STUDENT':
        student_submission = Submission.objects.filter(
            assignment=assignment,
            student=request.user
        ).first()

    return render(
        request,
        'assignments/assignment_detail.html',
        {
            'assignment': assignment,
            'student_submission': student_submission,
        }
    )


# ==========================================
# CREATE ASSIGNMENT
# ==========================================

@role_required('TEACHER')
def assignment_create(request):

    if request.method == 'POST':
        form = AssignmentForm(
            request.POST,
            teacher=request.user
        )

        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()

            messages.success(
                request,
                'Assignment created successfully.'
            )

            return redirect(
                'assignments:assignment_list'
            )

    else:
        form = AssignmentForm(teacher=request.user)

    return render(
        request,
        'assignments/assignment_form.html',
        {
            'form': form,
            'page_title': 'Create Assignment',
            'button_text': 'Create Assignment',
        }
    )


# ==========================================
# UPDATE ASSIGNMENT
# ==========================================

@role_required('TEACHER')
def assignment_update(request, pk):

    assignment = get_object_or_404(
        Assignment,
        pk=pk,
        created_by=request.user
    )

    if request.method == 'POST':
        form = AssignmentForm(
            request.POST,
            instance=assignment,
            teacher=request.user
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Assignment updated successfully.'
            )

            return redirect(
                'assignments:assignment_detail',
                pk=assignment.pk
            )

    else:
        form = AssignmentForm(
            instance=assignment,
            teacher=request.user
        )

    return render(
        request,
        'assignments/assignment_form.html',
        {
            'form': form,
            'assignment': assignment,
            'page_title': 'Edit Assignment',
            'button_text': 'Save Changes',
        }
    )


# ==========================================
# DELETE ASSIGNMENT
# ==========================================

@role_required('TEACHER')
def assignment_delete(request, pk):

    assignment = get_object_or_404(
        Assignment,
        pk=pk,
        created_by=request.user
    )

    if request.method == 'POST':

        try:
            assignment.delete()

            messages.success(
                request,
                'Assignment deleted successfully.'
            )

            return redirect(
                'assignments:assignment_list'
            )

        except ProtectedError:
            messages.error(
                request,
                'This assignment cannot be deleted because students have submitted work for it.'
            )

            return redirect(
                'assignments:assignment_detail',
                pk=assignment.pk
            )

    return render(
        request,
        'assignments/assignment_confirm_delete.html',
        {'assignment': assignment}
    )