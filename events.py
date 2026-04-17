"""
Staff module event subscriptions.

Registers handlers on the AsyncEventBus during module load.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from runtime.signals.dispatcher import AsyncEventBus

logger = logging.getLogger(__name__)

MODULE_ID = "staff"


async def register_events(bus: AsyncEventBus, module_id: str) -> None:
    """
    Register event handlers for the staff module.

    Called by ModuleRuntime during module load.
    """

    # Listen for appointment creation to notify staff
    await bus.subscribe(
        "appointment.created",
        _on_appointment_created,
        module_id=module_id,
    )


async def _on_appointment_created(
    event: str,
    sender: object = None,
    appointment: object = None,
    **kwargs: object,
) -> None:
    """
    When an appointment is created, log for traceability.
    Staff module can react to appointment events for notifications.
    """
    if appointment is None:
        return

    logger.debug(
        "Appointment created for staff %s (staff module notified)",
        getattr(appointment, "staff_id", "?"),
    )
