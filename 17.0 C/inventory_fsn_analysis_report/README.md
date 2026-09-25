# FSN Analysis Report

Classifies storable products as Fast, Slow, or Non-moving from stock movement in a date range. Odoo 17. Results can be opened as a list, pivot, and graph, or exported to Excel.

Server: `http://localhost:8017`

Depends on Inventory and Stock Accounting. Excel export needs the Python package `xlsxwriter`.

## Install

1. Open Apps and click **Update Apps List**.
2. Search for `FSN Analysis` and click **Install**.
3. The menu is available to **Inventory / User**.

## UI check

### 1. Wizard

1. Open **Inventory → Reporting → FSN Analysis Report**.
2. Confirm the dialog shows start date, end date, company, classification, fast and slow thresholds, and a Filters page for products, categories, and warehouses.
3. Set a period that contains done stock moves of storable products.
4. Leave product and warehouse filters empty to include everything, then click **Generate Analysis**.

### 2. Result views

1. Confirm the result opens with list, pivot, and graph.
2. On the list, confirm product, classification, and quantity columns. Fast, Slow, and Non-moving rows are visually distinct.
3. Switch to pivot and graph and confirm the same records are grouped.
4. Open one line in form view and confirm the classification matches the thresholds you entered.

### 3. Excel

1. Open the wizard again and click **Export to Excel**.
2. Confirm the file downloads and the rows match the on-screen analysis.
3. Click **Cancel** and confirm the wizard closes.

Raise the fast threshold and generate again. Products that were Fast should drop to Slow or Non-moving when their movement is below the new threshold.
