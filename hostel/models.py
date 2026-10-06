from django.db import models
from django.contrib.auth.models import User


# ============================================================
# STUDENT MODEL
# ============================================================

class Student(models.Model):

    GENDER_CHOICES = (
        ('Female', 'Female'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )

    student_id = models.CharField(
        max_length=30,
        unique=True
    )

    full_name = models.CharField(
        max_length=150
    )

    phone = models.CharField(
        max_length=20
    )

    email = models.EmailField()

    address = models.TextField()

    guardian_name = models.CharField(
        max_length=150
    )

    guardian_phone = models.CharField(
        max_length=20
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True
    )

    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        default='Female'
    )

    course = models.CharField(
        max_length=150,
        blank=True
    )

    semester = models.CharField(
        max_length=50,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.student_id} - {self.full_name}"


# ============================================================
# ROOM MODEL
# ============================================================

class Room(models.Model):

    ROOM_TYPE_CHOICES = (
        ('Single', 'Single'),
        ('Double', 'Double'),
        ('Triple', 'Triple'),
        ('Four Bed', 'Four Bed'),
    )

    room_number = models.CharField(
        max_length=20,
        unique=True
    )

    floor = models.CharField(
        max_length=50
    )

    room_type = models.CharField(
        max_length=30,
        choices=ROOM_TYPE_CHOICES
    )

    capacity = models.PositiveIntegerField()

    monthly_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    description = models.TextField(
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # --------------------------------------------------------
    # ROOM OCCUPANCY
    # --------------------------------------------------------

    def occupied_count(self):

        return self.allocations.filter(
            is_active=True
        ).count()

    def available_count(self):

        return max(
            self.capacity - self.occupied_count(),
            0
        )

    def is_full(self):

        return (
            self.occupied_count()
            >= self.capacity
        )

    def __str__(self):

        return f"Room {self.room_number}"


# ============================================================
# ROOM ALLOCATION MODEL
# ============================================================

class RoomAllocation(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='allocations'
    )

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='allocations'
    )

    allocated_date = models.DateField(
        auto_now_add=True
    )

    vacated_date = models.DateField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    remarks = models.TextField(
        blank=True
    )

    def __str__(self):

        return (
            f"{self.student.full_name} - "
            f"{self.room.room_number}"
        )


# ============================================================
# FEE PAYMENT MODEL
# ============================================================

class FeePayment(models.Model):

    PAYMENT_METHOD_CHOICES = (
        ('Cash', 'Cash'),
        ('Bank', 'Bank'),
        ('Online', 'Online'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('Paid', 'Paid'),
        ('Pending', 'Pending'),
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_date = models.DateField()

    payment_method = models.CharField(
        max_length=30,
        choices=PAYMENT_METHOD_CHOICES
    )

    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='Paid'
    )

    month = models.CharField(
        max_length=30
    )

    transaction_id = models.CharField(
        max_length=100,
        blank=True
    )

    remarks = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return (
            f"{self.student.full_name} - "
            f"{self.amount}"
        )


# ============================================================
# NOTICE MODEL
# ============================================================

class Notice(models.Model):

    # --------------------------------------------------------
    # NOTICE INFORMATION
    # --------------------------------------------------------

    title = models.CharField(
        max_length=200
    )

    content = models.TextField()

    # --------------------------------------------------------
    # NOTICE CREATOR
    # --------------------------------------------------------

    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_hostel_notices'
    )

    # --------------------------------------------------------
    # NOTICE RECIPIENT
    # --------------------------------------------------------

    # True:
    #     Notice is sent to all students.
    #
    # False:
    #     Notice is sent only to selected students.

    send_to_all = models.BooleanField(
        default=True
    )

    # --------------------------------------------------------
    # SELECTED STUDENTS
    # --------------------------------------------------------

    students = models.ManyToManyField(
        Student,
        blank=True,
        related_name='received_notices'
    )

    # --------------------------------------------------------
    # NOTICE STATUS
    # --------------------------------------------------------

    is_active = models.BooleanField(
        default=True
    )

    # --------------------------------------------------------
    # DATE AND TIME
    # --------------------------------------------------------

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # --------------------------------------------------------
    # STRING REPRESENTATION
    # --------------------------------------------------------

    def __str__(self):

        return self.title