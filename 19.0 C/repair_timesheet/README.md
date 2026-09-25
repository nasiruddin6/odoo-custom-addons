# Repair Timesheet

Track technician time on repair orders and turn that time into timesheet lines.

Depends on `repair`, `hr`, and `hr_timesheet`.

## What it does

- Add one or more technicians on a repair order (`technician_ids`) and an estimated duration.
- **Generate Technician Timesheet** creates timesheet lines for the assigned technicians.
- A **Timesheet** tab on the repair order lists date, employee, description, and hours.
- A repair timesheet product is set in Settings and used for those entries.
- The repair order print report includes the timesheet.

## How to check the UI

1. Install **Repair Timesheet** from Apps.
2. Open **Repairs → Repair Orders** and open or create an order.
3. Set technicians and estimated time on the form.
4. Click **Generate Technician Timesheet** and open the **Timesheet** tab. Confirm date, employee, and hours.
5. Open **Settings → Repair** and check **Repair Timesheet Product**.
6. Print the repair order and confirm the timesheet section is on the report.
