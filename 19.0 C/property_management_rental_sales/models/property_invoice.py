from odoo import models, fields, api
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class PropertyInstallment(models.Model):
    _name = 'property.invoice'
    _description = 'Tenancy Installment'

    contract_id = fields.Many2one('property.contract', string='Contract', ondelete='cascade')
    sale_order_id = fields.Many2one('sale.order', string='Sales Contract', ondelete='cascade')
    invoice_date = fields.Date(string='Invoice Date')
    invoice_type = fields.Selection([
        ('rent', 'Rent'),
        ('Lease', 'Lease'),
        ('maintenance', 'Maintenance'),
        ('deposit', 'Deposit'),
        ('penalty', 'Penalty'),
        ('fees', 'Fees'),
        ('other', 'Other')
    ], string='Type')
    description = fields.Char(string='Description')
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True, copy=False)
    payment_status = fields.Selection(related='invoice_id.payment_state', string='Payment Status', store=True)
    currency_id = fields.Many2one(related='contract_id.currency_id')

    def action_view_invoice(self):
        """
        Action to view the invoice related to this installment.
        """
        self.ensure_one()
        if not self.invoice_id:
            raise UserError('No invoice is linked to this installment.')

        action = self.env["ir.actions.act_window"]._for_xml_id("account.action_move_out_invoice_type")
        action.update({
            "name": "Customer Invoice",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "form",
            "views": [(self.env.ref("account.view_move_form").id, "form")],
            "res_id": self.invoice_id.id,
            "target": "current",
        })
        return action

    def action_create_invoice(self):
        """
        Creates an invoice for this installment line.
        """
        for installment in self:
            if installment.invoice_id:
                raise UserError('An invoice already exists for this installment.')
            if installment.amount <= 0:
                raise UserError('Cannot create an invoice for a zero or negative amount.')

            tax_ids = []
            contract = False
            is_sell_invoice = False
            if self.invoice_type == 'sale':
                installment_product_id = int(self.env['ir.config_parameter'].sudo().get_param(
                    'property_management_rental_sales.sales_installment_product_id', 0
                ))
                if not installment_product_id:
                    raise UserError('Please configure the Default Rental Product in Settings.')
                product = self.env['product.product'].browse(installment_product_id)
                partner_id = self.sale_order_id.partner_id
                is_sell_invoice = True

            elif self.invoice_type in ['rent', 'lease']:
                contract = installment.contract_id
                product = contract.installment_product_id
                partner_id = contract.partner_id
                tax_ids = [(6, 0, contract.tax_ids.ids)] if contract.taxes_on_installment else []
            else:
                contract = installment.contract_id
                product = contract.installment_product_id
                partner_id = contract.partner_id
                tax_ids = [(6, 0, contract.tax_ids.ids)] if contract.taxes_on_installment else []

            invoice_lines = [(0, 0, {
                'product_id': product.id,
                'name': installment.description or product.name,
                'quantity': 1,
                'price_unit': installment.amount,
                'tax_ids': tax_ids,
            })]

            invoice_vals = {
                'partner_id': partner_id.id,
                'is_sell_invoice':  is_sell_invoice,
                'move_type': 'out_invoice',
                'invoice_date': installment.invoice_date,
                'invoice_line_ids': invoice_lines,
                'contract_id': contract.id if contract else False,
                'property_id': contract.property_id.id if contract else False,
                'property_unit_id': contract.unit_id.id if contract else False,
                'is_rent_invoice': True,
            }

            invoice = self.env['account.move'].create(invoice_vals)
            installment.invoice_id = invoice.id

        # Return action to open the created invoice(s)
        action = self.env["ir.actions.act_window"]._for_xml_id("account.action_move_out_invoice_type")
        action.update({
            "name": "Customer Invoice",
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "form",
            "views": [(self.env.ref("account.view_move_form").id, "form")],
            "res_id": self.invoice_id.id,
            "target": "current",
        })
        return action

    @api.model
    def cron_auto_create_invoice(self):
        """Create invoice for every Installment (CRON SAFE)"""
        today = fields.Date.today()
        _logger.info("CRON STARTED: %s", today)
        installments = self.search([
            ('contract_id.state', '=', 'active'),
            ('invoice_id', '=', False),
            ('invoice_date', '=', today),
            ('amount', '>', 0),
        ])
        _logger.info(installments)
        if installments:
            for installment in installments:
                installment.action_create_invoice()