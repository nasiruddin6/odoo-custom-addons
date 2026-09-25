from odoo import fields, models, api

class PropertyCity(models.Model):
    _name = 'property.city'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property City'

    name = fields.Char(string='City Name', required=True)
    state_id = fields.Many2one('res.country.state', string='State', required=True)
    country_id = fields.Many2one('res.country', string='Country', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name']
        return super(PropertyCity, self).create(vals)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name']
        return super(PropertyCity, self).write(vals)