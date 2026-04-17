"""
Staff module HTMX views — FastAPI router.

Replaces Django views.py + urls.py. Uses @htmx_view decorator.
Mounted at /m/staff/ by ModuleRuntime.
"""

from __future__ import annotations

import uuid
from datetime import datetime, time, UTC

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import or_

from runtime.models.queryset import HubQuery
from runtime.orm.transactions import atomic
from runtime.auth.current_user import CurrentUser, DbSession, HubId
from runtime.views.responses import htmx_view

from .models import (
    StaffMember,
    StaffRole,
    StaffSchedule,
    StaffService,
    StaffSettings,
    StaffTimeOff,
    StaffWorkingHours,
)
from .schemas import (
    StaffMemberCreate,
    StaffMemberUpdate,
    StaffRoleCreate,
    StaffRoleUpdate,
    StaffScheduleCreate,
    StaffServiceBulkSave,
    StaffSettingsUpdate,
    StaffTimeOffCreate,
    WorkingHoursInput,
)

router = APIRouter()


def _q(model, db, hub_id):
    return HubQuery(model, db, hub_id)


# ============================================================================
# Dashboard
# ============================================================================

@router.get("/")
@htmx_view(module_id="staff", view_id="dashboard", permissions="staff.view_staff_member")
async def dashboard(request: Request, db: DbSession, user: CurrentUser, hub_id: HubId):
    """Staff dashboard with KPIs."""
    total_staff = await _q(StaffMember, db, hub_id).count()

    active_staff = await _q(StaffMember, db, hub_id).filter(
        StaffMember.status == "active"
    ).count()

    on_leave = await _q(StaffMember, db, hub_id).filter(
        StaffMember.status == "on_leave"
    ).count()

    pending_time_off = await _q(StaffTimeOff, db, hub_id).filter(
        StaffTimeOff.status == "pending"
    ).count()

    # Recent staff members
    recent_staff = await (
        _q(StaffMember, db, hub_id)
        .order_by(StaffMember.created_at.desc())
        .limit(5)
        .all()
    )

    # Roles summary
    roles = await _q(StaffRole, db, hub_id).filter(
        StaffRole.is_active == True  # noqa: E712
    ).order_by(StaffRole.order).all()

    return {
        "total_staff": total_staff,
        "active_staff": active_staff,
        "on_leave": on_leave,
        "pending_time_off": pending_time_off,
        "recent_staff": recent_staff,
        "roles": roles,
    }


# ============================================================================
# Staff List
# ============================================================================

@router.get("/staff")
@htmx_view(module_id="staff", view_id="staff_list", permissions="staff.view_staff_member")
async def staff_list(
    request: Request, db: DbSession, user: CurrentUser, hub_id: HubId,
    search: str = "", status: str = "", role_id: str = "",
    page: int = 1, per_page: int = 25,
):
    """Staff list with search and filters."""
    query = _q(StaffMember, db, hub_id)

    if search:
        query = query.filter(or_(
            StaffMember.first_name.ilike(f"%{search}%"),
            StaffMember.last_name.ilike(f"%{search}%"),
            StaffMember.email.ilike(f"%{search}%"),
            StaffMember.phone.ilike(f"%{search}%"),
        ))

    if status:
        query = query.filter(StaffMember.status == status)

    if role_id:
        query = query.filter(StaffMember.role_id == uuid.UUID(role_id))

    query = query.order_by(StaffMember.order, StaffMember.first_name)

    total = await query.count()
    staff = await query.offset((page - 1) * per_page).limit(per_page).all()

    roles = await _q(StaffRole, db, hub_id).filter(
        StaffRole.is_active == True  # noqa: E712
    ).order_by(StaffRole.order).all()

    hx_target = request.headers.get("HX-Target", "")
    if hx_target == "staff-list-container":
        return {
            "_template": "staff/partials/staff_list_content.html",
            "staff": staff,
            "roles": roles,
            "total": total,
            "page": page,
            "per_page": per_page,
            "has_next": (page * per_page) < total,
            "has_prev": page > 1,
            "search": search,
            "status_filter": status,
            "role_filter": role_id,
        }

    return {
        "staff": staff,
        "roles": roles,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_next": (page * per_page) < total,
        "has_prev": page > 1,
        "search": search,
        "status_filter": status,
        "role_filter": role_id,
    }


# ============================================================================
# Staff Create
# ============================================================================

@router.get("/staff/create")
@htmx_view(module_id="staff", view_id="staff_list")
async def staff_form_new(request: Request, db: DbSession, user: CurrentUser, hub_id: HubId):
    """Staff create form."""
    roles = await _q(StaffRole, db, hub_id).filter(
        StaffRole.is_active == True  # noqa: E712
    ).order_by(StaffRole.order).all()

    return {
        "_template": "staff/pages/staff_form.html",
        "_partial": "staff/partials/staff_form_content.html",
        "member": None,
        "roles": roles,
    }


@router.post("/staff/create")
async def staff_create(
    request: Request, db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Create a staff member."""
    try:
        body = await request.json()
        data = StaffMemberCreate(**body)

        async with atomic(db) as session:
            member = StaffMember(
                hub_id=hub_id,
                **data.model_dump(exclude_unset=True),
            )
            session.add(member)
            await session.flush()

        return JSONResponse({"success": True, "id": str(member.id)})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


# ============================================================================
# Staff Detail
# ============================================================================

@router.get("/staff/{member_id}")
@htmx_view(module_id="staff", view_id="staff_list")
async def staff_detail(
    request: Request, member_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Staff member detail view."""
    member = await _q(StaffMember, db, hub_id).get(member_id)
    if member is None:
        return JSONResponse({"error": "Staff member not found"}, status_code=404)

    # Pending time off for this member
    pending_time_off = await _q(StaffTimeOff, db, hub_id).filter(
        StaffTimeOff.staff_id == member_id,
        StaffTimeOff.status == "pending",
    ).all()

    # Active schedules
    schedules = await _q(StaffSchedule, db, hub_id).filter(
        StaffSchedule.staff_id == member_id,
        StaffSchedule.is_active == True,  # noqa: E712
    ).all()

    # Services
    services = await _q(StaffService, db, hub_id).filter(
        StaffService.staff_id == member_id,
        StaffService.is_active == True,  # noqa: E712
    ).all()

    return {
        "_template": "staff/pages/staff_detail.html",
        "_partial": "staff/partials/staff_detail_content.html",
        "member": member,
        "pending_time_off": pending_time_off,
        "schedules": schedules,
        "services": services,
    }


# ============================================================================
# Staff Edit
# ============================================================================

@router.get("/staff/{member_id}/edit")
@htmx_view(module_id="staff", view_id="staff_list")
async def staff_form_edit(
    request: Request, member_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Staff edit form."""
    member = await _q(StaffMember, db, hub_id).get(member_id)
    if member is None:
        return JSONResponse({"error": "Staff member not found"}, status_code=404)

    roles = await _q(StaffRole, db, hub_id).filter(
        StaffRole.is_active == True  # noqa: E712
    ).order_by(StaffRole.order).all()

    return {
        "_template": "staff/pages/staff_form.html",
        "_partial": "staff/partials/staff_form_content.html",
        "member": member,
        "roles": roles,
    }


@router.post("/staff/{member_id}/edit")
async def staff_edit(
    request: Request, member_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Update a staff member."""
    member = await _q(StaffMember, db, hub_id).get(member_id)
    if member is None:
        return JSONResponse({"success": False, "error": "Staff member not found"}, status_code=404)

    try:
        body = await request.json()
        data = StaffMemberUpdate(**body)

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(member, key, value)
        await db.flush()

        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


# ============================================================================
# Staff Delete
# ============================================================================

@router.post("/staff/{member_id}/delete")
async def staff_delete(
    request: Request, member_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Soft-delete a staff member."""
    deleted = await _q(StaffMember, db, hub_id).delete(member_id)
    if not deleted:
        return JSONResponse({"success": False, "error": "Staff member not found"}, status_code=404)
    return JSONResponse({"success": True})


# ============================================================================
# Schedules
# ============================================================================

@router.get("/staff/{member_id}/schedules")
@htmx_view(module_id="staff", view_id="schedules")
async def staff_schedules(
    request: Request, member_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Schedules for a staff member."""
    member = await _q(StaffMember, db, hub_id).get(member_id)
    if member is None:
        return JSONResponse({"error": "Staff member not found"}, status_code=404)

    schedules = await _q(StaffSchedule, db, hub_id).filter(
        StaffSchedule.staff_id == member_id,
    ).order_by(StaffSchedule.is_default.desc(), StaffSchedule.name).all()

    return {
        "_template": "staff/pages/schedules.html",
        "_partial": "staff/partials/schedules_content.html",
        "member": member,
        "schedules": schedules,
    }


@router.post("/staff/{member_id}/schedules/create")
async def schedule_create(
    request: Request, member_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Create a schedule with working hours."""
    member = await _q(StaffMember, db, hub_id).get(member_id)
    if member is None:
        return JSONResponse({"success": False, "error": "Staff member not found"}, status_code=404)

    try:
        body = await request.json()
        schedule_data = StaffScheduleCreate(**body.get("schedule", {}))
        hours_data = [WorkingHoursInput(**h) for h in body.get("working_hours", [])]

        async with atomic(db) as session:
            # If this is default, unset other defaults
            if schedule_data.is_default:
                existing = await _q(StaffSchedule, session, hub_id).filter(
                    StaffSchedule.staff_id == member_id,
                    StaffSchedule.is_default == True,  # noqa: E712
                ).all()
                for s in existing:
                    s.is_default = False

            schedule = StaffSchedule(
                hub_id=hub_id,
                staff_id=member_id,
                **schedule_data.model_dump(),
            )
            session.add(schedule)
            await session.flush()

            # Create working hours
            for wh in hours_data:
                working_hours = StaffWorkingHours(
                    hub_id=hub_id,
                    schedule_id=schedule.id,
                    day_of_week=wh.day_of_week,
                    start_time=time.fromisoformat(wh.start_time),
                    end_time=time.fromisoformat(wh.end_time),
                    break_start=time.fromisoformat(wh.break_start) if wh.break_start else None,
                    break_end=time.fromisoformat(wh.break_end) if wh.break_end else None,
                    is_working=wh.is_working,
                )
                session.add(working_hours)

        return JSONResponse({"success": True, "id": str(schedule.id)})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


# ============================================================================
# Schedules overview (all staff)
# ============================================================================

@router.get("/schedules")
@htmx_view(module_id="staff", view_id="schedules", permissions="staff.view_staff_member")
async def schedules_overview(
    request: Request, db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Schedules overview for all staff."""
    staff = await _q(StaffMember, db, hub_id).filter(
        StaffMember.status == "active"
    ).order_by(StaffMember.order, StaffMember.first_name).all()

    # Load schedules for each staff member
    staff_schedules = {}
    for member in staff:
        schedules = await _q(StaffSchedule, db, hub_id).filter(
            StaffSchedule.staff_id == member.id,
            StaffSchedule.is_active == True,  # noqa: E712
        ).all()
        staff_schedules[str(member.id)] = schedules

    return {
        "staff": staff,
        "staff_schedules": staff_schedules,
    }


# ============================================================================
# Time Off
# ============================================================================

@router.get("/staff/{member_id}/time-off")
@htmx_view(module_id="staff", view_id="staff_list")
async def staff_time_off(
    request: Request, member_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Time off list for a staff member."""
    member = await _q(StaffMember, db, hub_id).get(member_id)
    if member is None:
        return JSONResponse({"error": "Staff member not found"}, status_code=404)

    time_offs = await _q(StaffTimeOff, db, hub_id).filter(
        StaffTimeOff.staff_id == member_id,
    ).order_by(StaffTimeOff.start_date.desc()).all()

    return {
        "_template": "staff/pages/time_off.html",
        "_partial": "staff/partials/time_off_content.html",
        "member": member,
        "time_offs": time_offs,
    }


@router.post("/staff/{member_id}/time-off/create")
async def time_off_create(
    request: Request, member_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Create a time off request."""
    member = await _q(StaffMember, db, hub_id).get(member_id)
    if member is None:
        return JSONResponse({"success": False, "error": "Staff member not found"}, status_code=404)

    try:
        body = await request.json()
        data = StaffTimeOffCreate(**body)

        if data.end_date < data.start_date:
            return JSONResponse({"success": False, "error": "End date must be after start date"})

        async with atomic(db) as session:
            time_off = StaffTimeOff(
                hub_id=hub_id,
                staff_id=member_id,
                leave_type=data.leave_type,
                start_date=data.start_date,
                end_date=data.end_date,
                is_full_day=data.is_full_day,
                start_time=time.fromisoformat(data.start_time) if data.start_time else None,
                end_time=time.fromisoformat(data.end_time) if data.end_time else None,
                reason=data.reason,
                notes=data.notes,
            )
            session.add(time_off)

        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


@router.post("/staff/{member_id}/time-off/{to_id}/approve")
async def time_off_approve(
    request: Request, member_id: uuid.UUID, to_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Approve a time off request."""
    time_off = await _q(StaffTimeOff, db, hub_id).get(to_id)
    if time_off is None or time_off.staff_id != member_id:
        return JSONResponse({"success": False, "error": "Time off not found"}, status_code=404)

    if time_off.status != "pending":
        return JSONResponse({"success": False, "error": "Only pending requests can be approved"})

    time_off.status = "approved"
    time_off.approved_by = user.id
    time_off.approved_at = datetime.now(UTC)
    await db.flush()

    return JSONResponse({"success": True})


@router.post("/staff/{member_id}/time-off/{to_id}/reject")
async def time_off_reject(
    request: Request, member_id: uuid.UUID, to_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Reject a time off request."""
    time_off = await _q(StaffTimeOff, db, hub_id).get(to_id)
    if time_off is None or time_off.staff_id != member_id:
        return JSONResponse({"success": False, "error": "Time off not found"}, status_code=404)

    if time_off.status != "pending":
        return JSONResponse({"success": False, "error": "Only pending requests can be rejected"})

    body = await request.json()
    time_off.status = "rejected"
    time_off.notes = body.get("notes", "")
    await db.flush()

    return JSONResponse({"success": True})


# ============================================================================
# Staff Services
# ============================================================================

@router.get("/staff/{member_id}/services")
@htmx_view(module_id="staff", view_id="staff_list")
async def staff_services(
    request: Request, member_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Staff service assignments."""
    member = await _q(StaffMember, db, hub_id).get(member_id)
    if member is None:
        return JSONResponse({"error": "Staff member not found"}, status_code=404)

    services = await _q(StaffService, db, hub_id).filter(
        StaffService.staff_id == member_id,
    ).all()

    # Try to load available services from services module (optional)
    available_services = []
    try:
        from services.models import Service
        available_services = await _q(Service, db, hub_id).filter(
            Service.is_active == True  # noqa: E712
        ).all()
    except (ImportError, Exception):
        pass

    return {
        "_template": "staff/pages/staff_detail.html",
        "_partial": "staff/partials/staff_detail_content.html",
        "member": member,
        "services": services,
        "available_services": available_services,
        "active_tab": "services",
    }


@router.post("/staff/{member_id}/services/save")
async def staff_services_save(
    request: Request, member_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Bulk save service assignments for a staff member."""
    member = await _q(StaffMember, db, hub_id).get(member_id)
    if member is None:
        return JSONResponse({"success": False, "error": "Staff member not found"}, status_code=404)

    try:
        body = await request.json()
        data = StaffServiceBulkSave(**body)

        async with atomic(db) as session:
            # Delete existing services for this member
            existing = await _q(StaffService, session, hub_id).filter(
                StaffService.staff_id == member_id,
            ).all()
            for svc in existing:
                await _q(StaffService, session, hub_id).hard_delete(svc.id)

            # Create new assignments
            for svc_input in data.services:
                svc = StaffService(
                    hub_id=hub_id,
                    staff_id=member_id,
                    service_id=svc_input.service_id,
                    service_name=svc_input.service_name,
                    custom_duration=svc_input.custom_duration,
                    custom_price=svc_input.custom_price,
                    is_primary=svc_input.is_primary,
                    is_active=svc_input.is_active,
                )
                session.add(svc)

        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


# ============================================================================
# Roles
# ============================================================================

@router.get("/roles")
@htmx_view(module_id="staff", view_id="roles", permissions="staff.view_staff_member")
async def roles_list(
    request: Request, db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Roles list."""
    roles = await _q(StaffRole, db, hub_id).order_by(
        StaffRole.order, StaffRole.name
    ).all()

    # Count members per role
    role_counts = {}
    for role in roles:
        count = await _q(StaffMember, db, hub_id).filter(
            StaffMember.role_id == role.id,
        ).count()
        role_counts[str(role.id)] = count

    return {
        "roles": roles,
        "role_counts": role_counts,
    }


@router.post("/roles/create")
async def role_create(
    request: Request, db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Create a role."""
    try:
        body = await request.json()
        data = StaffRoleCreate(**body)

        async with atomic(db) as session:
            role = StaffRole(hub_id=hub_id, **data.model_dump())
            session.add(role)

        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


@router.post("/roles/{role_id}/edit")
async def role_edit(
    request: Request, role_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Update a role."""
    role = await _q(StaffRole, db, hub_id).get(role_id)
    if role is None:
        return JSONResponse({"success": False, "error": "Role not found"}, status_code=404)

    try:
        body = await request.json()
        data = StaffRoleUpdate(**body)

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(role, key, value)
        await db.flush()

        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


@router.post("/roles/{role_id}/delete")
async def role_delete(
    request: Request, role_id: uuid.UUID,
    db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Soft-delete a role."""
    # Check if any members are using this role
    member_count = await _q(StaffMember, db, hub_id).filter(
        StaffMember.role_id == role_id,
    ).count()
    if member_count > 0:
        return JSONResponse({
            "success": False,
            "error": f"Cannot delete role: {member_count} member(s) are assigned to it",
        })

    deleted = await _q(StaffRole, db, hub_id).delete(role_id)
    if not deleted:
        return JSONResponse({"success": False, "error": "Role not found"}, status_code=404)
    return JSONResponse({"success": True})


# ============================================================================
# Settings
# ============================================================================

@router.get("/settings")
@htmx_view(module_id="staff", view_id="settings", permissions="staff.manage_settings")
async def settings_view(
    request: Request, db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Staff settings page."""
    settings = await _q(StaffSettings, db, hub_id).first()
    if settings is None:
        async with atomic(db) as session:
            settings = StaffSettings(hub_id=hub_id)
            session.add(settings)
            await session.flush()

    return {
        "settings": settings,
    }


@router.post("/settings/save")
async def settings_save(
    request: Request, db: DbSession, user: CurrentUser, hub_id: HubId,
):
    """Save staff settings."""
    try:
        body = await request.json()
        data = StaffSettingsUpdate(**body)

        settings = await _q(StaffSettings, db, hub_id).first()
        if settings is None:
            async with atomic(db) as session:
                settings = StaffSettings(hub_id=hub_id)
                session.add(settings)
                await session.flush()

        updates = data.model_dump(exclude_unset=True)

        # Convert time strings to time objects
        for field in ("default_work_start", "default_work_end"):
            if field in updates and isinstance(updates[field], str):
                updates[field] = time.fromisoformat(updates[field])

        for key, value in updates.items():
            setattr(settings, key, value)
        await db.flush()

        return JSONResponse({"success": True})
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=400)


# ============================================================================
# API: Search staff
# ============================================================================

@router.get("/api/search")
async def api_search_staff(
    request: Request, db: DbSession, hub_id: HubId,
    q: str = "", limit: int = 20,
):
    """JSON search staff members."""
    query = _q(StaffMember, db, hub_id).filter(
        StaffMember.status == "active"
    )

    if q:
        query = query.filter(or_(
            StaffMember.first_name.ilike(f"%{q}%"),
            StaffMember.last_name.ilike(f"%{q}%"),
        ))

    members = await query.order_by(
        StaffMember.order, StaffMember.first_name
    ).limit(limit).all()

    data = [{
        "id": str(m.id),
        "name": m.full_name,
        "email": m.email,
        "phone": m.phone,
        "role": m.role_rel.name if m.role_rel else "",
        "is_bookable": m.is_bookable,
        "photo": m.photo,
        "color": m.color,
    } for m in members]

    return JSONResponse({"success": True, "staff": data})


# ============================================================================
# API: Available staff at datetime
# ============================================================================

@router.get("/api/available")
async def api_available_staff(
    request: Request, db: DbSession, hub_id: HubId,
    date_str: str = "", time_str: str = "", service_id: str = "",
):
    """JSON available staff at a given datetime, optionally for a specific service."""
    from datetime import date as date_type

    try:
        target_date = date_type.fromisoformat(date_str) if date_str else date_type.today()
        target_time = time.fromisoformat(time_str) if time_str else None
    except ValueError:
        return JSONResponse({"success": False, "error": "Invalid date/time format"})

    # Get bookable staff
    query = _q(StaffMember, db, hub_id).filter(
        StaffMember.status == "active",
        StaffMember.is_bookable == True,  # noqa: E712
    )

    members = await query.order_by(
        StaffMember.order, StaffMember.first_name
    ).all()

    available = []
    day_of_week = target_date.weekday()

    for member in members:
        # Check if on time off
        time_offs = await _q(StaffTimeOff, db, hub_id).filter(
            StaffTimeOff.staff_id == member.id,
            StaffTimeOff.status == "approved",
            StaffTimeOff.start_date <= target_date,
            StaffTimeOff.end_date >= target_date,
        ).all()

        if time_offs:
            continue

        # Check schedule
        schedule = await _q(StaffSchedule, db, hub_id).filter(
            StaffSchedule.staff_id == member.id,
            StaffSchedule.is_active == True,  # noqa: E712
        ).first()

        if schedule:
            wh = await _q(StaffWorkingHours, db, hub_id).filter(
                StaffWorkingHours.schedule_id == schedule.id,
                StaffWorkingHours.day_of_week == day_of_week,
                StaffWorkingHours.is_working == True,  # noqa: E712
            ).first()

            if wh is None:
                continue

            # If time specified, check within working hours
            if target_time:
                if target_time < wh.start_time or target_time > wh.end_time:
                    continue
                # Check if during break
                if wh.break_start and wh.break_end:
                    if wh.break_start <= target_time <= wh.break_end:
                        continue

        # If service_id specified, check if member provides it
        if service_id:
            svc = await _q(StaffService, db, hub_id).filter(
                StaffService.staff_id == member.id,
                StaffService.service_id == uuid.UUID(service_id),
                StaffService.is_active == True,  # noqa: E712
            ).first()
            if svc is None:
                continue

        available.append({
            "id": str(member.id),
            "name": member.full_name,
            "role": member.role_rel.name if member.role_rel else "",
            "color": member.color,
            "photo": member.photo,
        })

    return JSONResponse({"success": True, "available": available, "count": len(available)})
