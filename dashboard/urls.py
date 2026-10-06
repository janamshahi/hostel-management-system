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


    # ========================================================
    # STUDENT PROFILE
    # ========================================================

    path(
        'student/profile/',
        views.student_profile,
        name='student_profile'
    ),


    # ========================================================
    # EDIT STUDENT PROFILE
    # ========================================================

    path(
        'student/profile/edit/',
        views.edit_profile,
        name='edit_profile'
    ),


    # ========================================================
    # ADMIN DASHBOARD
    # ========================================================

    path(
        'admin/',
        views.admin_dashboard,
        name='admin_dashboard'
    ),

]