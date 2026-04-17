"""
Staff module models — SQLAlchemy 2.0.

Models: StaffSettings, StaffRole, StaffMember, StaffSchedule,
StaffWorkingHours, StaffTimeOff, StaffService.

Staff is the base HR module. It has no dependency on services — the
StaffService model uses a nullable service_id for optional integration.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from runtime.models.base import HubBaseModel

if TYPE_CHECKING:
    pass


# ============================================================================
# Staff Settings (singleton per hub)
# ============================================================================

class StaffSettings(HubBaseModel):
    """Per-hub staff configuration."""

    __tablename__ = "staff_settings"
    __table_args__ = (
        UniqueConstraint("hub_id", name="uq_staff_settings_hub"),
    )

    # Working hours defaults
    default_work_start: Mapped[time] = mapped_column(
        Time, default=time(9, 0), server_default="09:00:00",
    )
    default_work_end: Mapped[time] = mapped_column(
        Time, default=time(18, 0), server_default="18:00:00",
    )
    default_break_duration: Mapped[int] = mapped_column(
        Integer, default=60, server_default="60",
    )

    # Scheduling
    min_advance_booking: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1",
    )
    max_daily_hours: Mapped[int] = mapped_column(
        Integer, default=12, server_default="12",
    )
    overtime_threshold: Mapped[int] = mapped_column(
        Integer, default=40, server_default="40",
    )

    # Display
    show_staff_photos: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )
    show_staff_bio: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )
    allow_staff_selection: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )

    # Notifications
    notify_new_appointment: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )
    notify_cancellation: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )

    def __repr__(self) -> str:
        return f"<StaffSettings hub={self.hub_id}>"


# ============================================================================
# Staff Role
# ============================================================================

class StaffRole(HubBaseModel):
    """Staff roles for categorization."""

    __tablename__ = "staff_role"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(
        Text, default="", server_default="",
    )
    color: Mapped[str] = mapped_column(
        String(7), default="", server_default="",
    )
    order: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )

    # Relationships
    members: Mapped[list[StaffMember]] = relationship(
        "StaffMember", back_populates="role_rel", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<StaffRole {self.name!r}>"


# ============================================================================
# Staff Member
# ============================================================================

STAFF_STATUSES = ("active", "inactive", "on_leave", "terminated")

STATUS_LABELS = {
    "active": "Active",
    "inactive": "Inactive",
    "on_leave": "On Leave",
    "terminated": "Terminated",
}


class StaffMember(HubBaseModel):
    """Staff member profile."""

    __tablename__ = "staff_member"
    __table_args__ = (
        Index("ix_staff_hub_status", "hub_id", "status"),
        Index("ix_staff_hub_bookable", "hub_id", "is_bookable"),
    )

    # Basic info
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(254), default="", server_default="",
    )
    phone: Mapped[str] = mapped_column(
        String(20), default="", server_default="",
    )
    photo: Mapped[str] = mapped_column(
        String(500), default="", server_default="",
    )

    # Employment
    employee_id: Mapped[str] = mapped_column(
        String(50), default="", server_default="",
    )
    role_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("staff_role.id", ondelete="SET NULL"), nullable=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True,
    )
    hire_date: Mapped[date | None] = mapped_column(
        Date, nullable=True,
    )
    termination_date: Mapped[date | None] = mapped_column(
        Date, nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active", server_default="active",
    )

    # Bio
    bio: Mapped[str] = mapped_column(
        Text, default="", server_default="",
    )
    specialties: Mapped[str] = mapped_column(
        Text, default="", server_default="",
    )

    # Booking
    is_bookable: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )
    color: Mapped[str] = mapped_column(
        String(7), default="", server_default="",
    )
    booking_buffer: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0",
    )

    # Compensation
    hourly_rate: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), server_default="0.00",
    )
    commission_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00"), server_default="0.00",
    )

    # Display
    order: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0",
    )
    notes: Mapped[str] = mapped_column(
        Text, default="", server_default="",
    )

    # Relationships
    role_rel: Mapped[StaffRole | None] = relationship(
        "StaffRole", back_populates="members", lazy="joined",
    )
    schedules: Mapped[list[StaffSchedule]] = relationship(
        "StaffSchedule", back_populates="staff_rel",
        cascade="all, delete-orphan", lazy="selectin",
    )
    time_off: Mapped[list[StaffTimeOff]] = relationship(
        "StaffTimeOff", back_populates="staff_rel",
        cascade="all, delete-orphan", lazy="selectin",
    )
    staff_services: Mapped[list[StaffService]] = relationship(
        "StaffService", back_populates="staff_rel",
        cascade="all, delete-orphan", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<StaffMember {self.full_name!r}>"

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def status_label(self) -> str:
        return STATUS_LABELS.get(self.status, self.status)

    @property
    def is_available(self) -> bool:
        return self.status == "active" and self.is_bookable

    @property
    def years_of_service(self) -> int:
        if not self.hire_date:
            return 0
        end = self.termination_date or date.today()
        return (end - self.hire_date).days // 365

    def get_specialties_list(self) -> list[str]:
        if not self.specialties:
            return []
        return [s.strip() for s in self.specialties.split(",") if s.strip()]


# ============================================================================
# Staff Schedule
# ============================================================================

class StaffSchedule(HubBaseModel):
    """Weekly schedule template for a staff member."""

    __tablename__ = "staff_schedule"

    staff_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("staff_member.id", ondelete="CASCADE"), nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(100), default="Default Schedule", server_default="Default Schedule",
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )
    effective_from: Mapped[date | None] = mapped_column(
        Date, nullable=True,
    )
    effective_until: Mapped[date | None] = mapped_column(
        Date, nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )

    # Relationships
    staff_rel: Mapped[StaffMember] = relationship(
        "StaffMember", back_populates="schedules",
    )
    working_hours: Mapped[list[StaffWorkingHours]] = relationship(
        "StaffWorkingHours", back_populates="schedule_rel",
        cascade="all, delete-orphan", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<StaffSchedule {self.name!r}>"

    def is_applicable_on(self, target_date: date) -> bool:
        if not self.is_active:
            return False
        if self.effective_from and target_date < self.effective_from:
            return False
        return not (self.effective_until and target_date > self.effective_until)


# ============================================================================
# Staff Working Hours
# ============================================================================

DAY_NAMES = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}


class StaffWorkingHours(HubBaseModel):
    """Working hours for a specific day of week within a schedule."""

    __tablename__ = "staff_working_hours"
    __table_args__ = (
        UniqueConstraint("schedule_id", "day_of_week", name="uq_staff_working_hours_schedule_day"),
    )

    schedule_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("staff_schedule.id", ondelete="CASCADE"), nullable=False,
    )
    day_of_week: Mapped[int] = mapped_column(
        SmallInteger, nullable=False,
    )
    start_time: Mapped[time] = mapped_column(
        Time, nullable=False,
    )
    end_time: Mapped[time] = mapped_column(
        Time, nullable=False,
    )
    break_start: Mapped[time | None] = mapped_column(
        Time, nullable=True,
    )
    break_end: Mapped[time | None] = mapped_column(
        Time, nullable=True,
    )
    is_working: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )

    # Relationships
    schedule_rel: Mapped[StaffSchedule] = relationship(
        "StaffSchedule", back_populates="working_hours",
    )

    def __repr__(self) -> str:
        day_name = DAY_NAMES.get(self.day_of_week, "?")
        if not self.is_working:
            return f"<WorkingHours {day_name}: Day Off>"
        return f"<WorkingHours {day_name}: {self.start_time}-{self.end_time}>"

    @property
    def day_name(self) -> str:
        return DAY_NAMES.get(self.day_of_week, "Unknown")

    @property
    def working_minutes(self) -> int:
        if not self.is_working:
            return 0
        start = datetime.combine(date.today(), self.start_time)
        end = datetime.combine(date.today(), self.end_time)
        total = int((end - start).total_seconds()) // 60
        if self.break_start and self.break_end:
            b_start = datetime.combine(date.today(), self.break_start)
            b_end = datetime.combine(date.today(), self.break_end)
            total -= int((b_end - b_start).total_seconds()) // 60
        return total


# ============================================================================
# Staff Time Off
# ============================================================================

LEAVE_TYPES = ("vacation", "sick", "personal", "training", "other")
TIME_OFF_STATUSES = ("pending", "approved", "rejected", "cancelled")

LEAVE_TYPE_LABELS = {
    "vacation": "Vacation",
    "sick": "Sick Leave",
    "personal": "Personal Leave",
    "training": "Training",
    "other": "Other",
}

TIME_OFF_STATUS_LABELS = {
    "pending": "Pending",
    "approved": "Approved",
    "rejected": "Rejected",
    "cancelled": "Cancelled",
}


class StaffTimeOff(HubBaseModel):
    """Time off / vacation / leave for staff."""

    __tablename__ = "staff_time_off"
    __table_args__ = (
        Index("ix_staff_time_off_hub_staff", "hub_id", "staff_id"),
        Index("ix_staff_time_off_hub_status", "hub_id", "status"),
    )

    staff_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("staff_member.id", ondelete="CASCADE"), nullable=False,
    )
    leave_type: Mapped[str] = mapped_column(
        String(20), default="vacation", server_default="vacation",
    )
    start_date: Mapped[date] = mapped_column(
        Date, nullable=False,
    )
    end_date: Mapped[date] = mapped_column(
        Date, nullable=False,
    )
    is_full_day: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )
    start_time: Mapped[time | None] = mapped_column(
        Time, nullable=True,
    )
    end_time: Mapped[time | None] = mapped_column(
        Time, nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending",
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True,
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    reason: Mapped[str] = mapped_column(
        Text, default="", server_default="",
    )
    notes: Mapped[str] = mapped_column(
        Text, default="", server_default="",
    )

    # Relationships
    staff_rel: Mapped[StaffMember] = relationship(
        "StaffMember", back_populates="time_off",
    )

    def __repr__(self) -> str:
        return f"<StaffTimeOff {self.leave_type} {self.start_date}-{self.end_date}>"

    @property
    def leave_type_label(self) -> str:
        return LEAVE_TYPE_LABELS.get(self.leave_type, self.leave_type)

    @property
    def status_label(self) -> str:
        return TIME_OFF_STATUS_LABELS.get(self.status, self.status)

    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days + 1

    def conflicts_with(self, start_date: date, end_date: date) -> bool:
        if self.status not in ("pending", "approved"):
            return False
        return not (end_date < self.start_date or start_date > self.end_date)


# ============================================================================
# Staff Service (optional integration with services module)
# ============================================================================

class StaffService(HubBaseModel):
    """Services that a staff member can provide."""

    __tablename__ = "staff_service"
    __table_args__ = (
        UniqueConstraint("staff_id", "service_id", name="uq_staff_service_staff_service"),
    )

    staff_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("staff_member.id", ondelete="CASCADE"), nullable=False,
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, nullable=True,
    )
    service_name: Mapped[str] = mapped_column(
        String(200), nullable=False,
    )
    custom_duration: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
    )
    custom_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true",
    )

    # Relationships
    staff_rel: Mapped[StaffMember] = relationship(
        "StaffMember", back_populates="staff_services",
    )

    def __repr__(self) -> str:
        return f"<StaffService {self.service_name!r}>"
