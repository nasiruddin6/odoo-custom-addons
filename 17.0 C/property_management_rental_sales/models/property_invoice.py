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
        ('maintenance', 'Maintenance'),
        ('deposit', 'Deposit'),
        ('penalty', 'Penalty'),
        ('fees', 'Fees'),
        ('other', 'Other')
    ], string='Type')
    description = fields.Char(string='Description')
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    vat = fields.Monetary(string='VAT', currency_field='currency_id', compute="_compute_amount", store=True, precompute=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True, copy=False)
    payment_status = fields.Selection(related='invoice_id.payment_state', string='Payment Status', store=True)
    currency_id = fields.Many2one(related='contract_id.currency_id')
    tax_ids = fields.Many2many(related='contract_id.tax_ids', string='Taxes', readonly=1)
    price_total = fields.Monetary(
        string="Included Tax",
        compute='_compute_amount',
        store=True, precompute=True)

    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        """Convert the current record to a dictionary for generic taxes computation.
        
        :return: A python dictionary.
        """
        self.ensure_one()
        partner_id = self.contract_id.partner_id if self.contract_id else self.env.company.partner_id
        currency_id = self.currency_id or self.env.company.currency_id
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            **{
                'tax_ids': self.tax_ids,
                'price_unit': self.amount,
                'quantity': 1.0,
                'partner_id': partner_id,
                'currency_id': currency_id,
                **kwargs,
            },
        )

    @api.depends('amount', 'tax_ids', 'contract_id.taxes_on_installment')
    def _compute_amount(self):
        """Compute price_total and vat following Odoo's standard tax computation."""
        for line in self:
            if line.contract_id and line.contract_id.taxes_on_installment:
                base_line = line._prepare_base_line_for_taxes_computation()
                company = line.contract_id.company_id if line.contract_id else self.env.company
                self.env['account.tax']._add_tax_details_in_base_line(base_line, company)
                line.price_total = base_line['tax_details']['raw_total_included_currency']
                line.vat = line.price_total - line.amount
            else:
                line.vat = 0
                line.price_total = line.amount

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

            elif self.invoice_type == 'rent':
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