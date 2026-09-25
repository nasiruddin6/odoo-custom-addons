from dateutil.relativedelta import relativedelta
from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
import logging


_logger = logging.getLogger(__name__)


class SOInstallmentLine(models.Model):
    _name = 'so.installment.line'
    _description = 'SO Installment Line'


    so_id = fields.Many2one('sale.order', string='SO', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    name = fields.Char(string='Name', required=True)
    type = fields.Selection([
        ('down_payment', 'Down Payment'),
        ('admin_fees', 'Admin Fees'),
        ('stamp_duty', 'Stamp Duty Fees'),
        ('registration', 'Registration Fees'),
        ('mutation', 'Mutation Fees'),
        ('installment_before', 'Installment Before Handover'),
        ('installment_on', 'Installment On Handover'),
        ('installment_after', 'Installment After Handover'),
        ('others', 'Others'),
    ], 'Type')
    due_date = fields.Date(string='Due Date')
    invoice_date = fields.Date(string='Invoice Date')
    percentage = fields.Float('%')
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    vat = fields.Monetary(string='VAT', currency_field='currency_id')
    paid_amount = fields.Monetary('Paid Amount', default=0, currency_field='currency_id')
    due_amount = fields.Monetary('Due Amount', default=0, currency_field='currency_id')
    payment_date = fields.Date('Payment Date')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    payment_state = fields.Selection(string='Payment Status', related='invoice_id.payment_state')

    def action_create_invoice(self):
        self.ensure_one()
        for installment in self:
            if installment.invoice_id:
                raise UserError('An invoice already exists for this installment.')
            if installment.amount <= 0:
                raise UserError('Cannot create an invoice for a zero or negative amount.')

            invoice_lines = [(0, 0, {
                'product_id': False,
                'name': f'Down payment for {installment.so_id.name}',
                'quantity': 1,
                'price_unit': installment.amount,
                'tax_ids': [],
            })]

            so_id = installment.so_id

            invoice_vals = {
                'partner_id': so_id.partner_id.id,
                'is_sell_invoice': True,
                'move_type': 'out_invoice',
                'invoice_date': installment.invoice_date,
                'invoice_line_ids': invoice_lines,
                'property_id': so_id.property_id.id if so_id else False,
                'property_unit_id': so_id.unit_id.id if so_id else False,
                'is_rent_invoice': False,
                'so_id': so_id.id if so_id else False,
            }
            invoice = self.env['account.move'].create(invoice_vals)
            installment.invoice_id = invoice.id

    def action_view_invoice(self):
        self.ensure_one()
        if not self.invoice_id:
            raise UserError('No Invoice Found for this installment.')

        return {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'model': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'target': 'current',
            'res_id': self.invoice_id.id,
        }

    @api.model
    def default_get(self, vals):
        res = super().default_get(vals)
        currency = self.env.company.currency_id
        if self.so_id:
            currency = self.so_id.currency_id

        res.update({
            'currency_id': currency.id,
            'due_date': fields.Date.today(),
        })
        return res

    @api.model
    def cron_auto_create_invoice(self):
        """Create invoice for installment lines scheduled for today (CRON SAFE)"""
        today = fields.Date.today()
        _logger.info("SO Installment CRON STARTED: %s", today)
        installments = self.search([
            ('invoice_id', '=', False),
            ('invoice_date', '=', today),
            ('amount', '>', 0),
            ('so_id.state', '!=', 'cancel'),
        ])
        print("=======================================================")
        print(today)
        print(installments)
        print("=======================================================")
        _logger.info("Found %s installments to invoice", len(installments))
        if installments:
            for installment in installments:
                try:
                    installment.action_create_invoice()
                except Exception:
                    _logger.exception('Failed to create invoice for installment %s', installment.id)
