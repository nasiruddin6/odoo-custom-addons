# Employee Attendance Report

## Overview
Comprehensive employee attendance reporting module for Odoo 19 that generates detailed Excel reports with advanced attendance analytics.

## Features

### Core Functionality
- Date range based attendance tracking
- Multi-employee support
- Automatic working days calculation based on employee shift
- Leave and holiday integration
- Timezone-aware time tracking

### Attendance Metrics
- **Total Working Days**: Calculated based on employee's shift schedule
- **Present Days**: Days with attendance records (excluding leaves/holidays)
- **Absent Days**: Missing attendance on working days
- **Late Check-ins**: Arrivals after shift start time
- **Early Check-outs**: Departures before shift end time
- **Leave Days**: Approved leaves within date range
- **Holidays**: Public holidays from resource calendar
- **Overtime Hours**: Hours worked beyond standard 8-hour day

### Status Classification
- **Present**: Normal attendance
- **Late**: Check-in after shift start
- **Early Checkout**: Check-out before shift end
- **Late & Early Checkout**: Both conditions met
- **Leave**: Employee on approved leave
- **Holiday**: Public holiday
- **Absent**: No attendance on working day
- **Non-Working Day**: Weekend or non-scheduled day

### Excel Report Features
- Company header with logo and contact information
- Employee details summary
- Date-wise attendance table with:
  - Date and day of week
  - Check-in and check-out times (user timezone)
  - Working hours and extra hours
  - Attendance status
- Professional formatting with borders and styles
- Auto-sized columns for better readability
- Language-specific date/time formatting

## Technical Details

### Dependencies
- `hr`: Base HR module
- `hr_attendance`: Attendance management
- `hr_holidays`: Leave management

### Python Dependencies
- `xlsxwriter`: Excel file generation
- `pytz`: Timezone handling

### Models
- **attendance.report.wizard**: Transient model for report generation

### Access Rights
- Available to all users (can be customized via security groups)

## Usage

1. Navigate to: **Attendances > Reporting > Employee Attendance Report**
2. Select employee
3. Choose date range (From - To)
4. Click **Export Excel**
5. Download automatically generated report

## Configuration

### Shift Configuration
The module respects employee shift settings from `resource.calendar`:
- Working days (Mon-Sun configuration)
- Shift start and end times
- Default: 8:00 AM - 5:00 PM if no calendar assigned

### Leave Management
Integrates with Odoo's leave system:
- Only approved leaves counted
- Leave dates excluded from present days calculation
- Leave status shown in report

### Holiday Management
Uses resource calendar leaves:
- Global holidays (company-wide)
- Employee-specific holidays
- Calendar-based holiday tracking

## Timezone Handling
All times are converted from UTC (database) to user's timezone for accurate reporting.

## Date Format
Automatically formats dates and times based on user's language settings from `res.lang`.

## Version
**19.0.1.0.0**

## Author
TecTISE Solutions

## License
LGPL-3

