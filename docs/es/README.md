# Staff (módulo: `staff`)

Perfiles de empleados, roles, horarios, ausencias y asignación de servicios.

## Propósito

El módulo Staff es el módulo base de RRHH. Almacena los perfiles de empleados y es una dependencia de `attendance`, `timesheets`, `payroll`, `time_control`, `commissions`, `training`, `leave` y `workforce_planning`.

Los gestores lo usan para crear y gestionar perfiles de empleados, asignar roles (con ámbitos de permisos), definir horarios de trabajo, aprobar solicitudes de ausencia y vincular empleados a los servicios que pueden prestar (integración opcional con `services`).

## Modelos

- `StaffSettings` — Singleton por hub. Horario de entrada/salida por defecto, duración del descanso, antelación mínima de reserva (días), máximo de horas diarias, umbral de horas extra (horas/semana), flags de visualización (fotos, bio, permitir selección de empleado), flags de notificación.
- `StaffRole` — Definición de rol con nombre y conjunto de permisos (mapeado a las claves de `ROLE_PERMISSIONS`).
- `StaffMember` — Perfil de empleado: nombre, email, teléfono, foto, rol, is_active, fecha de contratación, tarifa horaria, bio, color (para visualización en calendario).
- `StaffSchedule` — Horario de disponibilidad con nombre asignado a un empleado.
- `StaffWorkingHours` — Bloques de horas de trabajo dentro de un `StaffSchedule` (día de la semana, hora de inicio, hora de fin).
- `StaffTimeOff` — Solicitud de ausencia de un empleado: rango de fechas, motivo, estado (pending/approved/rejected/cancelled).
- `StaffService` — Vínculo entre un empleado y un servicio que puede realizar (opcional, `service_id` nullable).

## Rutas

`GET /m/staff/` — Panel de personal con estadísticas de plantilla
`GET /m/staff/staff_list` — Lista de empleados
`GET /m/staff/schedules` — Gestión de horarios
`GET /m/staff/roles` — Gestión de roles
`GET /m/staff/settings` — Configuración del módulo

## Eventos

### Consumidos

`appointment.created` — Registrado para trazabilidad cuando se crea una cita para un empleado.

## Hooks

### Emitidos (acciones a las que otros módulos pueden suscribirse)

`staff.member_created` — Se dispara tras crear un empleado.
`staff.time_off_approved` — Se dispara tras aprobar una solicitud de ausencia.

## Precio

Gratuito.
