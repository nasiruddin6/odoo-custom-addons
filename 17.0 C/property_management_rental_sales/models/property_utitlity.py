from odoo import fields, models, api

class PropertyUtility(models.Model):
    _inherit = 'product.product'
    _description = 'Property Utility'

    is_property_utility = fields.Boolean(string='Is Property Utility', default=False)
    utility_type = fields.Selection([
        ('water', 'Water Supply'),
        ('electricity', 'Electricity'),
        ('gas', 'Gas Supply'),
        ('internet', 'Internet'),
        ('sewage', 'Sewage System'),
        ('other', 'Other')
    ], string='Utility Type')
