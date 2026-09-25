from odoo import fields, models, api

class PropertyConnectivity(models.Model):
    _name = 'property.connectivity'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Connectivity'

    name = fields.Char(string='Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyConnectivity, self).create(vals)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyConnectivity, self).write(vals)