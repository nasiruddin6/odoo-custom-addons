# Employee Attendance Report

Export an Excel attendance report for selected employees over a date range.

Depends on `hr`, `hr_attendance`, and `hr_holidays`.

## What it does

- Wizard filters: date range and employees.
- Day-level status such as present, absent, late check-in, early check-out, leave, and public holiday.
- Worked hours and overtime against the employee shift.
- Menu under attendance reporting.

## How to check the UI

1. Create attendance check-in and check-out for a few employees, plus one approved leave and a working day with no attendance.
2. Open **Attendances → Reporting → Employee Attendance Report**.
3. Set the date range and employees, then click **Export Excel**.
4. In the file, confirm present days, a late or early line if the times differ from the shift, the leave day, and the absent working day.
5. Repeat with a single employee and a short range so the totals are easy to count by hand.
