"""
Test fixtures for the staff module.
"""

from __future__ import annotations

import uuid
from datetime import date, time
from decimal import Decimal

import pytest

from staff.models import (
    StaffMember,
    StaffRole,
    StaffSchedule,
    StaffService,
    StaffSettings,
    StaffTimeOff,
    StaffWorkingHours,
)


@pytest.fixture
def hub_id():
    """Test hub UUID."""
    return uuid.uuid4()


@pytest.fixture
def settings(hub_id):
    """Create default staff settings (not persisted)."""
    return StaffSettings(hub_id=hub_id)


@pytest.fixture
def role(hub_id):
    """Create a sample staff role (not persisted)."""
    return StaffRole(
        hub_id=hub_id,
        name="Stylist",
        description="Hair styling professional",
        color="#FF5733",
        order=1,
        is_active=True,
    )


@pytest.fixture
def inactive_role(hub_id):
    """Create an inactive staff role (not persisted)."""
    return StaffRole(
        hub_id=hub_id,
        name="Intern",
        description="Temporary position",
        color="#CCCCCC",
        order=99,
        is_active=False,
    )


@pytest.fixture
def member(hub_id, role):
    """Create a sample staff member (not persisted)."""
    return StaffMember(
        hub_id=hub_id,
        first_name="Ana",
        last_name="Martinez",
        email="ana@example.com",
        phone="612345678",
        employee_id="EMP-001",
        role_rel=role,
        hire_date=date(2024, 1, 15),
        status="active",
        bio="Senior stylist with 10 years of experience",
        specialties="Coloring, Highlights, Balayage",
        is_bookable=True,
        color="#3B82F6",
        booking_buffer=10,
        hourly_rate=Decimal("18.50"),
        commission_rate=Decimal("15.00"),
        order=1,
    )


@pytest.fixture
def inactive_member(hub_id):
    """Create an inactive staff member (not persisted)."""
    return StaffMember(
        hub_id=hub_id,
        first_name="Carlos",
        last_name="Lopez",
        email="carlos@example.com",
        status="inactive",
        is_bookable=False,
    )


@pytest.fixture
def on_leave_member(hub_id):
    """Create an on-leave staff member (not persisted)."""
    return StaffMember(
        hub_id=hub_id,
        first_name="Laura",
        last_name="Garcia",
        status="on_leave",
        is_bookable=True,
    )


@pytest.fixture
def terminated_member(hub_id):
    """Create a terminated staff member (not persisted)."""
    return StaffMember(
        hub_id=hub_id,
        first_name="Pedro",
        last_name="Sanchez",
        status="terminated",
        hire_date=date(2022, 6, 1),
        termination_date=date(2025, 3, 15),
    )


@pytest.fixture
def schedule(hub_id, member):
    """Create a default staff schedule (not persisted)."""
    return StaffSchedule(
        hub_id=hub_id,
        staff_id=member.id,
        name="Default Schedule",
        is_default=True,
        effective_from=date(2024, 1, 1),
        is_active=True,
    )


@pytest.fixture
def working_hours_monday(hub_id, schedule):
    """Create Monday working hours (not persisted)."""
    return StaffWorkingHours(
        hub_id=hub_id,
        schedule_id=schedule.id,
        day_of_week=0,
        start_time=time(9, 0),
        end_time=time(18, 0),
        break_start=time(13, 0),
        break_end=time(14, 0),
        is_working=True,
    )


@pytest.fixture
def working_hours_sunday(hub_id, schedule):
    """Create Sunday day-off working hours (not persisted)."""
    return StaffWorkingHours(
        hub_id=hub_id,
        schedule_id=schedule.id,
        day_of_week=6,
        start_time=time(0, 0),
        end_time=time(0, 0),
        is_working=False,
    )


@pytest.fixture
def time_off_pending(hub_id, member):
    """Create a pending vacation time-off request (not persisted)."""
    return StaffTimeOff(
        hub_id=hub_id,
        staff_id=member.id,
        leave_type="vacation",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 15),
        is_full_day=True,
        status="pending",
        reason="Summer holiday",
    )


@pytest.fixture
def time_off_approved(hub_id, member):
    """Create an approved sick leave request (not persisted)."""
    return StaffTimeOff(
        hub_id=hub_id,
        staff_id=member.id,
        leave_type="sick",
        start_date=date(2026, 3, 10),
        end_date=date(2026, 3, 12),
        is_full_day=True,
        status="approved",
        reason="Flu",
    )


@pytest.fixture
def staff_service(hub_id, member):
    """Create a staff service assignment (not persisted)."""
    return StaffService(
        hub_id=hub_id,
        staff_id=member.id,
        service_id=uuid.uuid4(),
        service_name="Haircut",
        custom_duration=45,
        custom_price=Decimal("25.00"),
        is_primary=True,
        is_active=True,
    )
