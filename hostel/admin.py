from django.contrib import admin

from .models import (
    Student,
    Room,
    RoomAllocation,
    FeePayment,
    Notice
)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):

    list_display = (
        'student_id',
        'full_name',
        'phone',
        'course',
        'semester',
    )

    search_fields = (
        'student_id',
        'full_name',
        'phone',
    )


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):

    list_display = (
        'room_number',
        'floor',
        'room_type',
        'capacity',
        'monthly_fee',
        'is_active',
    )


@admin.register(RoomAllocation)
class RoomAllocationAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'room',
        'allocated_date',
        'is_active',
    )


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):

    list_display = (
        'student',
        'amount',
        'month',
        'payment_date',
        'status',
    )


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'created_by',
        'created_at',
        'is_active',
    )