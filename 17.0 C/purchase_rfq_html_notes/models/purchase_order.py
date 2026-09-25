from odoo import models, fields, api


class PurchaseConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    purchase_rfq_note = fields.Html(string='Default Purchase Note')

    def set_values(self):
        super(PurchaseConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'purchase_rfq_html_notes.rfq_note', self.purchase_rfq_note
        )

    @api.model
    def get_values(self):
        res = super(PurchaseConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            purchase_rfq_note=params.get_param('purchase_rfq_html_notes.rfq_note')
        )
        return res


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _get_default_purchase_notes(self):
        return self.env['ir.config_parameter'].sudo().get_param('purchase_rfq_html_notes.rfq_note')

    purchase_notes = fields.Html(
        string='Purchase Notes',
        default=_get_default_purchase_notes
    )
