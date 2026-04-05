"""
Staff module AI context — injected into the LLM system prompt.

Provides the LLM with knowledge about the module's models, relationships,
and standard operating procedures.
"""

CONTEXT = """
## Staff Module

Base HR module for staff profiles, roles, schedules, time off, and service assignments.

### StaffSettings (singleton per hub)
- Working hours defaults: default_work_start/end (Time), default_break_duration (minutes)
- Scheduling: min_advance_booking (hours), max_daily_hours, overtime_threshold (hours/week)
- Display: show_staff_photos, show_staff_bio, allow_staff_selection
- Notifications: notify_new_appointment, notify_cancellation

### StaffRole Model
- Fields: name, description, color (hex), order, is_active
- Used to categorize staff members (Manager, Employee, Trainee, etc.)

### StaffMember Model
- Basic info: first_name, last_name, email, phone, photo
- Employment: employee_id (string), role_id (FK StaffRole), user_id (UUID to LocalUser, nullable)
- Dates: hire_date, termination_date
- Status: active/inactive/on_leave/terminated
- Bio: bio (text), specialties (comma-separated)
- Booking: is_bookable, color (calendar), booking_buffer (minutes between appointments)
- Compensation: hourly_rate, commission_rate (%)
- Properties: full_name, status_label, is_available, years_of_service, get_specialties_list()

### StaffSchedule Model
- Fields: staff_id (FK StaffMember), name, is_default, effective_from/until (dates), is_active
- One staff member can have multiple schedules (seasonal, temporary)
- Only one default schedule per staff member

### StaffWorkingHours Model
- Fields: schedule_id (FK StaffSchedule), day_of_week (0=Mon, 6=Sun)
- Times: start_time, end_time, break_start, break_end
- is_working (false = day off)
- Unique constraint: (schedule_id, day_of_week)
- Property: working_minutes (excludes break)

### StaffTimeOff Model
- Fields: staff_id (FK StaffMember), leave_type (vacation/sick/personal/training/other)
- Dates: start_date, end_date, is_full_day, start_time, end_time (for partial days)
- Status: pending/approved/rejected/cancelled
- Approval: approved_by (UUID), approved_at (datetime)
- Fields: reason, notes
- Property: duration_days, conflicts_with(start_date, end_date)

### StaffService Model (optional integration with services module)
- Fields: staff_id (FK StaffMember), service_id (UUID, nullable — no hard FK to services)
- service_name (cached), custom_duration (override minutes), custom_price (override)
- is_primary (specialty), is_active
- Unique constraint: (staff_id, service_id)

### Key Relationships
- StaffMember -> StaffRole (FK, SET NULL on delete)
- StaffMember -> StaffSchedule (one-to-many, CASCADE)
- StaffSchedule -> StaffWorkingHours (one-to-many, CASCADE)
- StaffMember -> StaffTimeOff (one-to-many, CASCADE)
- StaffMember -> StaffService (one-to-many, CASCADE)

### Architecture Notes
- NO hard dependency on services module — StaffService.service_id is nullable UUID
- Other modules (appointments, commissions) depend on staff, not the other way around
- Availability check: active + bookable + not on approved time off + within working hours
- API endpoints /api/search and /api/available for cross-module integration
"""

SOPS = [
    {
        "id": "list_staff",
        "triggers_es": ["listar personal", "ver empleados", "quienes trabajan"],
        "triggers_en": ["list staff", "show employees", "who works here"],
        "steps": ["list_staff"],
        "modules_required": ["staff"],
    },
    {
        "id": "check_staff_availability",
        "triggers_es": ["disponibilidad personal", "quien esta disponible", "personal disponible"],
        "triggers_en": ["staff availability", "who is available", "available staff"],
        "steps": ["check_staff_availability"],
        "modules_required": ["staff"],
    },
    {
        "id": "manage_time_off",
        "triggers_es": ["solicitar vacaciones", "pedir dias libres", "aprobar permiso"],
        "triggers_en": ["request time off", "request vacation", "approve leave"],
        "steps": ["list_time_off", "approve_time_off"],
        "modules_required": ["staff"],
    },
    {
        "id": "view_schedules",
        "triggers_es": ["ver horarios", "horario de trabajo", "turnos"],
        "triggers_en": ["view schedules", "work schedule", "shifts"],
        "steps": ["get_staff_schedule"],
        "modules_required": ["staff"],
    },
]
