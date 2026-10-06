from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import (
    Student,
    Room,
    RoomAllocation,
    FeePayment,
    Notice,
)


# ============================================================
# ADMIN ACCESS
# ============================================================

def admin_required(view_func):
    """
    Allow only authenticated superusers to access
    hostel administration pages.
    """

    return user_passes_test(
        lambda user: (
            user.is_authenticated
            and user.is_superuser
        ),
        login_url='login'
    )(view_func)


# ============================================================
# STUDENT MANAGEMENT
# ============================================================

@admin_required
def student_list(request):
    """
    Display all registered hostel students.
    """

    search_query = request.GET.get(
        'search',
        ''
    ).strip()

    students = (
        Student.objects
        .select_related('user')
        .all()
        .order_by('-created_at')
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search_query:

        students = students.filter(
            Q(student_id__icontains=search_query)
            |
            Q(full_name__icontains=search_query)
            |
            Q(email__icontains=search_query)
            |
            Q(phone__icontains=search_query)
            |
            Q(address__icontains=search_query)
            |
            Q(guardian_name__icontains=search_query)
            |
            Q(guardian_phone__icontains=search_query)
        )

    context = {
        'students': students,
        'total_students': students.count(),
        'search_query': search_query,
    }

    return render(
        request,
        'hostel/student_list.html',
        context
    )


# ============================================================
# STUDENT DETAIL
# ============================================================

@admin_required
def student_detail(request, pk):
    """
    Display complete information about a student.
    """

    student = get_object_or_404(
        Student.objects.select_related('user'),
        pk=pk
    )

    # --------------------------------------------------------
    # ACTIVE ROOM ALLOCATION
    # --------------------------------------------------------

    allocation = (
        RoomAllocation.objects
        .select_related('room')
        .filter(
            student=student,
            is_active=True
        )
        .first()
    )

    # --------------------------------------------------------
    # PAYMENT HISTORY
    # --------------------------------------------------------

    payments = (
        FeePayment.objects
        .filter(
            student=student
        )
        .order_by(
            '-payment_date',
            '-created_at'
        )
    )

    # --------------------------------------------------------
    # TOTAL PAID
    # --------------------------------------------------------

    total_paid = sum(
        payment.amount
        for payment in payments
        if payment.status == 'Paid'
    )

    # --------------------------------------------------------
    # CONTEXT
    # --------------------------------------------------------

    context = {
        'student': student,
        'allocation': allocation,
        'payments': payments,
        'total_paid': total_paid,
    }

    return render(
        request,
        'hostel/student_detail.html',
        context
    )


# ============================================================
# DELETE STUDENT
# ============================================================

@admin_required
def student_delete(request, pk):
    """
    Delete a student and associated Django user account.

    Only POST requests are accepted.
    """

    # --------------------------------------------------------
    # SECURITY
    # --------------------------------------------------------

    if request.method != 'POST':

        messages.error(
            request,
            'Invalid request method.'
        )

        return redirect(
            'student_list'
        )

    student = get_object_or_404(
        Student,
        pk=pk
    )

    student_name = student.full_name
    student_id = student.student_id

    # --------------------------------------------------------
    # DELETE USER
    # --------------------------------------------------------

    try:

        user = student.user

        if user:
            user.delete()
        else:
            student.delete()

    except Exception:

        student.delete()

    messages.success(
        request,
        f'Student "{student_name}" '
        f'({student_id}) deleted successfully.'
    )

    return redirect(
        'student_list'
    )


# ============================================================
# ROOM MANAGEMENT
# ============================================================

@admin_required
def room_list(request):
    """
    Display all hostel rooms and room statistics.
    """

    rooms = list(
        Room.objects
        .all()
        .order_by('room_number')
    )

    total_rooms = len(rooms)

    active_rooms = 0
    inactive_rooms = 0

    available_rooms = 0
    full_rooms = 0

    total_capacity = 0
    occupied_beds = 0
    available_beds = 0

    # --------------------------------------------------------
    # ROOM STATISTICS
    # --------------------------------------------------------

    for room in rooms:

        occupied_count = (
            RoomAllocation.objects
            .filter(
                room=room,
                is_active=True
            )
            .count()
        )

        room.occupied_beds = occupied_count

        room.available_beds = max(
            room.capacity - occupied_count,
            0
        )

        room.full_status = (
            occupied_count >= room.capacity
        )

        total_capacity += room.capacity

        if room.is_active:
            active_rooms += 1
        else:
            inactive_rooms += 1

        if (
            room.is_active
            and not room.full_status
        ):
            available_rooms += 1

        if room.full_status:
            full_rooms += 1

        occupied_beds += occupied_count
        available_beds += room.available_beds

    context = {
        'rooms': rooms,
        'total_rooms': total_rooms,
        'active_rooms': active_rooms,
        'inactive_rooms': inactive_rooms,
        'available_rooms': available_rooms,
        'full_rooms': full_rooms,
        'total_capacity': total_capacity,
        'occupied_beds': occupied_beds,
        'available_beds': available_beds,
    }

    return render(
        request,
        'hostel/room_list.html',
        context
    )


# ============================================================
# CREATE ROOM
# ============================================================

@admin_required
def room_create(request):
    """
    Create a new hostel room.
    """

    if request.method == 'POST':

        room_number = request.POST.get(
            'room_number',
            ''
        ).strip()

        floor = request.POST.get(
            'floor',
            ''
        ).strip()

        room_type = request.POST.get(
            'room_type',
            ''
        ).strip()

        capacity = request.POST.get(
            'capacity',
            ''
        ).strip()

        monthly_fee = request.POST.get(
            'monthly_fee',
            ''
        ).strip()

        description = request.POST.get(
            'description',
            ''
        ).strip()

        # ----------------------------------------------------
        # REQUIRED VALIDATION
        # ----------------------------------------------------

        if not room_number:

            messages.error(
                request,
                'Room number is required.'
            )

            return redirect(
                'room_create'
            )

        if not floor:

            messages.error(
                request,
                'Floor is required.'
            )

            return redirect(
                'room_create'
            )

        if not room_type:

            messages.error(
                request,
                'Please select a room type.'
            )

            return redirect(
                'room_create'
            )

        if not capacity:

            messages.error(
                request,
                'Room capacity is required.'
            )

            return redirect(
                'room_create'
            )

        if not monthly_fee:

            messages.error(
                request,
                'Monthly fee is required.'
            )

            return redirect(
                'room_create'
            )

        # ----------------------------------------------------
        # DUPLICATE ROOM
        # ----------------------------------------------------

        if Room.objects.filter(
            room_number=room_number
        ).exists():

            messages.error(
                request,
                f'Room {room_number} already exists.'
            )

            return redirect(
                'room_create'
            )

        # ----------------------------------------------------
        # CAPACITY
        # ----------------------------------------------------

        try:

            capacity_value = int(
                capacity
            )

            if capacity_value < 1:

                messages.error(
                    request,
                    'Room capacity must be at least 1.'
                )

                return redirect(
                    'room_create'
                )

        except (ValueError, TypeError):

            messages.error(
                request,
                'Room capacity must be a valid number.'
            )

            return redirect(
                'room_create'
            )

        # ----------------------------------------------------
        # MONTHLY FEE
        # ----------------------------------------------------

        try:

            monthly_fee_value = float(
                monthly_fee
            )

            if monthly_fee_value < 0:

                messages.error(
                    request,
                    'Monthly fee cannot be negative.'
                )

                return redirect(
                    'room_create'
                )

        except (ValueError, TypeError):

            messages.error(
                request,
                'Monthly fee must be a valid amount.'
            )

            return redirect(
                'room_create'
            )

        # ----------------------------------------------------
        # CREATE ROOM
        # ----------------------------------------------------

        Room.objects.create(

            room_number=room_number,

            floor=floor,

            room_type=room_type,

            capacity=capacity_value,

            monthly_fee=monthly_fee_value,

            description=description,

        )

        messages.success(
            request,
            f'Room {room_number} added successfully.'
        )

        return redirect(
            'room_list'
        )

    return render(
        request,
        'hostel/room_form.html'
    )


# ============================================================
# ROOM ALLOCATION LIST
# ============================================================

@admin_required
def allocation_list(request):
    """
    Display all active room allocations.
    """

    allocations = (
        RoomAllocation.objects
        .select_related(
            'student',
            'room'
        )
        .filter(
            is_active=True
        )
        .order_by(
            '-allocated_date'
        )
    )

    context = {
        'allocations': allocations,
        'total_allocations': allocations.count(),
    }

    return render(
        request,
        'hostel/allocation_list.html',
        context
    )


# ============================================================
# ALLOCATE STUDENT
# ============================================================

@admin_required
def allocate_student(request):
    """
    Allocate an available room to a student.
    """

    students = (
        Student.objects
        .all()
        .order_by('full_name')
    )

    rooms = list(
        Room.objects
        .filter(
            is_active=True
        )
        .order_by('room_number')
    )

    # --------------------------------------------------------
    # ROOM AVAILABILITY
    # --------------------------------------------------------

    for room in rooms:

        occupied_count = (
            RoomAllocation.objects
            .filter(
                room=room,
                is_active=True
            )
            .count()
        )

        room.occupied_beds = occupied_count

        room.available_beds = max(
            room.capacity - occupied_count,
            0
        )

        room.full_status = (
            room.available_beds <= 0
        )

    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    if request.method == 'POST':

        student_id = request.POST.get(
            'student'
        )

        room_id = request.POST.get(
            'room'
        )

        remarks = request.POST.get(
            'remarks',
            ''
        ).strip()

        if not student_id:

            messages.error(
                request,
                'Please select a student.'
            )

            return redirect(
                'allocate_student'
            )

        if not room_id:

            messages.error(
                request,
                'Please select a room.'
            )

            return redirect(
                'allocate_student'
            )

        student = get_object_or_404(
            Student,
            id=student_id
        )

        room = get_object_or_404(
            Room,
            id=room_id,
            is_active=True
        )

        # ----------------------------------------------------
        # EXISTING ALLOCATION
        # ----------------------------------------------------

        if RoomAllocation.objects.filter(
            student=student,
            is_active=True
        ).exists():

            messages.error(
                request,
                f'{student.full_name} already has '
                f'an active room.'
            )

            return redirect(
                'allocate_student'
            )

        # ----------------------------------------------------
        # ROOM CAPACITY
        # ----------------------------------------------------

        occupied_count = (
            RoomAllocation.objects
            .filter(
                room=room,
                is_active=True
            )
            .count()
        )

        if occupied_count >= room.capacity:

            messages.error(
                request,
                f'Room {room.room_number} is already full.'
            )

            return redirect(
                'allocate_student'
            )

        # ----------------------------------------------------
        # CREATE ALLOCATION
        # ----------------------------------------------------

        RoomAllocation.objects.create(

            student=student,

            room=room,

            is_active=True,

            remarks=remarks

        )

        messages.success(
            request,
            f'{student.full_name} has been allocated '
            f'to Room {room.room_number}.'
        )

        return redirect(
            'allocation_list'
        )

    return render(
        request,
        'hostel/allocation_form.html',
        {
            'students': students,
            'rooms': rooms,
        }
    )


# ============================================================
# VACATE ROOM
# ============================================================

@admin_required
def vacate_room(request, pk):
    """
    Vacate a student's active room allocation.
    """

    allocation = get_object_or_404(
        RoomAllocation,
        pk=pk,
        is_active=True
    )

    student_name = allocation.student.full_name
    room_number = allocation.room.room_number

    allocation.is_active = False

    allocation.vacated_date = timezone.localdate()

    allocation.save(
        update_fields=[
            'is_active',
            'vacated_date'
        ]
    )

    messages.success(
        request,
        f'{student_name} has been vacated from '
        f'Room {room_number}.'
    )

    return redirect(
        'allocation_list'
    )


# ============================================================
# PAYMENT MANAGEMENT
# ============================================================

@admin_required
def payment_list(request):
    """
    Display all hostel fee payments.
    """

    payments = (
        FeePayment.objects
        .select_related(
            'student'
        )
        .order_by(
            '-payment_date',
            '-created_at'
        )
    )

    total_payments = payments.count()

    paid_payments = payments.filter(
        status='Paid'
    ).count()

    pending_payments = payments.filter(
        status='Pending'
    ).count()

    context = {
        'payments': payments,
        'total_payments': total_payments,
        'paid_payments': paid_payments,
        'pending_payments': pending_payments,
    }

    return render(
        request,
        'hostel/payment_list.html',
        context
    )


# ============================================================
# CREATE PAYMENT
# ============================================================

@admin_required
def payment_create(request):
    """
    Record a new hostel fee payment.
    """

    students = (
        Student.objects
        .all()
        .order_by('full_name')
    )

    if request.method == 'POST':

        student_id = request.POST.get(
            'student'
        )

        amount = request.POST.get(
            'amount',
            ''
        ).strip()

        payment_date = request.POST.get(
            'payment_date'
        )

        payment_method = request.POST.get(
            'payment_method'
        )

        status = request.POST.get(
            'status'
        )

        month = request.POST.get(
            'month',
            ''
        ).strip()

        transaction_id = request.POST.get(
            'transaction_id',
            ''
        ).strip()

        remarks = request.POST.get(
            'remarks',
            ''
        ).strip()

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not student_id:

            messages.error(
                request,
                'Please select a student.'
            )

            return redirect(
                'payment_create'
            )

        if not amount:

            messages.error(
                request,
                'Payment amount is required.'
            )

            return redirect(
                'payment_create'
            )

        if not payment_date:

            messages.error(
                request,
                'Payment date is required.'
            )

            return redirect(
                'payment_create'
            )

        if not payment_method:

            messages.error(
                request,
                'Please select a payment method.'
            )

            return redirect(
                'payment_create'
            )

        if not status:

            messages.error(
                request,
                'Please select payment status.'
            )

            return redirect(
                'payment_create'
            )

        if not month:

            messages.error(
                request,
                'Payment month is required.'
            )

            return redirect(
                'payment_create'
            )

        student = get_object_or_404(
            Student,
            id=student_id
        )

        # ----------------------------------------------------
        # AMOUNT VALIDATION
        # ----------------------------------------------------

        try:

            amount_value = float(
                amount
            )

            if amount_value <= 0:

                messages.error(
                    request,
                    'Payment amount must be greater than zero.'
                )

                return redirect(
                    'payment_create'
                )

        except (ValueError, TypeError):

            messages.error(
                request,
                'Payment amount must be a valid number.'
            )

            return redirect(
                'payment_create'
            )

        # ----------------------------------------------------
        # CREATE PAYMENT
        # ----------------------------------------------------

        FeePayment.objects.create(

            student=student,

            amount=amount_value,

            payment_date=payment_date,

            payment_method=payment_method,

            status=status,

            month=month,

            transaction_id=transaction_id,

            remarks=remarks,

        )

        messages.success(
            request,
            f'Fee payment for {student.full_name} '
            f'was recorded successfully.'
        )

        return redirect(
            'payment_list'
        )

    return render(
        request,
        'hostel/payment_form.html',
        {
            'students': students
        }
    )


# ============================================================
# NOTICE MANAGEMENT
# ============================================================

@admin_required
def notice_list(request):
    """
    Display all hostel notices.
    """

    notices = (
        Notice.objects
        .select_related(
            'created_by'
        )
        .prefetch_related(
            'students'
        )
        .all()
        .order_by(
            '-created_at'
        )
    )

    context = {
        'notices': notices,
        'total_notices': notices.count(),
        'active_notices': notices.filter(
            is_active=True
        ).count(),
        'inactive_notices': notices.filter(
            is_active=False
        ).count(),
    }

    return render(
        request,
        'hostel/notice_list.html',
        context
    )


# ============================================================
# CREATE NOTICE
# ============================================================

@admin_required
def notice_create(request):
    """
    Create a notice.

    Admin can send notice to:
    - All students
    - One student
    - Multiple selected students
    """

    students = (
        Student.objects
        .all()
        .order_by(
            'full_name'
        )
    )

    if request.method == 'POST':

        title = request.POST.get(
            'title',
            ''
        ).strip()

        content = request.POST.get(
            'content',
            ''
        ).strip()

        recipient_type = request.POST.get(
            'recipient_type',
            'all'
        )

        selected_student_ids = request.POST.getlist(
            'students'
        )

        is_active = (
            request.POST.get(
                'is_active'
            ) == '1'
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        if not title:

            messages.error(
                request,
                'Notice title is required.'
            )

            return render(
                request,
                'hostel/notice_form.html',
                {
                    'students': students,
                    'notice': None,
                    'selected_students':
                        selected_student_ids,
                }
            )

        # ----------------------------------------------------
        # CONTENT
        # ----------------------------------------------------

        if not content:

            messages.error(
                request,
                'Notice content is required.'
            )

            return render(
                request,
                'hostel/notice_form.html',
                {
                    'students': students,
                    'notice': None,
                    'selected_students':
                        selected_student_ids,
                }
            )

        # ----------------------------------------------------
        # RECIPIENT TYPE
        # ----------------------------------------------------

        if recipient_type not in [
            'all',
            'selected'
        ]:

            messages.error(
                request,
                'Invalid notice recipient type.'
            )

            return render(
                request,
                'hostel/notice_form.html',
                {
                    'students': students,
                    'notice': None,
                    'selected_students':
                        selected_student_ids,
                }
            )

        selected_students = []

        # ----------------------------------------------------
        # SELECTED STUDENTS
        # ----------------------------------------------------

        if recipient_type == 'selected':

            if not selected_student_ids:

                messages.error(
                    request,
                    'Please select at least one student.'
                )

                return render(
                    request,
                    'hostel/notice_form.html',
                    {
                        'students': students,
                        'notice': None,
                        'selected_students': [],
                    }
                )

            selected_students = list(
                Student.objects.filter(
                    id__in=selected_student_ids
                )
            )

            if not selected_students:

                messages.error(
                    request,
                    'Selected student does not exist.'
                )

                return render(
                    request,
                    'hostel/notice_form.html',
                    {
                        'students': students,
                        'notice': None,
                        'selected_students': [],
                    }
                )

        # ----------------------------------------------------
        # CREATE NOTICE
        # ----------------------------------------------------

        notice = Notice.objects.create(

            title=title,

            content=content,

            created_by=request.user,

            send_to_all=(
                recipient_type == 'all'
            ),

            is_active=is_active,

        )

        # ----------------------------------------------------
        # ADD SELECTED STUDENTS
        # ----------------------------------------------------

        if recipient_type == 'selected':

            notice.students.set(
                selected_students
            )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        if recipient_type == 'all':

            messages.success(
                request,
                'Notice published successfully '
                'to all students.'
            )

        else:

            messages.success(
                request,
                f'Notice sent successfully to '
                f'{len(selected_students)} student(s).'
            )

        return redirect(
            'notice_list'
        )

    return render(
        request,
        'hostel/notice_form.html',
        {
            'students': students,
            'notice': None,
            'selected_students': [],
        }
    )


# ============================================================
# UPDATE NOTICE
# ============================================================

@admin_required
def notice_update(request, pk):
    """
    Update an existing notice.
    """

    notice = get_object_or_404(
        Notice,
        pk=pk
    )

    students = (
        Student.objects
        .all()
        .order_by(
            'full_name'
        )
    )

    existing_students = list(
        notice.students.values_list(
            'id',
            flat=True
        )
    )

    if request.method == 'POST':

        title = request.POST.get(
            'title',
            ''
        ).strip()

        content = request.POST.get(
            'content',
            ''
        ).strip()

        recipient_type = request.POST.get(
            'recipient_type',
            'all'
        )

        selected_student_ids = request.POST.getlist(
            'students'
        )

        is_active = (
            request.POST.get(
                'is_active'
            ) == '1'
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        if not title:

            messages.error(
                request,
                'Notice title is required.'
            )

            return render(
                request,
                'hostel/notice_form.html',
                {
                    'notice': notice,
                    'students': students,
                    'selected_students':
                        selected_student_ids,
                }
            )

        # ----------------------------------------------------
        # CONTENT
        # ----------------------------------------------------

        if not content:

            messages.error(
                request,
                'Notice content is required.'
            )

            return render(
                request,
                'hostel/notice_form.html',
                {
                    'notice': notice,
                    'students': students,
                    'selected_students':
                        selected_student_ids,
                }
            )

        # ----------------------------------------------------
        # RECIPIENT TYPE
        # ----------------------------------------------------

        if recipient_type not in [
            'all',
            'selected'
        ]:

            messages.error(
                request,
                'Invalid notice recipient type.'
            )

            return render(
                request,
                'hostel/notice_form.html',
                {
                    'notice': notice,
                    'students': students,
                    'selected_students':
                        selected_student_ids,
                }
            )

        selected_students = []

        # ----------------------------------------------------
        # SELECTED STUDENTS
        # ----------------------------------------------------

        if recipient_type == 'selected':

            if not selected_student_ids:

                messages.error(
                    request,
                    'Please select at least one student.'
                )

                return render(
                    request,
                    'hostel/notice_form.html',
                    {
                        'notice': notice,
                        'students': students,
                        'selected_students': [],
                    }
                )

            selected_students = list(
                Student.objects.filter(
                    id__in=selected_student_ids
                )
            )

            if not selected_students:

                messages.error(
                    request,
                    'Selected student does not exist.'
                )

                return render(
                    request,
                    'hostel/notice_form.html',
                    {
                        'notice': notice,
                        'students': students,
                        'selected_students': [],
                    }
                )

        # ----------------------------------------------------
        # UPDATE
        # ----------------------------------------------------

        notice.title = title

        notice.content = content

        notice.send_to_all = (
            recipient_type == 'all'
        )

        notice.is_active = is_active

        notice.save()

        # ----------------------------------------------------
        # UPDATE RECIPIENTS
        # ----------------------------------------------------

        notice.students.clear()

        if recipient_type == 'selected':

            notice.students.set(
                selected_students
            )

        messages.success(
            request,
            'Notice updated successfully.'
        )

        return redirect(
            'notice_list'
        )

    return render(
        request,
        'hostel/notice_form.html',
        {
            'notice': notice,
            'students': students,
            'selected_students':
                existing_students,
        }
    )


# ============================================================
# DELETE NOTICE
# ============================================================

@admin_required
def notice_delete(request, pk):
    """
    Delete a hostel notice.
    """

    if request.method != 'POST':

        messages.error(
            request,
            'Invalid request method.'
        )

        return redirect(
            'notice_list'
        )

    notice = get_object_or_404(
        Notice,
        pk=pk
    )

    notice_title = notice.title

    notice.delete()

    messages.success(
        request,
        f'Notice "{notice_title}" deleted successfully.'
    )

    return redirect(
        'notice_list'
    )


# ============================================================
# STUDENT NOTICE PAGE
# ============================================================

@login_required
def student_notices(request):
    """
    Display notices for the logged-in student.

    Students can see:
    1. Notices sent to all students.
    2. Notices specifically sent to them.
    """

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

    if request.user.is_superuser:

        notices = (
            Notice.objects
            .filter(
                is_active=True
            )
            .select_related(
                'created_by'
            )
            .prefetch_related(
                'students'
            )
            .order_by(
                '-created_at'
            )
        )

    # --------------------------------------------------------
    # STUDENT
    # --------------------------------------------------------

    else:

        student = getattr(
            request.user,
            'student_profile',
            None
        )

        if student is None:

            messages.error(
                request,
                'Student profile not found.'
            )

            return redirect(
                'student_dashboard'
            )

        notices = (
            Notice.objects
            .filter(
                is_active=True
            )
            .filter(
                Q(send_to_all=True)
                |
                Q(students=student)
            )
            .select_related(
                'created_by'
            )
            .prefetch_related(
                'students'
            )
            .distinct()
            .order_by(
                '-created_at'
            )
        )

    context = {
        'notices': notices,
        'total_notices': notices.count(),
    }

    return render(
        request,
        'hostel/student_notices.html',
        context
    )