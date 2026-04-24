# `school_academics` — Entity Relationship Diagram

```mermaid
erDiagram
    SCHOOL_SUBJECT ||--o{ SCHOOL_COURSE : "course_ids"
    SCHOOL_COURSE ||--o{ SCHOOL_COURSE_SCHEDULE_RULE : "schedule_rule_ids"
    SCHOOL_COURSE ||--o{ CALENDAR_EVENT : "session_ids"
    SCHOOL_COURSE }o--|| SCHOOL_ACADEMIC_TERM : "term_id"
    SCHOOL_COURSE }o--|| SCHOOL_CLASSROOM : "classroom_id"
    SCHOOL_COURSE }o--|| HR_EMPLOYEE : "teacher_id"
    SCHOOL_COURSE }o--o{ RES_PARTNER : "student_ids (M:N school_course_student_rel)"
    CALENDAR_EVENT ||--o{ SCHOOL_ATTENDANCE : "school_attendance_ids"
    SCHOOL_ATTENDANCE }o--|| RES_PARTNER : "student_id (is_student)"

    SCHOOL_SUBJECT {
        char name
        char code "unique"
        text description
        float default_weekly_hours
        boolean active
    }

    SCHOOL_COURSE {
        char name "computed, editable"
        many2one subject_id "-> school.subject"
        many2one term_id "-> school.academic.term"
        many2one academic_year_id "related from term_id, stored"
        many2one teacher_id "-> hr.employee (is_teacher)"
        many2one classroom_id "-> school.classroom"
        many2many student_ids "-> res.partner (is_student)"
        integer student_count "computed, stored"
        integer session_count "computed, stored"
        selection state "draft / open / closed"
        integer color
    }

    SCHOOL_COURSE_SCHEDULE_RULE {
        many2one course_id "-> school.course (cascade)"
        selection weekday "mon / tue / wed / thu / fri / sat / sun"
        float time_start "24h, e.g. 10.5 = 10:30"
        float duration "hours"
        char location "optional, defaults to classroom name"
    }

    CALENDAR_EVENT {
        many2one school_course_id "-> school.course (set null)"
        one2many school_attendance_ids "-> school.attendance"
        selection school_session_state "scheduled / completed / cancelled"
        integer school_attendance_count "computed, stored"
        integer school_present_count "computed, stored"
    }

    SCHOOL_ATTENDANCE {
        many2one student_id "-> res.partner (is_student)"
        many2one session_id "-> calendar.event (cascade)"
        many2one course_id "related from session, stored"
        selection state "present / absent / late / excused"
        char note
        many2one recorded_by_id "-> res.users"
        datetime recorded_at
    }
```

## Notes

- **Auto-enrollment** runs in `school.course.create()`: any course created without an explicit `student_ids` value is seeded from `classroom_id.student_ids`. Subsequent changes to the classroom roster do **not** auto-propagate — the **Re-sync Roster** action on the course is the explicit way to pull in new students (or `action_reset_enrollment()` programmatically).
- **Sessions are regular `calendar.event` records**, extended with a few school fields. The inverse field `session_ids` on `school.course` is a One2many to `calendar.event` filtered by `school_course_id`.
- **Materialise Sessions** (`school.course.action_materialize_sessions`) walks `term_id.date_start → term_id.date_end`, iterates the course's schedule rules per weekday, and creates a `calendar.event` for every `(date, time_start)` tuple that doesn't already exist — so the action is safe to re-run.
- **Attendance** enforces `UNIQUE(student_id, session_id)` at the DB level and verifies enrollment at the ORM level (`@api.constrains`). The `course_id` field is a stored related for fast filtering.
- **"Mark All Present"** (`calendar.event.action_school_mark_all_present`) only creates rows for enrolled students that don't already have one — it never overwrites existing attendance — and flips the session to `completed`.
```
