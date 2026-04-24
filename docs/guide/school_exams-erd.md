# `school_exams` — Entity Relationship Diagram

```mermaid
erDiagram
    SCHOOL_GRADING_SCALE ||--o{ SCHOOL_GRADING_SCALE_BAND : "band_ids"
    SCHOOL_EXAM }o--|| SCHOOL_COURSE : "course_id"
    SCHOOL_EXAM }o--|| SCHOOL_EXAM_TYPE : "exam_type_id"
    SCHOOL_EXAM }o--o| SCHOOL_GRADING_SCALE : "grading_scale_id (optional)"
    SCHOOL_EXAM ||--o{ SCHOOL_EXAM_RESULT : "result_ids"
    SCHOOL_EXAM_RESULT }o--|| RES_PARTNER : "student_id (is_student)"
    SCHOOL_REPORT_CARD ||--o{ SCHOOL_REPORT_CARD_LINE : "line_ids"
    SCHOOL_REPORT_CARD }o--|| RES_PARTNER : "student_id (is_student)"
    SCHOOL_REPORT_CARD }o--|| SCHOOL_ACADEMIC_TERM : "term_id"
    SCHOOL_REPORT_CARD_LINE }o--|| SCHOOL_COURSE : "course_id"

    SCHOOL_GRADING_SCALE {
        char name
        char code "unique"
        boolean is_default "exactly one at a time"
        boolean active
    }

    SCHOOL_GRADING_SCALE_BAND {
        many2one scale_id "-> school.grading.scale (cascade)"
        char letter "e.g. A, 1.00"
        float min_percentage "0-100 inclusive"
        float gpa_value
        integer sequence
    }

    SCHOOL_EXAM_TYPE {
        char name
        char code "unique"
        float default_weight "percent contribution seed"
        integer sequence
        boolean active
    }

    SCHOOL_EXAM {
        char name "computed, editable"
        many2one course_id "-> school.course"
        many2one exam_type_id "-> school.exam.type"
        date date
        float max_score
        float weight "% weight in course grade, seeded from type"
        many2one grading_scale_id "optional override"
        many2one effective_scale_id "computed: override || default"
        selection state "draft / published / closed"
        integer result_count "computed, stored"
        float average_percentage "computed, stored"
    }

    SCHOOL_EXAM_RESULT {
        many2one exam_id "-> school.exam (cascade)"
        many2one student_id "-> res.partner (is_student)"
        many2one course_id "related from exam_id, stored"
        float max_score "related readonly"
        float score
        float percentage "computed, stored"
        char letter_grade "computed via exam scale"
        float gpa_value "computed"
        char remark
    }

    SCHOOL_REPORT_CARD {
        char name "computed"
        many2one student_id "-> res.partner (is_student)"
        many2one term_id "-> school.academic.term"
        many2one academic_year_id "related"
        float overall_percentage "computed, stored"
        float overall_gpa "computed, stored"
        char overall_letter "computed, stored"
        selection state "draft / final / distributed"
        text teacher_remark
        date issue_date
    }

    SCHOOL_REPORT_CARD_LINE {
        many2one report_card_id "-> school.report.card (cascade)"
        many2one course_id "-> school.course"
        many2one subject_id "related from course, stored"
        many2one teacher_id "related from course, stored"
        float percentage "computed, stored (weighted)"
        char letter_grade "computed"
        float gpa_value "computed"
        boolean is_incomplete "computed"
        char teacher_remark "editable"
    }
```

## Notes

- **Default scale** — Exactly one `school.grading.scale` has `is_default = True`. Enforced via `@api.constrains`, not a partial unique index.
- **Band lookup** — `scale.band_for_percentage(pct)` returns the highest-`min_percentage` band whose threshold is ≤ `pct`. Below every band → returns the lowest band (so `letter_grade` is always produced).
- **Effective scale** — `exam.effective_scale_id` is `grading_scale_id || get_default_scale()`. Results always pick up the correct scale for computed grades.
- **Weighted course grade** — Σ(r.percentage × r.exam.weight) / Σ(r.exam.weight) over the student's graded results (exam state ∈ {published, closed}, weight > 0) for the course. Incomplete lines (no graded exams) skip from the overall aggregate.
- **Overall GPA** — mean of line `gpa_value` for non-incomplete lines; overall letter looked up against the default scale.
- **Unique constraints** — scale code, exam-type code, (exam, student) results, (student, term) report cards, (report_card, course) lines.
- **PDF** — `ir.actions.report` (`report_type="qweb-pdf"`) on `school.report.card`, bound via `binding_model_id` so "Print → Report Card" appears on the record.
```
