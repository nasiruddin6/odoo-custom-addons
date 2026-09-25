from odoo import fields, models, api

class PropertyAmenities(models.Model):
    _name = 'property.amenities'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Property Amenities'

    name = fields.Char(string='Amenity Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)

    @api.model_create_multi
    def create(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyAmenities, self).create(vals)

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].strip()
        return super(PropertyAmenities, self).write(vals)