# Employee Leave Summary Report

## Overview
This module provides a comprehensive Employee Leave Summary Report with Excel export functionality for Odoo 19.

## Features
* Generate leave summary reports for selected employees
* Filter by date range (From Date - To Date)
* Filter by leave status (To Approve, Approved, Refused, etc.)
* Multi-employee selection support
* Professional Excel export with company branding
* Display leave balance information
* Department-wise employee details

## Report Columns
* Badge ID
* Employee Name
* Department
* Leave Start Date
* Leave End Date
* Leave Type
* Total Leave Days
* Leave Balance
* Status

## Usage
1. Navigate to: **Time Off → Reporting → Leave Summary Report**
2. Select date range (From Date and To Date)
3. Choose employees (multiple selection supported)
4. Select leave status filter
5. Click "Export" to generate Excel report

## Technical Details
* **Module Name**: employee_leave_summary_report
* **Odoo Version**: 19.0
* **Dependencies**: hr, hr_holidays
* **External Library**: xlsxwriter

## Installation
Install required Python library:
```bash
pip install xlsxwriter
```

## Author
Tectise

## License
LGPL-3

