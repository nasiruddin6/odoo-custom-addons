# Purchase / RFQ HTML Notes

Set one HTML note (terms, delivery instructions, or a disclaimer) and apply it to every RFQ and purchase order.

Depends on `purchase`.

## What it does

- A company-level HTML note in Purchase settings.
- A **Purchase Notes** tab on the RFQ and purchase order form, filled from that default.
- The same note on the printed RFQ and purchase order PDF.

## How to check the UI

1. Open **Purchase → Configuration → Settings**.
2. Under **Purchase Notes**, enter formatted HTML (a heading and a short paragraph) and save.
3. Create a new **RFQ**. Open the **Purchase Notes** tab and confirm the settings text is there.
4. Confirm the RFQ so it becomes a purchase order and check the same tab still shows the note.
5. Print or download the PDF and confirm the note appears on the document.
