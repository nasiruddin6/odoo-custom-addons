# Employee Leave Summary Report

Export an Excel summary of employee time off for a date range, selected employees, and leave status.

Depends on `hr` and `hr_holidays`. Requires the Python package `xlsxwriter`.

## What it does

- Wizard filters: from date, to date, one or more employees, and leave status.
- Excel columns: badge ID, employee name, department, start date, end date, leave type, total days, leave balance, and status.
- Menu is limited to Time Off users.

## How to check the UI

1. Make sure at least one employee has time off in the date range you will use.
2. Open **Time Off → Reporting → Leave Summary Report**.
3. Set from date, to date, employees, and status, then click **Export**.
4. Open the Excel file and match rows to the leaves in Odoo (dates, type, days, status).
5. Run it again with a range that has no leaves and confirm the file still downloads cleanly.
