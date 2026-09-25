from odoo import fields, models, api

class PropertyAreaType(models.Model):
    _name = 'property.area.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Area Type'

    name = fields.Char(string='Area Type', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyAreaType, self).create(vals)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyAreaType, self).write(vals)