# Purchase / RFQ HTML Notes

Puts the same HTML notes (terms, delivery notes, legal text) on every RFQ and purchase order in Odoo 17. A default note from Settings is copied onto new orders. Each order can still edit its own note, and the note is printed on the PDF.

Server: `http://localhost:8017`

Depends on Purchase.

## Install

1. Open Apps and click **Update Apps List**.
2. Search for `Purchase / RFQ HTML Notes` and click **Install**.

## UI check

### 1. Global note

1. Open **Purchase → Configuration → Settings**.
2. Confirm the **Purchase Notes** block is visible.
3. Write a note in the HTML editor (for example a bold line and a list) and click **Save**.

### 2. New RFQ

1. Open **Purchase → Orders → Requests for Quotation** and click **New**.
2. Set a vendor and one product line, then save.
3. Open the **Purchase Notes** page at the end of the notebook.
4. Confirm the Settings note was copied here. Edit it if this order needs a different note.

### 3. PDF

1. On the RFQ, use **Print → Request for Quotation**.
2. Confirm the PDF shows a **Purchase Notes** section with the HTML formatting.
3. Confirm the order and print the **Purchase Order**. The same note is on that PDF.

If the note is empty, the PDF section is omitted.
