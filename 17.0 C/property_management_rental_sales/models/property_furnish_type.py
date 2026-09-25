from odoo import fields, models, api

class PropertyFurnishType(models.Model):
    _name = 'property.furnish.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Furnish Type'

    name = fields.Char(string='Furnish Type', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyFurnishType, self).create(vals)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyFurnishType, self).write(vals)