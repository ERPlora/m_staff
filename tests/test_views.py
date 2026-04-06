"""
Tests for staff module routes (views).

Covers model properties, schema validation, and route definitions.
"""

from __future__ import annotations

import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from pydantic import ValidationError

from staff.models import (
    DAY_NAMES,
    LEAVE_TYPE_LABELS,
    LEAVE_TYPES,
    STAFF_STATUSES,
    STATUS_LABELS,
    TIME_OFF_STATUS_LABELS,
    TIME_OFF_STATUSES,
    StaffMember,
    StaffSchedule,
    StaffTimeOff,
    StaffWorkingHours,
)
from staff.schemas import (
    StaffMemberCreate,
    StaffMemberUpdate,
    StaffRoleCreate,
    StaffRoleUpdate,
    StaffScheduleCreate,
    StaffServiceBulkSave,
    StaffServiceInput,
    StaffSettingsUpdate,
    StaffTimeOffCreate,
    WorkingHoursInput,
)


# ============================================================================
# Route definitions
# ============================================================================


class TestRouteDefinitions:
    """Verify route module imports correctly and has expected endpoints."""

    def test_router_has_htmx_routes(self):
        """Router should expose all expected HTMX page routes."""
        from staff.routes import router

        route_paths = [r.path for r in router.routes]

        assert "/" in route_paths
        assert "/staff" in route_paths
        assert "/staff/create" in route_paths
        assert "/staff/{member_id}" in route_paths
        assert "/staff/{member_id}/edit" in route_paths
        assert "/schedules" in route_paths
        assert "/roles" in route_paths
        assert "/settings" in route_paths

    def test_router_has_crud_routes(self):
        """Router should expose all CRUD POST routes."""
        from staff.routes import router

        route_paths = [r.path for r in router.routes]

        assert "/staff/{member_id}/delete" in route_paths
        assert "/roles/create" in route_paths
        assert "/roles/{role_id}/edit" in route_paths
        assert "/roles/{role_id}/delete" in route_paths
        assert "/settings/save" in route_paths

    def test_router_has_time_off_routes(self):
        """Router should expose time-off management routes."""
        from staff.routes import router

        route_paths = [r.path for r in router.routes]

        assert "/staff/{member_id}/time-off" in route_paths
        assert "/staff/{member_id}/time-off/create" in route_paths
        assert "/staff/{member_id}/time-off/{to_id}/approve" in route_paths
        assert "/staff/{member_id}/time-off/{to_id}/reject" in route_paths

    def test_router_has_api_routes(self):
        """Router should expose JSON API endpoints."""
        from staff.routes import router

        route_paths = [r.path for r in router.routes]

        assert "/api/search" in route_paths
        assert "/api/available" in route_paths

    def test_router_has_service_routes(self):
        """Router should expose staff service assignment routes."""
        from staff.routes import router

        route_paths = [r.path for r in router.routes]

        assert "/staff/{member_id}/services" in route_paths
        assert "/staff/{member_id}/services/save" in route_paths

    def test_router_has_schedule_routes(self):
        """Router should expose schedule management routes."""
        from staff.routes import router

        route_paths = [r.path for r in router.routes]

        assert "/staff/{member_id}/schedules" in route_paths
        assert "/staff/{member_id}/schedules/create" in route_paths


# ============================================================================
# StaffMember model properties
# ============================================================================


class TestStaffMemberProperties:
    """Tests for StaffMember computed properties."""

    def test_full_name(self, member):
        """full_name should concatenate first and last name."""
        assert member.full_name == "Ana Martinez"

    def test_full_name_only_first(self, hub_id):
        """full_name should handle empty last name gracefully."""
        m = StaffMember(hub_id=hub_id, first_name="Solo", last_name="")
        assert m.full_name == "Solo"

    def test_status_label_active(self, member):
        """status_label should return human-readable label for active."""
        assert member.status_label == "Active"

    def test_status_label_all_statuses(self, hub_id):
        """Every known status should have a human-readable label."""
        for status in STAFF_STATUSES:
            m = StaffMember(hub_id=hub_id, first_name="X", last_name="Y", status=status)
            assert m.status_label == STATUS_LABELS[status]

    def test_status_label_unknown_fallback(self, hub_id):
        """Unknown status should fall back to the raw status string."""
        m = StaffMember(hub_id=hub_id, first_name="X", last_name="Y", status="mystery")
        assert m.status_label == "mystery"

    def test_is_available_active_bookable(self, member):
        """Active and bookable member should be available."""
        assert member.is_available is True

    def test_is_available_active_not_bookable(self, hub_id):
        """Active but not bookable member should not be available."""
        m = StaffMember(
            hub_id=hub_id, first_name="A", last_name="B",
            status="active", is_bookable=False,
        )
        assert m.is_available is False

    def test_is_available_inactive(self, inactive_member):
        """Inactive member should not be available."""
        assert inactive_member.is_available is False

    def test_is_available_on_leave(self, on_leave_member):
        """On-leave member should not be available even if bookable."""
        assert on_leave_member.is_available is False

    def test_years_of_service_with_dates(self, member):
        """years_of_service should compute from hire_date to today."""
        # member hire_date is 2024-01-15, today is 2026-04-06 => ~2 years
        yos = member.years_of_service
        assert yos >= 2

    def test_years_of_service_no_hire_date(self, hub_id):
        """years_of_service should return 0 when no hire date."""
        m = StaffMember(hub_id=hub_id, first_name="X", last_name="Y")
        assert m.years_of_service == 0

    def test_years_of_service_terminated(self, terminated_member):
        """years_of_service should use termination_date when available."""
        # 2022-06-01 to 2025-03-15 => ~2 years
        yos = terminated_member.years_of_service
        assert yos == 2

    def test_get_specialties_list(self, member):
        """get_specialties_list should split comma-separated specialties."""
        specs = member.get_specialties_list()
        assert specs == ["Coloring", "Highlights", "Balayage"]

    def test_get_specialties_list_empty(self, hub_id):
        """get_specialties_list should return empty list when no specialties."""
        m = StaffMember(hub_id=hub_id, first_name="X", last_name="Y", specialties="")
        assert m.get_specialties_list() == []

    def test_get_specialties_list_whitespace(self, hub_id):
        """get_specialties_list should strip whitespace and skip blanks."""
        m = StaffMember(
            hub_id=hub_id, first_name="X", last_name="Y",
            specialties="  Cut , , Color  ",
        )
        assert m.get_specialties_list() == ["Cut", "Color"]

    def test_repr(self, member):
        """repr should include the full name."""
        assert "Ana Martinez" in repr(member)


# ============================================================================
# StaffRole model
# ============================================================================


class TestStaffRole:
    """Tests for StaffRole model."""

    def test_repr(self, role):
        """repr should include the role name."""
        assert "Stylist" in repr(role)

    def test_active_role(self, role):
        """Active role should have is_active=True."""
        assert role.is_active is True

    def test_inactive_role(self, inactive_role):
        """Inactive role should have is_active=False."""
        assert inactive_role.is_active is False


# ============================================================================
# StaffSchedule model
# ============================================================================


class TestStaffSchedule:
    """Tests for StaffSchedule model."""

    def test_repr(self, schedule):
        """repr should include the schedule name."""
        assert "Default Schedule" in repr(schedule)

    def test_is_applicable_on_active(self, schedule):
        """Active schedule within effective range should be applicable."""
        assert schedule.is_applicable_on(date(2026, 6, 15)) is True

    def test_is_applicable_on_inactive(self, hub_id, member):
        """Inactive schedule should not be applicable."""
        s = StaffSchedule(
            hub_id=hub_id, staff_id=member.id,
            name="Old", is_active=False,
        )
        assert s.is_applicable_on(date(2026, 6, 15)) is False

    def test_is_applicable_before_effective_from(self, schedule):
        """Date before effective_from should not be applicable."""
        assert schedule.is_applicable_on(date(2023, 12, 31)) is False

    def test_is_applicable_after_effective_until(self, hub_id, member):
        """Date after effective_until should not be applicable."""
        s = StaffSchedule(
            hub_id=hub_id, staff_id=member.id,
            name="Temp", is_active=True,
            effective_from=date(2026, 1, 1),
            effective_until=date(2026, 3, 31),
        )
        assert s.is_applicable_on(date(2026, 4, 1)) is False
        assert s.is_applicable_on(date(2026, 3, 31)) is True

    def test_is_applicable_no_bounds(self, hub_id, member):
        """Schedule with no effective dates should always be applicable if active."""
        s = StaffSchedule(
            hub_id=hub_id, staff_id=member.id,
            name="Open", is_active=True,
        )
        assert s.is_applicable_on(date(2020, 1, 1)) is True
        assert s.is_applicable_on(date(2030, 12, 31)) is True


# ============================================================================
# StaffWorkingHours model
# ============================================================================


class TestStaffWorkingHours:
    """Tests for StaffWorkingHours computed properties."""

    def test_day_name(self, working_hours_monday):
        """day_name should return 'Monday' for day_of_week=0."""
        assert working_hours_monday.day_name == "Monday"

    def test_day_name_all_days(self, hub_id, schedule):
        """All 7 days should have a valid day name."""
        for dow in range(7):
            wh = StaffWorkingHours(
                hub_id=hub_id, schedule_id=schedule.id,
                day_of_week=dow,
                start_time=time(9, 0), end_time=time(18, 0),
                is_working=True,
            )
            assert wh.day_name == DAY_NAMES[dow]

    def test_working_minutes_standard_day(self, working_hours_monday):
        """Working minutes should be total time minus break time."""
        # 9:00-18:00 = 540 min, break 13:00-14:00 = 60 min => 480 min
        assert working_hours_monday.working_minutes == 480

    def test_working_minutes_no_break(self, hub_id, schedule):
        """Working minutes without break should be full span."""
        wh = StaffWorkingHours(
            hub_id=hub_id, schedule_id=schedule.id,
            day_of_week=2,
            start_time=time(10, 0), end_time=time(14, 0),
            is_working=True,
        )
        assert wh.working_minutes == 240

    def test_working_minutes_day_off(self, working_hours_sunday):
        """Day off should have 0 working minutes."""
        assert working_hours_sunday.working_minutes == 0

    def test_repr_working_day(self, working_hours_monday):
        """repr should show day name and time range for working day."""
        r = repr(working_hours_monday)
        assert "Monday" in r
        assert "09:00" in r

    def test_repr_day_off(self, working_hours_sunday):
        """repr should show 'Day Off' for non-working day."""
        assert "Day Off" in repr(working_hours_sunday)


# ============================================================================
# StaffTimeOff model
# ============================================================================


class TestStaffTimeOff:
    """Tests for StaffTimeOff computed properties."""

    def test_leave_type_label(self, time_off_pending):
        """leave_type_label should return human-readable label."""
        assert time_off_pending.leave_type_label == "Vacation"

    def test_all_leave_types_have_labels(self):
        """Every leave type should have a display label."""
        for lt in LEAVE_TYPES:
            assert lt in LEAVE_TYPE_LABELS

    def test_status_label(self, time_off_pending):
        """status_label should return human-readable status."""
        assert time_off_pending.status_label == "Pending"

    def test_all_time_off_statuses_have_labels(self):
        """Every time-off status should have a display label."""
        for st in TIME_OFF_STATUSES:
            assert st in TIME_OFF_STATUS_LABELS

    def test_duration_days(self, time_off_pending):
        """duration_days should count inclusive days."""
        # July 1 to July 15 = 15 days
        assert time_off_pending.duration_days == 15

    def test_duration_days_single_day(self, hub_id, member):
        """Single-day time off should have duration_days=1."""
        to = StaffTimeOff(
            hub_id=hub_id, staff_id=member.id,
            start_date=date(2026, 5, 1), end_date=date(2026, 5, 1),
            status="pending",
        )
        assert to.duration_days == 1

    def test_conflicts_with_overlapping(self, time_off_pending):
        """Pending time off should conflict with overlapping dates."""
        assert time_off_pending.conflicts_with(date(2026, 7, 5), date(2026, 7, 10)) is True

    def test_conflicts_with_touching_start(self, time_off_pending):
        """Time off should conflict when ranges share the start boundary."""
        assert time_off_pending.conflicts_with(date(2026, 6, 25), date(2026, 7, 1)) is True

    def test_conflicts_with_touching_end(self, time_off_pending):
        """Time off should conflict when ranges share the end boundary."""
        assert time_off_pending.conflicts_with(date(2026, 7, 15), date(2026, 7, 20)) is True

    def test_no_conflict_before(self, time_off_pending):
        """Dates entirely before time off should not conflict."""
        assert time_off_pending.conflicts_with(date(2026, 6, 1), date(2026, 6, 30)) is False

    def test_no_conflict_after(self, time_off_pending):
        """Dates entirely after time off should not conflict."""
        assert time_off_pending.conflicts_with(date(2026, 7, 16), date(2026, 7, 31)) is False

    def test_no_conflict_cancelled(self, hub_id, member):
        """Cancelled time off should not conflict with any dates."""
        to = StaffTimeOff(
            hub_id=hub_id, staff_id=member.id,
            start_date=date(2026, 8, 1), end_date=date(2026, 8, 10),
            status="cancelled",
        )
        assert to.conflicts_with(date(2026, 8, 5), date(2026, 8, 6)) is False

    def test_no_conflict_rejected(self, hub_id, member):
        """Rejected time off should not conflict with any dates."""
        to = StaffTimeOff(
            hub_id=hub_id, staff_id=member.id,
            start_date=date(2026, 8, 1), end_date=date(2026, 8, 10),
            status="rejected",
        )
        assert to.conflicts_with(date(2026, 8, 5), date(2026, 8, 6)) is False

    def test_conflict_approved(self, time_off_approved):
        """Approved time off should still conflict."""
        assert time_off_approved.conflicts_with(date(2026, 3, 11), date(2026, 3, 11)) is True

    def test_repr(self, time_off_pending):
        """repr should include leave type and date range."""
        r = repr(time_off_pending)
        assert "vacation" in r
        assert "2026-07-01" in r


# ============================================================================
# StaffService model
# ============================================================================


class TestStaffService:
    """Tests for StaffService model."""

    def test_repr(self, staff_service):
        """repr should include the service name."""
        assert "Haircut" in repr(staff_service)

    def test_custom_price(self, staff_service):
        """Custom price should be set correctly."""
        assert staff_service.custom_price == Decimal("25.00")

    def test_is_primary(self, staff_service):
        """Primary flag should be set correctly."""
        assert staff_service.is_primary is True


# ============================================================================
# StaffSettings model
# ============================================================================


class TestStaffSettings:
    """Tests for StaffSettings model."""

    def test_repr(self, settings):
        """repr should include hub_id."""
        assert "hub=" in repr(settings)


# ============================================================================
# Schema validation — StaffMemberCreate
# ============================================================================


class TestStaffMemberCreateSchema:
    """Tests for StaffMemberCreate Pydantic schema validation."""

    def test_valid_minimal(self):
        """Schema should accept minimal required fields."""
        data = StaffMemberCreate(first_name="Ana", last_name="Lopez")
        assert data.first_name == "Ana"
        assert data.status == "active"
        assert data.is_bookable is True

    def test_valid_full(self):
        """Schema should accept all optional fields."""
        data = StaffMemberCreate(
            first_name="Ana",
            last_name="Lopez",
            email="ana@example.com",
            phone="612345678",
            employee_id="EMP-002",
            role_id=uuid.uuid4(),
            hire_date=date(2024, 6, 1),
            status="active",
            bio="Experienced stylist",
            specialties="Coloring",
            is_bookable=True,
            color="#FF0000",
            booking_buffer=15,
            hourly_rate=Decimal("20.00"),
            commission_rate=Decimal("10.00"),
            order=5,
            notes="Senior staff",
        )
        assert data.commission_rate == Decimal("10.00")

    def test_missing_first_name(self):
        """Schema should reject missing first_name."""
        with pytest.raises(ValidationError):
            StaffMemberCreate(last_name="Lopez")

    def test_missing_last_name(self):
        """Schema should reject missing last_name."""
        with pytest.raises(ValidationError):
            StaffMemberCreate(first_name="Ana")

    def test_empty_first_name(self):
        """Schema should reject empty first_name (min_length=1)."""
        with pytest.raises(ValidationError):
            StaffMemberCreate(first_name="", last_name="Lopez")

    def test_commission_rate_bounds(self):
        """Commission rate must be between 0 and 100."""
        with pytest.raises(ValidationError):
            StaffMemberCreate(first_name="A", last_name="B", commission_rate=Decimal("101"))

    def test_commission_rate_negative(self):
        """Negative commission rate should be rejected."""
        with pytest.raises(ValidationError):
            StaffMemberCreate(first_name="A", last_name="B", commission_rate=Decimal("-1"))

    def test_defaults(self):
        """Default values should be set correctly."""
        data = StaffMemberCreate(first_name="A", last_name="B")
        assert data.email == ""
        assert data.phone == ""
        assert data.role_id is None
        assert data.hourly_rate == Decimal("0.00")
        assert data.booking_buffer == 0
        assert data.order == 0


# ============================================================================
# Schema validation — StaffMemberUpdate
# ============================================================================


class TestStaffMemberUpdateSchema:
    """Tests for StaffMemberUpdate Pydantic schema validation."""

    def test_partial_update(self):
        """Schema should accept partial fields for update."""
        data = StaffMemberUpdate(first_name="New Name")
        dump = data.model_dump(exclude_unset=True)
        assert dump == {"first_name": "New Name"}

    def test_empty_update(self):
        """Schema should allow empty body (no fields to update)."""
        data = StaffMemberUpdate()
        assert data.model_dump(exclude_unset=True) == {}

    def test_update_commission_rate_bounds(self):
        """Update should also enforce commission rate bounds."""
        with pytest.raises(ValidationError):
            StaffMemberUpdate(commission_rate=Decimal("200"))


# ============================================================================
# Schema validation — StaffRoleCreate / StaffRoleUpdate
# ============================================================================


class TestStaffRoleSchemas:
    """Tests for StaffRole Pydantic schemas."""

    def test_role_create_valid(self):
        """RoleCreate should accept valid data."""
        data = StaffRoleCreate(name="Manager", color="#00FF00")
        assert data.name == "Manager"
        assert data.is_active is True

    def test_role_create_empty_name(self):
        """RoleCreate should reject empty name."""
        with pytest.raises(ValidationError):
            StaffRoleCreate(name="")

    def test_role_update_partial(self):
        """RoleUpdate should accept partial fields."""
        data = StaffRoleUpdate(name="New Name")
        dump = data.model_dump(exclude_unset=True)
        assert dump == {"name": "New Name"}


# ============================================================================
# Schema validation — StaffScheduleCreate / WorkingHoursInput
# ============================================================================


class TestScheduleSchemas:
    """Tests for schedule-related Pydantic schemas."""

    def test_schedule_create_defaults(self):
        """ScheduleCreate should have sensible defaults."""
        data = StaffScheduleCreate()
        assert data.name == "Default Schedule"
        assert data.is_default is True
        assert data.is_active is True

    def test_working_hours_valid(self):
        """WorkingHoursInput should accept valid day and times."""
        wh = WorkingHoursInput(
            day_of_week=0, start_time="09:00", end_time="18:00",
            break_start="13:00", break_end="14:00", is_working=True,
        )
        assert wh.day_of_week == 0

    def test_working_hours_day_bounds(self):
        """day_of_week must be 0-6."""
        with pytest.raises(ValidationError):
            WorkingHoursInput(day_of_week=7)
        with pytest.raises(ValidationError):
            WorkingHoursInput(day_of_week=-1)

    def test_working_hours_defaults(self):
        """WorkingHoursInput should have sensible defaults."""
        wh = WorkingHoursInput(day_of_week=3)
        assert wh.start_time == "09:00"
        assert wh.end_time == "18:00"
        assert wh.is_working is True


# ============================================================================
# Schema validation — StaffTimeOffCreate
# ============================================================================


class TestTimeOffCreateSchema:
    """Tests for StaffTimeOffCreate Pydantic schema."""

    def test_valid(self):
        """TimeOffCreate should accept valid dates."""
        data = StaffTimeOffCreate(
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 5),
            leave_type="vacation",
            reason="Summer break",
        )
        assert data.is_full_day is True

    def test_missing_dates(self):
        """TimeOffCreate should reject missing required dates."""
        with pytest.raises(ValidationError):
            StaffTimeOffCreate(leave_type="vacation")

    def test_defaults(self):
        """TimeOffCreate should have sensible defaults."""
        data = StaffTimeOffCreate(
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 1),
        )
        assert data.leave_type == "vacation"
        assert data.is_full_day is True
        assert data.reason == ""
        assert data.notes == ""

    def test_partial_day(self):
        """TimeOffCreate should accept partial day with times."""
        data = StaffTimeOffCreate(
            start_date=date(2026, 8, 1),
            end_date=date(2026, 8, 1),
            is_full_day=False,
            start_time="09:00",
            end_time="13:00",
        )
        assert data.is_full_day is False
        assert data.start_time == "09:00"


# ============================================================================
# Schema validation — StaffSettingsUpdate
# ============================================================================


class TestStaffSettingsUpdateSchema:
    """Tests for StaffSettingsUpdate Pydantic schema."""

    def test_partial_update(self):
        """SettingsUpdate should accept partial fields."""
        data = StaffSettingsUpdate(max_daily_hours=10)
        dump = data.model_dump(exclude_unset=True)
        assert dump == {"max_daily_hours": 10}

    def test_break_duration_bounds(self):
        """Break duration must be 0-480."""
        with pytest.raises(ValidationError):
            StaffSettingsUpdate(default_break_duration=500)

    def test_max_daily_hours_bounds(self):
        """Max daily hours must be 1-24."""
        with pytest.raises(ValidationError):
            StaffSettingsUpdate(max_daily_hours=25)
        with pytest.raises(ValidationError):
            StaffSettingsUpdate(max_daily_hours=0)

    def test_overtime_threshold_bounds(self):
        """Overtime threshold must be 1-168."""
        with pytest.raises(ValidationError):
            StaffSettingsUpdate(overtime_threshold=200)

    def test_min_advance_booking_bounds(self):
        """Min advance booking must be 0-168."""
        with pytest.raises(ValidationError):
            StaffSettingsUpdate(min_advance_booking=200)


# ============================================================================
# Schema validation — StaffServiceBulkSave
# ============================================================================


class TestStaffServiceBulkSaveSchema:
    """Tests for StaffServiceBulkSave Pydantic schema."""

    def test_empty_services(self):
        """BulkSave should accept empty services list."""
        data = StaffServiceBulkSave(services=[])
        assert data.services == []

    def test_with_services(self):
        """BulkSave should accept a list of service inputs."""
        sid = uuid.uuid4()
        data = StaffServiceBulkSave(services=[
            StaffServiceInput(
                service_id=sid,
                service_name="Haircut",
                custom_duration=45,
                custom_price=Decimal("25.00"),
                is_primary=True,
            ),
            StaffServiceInput(
                service_name="Coloring",
                is_primary=False,
            ),
        ])
        assert len(data.services) == 2
        assert data.services[0].service_id == sid
        assert data.services[1].service_id is None

    def test_service_input_defaults(self):
        """ServiceInput should have sensible defaults."""
        data = StaffServiceInput(service_name="Trim")
        assert data.service_id is None
        assert data.custom_duration is None
        assert data.custom_price is None
        assert data.is_primary is False
        assert data.is_active is True


# ============================================================================
# Module manifest
# ============================================================================


class TestModuleManifest:
    """Tests for staff module.py manifest constants."""

    def test_module_id(self):
        """Module ID should be 'staff'."""
        from staff.module import MODULE_ID
        assert MODULE_ID == "staff"

    def test_module_has_models(self):
        """Module should declare HAS_MODELS=True."""
        from staff.module import HAS_MODELS
        assert HAS_MODELS is True

    def test_module_no_dependencies(self):
        """Staff module should have no dependencies."""
        from staff.module import DEPENDENCIES
        assert DEPENDENCIES == []

    def test_navigation_tabs(self):
        """Module should declare expected navigation tabs."""
        from staff.module import NAVIGATION
        tab_ids = [tab["id"] for tab in NAVIGATION]
        assert "dashboard" in tab_ids
        assert "staff" in tab_ids
        assert "schedules" in tab_ids
        assert "roles" in tab_ids
        assert "settings" in tab_ids

    def test_permissions_defined(self):
        """Module should declare permissions for RBAC."""
        from staff.module import PERMISSIONS
        perm_codes = [p[0] for p in PERMISSIONS]
        assert "view_staff_member" in perm_codes
        assert "add_staff_member" in perm_codes
        assert "change_staff_member" in perm_codes
        assert "delete_staff_member" in perm_codes
        assert "manage_time_off" in perm_codes

    def test_role_permissions(self):
        """Admin should have wildcard, employee should have limited perms."""
        from staff.module import ROLE_PERMISSIONS
        assert ROLE_PERMISSIONS["admin"] == ["*"]
        assert "view_staff_member" in ROLE_PERMISSIONS["employee"]
        assert "delete_staff_member" not in ROLE_PERMISSIONS["employee"]

    def test_menu_entry(self):
        """Module should declare a sidebar menu entry."""
        from staff.module import MENU
        assert MENU["label"] == "Staff"
        assert "icon" in MENU
