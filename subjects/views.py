from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.deletion import ProtectedError
from django.db.models import Q
from django.core.paginator import Paginator

from accounts.decorators import role_required
from .models import Subject
from .forms import SubjectForm


# ==========================================
# SUBJECT LIST
# ==========================================

@login_required
def subject_list(request):

    if request.user.role == 'TEACHER':
        subjects = Subject.objects.filter(
            teacher=request.user
        )

    elif request.user.role == 'STUDENT':
        subjects = Subject.objects.filter(
            students=request.user
        )

    else:
        subjects = Subject.objects.none()

    # SEARCH
    search_query = request.GET.get('q', '').strip()

    if search_query:
        subjects = subjects.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # PAGINATION
    paginator = Paginator(subjects, 6)

    page_number = request.GET.get('page')

    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'subjects/subject_list.html',
        {
            'subjects': page_obj,
            'page_obj': page_obj,
            'search_query': search_query,
        }
    )


# ==========================================
# SUBJECT DETAILS
# ==========================================

@login_required
def subject_detail(request, pk):

    subject = get_object_or_404(Subject, pk=pk)

    if request.user.role == 'TEACHER':
        if subject.teacher_id != request.user.id:
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

    elif request.user.role == 'STUDENT':
        if not subject.students.filter(pk=request.user.pk).exists():
            from django.core.exceptions import PermissionDenied
            raise PermissionDenied

    else:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    return render(
        request,
        'subjects/subject_detail.html',
        {'subject': subject}
    )


# ==========================================
# CREATE SUBJECT
# ==========================================

@role_required('TEACHER')
def subject_create(request):

    if request.method == 'POST':
        form = SubjectForm(request.POST)

        if form.is_valid():
            subject = form.save(commit=False)
            subject.teacher = request.user
            subject.save()

            messages.success(
                request,
                'Subject created successfully.'
            )

            return redirect('subjects:subject_list')

    else:
        form = SubjectForm()

    return render(
        request,
        'subjects/subject_form.html',
        {
            'form': form,
            'page_title': 'Create Subject',
            'button_text': 'Create Subject',
        }
    )


# ==========================================
# UPDATE SUBJECT
# ==========================================

@role_required('TEACHER')
def subject_update(request, pk):

    subject = get_object_or_404(
        Subject,
        pk=pk,
        teacher=request.user
    )

    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Subject updated successfully.'
            )

            return redirect(
                'subjects:subject_detail',
                pk=subject.pk
            )

    else:
        form = SubjectForm(instance=subject)

    return render(
        request,
        'subjects/subject_form.html',
        {
            'form': form,
            'subject': subject,
            'page_title': 'Edit Subject',
            'button_text': 'Save Changes',
        }
    )


# ==========================================
# DELETE SUBJECT
# ==========================================

@role_required('TEACHER')
def subject_delete(request, pk):

    subject = get_object_or_404(
        Subject,
        pk=pk,
        teacher=request.user
    )

    if request.method == 'POST':

        try:
            subject.delete()

            messages.success(
                request,
                'Subject deleted successfully.'
            )

            return redirect('subjects:subject_list')

        except ProtectedError:
            messages.error(
                request,
                'This subject cannot be deleted because it has existing assignments.'
            )

            return redirect(
                'subjects:subject_detail',
                pk=subject.pk
            )

    return render(
        request,
        'subjects/subject_confirm_delete.html',
        {'subject': subject}
    )