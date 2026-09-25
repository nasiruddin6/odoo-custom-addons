# NN Fund Management

Fund request module for Odoo 17. Create a request for a contact, then move it through Draft, Submitted, Approved, or Rejected. Request numbers come from a sequence, a PDF can be printed, and status changes are logged in the chatter.

Server: `http://localhost:8017`

## Install

1. Open Apps and click **Update Apps List**.
2. Search for `NN Fund Management` and click **Install**.
3. Turn on **Load demonstration data** if you want the sample requests for John Doe and Jane Smith.

## User groups

The Approve and Reject buttons are visible only to **Fund Manager**. Even the administrator does not see them until that group is assigned.

1. Go to **Settings → Users & Companies → Users**.
2. Open your user and set **Finance → Fund Manager**.
3. Save and refresh the browser.

| Group | What they can do |
| --- | --- |
| Fund User | Create a request and click Submit |
| Fund Manager | Approve, Reject, Reset to Draft, and delete |

## UI check

### 1. Menu and list

1. Open **Fund Management → Fund Requests**.
2. Confirm the list shows Request Number, Request Date, Employee, Amount, and Status.
3. Status badge colors: Draft is blue, Submitted is yellow, Approved is green, Rejected is red.

### 2. New request

1. Click **New**.
2. Select a contact in **Employee Name**.
3. Set **Amount** to `0` or less and save. Odoo must show an error that the amount has to be greater than 0.
4. Set Amount to `1500`, fill in **Purpose**, and save.
5. Confirm **Request Number** changed from `New` to a sequence such as `FR/...`.
6. Confirm the chatter is visible under the form.

### 3. Workflow

1. In Draft, only **Submit** and **Print Report** are shown.
2. Click **Submit**. Status becomes Submitted and the chatter logs “Submitted”.
3. As Fund Manager, click **Approve**. Status becomes Approved and the chatter logs “Approved”.
4. Create another request, submit it, and click **Reject**. Status becomes Rejected.
5. On the rejected request, click **Reset to Draft**. Submit is available again.
6. On an approved request, Submit, Approve, Reject, and Reset to Draft stay hidden.

### 4. Print and search

1. On a saved request, click **Print Report**. A PDF downloads.
2. On the list, use the status filters (Draft, Submitted, Approved, Rejected) and confirm the list updates.
