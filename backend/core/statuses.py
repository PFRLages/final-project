# backend/core/statuses.py
# All the class statuses a row can have, using the STUDENT-side labels
# and the colors from my original spreadsheet. The key is what I store in
# the database; the label/color is what the frontend shows.

STUDENT_STATUSES = {
    "attended":         "Present",
    "vacation":         "student vacation",
    "makeup":           "supplementary class",
    "holiday":          "holiday",
    "rest_day":         "rest day",
    "technical":        "technical concern",
    "no_class":         "pre-scheduled class",
    "absent_notice":    "absence with prior notice",
    "absent_late":      "late notification of absence",
    "absent_no_notice": "no-notice absence",
    "teacher_absent":   "teacher unavailability",
}

# Colors taken from my spreadsheet legend (hex, so the frontend can paint rows).
STATUS_COLORS = {
    "attended":         "#FFFFFF",
    "vacation":         "#00E5FF",
    "makeup":           "#3D85C6",
    "holiday":          "#8C9EC4",
    "rest_day":         "#FF0000",
    "technical":        "#F6B26B",
    "no_class":         "#B7B7B7",
    "absent_notice":    "#F4A582",
    "absent_late":      "#A4A6D6",
    "absent_no_notice": "#FFFF00",
    "teacher_absent":   "#93C47D",
}