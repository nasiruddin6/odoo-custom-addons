from odoo import api, models, fields, _

class ReportSaleContract(models.AbstractModel):
    _name = 'report.property_management_rental_sales.report_sale_contract'
    _description = 'Report Property Sale Contract Template'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sale.order'].sudo().browse(docids)
        return {
            'doc_ids': docids,
            'doc_model': 'sale.order',
            'docs': docs,
        }