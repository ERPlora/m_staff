"""Initial staff module schema.

Revision ID: 001
Revises: -
Create Date: 2026-04-05

Creates tables: staff_settings, staff_role, staff_member, staff_schedule,
staff_working_hours, staff_time_off, staff_service.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # StaffSettings
    op.create_table(
        "staff_settings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("hub_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("default_work_start", sa.Time(), server_default="09:00:00"),
        sa.Column("default_work_end", sa.Time(), server_default="18:00:00"),
        sa.Column("default_break_duration", sa.Integer(), server_default="60"),
        sa.Column("min_advance_booking", sa.Integer(), server_default="1"),
        sa.Column("max_daily_hours", sa.Integer(), server_default="12"),
        sa.Column("overtime_threshold", sa.Integer(), server_default="40"),
        sa.Column("show_staff_photos", sa.Boolean(), server_default="true"),
        sa.Column("show_staff_bio", sa.Boolean(), server_default="true"),
        sa.Column("allow_staff_selection", sa.Boolean(), server_default="true"),
        sa.Column("notify_new_appointment", sa.Boolean(), server_default="true"),
        sa.Column("notify_cancellation", sa.Boolean(), server_default="true"),
        sa.UniqueConstraint("hub_id", name="uq_staff_settings_hub"),
    )

    # StaffRole
    op.create_table(
        "staff_role",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("hub_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("color", sa.String(7), server_default=""),
        sa.Column("order", sa.Integer(), server_default="0"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
    )

    # StaffMember
    op.create_table(
        "staff_member",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("hub_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(254), server_default=""),
        sa.Column("phone", sa.String(20), server_default=""),
        sa.Column("photo", sa.String(500), server_default=""),
        sa.Column("employee_id", sa.String(50), server_default=""),
        sa.Column("role_id", sa.Uuid(), sa.ForeignKey("staff_role.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=True),
        sa.Column("hire_date", sa.Date(), nullable=True),
        sa.Column("termination_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20), server_default="active"),
        sa.Column("bio", sa.Text(), server_default=""),
        sa.Column("specialties", sa.Text(), server_default=""),
        sa.Column("is_bookable", sa.Boolean(), server_default="true"),
        sa.Column("color", sa.String(7), server_default=""),
        sa.Column("booking_buffer", sa.Integer(), server_default="0"),
        sa.Column("hourly_rate", sa.Numeric(10, 2), server_default="0.00"),
        sa.Column("commission_rate", sa.Numeric(5, 2), server_default="0.00"),
        sa.Column("order", sa.Integer(), server_default="0"),
        sa.Column("notes", sa.Text(), server_default=""),
    )
    op.create_index("ix_staff_hub_status", "staff_member", ["hub_id", "status"])
    op.create_index("ix_staff_hub_bookable", "staff_member", ["hub_id", "is_bookable"])

    # StaffSchedule
    op.create_table(
        "staff_schedule",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("hub_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("staff_id", sa.Uuid(), sa.ForeignKey("staff_member.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), server_default="Default Schedule"),
        sa.Column("is_default", sa.Boolean(), server_default="true"),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
    )

    # StaffWorkingHours
    op.create_table(
        "staff_working_hours",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("hub_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("schedule_id", sa.Uuid(), sa.ForeignKey("staff_schedule.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("break_start", sa.Time(), nullable=True),
        sa.Column("break_end", sa.Time(), nullable=True),
        sa.Column("is_working", sa.Boolean(), server_default="true"),
        sa.UniqueConstraint("schedule_id", "day_of_week", name="uq_staff_working_hours_schedule_day"),
    )

    # StaffTimeOff
    op.create_table(
        "staff_time_off",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("hub_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("staff_id", sa.Uuid(), sa.ForeignKey("staff_member.id", ondelete="CASCADE"), nullable=False),
        sa.Column("leave_type", sa.String(20), server_default="vacation"),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("is_full_day", sa.Boolean(), server_default="true"),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("status", sa.String(20), server_default="pending"),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text(), server_default=""),
        sa.Column("notes", sa.Text(), server_default=""),
    )
    op.create_index("ix_staff_time_off_hub_staff", "staff_time_off", ["hub_id", "staff_id"])
    op.create_index("ix_staff_time_off_hub_status", "staff_time_off", ["hub_id", "status"])

    # StaffService
    op.create_table(
        "staff_service",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("hub_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=False, index=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("staff_id", sa.Uuid(), sa.ForeignKey("staff_member.id", ondelete="CASCADE"), nullable=False),
        sa.Column("service_id", sa.Uuid(), nullable=True),
        sa.Column("service_name", sa.String(200), nullable=False),
        sa.Column("custom_duration", sa.Integer(), nullable=True),
        sa.Column("custom_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default="false"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.UniqueConstraint("staff_id", "service_id", name="uq_staff_service_staff_service"),
    )


def downgrade() -> None:
    op.drop_table("staff_service")
    op.drop_table("staff_time_off")
    op.drop_table("staff_working_hours")
    op.drop_table("staff_schedule")
    op.drop_table("staff_member")
    op.drop_table("staff_role")
    op.drop_table("staff_settings")
