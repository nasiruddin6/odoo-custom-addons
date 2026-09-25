# Employee Attendance Report

Excel attendance report for Odoo 17. Pick one employee and a date range, then download a workbook with daily check-in, check-out, leave, holiday, and absence rows.

Server: `http://localhost:8017`

Depends on Employees, Attendances, and Time Off. The Python package `xlsxwriter` must be installed.

## Install

1. Open Apps and click **Update Apps List**.
2. Search for `Employee Attendance Report` and click **Install**.

## What the report includes

- Working days from the employee working schedule
- Present, absent, late check-in, and early check-out
- Approved time off and public holidays
- Check-in and check-out times in the user timezone

## UI check

1. Create an employee with a working schedule, then record at least one attendance and, if you want, one approved time off inside the date range.
2. Open **Attendances → Reporting → Employee Attendance Report**.
3. Confirm a dialog opens with Employee, From, and To.
4. Select the employee and a date range that contains the attendance, then click **Export Excel**.
5. Open the file and confirm the company header, the employee block, and one row per date with check-in, check-out, hours, and status.
6. Click **Cancel** on a fresh dialog and confirm it closes without a download.

If `xlsxwriter` is missing, the export raises an error. Install it in the same Python environment that runs Odoo, then retry.
