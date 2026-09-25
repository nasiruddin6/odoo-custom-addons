from odoo import models, fields


class TimesheetLine(models.Model):
    _inherit = "account.analytic.line"

    repair_id = fields.Many2one('repair.order', string="Repair")
