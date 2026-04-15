# Staff (module: `staff`)

Staff profiles, roles, schedules, time off, and service assignments.

## Purpose

The Staff module is the base HR module. It stores employee profiles and is a dependency for `attendance`, `timesheets`, `payroll`, `time_control`, `commissions`, `training`, `leave`, and `workforce_planning`.

Managers use it to create and manage employee profiles, assign roles (with permission scopes), define working hour schedules, approve time off requests, and link staff members to the services they can perform (optional `services` integration).

## Models

- `StaffSettings` — Singleton per hub. Default work start/end times, break duration, min advance booking (days), max daily hours, overtime threshold (hours/week), display flags (photos, bio, allow staff selection), notification flags.
- `StaffRole` — Named role definition with permission set (maps to `ROLE_PERMISSIONS` keys).
- `StaffMember` — Employee profile: name, email, phone, photo, role, is_active, hire date, hourly rate, bio, color (for calendar display).
- `StaffSchedule` — Named availability schedule assigned to a staff member.
- `StaffWorkingHours` — Working hour blocks within a `StaffSchedule` (day of week, start time, end time).
- `StaffTimeOff` — Time off request from an employee: date range, reason, status (pending/approved/rejected/cancelled).
- `StaffService` — Link between a staff member and a service they can perform (optional, nullable `service_id`).

## Routes

`GET /m/staff/` — Staff dashboard with headcount stats
`GET /m/staff/staff_list` — Staff member list
`GET /m/staff/schedules` — Schedule management
`GET /m/staff/roles` — Role management
`GET /m/staff/settings` — Module settings

## Events

### Consumed

`appointment.created` — Logged for traceability when an appointment is created for a staff member.

## Hooks

### Emitted (actions other modules can subscribe to)

`staff.member_created` — Fired after a staff member is created.
`staff.time_off_approved` — Fired after a time off request is approved.

## Pricing

Free.
