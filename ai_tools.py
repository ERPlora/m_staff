"""
AI tools for the Staff module.

Uses @register_tool + AssistantTool class pattern.
All tools are async and use HubQuery for DB access.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from app.ai.registry import AssistantTool, register_tool
from app.core.db.query import HubQuery
from app.core.db.transactions import atomic

from .models import StaffMember, StaffRole


def _q(model, session, hub_id):
    return HubQuery(model, session, hub_id)


@register_tool
class ListStaff(AssistantTool):
    name = "list_staff"
    description = (
        "List staff members with optional filters by status, role, bookable. "
        "Read-only -- no side effects."
    )
    module_id = "staff"
    required_permission = "staff.view_staff_member"
    parameters = {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Filter: active, inactive, on_leave, terminated",
            },
            "role_id": {"type": "string", "description": "Filter by role UUID"},
            "is_bookable": {"type": "boolean", "description": "Filter by bookable flag"},
            "search": {"type": "string", "description": "Search by name (partial match)"},
            "limit": {"type": "integer", "description": "Max results (default 20)"},
        },
        "required": [],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id
        query = _q(StaffMember, db, hub_id)

        if args.get("status"):
            query = query.filter(StaffMember.status == args["status"])
        if args.get("role_id"):
            query = query.filter(StaffMember.role_id == uuid.UUID(args["role_id"]))
        if args.get("is_bookable") is not None:
            query = query.filter(StaffMember.is_bookable == args["is_bookable"])
        if args.get("search"):
            term = f"%{args['search']}%"
            from sqlalchemy import or_
            query = query.filter(
                or_(
                    StaffMember.first_name.ilike(term),
                    StaffMember.last_name.ilike(term),
                )
            )

        limit = args.get("limit", 20)
        total = await query.count()
        members = await query.order_by(StaffMember.first_name).limit(limit).all()

        return {
            "staff": [{
                "id": str(m.id),
                "first_name": m.first_name,
                "last_name": m.last_name,
                "full_name": m.full_name,
                "email": m.email,
                "phone": m.phone,
                "role": m.role_rel.name if m.role_rel else "",
                "status": m.status,
                "is_bookable": m.is_bookable,
                "hire_date": str(m.hire_date) if m.hire_date else None,
                "hourly_rate": str(m.hourly_rate),
            } for m in members],
            "total": total,
        }


@register_tool
class GetStaffDetail(AssistantTool):
    name = "get_staff_detail"
    description = "Get full details of a staff member including schedules and services. Read-only."
    module_id = "staff"
    required_permission = "staff.view_staff_member"
    parameters = {
        "type": "object",
        "properties": {
            "staff_id": {"type": "string", "description": "Staff member UUID"},
        },
        "required": ["staff_id"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id
        m = await _q(StaffMember, db, hub_id).get(uuid.UUID(args["staff_id"]))
        if m is None:
            return {"error": "Staff member not found"}

        services = [
            {
                "service_name": s.service_name,
                "custom_duration": s.custom_duration,
                "custom_price": str(s.custom_price) if s.custom_price else None,
                "is_primary": s.is_primary,
                "is_active": s.is_active,
            }
            for s in m.staff_services if not s.is_deleted
        ]

        return {
            "id": str(m.id),
            "first_name": m.first_name,
            "last_name": m.last_name,
            "full_name": m.full_name,
            "email": m.email,
            "phone": m.phone,
            "employee_id": m.employee_id,
            "role": m.role_rel.name if m.role_rel else "",
            "role_id": str(m.role_id) if m.role_id else None,
            "status": m.status,
            "hire_date": str(m.hire_date) if m.hire_date else None,
            "termination_date": str(m.termination_date) if m.termination_date else None,
            "years_of_service": m.years_of_service,
            "bio": m.bio,
            "specialties": m.get_specialties_list(),
            "is_bookable": m.is_bookable,
            "hourly_rate": str(m.hourly_rate),
            "commission_rate": str(m.commission_rate),
            "color": m.color,
            "notes": m.notes,
            "services": services,
        }


@register_tool
class CreateStaffMember(AssistantTool):
    name = "create_staff_member"
    description = (
        "Create a new staff member. "
        "SIDE EFFECT: creates a staff record. Requires confirmation."
    )
    module_id = "staff"
    required_permission = "staff.add_staff_member"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "first_name": {"type": "string", "description": "First name"},
            "last_name": {"type": "string", "description": "Last name"},
            "email": {"type": "string", "description": "Email address"},
            "phone": {"type": "string", "description": "Phone number"},
            "role_id": {"type": "string", "description": "Role UUID"},
            "hire_date": {"type": "string", "description": "Hire date (YYYY-MM-DD)"},
            "hourly_rate": {"type": "string", "description": "Hourly rate (decimal)"},
            "is_bookable": {"type": "boolean", "description": "Can be booked for appointments"},
            "bio": {"type": "string", "description": "Staff bio"},
            "specialties": {"type": "string", "description": "Comma-separated specialties"},
        },
        "required": ["first_name", "last_name"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id

        hire = None
        if args.get("hire_date"):
            hire = datetime.strptime(args["hire_date"], "%Y-%m-%d").date()

        from decimal import Decimal
        async with atomic(db) as session:
            m = StaffMember(
                hub_id=hub_id,
                first_name=args["first_name"],
                last_name=args["last_name"],
                email=args.get("email", ""),
                phone=args.get("phone", ""),
                role_id=uuid.UUID(args["role_id"]) if args.get("role_id") else None,
                hire_date=hire,
                hourly_rate=Decimal(args["hourly_rate"]) if args.get("hourly_rate") else Decimal("0.00"),
                is_bookable=args.get("is_bookable", True),
                bio=args.get("bio", ""),
                specialties=args.get("specialties", ""),
            )
            session.add(m)
            await session.flush()

        return {"id": str(m.id), "full_name": m.full_name, "created": True}


@register_tool
class UpdateStaffMember(AssistantTool):
    name = "update_staff_member"
    description = "Update an existing staff member. SIDE EFFECT. Requires confirmation."
    module_id = "staff"
    required_permission = "staff.change_staff_member"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "staff_id": {"type": "string", "description": "Staff member UUID"},
            "first_name": {"type": "string", "description": "First name"},
            "last_name": {"type": "string", "description": "Last name"},
            "email": {"type": "string", "description": "Email address"},
            "phone": {"type": "string", "description": "Phone number"},
            "role_id": {"type": "string", "description": "Role UUID (null to remove)"},
            "status": {"type": "string", "description": "Status: active, inactive, on_leave, terminated"},
            "hire_date": {"type": "string", "description": "Hire date (YYYY-MM-DD)"},
            "hourly_rate": {"type": "string", "description": "Hourly rate (decimal)"},
            "commission_rate": {"type": "string", "description": "Commission rate % (decimal)"},
            "is_bookable": {"type": "boolean", "description": "Can be booked"},
            "bio": {"type": "string", "description": "Staff bio"},
            "specialties": {"type": "string", "description": "Comma-separated specialties"},
            "notes": {"type": "string", "description": "Notes"},
        },
        "required": ["staff_id"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id

        m = await _q(StaffMember, db, hub_id).get(uuid.UUID(args["staff_id"]))
        if m is None:
            return {"error": "Staff member not found"}

        from decimal import Decimal
        async with atomic(db):
            for field in ("first_name", "last_name", "email", "phone", "bio", "specialties", "notes", "status"):
                if field in args:
                    setattr(m, field, args[field])
            if "role_id" in args:
                m.role_id = uuid.UUID(args["role_id"]) if args["role_id"] else None
            if "hire_date" in args:
                m.hire_date = datetime.strptime(args["hire_date"], "%Y-%m-%d").date() if args["hire_date"] else None
            if "hourly_rate" in args:
                m.hourly_rate = Decimal(args["hourly_rate"])
            if "commission_rate" in args:
                m.commission_rate = Decimal(args["commission_rate"])
            if "is_bookable" in args:
                m.is_bookable = args["is_bookable"]
            await db.flush()

        return {"id": str(m.id), "full_name": m.full_name, "updated": True}


@register_tool
class DeactivateStaffMember(AssistantTool):
    name = "deactivate_staff_member"
    description = (
        "Soft-deactivate a staff member (sets status to 'inactive'). "
        "Checks for active appointments/assignments first. "
        "SIDE EFFECT. Requires confirmation."
    )
    module_id = "staff"
    required_permission = "staff.change_staff_member"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "staff_id": {"type": "string", "description": "Staff member UUID"},
        },
        "required": ["staff_id"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id

        m = await _q(StaffMember, db, hub_id).get(uuid.UUID(args["staff_id"]))
        if m is None:
            return {"error": "Staff member not found"}

        if m.status == "inactive":
            return {"error": "Staff member is already inactive"}

        if m.status == "terminated":
            return {"error": "Staff member is already terminated"}

        # Check for active time off (pending/approved)
        from .models import StaffTimeOff
        active_time_off = await _q(StaffTimeOff, db, hub_id).filter(
            StaffTimeOff.staff_id == m.id,
            StaffTimeOff.status.in_(["pending", "approved"]),
            StaffTimeOff.end_date >= date.today(),
        ).count()

        if active_time_off > 0:
            return {
                "error": f"Cannot deactivate: {active_time_off} active time-off request(s) exist. "
                "Cancel or resolve them first."
            }

        async with atomic(db):
            m.status = "inactive"
            m.is_bookable = False
            await db.flush()

        return {"id": str(m.id), "full_name": m.full_name, "deactivated": True}


@register_tool
class ListRoles(AssistantTool):
    name = "list_roles"
    description = "List all staff roles. Read-only."
    module_id = "staff"
    required_permission = "staff.view_staff_member"
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id

        roles = await _q(StaffRole, db, hub_id).filter(
            StaffRole.is_active == True,  # noqa: E712
        ).order_by(StaffRole.order, StaffRole.name).all()

        return {
            "roles": [{
                "id": str(r.id),
                "name": r.name,
                "description": r.description,
                "color": r.color,
                "member_count": len([m for m in r.members if not m.is_deleted and m.status == "active"]),
            } for r in roles],
        }


@register_tool
class CreateRole(AssistantTool):
    name = "create_role"
    description = "Create a new staff role. SIDE EFFECT. Requires confirmation."
    module_id = "staff"
    required_permission = "staff.manage_settings"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Role name"},
            "description": {"type": "string", "description": "Role description"},
            "color": {"type": "string", "description": "Hex color (e.g. #FF5733)"},
        },
        "required": ["name"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict, request: Any) -> dict:
        db = request.state.db
        hub_id = request.state.hub_id

        async with atomic(db) as session:
            r = StaffRole(
                hub_id=hub_id,
                name=args["name"],
                description=args.get("description", ""),
                color=args.get("color", ""),
            )
            session.add(r)
            await session.flush()

        return {"id": str(r.id), "name": r.name, "created": True}
