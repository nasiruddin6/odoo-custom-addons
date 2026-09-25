from odoo import models, fields

class PropertyFacilities(models.Model):
    _name = 'property.facilities'
    _description = 'Property Facilities'

    name = fields.Char(string='Facility Name', required=True)
    active = fields.Boolean(string='Active', default=True)
