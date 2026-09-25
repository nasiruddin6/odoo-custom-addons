from odoo import fields, models, api
from odoo.exceptions import UserError

class PropertyInvoiceWizard(models.TransientModel):
    _name = 'property.invoice.wizard'
    _description = 'Property Invoice Wizard'

    invoice_for = fields.Selection([
        ('rent', 'Rent'),
        ('maintenance', 'Maintenance'),
        ('deposit', 'Deposit'),
        ('penalty', 'Penalty'),
        ('fees', 'Fees'),
        ('other', 'Other')
    ], string='Invoice For', required=True, default='maintenance')
    invoice_date = fields.Date(string='Invoice Date', required=True)
    amount = fields.Float(string='Amount', required=True)
    description = fields.Text(string='Description')
    property_id = fields.Many2one('property.property', 'Property')
    property_unit_id = fields.Many2one('property.unit', 'Property Unit')
    contract_id = fields.Many2one('property.contract', string='Contract', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    partner_id = fields.Many2one('res.partner', string='Tenant / Customer', required=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes')

    @api.onchange('invoice_for')
    def _onchange_invoice_for(self):
        if self.invoice_for:
            product_mapping = {
                'rent': 'property_management_rental_sales.product_property_rent',
                'maintenance': 'property_management_rental_sales.product_property_maintenance',
                'deposit': 'property_management_rental_sales.product_property_deposit',
                'penalty': 'property_management_rental_sales.product_property_penalty',
                'other': 'property_management_rental_sales.product_property_other',
            }

            xml_id = product_mapping.get(self.invoice_for)
            if xml_id:
                try:
                    self.product_id = self.env.ref(xml_id)
                except ValueError:
                    # Product not found, leave it empty
                    self.product_id = False

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if self.contract_id and self.contract_id.partner_id:
            self.partner_id = self.contract_id.partner_id


    def action_create_invoice(self):
        vals = {
            'invoice_date': self.invoice_date,
            'amount': self.amount,
            'invoice_type': self.invoice_for,
            'description': f"for {self.invoice_for}: {self.description}",
            'contract_id': self.contract_id.id,
        }
        property_invoice = self.env['property.invoice'].create(vals)

        invoice_lines = [(0, 0, {
            'product_id': self.product_id.id,
            'name': f" For {self.invoice_for}: {self.description}",
            'quantity': 1,
            'price_unit': self.amount,
            'tax_ids': [(6, 0, self.tax_ids.ids)] if self.tax_ids else [],
        })]

        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': self.invoice_date,
            'contract_id': self.contract_id.id,
            'property_id': self.property_id.id,
            'property_unit_id': self.property_unit_id.id,
            'is_rent_invoice': True,
            'invoice_line_ids': invoice_lines
        }

        invoice = self.env['account.move'].create(invoice_vals)
        property_invoice.invoice_id = invoice.id

        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }