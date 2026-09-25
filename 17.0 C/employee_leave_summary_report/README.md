# Employee Leave Summary Report

Excel time-off summary for Odoo 17. Filter by dates, employees, and status, then download one row per leave with balance and department.

Server: `http://localhost:8017`

Depends on Employees and Time Off. The Python package `xlsxwriter` must be installed.

## Install

1. Open Apps and click **Update Apps List**.
2. Search for `Employee Leave Summary Report` and click **Install**.

## Report columns

Badge ID, employee name, department, start date, end date, leave type, duration, leave balance, and status.

## UI check

1. Create at least one time-off request for an employee and approve it.
2. Open **Time Off → Reporting → Leave Summary Report**. The menu is limited to **Time Off / Officer**.
3. Confirm the dialog shows From, To, Employees, and Status.
4. Set a date range that covers the leave, select that employee, keep the status filter, and click **Export**.
5. Open the file and confirm the leave row matches the request (dates, type, days, status).
6. Change Status to a value that does not match the leave and export again. That leave must be absent from the file.
7. Click **Cancel** and confirm the dialog closes without a download.

If `xlsxwriter` is missing, the export raises an error. Install it in the same Python environment that runs Odoo, then retry.
