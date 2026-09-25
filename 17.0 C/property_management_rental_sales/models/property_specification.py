from odoo import fields, models, api

class PropertySpecification(models.Model):
    _name = 'property.specification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Specification'

    name = fields.Char(string='Specification', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertySpecification, self).create(vals)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertySpecification, self).write(vals)