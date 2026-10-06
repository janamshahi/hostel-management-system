from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404

from hostel.models import (
    Student,
    Room,
    RoomAllocation,
    FeePayment,
    Notice,
)


# ============================================================
# ADMIN ACCESS DECORATOR
# ============================================================

def admin_required(view_func):
    """
    Allow access only to authenticated superusers.
    """

    return user_passes_test(
        lambda user: (
            user.is_authenticated
            and user.is_superuser
        ),
        login_url='login'
    )(view_func)


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@login_required
def dashboard(request):
    """
    Student dashboard.

    Normal authenticated users are shown the student dashboard.
    Superusers are redirected to the admin dashboard.
    """

    # --------------------------------------------------------
    # Redirect superuser to admin dashboard
    # --------------------------------------------------------

    if request.user.is_superuser:
        return redirect('admin_dashboard')


    # --------------------------------------------------------
    # Get logged-in student's profile
    # --------------------------------------------------------

    student = getattr(
        request.user,
        'student_profile',
        None
    )


    # --------------------------------------------------------
    # If student profile does not exist
    # --------------------------------------------------------

    if student is None:

        messages.error(
            request,
            'Student profile was not found.'
        )

        return redirect('logout')


    # --------------------------------------------------------
    # Current room allocation
    # --------------------------------------------------------

    allocation = (
        RoomAllocation.objects
        .filter(
            student=student,
            is_active=True
        )
        .select_related('room')
        .first()
    )


    # --------------------------------------------------------
    # Student payments
    # --------------------------------------------------------

    payments = (
        FeePayment.objects
        .filter(
            student=student
        )
        .order_by(
            '-payment_date'
        )
    )


    # --------------------------------------------------------
    # Recent active notices
    # --------------------------------------------------------

    notices = (
        Notice.objects
        .filter(
            is_active=True
        )
        .order_by(
            '-created_at'
        )[:5]
    )


    # --------------------------------------------------------
    # Student dashboard context
    # --------------------------------------------------------

    context = {

        'student': student,

        'allocation': allocation,

        'payments': payments,

        'notices': notices,

    }


    # --------------------------------------------------------
    # Render student dashboard
    # --------------------------------------------------------

    return render(
        request,
        'dashboard/student_dashboard.html',
        context
    )


# ============================================================
# STUDENT PROFILE
# ============================================================

@login_required
def student_profile(request):
    """
    Display the profile of the currently logged-in student.

    This page is only for normal student users.
    """

    # --------------------------------------------------------
    # Prevent admin from accessing student profile
    # --------------------------------------------------------

    if request.user.is_superuser:

        return redirect(
            'admin_dashboard'
        )


    # --------------------------------------------------------
    # Get logged-in student's profile
    # --------------------------------------------------------

    student = get_object_or_404(
        Student.objects.select_related('user'),
        user=request.user
    )


    # --------------------------------------------------------
    # Profile context
    # --------------------------------------------------------

    context = {

        'student': student,

    }


    # --------------------------------------------------------
    # Render student profile
    # --------------------------------------------------------

    return render(
        request,
        'dashboard/student_profile.html',
        context
    )


# ============================================================
# EDIT STUDENT PROFILE
# ============================================================

@login_required
def edit_profile(request):
    """
    Allow the logged-in student to edit their own profile.

    Read-only:
        - Student ID
        - Username
        - Gender

    Editable:
        - Full Name
        - Phone
        - Email
        - Date of Birth
        - Address
        - Guardian Name
        - Guardian Phone

    Course and Semester are intentionally not edited here.
    """

    # --------------------------------------------------------
    # Prevent admin from accessing student profile editor
    # --------------------------------------------------------

    if request.user.is_superuser:

        return redirect(
            'admin_dashboard'
        )


    # --------------------------------------------------------
    # Get logged-in student's profile
    # --------------------------------------------------------

    student = get_object_or_404(
        Student.objects.select_related('user'),
        user=request.user
    )


    # ========================================================
    # POST REQUEST
    # ========================================================

    if request.method == 'POST':

        # ----------------------------------------------------
        # Get submitted data
        # ----------------------------------------------------

        full_name = request.POST.get(
            'full_name',
            ''
        ).strip()

        phone = request.POST.get(
            'phone',
            ''
        ).strip()

        email = request.POST.get(
            'email',
            ''
        ).strip()

        address = request.POST.get(
            'address',
            ''
        ).strip()

        guardian_name = request.POST.get(
            'guardian_name',
            ''
        ).strip()

        guardian_phone = request.POST.get(
            'guardian_phone',
            ''
        ).strip()

        date_of_birth = request.POST.get(
            'date_of_birth',
            ''
        ).strip()


        # ====================================================
        # VALIDATION
        # ====================================================

        # ----------------------------------------------------
        # Full name
        # ----------------------------------------------------

        if not full_name:

            messages.error(
                request,
                'Full name is required.'
            )

            return render(
                request,
                'dashboard/edit_profile.html',
                {
                    'student': student,
                }
            )


        # ----------------------------------------------------
        # Phone
        # ----------------------------------------------------

        if not phone:

            messages.error(
                request,
                'Phone number is required.'
            )

            return render(
                request,
                'dashboard/edit_profile.html',
                {
                    'student': student,
                }
            )


        # ----------------------------------------------------
        # Email
        # ----------------------------------------------------

        if not email:

            messages.error(
                request,
                'Email address is required.'
            )

            return render(
                request,
                'dashboard/edit_profile.html',
                {
                    'student': student,
                }
            )


        # ----------------------------------------------------
        # Address
        # ----------------------------------------------------

        if not address:

            messages.error(
                request,
                'Address is required.'
            )

            return render(
                request,
                'dashboard/edit_profile.html',
                {
                    'student': student,
                }
            )


        # ----------------------------------------------------
        # Guardian name
        # ----------------------------------------------------

        if not guardian_name:

            messages.error(
                request,
                'Guardian name is required.'
            )

            return render(
                request,
                'dashboard/edit_profile.html',
                {
                    'student': student,
                }
            )


        # ----------------------------------------------------
        # Guardian phone
        # ----------------------------------------------------

        if not guardian_phone:

            messages.error(
                request,
                'Guardian phone number is required.'
            )

            return render(
                request,
                'dashboard/edit_profile.html',
                {
                    'student': student,
                }
            )


        # ====================================================
        # DATE OF BIRTH VALIDATION
        # ====================================================

        parsed_date_of_birth = None


        if date_of_birth:

            try:

                parsed_date_of_birth = datetime.strptime(
                    date_of_birth,
                    '%Y-%m-%d'
                ).date()

            except ValueError:

                messages.error(
                    request,
                    'Please enter a valid date of birth.'
                )

                return render(
                    request,
                    'dashboard/edit_profile.html',
                    {
                        'student': student,
                    }
                )


        # ====================================================
        # UPDATE STUDENT PROFILE
        # ====================================================

        student.full_name = full_name

        student.phone = phone

        student.email = email

        student.address = address

        student.guardian_name = guardian_name

        student.guardian_phone = guardian_phone

        student.date_of_birth = parsed_date_of_birth

        # ----------------------------------------------------
        # Course and Semester are NOT changed here.
        # ----------------------------------------------------

        student.save()


        # ====================================================
        # UPDATE DJANGO USER ACCOUNT
        # ====================================================

        name_parts = full_name.split()


        # ----------------------------------------------------
        # First name
        # ----------------------------------------------------

        if name_parts:

            request.user.first_name = name_parts[0]

        else:

            request.user.first_name = ''


        # ----------------------------------------------------
        # Last name
        # ----------------------------------------------------

        if len(name_parts) > 1:

            request.user.last_name = (
                ' '.join(name_parts[1:])
            )

        else:

            request.user.last_name = ''


        # ----------------------------------------------------
        # Email
        # ----------------------------------------------------

        request.user.email = email


        # ----------------------------------------------------
        # Save Django User
        # ----------------------------------------------------

        request.user.save(
            update_fields=[
                'first_name',
                'last_name',
                'email',
            ]
        )


        # ====================================================
        # SUCCESS MESSAGE
        # ====================================================

        messages.success(
            request,
            'Your profile has been updated successfully.'
        )


        # ====================================================
        # REDIRECT TO PROFILE
        # ====================================================

        return redirect(
            'student_profile'
        )


    # ========================================================
    # GET REQUEST
    # ========================================================

    return render(
        request,
        'dashboard/edit_profile.html',
        {
            'student': student,
        }
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@admin_required
def admin_dashboard(request):
    """
    Main hostel administrator dashboard.
    """

    # ========================================================
    # STUDENT STATISTICS
    # ========================================================

    total_students = Student.objects.count()


    # ========================================================
    # ROOM STATISTICS
    # ========================================================

    active_rooms = Room.objects.filter(
        is_active=True
    )

    total_rooms = active_rooms.count()

    available_rooms = 0

    occupied_rooms = 0


    for room in active_rooms:

        if room.is_full():

            occupied_rooms += 1

        else:

            available_rooms += 1


    # ========================================================
    # ROOM ALLOCATION
    # ========================================================

    total_allocations = RoomAllocation.objects.filter(
        is_active=True
    ).count()


    # ========================================================
    # PAYMENT STATISTICS
    # ========================================================

    total_paid = (
        FeePayment.objects
        .filter(
            status='Paid'
        )
        .aggregate(
            total=Sum('amount')
        )['total']
        or 0
    )


    pending_payments = FeePayment.objects.filter(
        status='Pending'
    ).count()


    # ========================================================
    # RECENT STUDENTS
    # ========================================================

    recent_students = (
        Student.objects
        .order_by(
            '-created_at'
        )[:5]
    )


    # ========================================================
    # RECENT PAYMENTS
    # ========================================================

    recent_payments = (
        FeePayment.objects
        .select_related(
            'student'
        )
        .order_by(
            '-created_at'
        )[:5]
    )


    # ========================================================
    # ADMIN DASHBOARD CONTEXT
    # ========================================================

    context = {

        # Student statistics
        'total_students': total_students,

        # Room statistics
        'total_rooms': total_rooms,

        'available_rooms': available_rooms,

        'occupied_rooms': occupied_rooms,

        # Allocation
        'total_allocations': total_allocations,

        # Payment statistics
        'total_paid': total_paid,

        'pending_payments': pending_payments,

        # Recent records
        'recent_students': recent_students,

        'recent_payments': recent_payments,

    }


    # ========================================================
    # RENDER ADMIN DASHBOARD
    # ========================================================

    return render(
        request,
        'dashboard/admin_dashboard.html',
        context
    )