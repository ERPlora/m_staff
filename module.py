"""
Staff module manifest.

Staff profiles, roles, schedules, time off, and service assignments.
Base HR module for appointment booking, commissions, and workforce management.
"""


# ---------------------------------------------------------------------------
# Module identity
# ---------------------------------------------------------------------------
MODULE_ID = "staff"
MODULE_NAME = "Staff"
MODULE_VERSION = "2.0.3"
MODULE_ICON = "people-outline"
MODULE_DESCRIPTION = "Staff profiles, roles, schedules, time off, and service assignments"
MODULE_AUTHOR = "ERPlora"

# ---------------------------------------------------------------------------
# Capabilities
# ---------------------------------------------------------------------------
HAS_MODELS = True
MIDDLEWARE = ""

# ---------------------------------------------------------------------------
# Menu (sidebar entry)
# ---------------------------------------------------------------------------
MENU = {
    "label": "Staff",
    "icon": "people-outline",
    "order": 40,
}

# ---------------------------------------------------------------------------
# Navigation tabs (bottom tabbar in module views)
# ---------------------------------------------------------------------------
NAVIGATION = [
    {"id": "dashboard", "label": "Dashboard", "icon": "stats-chart-outline", "view": "dashboard"},
    {"id": "staff", "label": "Staff", "icon": "people-outline", "view": "staff_list"},
    {"id": "schedules", "label": "Schedules", "icon": "calendar-outline", "view": "schedules"},
    {"id": "roles", "label": "Roles", "icon": "shield-outline", "view": "roles"},
    {"id": "settings", "label": "Settings", "icon": "settings-outline", "view": "settings"},
]

# ---------------------------------------------------------------------------
# Dependencies (other modules required to be active)
# ---------------------------------------------------------------------------
DEPENDENCIES: list[str] = []

# ---------------------------------------------------------------------------
# Permissions
# ---------------------------------------------------------------------------
PERMISSIONS = [
    ("view_staff_member", "View staff members"),
    ("add_staff_member", "Add staff members"),
    ("change_staff_member", "Edit staff members"),
    ("delete_staff_member", "Delete staff members"),
    ("view_time_off", "View time off requests"),
    ("manage_time_off", "Manage time off requests"),
    ("manage_settings", "Manage staff settings"),
]

ROLE_PERMISSIONS = {
    "admin": ["*"],
    "manager": [
        "view_staff_member", "add_staff_member", "change_staff_member",
        "view_time_off", "manage_time_off", "manage_settings",
    ],
    "employee": ["view_staff_member", "view_time_off"],
}

# ---------------------------------------------------------------------------
# Scheduled tasks
# ---------------------------------------------------------------------------
SCHEDULED_TASKS: list[dict] = []

# ---------------------------------------------------------------------------
# Pricing (free module)
# ---------------------------------------------------------------------------
# PRICING = {"monthly": 0, "yearly": 0}
