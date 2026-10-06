from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect

from hostel.models import Student


# ==========================================================
# PUBLIC HOME PAGE
# ==========================================================

def home(request):
    """
    Public home page of DIDI BAHINI GIRLS HOSTEL.
    """

    return render(
        request,
        'home/home.html'
    )


# ==========================================================
# STUDENT REGISTRATION
# ==========================================================

def register_view(request):
    """
    Register a new hostel student.
    """

    # ------------------------------------------------------
    # ALREADY LOGGED-IN USER
    # ------------------------------------------------------

    if request.user.is_authenticated:

        # Superuser → Admin Dashboard
        if request.user.is_superuser:

            return redirect(
                'admin_dashboard'
            )

        # Normal user → Student Dashboard
        return redirect(
            'student_dashboard'
        )


    # ------------------------------------------------------
    # HANDLE REGISTRATION FORM
    # ------------------------------------------------------

    if request.method == 'POST':

        # ==================================================
        # ACCOUNT INFORMATION
        # ==================================================

        username = request.POST.get(
            'username',
            ''
        ).strip()


        password = request.POST.get(
            'password',
            ''
        )


        # ==================================================
        # PERSONAL INFORMATION
        # ==================================================

        full_name = request.POST.get(
            'full_name',
            ''
        ).strip()


        student_id = request.POST.get(
            'student_id',
            ''
        ).strip()


        email = request.POST.get(
            'email',
            ''
        ).strip()


        phone = request.POST.get(
            'phone',
            ''
        ).strip()


        address = request.POST.get(
            'address',
            ''
        ).strip()


        # ==================================================
        # GUARDIAN INFORMATION
        # ==================================================

        guardian_name = request.POST.get(
            'guardian_name',
            ''
        ).strip()


        guardian_phone = request.POST.get(
            'guardian_phone',
            ''
        ).strip()


        # ==================================================
        # REQUIRED FIELD VALIDATION
        # ==================================================

        if not username or not password:

            messages.error(
                request,
                'Username and password are required.'
            )

            return redirect(
                'register'
            )


        if not full_name or not student_id:

            messages.error(
                request,
                'Full name and student ID are required.'
            )

            return redirect(
                'register'
            )


        # ==================================================
        # USERNAME VALIDATION
        # ==================================================

        if User.objects.filter(
            username=username
        ).exists():

            messages.error(
                request,
                'Username already exists. Please choose another username.'
            )

            return redirect(
                'register'
            )


        # ==================================================
        # STUDENT ID VALIDATION
        # ==================================================

        if Student.objects.filter(
            student_id=student_id
        ).exists():

            messages.error(
                request,
                'Student ID already exists.'
            )

            return redirect(
                'register'
            )


        # ==================================================
        # CREATE DJANGO USER
        # ==================================================

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name
        )


        # ==================================================
        # CREATE STUDENT PROFILE
        # ==================================================

        Student.objects.create(
            user=user,
            student_id=student_id,
            full_name=full_name,
            phone=phone,
            email=email,
            address=address,
            guardian_name=guardian_name,
            guardian_phone=guardian_phone,
        )


        # ==================================================
        # REGISTRATION SUCCESS MESSAGE
        # ==================================================

        messages.success(
            request,
            'Registration successful. Please login.'
        )


        # ==================================================
        # REDIRECT TO LOGIN
        # ==================================================

        return redirect(
            'login'
        )


    # ======================================================
    # DISPLAY REGISTRATION PAGE
    # ======================================================

    return render(
        request,
        'accounts/register.html'
    )


# ==========================================================
# LOGIN
# ==========================================================

def login_view(request):
    """
    Login for both students and hostel administrators.

    Student:
        Redirects to Student Dashboard.

    Admin:
        Redirects to Admin Dashboard.

    Login success messages are consumed by the
    respective dashboard templates.
    """

    # ------------------------------------------------------
    # ALREADY LOGGED-IN USER
    # ------------------------------------------------------

    if request.user.is_authenticated:

        # Superuser → Admin Dashboard
        if request.user.is_superuser:

            return redirect(
                'admin_dashboard'
            )

        # Normal user → Student Dashboard
        return redirect(
            'student_dashboard'
        )


    # ------------------------------------------------------
    # HANDLE LOGIN FORM
    # ------------------------------------------------------

    if request.method == 'POST':

        username = request.POST.get(
            'username',
            ''
        ).strip()


        password = request.POST.get(
            'password',
            ''
        )


        # ==================================================
        # EMPTY FIELD VALIDATION
        # ==================================================

        if not username or not password:

            messages.error(
                request,
                'Please enter both username and password.'
            )

            return render(
                request,
                'accounts/login.html'
            )


        # ==================================================
        # AUTHENTICATE USER
        # ==================================================

        user = authenticate(
            request,
            username=username,
            password=password
        )


        # ==================================================
        # AUTHENTICATION SUCCESS
        # ==================================================

        if user is not None:

            # Create authenticated session
            login(
                request,
                user
            )


            # ==================================================
            # ADMIN LOGIN
            # ==================================================

            if user.is_superuser:

                messages.success(
                    request,
                    'Welcome to the Admin Dashboard.'
                )

                return redirect(
                    'admin_dashboard'
                )


            # ==================================================
            # STUDENT PROFILE CHECK
            # ==================================================

            if not hasattr(
                user,
                'student_profile'
            ):

                # Remove invalid login session
                logout(
                    request
                )


                messages.error(
                    request,
                    'Student profile not found. Please contact the hostel administrator.'
                )


                return redirect(
                    'login'
                )


            # ==================================================
            # STUDENT LOGIN SUCCESS
            # ==================================================

            messages.success(
                request,
                'Login successful. Welcome to DIDI BAHINI GIRLS HOSTEL.'
            )


            # Redirect to student dashboard
            return redirect(
                'student_dashboard'
            )


        # ==================================================
        # INVALID LOGIN
        # ==================================================

        messages.error(
            request,
            'Invalid username or password.'
        )


    # ======================================================
    # DISPLAY LOGIN PAGE
    # ======================================================

    return render(
        request,
        'accounts/login.html'
    )


# ==========================================================
# LOGOUT
# ==========================================================

def logout_view(request):
    """
    Logout the currently authenticated user.

    After logout, the user is redirected to the public
    Home page where the logout success message is displayed.
    """

    # ------------------------------------------------------
    # LOGOUT CURRENT USER
    # ------------------------------------------------------

    logout(
        request
    )


    # ------------------------------------------------------
    # LOGOUT SUCCESS MESSAGE
    # ------------------------------------------------------

    messages.success(
        request,
        'You have been logged out successfully.'
    )


    # ------------------------------------------------------
    # REDIRECT TO HOME
    # ------------------------------------------------------

    return redirect(
        'home'
    )