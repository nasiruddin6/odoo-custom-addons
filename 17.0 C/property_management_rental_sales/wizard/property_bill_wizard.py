from odoo import fields, models, api
from odoo.exceptions import UserError

class PropertyBillWizard(models.TransientModel):
    _name = 'property.bill.wizard'
    _description = 'Property bill Wizard'

    bill_for = fields.Selection([('commission', 'Commission'),  ('other', 'Other')], string='Bill For', required=True, default='commission')
    invoice_date = fields.Date(string='Bill Date', required=True)
    amount = fields.Float(string='Amount', required=True)
    description = fields.Text(string='Description')
    contract_id = fields.Many2one('property.contract', string='Contract', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    partner_id = fields.Many2one('res.partner', string='Tenant / Customer', required=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes')


    def action_create_bill(self):
        invoice_lines = [(0, 0, {
            'product_id': self.product_id.id,
            'name': f" For {self.bill_for}: {self.description}",
            'quantity': 1,
            'price_unit': self.amount,
            'tax_ids': [(6, 0, self.tax_ids.ids)] if self.tax_ids else [],
        })]

        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'in_invoice',
            'invoice_date': self.invoice_date,
            'invoice_line_ids': invoice_lines,
            'contract_id': self.contract_id.id,  # Assuming you added this field to account.move
            'is_rent_invoice': True,
        }

        invoice = self.env['account.move'].create(invoice_vals)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Invoice',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }