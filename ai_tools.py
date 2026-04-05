"""
Staff module AI tools for the assistant.

Tools for querying staff data, managing schedules, time off.
"""

from __future__ import annotations


# AI tools will be registered here following the same @register_tool pattern.
# The staff module exposes tools for:
# - list_staff: Query staff by status, role, bookable
# - get_staff_detail: Get full staff details with schedules and services
# - get_staff_schedule: Get working hours for a staff member
# - check_staff_availability: Check if staff is available at a datetime
# - list_time_off: Query time off requests by status
# - approve_time_off: Approve a pending time off request
# - get_staff_settings: Read current settings
# - update_staff_settings: Update settings

TOOLS = []
