{
    "name": "Purchase / RFQ HTML Notes | RFQ Global Notes | RFQ Terms & Conditions | Purchase Order Notes",
    'version': '17.0.1.0.0',
    "summary": """
    Odoo RFQ HTML Notes, Odoo Purchase Order Notes, Odoo PO HTML Notes, Global RFQ PO Notes Odoo, Odoo Purchase HTML Notes, RFQ PO PDF Notes Odoo, Odoo Purchase Notes Module, HTML Notes for RFQ Odoo, Purchase Order HTML Notes, Odoo RFQ PO Custom Notes, Odoo Purchase Document Notes, Odoo 19 RFQ Notes, Odoo 19 Purchase Order Notes, 
    Odoo 19 HTML Notes Module, Odoo Purchase Global Notes, RFQ Notes Odoo Module, PO Notes Odoo App, Odoo Purchase Terms Notes, Odoo RFQ Terms Conditions, Odoo Purchase Conditions Notes, Odoo Purchase HTML Editor, Odoo WYSIWYG Notes, Odoo RFQ PDF Notes, Odoo PO PDF Notes, Odoo Purchase Print Notes, Odoo RFQ Print Notes, Odoo Purchase Report Notes, Odoo QWeb RFQ Notes, Odoo QWeb PO Notes, Odoo Purchase Custom Notes, Odoo RFQ Custom Text, Odoo PO Custom Text, Odoo Purchase Legal Notes, Odoo RFQ Footer Notes, Odoo PO Footer Notes, Odoo Purchase Header Notes, Odoo RFQ Header Notes, Odoo Multi Company RFQ Notes, Odoo Multi Company PO Notes, Odoo Purchase Company Notes, Odoo Purchase Settings Notes, Odoo Global Purchase Notes, Odoo RFQ Standard Notes, Odoo PO Standard Notes, Odoo Purchase Email Notes, Odoo RFQ Email Notes, Odoo PO Email Notes, Odoo Purchase HTML Formatting, Odoo RFQ Rich Text Notes, Odoo PO Rich Text Notes, Odoo Purchase CSS Styling, Odoo RFQ CSS Notes, Odoo PO CSS Notes, Odoo Purchase Backend Notes, Odoo RFQ Form Notes, Odoo PO Form Notes, Odoo Purchase Automation Notes, Odoo Procurement Notes, Odoo Purchase Management Notes, Odoo ERP Purchase Notes, Odoo ERP RFQ Notes, Odoo ERP PO Notes, Odoo Purchase Workflow Notes, Odoo Purchase Documentation Notes, Odoo RFQ Instructions Notes, Odoo PO Instructions Notes, Odoo Purchase Terms Module, Odoo RFQ Terms Module, Odoo PO Terms Module, Odoo Native Purchase Notes, Odoo No Dependency Module, Odoo Standard Purchase Notes, Odoo Purchase Addon, Odoo RFQ Addon, Odoo PO Addon, Odoo Purchase Customization App, Odoo RFQ Customization, Odoo PO Customization, Odoo Purchase Professional Notes, Odoo RFQ Professional Layout, Odoo PO Professional Layout, Odoo Purchase Business Notes, Odoo Purchase Enterprise Notes
    """,
    "Description": """
Purchase / RFQ HTML Notes module allows users to add global notes or terms and conditions to all Request for Quotations (RFQs) and Purchase Orders in Odoo. This feature is particularly useful for businesses that need to include standard information, such as payment terms, delivery instructions, or legal disclaimers, on every RFQ or Purchase Order they issue.
Key Features:
1. Global Notes Configuration: Easily set up and manage global notes or terms and conditions from the settings menu.
2. Automatic Inclusion: The configured notes are automatically included in the description section of all RFQs and Purchase Orders.
3. HTML Formatting: Supports HTML formatting, allowing users to customize the appearance of the notes with styles, links, and other HTML elements.
4. Improved Communication: Ensures that all suppliers receive consistent information, reducing misunderstandings and improving communication.
5. User-Friendly Interface: Intuitive interface for configuring and updating global notes without requiring technical expertise.
Benefits:
- Saves time by eliminating the need to manually add notes to each RFQ or Purchase Order.
- Enhances professionalism by ensuring all documents contain necessary information.
- Reduces errors and omissions by standardizing the information provided to suppliers.
    """,
    "category": "Purchase",
    'author': 'Tectise',
    'website': 'https://www.tectise.com',
    'license': 'OPL-1',
    "depends": ["purchase"],
    "data": [
        "views/purchase_order_view.xml",
        'views/purchase_config_settings_views.xml',
        'views/purchase_report_templates.xml',
    ],
    "assets": {
        "web.assets_backend": [
            "purchase_rfq_html_notes/static/src/css/purchase_notes.css",
        ],
    },
    "installable": True,
    "application": False,
    'images': ['static/description/banner.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 10.00,
    'currency': 'USD',
}
