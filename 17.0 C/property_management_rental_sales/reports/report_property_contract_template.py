from odoo import models, api, fields, _


class ReportPropertyContractTemplate(models.AbstractModel):
    _name = 'report.property_management_rental_sales.property_contract'
    _description = 'Report Property Contract Template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['property.contract'].sudo().browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'property.contract',
            'docs': docs,
        }