# School Transport

**Odoo 19 Community module — buses, routes, stops, and per-student transport assignments.**

Depends on `school_base`, `mail`.

## Models

| Model | Summary |
|---|---|
| `school.transport.vehicle` | Bus record (plate number unique, model, capacity, driver, state). |
| `school.transport.route` | Named route with unique code, assigned vehicle, ordered stops, and state (draft / active / inactive). |
| `school.transport.stop` | Stop on a route: name, sequence, pickup time. Cascade-deleted with its route. |
| `school.transport.assignment` | Student ↔ route link for a given academic year, with pickup and drop-off stops. One active assignment per student per year. |

## Constraints

- Vehicle `plate_number` unique.
- Route `code` unique.
- Stop pickup time ∈ `[0, 24)`.
- Assignment's pickup / drop-off stops must belong to the chosen route.
- Partial unique index (EXCLUDE … WHERE state='active') enforces one active assignment per `(student_id, academic_year_id)`.

## Menus

- **School → Transport → Routes / Assignments / Vehicles**

## Security

Uses `school_base`'s Reader / User / Manager groups. User manages assignments; Manager manages the catalog (vehicles, routes, stops).

## Demo data

- 2 vehicles (Toyota Coaster 30-seater ABC-1234, Hino Dutro 25-seater XYZ-9876).
- 2 active routes (North / South) with 3 stops each.
- 3 active assignments — Alice + Ben both on the North route, Dino on the South route, all for AY 2026-2027.

## Tests

```bash
odoo-bin -d school_dev -i school_transport --test-enable --test-tags=/school_transport --stop-after-init
```

Covers: route creation / code uniqueness / stop count / state lifecycle, vehicle plate uniqueness, assignment creation / stop-on-route check / one-active-per-student-per-year / two students on same route / lifecycle.
