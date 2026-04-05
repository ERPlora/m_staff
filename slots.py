"""
Staff module slot registrations.

Defines slots that OTHER modules can fill (e.g. staff profile sidebar).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.slots import SlotRegistry

MODULE_ID = "staff"


def register_slots(slots: SlotRegistry, module_id: str) -> None:
    """
    Register slot definitions owned by the staff module.

    Other modules (appointments, commissions, etc.) register content INTO these slots.
    The staff module declares the extension points.

    Called by ModuleRuntime during module load.
    """
    # Declare slots that the staff detail template renders with {{ render_slot(...) }}
    # Other modules fill these via their own slots.py
    # The staff module doesn't fill its own slots — it owns them.
