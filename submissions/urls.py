from django.urls import path

from . import views

app_name = 'submissions'

urlpatterns = [
    path(
        'assignment/<int:assignment_id>/submit/',
        views.submission_create,
        name='submission_create'
    ),
    path(
        'my-submissions/',
        views.my_submissions,
        name='my_submissions'
    ),
    path(
        '<int:pk>/',
        views.submission_detail,
        name='submission_detail'
    ),
    path(
        '<int:pk>/edit/',
        views.submission_update,
        name='submission_update'
    ),
    path(
        '<int:pk>/download/',
        views.submission_download,
        name='submission_download'
    ),
    path(
    'assignment/<int:assignment_id>/submissions/',
    views.assignment_submissions,
    name='assignment_submissions'
    ),
    path(
    '<int:pk>/grade/',
    views.submission_grade,
    name='submission_grade'
    ),
]