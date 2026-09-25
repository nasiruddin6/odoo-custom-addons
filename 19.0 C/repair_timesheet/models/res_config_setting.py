# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    repair_timesheet_product_id = fields.Many2one(
        comodel_name='product.product',
        string="Repair Timesheet Product",
        config_parameter='repair_timesheet.repair_timesheet_product_id',
        domain="[('type', '=', 'service')]",
    )