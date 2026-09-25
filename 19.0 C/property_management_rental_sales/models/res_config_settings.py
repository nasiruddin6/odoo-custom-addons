from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    rental_installment_product_id = fields.Many2one(
        'product.product',
        string='Rental Installment Product',
        config_parameter='property_management_rental_sales.rental_installment_product_id'
    )

    sales_installment_product_id = fields.Many2one(
        'product.product',
        string='Sale Installment Product',
        config_parameter='property_management_rental_sales.sales_installment_product_id'
    )

    module_property_rental = fields.Boolean(string="Property Rental Management")
    module_property_sales = fields.Boolean(string="Property Sale Management")