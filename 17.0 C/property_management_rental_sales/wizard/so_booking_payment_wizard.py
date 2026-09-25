from odoo import api, models, fields, _
from odoo.exceptions import UserError


class SOBookingPaymentWizard(models.TransientModel):
    _name = 'so.booking.payment.wizard'
    _description = 'SO Booking Payment Wizard'

    booking_id = fields.Many2one('so.booking', 'Booking', required=True)
    partner_id = fields.Many2one('res.partner', 'Customer', related='booking_id.partner_id', readonly=True)
    currency_id = fields.Many2one('res.currency', 'Currency', related='booking_id.currency_id', readonly=True)
    amount = fields.Monetary('Amount', currency_field='currency_id', required=True)
    date = fields.Date('Payment Date', required=True, default=fields.Date.today)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True, domain="[('type', 'in', ('bank', 'cash'))]")
    payment_method_id = fields.Many2one('account.payment.method.line', 'Payment Method', required=True, domain="[('payment_type', '=', 'inbound'), ('journal_id', '=', journal_id)]")
    partner_bank_id = fields.Many2one('res.partner.bank', 'Bank Account')
    cheque_number = fields.Char('Cheque Number')

    @api.model
    def default_get(self, fields_list):
        """Set default amount from booking"""
        res = super().default_get(fields_list)
        if 'booking_id' in res:
            booking = self.env['so.booking'].browse(res['booking_id'])
            if booking and 'amount' in fields_list:
                res['amount'] = booking.amount + booking.other_fees
        return res

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        """Update payment method when journal changes"""
        if self.journal_id:
            payment_methods = self.journal_id.inbound_payment_method_line_ids
            if payment_methods:
                self.payment_method_id = payment_methods[0]
            else:
                self.payment_method_id = False

    def action_create_payment(self):
        """Create account.payment for the booking"""
        self.ensure_one()

        if self.amount <= 0:
            raise UserError(_("Payment amount must be greater than zero."))

        # Create account.payment record
        payment_vals = {
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.partner_id.id,
            'so_id': self.booking_id.so_id.id,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'payment_method_line_id': self.payment_method_id.id,
            'partner_bank_id': self.partner_bank_id.id if self.partner_bank_id else False,
            'cheque_number': self.cheque_number or False,
        }

        payment = self.env['account.payment'].create(payment_vals)

        # Update booking with payment reference
        self.booking_id.payment_id = payment.id

        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'res_id': payment.id,
            'target': 'current',
        }
