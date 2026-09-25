from odoo import fields, models, api

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    contract_id = fields.Many2one('property.contract', string='Contract')

    def create_invoices(self):
        res = super().create_invoices()
        res['context']['default_is_sell_invoice'] = True
        return res