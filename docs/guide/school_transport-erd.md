# `school_transport` — Entity Relationship Diagram

```mermaid
erDiagram
    SCHOOL_TRANSPORT_VEHICLE ||--o{ SCHOOL_TRANSPORT_ROUTE : "route_ids"
    SCHOOL_TRANSPORT_ROUTE ||--o{ SCHOOL_TRANSPORT_STOP : "stop_ids"
    SCHOOL_TRANSPORT_ROUTE ||--o{ SCHOOL_TRANSPORT_ASSIGNMENT : "assignment_ids"
    SCHOOL_TRANSPORT_ASSIGNMENT }o--|| RES_PARTNER : "student_id (is_student)"
    SCHOOL_TRANSPORT_ASSIGNMENT }o--|| SCHOOL_ACADEMIC_YEAR : "academic_year_id"
    SCHOOL_TRANSPORT_ASSIGNMENT }o--o| SCHOOL_TRANSPORT_STOP : "pickup_stop_id / dropoff_stop_id"

    SCHOOL_TRANSPORT_VEHICLE {
        char name "computed"
        char plate_number "unique"
        char model
        integer capacity
        many2one driver_id "-> hr.employee"
        selection state "active / in_repair / retired"
        boolean active
    }

    SCHOOL_TRANSPORT_ROUTE {
        char name
        char code "unique"
        many2one vehicle_id
        integer stop_count "computed, stored"
        integer assignment_count "computed, stored — active only"
        selection state "draft / active / inactive"
        boolean active
    }

    SCHOOL_TRANSPORT_STOP {
        many2one route_id "cascade"
        char name
        integer sequence
        float pickup_time "24h, 0 ≤ x < 24"
        char notes
    }

    SCHOOL_TRANSPORT_ASSIGNMENT {
        char name "computed"
        many2one student_id "-> res.partner (is_student)"
        many2one route_id
        many2one academic_year_id
        many2one pickup_stop_id "must belong to route_id"
        many2one dropoff_stop_id "must belong to route_id"
        selection state "draft / active / ended"
    }
```

## Notes

- **One active assignment per (student, year).** Enforced by a PostgreSQL `EXCLUDE USING btree` partial constraint filtered on `state = 'active'`. A student can have multiple historical (draft / ended) records for the same year, but only one concurrently active.
- **Stop-must-belong-to-route** check is an `@api.constrains` on assignment — the view already domain-filters the stops, but the constraint is the source of truth.
- **Route and stop cascade delete** — removing a route drops its stops (and you'd normally unlink or end its assignments manually first).
- **No sale / account coupling.** Transport fees, if billed, would be handled in `school_fees` via a structure referencing a dedicated product. Keeping transport lean makes the module reusable for schools that bundle transport into tuition vs charge separately.
```
