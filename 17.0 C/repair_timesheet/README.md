# Repair Timesheet

Adds technicians and a timesheet tab to repair orders in Odoo 17. When a service product is set in Settings and the repair is linked to a sales order, the total hours are written onto that product line.

Server: `http://localhost:8017`

Depends on Repair, Employees, and Timesheets.

## Install

1. Open Apps and click **Update Apps List**.
2. Search for `Repair Timesheet` and click **Install**.

## Setup

1. Open **Settings**.
2. In the **Repair** block, set **Repair Timesheet Product**. The product type must be Service.
3. Save.

## UI check

### 1. Repair form

1. Open the **Repairs** app and open a repair order, or click **New**.
2. Next to Tags, confirm **Technicians** and **Estimated Time (hours)** are visible.
3. Tag one or more employees, enter an estimated time, and save.

### 2. Timesheet tab

1. Open the **Timesheet** notebook page (it sits after Parts).
2. Add a line with Date, Employee, Description, and Hours, then save.
3. Click **Generate Technician Timesheet**. One line is created per technician, using the estimated time.

### 3. Hours on the sales order

1. Link a sales order on the repair (`sale_order_id`).
2. With hours on the timesheet, the service product from Settings is added or updated on the sales order.
3. Confirm the line description lists hours per employee.

### 4. Print

1. Print the repair order.
2. Confirm the printout includes the technicians and the timesheet section.
