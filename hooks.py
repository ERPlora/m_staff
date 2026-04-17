"""
Staff module hook registrations.

Registers actions and filters on the HookRegistry during module load.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.signals.hooks import HookRegistry

MODULE_ID = "staff"


def register_hooks(hooks: HookRegistry, module_id: str) -> None:
    """
    Register hooks for the staff module.

    Called by ModuleRuntime during module load.
    """
    # Action: after staff member created — other modules can subscribe
    hooks.add_action(
        "staff.member_created",
        _on_member_created_action,
        priority=10,
        module_id=module_id,
    )

    # Action: after time off approved
    hooks.add_action(
        "staff.time_off_approved",
        _on_time_off_approved_action,
        priority=10,
        module_id=module_id,
    )


async def _on_member_created_action(
    member=None,
    session=None,
    **kwargs,
) -> None:
    """
    Default action when a staff member is created.
    Other modules can add_action('staff.member_created', ...) to extend.
    """


async def _on_time_off_approved_action(
    time_off=None,
    session=None,
    **kwargs,
) -> None:
    """
    Default action when time off is approved.
    Appointments module can cancel conflicting appointments.
    """
