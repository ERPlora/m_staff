"""
Pydantic schemas for staff module.

Replaces Django forms — used for request validation and form rendering.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


# ============================================================================
# Staff Settings
# ============================================================================

class StaffSettingsUpdate(BaseModel):
    default_work_start: str | None = None
    default_work_end: str | None = None
    default_break_duration: int | None = Field(default=None, ge=0, le=480)
    min_advance_booking: int | None = Field(default=None, ge=0, le=168)
    max_daily_hours: int | None = Field(default=None, ge=1, le=24)
    overtime_threshold: int | None = Field(default=None, ge=1, le=168)
    show_staff_photos: bool | None = None
    show_staff_bio: bool | None = None
    allow_staff_selection: bool | None = None
    notify_new_appointment: bool | None = None
    notify_cancellation: bool | None = None


# ============================================================================
# Staff Role
# ============================================================================

class StaffRoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    color: str = Field(default="", max_length=7)
    order: int = 0
    is_active: bool = True


class StaffRoleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = None
    color: str | None = Field(default=None, max_length=7)
    order: int | None = None
    is_active: bool | None = None


# ============================================================================
# Staff Member
# ============================================================================

class StaffMemberCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: str = ""
    phone: str = ""
    employee_id: str = ""
    role_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    hire_date: date | None = None
    status: str = "active"
    bio: str = ""
    specialties: str = ""
    is_bookable: bool = True
    color: str = ""
    booking_buffer: int = 0
    hourly_rate: Decimal = Decimal("0.00")
    commission_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    order: int = 0
    notes: str = ""


class StaffMemberUpdate(BaseModel):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: str | None = None
    phone: str | None = None
    employee_id: str | None = None
    role_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    hire_date: date | None = None
    termination_date: date | None = None
    status: str | None = None
    bio: str | None = None
    specialties: str | None = None
    is_bookable: bool | None = None
    color: str | None = None
    booking_buffer: int | None = None
    hourly_rate: Decimal | None = None
    commission_rate: Decimal | None = Field(default=None, ge=0, le=100)
    order: int | None = None
    notes: str | None = None


# ============================================================================
# Staff Schedule
# ============================================================================

class StaffScheduleCreate(BaseModel):
    name: str = Field(default="Default Schedule", max_length=100)
    is_default: bool = True
    effective_from: date | None = None
    effective_until: date | None = None
    is_active: bool = True


class WorkingHoursInput(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: str = "09:00"
    end_time: str = "18:00"
    break_start: str | None = None
    break_end: str | None = None
    is_working: bool = True


# ============================================================================
# Staff Time Off
# ============================================================================

class StaffTimeOffCreate(BaseModel):
    leave_type: str = "vacation"
    start_date: date
    end_date: date
    is_full_day: bool = True
    start_time: str | None = None
    end_time: str | None = None
    reason: str = ""
    notes: str = ""


# ============================================================================
# Staff Service
# ============================================================================

class StaffServiceInput(BaseModel):
    service_id: uuid.UUID | None = None
    service_name: str
    custom_duration: int | None = None
    custom_price: Decimal | None = None
    is_primary: bool = False
    is_active: bool = True


class StaffServiceBulkSave(BaseModel):
    services: list[StaffServiceInput] = []
