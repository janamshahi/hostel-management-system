from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from hostel.models import (
    FeePayment,
    Notice,
    Room,
    RoomAllocation,
    Student,
)


# ============================================================
# ADMIN ACCESS CONTROL
# ============================================================

def admin_required(view_func):
    """
    Allow access only to authenticated Django superusers.

    Normal students cannot access the custom administrator
    dashboard.
    """

    return user_passes_test(
        lambda user: (
            user.is_authenticated
            and user.is_superuser
        ),
        login_url="admin_login"
    )(view_func)


# ============================================================
# STUDENT ID GENERATOR
# ============================================================

def generate_student_id():
    """
    Generate the next student ID.

    Format:
        DBH-001
        DBH-002
        DBH-003
        ...
    """

    students = Student.objects.filter(
        student_id__startswith="DBH-"
    ).values_list(
        "student_id",
        flat=True
    )

    highest_number = 0

    for student_id in students:

        try:
            number = int(
                student_id.replace("DBH-", "")
            )

            if number > highest_number:
                highest_number = number

        except (ValueError, TypeError):
            continue

    next_number = highest_number + 1

    return f"DBH-{next_number:03d}"


# ============================================================
# STUDENT DASHBOARD
# ============================================================

@login_required
def dashboard(request):
    """
    Student dashboard.

    Superusers are redirected to the administrator dashboard.
    Normal students see their profile, room, payments and notices.
    """

    # --------------------------------------------------------
    # Prevent administrators from using student dashboard
    # --------------------------------------------------------

    if request.user.is_superuser:
        return redirect("admin_dashboard")

    # --------------------------------------------------------
    # Get student profile
    # --------------------------------------------------------

    try:

        student = request.user.student_profile

    except Student.DoesNotExist:

        messages.error(
            request,
            "Student profile was not found."
        )

        return redirect("login")

    # --------------------------------------------------------
    # Get latest active room allocation
    # --------------------------------------------------------

    active_allocation = (
        RoomAllocation.objects
        .filter(
            student=student,
            is_active=True
        )
        .select_related("room")
        .order_by(
            "-allocated_date",
            "-id"
        )
        .first()
    )

    # --------------------------------------------------------
    # Payment history
    # --------------------------------------------------------

    payments = (
        FeePayment.objects
        .filter(student=student)
        .order_by(
            "-payment_date",
            "-id"
        )
    )

    # --------------------------------------------------------
    # Student notices
    #
    # Notice can be:
    # 1. Sent to everyone
    # 2. Sent specifically to this student
    # --------------------------------------------------------

    notices = (
        Notice.objects
        .filter(is_active=True)
        .filter(
            Q(send_to_all=True)
            | Q(students=student)
        )
        .select_related("created_by")
        .distinct()
        .order_by("-created_at")
    )

    # --------------------------------------------------------
    # Total paid amount
    # --------------------------------------------------------

    total_paid = (
        FeePayment.objects
        .filter(
            student=student,
            status__iexact="Paid"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # Total pending amount
    # --------------------------------------------------------

    pending_amount = (
        FeePayment.objects
        .filter(
            student=student,
            status__iexact="Pending"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # Payment count
    # --------------------------------------------------------

    payment_count = (
        FeePayment.objects
        .filter(student=student)
        .count()
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # The current student_dashboard.html uses:
    #
    #     allocation.room.room_number
    #
    # Therefore provide "allocation".
    #
    # "active_allocation" is also provided for compatibility
    # with other templates.
    # --------------------------------------------------------

    context = {

        "student": student,

        "allocation": active_allocation,

        "active_allocation": active_allocation,

        "payments": payments,

        "notices": notices,

        "total_paid": total_paid,

        "pending_amount": pending_amount,

        "payment_count": payment_count,
    }

    return render(
        request,
        "dashboard/student_dashboard.html",
        context
    )


# ============================================================
# STUDENT NOTICES
# ============================================================

@login_required
def student_notices(request):
    """
    Display notices available to the logged-in student.
    """

    if request.user.is_superuser:
        return redirect("admin_dashboard")

    try:

        student = request.user.student_profile

    except Student.DoesNotExist:

        messages.error(
            request,
            "Student profile was not found."
        )

        return redirect("login")

    notices = (
        Notice.objects
        .filter(is_active=True)
        .filter(
            Q(send_to_all=True)
            | Q(students=student)
        )
        .select_related("created_by")
        .distinct()
        .order_by("-created_at")
    )

    context = {
        "student": student,
        "notices": notices,
    }

    return render(
        request,
        "dashboard/student_notices.html",
        context
    )


# ============================================================
# STUDENT PROFILE
# ============================================================

@login_required
def student_profile(request):
    """
    Display the logged-in student's profile.
    """

    if request.user.is_superuser:
        return redirect("admin_dashboard")

    try:

        student = request.user.student_profile

    except Student.DoesNotExist:

        messages.error(
            request,
            "Student profile was not found."
        )

        return redirect("login")

    # --------------------------------------------------------
    # Latest active room allocation
    # --------------------------------------------------------

    active_allocation = (
        RoomAllocation.objects
        .filter(
            student=student,
            is_active=True
        )
        .select_related("room")
        .order_by(
            "-allocated_date",
            "-id"
        )
        .first()
    )

    # --------------------------------------------------------
    # Payment history
    # --------------------------------------------------------

    payments = (
        FeePayment.objects
        .filter(student=student)
        .order_by(
            "-payment_date",
            "-id"
        )
    )

    # --------------------------------------------------------
    # Total paid
    # --------------------------------------------------------

    total_paid = (
        FeePayment.objects
        .filter(
            student=student,
            status__iexact="Paid"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # Total pending
    # --------------------------------------------------------

    total_pending = (
        FeePayment.objects
        .filter(
            student=student,
            status__iexact="Pending"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    context = {

        "student": student,

        "allocation": active_allocation,

        "active_allocation": active_allocation,

        "payments": payments,

        "total_paid": total_paid,

        "total_pending": total_pending,
    }

    return render(
        request,
        "dashboard/student_profile.html",
        context
    )


# ============================================================
# EDIT STUDENT PROFILE
# ============================================================

@login_required
def edit_profile(request):
    """
    Allow students to edit their own profile.

    Student ID, gender and account username are not changed here.
    """

    if request.user.is_superuser:
        return redirect("admin_dashboard")

    try:

        student = request.user.student_profile

    except Student.DoesNotExist:

        messages.error(
            request,
            "Student profile was not found."
        )

        return redirect("login")

    if request.method == "POST":

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        date_of_birth = request.POST.get(
            "date_of_birth",
            ""
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        guardian_name = request.POST.get(
            "guardian_name",
            ""
        ).strip()

        guardian_phone = request.POST.get(
            "guardian_phone",
            ""
        ).strip()

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if not full_name:

            messages.error(
                request,
                "Full name is required."
            )

            return render(
                request,
                "dashboard/edit_profile.html",
                {
                    "student": student
                }
            )

        if not email:

            messages.error(
                request,
                "Email is required."
            )

            return render(
                request,
                "dashboard/edit_profile.html",
                {
                    "student": student
                }
            )

        if not phone:

            messages.error(
                request,
                "Phone number is required."
            )

            return render(
                request,
                "dashboard/edit_profile.html",
                {
                    "student": student
                }
            )

        if not guardian_name:

            messages.error(
                request,
                "Guardian name is required."
            )

            return render(
                request,
                "dashboard/edit_profile.html",
                {
                    "student": student
                }
            )

        if not guardian_phone:

            messages.error(
                request,
                "Guardian phone number is required."
            )

            return render(
                request,
                "dashboard/edit_profile.html",
                {
                    "student": student
                }
            )

        # ----------------------------------------------------
        # Update Student
        # ----------------------------------------------------

        student.full_name = full_name

        student.email = email

        student.phone = phone

        student.address = address

        student.guardian_name = guardian_name

        student.guardian_phone = guardian_phone

        if date_of_birth:

            try:

                student.date_of_birth = (
                    date.fromisoformat(date_of_birth)
                )

            except ValueError:

                messages.error(
                    request,
                    "Please enter a valid date of birth."
                )

                return render(
                    request,
                    "dashboard/edit_profile.html",
                    {
                        "student": student
                    }
                )

        else:

            student.date_of_birth = None

        student.save()

        # ----------------------------------------------------
        # Update Django User
        # ----------------------------------------------------

        user = request.user

        name_parts = full_name.split()

        user.first_name = (
            name_parts[0]
            if name_parts
            else ""
        )

        user.last_name = (
            " ".join(name_parts[1:])
            if len(name_parts) > 1
            else ""
        )

        user.email = email

        user.save()

        messages.success(
            request,
            "Your profile has been updated successfully."
        )

        return redirect("student_profile")

    return render(
        request,
        "dashboard/edit_profile.html",
        {
            "student": student
        }
    )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@admin_required
def admin_dashboard(request):
    """
    Main administrator dashboard.
    """

    # --------------------------------------------------------
    # Student statistics
    # --------------------------------------------------------

    total_students = Student.objects.count()

    # --------------------------------------------------------
    # Room statistics
    # --------------------------------------------------------

    total_rooms = Room.objects.count()

    active_rooms = Room.objects.filter(
        is_active=True
    )

    available_rooms = 0

    occupied_rooms = 0

    total_capacity = 0

    occupied_beds = 0

    available_beds = 0

    for room in active_rooms:

        occupied = room.occupied_count()

        available = max(
            room.capacity - occupied,
            0
        )

        total_capacity += room.capacity

        occupied_beds += occupied

        available_beds += available

        if available > 0:

            available_rooms += 1

        else:

            occupied_rooms += 1

    # --------------------------------------------------------
    # Allocation statistics
    # --------------------------------------------------------

    total_allocations = (
        RoomAllocation.objects
        .filter(is_active=True)
        .count()
    )

    # --------------------------------------------------------
    # Payment statistics
    # --------------------------------------------------------

    total_paid = (
        FeePayment.objects
        .filter(status__iexact="Paid")
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    pending_payments = (
        FeePayment.objects
        .filter(status__iexact="Pending")
        .count()
    )

    total_pending_amount = (
        FeePayment.objects
        .filter(status__iexact="Pending")
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # Occupancy percentage
    # --------------------------------------------------------

    if total_capacity > 0:

        occupancy_percentage = round(
            (
                occupied_beds
                / total_capacity
            ) * 100,
            2
        )

    else:

        occupancy_percentage = 0

    # --------------------------------------------------------
    # Recent students
    # --------------------------------------------------------

    recent_students = (
        Student.objects
        .select_related("user")
        .order_by("-created_at")[:5]
    )

    # --------------------------------------------------------
    # Recent payments
    # --------------------------------------------------------

    recent_payments = (
        FeePayment.objects
        .select_related("student")
        .order_by(
            "-payment_date",
            "-id"
        )[:5]
    )

    # --------------------------------------------------------
    # Recent notices
    # --------------------------------------------------------

    recent_notices = (
        Notice.objects
        .select_related("created_by")
        .order_by("-created_at")[:5]
    )

    # --------------------------------------------------------
    # Active notices
    # --------------------------------------------------------

    active_notices = Notice.objects.filter(
        is_active=True
    ).count()

    context = {

        "total_students": total_students,

        "total_rooms": total_rooms,

        "available_rooms": available_rooms,

        "occupied_rooms": occupied_rooms,

        "total_allocations": total_allocations,

        "total_paid": total_paid,

        "pending_payments": pending_payments,

        "total_pending_amount": total_pending_amount,

        "total_capacity": total_capacity,

        "occupied_beds": occupied_beds,

        "available_beds": available_beds,

        "occupancy_percentage": occupancy_percentage,

        "recent_students": recent_students,

        "recent_payments": recent_payments,

        "recent_notices": recent_notices,

        "active_notices": active_notices,

        "user": request.user,
    }

    return render(
        request,
        "dashboard/admin_dashboard.html",
        context
    )


# ============================================================
# ADMIN REPORTS
# ============================================================

@admin_required
def reports(request):
    """
    Administrator reports page.

    Includes:
    - Students
    - Rooms
    - Occupancy
    - Payments
    - Payment methods
    - Monthly payment totals
    - Room type statistics
    - Recent students
    - Recent payments
    - Notices
    """

    # --------------------------------------------------------
    # Basic counts
    # --------------------------------------------------------

    total_students = Student.objects.count()

    total_rooms = Room.objects.count()

    active_allocations = (
        RoomAllocation.objects
        .filter(is_active=True)
        .count()
    )

    # --------------------------------------------------------
    # Payments
    # --------------------------------------------------------

    total_paid_fees = (
        FeePayment.objects
        .filter(status__iexact="Paid")
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    total_pending_fees = (
        FeePayment.objects
        .filter(status__iexact="Pending")
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    total_payment_count = FeePayment.objects.count()

    paid_payment_count = (
        FeePayment.objects
        .filter(status__iexact="Paid")
        .count()
    )

    pending_payment_count = (
        FeePayment.objects
        .filter(status__iexact="Pending")
        .count()
    )

    # --------------------------------------------------------
    # Room statistics
    # --------------------------------------------------------

    active_rooms = Room.objects.filter(
        is_active=True
    )

    occupied_rooms = 0

    available_rooms = 0

    total_capacity = 0

    total_occupied_beds = 0

    total_available_beds = 0

    for room in active_rooms:

        occupied = room.occupied_count()

        available = max(
            room.capacity - occupied,
            0
        )

        total_capacity += room.capacity

        total_occupied_beds += occupied

        total_available_beds += available

        if occupied >= room.capacity:

            occupied_rooms += 1

        else:

            available_rooms += 1

    # --------------------------------------------------------
    # Payment method reports
    # --------------------------------------------------------

    cash_payment_total = (
        FeePayment.objects
        .filter(
            payment_method__iexact="Cash",
            status__iexact="Paid"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    cash_payment_count = (
        FeePayment.objects
        .filter(
            payment_method__iexact="Cash"
        )
        .count()
    )

    bank_payment_total = (
        FeePayment.objects
        .filter(
            payment_method__iexact="Bank",
            status__iexact="Paid"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    bank_payment_count = (
        FeePayment.objects
        .filter(
            payment_method__iexact="Bank"
        )
        .count()
    )

    online_payment_total = (
        FeePayment.objects
        .filter(
            payment_method__iexact="Online",
            status__iexact="Paid"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    online_payment_count = (
        FeePayment.objects
        .filter(
            payment_method__iexact="Online"
        )
        .count()
    )

    # --------------------------------------------------------
    # Monthly payment report
    # --------------------------------------------------------

    monthly_payments = []

    for month_number in range(1, 13):

        month_name = date(
            2000,
            month_number,
            1
        ).strftime("%B")

        month_total = (
            FeePayment.objects
            .filter(
                payment_date__month=month_number,
                status__iexact="Paid"
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0.00")
        )

        monthly_payments.append(
            {
                "month_name": month_name,
                "total": month_total,
            }
        )

    # --------------------------------------------------------
    # Room type report
    # --------------------------------------------------------

    room_type_report = []

    room_types = [
        choice[0]
        for choice in Room.ROOM_TYPE_CHOICES
    ]

    for room_type in room_types:

        rooms = Room.objects.filter(
            room_type=room_type,
            is_active=True
        )

        room_count = rooms.count()

        capacity = 0

        occupied = 0

        for room in rooms:

            capacity += room.capacity

            occupied += room.occupied_count()

        available = max(
            capacity - occupied,
            0
        )

        room_type_report.append(
            {
                "room_type": room_type,
                "room_count": room_count,
                "capacity": capacity,
                "occupied": occupied,
                "available": available,
            }
        )

    # --------------------------------------------------------
    # Individual room report
    # --------------------------------------------------------

    room_report = []

    rooms = (
        Room.objects
        .filter(is_active=True)
        .order_by("room_number")
    )

    for room in rooms:

        occupied_count = room.occupied_count()

        available_count = max(
            room.capacity - occupied_count,
            0
        )

        room_report.append(
            {
                "room": room,
                "occupied_count": occupied_count,
                "available_count": available_count,
            }
        )

    # --------------------------------------------------------
    # Recent payments
    # --------------------------------------------------------

    recent_payments = (
        FeePayment.objects
        .select_related("student")
        .order_by(
            "-payment_date",
            "-id"
        )[:10]
    )

    # --------------------------------------------------------
    # Recent students
    # --------------------------------------------------------

    recent_students = (
        Student.objects
        .order_by("-created_at")[:10]
    )

    # --------------------------------------------------------
    # Notices
    # --------------------------------------------------------

    total_notices = Notice.objects.count()

    active_notices = Notice.objects.filter(
        is_active=True
    ).count()

    inactive_notices = Notice.objects.filter(
        is_active=False
    ).count()

    # --------------------------------------------------------
    # Context
    # --------------------------------------------------------

    context = {

        "total_students": total_students,

        "total_rooms": total_rooms,

        "active_allocations": active_allocations,

        "total_paid_fees": total_paid_fees,

        "occupied_rooms": occupied_rooms,

        "available_rooms": available_rooms,

        "pending_payment_count": pending_payment_count,

        "active_notices": active_notices,

        "total_payment_count": total_payment_count,

        "paid_payment_count": paid_payment_count,

        "total_pending_fees": total_pending_fees,

        "cash_payment_total": cash_payment_total,

        "cash_payment_count": cash_payment_count,

        "bank_payment_total": bank_payment_total,

        "bank_payment_count": bank_payment_count,

        "online_payment_total": online_payment_total,

        "online_payment_count": online_payment_count,

        "monthly_payments": monthly_payments,

        "total_capacity": total_capacity,

        "total_occupied_beds": total_occupied_beds,

        "total_available_beds": total_available_beds,

        "room_type_report": room_type_report,

        "room_report": room_report,

        "recent_payments": recent_payments,

        "recent_students": recent_students,

        "total_notices": total_notices,

        "inactive_notices": inactive_notices,
    }

    return render(
        request,
        "dashboard/reports.html",
        context
    )


# ============================================================
# ADMIN STUDENT LIST
# ============================================================

@admin_required
def student_list(request):
    """
    Display all hostel students.
    """

    students = (
        Student.objects
        .select_related("user")
        .order_by("student_id")
    )

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    search = request.GET.get(
        "search",
        ""
    ).strip()

    if search:

        students = students.filter(
            Q(student_id__icontains=search)
            | Q(full_name__icontains=search)
            | Q(phone__icontains=search)
            | Q(email__icontains=search)
        )

    # --------------------------------------------------------
    # Gender
    # --------------------------------------------------------

    gender = request.GET.get(
        "gender",
        ""
    ).strip()

    if gender:

        students = students.filter(
            gender=gender
        )

    # --------------------------------------------------------
    # Context
    # --------------------------------------------------------

    context = {

        "students": students,

        "search": search,

        "gender": gender,

        "total_students": Student.objects.count(),
    }

    return render(
        request,
        "dashboard/student_list.html",
        context
    )


# ============================================================
# ADMIN ADD STUDENT
# ============================================================

@admin_required
def student_add(request):
    """
    Add a new student from administrator dashboard.

    A Django User account and Student profile are created
    together using an atomic transaction.
    """

    generated_student_id = generate_student_id()

    if request.method == "POST":

        # ----------------------------------------------------
        # Account information
        # ----------------------------------------------------

        username = request.POST.get(
            "username",
            ""
        ).strip()

        password = request.POST.get(
            "password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        # ----------------------------------------------------
        # Student information
        # ----------------------------------------------------

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        guardian_name = request.POST.get(
            "guardian_name",
            ""
        ).strip()

        guardian_phone = request.POST.get(
            "guardian_phone",
            ""
        ).strip()

        date_of_birth = request.POST.get(
            "date_of_birth",
            ""
        ).strip()

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if not username:

            messages.error(
                request,
                "Username is required."
            )

            return render(
                request,
                "dashboard/student_add.html",
                {
                    "generated_student_id":
                        generated_student_id
                }
            )

        if User.objects.filter(
            username__iexact=username
        ).exists():

            messages.error(
                request,
                "This username already exists."
            )

            return render(
                request,
                "dashboard/student_add.html",
                {
                    "generated_student_id":
                        generated_student_id
                }
            )

        if not password:

            messages.error(
                request,
                "Password is required."
            )

            return render(
                request,
                "dashboard/student_add.html",
                {
                    "generated_student_id":
                        generated_student_id
                }
            )

        if password != confirm_password:

            messages.error(
                request,
                "Passwords do not match."
            )

            return render(
                request,
                "dashboard/student_add.html",
                {
                    "generated_student_id":
                        generated_student_id
                }
            )

        if not full_name:

            messages.error(
                request,
                "Full name is required."
            )

            return render(
                request,
                "dashboard/student_add.html",
                {
                    "generated_student_id":
                        generated_student_id
                }
            )

        if not email:

            messages.error(
                request,
                "Email is required."
            )

            return render(
                request,
                "dashboard/student_add.html",
                {
                    "generated_student_id":
                        generated_student_id
                }
            )

        if not phone:

            messages.error(
                request,
                "Phone number is required."
            )

            return render(
                request,
                "dashboard/student_add.html",
                {
                    "generated_student_id":
                        generated_student_id
                }
            )

        if not guardian_name:

            messages.error(
                request,
                "Guardian name is required."
            )

            return render(
                request,
                "dashboard/student_add.html",
                {
                    "generated_student_id":
                        generated_student_id
                }
            )

        if not guardian_phone:

            messages.error(
                request,
                "Guardian phone number is required."
            )

            return render(
                request,
                "dashboard/student_add.html",
                {
                    "generated_student_id":
                        generated_student_id
                }
            )

        # ----------------------------------------------------
        # Parse DOB
        # ----------------------------------------------------

        parsed_dob = None

        if date_of_birth:

            try:

                parsed_dob = date.fromisoformat(
                    date_of_birth
                )

            except ValueError:

                messages.error(
                    request,
                    "Please enter a valid date of birth."
                )

                return render(
                    request,
                    "dashboard/student_add.html",
                    {
                        "generated_student_id":
                            generated_student_id
                    }
                )

        # ----------------------------------------------------
        # Create User + Student
        # ----------------------------------------------------

        try:

            with transaction.atomic():

                # --------------------------------------------
                # Generate ID again inside transaction
                # --------------------------------------------

                official_student_id = (
                    generate_student_id()
                )

                # --------------------------------------------
                # Create Django User
                # --------------------------------------------

                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email
                )

                # --------------------------------------------
                # Name
                # --------------------------------------------

                name_parts = full_name.split()

                user.first_name = (
                    name_parts[0]
                    if name_parts
                    else ""
                )

                user.last_name = (
                    " ".join(name_parts[1:])
                    if len(name_parts) > 1
                    else ""
                )

                user.save()

                # --------------------------------------------
                # Create Student
                # --------------------------------------------

                student = Student.objects.create(
                    user=user,
                    student_id=official_student_id,
                    full_name=full_name,
                    phone=phone,
                    email=email,
                    address=address,
                    guardian_name=guardian_name,
                    guardian_phone=guardian_phone,
                    date_of_birth=parsed_dob,
                    gender="Female",
                )

            messages.success(
                request,
                (
                    f"Student {student.full_name} "
                    f"was added successfully. "
                    f"Student ID: {student.student_id}"
                )
            )

            return redirect(
                "student_detail",
                student_id=student.id
            )

        except IntegrityError:

            messages.error(
                request,
                (
                    "Unable to create the student "
                    "because the username or student ID "
                    "already exists."
                )
            )

        except Exception as error:

            messages.error(
                request,
                (
                    "An error occurred while creating "
                    f"the student: {error}"
                )
            )

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    return render(
        request,
        "dashboard/student_add.html",
        {
            "generated_student_id":
                generated_student_id
        }
    )


# ============================================================
# ADMIN STUDENT DETAIL
# ============================================================

@admin_required
def student_detail(request, student_id):
    """
    Display complete information about a student.
    """

    student = get_object_or_404(
        Student.objects.select_related("user"),
        id=student_id
    )

    # --------------------------------------------------------
    # Latest active allocation
    # --------------------------------------------------------

    active_allocation = (
        RoomAllocation.objects
        .filter(
            student=student,
            is_active=True
        )
        .select_related("room")
        .order_by(
            "-allocated_date",
            "-id"
        )
        .first()
    )

    # --------------------------------------------------------
    # Payment history
    # --------------------------------------------------------

    payments = (
        FeePayment.objects
        .filter(student=student)
        .order_by(
            "-payment_date",
            "-id"
        )
    )

    # --------------------------------------------------------
    # Total paid
    # --------------------------------------------------------

    total_paid = (
        FeePayment.objects
        .filter(
            student=student,
            status__iexact="Paid"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # Total pending
    # --------------------------------------------------------

    total_pending = (
        FeePayment.objects
        .filter(
            student=student,
            status__iexact="Pending"
        )
        .aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    # --------------------------------------------------------
    # Context
    #
    # "allocation" is included because your existing
    # student_detail.html uses allocation.
    #
    # "active_allocation" is also included for compatibility.
    # --------------------------------------------------------

    context = {

        "student": student,

        "allocation": active_allocation,

        "active_allocation": active_allocation,

        "payments": payments,

        "total_paid": total_paid,

        "total_pending": total_pending,
    }

    return render(
        request,
        "dashboard/student_detail.html",
        context
    )


# ============================================================
# ADMIN EDIT STUDENT
# ============================================================

@admin_required
def student_edit(request, student_id):
    """
    Edit student information from administrator dashboard.
    """

    student = get_object_or_404(
        Student.objects.select_related("user"),
        id=student_id
    )

    user = student.user

    if request.method == "POST":

        full_name = request.POST.get(
            "full_name",
            ""
        ).strip()

        email = request.POST.get(
            "email",
            ""
        ).strip()

        phone = request.POST.get(
            "phone",
            ""
        ).strip()

        address = request.POST.get(
            "address",
            ""
        ).strip()

        guardian_name = request.POST.get(
            "guardian_name",
            ""
        ).strip()

        guardian_phone = request.POST.get(
            "guardian_phone",
            ""
        ).strip()

        date_of_birth = request.POST.get(
            "date_of_birth",
            ""
        ).strip()

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if not full_name:

            messages.error(
                request,
                "Full name is required."
            )

            return render(
                request,
                "dashboard/student_edit.html",
                {
                    "student": student
                }
            )

        if not email:

            messages.error(
                request,
                "Email is required."
            )

            return render(
                request,
                "dashboard/student_edit.html",
                {
                    "student": student
                }
            )

        if not phone:

            messages.error(
                request,
                "Phone number is required."
            )

            return render(
                request,
                "dashboard/student_edit.html",
                {
                    "student": student
                }
            )

        if not guardian_name:

            messages.error(
                request,
                "Guardian name is required."
            )

            return render(
                request,
                "dashboard/student_edit.html",
                {
                    "student": student
                }
            )

        if not guardian_phone:

            messages.error(
                request,
                "Guardian phone number is required."
            )

            return render(
                request,
                "dashboard/student_edit.html",
                {
                    "student": student
                }
            )

        # ----------------------------------------------------
        # Parse DOB
        # ----------------------------------------------------

        parsed_dob = None

        if date_of_birth:

            try:

                parsed_dob = date.fromisoformat(
                    date_of_birth
                )

            except ValueError:

                messages.error(
                    request,
                    "Please enter a valid date of birth."
                )

                return render(
                    request,
                    "dashboard/student_edit.html",
                    {
                        "student": student
                    }
                )

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        try:

            with transaction.atomic():

                student.full_name = full_name

                student.email = email

                student.phone = phone

                student.address = address

                student.guardian_name = guardian_name

                student.guardian_phone = guardian_phone

                student.date_of_birth = parsed_dob

                # Keep female-only hostel
                student.gender = "Female"

                student.save()

                # --------------------------------------------
                # Update Django User
                # --------------------------------------------

                name_parts = full_name.split()

                user.first_name = (
                    name_parts[0]
                    if name_parts
                    else ""
                )

                user.last_name = (
                    " ".join(name_parts[1:])
                    if len(name_parts) > 1
                    else ""
                )

                user.email = email

                user.save()

            messages.success(
                request,
                "Student information updated successfully."
            )

            return redirect(
                "student_detail",
                student_id=student.id
            )

        except IntegrityError:

            messages.error(
                request,
                "Unable to update student information."

            )

        except Exception as error:

            messages.error(
                request,
                (
                    "An error occurred while updating "
                    f"the student: {error}"
                )
            )

    return render(
        request,
        "dashboard/student_edit.html",
        {
            "student": student
        }
    )


# ============================================================
# ADMIN DELETE STUDENT
# ============================================================

@admin_required
def student_delete(request, student_id):
    """
    Delete a student.

    Because Student.user is OneToOne with CASCADE,
    deleting the User also removes the Student profile.
    """

    student = get_object_or_404(
        Student.objects.select_related("user"),
        id=student_id
    )

    if request.method != "POST":

        messages.warning(
            request,
            "Invalid request. Student was not deleted."
        )

        return redirect(
            "student_detail",
            student_id=student.id
        )

    student_name = student.full_name

    user = student.user

    try:

        with transaction.atomic():

            # ------------------------------------------------
            # Delete User.
            #
            # Student is related through OneToOne CASCADE,
            # so Student and related records are deleted
            # according to model relationships.
            # ------------------------------------------------

            user.delete()

        messages.success(
            request,
            f"Student {student_name} was deleted successfully."
        )

    except Exception as error:

        messages.error(
            request,
            (
                "Unable to delete the student: "
                f"{error}"
            )
        )

    return redirect("student_list")


# ============================================================
# ADMIN NOTICE LIST
# ============================================================

@admin_required
def notice_list(request):
    """
    Display all notices.
    """

    notices = (
        Notice.objects
        .select_related("created_by")
        .prefetch_related("students")
        .order_by("-created_at")
    )

    search = request.GET.get(
        "search",
        ""
    ).strip()

    if search:

        notices = notices.filter(
            Q(title__icontains=search)
            | Q(content__icontains=search)
        )

    status = request.GET.get(
        "status",
        ""
    ).strip()

    if status == "active":

        notices = notices.filter(
            is_active=True
        )

    elif status == "inactive":

        notices = notices.filter(
            is_active=False
        )

    context = {

        "notices": notices,

        "search": search,

        "status": status,

        "total_notices": Notice.objects.count(),

        "active_notices": Notice.objects.filter(
            is_active=True
        ).count(),

        "inactive_notices": Notice.objects.filter(
            is_active=False
        ).count(),
    }

    return render(
        request,
        "dashboard/notice_list.html",
        context
    )


# ============================================================
# ADMIN CREATE NOTICE
# ============================================================

@admin_required
def notice_create(request):
    """
    Create a new notice.

    Administrator can:
    - Send to all students
    - Send to selected students
    """

    students = (
        Student.objects
        .order_by("student_id")
    )

    if request.method == "POST":

        title = request.POST.get(
            "title",
            ""
        ).strip()

        content = request.POST.get(
            "content",
            ""
        ).strip()

        send_to_all = (
            request.POST.get("send_to_all")
            in ["on", "true", "1", "yes"]
        )

        selected_student_ids = request.POST.getlist(
            "students"
        )

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if not title:

            messages.error(
                request,
                "Notice title is required."
            )

            return render(
                request,
                "dashboard/notice_create.html",
                {
                    "students": students
                }
            )

        if not content:

            messages.error(
                request,
                "Notice content is required."
            )

            return render(
                request,
                "dashboard/notice_create.html",
                {
                    "students": students
                }
            )

        # ----------------------------------------------------
        # Create notice
        # ----------------------------------------------------

        try:

            with transaction.atomic():

                notice = Notice.objects.create(
                    title=title,
                    content=content,
                    created_by=request.user,
                    send_to_all=send_to_all,
                    is_active=True,
                )

                if not send_to_all:

                    selected_students = Student.objects.filter(
                        id__in=selected_student_ids
                    )

                    notice.students.set(
                        selected_students
                    )

            messages.success(
                request,
                "Notice created successfully."
            )

            return redirect(
                "notice_detail",
                notice_id=notice.id
            )

        except Exception as error:

            messages.error(
                request,
                (
                    "Unable to create notice: "
                    f"{error}"
                )
            )

    return render(
        request,
        "dashboard/notice_create.html",
        {
            "students": students
        }
    )


# ============================================================
# ADMIN NOTICE DETAIL
# ============================================================

@admin_required
def notice_detail(request, notice_id):
    """
    Display complete notice information.
    """

    notice = get_object_or_404(
        Notice.objects
        .select_related("created_by")
        .prefetch_related("students"),
        id=notice_id
    )

    context = {
        "notice": notice,
    }

    return render(
        request,
        "dashboard/notice_detail.html",
        context
    )


# ============================================================
# ADMIN EDIT NOTICE
# ============================================================

@admin_required
def notice_edit(request, notice_id):
    """
    Edit an existing notice.
    """

    notice = get_object_or_404(
        Notice.objects
        .prefetch_related("students"),
        id=notice_id
    )

    students = (
        Student.objects
        .order_by("student_id")
    )

    if request.method == "POST":

        title = request.POST.get(
            "title",
            ""
        ).strip()

        content = request.POST.get(
            "content",
            ""
        ).strip()

        send_to_all = (
            request.POST.get("send_to_all")
            in ["on", "true", "1", "yes"]
        )

        selected_student_ids = request.POST.getlist(
            "students"
        )

        is_active = (
            request.POST.get("is_active")
            in ["on", "true", "1", "yes"]
        )

        # ----------------------------------------------------
        # Validation
        # ----------------------------------------------------

        if not title:

            messages.error(
                request,
                "Notice title is required."
            )

            return render(
                request,
                "dashboard/notice_edit.html",
                {
                    "notice": notice,
                    "students": students,
                }
            )

        if not content:

            messages.error(
                request,
                "Notice content is required."
            )

            return render(
                request,
                "dashboard/notice_edit.html",
                {
                    "notice": notice,
                    "students": students,
                }
            )

        # ----------------------------------------------------
        # Update
        # ----------------------------------------------------

        try:

            with transaction.atomic():

                notice.title = title

                notice.content = content

                notice.send_to_all = send_to_all

                notice.is_active = is_active

                notice.save()

                if send_to_all:

                    notice.students.clear()

                else:

                    selected_students = Student.objects.filter(
                        id__in=selected_student_ids
                    )

                    notice.students.set(
                        selected_students
                    )

            messages.success(
                request,
                "Notice updated successfully."
            )

            return redirect(
                "notice_detail",
                notice_id=notice.id
            )

        except Exception as error:

            messages.error(
                request,
                (
                    "Unable to update notice: "
                    f"{error}"
                )
            )

    return render(
        request,
        "dashboard/notice_edit.html",
        {
            "notice": notice,
            "students": students,
        }
    )


# ============================================================
# ADMIN DELETE NOTICE
# ============================================================

@admin_required
def notice_delete(request, notice_id):
    """
    Delete a notice.
    """

    notice = get_object_or_404(
        Notice,
        id=notice_id
    )

    if request.method != "POST":

        messages.warning(
            request,
            "Invalid request. Notice was not deleted."
        )

        return redirect(
            "notice_detail",
            notice_id=notice.id
        )

    notice_title = notice.title

    try:

        notice.delete()

        messages.success(
            request,
            f'Notice "{notice_title}" was deleted successfully.'
        )

    except Exception as error:

        messages.error(
            request,
            (
                "Unable to delete notice: "
                f"{error}"
            )
        )

    return redirect("notice_list")