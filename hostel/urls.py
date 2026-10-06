from django.urls import path
from . import views


urlpatterns = [

    # ========================================================
    # STUDENT MANAGEMENT
    # ========================================================

    path(
        'students/',
        views.student_list,
        name='student_list'
    ),

    path(
        'students/<int:pk>/',
        views.student_detail,
        name='student_detail'
    ),

    path(
        'students/<int:pk>/delete/',
        views.student_delete,
        name='student_delete'
    ),


    # ========================================================
    # ROOM MANAGEMENT
    # ========================================================

    path(
        'rooms/',
        views.room_list,
        name='room_list'
    ),

    path(
        'rooms/add/',
        views.room_create,
        name='room_create'
    ),


    # ========================================================
    # ROOM ALLOCATION
    # ========================================================

    path(
        'allocations/',
        views.allocation_list,
        name='allocation_list'
    ),

    path(
        'allocations/add/',
        views.allocate_student,
        name='allocate_student'
    ),

    path(
        'allocations/<int:pk>/vacate/',
        views.vacate_room,
        name='vacate_room'
    ),


    # ========================================================
    # PAYMENT MANAGEMENT
    # ========================================================

    path(
        'payments/',
        views.payment_list,
        name='payment_list'
    ),

    path(
        'payments/add/',
        views.payment_create,
        name='payment_create'
    ),


    # ========================================================
    # NOTICE MANAGEMENT
    # ========================================================

    path(
        'notices/',
        views.notice_list,
        name='notice_list'
    ),

    path(
        'notices/add/',
        views.notice_create,
        name='notice_create'
    ),

    path(
        'notices/<int:pk>/edit/',
        views.notice_update,
        name='notice_update'
    ),

    path(
        'notices/<int:pk>/delete/',
        views.notice_delete,
        name='notice_delete'
    ),


    # ========================================================
    # STUDENT NOTICE PAGE
    # ========================================================

    path(
        'student/notices/',
        views.student_notices,
        name='student_notices'
    ),
]