# CRM Client Visit & Employee Attendance

Plans client visits in Odoo 17 CRM and records attendance from check-in and check-out. Visits move through Draft, Planned, In Progress, Review, and Completed. A manager can approve or reject a visit that is in review.

Server: `http://localhost:8017`

Depends on CRM, Employees, Attendances, and Contacts.

## Install

1. Open Apps and click **Update Apps List**.
2. Search for `CRM Client Visit` and click **Install**.
3. The administrator is added to **CRM Visit Manager**, which also includes **CRM Visit User**.

## UI check

### 1. Menus

Under **CRM**, open **Client Visits** and confirm these entries:

- **My Visits** (visit user)
- **All Visits** (visit manager)
- **Visit Attendance** (visit manager)
- **Reports** (visit manager)

### 2. Create a visit

1. Open **CRM → Client Visits → All Visits** and click **New**.
2. Set the client, visit leader (employee linked to a user), planned date, and visit type.
3. Save. Confirm a sequence number was assigned and the chatter is visible.
4. Switch the form to kanban and calendar from the view switcher and confirm the visit appears.

### 3. Workflow buttons

1. In Draft, click **Confirm Visit**. Status becomes Planned and **Check In** appears.
2. Click **Check In**. Status becomes In Progress and **Check Out** appears. Check-in time is stored on the Check-In/Out page.
3. Click **Check Out**. The visit moves to Review.
4. As a visit manager, click **Approve**. Status becomes Completed.
5. On another visit, use **Reject**, **Cancel**, **Mark as Missed** (only while Planned), and **Reset to Draft** and confirm the statusbar matches the button you clicked.

### 4. Related screens

1. On a visit, open the attendance smart button and confirm a visit attendance record exists after check-in.
2. Open the same customer and the CRM lead and confirm the visit smart button and count.
3. Open the employee form and confirm the visit attendance smart button.
4. Open **CRM → Client Visits → Reports** and confirm the analysis opens in graph, pivot, and list.
