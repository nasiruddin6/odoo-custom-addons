# CRM Client Visit & Employee Attendance Management

## 1. Overview

- **Module:** CRM Client Visit & Employee Attendance Management (`crm_client_visit_attendance`)
- **Description:** Plans and tracks client visits, team attendance, outcomes, notifications, and visit analysis from CRM.
- **Odoo version:** 18.0

## 2. Features

- Schedule visits from CRM opportunities or the Client Visits menu.
- Confirm, check in, check out, and submit visits for manager approval.
- Create visit attendance for the team and HR attendance after approval.
- Send visit confirmation emails and create related CRM activities.
- Record outcomes, follow-up details, attachments, and remarks.
- Analyze visits in graph, pivot, and list views.

## 3. Installation

1. Copy `crm_client_visit_attendance` into the Odoo addons path.
2. Restart Odoo, update the Apps list, and install **CRM Client Visit & Employee Attendance Management**.
3. Go to `Odoo → Settings → Users & Companies → Users`, open the user, and enable **CRM Visit User** or **CRM Visit Manager** under **Access Rights**.

**Required dependencies:** `base`, `crm`, `hr`, `hr_attendance`, `mail`, `web`, and `contacts`.

## 4. UI Testing

Use a user with **CRM Visit Manager** access for the complete approval workflow.

#### Test: Schedule and Confirm a Visit

**Go to:** `Odoo → CRM → Sales → My Pipeline`

**Steps:**

1. Open an opportunity linked to a company contact.
2. Click **Schedule Visit**.
3. Set **Team Leader**, optional **Team Members**, **Visit Type**, **Planned Date & Time**, **Expected Duration (Hours)**, and **Purpose**.
4. Click **Confirm Visit**.

**Expected Result:** The visit receives a reference, moves from **Draft** to **Planned**, creates a related CRM activity, and queues confirmation emails for the client and visit team when email addresses are available.

#### Test: Check In, Check Out, and Approve

**Go to:** `Odoo → CRM → Client Visits → All Visits`

**Steps:**

1. Open a visit in **Planned** status and click **Check In**.
2. Check the **Attendance** tab; one record should exist for the **Team Leader** and each **Team Member**.
3. Click **Check Out**. The visit moves to **Under Review** and records the check-out time and duration.
4. Open the **Outcome** tab and enter the visit result as needed.
5. Click **Approve**.
6. Check `Odoo → Attendances → Overview` and `Odoo → CRM → Client Visits → Visit Attendance`.

**Expected Result:** The visit moves through **In Progress** and **Under Review** to **Completed**. Approval creates linked HR attendance records for all visit employees. Visit attendance shows check-in, check-out, duration, and attendance type.

#### Test: Reject a Visit

**Go to:** `Odoo → CRM → Client Visits → All Visits`

**Steps:**

1. Open a visit in **Under Review** status.
2. Click **Reject**.
3. Check the visit status and its **Attendance** tab.

**Expected Result:** The visit moves to **Cancelled**, and its visit attendance records are removed without creating HR attendance.

#### Test: Send a Visit Email

**Go to:** `Odoo → CRM → Client Visits → All Visits`

**Steps:**

1. Open a visit whose client and employees have email addresses.
2. Click **Send**.
3. Review the **Client Visit: Confirmation Email** in the email composer and click **Send**.

**Expected Result:** A visit confirmation message containing the visit details is queued or sent to the configured recipients.

#### Test: Outcomes, Attachments, and Remarks

**Go to:** `Odoo → CRM → Client Visits → All Visits`

**Steps:**

1. Open a visit in **Under Review** or **Completed** status.
2. In **Outcome**, set **Outcome**, **Interest Level (%)**, **Next Action Required**, **Expected Value**, **Visit Notes**, and **Next Action** where applicable.
3. In **Attachments**, upload files under **Photos**, **Documents**, **Signed Forms**, or **Visiting Cards**.
4. In **Remarks**, enter **Internal Notes** and **Client Remarks**, then save.

**Expected Result:** The entered outcome, follow-up information, files, and remarks remain linked to the visit. Uploaded files appear through the **Attachments** smart button.

#### Test: Visit Analysis

**Go to:** `Odoo → CRM → Reporting → Visit Analysis`

**Steps:**

1. Review the default graph view.
2. Switch to the pivot view and review **Expected Value**, **Interest Level**, and **Actual Duration**.
3. Switch to the list view and review visit reference, client, team leader, type, date, and status.

**Expected Result:** Existing visit data is available in graph, pivot, and list views for analysis.

## 5. Screenshots

Check screenshots of:

- The **Schedule Visit** form from an opportunity.
- The visit workflow and **Check-In/Out Details**.
- The **Attendance**, **Outcome**, **Attachments**, and **Remarks** tabs.
- **Visit Attendance** and the linked HR attendance.
- **Visit Analysis** graph, pivot, and list views.

## 6. Changelog

- **18.0.1.0.2** — Current Odoo 18 release.
