from odoo import fields, models, api

class PropertyCategory(models.Model):
    _name = 'property.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Category'

    name = fields.Char(string='Category Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyCategory, self).create(vals)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyCategory, self).write(vals)