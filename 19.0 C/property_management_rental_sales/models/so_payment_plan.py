from odoo import api, models, fields, _


class SOPaymentPlan(models.Model):
    _name = 'so.payment.plan'
    _description = 'Payment Plan'
    _rec_name = 'name'

    # ======================================================================================================
    # Payment Plan
    # ======================================================================================================
    name = fields.Char('Name', required=True)
    company_id = fields.Many2one('res.company', 'Company')
    currency_id = fields.Many2one('res.currency', 'Currency')
    # plan setup
    duration = fields.Integer('Duration')
    collection_gaps = fields.Integer('Collection Gap')

    # Payment Ratio
    down_payment_percentage = fields.Float('Down Payment')
    pre_handover_percentage = fields.Float('Pre-Handover')
    on_handover_percentage = fields.Float('On-Handover')
    after_handover_percentage = fields.Float('After-Handover')

    @api.model
    def default_get(self, vals):
        res = super().default_get(vals)
        res.update({
            'company_id': self.env.company.id,
            'currency_id': self.env.user.company_id.currency_id.id
        })
        return res
