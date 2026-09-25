from odoo import fields, models, api, _

class PropertyType(models.Model):
    _name = 'property.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Type'
    _order = 'name asc'
    name = fields.Char(string='Property Type', required=True)
    property_categ_id = fields.Many2one('property.category', string='Property Category')
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)