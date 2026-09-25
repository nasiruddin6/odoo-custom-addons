from odoo import api, models, fields, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    is_rent_payment = fields.Boolean('Rent Payment')
    is_pdc = fields.Boolean('PDC Payment')
    cheque_number = fields.Char(string='Cheque No')
    property_id = fields.Many2one('property.property', 'Property')
    property_unit_id = fields.Many2one('property.unit', 'Property Unit')
    contract_id = fields.Many2one('property.contract', 'Contract')
    so_id = fields.Many2one('sale.order', 'Sale Order')
    is_eoi_payment = fields.Boolean('EOI Payment')

    @api.onchange('so_id', 'contract_id')
    def _onchange_contract_so(self):
        vals = {}
        if self.so_id:
            vals.update({
                'property_unit_id': self.so_id.unit_id.id,
                'property_id': self.so_id.property_id.id,
                'partner_id': self.so_id.partner_id.id
            })
        elif self.contract_id:
            vals.update({
                'property_unit_id': self.contract_id.unit_id.id,
                'property_id': self.contract_id.property_id.id,
                'partner_id': self.contract_id.partner_id.id
            })
        self.write(vals)
