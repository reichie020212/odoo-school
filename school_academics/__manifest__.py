{
    "name": "School Academics",
    "version": "19.0.1.0.0",
    "summary": "Curriculum, courses, sessions, and attendance for the School Management System",
    "description": """
School Academics
================
Adds the academic layer on top of ``school_base``:

* ``school.subject`` — curriculum catalog.
* ``school.course`` — concrete course offering (subject × term × teacher × classroom)
  with auto-enrolled students and a weekly schedule pattern.
* ``school.course.schedule.rule`` — weekly meeting pattern used to materialise
  ``calendar.event`` sessions.
* ``calendar.event`` (extended) — sessions carry school context, per-session
  attendance records, and a "Mark all present" action.
* ``school.attendance`` — per-student, per-session attendance with
  present/absent/late/excused states.
""",
    "author": "odoo-school",
    "website": "https://github.com/",
    "license": "LGPL-3",
    "category": "Education",
    "depends": [
        "school_base",
        "calendar",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/school_subject_views.xml",
        "views/school_course_schedule_rule_views.xml",
        "views/school_course_views.xml",
        "views/calendar_event_views.xml",
        "views/school_attendance_views.xml",
        "views/school_academics_menus.xml",
    ],
    "demo": [
        "demo/school_subject_demo.xml",
        "demo/school_course_demo.xml",
        "demo/school_attendance_demo.xml",
    ],
    "application": False,
    "installable": True,
    "auto_install": False,
}
