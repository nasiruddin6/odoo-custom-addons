from odoo import fields, models, api

class PropertyTags(models.Model):
    _name = 'property.tags'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Tags'

    name = fields.Char(string='Tag Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyTags, self).create(vals)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyTags, self).write(vals)