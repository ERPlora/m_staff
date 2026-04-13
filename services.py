"""
Staff module services — ModuleService pattern for AI assistant integration.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import or_

from app.core.db.repository import serialize, serialize_list
from app.core.db.transactions import atomic
from app.modules.services import ModuleService, action

from .models import StaffMember, StaffRole, StaffTimeOff


class StaffService(ModuleService):
    """Staff member and role management."""

    @action(permission="view_staff_member")
    async def list_staff(
        self,
        *,
        status: str = "",
        role_id: str = "",
        is_bookable: bool | None = None,
        search: str = "",
        limit: int = 20,
    ) -> dict:
        """List staff members with optional filters."""
        query = self.q(StaffMember)

        if status:
            query = query.filter(StaffMember.status == status)
        if role_id:
            query = query.filter(StaffMember.role_id == uuid.UUID(role_id))
        if is_bookable is not None:
            query = query.filter(StaffMember.is_bookable == is_bookable)
        if search:
            term = f"%{search}%"
            query = query.filter(
                or_(
                    StaffMember.first_name.ilike(term),
                    StaffMember.last_name.ilike(term),
                )
            )

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

    @action(permission="view_staff_member")
    async def get_staff_detail(self, *, staff_id: str) -> dict:
        """Get full details of a staff member including services."""
        m = await self.q(StaffMember).get(uuid.UUID(staff_id))
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

    @action(permission="add_staff_member", mutates=True)
    async def create_staff_member(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str = "",
        phone: str = "",
        role_id: str = "",
        hire_date: str = "",
        hourly_rate: str = "",
        is_bookable: bool = True,
        bio: str = "",
        specialties: str = "",
    ) -> dict:
        """Create a new staff member."""
        hire = None
        if hire_date:
            hire = datetime.strptime(hire_date, "%Y-%m-%d").date()

        async with atomic(self.db) as session:
            m = StaffMember(
                hub_id=self.hub_id,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                role_id=uuid.UUID(role_id) if role_id else None,
                hire_date=hire,
                hourly_rate=Decimal(hourly_rate) if hourly_rate else Decimal("0.00"),
                is_bookable=is_bookable,
                bio=bio,
                specialties=specialties,
            )
            session.add(m)
            await session.flush()

        return {"id": str(m.id), "full_name": m.full_name, "created": True}

    @action(permission="add_staff_member", mutates=True)
    async def bulk_create_staff_members(self, *, members: list[dict]) -> dict:
        """Create multiple staff members at once."""
        created = 0
        errors: list[dict] = []

        for item in members:
            try:
                hire = None
                if item.get("hire_date"):
                    hire = datetime.strptime(item["hire_date"], "%Y-%m-%d").date()

                async with atomic(self.db) as session:
                    m = StaffMember(
                        hub_id=self.hub_id,
                        first_name=item["first_name"],
                        last_name=item["last_name"],
                        email=item.get("email", ""),
                        phone=item.get("phone", ""),
                        role_id=uuid.UUID(item["role_id"]) if item.get("role_id") else None,
                        hire_date=hire,
                        hourly_rate=Decimal(item["hourly_rate"]) if item.get("hourly_rate") else Decimal("0.00"),
                        is_bookable=item.get("is_bookable", True),
                        bio=item.get("bio", ""),
                        specialties=item.get("specialties", ""),
                    )
                    session.add(m)
                    await session.flush()
                created += 1
            except Exception as e:
                errors.append({
                    "name": f"{item.get('first_name', '')} {item.get('last_name', '')}".strip(),
                    "error": str(e),
                })

        return {"success": True, "created": created, "errors": errors}

    @action(permission="change_staff_member", mutates=True)
    async def update_staff_member(
        self,
        *,
        staff_id: str,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        role_id: str | None = None,
        status: str | None = None,
        hire_date: str | None = None,
        hourly_rate: str | None = None,
        commission_rate: str | None = None,
        is_bookable: bool | None = None,
        bio: str | None = None,
        specialties: str | None = None,
        notes: str | None = None,
    ) -> dict:
        """Update an existing staff member."""
        m = await self.q(StaffMember).get(uuid.UUID(staff_id))
        if m is None:
            return {"error": "Staff member not found"}

        async with atomic(self.db):
            for field in ("first_name", "last_name", "email", "phone", "bio", "specialties", "notes", "status"):
                val = locals().get(field)
                if val is not None:
                    setattr(m, field, val)
            if role_id is not None:
                m.role_id = uuid.UUID(role_id) if role_id else None
            if hire_date is not None:
                m.hire_date = datetime.strptime(hire_date, "%Y-%m-%d").date() if hire_date else None
            if hourly_rate is not None:
                m.hourly_rate = Decimal(hourly_rate)
            if commission_rate is not None:
                m.commission_rate = Decimal(commission_rate)
            if is_bookable is not None:
                m.is_bookable = is_bookable
            await self.db.flush()

        return {"id": str(m.id), "full_name": m.full_name, "updated": True}

    @action(permission="change_staff_member", mutates=True)
    async def deactivate_staff_member(self, *, staff_id: str) -> dict:
        """Soft-deactivate a staff member (sets status to 'inactive')."""
        m = await self.q(StaffMember).get(uuid.UUID(staff_id))
        if m is None:
            return {"error": "Staff member not found"}

        if m.status == "inactive":
            return {"error": "Staff member is already inactive"}
        if m.status == "terminated":
            return {"error": "Staff member is already terminated"}

        active_time_off = await self.q(StaffTimeOff).filter(
            StaffTimeOff.staff_id == m.id,
            StaffTimeOff.status.in_(["pending", "approved"]),
            StaffTimeOff.end_date >= date.today(),
        ).count()

        if active_time_off > 0:
            return {
                "error": f"Cannot deactivate: {active_time_off} active time-off request(s) exist. "
                "Cancel or resolve them first."
            }

        async with atomic(self.db):
            m.status = "inactive"
            m.is_bookable = False
            await self.db.flush()

        return {"id": str(m.id), "full_name": m.full_name, "deactivated": True}

    @action(permission="view_staff_member")
    async def list_roles(self) -> dict:
        """List all active staff roles."""
        roles = await self.q(StaffRole).filter(
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

    @action(permission="manage_settings", mutates=True)
    async def create_role(
        self,
        *,
        name: str,
        description: str = "",
        color: str = "",
    ) -> dict:
        """Create a new staff role."""
        async with atomic(self.db) as session:
            r = StaffRole(
                hub_id=self.hub_id,
                name=name,
                description=description,
                color=color,
            )
            session.add(r)
            await session.flush()

        return {"id": str(r.id), "name": r.name, "created": True}
