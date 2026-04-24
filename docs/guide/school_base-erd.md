# `school_base` — Entity Relationship Diagram

```mermaid
erDiagram
    RES_PARTNER ||--o{ SCHOOL_CLASSROOM : "student_classroom_id"
    RES_PARTNER }o--o{ RES_PARTNER : "student_guardian_ids / student_ward_ids (M:N, symmetric via school_student_guardian_rel)"
    SCHOOL_ACADEMIC_YEAR ||--o{ SCHOOL_ACADEMIC_TERM : "term_ids"
    SCHOOL_ACADEMIC_YEAR ||--o{ SCHOOL_CLASSROOM : "classroom_ids"
    HR_EMPLOYEE ||--o{ SCHOOL_CLASSROOM : "homeroom_teacher_id / teacher_homeroom_ids"

    RES_PARTNER {
        boolean is_student
        boolean is_guardian
        char student_admission_number "unique, seq school.student.admission"
        date student_date_of_birth
        selection student_gender "male / female"
        date student_admission_date
        selection student_status "enrolled / on_leave / graduated / withdrawn"
        many2one student_classroom_id "-> school.classroom"
        many2one student_academic_year_id "-> school.academic.year (related, stored)"
        text student_medical_notes
        selection student_blood_type "A+/A-/B+/B-/AB+/AB-/O+/O-/unknown"
        char student_emergency_contact_name
        char student_emergency_contact_phone
    }

    HR_EMPLOYEE {
        boolean is_teacher
        char teacher_employee_number "unique"
        text teacher_qualifications
        date teacher_hire_date
        one2many teacher_homeroom_ids "inverse of school.classroom.homeroom_teacher_id"
    }

    SCHOOL_ACADEMIC_YEAR {
        char name
        char code "unique"
        date date_start
        date date_end
        selection state "draft / active / archived"
        boolean is_current "computed, searchable"
        one2many term_ids
        one2many classroom_ids
    }

    SCHOOL_ACADEMIC_TERM {
        char name
        char code "unique within academic_year_id"
        integer sequence
        many2one academic_year_id "-> school.academic.year"
        date date_start
        date date_end
    }

    SCHOOL_CLASSROOM {
        char name
        char code "unique within academic_year_id"
        selection grade_level "k / 1 .. 12"
        char section
        integer capacity
        many2one academic_year_id "-> school.academic.year"
        many2one homeroom_teacher_id "-> hr.employee (is_teacher = True)"
        one2many student_ids "inverse of res.partner.student_classroom_id"
        integer student_count "computed, stored"
    }
```

## Notes

- **Guardian ↔ Ward** is a symmetric many-to-many on `res.partner` implemented with a single relation table `school_student_guardian_rel` and swapped columns — assigning a guardian on a student automatically shows up as a ward on the guardian.
- **Access control** is group-based (Reader / User / Manager) bound to the Odoo 19 `res.groups.privilege` "School Management". Record rules are deferred to later modules.
- **Admission numbers** come from `ir.sequence` code `school.student.admission` (format configurable in the UI under School → Configuration → Admission Number Sequence). Default pattern: `<year>-NNNNN`, e.g. `2026-00001`.
- **Homeroom teacher is optional** on classroom. The relation is modelled canonically on `school.classroom.homeroom_teacher_id`; the `hr.employee.teacher_homeroom_ids` one2many is the inverse view.

## Downstream extensions (added by later modules)

Per repo convention, when a later module extends an `_inherit` target defined here, the addition is documented back on this ERD. Current known extensions:

- **`res.partner.canteen_allergy_tag_ids`** — `Many2many('school.canteen.dietary.tag')`. Added by `school_canteen`; purchases block when the student's allergies intersect the items' dietary tags.

For the full picture of each downstream extension, see the module's own ERD under `docs/guide/`:

- `school_academics-erd.md` — courses reference `res.partner` students as m2m and `hr.employee` as teacher.
- `school_fees-erd.md` — fee enrollments reference `res.partner` students.
- `school_canteen-erd.md` — wallets reference `res.partner` students, allergy tags extend `res.partner`.
- `school_shop-erd.md` — sales reference `res.partner` as buyer.
- `school_transport-erd.md` — assignments reference `res.partner` students.
- `school_exams-erd.md` — exam results and report cards reference `res.partner` students.
