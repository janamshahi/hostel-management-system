from django.urls import path

from . import views


urlpatterns = [

    # ========================================================
    # STUDENT DASHBOARD
    # ========================================================

    path(
        '',
        views.dashboard,
        name='student_dashboard'
    ),

    path(
        'student/profile/',
        views.student_profile,
        name='student_profile'
    ),

    path(
        'student/profile/edit/',
        views.edit_profile,
        name='edit_profile'
    ),

    path(
        'student/notices/',
        views.student_notices,
        name='student_notices'
    ),


    # ========================================================
    # ADMIN DASHBOARD
    # ========================================================

    path(
        'admin/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),


    # ========================================================
    # ADMIN REPORTS
    # ========================================================

    path(
        'admin/reports/',
        views.reports,
        name='reports'
    ),


    # ========================================================
    # ADMIN STUDENTS
    # ========================================================

    path(
        'admin/students/',
        views.student_list,
        name='student_list'
    ),

    path(
        'admin/students/add/',
        views.student_add,
        name='student_add'
    ),

    path(
        'admin/students/<int:student_id>/',
        views.student_detail,
        name='student_detail'
    ),

    path(
        'admin/students/<int:student_id>/edit/',
        views.student_edit,
        name='student_edit'
    ),

    path(
        'admin/students/<int:student_id>/delete/',
        views.student_delete,
        name='student_delete'
    ),


    # ========================================================
    # ADMIN NOTICES
    # ========================================================

    path(
        'admin/notices/',
        views.notice_list,
        name='notice_list'
    ),

    path(
        'admin/notices/create/',
        views.notice_create,
        name='notice_create'
    ),

    path(
        'admin/notices/<int:notice_id>/',
        views.notice_detail,
        name='notice_detail'
    ),

    path(
        'admin/notices/<int:notice_id>/edit/',
        views.notice_edit,
        name='notice_edit'
    ),

    path(
        'admin/notices/<int:notice_id>/delete/',
        views.notice_delete,
        name='notice_delete'
    ),

]