from odoo import api, models, fields, _

class PropertyUnitType(models.Model):
    _name = 'property.unit.type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Unit Type'

    name = fields.Char("Name", required=True, tracking=True)
    bedroom = fields.Integer("Bedrooms", default=0, tracking=True)
    living = fields.Integer(string='Living', default=0, tracking=True)
    dining = fields.Integer(string='Dining', default=0, tracking=True)
    kitchen = fields.Integer(string='Kitchen', default=0, tracking=True)
    bathroom = fields.Integer(string='Bathrooms', default=0, tracking=True)
    balcony = fields.Integer(string='Balconies', default=0, tracking=True)
    parking = fields.Integer(string='Parking Spaces', default=0, tracking=True)
    active = fields.Boolean(string='Active', default=True)