# Employee Attendance Report

## 1. Module Overview

- **Module name:** Employee Attendance Report (`employee_attendance_report`)
- **What it does:** Generates an Excel attendance report for one employee and a selected date range.
- **Main purpose:** Summarize attendance, working hours, absences, late arrivals, early check-outs, approved time off, public holidays, and overtime.

## 2. Odoo Version

- Odoo 18.0

## 3. Features

- Excel report by employee and date range.
- Company and employee details in the report header.
- Attendance summary and daily status.
- Working-schedule-based working-day, late, early, and absence checks.
- Approved time off and public holiday integration.
- Employee-timezone and user-language date/time formatting.

## 4. Dependencies

- `hr`
- `hr_attendance`
- `hr_holidays`

## 5. Installation

1. Copy `employee_attendance_report` into the Odoo addons path.
2. Restart Odoo and update the Apps list.
3. Open **Apps**, search for **Employee Attendance Report**, and install it.

## 6. Configuration

No module-specific setting must be enabled.

**Go to:** `Odoo → Employees → Employees → Employees → select an employee → Work Information`

**Steps:**

1. Under **Schedule**, set **Working Hours**.
2. Set the employee **Timezone**.
3. Save the employee.

To edit a schedule, go to `Odoo → Employees → Configuration → Employee → Working Schedules`, open the assigned schedule, and configure its working days and hours.

## 7. How to Test in Odoo UI

#### Test: Generate the Excel Report

**Go to:** `Odoo → Attendances → Reporting → Employee Attendance Report`

**Steps:**

1. Select an **Employee**.
2. Set **From** and **To** dates containing attendance records.
3. Click **Export Excel**.
4. Open the downloaded `Employee_Attendance_Report.xlsx` file.

**Expected Result:**

An Excel file downloads with company details, the selected dates, employee details, attendance totals, and a daily attendance table.

#### Test: Attendance Statuses and Hours

**Go to:** `Odoo → Attendances → Overview`

**Steps:**

1. Click **New** and create completed attendance records for the test employee using **Check In** and **Check Out**.
2. Include records that start after the employee's scheduled start, end before the scheduled finish, and exceed eight worked hours.
3. Return to `Odoo → Attendances → Reporting → Employee Attendance Report`.
4. Export a report covering the test dates.

**Expected Result:**

The daily rows show the applicable statuses: **Present**, **Late**, **Early Checkout**, or **Late & Early Checkout**. Scheduled days without attendance show **Absent**. The report shows working hours, extra hours, and summary totals.

#### Test: Approved Time Off

**Go to:** `Odoo → Time Off → Management → Time Off`

**Steps:**

1. Create a time-off request for the test employee on a scheduled working day.
2. Set the time-off type and dates, then approve the request.
3. Open `Odoo → Attendances → Reporting → Employee Attendance Report`.
4. Export a report covering the approved date.

**Expected Result:**

The date shows **Leave** in the daily table and is included in **Leave Days (Approved)**.

#### Test: Public Holiday

**Go to:** `Odoo → Time Off → Configuration → Public Holidays`

**Steps:**

1. Add a public holiday with a **Name**, **Working Hours**, **Start Date**, and **End Date**.
2. Use the working schedule assigned to the test employee.
3. Open `Odoo → Attendances → Reporting → Employee Attendance Report`.
4. Export a report covering the holiday date.

**Expected Result:**

The date shows **Holiday - [Name]** in the daily table and is included in **Holidays**.

#### Test: Timezone and Date/Time Formatting

**Go to:** `Odoo → Employees → Employees → Employees → select an employee → Work Information`

**Steps:**

1. Confirm the employee's **Timezone** under **Schedule**.
2. Create a completed attendance record from `Odoo → Attendances → Overview`.
3. Export a report that includes the record.
4. Compare the Excel check-in/check-out values with the employee's timezone and the current user's language format.

**Expected Result:**

Check-in and check-out values use the employee's timezone. Dates and times use the current user's Odoo language formats.

## 8. Screenshots

Add screenshots of:

- `Attendances → Reporting → Employee Attendance Report`.
- The completed report wizard before export.
- The generated Excel summary and daily attendance table.

## 9. Technical Notes

- Wizard model: `attendance.report.wizard` (`TransientModel`).
- Source models: `hr.employee`, `hr.attendance`, `hr.leave`, and `resource.calendar.leaves`.
- The wizard is opened by a modal form view and downloads an `ir.attachment` generated with `xlsxwriter`.
- Access is defined in `security/ir.model.access.csv`; the menu is under the standard Attendances Reporting menu.
- Extra hours are calculated as worked hours above eight hours per attendance record.

## 10. Changelog

- **18.0.1.0.0** — Initial Odoo 18 release with Excel export, attendance metrics, time off, holidays, and timezone-aware values.
