# Property Management — Rental and Sales

Odoo 17 app for properties, units, rental contracts, sales contracts, bookings, payment plans, settlements, visits, and maintenance. The administrator is in the Property / Manager group.

Server: `http://localhost:8017`

Depends on Contacts, Employees, CRM, Sales, Maintenance, and Portal.

## Install

1. Open Apps and click **Update Apps List**.
2. Search for `Property Management` and click **Install**.
3. Confirm the **Properties** app icon appears on the home screen.

## UI check

Work through the menus in this order. Each screen should open without a view error, show a list or kanban, and allow New, save, and discard.

### 1. Property and unit

1. Open **Properties → Property Management → Property** and click **New**.
2. Fill the name, save, and confirm kanban, list, and form all open. The chatter is under the form.
3. Open **Properties → Property Management → Unit**, create a unit linked to that property, and save.
4. On the unit kanban, confirm the image, name, property, and state badge render.

### 2. Rental

These menus are for Property / Manager.

1. **Properties → Rental → Contracts**: create a contract, set tenant, property, and unit, and save. Confirm the chatter and the lines in the notebook.
2. **Properties → Rental → Invoices**: the customer-invoice list opens, filtered to rent invoices.
3. **Properties → Rental → Payments**: the payment list opens.
4. **Properties → Rental → Settlements**: list, kanban, and form open. Create a draft settlement and save.
5. **Properties → Rental → Tenants**: the contact list is limited to tenants.

### 3. Sales

1. **Properties → Sales → Contracts**: the sales-order list for SPA orders opens. Open one and confirm the extra property, unit, booking, and installment fields.
2. **Properties → Sales → Payment Plans**: create a plan with duration and percentages, then check list, form, and kanban.
3. **Properties → Sales → Bookings**: the booking list and form open.
4. **Properties → Sales → Customers**: contacts filtered as customers.

### 4. Leads, maintenance, contacts

1. **Properties → Leads → Property Visits**: create a visit and save. Confirm the chatter.
2. **Properties → Leads → Property Leads** and **Opportunities** open the standard CRM views.
3. **Properties → Maintenance → Requests**: the maintenance list opens with property and unit columns.
4. **Properties → Contacts → LandLords** and **Brokers** open the matching contact filters.
5. **Properties → Employees** opens the employee list.

### 5. Configuration

Open **Properties → Configuration** and confirm each menu loads a list and a form with chatter where the model is mail-enabled:

Settings, Durations, Amenities, Cities, Nearby Connectivity, Furnish Types, Specifications, Tags, Utilities, Property Category, Property Types, Property Facilities, and Unit Types.

On **Settings**, confirm Rental Installment Product and Sales Installment Product are editable, then save.

### 6. Portal

Log in as a portal user linked to a contract partner and open `/my`. Confirm the rental-contract and sale-contract entries appear, and that opening a contract shows the portal page.
