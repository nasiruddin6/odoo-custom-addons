from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    property_id = fields.Many2one('property.property', 'Property')
    property_unit_id = fields.Many2one('property.unit', 'Property Unit')
    contract_id = fields.Many2one('property.contract', string='Contract')
    is_rent_invoice = fields.Boolean(string='Is Rent Invoice')
    is_sell_invoice = fields.Boolean(string='Is Sell Invoices')
    is_lease_invoice = fields.Boolean(string='Is Lease Invoices')
    so_id = fields.Many2one('sale.order', 'Sale Contract')

    @api.onchange('contract_id', 'partner_id', 'so_id')
    def _onchange_contract_id(self):        
        vals = {}
        if self.contract_id:
            vals.update({
                'property_unit_id': self.contract_id.unit_id.id,
                'property_id': self.contract_id.property_id.id,
                'partner_id': self.contract_id.partner_id.id
            })

        elif self.so_id:
            vals.update({
                'property_unit_id': self.so_id.unit_id.id,
                'property_id': self.so_id.property_id.id,
                'partner_id': self.so_id.partner_id.id
            })
        self.write(vals)


